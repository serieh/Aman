import os
import tempfile
import asyncio
import base64
from groq import AsyncGroq
from logger import get_logger

logger = get_logger(__name__)

# Initialize Groq client
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", ""))

async def transcribe_audio(audio_base64: str) -> str:
    """
    Decodes base64 audio, saves it to a temp file, and transcribes it using Groq's Whisper API.
    """
    if not audio_base64:
        return ""

    try:
        audio_data = base64.b64decode(audio_base64)
        
        # Determine format based on typical MediaRecorder output.
        # Chrome outputs webm or ogg, we can use a generic extension like .webm which Whisper accepts.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        logger.info(f"Transcribing audio file: {tmp_path}")
        
        with open(tmp_path, "rb") as file:
            transcription = await client.audio.transcriptions.create(
                file=(tmp_path, file.read()),
                model="whisper-large-v3",
                prompt="The user might be speaking Arabic, English, or a mix of both. This is an emotional wellness chat.",
                response_format="text"
            )

        os.remove(tmp_path)
        
        text = str(transcription).strip()
        logger.info(f"Transcription result: {text}")
        return text

    except Exception as e:
        logger.error(f"STT transcription failed: {e}")
        return ""
