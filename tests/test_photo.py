import pytest

from pipeline import photo

PAYLOAD = {"results": [
    {"score": 0.82, "species": {"scientificNameWithoutAuthor": "Urtica dioica", "genus": {"scientificNameWithoutAuthor": "Urtica"},
                                "family": {"scientificNameWithoutAuthor": "Urticaceae"}, "commonNames": ["Stinging nettle"]},
     "gbif": {"id": "5341407"}},
    {"score": 0.07, "species": {"scientificNameWithoutAuthor": "Urtica urens", "genus": {"scientificNameWithoutAuthor": "Urtica"},
                                "family": {"scientificNameWithoutAuthor": "Urticaceae"}, "commonNames": []}},
    {"score": 0.03, "species": {"scientificNameWithoutAuthor": "Lamium album", "genus": {"scientificNameWithoutAuthor": "Lamium"},
                                "family": {"scientificNameWithoutAuthor": "Lamiaceae"}, "commonNames": []}},
]}


class Resp:
    def __init__(self, status, payload=None):
        self.status_code, self._payload, self.ok, self.text = status, payload, status < 400, ""

    def json(self):
        return self._payload


def test_identify_parses_results_and_sends_organ(monkeypatch):
    sent = {}

    def fake_post(url, timeout, params, files, data):
        sent.update(url=url, params=params, data=data, files=files)
        return Resp(200, PAYLOAD)

    monkeypatch.setattr(photo.requests, "post", fake_post)
    res = photo.identify(b"jpg", organ="leaf", api_key="k")
    assert res[0] == {"species": "Urtica dioica", "genus": "Urtica", "family": "Urticaceae",
                      "common_names": ["Stinging nettle"], "score": 0.82, "gbif_key": "5341407"}
    assert sent["params"]["api-key"] == "k" and sent["data"]["organs"] == "leaf"
    assert sent["files"][0][0] == "images"


def test_no_match_quota_and_missing_key(monkeypatch):
    monkeypatch.setattr(photo.requests, "post", lambda *a, **k: Resp(404))
    assert photo.identify(b"x", api_key="k") == []
    monkeypatch.setattr(photo.requests, "post", lambda *a, **k: Resp(429))
    with pytest.raises(RuntimeError, match="quota"):
        photo.identify(b"x", api_key="k")
    with pytest.raises(RuntimeError, match="PLANTNET_API_KEY"):
        photo.identify(b"x", api_key="")


def test_match_library_by_species_then_genus():
    sugs = [{"species": "Urtica dioica", "genus": "Urtica"}, {"species": "Urtica urens", "genus": "Urtica"},
            {"species": "Lamium album", "genus": "Lamium"}]
    m = photo.match_library(sugs, ["Urtica dioica", "Matricaria chamomilla"])
    assert [x["match"] for x in m] == ["species", "genus", None]
    assert m[1]["library_species"] == ["Urtica dioica"]
