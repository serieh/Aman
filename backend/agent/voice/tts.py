import base64
import edge_tts
from logger import get_logger

logger = get_logger(__name__)

async def generate_audio(text: str, voice: str = "ar-EG-SalmaNeural") -> str:
    """
    Generates TTS audio using edge-tts and returns a Base64 encoded MP3 string.
    Default voice is ar-EG-SalmaNeural (Female, Egypt, Arabic).
    """
    try:
        if not text.strip():
            return ""
            
        communicate = edge_tts.Communicate(text, voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
                
        return base64.b64encode(audio_data).decode("utf-8")
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        return ""
