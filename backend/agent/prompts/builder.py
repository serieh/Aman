from .core import CORE_PROMPT
from .safety import SAFETY_PROMPT
from .cultural import CULTURAL_PROMPT
from .tools import TOOLS_PROMPT
from .dynamic import build_dynamic_context
from logger import get_logger

logger = get_logger(__name__)


"""
Runtime Injection Order
[1] SYSTEM PROMPT LAYERS
[2] TOOL CONTEXT
[3] SAFETY FLAGS
[4] CHAT MEMORY
[5] USER MESSAGE
"""

def build_system_prompt(
    language="auto",
    emotion=None,
    safety_flag=None
):
    log_meta = f"System prompt constructed | language: {language}"
    if emotion:
        # Assuming emotion might be a dict based on your other files, safely extract the string
        emotion_val = emotion.get('emotion', 'unknown') if isinstance(emotion, dict) else emotion
        log_meta += f" | emotion: {emotion_val}"
    if safety_flag:
        log_meta += f" | safety_flag: {safety_flag}"
        
    logger.debug(log_meta)

    try:
        return "\n\n".join([
            CORE_PROMPT,
            SAFETY_PROMPT,
            CULTURAL_PROMPT,
            TOOLS_PROMPT,
            build_dynamic_context(
                language=language,
                emotion=emotion,
                safety_flag=safety_flag
            )
        ])
    except Exception as e:
        # CORRECT LOG: Catching any issues if dynamic context injection fails
        logger.error(f"Failed to build system prompt | error: {str(e)}")
        raise