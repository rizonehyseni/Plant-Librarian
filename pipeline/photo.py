"""Identify a plant from a photo with the Pl@ntNet API, then match it to the library.

Pl@ntNet is free for non-commercial use (an account gives an API key with a daily quota, see
https://my.plantnet.org/). The photo is sent only when the user takes or uploads one and is not
stored here. Pl@ntNet's result is a suggestion with a confidence score: the app shows it as
such and never as a confirmed identification.
"""
import os

import requests

from . import config  # noqa: F401  (loads .env before the key is read)

PLANTNET_URL = "https://my-api.plantnet.org/v2/identify/{project}"
PLANTNET_API_KEY = os.getenv("PLANTNET_API_KEY", "")
PROJECT = os.getenv("PLANTNET_PROJECT", "all")
ORGANS = ("auto", "leaf", "flower", "fruit", "bark")


def identify(image: bytes, organ: str = "auto", filename: str = "plant.jpg", lang: str = "en",
             api_key: str | None = None, top: int = 5) -> list[dict]:
    """Top Pl@ntNet suggestions: [{species, genus, family, common_names, score, gbif_key}]."""
    key = PLANTNET_API_KEY if api_key is None else api_key
    if not key:
        raise RuntimeError("PLANTNET_API_KEY is not set. Get a free key at https://my.plantnet.org/ and add it to .env.")
    organ = organ if organ in ORGANS else "auto"
    r = requests.post(PLANTNET_URL.format(project=PROJECT), timeout=60,
                      params={"api-key": key, "lang": lang, "nb-results": top},
                      files=[("images", (filename, image, "image/jpeg"))], data={"organs": organ})
    if r.status_code == 404:  # Pl@ntNet answers 404 when no species matches the photo
        return []
    if r.status_code == 429:
        raise RuntimeError("Pl@ntNet daily quota reached. Try again tomorrow.")
    if not r.ok:
        raise RuntimeError(f"Pl@ntNet error {r.status_code}: {r.text[:200]}")
    out = []
    for res in r.json().get("results", [])[:top]:
        sp = res.get("species") or {}
        out.append({
            "species": sp.get("scientificNameWithoutAuthor") or "",
            "genus": ((sp.get("genus") or {}).get("scientificNameWithoutAuthor")) or "",
            "family": ((sp.get("family") or {}).get("scientificNameWithoutAuthor")) or "",
            "common_names": sp.get("commonNames") or [],
            "score": float(res.get("score") or 0),
            "gbif_key": (res.get("gbif") or {}).get("id"),
        })
    return out


def match_library(suggestions: list[dict], library: list[str]) -> list[dict]:
    """Add `match` ('species' | 'genus' | None) and `library_species` (names in the library) to each suggestion."""
    by_species = {s.lower(): s for s in library}
    by_genus: dict[str, list[str]] = {}
    for s in library:
        by_genus.setdefault(s.split()[0].lower(), []).append(s)
    out = []
    for sug in suggestions:
        name = " ".join(sug["species"].split()[:2]).lower()
        if name in by_species:
            out.append({**sug, "match": "species", "library_species": [by_species[name]]})
        elif sug["genus"].lower() in by_genus:
            out.append({**sug, "match": "genus", "library_species": sorted(by_genus[sug["genus"].lower()])})
        else:
            out.append({**sug, "match": None, "library_species": []})
    return out
