import json, re, os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from langchain.tools import tool
from langchain_groq import ChatGroq

load_dotenv()

from .config import LLM_FAST_MODEL, LLM_CONTEXT_WINDOW, LLM_REPEAT_PENALTY, LLM_MAX_RETRIES, GROQ_MODEL_NAME, GROQ_SECONDARY_MODEL_NAME
from .prompts.summary import SUMMARY_PROMPT
from .prompts.title import TITLE_PROMPT
from .tools.rag.RAG import run_rag
from logger import get_logger
from langchain_core.runnables import RunnableLambda

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
    return f"""<SYSTEM_DIRECTIVE_STRICT>
توجيه صارم للنظام: 
1. يجب أن تجيب باللغة العربية حصراً وبنفس لهجة شخصيتك.
2. لا تبدأ إجابتك بأي ترحيب (مثل "أهلاً بك" أو "مرحباً").
3. أجب مباشرة على سؤال المستخدم بناءً على هذه المعلومات فقط.
</SYSTEM_DIRECTIVE_STRICT>

[معلومات البحث المرجعية]
{formatted}"""

tools = [rag_search]

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

llm_fast = ChatOllama(
    model=LLM_FAST_MODEL,
    num_ctx=LLM_CONTEXT_WINDOW,
    keep_alive=-1,
    repeat_penalty=LLM_REPEAT_PENALTY,
    think=False,
)
fast_with_tools = llm_fast.bind_tools(tools)
structured_llm_fast = LLMWrapper(fast_with_tools)

groq_llm = ChatGroq(
    model_name=GROQ_MODEL_NAME,
    max_retries=1,
    max_tokens=2048,
    api_key=os.getenv("GROQ_API_KEY", "")
)

groq_secondary_llm = ChatGroq(
    model_name=GROQ_SECONDARY_MODEL_NAME,
    max_retries=1,
    max_tokens=2048,
    api_key=os.getenv("GROQ_API_KEY", "")
)

# Bind tools to both models, then create the fallback runnable
def check_groq_output(response):
    content = getattr(response, "content", "")
    content_lower = content.lower()
    if not content and not getattr(response, "tool_calls", None):
        logger.warning("Groq returned empty response. Forcing fallback...")
        raise ValueError("Empty response from Groq API (likely safety filter).")
        
    hard_refusal_patterns = [
        "cannot fulfill", "unable to provide", "i apologize, but i cannot", 
        "i must decline", "i cannot engage", "i am not able to", 
        "it would be inappropriate", "i must refrain",
        "لا أستطيع", "لا يمكنني", "أعتذر، لا يمكنني", "أنا غير قادر على"
    ]
    
    # Soft disclaimers that we can just strip out
    soft_disclaimers = [
        "As an AI language model, ",
        "I want to be transparent that I am an AI. ",
        "Please note that I am an AI and not a medical professional. "
    ]
    
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

groq_with_tools = groq_llm.bind_tools(tools) | RunnableLambda(check_groq_output)
groq_secondary_with_tools = groq_secondary_llm.bind_tools(tools) | RunnableLambda(check_groq_output)

llm_thinking_with_tools = groq_with_tools.with_fallbacks([groq_secondary_with_tools, fast_with_tools])
structured_llm_thinking = LLMWrapper(llm_thinking_with_tools)


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