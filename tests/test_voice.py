import pytest

from pipeline import voice


class Resp:
    def __init__(self, status, payload=None):
        self.status_code, self._payload, self.ok, self.text = status, payload, status < 400, ""

    def json(self):
        return self._payload


def test_transcribe_sends_audio_and_language(monkeypatch):
    sent = {}

    def fake_post(url, timeout, headers, data, files):
        sent.update(url=url, data=data, files=files, auth=headers["Authorization"])
        return Resp(200, {"text": "  Për çfarë përdoret hithra? "})

    monkeypatch.setattr(voice.requests, "post", fake_post)
    text = voice.transcribe(b"RIFF....", language="sq", api_key="k")
    assert text == "Për çfarë përdoret hithra?"
    assert sent["url"].endswith("/audio/transcriptions") and sent["auth"] == "Bearer k"
    assert sent["data"]["language"] == "sq" and sent["data"]["model"].startswith("whisper")
    assert sent["files"]["file"][1] == b"RIFF...."


def test_transcribe_needs_key_and_reports_rate_limit(monkeypatch):
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        voice.transcribe(b"x", api_key="")
    monkeypatch.setattr(voice.requests, "post", lambda *a, **k: Resp(429))
    with pytest.raises(RuntimeError, match="rate limit"):
        voice.transcribe(b"x", api_key="k")
