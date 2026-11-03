"""Step 5: safety and conservation flags. NO LLM here: rules file + open databases only."""
import csv

import requests

from .cache import cached
from .config import IUCN_TOKEN, SEED


def risk_flags(species: str) -> list[dict]:
    rows = []
    with open(SEED / "risk_rules.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            target = r["taxon"].strip()
            # a rule can target a species ("Hypericum perforatum") or a whole genus ("Symphytum")
            if species == target or species.split()[0] == target:
                rows.append({"species": species, "kind": "risk", "level": r["level"],
                             "note": r["note"], "source": r["source"]})
    return rows


def iucn_flag(species: str) -> list[dict]:
    """Global IUCN Red List category. Needs IUCN_TOKEN; check the v4 API docs if this changes."""
    if not IUCN_TOKEN:
        return []
    genus, _, epithet = species.partition(" ")

    def fetch():
        r = requests.get(
            "https://api.iucnredlist.org/api/v4/taxa/scientific_name",
            params={"genus_name": genus, "species_name": epithet.split(" ")[0]},
            headers={"Authorization": f"Bearer {IUCN_TOKEN}"}, timeout=30,
        )
        return r.json() if r.ok else {}

    data = cached("iucn", species, fetch) or {}
    assessments = data.get("assessments") or []
    latest = next((a for a in assessments if a.get("latest")), None)
    if not latest:
        return []
    return [{"species": species, "kind": "conservation", "level": latest.get("red_list_category_code", "?"),
             "note": f"IUCN Red List ({latest.get('year_published', '')})",
             "source": f"https://www.iucnredlist.org/species/{data.get('taxon', {}).get('sis_id', '')}"}]


def run(species: str) -> list[dict]:
    return risk_flags(species) + iucn_flag(species)
