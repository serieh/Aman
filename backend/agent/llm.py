import json, re
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from .config import LLM_THINKING_MODEL, LLM_FAST_MODEL, LLM_CONTEXT_WINDOW, LLM_REPEAT_PENALTY
from .prompts.summary import SUMMARY_PROMPT
from .prompts.title import TITLE_PROMPT
from logger import get_logger

logger = get_logger(__name__)

class ResponseFormat(BaseModel):
    content: str
    note: str = ""

class ThinkingLLMWrapper:
    """Wrapper to handle models that output <think> blocks before their JSON/text response."""
    def __init__(self, llm):
        self.llm = llm

    def invoke(self, messages):
        # We invoke the unstructured llm
        response = self.llm.invoke(messages)
        raw_text = response.content
        
        # 1. Strip <think> block
        clean_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
        if not clean_text:
            clean_text = raw_text # Fallback
            
        # 2. Try parsing as JSON
        try:
            json_match = re.search(r"\{.*\}", clean_text, flags=re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                if "content" in data:
                    return ResponseFormat(content=data.get("content", ""), note=data.get("note", ""))
        except json.JSONDecodeError:
            pass
            
        # 3. Fallback: Parse plain text based on the prompt's formatting
        content_val = clean_text
        note_val = ""
        
        clean_lower = clean_text.lower()
        c_match = re.search(r'(?:1\.\s*)?content\s*[:-]', clean_lower)
        n_match = re.search(r'(?:2\.\s*)?note\s*[:-]', clean_lower)
        
        if c_match and n_match:
            c_idx = c_match.start()
            n_idx = n_match.start()
            if c_idx < n_idx:
                content_val = clean_text[c_match.end():n_idx].strip()
                note_val = clean_text[n_match.end():].strip()
            else:
                note_val = clean_text[n_match.end():c_idx].strip()
                content_val = clean_text[c_match.end():].strip()
        
        return ResponseFormat(content=content_val, note=note_val)

logger.info("Building LLMs")

llm_thinking = ChatOllama(
    model=LLM_THINKING_MODEL,
    num_ctx=LLM_CONTEXT_WINDOW,
    keep_alive=-1,
    repeat_penalty=LLM_REPEAT_PENALTY,
)
# Use our custom wrapper instead of .with_structured_output() to avoid <think> tag JSON failures
structured_llm_thinking = ThinkingLLMWrapper(llm_thinking)

llm_fast = ChatOllama(
    model=LLM_FAST_MODEL,
    num_ctx=LLM_CONTEXT_WINDOW,
    keep_alive=-1,
    repeat_penalty=LLM_REPEAT_PENALTY,
    think=False,
)
structured_llm_fast = llm_fast.with_structured_output(ResponseFormat)

MAX_RETRIES = 3

def llm_summarize(user_message: str):
    logger.info("LLM summarization requested")
    messages = [
        SystemMessage(content=SUMMARY_PROMPT),
        HumanMessage(content=user_message)
    ]
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            reply = llm_fast.invoke(messages)
            raw = reply.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed = json.loads(raw)
            logger.info("LLM summarization completed successfully")
            return parsed
        
        except Exception as e:
            logger.warning(f"LLM summarization attempt {attempt}/{MAX_RETRIES} failed | error: {str(e)}")
            if attempt == MAX_RETRIES:
                logger.error("LLM summarization exhausted retries, using fallback")
                return {"content": user_message, "emotional_state": None, "note": None, "safety_flag": None}

def title_generator(user_message: str):
    logger.info("LLM title generation requested")
    messages = [
        SystemMessage(content=TITLE_PROMPT),
        HumanMessage(content=user_message)
    ]
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            reply = llm_fast.invoke(messages)
            title = reply.content.strip()
            logger.info("LLM title generation completed successfully")
            return title
        except Exception as e:
            logger.warning(f"LLM title generation attempt {attempt}/{MAX_RETRIES} failed | error: {str(e)}")
            if attempt == MAX_RETRIES:
                logger.error("LLM title generation exhausted retries, using fallback")
                return "New Chat"