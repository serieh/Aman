# voice/stt.py
"""Speech-to-text integration using Groq Whisper via raw urllib requests."""
import os
import uuid
import urllib.request
import urllib.error
import json
from pathlib import Path
from logger import get_logger

logger = get_logger(__name__)

def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "recording.webm",
    content_type: str = "audio/webm",
    language: str = None,
    prompt: str = None
) -> dict:
    """
    Transcribe audio bytes using Groq Whisper.
    Auto-detects language if not specified.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        # Fallback to load .env from workspace if not globally set
        env_path = Path("/home/opendude/Documents/Aman Reformed/.env")
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith("GROQ_API_KEY"):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        os.environ["GROQ_API_KEY"] = api_key
                        break

    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured in the environment.")

    boundary = uuid.uuid4().hex
    body = []

    # Model parameter
    body.append(f"--{boundary}".encode('utf-8'))
    body.append(b'Content-Disposition: form-data; name="model"')
    body.append(b'')
    body.append(b'whisper-large-v3')

    # Language parameter (optional)
    if language:
        body.append(f"--{boundary}".encode('utf-8'))
        body.append(b'Content-Disposition: form-data; name="language"')
        body.append(b'')
        body.append(language.encode('utf-8'))

    # Prompt parameter (optional)
    if prompt:
        body.append(f"--{boundary}".encode('utf-8'))
        body.append(b'Content-Disposition: form-data; name="prompt"')
        body.append(b'')
        body.append(prompt.encode('utf-8'))

    # File parameter
    body.append(f"--{boundary}".encode('utf-8'))
    body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode('utf-8'))
    body.append(f'Content-Type: {content_type}'.encode('utf-8'))
    body.append(b'')
    body.append(audio_bytes)

    # End boundary
    body.append(f"--{boundary}--".encode('utf-8'))
    body.append(b'')

    payload = b'\r\n'.join(body)

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Content-Length': str(len(payload)),
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    req = urllib.request.Request(url, data=payload, headers=headers, method='POST')

    try:
        logger.info(f"Sending STT request to Groq | size: {len(audio_bytes)} bytes")
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        logger.error(f"Groq Whisper HTTP Error: {e.code} - {err_msg}")
        raise RuntimeError(f"Whisper transcription failed: {err_msg}")
    except Exception as e:
        logger.error(f"Groq Whisper connection failed: {e}")
        raise RuntimeError(f"Whisper transcription connection failed: {e}")
