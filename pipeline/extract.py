"""Step 2: the LLM reads each study and returns structured plant-use records.

The LLM is used ONLY here, to turn unstructured text into rows. Every row keeps the
page number and a short verbatim quote, so it can be checked against the source.
Results are cached in data/cache/extract/<doc_id>.json; delete a file to re-extract.

Provider: Groq (free key, default when GROQ_API_KEY is set) or Anthropic (optional).
Set EXTRACT_PROVIDER=groq|anthropic to choose. Records whose page is outside the chunk
or whose quote is not found on that page are dropped, so a weaker model cannot add
lines the study does not contain.
"""
import json
import os
import re
import time
import unicodedata
from typing import List, Optional

import requests
from pydantic import BaseModel, Field, ValidationError
from rapidfuzz import fuzz

from .config import ANTHROPIC_API_KEY, CACHE, GROQ_API_KEY, MODEL, OFFLINE

PAGES_PER_CALL = 8
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_EXTRACT_MODEL = os.getenv("GROQ_EXTRACT_MODEL", "openai/gpt-oss-120b")
# Groq's free tier allows few tokens per minute, so send small chunks.
GROQ_PAGES_PER_CALL = int(os.getenv("GROQ_PAGES_PER_CALL", "2"))
QUOTE_MATCH = 80  # rapidfuzz partial_ratio needed between quote and page text


class PlantUse(BaseModel):
    local_name: str = Field(description="Albanian (or other local) name exactly as written")
    name_in_text: Optional[str] = Field(None, description="Scientific name if the study gives one")
    family: Optional[str] = None
    part_used: str = Field(description="e.g. leaves, flowers, root, aerial parts")
    preparation: str = Field(description="e.g. infusion, decoction, tincture, raw, ointment")
    administration: Optional[str] = Field(None, description="oral, topical, inhalation...")
    use: str = Field(description="What it is used for, in English")
    location: Optional[str] = Field(None, description="Village or region if stated")
    page: int = Field(description="Page number from the [page N] marker")
    quote: str = Field(description="Short verbatim snippet (max ~25 words) supporting this record")


class Extraction(BaseModel):
    records: List[PlantUse]


SYSTEM = (
    "You extract ethnobotanical records from scientific studies about medicinal plants "
    "in Kosovo and Albanian-speaking regions. Return one record per plant x part x "
    "preparation x use that the text actually states. Only include facts written in the "
    "text; never add knowledge from elsewhere. If a field is not stated, leave it null. "
    "Copy the supporting quote verbatim. Tables count: read each table row as a record."
)


def provider() -> str | None:
    """'groq', 'anthropic' or None (no key: extraction is skipped)."""
    choice = os.getenv("EXTRACT_PROVIDER", "").strip().lower()
    if choice in {"groq", "anthropic"}:
        return choice if (GROQ_API_KEY if choice == "groq" else ANTHROPIC_API_KEY) else None
    return "groq" if GROQ_API_KEY else "anthropic" if ANTHROPIC_API_KEY else None


def _chunks(pages: list[str], size: int = PAGES_PER_CALL):
    for start in range(0, len(pages), size):
        block = pages[start:start + size]
        yield "".join(f"\n[page {start + i + 1}]\n{p}" for i, p in enumerate(block))


def _strict_schema() -> dict:
    """PlantUse as a Groq strict JSON schema: every field required, optional ones nullable."""
    props = {}
    for name, f in PlantUse.model_fields.items():
        kind = "integer" if f.annotation is int else "string"
        props[name] = {"type": kind if f.is_required() else [kind, "null"], "description": f.description or name}
    record = {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}
    return {"type": "object", "properties": {"records": {"type": "array", "items": record}},
            "required": ["records"], "additionalProperties": False}


def _call_groq(text: str, retries: int = 6) -> list[dict]:
    body = {
        "model": GROQ_EXTRACT_MODEL,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": f"Extract all plant-use records from:\n{text}"}],
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "extraction", "strict": True, "schema": _strict_schema()}},
        "temperature": 0,
        "reasoning_effort": "low",
        "max_completion_tokens": 5000,
    }
    for attempt in range(retries):
        r = requests.post(GROQ_URL, json=body, timeout=120,
                          headers={"Authorization": f"Bearer {GROQ_API_KEY}"})
        if r.status_code == 429 or r.status_code >= 500:  # free-tier rate limit: wait and retry
            wait = float(r.headers.get("retry-after") or 10 * (attempt + 1))
            print(f"  extract: Groq {r.status_code}, waiting {wait:.0f}s")
            time.sleep(min(wait, 90))
            continue
        r.raise_for_status()
        choice = r.json()["choices"][0]
        if choice.get("finish_reason") == "length":
            print("  extract: output hit max tokens; lower GROQ_PAGES_PER_CALL")
        try:
            parsed = Extraction.model_validate_json(choice["message"]["content"] or "{}")
        except ValidationError:
            print("  extract: Groq returned invalid records for this chunk, skipping")
            return []
        return [{**rec.model_dump(), "record_origin": "AI Extracted"} for rec in parsed.records]
    raise RuntimeError("Groq rate limit: too many retries. Wait a minute and try again.")


def _flat(text: str) -> str:
    s = unicodedata.normalize("NFKC", text or "").lower()
    s = re.sub(r"-\s*\n\s*", "", s)  # words split across lines
    return " ".join(s.split())


def grounded(records: list[dict], pages: list[str]) -> list[dict]:
    """Keep records whose page exists and whose quote is found on that page."""
    kept = []
    for rec in records:
        page = rec.get("page")
        if not isinstance(page, int) or not 1 <= page <= len(pages):
            continue
        quote, text = _flat(rec.get("quote")), _flat(pages[page - 1])
        if quote and fuzz.partial_ratio(quote, text) >= QUOTE_MATCH:
            kept.append(rec)
    if len(kept) < len(records):
        print(f"  extract: dropped {len(records) - len(kept)} records whose page or quote did not match")
    return kept


def _call_llm(text: str) -> list[dict]:
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "medium"},
        system=SYSTEM,
        messages=[{"role": "user", "content": f"Extract all plant-use records from:\n{text}"}],
        output_format=Extraction,
    )
    if response.stop_reason == "refusal":
        print("  extract: model declined this chunk, skipping")
        return []
    if response.stop_reason == "max_tokens":
        print("  extract: output hit max_tokens; lower PAGES_PER_CALL")
    return [{**r.model_dump(), "record_origin": "AI Extracted"} for r in response.parsed_output.records]


def extract_doc(doc_id: str, pages: list[str]) -> list[dict]:
    path = CACHE / "extract" / f"{doc_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    which = provider()
    if OFFLINE or which is None:
        print(f"  extract: no cache and no API key (GROQ_API_KEY) for {doc_id}, skipping")
        return []
    records = []
    if which == "groq":
        for chunk in _chunks(pages, GROQ_PAGES_PER_CALL):
            records.extend(_call_groq(chunk))
    else:
        for chunk in _chunks(pages):
            records.extend(_call_llm(chunk))
    records = grounded(records, pages)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    return records


def run(docs: dict[str, list[str]]) -> dict[str, list[dict]]:
    out = {doc_id: extract_doc(doc_id, pages) for doc_id, pages in docs.items()}
    print(f"extract: {sum(map(len, out.values()))} records")
    return out
