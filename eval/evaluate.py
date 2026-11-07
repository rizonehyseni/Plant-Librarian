"""Evaluate extraction against real-study gold rows in eval/gold.csv.

Synthetic fixtures are deliberately excluded. A gold row counts as found when the
database has a record from the same document and page with the same local name,
part, preparation and reported use, and the same plant. An LLM record may list several
uses of one table row separated by ";" or "," ("Anti-diarrhoeal; Stomach pain"); the gold use
must then be one of them. The plant may be written
as in the study (`name_in_text`, e.g. Chamomilla recutita) or as the GBIF accepted
name the pipeline resolved it to (`species`, e.g. Matricaria chamomilla).

gold.csv is a hand-checked sample, not a full transcription of each study, so
precision cannot be measured: a database record missing from the sample may still be
correct. Records for sampled plants that are not in gold.csv are listed as unchecked.
"""
import csv
import re
from pathlib import Path

from pipeline.db import connect

GOLD = Path(__file__).parent / "gold.csv"
FIELDS = ("doc_id", "page", "part_used", "preparation")


def norm(s):
    return " ".join(str(s or "").strip().lower().split())


def binomial(name):
    """'Allium porrum L.' -> 'allium porrum' (drops the author)."""
    return " ".join(norm(name).split()[:2])


def plant_names(r):
    return {binomial(r.get("species")), binomial(r.get("name_in_text"))} - {""}


def key(r):
    fields = tuple(norm(r.get(f)) for f in FIELDS)
    return fields + (norm(r.get("community") or "Albanian"),)


def uses(r):
    """The whole `use` text and each part of it separated by ";" or ","."""
    text = str(r.get("use") or "")
    return {norm(text)} | {norm(u) for u in re.split(r"[;,]", text)} - {""}


def matches(g, r):
    """Gold row g and database record r name the same plant, local name and use."""
    return (binomial(g["species"]) in plant_names(r) and norm(g["local_name"]) in local_names(r)
            and norm(g["use"]) in uses(r))


def local_names(r):
    return {norm(name) for name in str(r.get("local_name") or "").split("/") if norm(name)}


def evaluate(conn=None, gold_path=GOLD):
    """Recall of the gold rows in the database; returns counts and the missed/unchecked rows."""
    with open(gold_path, encoding="utf-8") as f:
        gold = [g for g in csv.DictReader(f) if g["doc_id"] != "sample_fixture"]
    if not gold:
        raise SystemExit("No real-study gold rows found in eval/gold.csv")
    docs = {g["doc_id"] for g in gold}
    conn = conn or connect()
    rows = [dict(r) for r in conn.execute(
        f"SELECT * FROM uses WHERE doc_id IN ({','.join('?' * len(docs))})", list(docs))]

    by_key = {}
    for r in rows:
        by_key.setdefault(key(r), []).append(r)

    def found(g):
        return any(matches(g, r) for r in by_key.get(key(g), []))

    hits = [g for g in gold if found(g)]
    recall = len(hits) / len(gold)

    sampled = {(g["doc_id"], norm(g["local_name"])) for g in gold}
    in_sample = [r for r in rows if any((r["doc_id"], alias) in sampled for alias in local_names(r))]
    gold_by_key = {}
    for g in gold:
        gold_by_key.setdefault(key(g), []).append(g)
    unchecked = [r for r in in_sample if not any(matches(g, r) for g in gold_by_key.get(key(r), []))]

    by_local = {}
    for r in rows:
        for alias in local_names(r):
            by_local.setdefault((r["doc_id"], alias), set()).update(plant_names(r))
    named = [g for g in gold if (g["doc_id"], norm(g["local_name"])) in by_local]
    name_ok = sum(binomial(g["species"]) in by_local[(g["doc_id"], norm(g["local_name"]))]
                  for g in named)

    per_doc = {d: (sum(g["doc_id"] == d for g in hits), sum(g["doc_id"] == d for g in gold))
               for d in sorted(docs)}
    return {"gold": len(gold), "rows": len(rows), "hits": len(hits), "recall": recall, "per_doc": per_doc,
            "name_ok": name_ok, "named": len(named),
            "missed": [g for g in gold if not found(g)], "unchecked": unchecked}


def main():
    res = evaluate()
    print(f"real-study gold records: {res['gold']}   database records in those studies: {res['rows']}")
    print(f"recall: {res['hits']}/{res['gold']} = {res['recall']:.0%}")
    for doc, (hit, total) in res["per_doc"].items():
        print(f"  {doc}: {hit}/{total}")
    print(f"local name -> plant: {res['name_ok']}/{res['named']} correct")
    for g in res["missed"]:
        print(f"  missed: p{g['page']} {g['local_name']} -> {g['species']} ({g['part_used']})")
    unchecked = res["unchecked"]
    if unchecked:
        print(f"{len(unchecked)} other record(s) for sampled plants, not in gold.csv (unchecked):")
    for r in unchecked:
        print(f"  p{r['page']} {r['local_name']} -> {r['species']} "
              f"({r['part_used']}, {r['preparation']}, {r['use']})")


if __name__ == "__main__":
    main()
