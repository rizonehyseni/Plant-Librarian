"""Summaries for the map page: where uses were recorded and which plants communities share.

No AI and no network: plain counts over the `uses` table.
"""
from collections import defaultdict


def place_summary(rows: list[dict]) -> list[dict]:
    """One entry per mapped place: record count, plants, communities, studies, precision."""
    places: dict[tuple, dict] = {}
    for r in rows:
        if r.get("lat") is None or r.get("lon") is None:
            continue
        k = (r.get("place") or "Unnamed place", float(r["lat"]), float(r["lon"]), r.get("geo_precision"))
        p = places.setdefault(k, {"place": k[0], "lat": k[1], "lon": k[2], "precision": k[3], "records": 0,
                                  "plants": defaultdict(int), "communities": set(), "studies": set()})
        p["records"] += 1
        if r.get("species"):
            p["plants"][r["species"]] += 1
        if r.get("community"):
            p["communities"].add(r["community"])
        p["studies"].add(r.get("doc_id"))
    out = []
    for p in places.values():
        top = sorted(p["plants"].items(), key=lambda kv: (-kv[1], kv[0]))
        out.append({**p, "plants": len(top), "top_plants": [name for name, _ in top[:8]],
                    "communities": sorted(p["communities"]), "studies": sorted(s for s in p["studies"] if s)})
    return sorted(out, key=lambda p: -p["records"])


def community_overlap(rows: list[dict]) -> dict:
    """Which plants each community uses, and how many are shared by all, some, or one."""
    by_plant: dict[str, set] = defaultdict(set)
    for r in rows:
        if r.get("species") and r.get("community"):
            by_plant[r["species"]].add(r["community"])
    communities = sorted({c for cs in by_plant.values() for c in cs})
    shared_all = sorted(sp for sp, cs in by_plant.items() if len(cs) == len(communities) and communities)
    only = {c: sorted(sp for sp, cs in by_plant.items() if cs == {c}) for c in communities}
    some = sorted(sp for sp, cs in by_plant.items() if 1 < len(cs) < len(communities))
    per_community = {c: sum(c in cs for cs in by_plant.values()) for c in communities}
    return {"communities": communities, "per_community": per_community, "shared_all": shared_all,
            "shared_some": some, "only": only, "plants": len(by_plant)}
