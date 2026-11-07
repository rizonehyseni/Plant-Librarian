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
    monkeypatch.setattr(extract, "OFFLINE", False)

    first = extract.extract_doc("paper", ["page text"])
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

