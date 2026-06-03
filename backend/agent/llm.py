import json, re
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from .config import LLM_THINKING_MODEL, LLM_FAST_MODEL, LLM_CONTEXT_WINDOW, LLM_REPEAT_PENALTY, LLM_MAX_RETRIES
from .prompts.summary import SUMMARY_PROMPT
from .prompts.title import TITLE_PROMPT
from logger import get_logger

logger = get_logger(__name__)

class ResponseFormat(BaseModel):
    content: str

class ThinkingLLMWrapper:
    """Wrapper to handle models that output <think> blocks before their JSON/text response."""
    def __init__(self, llm):
        self.llm = llm

    def invoke(self, messages):
        # invoke the unstructured llm
        response = self.llm.invoke(messages)
        raw_text = response.content
        
        # Strip <think> block
        clean_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
        if not clean_text:
            clean_text = raw_text # Fallback
            
        # Try parsing as JSON
        try:
            json_match = re.search(r"\{.*\}", clean_text, flags=re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                if "content" in data:
                    return ResponseFormat(content=data.get("content", ""))
        except json.JSONDecodeError:
            pass
            
        # Fallback: use the cleaned text as content directly
        return ResponseFormat(content=clean_text)

logger.info("Building LLMs")

llm_thinking = ChatOllama(
    model=LLM_THINKING_MODEL,
    num_ctx=LLM_CONTEXT_WINDOW,
    keep_alive=-1,
    repeat_penalty=LLM_REPEAT_PENALTY,
)

structured_llm_thinking = ThinkingLLMWrapper(llm_thinking)

llm_fast = ChatOllama(
    model=LLM_FAST_MODEL,
    num_ctx=LLM_CONTEXT_WINDOW,
    keep_alive=-1,
    repeat_penalty=LLM_REPEAT_PENALTY,
    think=False,
)
structured_llm_fast = llm_fast.with_structured_output(ResponseFormat)

def llm_summarize(user_message: str):
    logger.info("LLM summarization requested")
    messages = [
        SystemMessage(content=SUMMARY_PROMPT),
        HumanMessage(content=user_message)
    ]
    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            reply = llm_fast.invoke(messages)
            raw = reply.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed = json.loads(raw)
            logger.info("LLM summarization completed successfully")
            return parsed
        
        except Exception as e:
            logger.warning(f"LLM summarization attempt {attempt}/{LLM_MAX_RETRIES} failed | error: {str(e)}")
            if attempt == LLM_MAX_RETRIES:
                logger.error("LLM summarization exhausted retries, using fallback")
                return {"content": user_message, "emotional_state": None, "safety_flag": None}

def title_generator(user_message: str):
    logger.info("LLM title generation requested")
    messages = [
        SystemMessage(content=TITLE_PROMPT),
        HumanMessage(content=user_message)
    ]
    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            reply = llm_fast.invoke(messages)
            title = reply.content.strip()
            logger.info("LLM title generation completed successfully")
            return title
        except Exception as e:
            logger.warning(f"LLM title generation attempt {attempt}/{LLM_MAX_RETRIES} failed | error: {str(e)}")
            if attempt == LLM_MAX_RETRIES:
                logger.error("LLM title generation exhausted retries, using fallback")
                return "New Chat"