"""One command rebuilds everything: `make build` (or `python -m pipeline.build`)."""
import csv

from . import chemistry, evidence, extract, flags, geo, ingest, names, places
from .config import DB_PATH, SEED
from .db import reset


def _insert(conn, table: str, rows: list[dict]):
    if not rows:
        return
    cols = list(rows[0].keys())
    conn.executemany(
        f"INSERT OR IGNORE INTO {table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
        [tuple(r[c] for c in cols) for r in rows],
    )


def _step(label: str, fn, *args) -> list[dict]:
    """Network steps must never kill the build; log and carry on."""
    try:
        return fn(*args)
    except Exception as exc:  # noqa: BLE001
        print(f"  {label}: skipped ({type(exc).__name__}: {str(exc)[:80]})")
        return []


USE_COLUMNS = (
    "page", "local_name", "name_in_text", "community", "species", "gbif_key", "match_method", "match_score",
    "family", "part_used", "preparation", "prep_class", "administration", "use", "location",
    "place", "lat", "lon", "geo_precision", "quote")


def use_rows(doc_id: str, records: list[dict], study_area: str | None) -> list[dict]:
    """Extracted records of one study -> rows for the `uses` table (names, prep class, place)."""
    rows = []
    for rec in records:
        r = names.resolve(rec)
        r["prep_class"] = evidence.classify_traditional(r["preparation"])
        r.update(places.locate_record(r.get("location"), study_area))
        rows.append({"doc_id": doc_id, **{k: r.get(k) for k in USE_COLUMNS},
                     "record_origin": rec.get("record_origin") or "AI Extracted"})
    return rows


def enrich(conn, species_keys: dict[str, int | None]) -> None:
    """Evidence, flags, occurrences and compounds for each species (network steps, cached)."""
    for sp, key in sorted(species_keys.items()):
        _insert(conn, "evidence", _step("evidence", evidence.run, sp))
        _insert(conn, "flags", _step("flags", flags.run, sp))
        _insert(conn, "occurrences", _step("geo", geo.occurrences, key, sp))
        _insert(conn, "compounds", _step("chemistry", chemistry.run, sp))
        print(f"  done {sp}")


def species_keys(rows: list[dict]) -> dict[str, int | None]:
    keys: dict[str, int | None] = {}
    for r in rows:
        if r["species"]:
            keys.setdefault(r["species"], r["gbif_key"])
    return keys


def main():
    conn = reset()
    with open(SEED / "sources.csv", encoding="utf-8") as f:
        sources = list(csv.DictReader(f))
    _insert(conn, "sources", sources)
    study_area = {s["doc_id"]: s.get("study_area") for s in sources}

    docs = ingest.run()
    extracted = extract.run(docs)

    rows = [row for doc_id, records in extracted.items()
            for row in use_rows(doc_id, records, study_area.get(doc_id))]
    _insert(conn, "uses", rows)
    keys = species_keys(rows)
    unresolved = sum(1 for r in rows if not r["species"])
    print(f"names: {len(keys)} species, {unresolved} unresolved records")
    located = {p: sum(1 for r in rows if r["geo_precision"] == p) for p in ("record", "study")}
    print(f"places: {located['record']} records located by village/town, "
          f"{located['study']} by study area, {len(rows) - sum(located.values())} not on the map")

    enrich(conn, keys)
    conn.commit()
    print(f"build: wrote {DB_PATH}")


if __name__ == "__main__":
    main()
