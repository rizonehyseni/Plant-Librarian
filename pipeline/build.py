"""One command rebuilds everything: `make build` (or `python -m pipeline.build`)."""
import csv

from . import chemistry, evidence, extract, flags, geo, ingest, names
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


def main():
    conn = reset()
    with open(SEED / "sources.csv", encoding="utf-8") as f:
        _insert(conn, "sources", list(csv.DictReader(f)))

    docs = ingest.run()
    extracted = extract.run(docs)

    species_keys: dict[str, int | None] = {}
    use_rows = []
    for doc_id, records in extracted.items():
        for rec in records:
            r = names.resolve(rec)
            r["prep_class"] = evidence.classify_traditional(r["preparation"])
            use_rows.append({"doc_id": doc_id, **{k: r.get(k) for k in (
                "page", "local_name", "name_in_text", "species", "gbif_key", "match_method", "match_score",
                "family", "part_used", "preparation", "prep_class", "administration", "use", "location", "quote")}})
            if r["species"]:
                species_keys.setdefault(r["species"], r["gbif_key"])
    _insert(conn, "uses", use_rows)
    unresolved = sum(1 for r in use_rows if not r["species"])
    print(f"names: {len(species_keys)} species, {unresolved} unresolved records")

    for sp, key in sorted(species_keys.items()):
        _insert(conn, "evidence", _step("evidence", evidence.run, sp))
        _insert(conn, "flags", _step("flags", flags.run, sp))
        _insert(conn, "occurrences", _step("geo", geo.occurrences, key, sp))
        _insert(conn, "compounds", _step("chemistry", chemistry.run, sp))
        print(f"  done {sp}")

    conn.commit()
    print(f"build: wrote {DB_PATH}")


if __name__ == "__main__":
    main()
