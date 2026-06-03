import operator
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END

from .llm import structured_llm_thinking, structured_llm_fast
from logger import get_logger
from config import LLM_MAX_RETRIES

logger = get_logger(__name__)
logger.info("Creator agent module loaded")

class AgentState(TypedDict):
    messages: Annotated[Sequence, operator.add]
    user_id: str
    chat_id: str
    emotion_context: dict | None   
    response: dict | None
    model_preference: str

FALLBACK_RESPONSE = {
    "content": "I'm here with you. Could you tell me a little more about what's on your mind?",
    "emotional_state": {"emotion": "unknown", "confidence": 0.0},
}

def agent_node(state: AgentState):
    chat_id = state.get("chat_id", "unknown")
    model_preference = state.get("model_preference", "2")
    logger.info(f"Agent node processing | chat_id: {chat_id} | model_tier: {model_preference}")

    llm = structured_llm_thinking if model_preference == "1" else structured_llm_fast

    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            response = llm.invoke(state["messages"])
            resp_dict = response.model_dump()
            emotion = resp_dict.get("emotional_state", {}).get("emotion", "unknown")
            logger.info(f"LLM response generated | chat_id: {chat_id} | detected_emotion: {emotion} | attempt: {attempt}")
            return {"response": resp_dict}

        except Exception as e:
            logger.warning(f"Agent node attempt {attempt}/{LLM_MAX_RETRIES} failed | chat_id: {chat_id} | error: {str(e)}")
            if attempt == LLM_MAX_RETRIES:
                logger.error(f"Agent node exhausted retries, using fallback | chat_id: {chat_id}")
                return {"response": FALLBACK_RESPONSE}

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