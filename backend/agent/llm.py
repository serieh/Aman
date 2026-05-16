"""
LLM definitions and direct interactions.
"""
import json
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from config import LLM_THINKING_MODEL, LLM_FAST_MODEL, LLM_CONTEXT_WINDOW, LLM_REPEAT_PENALTY
from .prompts.summary import SUMMARY_PROMPT
from .prompts.title import TITLE_PROMPT
from logger import get_logger

logger = get_logger(__name__)

class ResponseFormat(BaseModel):
    content: str
    emotional_state: dict        # e.g. {"emotion": "sadness", "confidence": 0.84}
    # safety_flag: str  

logger.info("Building LLMs")

llm_thinking = ChatOllama(
    model=LLM_THINKING_MODEL,
    num_ctx=LLM_CONTEXT_WINDOW,
    keep_alive=-1,
    repeat_penalty=LLM_REPEAT_PENALTY,
)
structured_llm_thinking = llm_thinking.with_structured_output(ResponseFormat)

llm_fast = ChatOllama(
    model=LLM_FAST_MODEL,
    num_ctx=LLM_CONTEXT_WINDOW,
    keep_alive=-1,
    repeat_penalty=LLM_REPEAT_PENALTY,
    think=False,
)
structured_llm_fast = llm_fast.with_structured_output(ResponseFormat)

async def llm_summrize(user_message: str):
    logger.info("LLM summarization requested")
    try:
        llm = ChatOllama(model=LLM_FAST_MODEL, num_ctx=LLM_CONTEXT_WINDOW)
        messages = [
            SystemMessage(content=SUMMARY_PROMPT),
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
        llm = ChatOllama(model=LLM_FAST_MODEL)
        messages = [
            SystemMessage(content=TITLE_PROMPT),
            HumanMessage(content=user_message)
        ]
        reply = await llm.ainvoke(messages)
        title = reply.content.strip()
        logger.info("LLM title generation completed successfully")
        return title
    except Exception as e:
        logger.error(f"LLM title generation failed | error: {str(e)}")
        raise
