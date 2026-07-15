# Tests/test_voice_subsystems.py
import sys
import os
import unittest
import asyncio
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).resolve().parents[1] / "Backend"))
sys.path.append(str(Path(__file__).resolve().parents[1] / "Backend" / "agent"))

from agent.voice.voices import VOICE_CATALOG, get_voice, list_voices, resolve_voice_for_language
from agent.voice.tts import synthesize_speech
from agent.voice.stt import transcribe_audio

class TestVoiceCatalog(unittest.TestCase):
    def test_voice_listing(self):
        voices = list_voices()
        self.assertEqual(len(voices), 4)
        
        ar_voices = list_voices(language="arabic")
        self.assertEqual(len(ar_voices), 2)
        self.assertTrue(all(v.language == "arabic" for v in ar_voices))

    def test_voice_retrieval(self):
        emma = get_voice("en_emma")
        self.assertIsNotNone(emma)
        self.assertEqual(emma.voice, "en-US-EmmaNeural")
        
        unknown = get_voice("nonexistent")
        self.assertIsNone(unknown)

    def test_voice_language_routing(self):
        # 1. Matching language (English -> English)
        emma = resolve_voice_for_language("en_emma", detected_language="en")
        self.assertEqual(emma.id, "en_emma")

        # 2. Language mismatch (English voice requested, but Arabic detected -> Swaps to Zariyah)
        zariyah = resolve_voice_for_language("en_emma", detected_language="ar")
        self.assertEqual(zariyah.id, "ar_zariyah")

        # 3. Dynamic gender preservation (Male English -> Male Arabic)
        hamed = resolve_voice_for_language("en_brian", detected_language="arabic")
        self.assertEqual(hamed.id, "ar_hamed")

        # 4. Dynamic gender preservation (Female Arabic -> Female English)
        emma_swapped = resolve_voice_for_language("ar_zariyah", detected_language="english")
        self.assertEqual(emma_swapped.id, "en_emma")

class TestVoiceSynthesis(unittest.IsolatedAsyncioTestCase):
    async def test_edge_tts_synthesis(self):
        # We test with a short text sentence
        voice = get_voice("en_emma")
        try:
            audio_bytes = await synthesize_speech("Hello, this is a test.", voice)
            self.assertGreater(len(audio_bytes), 0)
            # Standard MP3 file header check (ID3 or frame sync)
            self.assertTrue(audio_bytes.startswith(b'ID3') or audio_bytes.startswith(b'\xff'))
            print(f"Synthesized {len(audio_bytes)} bytes successfully.")
        except Exception as e:
            self.fail(f"edge-tts synthesis failed: {e}")

if __name__ == "__main__":
    unittest.main()
