"""Tiny JSON-on-disk cache so every API call is made once and builds are reproducible."""
import hashlib
import json
from typing import Any, Callable

from .config import CACHE, OFFLINE


def cached(namespace: str, key: str, fetch: Callable[[], Any]) -> Any:
    folder = CACHE / "api" / namespace
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (hashlib.sha1(key.encode()).hexdigest()[:16] + ".json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))["value"]
    if OFFLINE:
        return None
    value = fetch()
    path.write_text(json.dumps({"key": key, "value": value}, ensure_ascii=False, indent=1), encoding="utf-8")
    return value
