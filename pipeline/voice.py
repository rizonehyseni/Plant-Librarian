"""Speech to text for asking with your voice, with Groq's free Whisper model.

The recording is sent to Groq only when the user presses record, and is not stored.
Whisper understands Albanian; `language` is a hint ("sq" or "en"), not a restriction.
"""
import os

import requests

from .config import GROQ_API_KEY

TRANSCRIBE_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
WHISPER_MODEL = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3")
# Plant names help Whisper spell dialect words it would otherwise mishear.
PROMPT = "Bimë mjekësore: kamomil, hithër, çaj mali, mullaga, sherebel, kantarion, gëlli, bari sherbetit."


def transcribe(audio: bytes, filename: str = "question.wav", language: str | None = None,
               api_key: str = GROQ_API_KEY) -> str:
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to .env (free key: https://console.groq.com/keys).")
    data = {"model": WHISPER_MODEL, "response_format": "json", "temperature": "0", "prompt": PROMPT}
    if language:
        data["language"] = language
    r = requests.post(TRANSCRIBE_URL, timeout=60, headers={"Authorization": f"Bearer {api_key}"},
                      data=data, files={"file": (filename, audio, "audio/wav")})
    if r.status_code == 429:
        raise RuntimeError("Groq rate limit reached. Wait a minute and try again.")
    if not r.ok:
        raise RuntimeError(f"Groq speech-to-text error {r.status_code}: {r.text[:200]}")
    return (r.json().get("text") or "").strip()
