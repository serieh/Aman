from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, Sequence
import operator, json
from langchain_core.messages import SystemMessage, HumanMessage
from .prompts.summary import SUMMARY_PROMPT
from .prompts.title import TITLE_PROMPT
from pydantic import BaseModel
from logger import get_logger

logger = get_logger(__name__)
logger.info("Creator agent module loaded")

llm_thinking_name = "gemma4:31b" # "qwen3.5:9b"
llm_fast_name = "gemma4:e2b" # "qwen3.5:4b"

# Import for any tool here, e.g.:
# from .tools.rag import rag_tool
TOOLS = []

class ResponseFormat(BaseModel):
    content: str
    emotional_state: dict        # e.g. {"emotion": "sadness", "confidence": 0.84}
    # safety_flag: str  

logger.info("Building LLMs")

logger.info(f"Building LLM | Target Model: Thinking")
llm_thinking = ChatOllama(
    model=llm_thinking_name,
    num_ctx=8192,
    keep_alive=-1,
    repeat_penalty=1.15,
).bind_tools(TOOLS)
structured_llm_thinking = llm_thinking.with_structured_output(ResponseFormat)

logger.info(f"Building LLM | Target Model: Fast")
llm_fast = ChatOllama(
    model=llm_fast_name,
    num_ctx=8192,
    keep_alive=-1,
    repeat_penalty=1.15,
    think=False,
)
structured_llm_fast = llm_fast.with_structured_output(ResponseFormat)

async def llm_summrize(user_message: str):
    logger.info("LLM summarization requested")
    try:
        llm = ChatOllama(model=llm_fast_name, num_ctx=8192)
        messages = [
            SystemMessage(content = SUMMARY_PROMPT),
            HumanMessage(content=user_message)
        ]

        reply = await llm.ainvoke(messages)
        parsed = json.loads(reply.content)
        
        logger.info("LLM summarization completed successfully")
        return parsed
        
    except Exception as e:
        logger.error(f"LLM summarization failed | error: {str(e)}")
        raise

async def title_generator(user_message: str):
    logger.info("LLM title generation requested")
    try:
        llm = ChatOllama(model=llm_fast_name)
        messages = [
            SystemMessage(content = TITLE_PROMPT),
            HumanMessage(content=user_message)
        ]

        reply = await llm.ainvoke(messages)

        title = reply.content.strip()
        
        logger.info("LLM title generation completed successfully")
        return title
        
    except Exception as e:
        logger.error(f"LLM title generation failed | error: {str(e)}")
        raise

class AgentState(TypedDict):
    messages: Annotated[Sequence, operator.add]
    user_id: str
    chat_id: str
    emotion_context: dict | None   
    response: dict | None
    model_preference: str


async def agent_node(state: AgentState):
    chat_id = state.get("chat_id", "unknown")
    model_preference = state.get("model_preference", "thinking")
    logger.info(f"Agent node processing | chat_id: {chat_id} | model_tier: {model_preference}")
    
    try:
        llm = structured_llm_thinking if model_preference == "thinking" else structured_llm_fast
        response = await llm.ainvoke(state["messages"])
        logger.debug(f"LLM response received | chat_id: {chat_id} | Model Used: {model_preference}")
        
        resp_dict = response.model_dump()
        emotion = resp_dict.get("emotional_state", {}).get("emotion", "unknown")
        
        logger.info(f"LLM response generated | chat_id: {chat_id} | detected_emotion: {emotion}")
        
        return {"response": resp_dict}
        
    except Exception as e:
        logger.error(f"Agent node execution failed | chat_id: {chat_id} | error: {str(e)}")
        raise


def should_use_tools(state: AgentState) -> str:
    last = state["messages"][-1]
    chat_id = state.get("chat_id", "unknown")
    
    if hasattr(last, "tool_calls") and last.tool_calls:
        tool_names = [tc.get("name") for tc in last.tool_calls]
        logger.info(f"Routing to tools | chat_id: {chat_id} | tools: {tool_names}")
        return "tools"
        
    logger.debug(f"Routing to end | chat_id: {chat_id}")
    return "end"


def build_graph() -> object:
    logger.info("Building agent graph")

    tool_node = ToolNode(TOOLS)
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")

    graph.add_conditional_edges(
        "agent",
        should_use_tools,
        {"tools": "tools", "end": END},
    )

    graph.add_edge("tools", "agent")

    logger.info(f"Agent graph compiled successfully | tools_loaded: {len(TOOLS)}")

    return graph.compile()


GRAPH = build_graph()