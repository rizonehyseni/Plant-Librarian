"""Headline numbers for the slides and the README, computed from data/ethnohack.db.

    python -m eval.stats              # readable text block
    python -m eval.stats --markdown   # also writes docs/numbers.md

Every number comes from the database and the pipeline's own functions
(pipeline.atlas.community_overlap, pipeline.compare.compare_all, eval.evaluate),
never typed by hand. The synthetic fixture (doc_id 'sample_fixture') is excluded.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
from pathlib import Path

from pipeline.atlas import community_overlap
from pipeline.compare import VERDICTS, compare_all
from pipeline.config import DB_PATH, ROOT
from pipeline.db import connect

from .evaluate import GOLD, evaluate

FIXTURE = "sample_fixture"
NUMBERS_MD = ROOT / "docs" / "numbers.md"
GAP_VERDICTS = ("different", "none")


def _count_species(conn, table: str, species: set[str]) -> int:
    found = {r[0] for r in conn.execute(f"SELECT DISTINCT species FROM {table}")}
    return len(found & species)


def compute(conn, gold_path=GOLD, reviewed=None) -> dict:
    """All headline numbers as a dict. `reviewed` is passed to compare_all (None = seed file)."""
    rows = [dict(r) for r in conn.execute(
        "SELECT doc_id, species, community, review_status FROM uses WHERE doc_id != ?", (FIXTURE,))]
    species = {r["species"] for r in rows if r["species"]}
    overlap = community_overlap(rows)

    verdicts = Counter(r["verdict"] for r in compare_all(conn, reviewed=reviewed))
    flags = Counter((r["kind"], r["level"]) for r in conn.execute("SELECT species, kind, level FROM flags")
                    if r["species"] in species)
    flagged = len({r[0] for r in conn.execute("SELECT species FROM flags")} & species)

    try:
        ev = evaluate(conn, gold_path)
    except (SystemExit, FileNotFoundError):
        ev = None

    return {
        "studies": len({r["doc_id"] for r in rows}),
        "records": len(rows),
        "plants": len(species),
        "records_per_community": dict(sorted(Counter(r["community"] or "not stated" for r in rows).items())),
        "communities": overlap["communities"],
        "plants_per_community": overlap["per_community"],
        "shared_all": len(overlap["shared_all"]),
        "shared_all_names": overlap["shared_all"],
        "shared_some": len(overlap["shared_some"]),
        "only": {c: len(v) for c, v in overlap["only"].items()},
        "verdicts": {k: verdicts.get(k, 0) for k in VERDICTS},
        "gaps": sum(verdicts.get(k, 0) for k in GAP_VERDICTS),
        "with_pubmed": _count_species(conn, "evidence", species),
        "with_gbif": _count_species(conn, "occurrences", species),
        "with_compounds": _count_species(conn, "compounds", species),
        "flagged_plants": flagged,
        "flags": {f"{k} / {lvl}": n for (k, lvl), n in sorted(flags.items())},
        "review_status": dict(sorted(Counter(r["review_status"] for r in rows).items())),
        "verified": sum(r["review_status"] == "Verified" for r in rows),
        "eval": None if ev is None else {k: ev[k] for k in ("gold", "hits", "recall", "name_ok", "named")},
    }


def _lines(s: dict) -> list[tuple[str, str]]:
    """(label, value) pairs shared by the text and Markdown output."""
    out = [
        ("Studies", s["studies"]),
        ("Use records", s["records"]),
        ("Plants (accepted species)", s["plants"]),
    ]
    out += [(f"Records, {c}", n) for c, n in s["records_per_community"].items()]
    out += [(f"Plants used by {c}", n) for c, n in s["plants_per_community"].items()]
    out += [
        (f"Plants used by all {len(s['communities'])} communities", s["shared_all"]),
        ("Plants used by some (2+) but not all", s["shared_some"]),
    ]
    out += [(f"Plants used only by {c}", n) for c, n in s["only"].items()]
    out += [(f"Verdict: {VERDICTS[k][0]}", n) for k, n in s["verdicts"].items()]
    out += [
        ("Research gaps (only other preparations + no studies)", s["gaps"]),
        ("Plants with PubMed candidates", f"{s['with_pubmed']} / {s['plants']}"),
        ("Plants with GBIF occurrences", f"{s['with_gbif']} / {s['plants']}"),
        ("Plants with compounds (Wikidata/LOTUS)", f"{s['with_compounds']} / {s['plants']}"),
        ("Plants with a safety flag", s["flagged_plants"]),
    ]
    out += [(f"Flags, {k}", n) for k, n in s["flags"].items()]
    out += [(f"Records {status}", n) for status, n in s["review_status"].items()]
    out.append(("Verified records", s["verified"]))
    ev = s["eval"]
    if ev:
        out += [
            ("Eval recall (hand-checked gold rows)", f"{ev['hits']}/{ev['gold']} = {ev['recall']:.0%}"),
            ("Eval local name -> plant", f"{ev['name_ok']}/{ev['named']}"),
        ]
    else:
        out.append(("Eval recall", "no gold rows"))
    return [(k, str(v)) for k, v in out]


def to_text(s: dict) -> str:
    pairs = _lines(s)
    width = max(len(k) for k, _ in pairs)
    return "\n".join(f"{k:<{width}}  {v}" for k, v in pairs)


def to_markdown(s: dict) -> str:
    rows = "\n".join(f"| {k} | {v} |" for k, v in _lines(s))
    shared = ", ".join(f"*{n}*" for n in s["shared_all_names"]) or "none"
    return (
        "# EthnoHack in numbers\n\n"
        f"Generated by `make stats` (`python -m eval.stats --markdown`) on {date.today().isoformat()} "
        "from `data/ethnohack.db`. Do not edit by hand; rebuild with `OFFLINE=1 make build && make stats`.\n"
        "The synthetic test fixture is excluded.\n\n"
        "| Number | Value |\n| --- | --- |\n"
        f"{rows}\n\n"
        f"Plants used by all communities: {shared}.\n\n"
        "Verdicts are keyword screening of the top PubMed candidates, not a review. Traditional use is not "
        "proof of efficacy.\n"
    )


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--markdown", nargs="?", const=str(NUMBERS_MD), metavar="PATH",
                    help=f"also write Markdown (default {NUMBERS_MD.relative_to(ROOT)})")
    ap.add_argument("--db", default=str(DB_PATH), help="database path")
    args = ap.parse_args(argv)
    db = Path(args.db)
    if not db.exists():
        raise SystemExit(f"No database at {db}. Run `make build` first.")
    conn = connect(db)
    try:
        s = compute(conn)
    finally:
        conn.close()
    print(to_text(s))
    if args.markdown:
        out = Path(args.markdown)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(to_markdown(s), encoding="utf-8")
        print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
