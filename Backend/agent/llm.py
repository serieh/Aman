import json, re, os
from typing import Annotated
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableLambda

from .config import (
    LLM_FAST_MODEL_NAME, LLM_FAST_MAX_TOKENS, LLM_FAST_MAX_RETRIES,

    LLM_THINKING_MODEL_NAME, LLM_THINKING_SECONDARY_MODEL_NAME, LLM_THINKING_TERTIARY_MODEL_NAME,
    LLM_THINKING_MAX_TOKENS, LLM_THINKING_MAX_RETRIES,

    USE_OLLAMA,
    OLLAMA_FALLBACK_THINKING_MODEL, OLLAMA_FALLBACK_FAST_MODEL,
    OLLAMA_FALLBACK_CONTEXT_WINDOW, OLLAMA_FALLBACK_KEEP_ALIVE,
    OLLAMA_FALLBACK_REPEAT_PENALTY,

    hard_refusal_patterns, soft_disclaimers,
    LLM_MAX_RETRIES,
)
from .prompts.summary import SUMMARY_PROMPT
from .prompts.title import TITLE_PROMPT
from .tools.rag.RAG import run_rag
from logger import get_logger
from timing_logger import timed_operation


load_dotenv()
logger = get_logger(__name__)

@tool
def rag_search(query: str) -> str:
    """
    Search the RAG knowledge base for clinical guidelines, coping strategies, or relevant mental health information.
    CRITICAL: If no results are found, or if the topic is not mental-health related, DO NOT apologize. DO NOT say "there was a mistake" or "let me try again". Simply answer the user directly using your general knowledge, acting naturally as a friend.
    """
    logger.info(f"RAG tool invoked with query: {query}")
    result = run_rag(query)
    passages = result.get("passages", [])
    
    if not passages:
        return "SYSTEM INSTRUCTION: No relevant passages found. Answer the user naturally using your own general knowledge. DO NOT apologize. DO NOT mention that a search failed."
    
    formatted = "\n\n---\n\n".join(passages)
    return f"Information retrieved from knowledge base:\n{formatted}\n\nSYSTEM INSTRUCTION: If these passages are irrelevant to the user's question (e.g. general health like anosmia), ignore them completely and answer from your own knowledge. Do NOT mention the passages or apologize."


@tool
def search_user_memory(query: str, user_id: str) -> str:
    """
    Search your long-term memory for permanent facts, preferences, or biographical details
    about the user. Use this when you need to recall past details they shared.
    """
    if not user_id:
        return "Error: User ID not provided."
        
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

# ── Helpers ──────────────────────────────────────────────────────────

def _clean_thinking_blocks(text: str) -> str:
    """Strip <think>...</think> blocks from model output."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _try_extract_json_content(text: str) -> str | None:
    """Try to extract a JSON 'content' field, but only if the text looks like JSON.
    
    Returns the extracted content string, or None if not applicable.
    This is intentionally conservative to avoid accidentally destroying
    Arabic or mixed-language prose that happens to contain braces.
    """
    stripped = text.strip()
    # Only attempt JSON parsing if the text clearly starts with '{'
    if not stripped.startswith("{"):
        return None
    try:
        data = json.loads(stripped)
        if isinstance(data, dict) and "content" in data and data["content"]:
            return data["content"]
    except json.JSONDecodeError:
        pass
    # Fallback: try to find a JSON object, but only if the whole thing looks like JSON
    try:
        json_match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            if isinstance(data, dict) and "content" in data and data["content"]:
                return data["content"]
    except (json.JSONDecodeError, ValueError):
        pass
    return None


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
            
        clean_text = _clean_thinking_blocks(raw_text)
        if not clean_text:
            clean_text = raw_text  # Fallback
            
        # Try parsing as JSON only if it looks like JSON
        json_content = _try_extract_json_content(clean_text)
        if json_content:
            return ResponseFormat(content=json_content)
            
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
            
        clean_text = _clean_thinking_blocks(raw_text)
        if not clean_text:
            clean_text = raw_text  # Fallback
            
        # Try parsing as JSON only if it looks like JSON
        json_content = _try_extract_json_content(clean_text)
        if json_content:
            logger.debug(f"[LLMWrapper] Parsed JSON content length: {len(json_content)}")
            return ResponseFormat(content=json_content)
            
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


# ═══════════════════════════════════════════════════════════════════════
# Build LLM instances
# ═══════════════════════════════════════════════════════════════════════
logger.info(f"Building LLMs | USE_OLLAMA={USE_OLLAMA}")

# ── Groq models ──────────────────────────────────────────────────────
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

thinking_tertiary_llm = ChatGroq(
    model_name=LLM_THINKING_TERTIARY_MODEL_NAME,
    max_retries=LLM_THINKING_MAX_RETRIES,
    max_tokens=LLM_THINKING_MAX_TOKENS,
    api_key=os.getenv("GROQ_API_KEY", "")
)

# Fast model: same Groq model as thinking, but used without thinking/reasoning
llm_fast_primary = ChatGroq(
    model_name=LLM_FAST_MODEL_NAME,
    max_retries=LLM_FAST_MAX_RETRIES,
    max_tokens=LLM_FAST_MAX_TOKENS,
    api_key=os.getenv("GROQ_API_KEY", "")
)

# ── Safety output check ─────────────────────────────────────────────
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

# ── Bind tools to all models ────────────────────────────────────────
groq_thinking_with_tools = thinking_llm.bind_tools(tools) | RunnableLambda(check_groq_output)
groq_secondary_with_tools = thinking_secondary_llm.bind_tools(tools) | RunnableLambda(check_groq_output)
groq_tertiary_with_tools = thinking_tertiary_llm.bind_tools(tools) | RunnableLambda(check_groq_output)
groq_fast_with_tools = llm_fast_primary.bind_tools(tools) | RunnableLambda(check_groq_output)

# ── Build fallback chains conditionally ──────────────────────────────
# Thinking chain: primary → secondary → tertiary → [ollama gemma4:26b if USE_OLLAMA]
thinking_fallbacks = [groq_secondary_with_tools, groq_tertiary_with_tools]

# Fast chain: primary (no-think) → secondary → tertiary → [ollama gemma4:e2b if USE_OLLAMA]
fast_fallbacks = [groq_secondary_with_tools, groq_tertiary_with_tools]

if USE_OLLAMA:
    from langchain_ollama import ChatOllama
    logger.info("Ollama fallback enabled — creating lazy fallback instances (not preloaded)")

    ollama_thinking_fallback = ChatOllama(
        model=OLLAMA_FALLBACK_THINKING_MODEL,
        num_ctx=OLLAMA_FALLBACK_CONTEXT_WINDOW,
        keep_alive=OLLAMA_FALLBACK_KEEP_ALIVE,
        repeat_penalty=OLLAMA_FALLBACK_REPEAT_PENALTY,
    ).bind_tools(tools)
    thinking_fallbacks.append(ollama_thinking_fallback)

    ollama_fast_fallback = ChatOllama(
        model=OLLAMA_FALLBACK_FAST_MODEL,
        num_ctx=OLLAMA_FALLBACK_CONTEXT_WINDOW,
        keep_alive=OLLAMA_FALLBACK_KEEP_ALIVE,
        repeat_penalty=OLLAMA_FALLBACK_REPEAT_PENALTY,
    ).bind_tools(tools)
    fast_fallbacks.append(ollama_fast_fallback)
else:
    logger.info("Ollama fallback disabled (cloud-only mode)")

# Assemble the final chains
llm_thinking_with_tools = groq_thinking_with_tools.with_fallbacks(thinking_fallbacks)
structured_llm_thinking = LLMWrapper(llm_thinking_with_tools)

llm_fast = groq_fast_with_tools.with_fallbacks(fast_fallbacks)
fast_with_tools = llm_fast  # already has tools bound
structured_llm_fast = LLMWrapper(llm_fast)

logger.info(f"LLM chains built | thinking fallbacks: {len(thinking_fallbacks)} | fast fallbacks: {len(fast_fallbacks)}")


# ═══════════════════════════════════════════════════════════════════════
# Utility LLM functions (summarize, title)
# ═══════════════════════════════════════════════════════════════════════

def llm_summarize(history_text: str) -> dict:
    logger.info("LLM summarization requested")
    messages = [
        SystemMessage(content=SUMMARY_PROMPT),
        HumanMessage(content=history_text)
    ]
    
    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            with timed_operation("llm_summarize", attempt=attempt):
                reply = llm_fast.invoke(messages)
            raw_content = getattr(reply, "content", "") or ""
            
            # Clean thinking blocks if present (common in reasoning models)
            clean_content = _clean_thinking_blocks(raw_content)
            
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
            

def title_generator(user_message: str, language: str = "en") -> str:
    logger.info("LLM title generation requested using thinking model (gpt-oss-120b)")
    messages = [
        SystemMessage(content=TITLE_PROMPT),
        HumanMessage(content=user_message)
    ]
    
    # Always use the thinking model (gpt-oss-120b) for high-quality titles
    chain = llm_thinking_with_tools
    
    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            with timed_operation("title_generation", attempt=attempt):
                reply = chain.invoke(messages)
            raw_content = getattr(reply, "content", "") or ""
            
            # Clean thinking blocks if present (common in reasoning models)
            clean_title = _clean_thinking_blocks(raw_content)
            
            # Programmatically clean up quotes, backticks, and trailing punctuation
            clean_title = clean_title.strip("\"'`«»\u201c\u201d").rstrip(".").strip()
            
            if not clean_title:
                raise ValueError("Generated title was empty")
                
            logger.info("LLM title generation completed successfully")
            return clean_title
            
        except Exception as e:
            logger.warning(f"LLM title generation attempt {attempt}/{LLM_MAX_RETRIES} failed | error: {str(e)}")
            if attempt == LLM_MAX_RETRIES:
                logger.error("LLM title generation exhausted retries, using fallback")
                return "محادثة جديدة" if language == "ar" else "New Chat"