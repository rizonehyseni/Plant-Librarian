"""Step 3: link local (dialect) names to accepted scientific names.

Order: scientific name given in the study -> seed dictionary (exact, then fuzzy) -> unresolved.
Every scientific name is then confirmed with the GBIF species-match API.
"""
import csv
import unicodedata
from functools import lru_cache

import requests
from rapidfuzz import fuzz, process

from .cache import cached
from .config import SEED

FUZZY_THRESHOLD = 85


def normalize(name: str) -> str:
    """Lowercase, strip diacritics (ë->e, ç->c) and the Albanian definite suffixes."""
    s = unicodedata.normalize("NFKD", name.lower().strip())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = " ".join(s.replace("-", " ").split())
    for suffix in ("it", "ja", "i", "a", "et", "te"):
        # 'kamomili' -> 'kamomil', 'sherebela' -> 'sherebel'; only on longer words
        words = s.split()
        if words and len(words[0]) > 5 and words[0].endswith(suffix):
            words[0] = words[0][: -len(suffix)]
            s = " ".join(words)
            break
    return s


@lru_cache(maxsize=1)
def seed_names() -> dict[str, str]:
    with open(SEED / "albanian_names.csv", encoding="utf-8") as f:
        return {normalize(r["local_name"]): r["species"] for r in csv.DictReader(f)}


def match_local(local_name: str) -> tuple[str | None, str, float]:
    names = seed_names()
    key = normalize(local_name)
    if key in names:
        return names[key], "exact", 100.0
    hit = process.extractOne(key, names.keys(), scorer=fuzz.WRatio)
    if hit and hit[1] >= FUZZY_THRESHOLD:
        return names[hit[0]], "fuzzy", float(hit[1])
    return None, "unresolved", float(hit[1]) if hit else 0.0


def gbif_match(scientific_name: str) -> dict:
    def fetch():
        r = requests.get(
            "https://api.gbif.org/v1/species/match",
            params={"name": scientific_name, "kingdom": "Plantae"},
            timeout=20,
        )
        r.raise_for_status()
        return r.json()

    return cached("gbif_match", scientific_name, fetch) or {}


def resolve(record: dict) -> dict:
    method, score = "given", 100.0
    name = record.get("name_in_text")
    if not name:
        name, method, score = match_local(record["local_name"])
    species, key = None, None
    if name:
        try:
            g = gbif_match(name)
        except requests.RequestException as exc:
            print(f"  names: GBIF unreachable for {name} ({type(exc).__name__}); keeping it unconfirmed")
            g = {}
        if g.get("matchType") in {"EXACT", "FUZZY"} and g.get("rank") in {"SPECIES", "SUBSPECIES", "VARIETY"}:
            species = g.get("species") or g.get("canonicalName")
            key = g.get("acceptedUsageKey") or g.get("usageKey")
            record["family"] = record.get("family") or g.get("family")
        else:
            species = name  # keep the name but mark that GBIF did not confirm it
            method += "+unconfirmed"
    return {**record, "species": species, "gbif_key": key, "match_method": method, "match_score": score}
