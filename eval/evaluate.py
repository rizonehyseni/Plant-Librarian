"""Accuracy against the hand-checked gold sample in eval/gold.csv.

A gold row counts as found when the database has a record from the same document
with the same species and the same part used. Reports precision, recall and
name-matching accuracy - put these numbers in the slides.
"""
import csv
from pathlib import Path

from pipeline.db import connect

GOLD = Path(__file__).parent / "gold.csv"


def norm(s):
    return (s or "").strip().lower()


def main():
    gold = list(csv.DictReader(open(GOLD, encoding="utf-8")))
    docs = {g["doc_id"] for g in gold}
    conn = connect()
    rows = [dict(r) for r in conn.execute(
        f"SELECT * FROM uses WHERE doc_id IN ({','.join('?' * len(docs))})", list(docs))]

    key = lambda r: (r["doc_id"], norm(r["species"]), norm(r["part_used"]))
    gold_keys = {key(g) for g in gold}
    pred_keys = {key(r) for r in rows}
    tp = len(gold_keys & pred_keys)
    precision = tp / len(pred_keys) if pred_keys else 0
    recall = tp / len(gold_keys) if gold_keys else 0

    by_local = {(r["doc_id"], norm(r["local_name"])): norm(r["species"]) for r in rows}
    named = [g for g in gold if (g["doc_id"], norm(g["local_name"])) in by_local]
    name_acc = sum(by_local[(g["doc_id"], norm(g["local_name"]))] == norm(g["species"]) for g in named)

    print(f"gold records: {len(gold)}   extracted: {len(rows)}")
    print(f"precision: {precision:.0%}   recall: {recall:.0%}")
    print(f"name matching: {name_acc}/{len(named)} correct")
    for g in gold:
        if key(g) not in pred_keys:
            print(f"  missed: {g['local_name']} -> {g['species']} ({g['part_used']})")


if __name__ == "__main__":
    main()
