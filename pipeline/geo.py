"""Where the species grows: GBIF occurrence records in Kosovo and Albania, for the map."""
import requests

from .cache import cached


def occurrences(gbif_key: int | None, species: str, limit: int = 150) -> list[dict]:
    if not gbif_key:
        return []

    def fetch():
        r = requests.get("https://api.gbif.org/v1/occurrence/search", timeout=30, params={
            "taxonKey": gbif_key, "country": ["XK", "AL", "MK"], "hasCoordinate": "true", "limit": limit,
        })
        r.raise_for_status()
        return [{"lat": o["decimalLatitude"], "lon": o["decimalLongitude"], "year": o.get("year")}
                for o in r.json().get("results", [])]

    return [{"species": species, **o} for o in (cached("gbif_occ", str(gbif_key), fetch) or [])]
