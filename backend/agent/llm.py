import json, re, os
from typing import Annotated
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import InjectedState

from .config import (
    LLM_FAST_MODEL, LLM_FAST_CONTEXT_WINDOW, 
    LLM_FAST_KEEP_ALIVE, LLM_FAST_REPEAT_PENALTY, LLM_FAST_THINK,

    LLM_THINKING_MODEL_NAME, LLM_THINKING_SECONDARY_MODEL_NAME,
    LLM_THINKING_MAX_TOKENS, LLM_THINKING_MAX_RETRIES,

    hard_refusal_patterns, soft_disclaimers,
    LLM_MAX_RETRIES,
)
from .prompts.summary import SUMMARY_PROMPT
from .prompts.title import TITLE_PROMPT
from .tools.rag.RAG import run_rag
from logger import get_logger


load_dotenv()
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
        return "No relevant passages found in the knowledge base."
    
    formatted = "\n\n---\n\n".join(passages)
    return f"Information retrieved from knowledge base:\n{formatted}"


@tool
def search_user_memory(query: str, state: Annotated[dict, InjectedState]) -> str:
    """
    Search your long-term memory for permanent facts, preferences, or biographical details
    about the user. Use this when you need to recall past details they shared.
    """
    user_id = state.get("user_id")
    if not user_id:
        return "Error: User ID not found in conversation state."
        
    logger.info(f"Memory search invoked for user {user_id} with query: {query}")
    # Local import to prevent circular dependency
    from agent.memory.long_term_memory import retrieve_user_facts
    facts = retrieve_user_facts(user_id, query)
    
    if not facts:
        return "No relevant facts found in memory."
    return f"[Retrieved User Memory]:\n{facts}"

tools = [rag_search, search_user_memory]

class ResponseFormat(BaseModel):
    content: str

class LLMWrapper:
    def __init__(self, llm):
        self.llm = llm

    def invoke(self, messages, config=None):
        if config:
            response = self.llm.invoke(messages, config=config)
        else:
            response = self.llm.invoke(messages)
            
        # If the LLM invoked a tool, return the AIMessage directly
        if getattr(response, "tool_calls", None):
            return response
            
        raw_text = response.content
        if "reasoning_content" in response.additional_kwargs and response.additional_kwargs["reasoning_content"]:
            raw_text = "<think>\n" + response.additional_kwargs["reasoning_content"] + "\n</think>\n" + raw_text
            
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

    async def ainvoke(self, messages, config=None):
        if config:
            response = await self.llm.ainvoke(messages, config=config)
        else:
            response = await self.llm.ainvoke(messages)
            
        # If the LLM invoked a tool, return the AIMessage directly
        if getattr(response, "tool_calls", None):
            return response
            
        raw_text = response.content
        if "reasoning_content" in response.additional_kwargs and response.additional_kwargs["reasoning_content"]:
            raw_text = "<think>\n" + response.additional_kwargs["reasoning_content"] + "\n</think>\n" + raw_text
            
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
                    logger.debug(f"[LLMWrapper] Parsed JSON content: {data.get('content', '')}")
                    return ResponseFormat(content=data.get("content", ""))
        except json.JSONDecodeError:
            pass
            
        logger.debug(f"[LLMWrapper] Fallback returning clean_text. Length: {len(clean_text)}")
        # Fallback: use the cleaned text as content directly
        return ResponseFormat(content=clean_text)

    def stream(self, messages):
        in_reasoning = False
        reasoning_started = False
        
        # Try to extract actual model name from Langchain wrapper
        model_str = "unknown"
        if hasattr(self.llm, "runnable"): # RunnableWithFallbacks
            base = getattr(self.llm.runnable, "bound", self.llm.runnable)
            model_str = getattr(base, "model_name", getattr(base, "model", "unknown"))
        else:
            base = getattr(self.llm, "bound", self.llm)
            model_str = getattr(base, "model_name", getattr(base, "model", "unknown"))

        logger.info(f"LLM Stream starting | Target Model: {model_str}")
        
        for chunk in self.llm.stream(messages):
            # If the chunk has tool calls, just yield it (useful if tools are used)
            if getattr(chunk, "tool_call_chunks", None):
                yield chunk
                continue
                
            reasoning = chunk.additional_kwargs.get("reasoning_content", "")
            if reasoning:
                if not reasoning_started:
                    chunk.content = "<think>\n" + reasoning
                    reasoning_started = True
                    in_reasoning = True
                else:
                    chunk.content = reasoning
            else:
                if in_reasoning:
                    chunk.content = "\n</think>\n" + (chunk.content or "")
                    in_reasoning = False
            yield chunk

logger.info("Building LLMs")

thinking_llm = ChatGroq(
    model_name=LLM_THINKING_MODEL_NAME,
    max_retries=LLM_THINKING_MAX_RETRIES,
    max_tokens=LLM_THINKING_MAX_TOKENS,
    api_key=os.getenv("GROQ_API_KEY", "")
)

thinking_secondary_llm = ChatGroq(
    model_name=LLM_THINKING_SECONDARY_MODEL_NAME,
    max_retries=LLM_THINKING_MAX_RETRIES,
    max_tokens=LLM_THINKING_MAX_TOKENS,
    api_key=os.getenv("GROQ_API_KEY", "")
)

ollama_fast = ChatOllama(
    model=LLM_FAST_MODEL,
    num_ctx=LLM_FAST_CONTEXT_WINDOW,
    keep_alive=LLM_FAST_KEEP_ALIVE,
    repeat_penalty=LLM_FAST_REPEAT_PENALTY,
    think=LLM_FAST_THINK,
)
llm_fast = ollama_fast.with_fallbacks([thinking_secondary_llm])

fast_with_tools = llm_fast.bind_tools(tools)
structured_llm_fast = LLMWrapper(fast_with_tools)

# Bind tools to both models, then create the fallback runnable
def check_groq_output(response):
    content = getattr(response, "content", "")
    content_lower = content.lower()
    if not content and not getattr(response, "tool_calls", None):
        logger.warning("Groq returned empty response. Forcing fallback...")
        raise ValueError("Empty response from Groq API (likely safety filter).")
    
    if any(p in content_lower for p in hard_refusal_patterns):
        # If it's a short response, it's a hard refusal
        if len(content.split()) < 40:
            logger.warning(f"Groq returned a hard refusal: {content}. Forcing fallback...")
            raise ValueError("API Refusal detected.")
            
    # Strip soft disclaimers
    clean_content = content
    for disclaimer in soft_disclaimers:
        if clean_content.startswith(disclaimer):
            clean_content = clean_content[len(disclaimer):].strip()
            
    response.content = clean_content
    return response

groq_with_tools = thinking_llm.bind_tools(tools) | RunnableLambda(check_groq_output)
groq_secondary_with_tools = thinking_secondary_llm.bind_tools(tools) | RunnableLambda(check_groq_output)

llm_thinking_with_tools = groq_with_tools.with_fallbacks([groq_secondary_with_tools, fast_with_tools])
structured_llm_thinking = LLMWrapper(llm_thinking_with_tools)


def llm_summarize(history_text: str) -> dict:
    logger.info("LLM summarization requested")
    messages = [
        SystemMessage(content=SUMMARY_PROMPT),
        HumanMessage(content=history_text)
    ]
    
    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            reply = llm_fast.invoke(messages)
            raw_content = reply.content or ""
            
            # Clean thinking blocks if present (common in reasoning models)
            clean_content = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.DOTALL).strip()
            
            # Extract JSON block using regex (ignores markdown fences and preambles)
            json_match = re.search(r"\{.*\}", clean_content, flags=re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in response")
                
            parsed = json.loads(json_match.group(0))
            
            # 3. Normalize keys to prevent KeyErrors in caller
            normalized = {
                "content": parsed.get("content") or parsed.get("summary") or "Factual summary of the conversation",
                "emotional_state": parsed.get("emotional_state"),
                "safety_flag": parsed.get("safety_flag")
            }
            
            logger.info("LLM summarization completed successfully")
            return normalized
            
        except Exception as e:
            logger.warning(f"LLM summarization attempt {attempt}/{LLM_MAX_RETRIES} failed | error: {str(e)}")
            if attempt == LLM_MAX_RETRIES:
                logger.error("LLM summarization exhausted retries, using fallback")
                # Return a safe fallback dict matching the expected schema
                return {
                    "content": "Conversation history chunk archived under fallback due to parsing error.",
                    "emotional_state": None,
                    "safety_flag": None
                }
            

def title_generator(user_message: str) -> str:
    logger.info("LLM title generation requested")
    messages = [
        SystemMessage(content=TITLE_PROMPT),
        HumanMessage(content=user_message)
    ]
    
    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            reply = llm_fast.invoke(messages)
            raw_content = reply.content or ""
            
            # Clean thinking blocks if present (common in reasoning models)
            clean_title = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.DOTALL).strip()
            
            # Programmatically clean up quotes, backticks, and trailing punctuation
            clean_title = clean_title.strip("\"'`«»“”").rstrip(".").strip()
            
            if not clean_title:
                raise ValueError("Generated title was empty")
                
            logger.info("LLM title generation completed successfully")
            return clean_title
            
        except Exception as e:
            logger.warning(f"LLM title generation attempt {attempt}/{LLM_MAX_RETRIES} failed | error: {str(e)}")
            if attempt == LLM_MAX_RETRIES:
                logger.error("LLM title generation exhausted retries, using fallback")
                return "Untitled Chat"