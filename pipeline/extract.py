"""Step 2: the LLM reads each study and returns structured plant-use records.

The LLM is used ONLY here, to turn unstructured text into rows. Every row keeps the
page number and a short verbatim quote, so it can be checked against the source.
Results are cached in data/cache/extract/<doc_id>.json; delete a file to re-extract.
"""
import json
from typing import List, Optional

from pydantic import BaseModel, Field

from .config import ANTHROPIC_API_KEY, CACHE, MODEL, OFFLINE

PAGES_PER_CALL = 8


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


def _chunks(pages: list[str]):
    for start in range(0, len(pages), PAGES_PER_CALL):
        block = pages[start:start + PAGES_PER_CALL]
        yield "".join(f"\n[page {start + i + 1}]\n{p}" for i, p in enumerate(block))


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
    return [r.model_dump() for r in response.parsed_output.records]


def extract_doc(doc_id: str, pages: list[str]) -> list[dict]:
    path = CACHE / "extract" / f"{doc_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    if OFFLINE or not ANTHROPIC_API_KEY:
        print(f"  extract: no cache and no API key for {doc_id}, skipping")
        return []
    records = []
    for chunk in _chunks(pages):
        records.extend(_call_llm(chunk))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    return records


def run(docs: dict[str, list[str]]) -> dict[str, list[dict]]:
    out = {doc_id: extract_doc(doc_id, pages) for doc_id, pages in docs.items()}
    print(f"extract: {sum(map(len, out.values()))} records")
    return out
