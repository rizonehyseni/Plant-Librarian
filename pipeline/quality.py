"""Data quality checks and review persistence for plant-use records."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from .db import initialize

REVIEW_STATUSES = ("Needs Review", "Verified")
RECORD_ORIGINS = ("AI Extracted", "Source Table", "Manually Reviewed")
EDITABLE_FIELDS = {
    "local_name", "name_in_text", "species", "family", "part_used", "preparation",
    "administration", "use", "location", "place", "lat", "lon", "geo_precision",
    "quote", "page", "review_status", "reviewer_note", "record_origin",
}

ISSUE_LABELS = {
    "missing_citation": "The source has no citation URL.",
    "invalid_citation": "The source citation URL is not a valid HTTP(S) link.",
    "missing_source": "The linked source is missing its title or citation metadata.",
    "unresolved_scientific_name": "The scientific plant name is unresolved or unconfirmed.",
    "unconfirmed_local_name": "The local plant name was matched fuzzily or could not be matched.",
    "missing_preparation": "No preparation method is recorded.",
    "missing_plant_part": "No plant part is recorded.",
    "missing_location": "No specific record location is available.",
    "potential_duplicate": "This record has the same plant, use, part and preparation as another record in the same source.",
}


def _blank(value: Any) -> bool:
    return value is None or not str(value).strip()


def _valid_url(value: Any) -> bool:
    if _blank(value):
        return False
    parsed = urlparse(str(value).strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _normal(value: Any) -> str:
    return " ".join(str(value or "").lower().split())


def _duplicate_ids(records: Iterable[Mapping[str, Any]]) -> set[int]:
    groups: dict[tuple[str, str, str, str, str], list[int]] = {}
    for record in records:
        key = tuple(_normal(record.get(field)) for field in (
            "doc_id", "species", "use", "part_used", "preparation"
        ))
        if any(key[1:]):
            groups.setdefault(key, []).append(int(record["id"]))
    return {record_id for group in groups.values() if len(group) > 1 for record_id in group}


def check_records(records: Iterable[Mapping[str, Any]]) -> dict[int, list[str]]:
    """Return warning codes for each record without changing the database."""
    rows = list(records)
    duplicates = _duplicate_ids(rows)
    findings: dict[int, list[str]] = {}
    for record in rows:
        issues: list[str] = []
        if _blank(record.get("source_url")):
            issues.append("missing_citation")
        elif not _valid_url(record.get("source_url")):
            issues.append("invalid_citation")
        if _blank(record.get("source_title")) or _blank(record.get("source_citation")):
            issues.append("missing_source")
        match_method = _normal(record.get("match_method"))
        if _blank(record.get("species")) or "unresolved" in match_method or "unconfirmed" in match_method:
            issues.append("unresolved_scientific_name")
        if _blank(record.get("local_name")) or match_method.startswith(("fuzzy", "unresolved")):
            issues.append("unconfirmed_local_name")
        if _blank(record.get("preparation")):
            issues.append("missing_preparation")
        if _blank(record.get("part_used")):
            issues.append("missing_plant_part")
        if record.get("geo_precision") != "record":
            issues.append("missing_location")
        if int(record["id"]) in duplicates:
            issues.append("potential_duplicate")
        findings[int(record["id"])] = issues
    return findings


def issue_messages(codes: Iterable[str]) -> list[str]:
    return [ISSUE_LABELS[code] for code in codes]


def dashboard_metrics(records: Iterable[Mapping[str, Any]], findings: Mapping[int, list[str]]) -> dict[str, int]:
    rows = list(records)
    return {
        "total": len(rows),
        "verified": sum(row.get("review_status") == "Verified" for row in rows),
        "needs_review": sum(row.get("review_status") != "Verified" for row in rows),
        "ai_extracted": sum(row.get("record_origin") == "AI Extracted" for row in rows),
        "missing_citations": sum("missing_citation" in findings[int(row["id"])] or "invalid_citation" in findings[int(row["id"])] for row in rows),
        "unresolved_names": sum("unresolved_scientific_name" in findings[int(row["id"])] for row in rows),
        "without_specific_locations": sum("missing_location" in findings[int(row["id"])] for row in rows),
    }


def fetch_records(conn) -> list[dict[str, Any]]:
    initialize(conn)
    rows = conn.execute(
        """
        SELECT uses.*, sources.title AS source_title, sources.citation AS source_citation,
               sources.url AS source_url
        FROM uses LEFT JOIN sources ON sources.doc_id = uses.doc_id
        ORDER BY uses.id
        """
    ).fetchall()
    return [dict(row) for row in rows]


def filter_records(
    records: Iterable[Mapping[str, Any]], findings: Mapping[int, list[str]], *,
    review_status: str | None = None, species: str | None = None, issue: str | None = None,
) -> list[Mapping[str, Any]]:
    filtered = []
    for record in records:
        if review_status and record.get("review_status") != review_status:
            continue
        if species and record.get("species") != species:
            continue
        if issue and issue not in findings[int(record["id"])]:
            continue
        filtered.append(record)
    return filtered


def _validate_updates(current: Mapping[str, Any], updates: Mapping[str, Any], reviewer: str) -> dict[str, Any]:
    if _blank(reviewer):
        raise ValueError("A local reviewer name is required.")
    unknown = set(updates) - EDITABLE_FIELDS
    if unknown:
        raise ValueError(f"Fields cannot be edited: {', '.join(sorted(unknown))}")
    cleaned = dict(updates)
    if "review_status" in cleaned and cleaned["review_status"] not in REVIEW_STATUSES:
        raise ValueError("Invalid review status.")
    if "record_origin" in cleaned and cleaned["record_origin"] not in RECORD_ORIGINS:
        raise ValueError("Invalid record origin.")
    if "page" in cleaned and cleaned["page"] not in (None, ""):
        try:
            cleaned["page"] = int(cleaned["page"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Page must be a positive whole number.") from exc
        if cleaned["page"] < 1:
            raise ValueError("Page must be a positive whole number.")
    target_status = cleaned.get("review_status", current["review_status"])
    target_origin = cleaned.get("record_origin", current["record_origin"])
    if target_status == "Verified" and target_origin == "AI Extracted":
        raise ValueError("AI-extracted records must be manually reviewed before verification.")
    return cleaned


def save_review(conn, record_id: int, updates: Mapping[str, Any], reviewer: str, note: str = "") -> list[dict[str, Any]]:
    """Validate, persist and audit one local review action."""
    initialize(conn)
    current_row = conn.execute("SELECT * FROM uses WHERE id = ?", (record_id,)).fetchone()
    if current_row is None:
        raise ValueError("Record not found.")
    current = dict(current_row)
    cleaned = _validate_updates(current, updates, reviewer)
    changed = {
        field: value for field, value in cleaned.items()
        if current.get(field) != value
    }
    timestamp = datetime.now(UTC).isoformat(timespec="seconds")
    action = cleaned.get("review_status", current["review_status"])
    if changed:
        assignments = ", ".join(f"{field} = ?" for field in changed)
        conn.execute(f"UPDATE uses SET {assignments} WHERE id = ?", (*changed.values(), record_id))
    audit_rows = []
    for field, value in changed.items():
        audit_rows.append((record_id, field, str(current.get(field) or ""), str(value or ""), timestamp, action, reviewer, note))
    if not audit_rows:
        audit_rows.append((record_id, None, None, None, timestamp, "Review noted", reviewer, note))
    conn.executemany(
        """
        INSERT INTO audit_log (record_id, changed_field, previous_value, new_value, timestamp, action, reviewer, reviewer_note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        audit_rows,
    )
    conn.commit()
    return [dict(row) for row in conn.execute(
        "SELECT * FROM audit_log WHERE record_id = ? ORDER BY id DESC", (record_id,)
    )]


def audit_history(conn, record_id: int) -> list[dict[str, Any]]:
    initialize(conn)
    return [dict(row) for row in conn.execute(
        "SELECT * FROM audit_log WHERE record_id = ? ORDER BY id DESC", (record_id,)
    )]
