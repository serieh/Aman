# backend/agent/apps.py
import threading, requests
from logger import get_logger
from .config import LLM_FAST_MODEL, LLM_THINKING_MODEL
from agent.emotion_estimator import estimate_emotion

logger = get_logger(__name__)

def _preload():
    for model in [LLM_FAST_MODEL]:
        try:
            requests.post("http://localhost:11434/api/generate", json={
                "model": model,
                "prompt": "",
            })
            logger.info(f"Preloaded model into VRAM | model: {model}")
        except Exception as e:
            logger.warning(f"Model preload failed | model: {model} | error: {e}")
            
    estimate_emotion("test")
    logger.info("Preloaded emotion estimator")

def preload_models():
    threading.Thread(target=_preload, daemon=True).start()


        
        
