from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, Sequence
import operator, json
from langchain_core.messages import SystemMessage, HumanMessage
from .prompts.summary import summary_prompt
from pydantic import BaseModel
from logger import get_logger

logger = get_logger(__name__)
logger.info("Creator agent module loaded")

llm_name = "qwen3.5:9b"
llm_summary_name = "qwen3.5:4b"

# Import for any tool here, e.g.:
# from .tools.rag import rag_tool


class ResponseFormat(BaseModel):
    content: str
    emotional_state: dict        # e.g. {"emotion": "sadness", "confidence": 0.84}
    # safety_flag: str  


class AgentState(TypedDict):
    messages: Annotated[Sequence, operator.add]
    user_id: str
    chat_id: str
    emotion_context: dict | None   
    response: dict | None # it works and i dont like it


# Tools will be added here when YOU MY FRIEND finshed them :|
TOOLS = []

def build_llm():
    logger.info("Building LLM")
    llm = ChatOllama(
        model=llm_name, 
        stop=["<|im_start|>", "<|im_end|>"],
        num_ctx=32768, 
        keep_alive=-1 # Keeps the model in VRAM indefinitely
    ).bind_tools(TOOLS)
    structured_llm = llm.with_structured_output(ResponseFormat)
    return structured_llm

async def llm_summrize(user_message: str):
    logger.debug("LLM summarization requested")
    try:
        llm = ChatOllama(model=llm_summary_name, format="json")
        messages = [
            SystemMessage(content = summary_prompt),
            HumanMessage(content=user_message)
        ]

        reply = llm.invoke(messages)
        parsed = json.loads(reply.content)
        
        # CORRECT LOG: Track the success, but NEVER the raw `parsed` content.
        logger.info("LLM summarization completed successfully")
        return parsed
        
    except Exception as e:
        logger.error(f"LLM summarization failed | error: {str(e)}")
        raise


async def agent_node(state: AgentState):
    chat_id = state.get("chat_id", "unknown")
    logger.debug(f"Agent node processing | chat_id: {chat_id}")
    
    try:
        llm = build_llm()
        
        # FIX: Changed to await and ainvoke
        response = await llm.ainvoke(state["messages"])
        
        # Extract metadata for logging without exposing content
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