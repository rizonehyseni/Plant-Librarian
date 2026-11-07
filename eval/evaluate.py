"""Evaluate extraction against real-study gold rows in eval/gold.csv.

Synthetic fixtures are deliberately excluded. Exact record matching checks the
plant, local name, part, preparation, and reported use, rather than counting a
species/part match as a fully correct record.
"""
import csv
from pathlib import Path

from pipeline.db import connect

GOLD = Path(__file__).parent / "gold.csv"


def norm(s):
    return " ".join((s or "").strip().lower().split())


def main():
    gold = [g for g in csv.DictReader(open(GOLD, encoding="utf-8"))
            if g["doc_id"] != "sample_fixture"]
    if not gold:
        raise SystemExit("No real-study gold rows found in eval/gold.csv")
    docs = {g["doc_id"] for g in gold}
    conn = connect()
    rows = [dict(r) for r in conn.execute(
        f"SELECT * FROM uses WHERE doc_id IN ({','.join('?' * len(docs))})", list(docs))]

    fields = ("doc_id", "local_name", "species", "part_used", "preparation", "use")
    key = lambda r: tuple(norm(r.get(field)) for field in fields)
    gold_keys = {key(g) for g in gold}
    pred_keys = {key(r) for r in rows}
    tp = len(gold_keys & pred_keys)
    precision = tp / len(pred_keys) if pred_keys else 0
    recall = tp / len(gold_keys) if gold_keys else 0

    by_local = {(r["doc_id"], norm(r["local_name"])): norm(r["species"]) for r in rows}
    named = [g for g in gold if (g["doc_id"], norm(g["local_name"])) in by_local]
    name_acc = sum(by_local[(g["doc_id"], norm(g["local_name"]))] == norm(g["species"]) for g in named)

    print(f"real-study gold records: {len(gold)}   extracted: {len(rows)}")
    print(f"exact record precision: {precision:.0%}   recall: {recall:.0%}")
    print(f"local-name species accuracy: {name_acc}/{len(named)} correct")
    for g in gold:
        if key(g) not in pred_keys:
            print(f"  missed: {g['local_name']} -> {g['species']} ({g['part_used']})")


if __name__ == "__main__":
    main()
