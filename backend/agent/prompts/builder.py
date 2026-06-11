from .core import get_core_prompt
from .safety import SAFETY_PROMPT
from .cultural import CULTURAL_PROMPT
from .tools import TOOLS_PROMPT
from .dynamic import build_dynamic_context
from logger import get_logger
import functools

logger = get_logger(__name__)


"""
Runtime Injection Order
[1] SYSTEM PROMPT LAYERS
[2] TOOL CONTEXT
[3] SAFETY FLAGS
[4] CHAT MEMORY
[5] USER MESSAGE
"""

@functools.lru_cache(maxsize=10)
def _get_static_prompt(mode: str) -> str:
    return "\n\n".join([
        get_core_prompt(mode),
        SAFETY_PROMPT,
        CULTURAL_PROMPT,
        TOOLS_PROMPT,
    ])

def build_system_prompt(
    emotion=None,
    safety_flag=None,
    grey_area_categories: str = "",
    user_context: str = "",
    mode: str = "normal",
    emotion_history: list = None,
    flag_history: list = None,
):
    log_meta = f"System prompt constructed | mode: {mode}"
    if emotion:
        emotion_val = emotion.get('emotion', 'unknown') if isinstance(emotion, dict) else emotion
        log_meta += f" | emotion: {emotion_val}"
    if safety_flag:
        log_meta += f" | safety_flag: {safety_flag}"
        
    logger.debug(log_meta)

    try:
        parts = []
        if user_context:
            parts.append(user_context)
        
        parts.append(_get_static_prompt(mode))
        
        parts.append(build_dynamic_context(
            emotion=emotion,
            safety_flag=safety_flag,
            grey_area_categories=grey_area_categories,
            emotion_history=emotion_history,
            flag_history=flag_history,
        ))
        return "\n\n".join(parts)
    except Exception as e:
        logger.error(f"Failed to build system prompt | error: {str(e)}")
        raise