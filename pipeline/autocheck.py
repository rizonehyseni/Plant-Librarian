"""Automatic check of every record against its source PDF. NO AI: text matching only.

For each record with a page: does the page exist, and are the local name, the plant part, the
preparation, the use and the quote found on that page (fuzzy, line breaks and hyphenation
ignored)? The result is stored in `uses.auto_check` as `passed` or `issues`, with the details in
`uses.auto_check_detail`.

This is NOT a human verification: `review_status` is never changed here. A person still confirms
records on the Data quality review page; the automatic check only tells them where to look first.
"""
import re
import unicodedata
from functools import lru_cache

from rapidfuzz import fuzz

from . import ingest
from .config import RAW

FIELD_MATCH = 85      # partial_ratio a field needs to count as found on the page
FIELDS = ("local_name", "part_used", "preparation", "use")
PASSED, ISSUES, NO_PAGE = "passed", "issues", "no page"


def _flat(text: str) -> str:
    s = unicodedata.normalize("NFKD", text or "").lower()
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("ı", "i").replace("‑", "-")
    s = re.sub(r"-\s*\n\s*", "", s)          # words split across lines
    s = re.sub(r"[^\w\s]", " ", s)
    return " ".join(s.split())


@lru_cache(maxsize=16)
def _pages(doc_id: str) -> tuple[str, ...] | None:
    for suffix in (".pdf", ".txt"):
        path = RAW / f"{doc_id}{suffix}"
        if path.exists():
            return tuple(_flat(p) for p in ingest.load_pages(path))
    return None


def _found(value: str | None, page_text: str) -> bool | None:
    """True/False, or None when the field is empty or is a placeholder the study does not print."""
    v = _flat(value or "")
    v = v.replace("amount", "").strip()
    if not v or v in {"not stated", "unknown"}:
        return None
    parts = [p for p in re.split(r"\s{2,}|;|,| and ", v) if len(p.strip()) >= 3] or [v]
    return all(fuzz.partial_ratio(p.strip(), page_text) >= FIELD_MATCH for p in parts)


def check_record(rec: dict) -> tuple[str, str]:
    """(status, detail) for one record."""
    page = rec.get("page")
    pages = _pages(rec.get("doc_id") or "")
    if pages is None or page in (None, ""):
        return NO_PAGE, "no source PDF or page (e.g. community contribution)"
    page = int(page)
    if not 1 <= page <= len(pages):
        return ISSUES, f"page {page} does not exist (PDF has {len(pages)})"
    text = pages[page - 1]
    names = [n for n in str(rec.get("local_name") or "").split("/") if n.strip()]
    results = {"local_name": any(_found(n, text) for n in names) if names else None}
    for field in FIELDS[1:]:
        results[field] = _found(rec.get(field), text)
    quote = rec.get("quote") or ""
    pieces = [p for p in quote.split("...") if p.strip()]
    results["quote"] = all(fuzz.partial_ratio(_flat(p), text) >= 80 for p in pieces) if pieces else None
    missing = [f for f, ok in results.items() if ok is False]
    checked = [f for f, ok in results.items() if ok is not None]
    ok = results["local_name"] is not False and len(missing) <= 1 and len(checked) >= 3
    detail = (f"p.{page}: found " + ", ".join(f for f in checked if f not in missing)
              + (f"; not found: {', '.join(missing)}" if missing else ""))
    if results["local_name"] is False:  # maybe the page number is off: say where the name does appear
        elsewhere = [i + 1 for i, other in enumerate(pages) if i + 1 != page and any(_found(n, other) for n in names)]
        if elsewhere:
            detail += f"; local name appears on p.{', '.join(map(str, elsewhere[:3]))}"
    return (PASSED if ok and not (results["quote"] is False and results["local_name"] is False) else ISSUES), detail


def run(conn) -> dict[str, int]:
    """Check every record and store the result. Returns counts per status."""
    rows = [dict(r) for r in conn.execute(
        "SELECT id, doc_id, page, local_name, part_used, preparation, use, quote FROM uses")]
    counts = {PASSED: 0, ISSUES: 0, NO_PAGE: 0}
    updates = []
    for r in rows:
        status, detail = check_record(r)
        counts[status] += 1
        updates.append((status, detail, r["id"]))
    conn.executemany("UPDATE uses SET auto_check = ?, auto_check_detail = ? WHERE id = ?", updates)
    conn.commit()
    return counts
