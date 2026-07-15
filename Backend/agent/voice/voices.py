# voice/voices.py
"""Voice catalog for edge-tts neural voices and accents."""
from dataclasses import dataclass
from typing import Literal

Language = Literal["english", "arabic"]
Gender = Literal["female", "male"]

@dataclass(frozen=True)
class VoiceOption:
    id: str
    label: str
    language: Language
    gender: Gender
    voice: str  # The edge-tts voice string, e.g. "en-US-EmmaNeural"
    description: str = ""

VOICE_CATALOG: tuple[VoiceOption, ...] = (
    VoiceOption(
        id="en_emma",
        label="Emma (US)",
        language="english",
        gender="female",
        voice="en-US-EmmaNeural",
        description="English (US) — warm, expressive female voice",
    ),
    VoiceOption(
        id="en_brian",
        label="Brian (US)",
        language="english",
        gender="male",
        voice="en-US-BrianNeural",
        description="English (US) — clear male voice",
    ),
    VoiceOption(
        id="ar_zariyah",
        label="Zariyah (SA)",
        language="arabic",
        gender="female",
        voice="ar-SA-ZariyahNeural",
        description="Arabic (Saudi Arabia) — natural female voice",
    ),
    VoiceOption(
        id="ar_hamed",
        label="Hamed (SA)",
        language="arabic",
        gender="male",
        voice="ar-SA-HamedNeural",
        description="Arabic (Saudi Arabia) — clear male voice",
    ),
)

_VOICES_BY_ID = {v.id: v for v in VOICE_CATALOG}

def get_voice(voice_id: str) -> VoiceOption | None:
    return _VOICES_BY_ID.get(voice_id)

def list_voices(*, language: Language | None = None) -> list[VoiceOption]:
    if language is None:
        return list(VOICE_CATALOG)
    return [v for v in VOICE_CATALOG if v.language == language]

def resolve_voice_for_language(
    voice_id: str,
    *,
    detected_language: str | None = None,
) -> VoiceOption:
    """
    Returns the configured voice.
    If the detected language does not match the voice's language,
    routes to the corresponding same-gender voice in the detected language.
    """
    selected = get_voice(voice_id)
    if not selected:
        # Default fallback
        selected = VOICE_CATALOG[0]

    if not detected_language:
        return selected

    lang = detected_language.lower()
    is_arabic = lang in {"ar", "arabic", "mixed"} or lang.startswith("ar")

    if is_arabic and selected.language == "arabic":
        return selected
    if not is_arabic and selected.language == "english":
        return selected

    # Swap to same-gender voice in detected language
    target_lang = "arabic" if is_arabic else "english"
    for candidate in VOICE_CATALOG:
        if candidate.language == target_lang and candidate.gender == selected.gender:
            return candidate

    # Return default for target language if gender match not found
    for candidate in VOICE_CATALOG:
        if candidate.language == target_lang:
            return candidate

    return selected

import re
def resolve_voice_for_text(
    text: str,
    preferred_voice_id: str,
    persona_id: str
) -> VoiceOption:
    """
    Resolves the best VoiceOption based on the actual text to be spoken
    and the selected persona, avoiding misaligned auto-detection.
    """
    preferred = get_voice(preferred_voice_id)
    if not preferred:
        preferred = VOICE_CATALOG[0]

    # Check if the text contains Arabic characters
    has_arabic = bool(re.search(r'[\u0600-\u06FF]', text))
    
    if has_arabic:
        # Arabic text MUST be read by an Arabic voice to avoid crash/gibberish
        if preferred.language == "arabic":
            return preferred
        # If preferred voice is English (e.g. Layla), swap to corresponding female Arabic voice
        target_gender = preferred.gender
        for candidate in VOICE_CATALOG:
            if candidate.language == "arabic" and candidate.gender == target_gender:
                return candidate
        return VOICE_CATALOG[2] # Fallback to ar_zariyah (Saudi Arabic female)
    else:
        # Purely English/Latin text
        # If the preferred voice is English, use it.
        if preferred.language == "english":
            return preferred
        # If the preferred voice is Arabic, keep it to preserve persona identity
        return preferred
