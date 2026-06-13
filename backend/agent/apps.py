# backend/agent/apps.py
import threading
from logger import get_logger
from agent.emotion_estimator import estimate_emotion

logger = get_logger(__name__)

def _warmup_groq():
    """Send a tiny request to Groq to verify the API key works and warm up the connection."""
    try:
        from agent.llm import llm_fast_primary
        from langchain_core.messages import HumanMessage
        response = llm_fast_primary.invoke(
            [HumanMessage(content="Say OK")],
            max_tokens=5,
        )
        logger.info(f"Groq warmup successful | response: {getattr(response, 'content', '')[:30]}")
    except Exception as e:
        logger.warning(f"Groq warmup failed (API may be unreachable or key invalid) | error: {e}")

def _preload():
    # Warmup Groq API connection
    _warmup_groq()

    # Preload RAG embedding model
    try:
        from agent.tools.rag.embeddings import get_embedding_model
        get_embedding_model().embed_query("test")
        logger.info("Preloaded RAG embedding model")
    except Exception as e:
        logger.warning(f"Failed to preload embedding model | error: {e}")

    # Preload emotion estimator
    estimate_emotion("test")
    logger.info("Preloaded emotion estimator")

def preload_models():
    threading.Thread(target=_preload, daemon=True).start()
