"""
Backend/services/transcriber.py
─────────────────────────────────
Sends recorded audio bytes to OpenAI Whisper API.
Returns transcribed text string.
"""

import io
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Sends raw audio bytes to Whisper API.
    Returns transcribed text or empty string if failed.
    """
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"

        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en"
        )
        return response.text.strip()

    except Exception as e:
        print(f"[Transcriber] Error: {e}")
        return ""