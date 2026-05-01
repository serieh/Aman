from .core import CORE_PROMPT
from .safety import SAFETY_PROMPT
from .cultural import CULTURAL_PROMPT
from .tools import TOOLS_PROMPT
from .dynamic import build_dynamic_context

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