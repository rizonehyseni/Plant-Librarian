"""Add one new study to an existing database without a full rebuild.

This is the "give it a study it has never seen" step: the file is saved to data/raw,
its metadata appended to data/seed/sources.csv (so `make build` reproduces it later),
the LLM (Groq, free) extracts the plant-use records (cached in data/cache/extract/<doc_id>.json),
and the records go through the same name, preparation and place steps as the build.
Only species that are new to the database are enriched with evidence, flags and maps.
"""
import csv
import re
import unicodedata
from dataclasses import dataclass, field

from . import build, extract, ingest
from .config import RAW, SEED
from .db import connect, initialize

SOURCE_FIELDS = ("doc_id", "title", "citation", "url", "licence", "study_area")
ALLOWED_SUFFIXES = {".pdf", ".txt"}


@dataclass
class AddResult:
    doc_id: str
    pages: int
    records: int
    species: list[str] = field(default_factory=list)
    new_species: list[str] = field(default_factory=list)
    located: dict[str, int] = field(default_factory=dict)


def slugify(text: str) -> str:
    """'Mustafa et al. 2012' -> 'mustafa_et_al_2012' (safe as a file name and doc_id)."""
    s = unicodedata.normalize("NFKD", text.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")[:60]


def known_doc_ids() -> set[str]:
    with open(SEED / "sources.csv", encoding="utf-8") as f:
        return {r["doc_id"] for r in csv.DictReader(f)}


def _append_source(meta: dict) -> None:
    path = SEED / "sources.csv"
    text = path.read_text(encoding="utf-8")
    with open(path, "a", encoding="utf-8", newline="") as f:
        if text and not text.endswith("\n"):
            f.write("\n")
        csv.DictWriter(f, fieldnames=SOURCE_FIELDS, lineterminator="\n").writerow(meta)


def add_study(file_bytes: bytes, suffix: str, meta: dict, conn=None, extractor=None) -> AddResult:
    """Save, extract and insert one study. `meta` holds the sources.csv fields.

    Raises ValueError for a bad file type or a doc_id that already exists.
    """
    suffix = suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError("Upload a PDF or a plain-text file.")
    doc_id = slugify(meta.get("doc_id") or meta.get("title") or "")
    if not doc_id:
        raise ValueError("Give the study a short id or a title.")
    if doc_id in known_doc_ids() or any(RAW.glob(f"{doc_id}.*")):
        raise ValueError(f"A study with id '{doc_id}' already exists.")
    meta = {k: (meta.get(k) or "").strip() for k in SOURCE_FIELDS} | {"doc_id": doc_id}

    path = RAW / f"{doc_id}{suffix}"
    path.write_bytes(file_bytes)
    pages = ingest.load_pages(path)
    if not any(p.strip() for p in pages):
        path.unlink()
        raise ValueError("No text found in the file (a scanned PDF needs OCR first).")

    try:
        records = (extractor or extract.extract_doc)(doc_id, pages)
    except Exception:
        path.unlink()
        raise
    if not records:
        path.unlink()
        raise ValueError(
            "No plant-use records were extracted. Set the free GROQ_API_KEY in .env (or add a checked "
            f"extraction at data/cache/extract/{doc_id}.json) and try again.")
    _append_source(meta)

    own_conn = conn is None
    conn = conn or connect()
    initialize(conn)
    build._insert(conn, "sources", [meta])
    rows = build.use_rows(doc_id, records, meta["study_area"])
    build._insert(conn, "uses", rows)
    keys = build.species_keys(rows)
    existing = {r[0] for r in conn.execute("SELECT DISTINCT species FROM evidence")} | {
        r[0] for r in conn.execute("SELECT DISTINCT species FROM uses WHERE doc_id != ?", (doc_id,))}
    new = {sp: k for sp, k in keys.items() if sp not in existing}
    build.enrich(conn, new)
    conn.commit()
    if own_conn:
        conn.close()

    located = {p: sum(1 for r in rows if r["geo_precision"] == p) for p in ("record", "study")}
    located["none"] = len(rows) - sum(located.values())
    return AddResult(doc_id, len(pages), len(rows), sorted(keys), sorted(new), located)
