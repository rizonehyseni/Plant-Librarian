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

    fields = ("doc_id", "species", "part_used", "preparation", "use")
    def key(row):
        community = row.get("community") or "Albanian"
        return tuple(norm(row.get(field)) for field in fields) + (norm(community),)

    gold_keys = {key(g) for g in gold}
    pred_keys = {key(r) for r in rows}
    aliases = {(key(r), norm(alias))
               for r in rows for alias in str(r.get("local_name") or "").split("/")}
    matched_gold = {key(g) for g in gold if key(g) in pred_keys
                    and (key(g), norm(g["local_name"])) in aliases}
    tp = len(matched_gold)
    precision = tp / len(pred_keys) if pred_keys else 0
    recall = tp / len(gold_keys) if gold_keys else 0

    named = gold
    name_acc = sum((key(g), norm(g["local_name"])) in aliases for g in named)

    print(f"real-study gold records: {len(gold)}   extracted: {len(rows)}")
    print(f"exact record precision: {precision:.0%}   recall: {recall:.0%}")
    print(f"local-name species accuracy: {name_acc}/{len(named)} correct")
    for g in gold:
        if key(g) not in pred_keys:
            print(f"  missed: {g['local_name']} -> {g['species']} ({g['part_used']})")


if __name__ == "__main__":
    main()
