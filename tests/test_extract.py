import json
import sys
from types import SimpleNamespace

import pytest

from pipeline import extract


def sample_record():
    return extract.PlantUse(
        local_name="Çaj mali",
        name_in_text="Origanum vulgare L.",
        family="Lamiaceae",
        part_used="Aerial parts",
        preparation="Infusion",
        administration=None,
        use="Reported for cough",
        location=None,
        page=1,
        quote="Çaj mali, aerial parts, infusion.",
    )


def test_chunks_keep_original_page_numbers():
    pages = [f"text {i}" for i in range(1, extract.PAGES_PER_CALL + 2)]

    chunks = list(extract._chunks(pages))

    assert len(chunks) == 2
    assert "[page 1]" in chunks[0]
    assert f"[page {extract.PAGES_PER_CALL}]" in chunks[0]
    assert f"[page {extract.PAGES_PER_CALL + 1}]" in chunks[1]


def test_missing_api_key_skips_uncached_document(tmp_path, monkeypatch):
    monkeypatch.setattr(extract, "CACHE", tmp_path)
    monkeypatch.setattr(extract, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(extract, "GROQ_API_KEY", "")
    monkeypatch.setattr(extract, "OFFLINE", False)

    assert extract.extract_doc("paper", ["page text"]) == []
    assert not (tmp_path / "extract" / "paper.json").exists()


def test_structured_response_is_parsed_and_cached(tmp_path, monkeypatch):
    record = sample_record()
    parsed = extract.Extraction(records=[record])
    calls = []

    class FakeMessages:
        def parse(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(stop_reason="end_turn", parsed_output=parsed)

    fake_anthropic = SimpleNamespace(Anthropic=lambda: SimpleNamespace(messages=FakeMessages()))
    monkeypatch.setitem(sys.modules, "anthropic", fake_anthropic)
    monkeypatch.setattr(extract, "CACHE", tmp_path)
    monkeypatch.setattr(extract, "ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(extract, "GROQ_API_KEY", "")
    monkeypatch.setattr(extract, "OFFLINE", False)

    first = extract.extract_doc("paper", ["Table 1. Çaj mali, aerial parts, infusion. Cough."])
    second = extract.extract_doc("paper", ["different text"])

    assert first == [{**record.model_dump(), "record_origin": "AI Extracted"}]
    assert second == first
    assert len(calls) == 1
    assert calls[0]["output_format"] is extract.Extraction
    assert "[page 1]" in calls[0]["messages"][0]["content"]
    saved = json.loads((tmp_path / "extract" / "paper.json").read_text(encoding="utf-8"))
    assert saved == first


def test_cache_is_used_without_api_key(tmp_path, monkeypatch):
    cache_file = tmp_path / "extract" / "paper.json"
    cache_file.parent.mkdir(parents=True)
    expected = [sample_record().model_dump()]
    cache_file.write_text(json.dumps(expected), encoding="utf-8")
    monkeypatch.setattr(extract, "CACHE", tmp_path)
    monkeypatch.setattr(extract, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(extract, "OFFLINE", True)

    assert extract.extract_doc("paper", ["ignored"]) == expected



class FakeResponse:
    def __init__(self, status, payload=None, headers=None):
        self.status_code, self._payload, self.headers = status, payload, headers or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


def test_groq_is_default_free_provider_and_records_are_grounded(tmp_path, monkeypatch):
    good = sample_record().model_dump()
    invented = {**good, "local_name": "Bar i shpikur", "quote": "a line that is not in the study"}
    wrong_page = {**good, "page": 9}
    content = json.dumps({"records": [good, invented, wrong_page]})
    calls = []

    def fake_post(url, json, timeout, headers):
        calls.append(json)
        if len(calls) == 1:  # free-tier rate limit once
            return FakeResponse(429, headers={"retry-after": "0"})
        return FakeResponse(200, {"choices": [{"finish_reason": "stop", "message": {"content": content}}]})

    monkeypatch.setattr(extract.requests, "post", fake_post)
    monkeypatch.setattr(extract.time, "sleep", lambda s: None)
    monkeypatch.setattr(extract, "CACHE", tmp_path)
    monkeypatch.setattr(extract, "GROQ_API_KEY", "free-key")
    monkeypatch.setattr(extract, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(extract, "OFFLINE", False)
    monkeypatch.delenv("EXTRACT_PROVIDER", raising=False)

    records = extract.extract_doc("paper", ["Table 1. Çaj mali, aerial parts,\ninfusion. Cough."])

    assert extract.provider() == "groq"
    assert [r["local_name"] for r in records] == ["Çaj mali"]
    assert records[0]["record_origin"] == "AI Extracted"
    schema = calls[1]["response_format"]["json_schema"]
    assert schema["strict"] is True
    item = schema["schema"]["properties"]["records"]["items"]
    assert set(item["required"]) == set(item["properties"]) and item["additionalProperties"] is False
    assert len(calls) == 2  # retried after the 429


def test_provider_choice(monkeypatch):
    monkeypatch.setattr(extract, "GROQ_API_KEY", "g")
    monkeypatch.setattr(extract, "ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("EXTRACT_PROVIDER", "anthropic")
    assert extract.provider() is None  # asked for Anthropic but no key: never a silent paid fallback
    monkeypatch.delenv("EXTRACT_PROVIDER")
    assert extract.provider() == "groq"


# A table row as PDF text: each cell on its own line, columns interleaved with other rows.
TABLE_PAGE = """Arctium lappa L.
(Asteraceae) 12/DE/10
Bullushtra
Areal parts
Decoction
Skin inflammation
Anti‑diabetic
Aristolochia clematitis L.
Fiku i egër"""


def test_quote_with_cells_joined_by_ellipsis_is_found():
    quote = "Arctium lappa L. ... Bullushtra ... Areal parts ... Decoction ... Anti-diabetic"
    assert extract.quote_on_page(quote, TABLE_PAGE)
    assert extract.quote_on_page("Arctium lappa L. … Bullushtra", TABLE_PAGE)


def test_quote_piece_missing_from_page_is_rejected():
    quote = "Arctium lappa L. ... Bullushtra ... Infusion against cough"
    assert not extract.quote_on_page(quote, TABLE_PAGE)
    assert not extract.quote_on_page("Arctium lappa L. ... Bullushtra", "Some other page about Zea mays")


def test_too_short_quote_is_rejected():
    assert not extract.quote_on_page("Decoction", TABLE_PAGE)
    assert not extract.quote_on_page("...", TABLE_PAGE)


def test_groq_extraction_resumes_and_retries_rejected_chunks_page_by_page(tmp_path, monkeypatch):
    calls = []

    def fake_call(text):
        calls.append(text)
        if "[page 1]" in text and "[page 2]" in text:
            raise extract.GroqChunkError("schema")  # the 2-page chunk is rejected
        if "[page 2]" in text:
            raise extract.GroqChunkError("schema")  # page 2 alone is rejected too: skipped
        return [{"page": int(text.split("[page ")[1].split("]")[0])}]

    monkeypatch.setattr(extract, "CACHE", tmp_path)
    monkeypatch.setattr(extract, "GROQ_PAGES_PER_CALL", 2)
    monkeypatch.setattr(extract, "_call_groq", fake_call)
    records = extract._extract_groq_resumable("doc", ["a", "b", "c"])
    assert [r["page"] for r in records] == [1, 3]
    assert not (tmp_path / "extract" / "doc.partial.json").exists()

    # a crash after the first chunk keeps its pages for the next run
    (tmp_path / "extract").mkdir(exist_ok=True)
    (tmp_path / "extract" / "doc2.partial.json").write_text('{"0": [{"page": 1}]}', encoding="utf-8")
    calls.clear()
    assert [r["page"] for r in extract._extract_groq_resumable("doc2", ["a", "b", "c"])] == [1, 3]
    assert all("[page 1]" not in c for c in calls)
