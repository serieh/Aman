# voice/tts.py
"""Text-to-speech synthesis using edge-tts."""
import asyncio
import edge_tts
from logger import get_logger
from .voices import VoiceOption, get_voice

logger = get_logger(__name__)

async def synthesize_speech(text: str, voice: VoiceOption) -> bytes:
    """
    Synthesize text into speech MP3 bytes using edge-tts.
    """
    stripped_text = (text or "").strip()
    if not stripped_text:
        raise ValueError("Cannot synthesize speech from empty text.")

    logger.info(f"Synthesizing TTS with voice {voice.voice} | text length: {len(stripped_text)} chars")
    
    try:
        communicate = edge_tts.Communicate(stripped_text, voice.voice)
        audio_bytes = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]
                
        if not audio_bytes:
            raise RuntimeError("TTS returned empty audio stream.")
            
        logger.info(f"TTS synthesis complete | size: {len(audio_bytes)} bytes")
        return audio_bytes
    except Exception as e:
        logger.error(f"edge-tts synthesis failed: {e}")
        raise RuntimeError(f"TTS synthesis failed: {e}")
