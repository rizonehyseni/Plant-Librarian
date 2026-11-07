"""Family knowledge shared through the app, with consent. NO AI.

People can add a traditional use they know from their family. Nothing is published until a
reviewer approves it, every entry needs two consents (the person sharing, and the person who
holds the knowledge), names of people are not collected, and doses are refused. Entries live in
data/contributions/contributions.csv so `make build` reproduces the approved ones; an approved
entry can be withdrawn at any time, which removes it from the library.
"""
import csv
import re
from datetime import datetime, timezone

from .config import DATA

PATH = DATA / "contributions" / "contributions.csv"
DOC_ID = "community_contributions"
ORIGIN = "Community Contribution"
FIELDS = ("id", "submitted_at", "local_name", "scientific_name", "part_used", "preparation", "use", "location",
          "knowledge_holder", "language", "consent_share", "consent_holder", "status", "reviewer", "reviewed_at",
          "note")
STATUSES = ("pending", "approved", "rejected", "withdrawn")
SOURCE = {"doc_id": DOC_ID, "title": "Community contributions (shared with consent)",
          "citation": "EthnoHack 2026 family knowledge form; reviewed before publication",
          "url": "", "licence": "CC BY 4.0, given by the contributor", "study_area": ""}
HOLDERS = ("grandmother", "grandfather", "mother", "father", "other relative", "neighbour", "healer", "myself", "other")
# Amounts and schedules: a number followed by a unit, in English or Albanian. Doses are never stored.
DOSE = re.compile(
    r"\d+([.,]\d+)?\s*(-|–|to|deri)?\s*\d*\s*(mg|g|gr|gram|kg|ml|l|litre|liter|litra?|cups?|spoons?|tablespoons?|"
    r"teaspoons?|drops?|times|x|days?|weeks?|filxhan\w*|got\w*|lug\w*|pika|herë|here|ditë|dite|javë|jave)\b",
    re.IGNORECASE)


def has_dose(*texts: str) -> bool:
    return any(DOSE.search(t or "") for t in texts)


def _read() -> list[dict]:
    if not PATH.exists():
        return []
    with open(PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write(rows: list[dict]) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in FIELDS} for r in rows)


def entries(status: str | None = None) -> list[dict]:
    return [r for r in _read() if status is None or r["status"] == status]


def submit(form: dict) -> int:
    """Validate and store one entry as `pending`. Raises ValueError with a reason to show the user."""
    clean = {k: " ".join(str(form.get(k) or "").split()) for k in FIELDS}
    if not clean["local_name"] or not clean["use"]:
        raise ValueError("missing")
    if form.get("consent_share") is not True or form.get("consent_holder") is not True:
        raise ValueError("consent")
    if has_dose(clean["use"], clean["preparation"], clean["part_used"]):
        raise ValueError("dose")
    rows = _read()
    new_id = max((int(r["id"]) for r in rows), default=0) + 1
    rows.append({**clean, "id": new_id, "consent_share": "yes", "consent_holder": "yes", "status": "pending",
                 "submitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "reviewer": "", "reviewed_at": "", "note": ""})
    _write(rows)
    return new_id


def set_status(entry_id: int, status: str, reviewer: str, note: str = "") -> dict:
    if status not in STATUSES:
        raise ValueError("status")
    if not reviewer.strip():
        raise ValueError("reviewer")
    rows = _read()
    for r in rows:
        if int(r["id"]) == int(entry_id):
            r.update(status=status, reviewer=reviewer.strip(), note=note.strip(),
                     reviewed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
            _write(rows)
            return r
    raise KeyError(entry_id)


def as_record(entry: dict) -> dict:
    """An approved entry in the extraction format the build understands."""
    return {
        "local_name": entry["local_name"], "name_in_text": entry.get("scientific_name") or None, "family": None,
        "part_used": entry.get("part_used") or "not stated", "preparation": entry.get("preparation") or "not stated",
        "administration": None, "use": entry["use"], "location": entry.get("location") or None, "page": None,
        "quote": f"Contribution #{entry['id']}: shared with consent"
                 + (f" (knowledge from: {entry['knowledge_holder']})" if entry.get("knowledge_holder") else ""),
        "record_origin": ORIGIN,
    }


def approved_records() -> list[dict]:
    return [as_record(e) for e in entries("approved")]


def publish(conn, entry: dict) -> int:
    """Insert one approved entry into the database now (the build does the same from the CSV)."""
    from . import build
    build._insert(conn, "sources", [SOURCE])
    rows = build.use_rows(DOC_ID, [as_record(entry)], None)
    build._insert(conn, "uses", rows)
    conn.commit()
    return len(rows)


def unpublish(conn, entry_id: int) -> int:
    cur = conn.execute("DELETE FROM uses WHERE doc_id = ? AND quote LIKE ?", (DOC_ID, f"Contribution #{entry_id}:%"))
    conn.commit()
    return cur.rowcount
