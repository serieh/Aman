import json, re
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from langchain.tools import tool
from .tools.rag.RAG import run_rag

from .config import LLM_THINKING_MODEL, LLM_FAST_MODEL, LLM_CONTEXT_WINDOW, LLM_REPEAT_PENALTY, LLM_MAX_RETRIES
from .prompts.summary import SUMMARY_PROMPT
from .prompts.title import TITLE_PROMPT
from logger import get_logger

logger = get_logger(__name__)

@tool
def rag_search(query: str) -> str:
    """
    Search the RAG knowledge base for clinical guidelines, coping strategies, or relevant mental health information.
    """
    logger.info(f"RAG tool invoked with query: {query}")
    result = run_rag(query)
    passages = result.get("passages", [])
    if not passages:
        return "No relevant passages found in the knowledge base. Please answer the user's question using your general therapeutic knowledge and do your best to respond."
    
    formatted = "\n\n---\n\n".join(passages)
    return (
        "Here is the retrieved knowledge based on your query:\n\n"
        f"{formatted}\n\n"
        "Please read and integrate this information where see fit into your final response to the user."
    )

tools = [rag_search]

class ResponseFormat(BaseModel):
    content: str

class LLMWrapper:
    """Wrapper to handle tool calls or extract JSON/text response."""
    def __init__(self, llm):
        self.llm = llm

    def invoke(self, messages):
        response = self.llm.invoke(messages)
        
        # If the LLM invoked a tool, return the AIMessage directly
        if getattr(response, "tool_calls", None):
            return response
            
        raw_text = response.content
        
        # Strip <think> block if present
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

    def stream(self, messages):
        # Directly yield chunks for streaming, frontend handles parsing/think blocks
        for chunk in self.llm.stream(messages):
            yield chunk

logger.info("Building LLMs")

llm_thinking = ChatOllama(
    model=LLM_THINKING_MODEL,
    num_ctx=LLM_CONTEXT_WINDOW,
    keep_alive=-1,
    repeat_penalty=LLM_REPEAT_PENALTY,
)
structured_llm_thinking = LLMWrapper(llm_thinking.bind_tools(tools))

llm_fast = ChatOllama(
    model=LLM_FAST_MODEL,
    num_ctx=LLM_CONTEXT_WINDOW,
    keep_alive=-1,
    repeat_penalty=LLM_REPEAT_PENALTY,
    think=False,
)
structured_llm_fast = LLMWrapper(llm_fast.bind_tools(tools))

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