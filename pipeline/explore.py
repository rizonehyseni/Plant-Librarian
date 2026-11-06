"""Search, filtering and comparison helpers for the plant explorer."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

from .db import initialize
from .names import normalize, seed_names

TRADITIONAL_EVIDENCE = "Traditional use"


def _values(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, (set, list, tuple)):
        return {str(item) for item in value if str(item).strip()}
    return {str(value)} if str(value).strip() else set()


def aliases_by_species() -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = defaultdict(set)
    for alias, species in seed_names().items():
        aliases[species].add(alias)
    return dict(aliases)


def load_records(conn) -> list[dict[str, Any]]:
    """Load all records and enrich each with its existing evidence and safety data."""
    initialize(conn)
    records = [dict(row) for row in conn.execute(
        """
        SELECT uses.*, sources.title AS source_title, sources.url AS source_url
        FROM uses LEFT JOIN sources ON sources.doc_id = uses.doc_id
        WHERE uses.species IS NOT NULL AND uses.doc_id != ?
        ORDER BY uses.id
        """,
        ("sample_fixture",),
    )]
    evidence: dict[str, set[str]] = defaultdict(set)
    for row in conn.execute("SELECT species, study_type FROM evidence WHERE study_type IS NOT NULL"):
        evidence[row["species"]].add(row["study_type"])
    flags: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in conn.execute("SELECT species, kind, level, note, source FROM flags"):
        flags[row["species"]].append(dict(row))
    aliases = aliases_by_species()
    uses_per_species: dict[str, int] = defaultdict(int)
    for record in records:
        uses_per_species[record["species"]] += 1
    for record in records:
        species = record["species"]
        record["aliases"] = aliases.get(species, set())
        record["evidence_types"] = {TRADITIONAL_EVIDENCE, *evidence[species]}
        record["safety_flags"] = flags[species]
        record["safety_levels"] = {flag["level"] for flag in flags[species] if flag.get("level")}
        record["location_label"] = record.get("location") or record.get("place")
        record["use_count"] = uses_per_species[species]
    return records


def filter_options(records: Iterable[Mapping[str, Any]]) -> dict[str, list[str]]:
    rows = list(records)
    return {
        "species": sorted({row["species"] for row in rows if row.get("species")}),
        "parts": sorted({row["part_used"] for row in rows if row.get("part_used")}),
        "preparations": sorted({row["preparation"] for row in rows if row.get("preparation")}),
        "uses": sorted({row["use"] for row in rows if row.get("use")}),
        "locations": sorted({row["location_label"] for row in rows if row.get("location_label")}),
        "evidence": sorted({item for row in rows for item in _values(row.get("evidence_types"))}),
        "safety": sorted({item for row in rows for item in _values(row.get("safety_levels"))}),
        "review_status": sorted({row["review_status"] for row in rows if row.get("review_status")}),
    }


def _matches_query(record: Mapping[str, Any], query: str) -> bool:
    term = normalize(query)
    if len(term) < 2:
        return not term
    fields = (
        record.get("local_name"), record.get("species"), record.get("use"),
        record.get("part_used"), record.get("preparation"), record.get("location_label"),
        *record.get("aliases", ()),
    )
    return any(term in normalize(str(value or "")) for value in fields)


def search_and_filter(
    records: Iterable[Mapping[str, Any]], *, query: str = "", species: Iterable[str] = (),
    parts: Iterable[str] = (), preparations: Iterable[str] = (), uses: Iterable[str] = (),
    locations: Iterable[str] = (), evidence_types: Iterable[str] = (),
    safety_levels: Iterable[str] = (), review_statuses: Iterable[str] = (),
) -> list[Mapping[str, Any]]:
    """Apply an AND combination of selected filters, with OR semantics within each filter."""
    selected = {
        "species": set(species), "parts": set(parts), "preparations": set(preparations),
        "uses": set(uses), "locations": set(locations), "evidence": set(evidence_types),
        "safety": set(safety_levels), "status": set(review_statuses),
    }
    results = []
    for record in records:
        if not _matches_query(record, query):
            continue
        if selected["species"] and record.get("species") not in selected["species"]:
            continue
        if selected["parts"] and record.get("part_used") not in selected["parts"]:
            continue
        if selected["preparations"] and record.get("preparation") not in selected["preparations"]:
            continue
        if selected["uses"] and record.get("use") not in selected["uses"]:
            continue
        if selected["locations"] and record.get("location_label") not in selected["locations"]:
            continue
        if selected["evidence"] and not selected["evidence"].intersection(_values(record.get("evidence_types"))):
            continue
        if selected["safety"] and not selected["safety"].intersection(_values(record.get("safety_levels"))):
            continue
        if selected["status"] and record.get("review_status") not in selected["status"]:
            continue
        results.append(record)
    return results


def sort_records(records: Iterable[Mapping[str, Any]], order: str) -> list[Mapping[str, Any]]:
    rows = list(records)
    if order == "Scientific name":
        return sorted(rows, key=lambda row: (str(row.get("species") or "").lower(), row["id"]))
    if order == "Number of documented uses":
        return sorted(rows, key=lambda row: (-int(row.get("use_count") or 0), str(row.get("species") or "").lower(), row["id"]))
    if order == "Verification status":
        return sorted(rows, key=lambda row: (row.get("review_status") != "Verified", str(row.get("species") or "").lower(), row["id"]))
    return sorted(rows, key=lambda row: (str(row.get("local_name") or "").lower(), row["id"]))


def page_records(records: Iterable[Mapping[str, Any]], page: int, page_size: int = 12) -> tuple[list[Mapping[str, Any]], int]:
    rows = list(records)
    total_pages = max(1, (len(rows) + page_size - 1) // page_size)
    current_page = min(max(page, 1), total_pages)
    start = (current_page - 1) * page_size
    return rows[start:start + page_size], total_pages


def compare_plants(records: Iterable[Mapping[str, Any]], species_names: Iterable[str]) -> list[dict[str, Any]]:
    """Aggregate existing record data for up to three selected plant profiles."""
    selected = list(dict.fromkeys(species_names))[:3]
    comparisons = []
    for species in selected:
        matches = [record for record in records if record.get("species") == species]
        if not matches:
            continue
        first = matches[0]
        comparisons.append({
            "species": species,
            "local_names": sorted({row["local_name"] for row in matches if row.get("local_name")}),
            "uses": sorted({row["use"] for row in matches if row.get("use")}),
            "parts": sorted({row["part_used"] for row in matches if row.get("part_used")}),
            "preparations": sorted({row["preparation"] for row in matches if row.get("preparation")}),
            "locations": sorted({row["location_label"] for row in matches if row.get("location_label")}),
            "evidence_types": sorted({item for row in matches for item in _values(row.get("evidence_types"))}),
            "safety_flags": [flag for row in matches for flag in row.get("safety_flags", ())],
            "review_statuses": sorted({row["review_status"] for row in matches if row.get("review_status")}),
            "source_count": len({row.get("doc_id") for row in matches if row.get("doc_id")}),
            "use_count": first.get("use_count", len(matches)),
        })
    return comparisons
