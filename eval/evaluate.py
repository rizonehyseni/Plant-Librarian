"""Evaluate extraction against real-study gold rows in eval/gold.csv.

Synthetic fixtures are deliberately excluded. A gold row counts as found when the
database has a record from the same document and page with the same local name,
part, preparation and reported use, and the same plant. The plant may be written
as in the study (`name_in_text`, e.g. Chamomilla recutita) or as the GBIF accepted
name the pipeline resolved it to (`species`, e.g. Matricaria chamomilla).

gold.csv is a hand-checked sample, not a full transcription of each study, so
precision cannot be measured: a database record missing from the sample may still be
correct. Records for sampled plants that are not in gold.csv are listed as unchecked.
"""
import csv
from pathlib import Path

from pipeline.db import connect

GOLD = Path(__file__).parent / "gold.csv"
FIELDS = ("doc_id", "page", "local_name", "part_used", "preparation", "use")


def norm(s):
    return " ".join(str(s or "").strip().lower().split())


def binomial(name):
    """'Allium porrum L.' -> 'allium porrum' (drops the author)."""
    return " ".join(norm(name).split()[:2])


def plant_names(r):
    return {binomial(r.get("species")), binomial(r.get("name_in_text"))} - {""}


def key(r):
    return tuple(norm(r.get(f)) for f in FIELDS)


def main():
    gold = [g for g in csv.DictReader(open(GOLD, encoding="utf-8"))
            if g["doc_id"] != "sample_fixture"]
    if not gold:
        raise SystemExit("No real-study gold rows found in eval/gold.csv")
    docs = {g["doc_id"] for g in gold}
    conn = connect()
    rows = [dict(r) for r in conn.execute(
        f"SELECT * FROM uses WHERE doc_id IN ({','.join('?' * len(docs))})", list(docs))]

    by_key = {}
    for r in rows:
        by_key.setdefault(key(r), []).append(r)

    def found(g):
        return any(binomial(g["species"]) in plant_names(r) for r in by_key.get(key(g), []))

    hits = [g for g in gold if found(g)]
    recall = len(hits) / len(gold)

    sampled = {(g["doc_id"], norm(g["local_name"])) for g in gold}
    in_sample = [r for r in rows if (r["doc_id"], norm(r["local_name"])) in sampled]
    gold_by_key = {}
    for g in gold:
        gold_by_key.setdefault(key(g), set()).add(binomial(g["species"]))
    unchecked = [r for r in in_sample if not plant_names(r) & gold_by_key.get(key(r), set())]

    by_local = {}
    for r in rows:
        by_local.setdefault((r["doc_id"], norm(r["local_name"])), set()).update(plant_names(r))
    named = [g for g in gold if (g["doc_id"], norm(g["local_name"])) in by_local]
    name_ok = sum(binomial(g["species"]) in by_local[(g["doc_id"], norm(g["local_name"]))]
                  for g in named)

    print(f"real-study gold records: {len(gold)}   database records in those studies: {len(rows)}")
    print(f"recall: {len(hits)}/{len(gold)} = {recall:.0%}")
    print(f"local name -> plant: {name_ok}/{len(named)} correct")
    for g in gold:
        if not found(g):
            print(f"  missed: p{g['page']} {g['local_name']} -> {g['species']} ({g['part_used']})")
    if unchecked:
        print(f"{len(unchecked)} other record(s) for sampled plants, not in gold.csv (unchecked):")
    for r in unchecked:
        print(f"  p{r['page']} {r['local_name']} -> {r['species']} "
              f"({r['part_used']}, {r['preparation']}, {r['use']})")


if __name__ == "__main__":
    main()
