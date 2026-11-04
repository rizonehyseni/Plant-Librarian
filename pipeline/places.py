"""Where a use was recorded: turn the free-text `location` of a record into map coordinates.

NO LLM and no network here: a small hand-checked gazetteer (data/seed/places.csv) with
Albanian, definite and Slavic spellings of each place. Order of matching:
exact name -> place name inside a longer phrase ("village near Dragash") -> fuzzy word.
If the record itself names no known place, the study area from sources.csv is used and
the record is marked as located only at study level, so the map never claims more
precision than the source gives.
"""
import csv
import re
import unicodedata
from functools import lru_cache

from rapidfuzz import fuzz, process

from .config import SEED

FUZZY_THRESHOLD = 85
MIN_PHRASE_LEN = 4  # short aliases ("Has") are only matched exactly, never inside a phrase


def normalize(text: str) -> str:
    """Lowercase, strip diacritics (ë->e, ç->c, š->s) and punctuation."""
    s = unicodedata.normalize("NFKD", (text or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("đ", "dj")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


@lru_cache(maxsize=1)
def gazetteer() -> dict[str, dict]:
    """Normalised name or alias -> place row (name, lat, lon, country, kind)."""
    index: dict[str, dict] = {}
    with open(SEED / "places.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            place = {"place": r["place"], "lat": float(r["lat"]), "lon": float(r["lon"]),
                     "country": r["country"], "kind": r["kind"]}
            for name in [r["place"], *filter(None, r["aliases"].split("|"))]:
                index.setdefault(normalize(name), place)
    return index


def locate(text: str | None) -> dict | None:
    """Best place for a location string, or None. Adds `geo_method` and `geo_score`."""
    key = normalize(text or "")
    if not key:
        return None
    index = gazetteer()

    if key in index:
        return {**index[key], "geo_method": "exact", "geo_score": 100.0}

    # Longest alias first, so "malet e sharrit" wins over "sharrit".
    for alias in sorted(index, key=len, reverse=True):
        if len(alias) >= MIN_PHRASE_LEN and re.search(rf"\b{re.escape(alias)}\b", key):
            return {**index[alias], "geo_method": "phrase", "geo_score": 100.0}

    # Dialect / case endings not in the list: "Prizrendi", "Dragashe".
    candidates = [a for a in index if len(a) >= MIN_PHRASE_LEN]
    best = None
    for word in key.split():
        if len(word) < MIN_PHRASE_LEN:
            continue
        hit = process.extractOne(word, candidates, scorer=fuzz.ratio)
        if hit and hit[1] >= FUZZY_THRESHOLD and (best is None or hit[1] > best[1]):
            best = hit
    if best:
        return {**index[best[0]], "geo_method": "fuzzy", "geo_score": float(best[1])}
    return None


def locate_record(location: str | None, study_area: str | None) -> dict:
    """Coordinates for one use record, falling back to the study area.

    `geo_precision` is "record" when the record names the place, "study" when only the
    study area is known, and None when neither can be placed on the map.
    """
    hit = locate(location)
    precision = "record"
    if hit is None:
        hit, precision = locate(study_area), "study"
    if hit is None:
        return {"place": None, "lat": None, "lon": None, "geo_precision": None}
    return {"place": hit["place"], "lat": hit["lat"], "lon": hit["lon"], "geo_precision": precision}
