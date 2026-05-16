"""
LangGraph agent definition.
"""
import operator
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END

from .llm import structured_llm_thinking, structured_llm_fast
from logger import get_logger

logger = get_logger(__name__)
logger.info("Creator agent module loaded")

class AgentState(TypedDict):
    messages: Annotated[Sequence, operator.add]
    user_id: str
    chat_id: str
    emotion_context: dict | None   
    response: dict | None
    model_preference: str

async def agent_node(state: AgentState):
    chat_id = state.get("chat_id", "unknown")
    model_preference = state.get("model_preference", "2")
    logger.info(f"Agent node processing | chat_id: {chat_id} | model_tier: {model_preference}")
    
    try:
        llm = structured_llm_thinking if model_preference == "1" else structured_llm_fast
        response = await llm.ainvoke(state["messages"])
        logger.debug(f"LLM response received | chat_id: {chat_id} | Model Used: {model_preference}")
        
        resp_dict = response.model_dump()
        emotion = resp_dict.get("emotional_state", {}).get("emotion", "unknown")
        
        logger.info(f"LLM response generated | chat_id: {chat_id} | detected_emotion: {emotion}")
        
        return {"response": resp_dict}
        
    except Exception as e:
        logger.error(f"Agent node execution failed | chat_id: {chat_id} | error: {str(e)}")
        raise

def build_graph() -> object:
    logger.info("Building agent graph")

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.set_entry_point("agent")
    graph.add_edge("agent", END)

    # TODO: When tools are added, re-introduce conditional edges here

    logger.info("Agent graph compiled successfully")
    return graph.compile()

GRAPH = build_graph()
