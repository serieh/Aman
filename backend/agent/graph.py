import operator
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableConfig
from .llm import structured_llm_thinking, structured_llm_fast, tools
from logger import get_logger
from .config import LLM_MAX_RETRIES, FALLBACK_RESPONSE

logger = get_logger(__name__)
logger.info("Creator agent module loaded")

class AgentState(TypedDict):
    messages: Annotated[Sequence, operator.add]
    user_id: str
    chat_id: str
    emotion_context: dict | None   
    response: dict | None
    model_preference: str
    safety_context: dict | None
    


async def agent_node(state: AgentState, config: RunnableConfig):
    chat_id = state.get("chat_id", "unknown")
    model_preference = state.get("model_preference", "2")
    logger.info(f"Agent node processing | chat_id: {chat_id} | model_tier: {model_preference}")

    llm = structured_llm_thinking if model_preference == "1" else structured_llm_fast

    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            # Pass config so astream_events can intercept the chat model stream
            response = await llm.ainvoke(state["messages"], config=config)
            
            # If it's a tool call, update messages state and continue graph execution
            if getattr(response, "tool_calls", None):
                logger.info(f"LLM tool call generated | chat_id: {chat_id} | attempt: {attempt}")
                return {"messages": [response]}
            
            # Otherwise, it's final ResponseFormat object
            resp_dict = response.model_dump() if hasattr(response, "model_dump") else {"content": response.content}
            emotion = resp_dict.get("emotional_state", {}).get("emotion", "unknown")
            logger.info(f"LLM final response generated | chat_id: {chat_id} | detected_emotion: {emotion} | attempt: {attempt}")
            return {"response": resp_dict}

        except Exception as e:
            logger.warning(f"Agent node attempt {attempt}/{LLM_MAX_RETRIES} failed | chat_id: {chat_id} | error: {str(e)}")
            if attempt == LLM_MAX_RETRIES:
                logger.error(f"Agent node exhausted retries, using fallback | chat_id: {chat_id}")
                return {"response": FALLBACK_RESPONSE}
            

def should_use_tools(state: AgentState) -> str:
    """
    Edge condition: did the LLM ask to call a tool?
    Returns "tools" → ToolNode, or "end" → done.
    """
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return "end"

def build_graph() -> object:
    logger.info("Building agent graph")

    graph = StateGraph(AgentState)
    tool_node = ToolNode(tools)
    graph.add_node("tools", tool_node)
    graph.add_node("agent", agent_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent",
        should_use_tools,
        {"tools": "tools", "end": END},
    )
    graph.add_edge("tools", "agent")

    logger.info("Agent graph compiled successfully")
    return graph.compile()

GRAPH = build_graph()