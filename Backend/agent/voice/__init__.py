# voice/__init__.py
"""Voice components package."""
from .stt import transcribe_audio
from .tts import synthesize_speech
from .voices import VOICE_CATALOG, get_voice, list_voices, resolve_voice_for_language
