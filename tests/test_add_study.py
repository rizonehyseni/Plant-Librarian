import csv
import shutil

import pytest

from pipeline import add_study, build, names
from pipeline.db import connect, initialize

RECORDS = [{
    "local_name": "Çaj mali", "name_in_text": "Sideritis scardica Griseb.", "family": "Lamiaceae",
    "part_used": "aerial parts", "preparation": "infusion", "administration": "oral",
    "use": "cough", "location": "Dragash", "page": 1, "quote": "Çaj mali ... infusion for cough",
}, {
    "local_name": "Kamomil", "name_in_text": None, "family": None, "part_used": "flowers",
    "preparation": "decoction", "administration": None, "use": "stomach ache",
    "location": None, "page": 1, "quote": "Kamomil ... decoction",
}]


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    raw, seed = tmp_path / "raw", tmp_path / "seed"
    raw.mkdir()
    shutil.copytree(add_study.SEED, seed)
    monkeypatch.setattr(add_study, "RAW", raw)
    monkeypatch.setattr(add_study, "SEED", seed)
    monkeypatch.setattr(names, "gbif_match", lambda name: {})  # no network
    enriched = []
    monkeypatch.setattr(build, "enrich", lambda conn, keys: enriched.extend(keys))
    conn = connect(tmp_path / "test.db")
    initialize(conn)
    yield raw, seed, conn, enriched
    conn.close()


META = {"title": "Mustafa et al. 2012", "citation": "J Ethnopharmacol", "url": "", "licence": "CC BY",
        "study_area": "Malet e Sharrit"}


def test_adds_records_places_and_source(workspace):
    raw, seed, conn, enriched = workspace
    calls = []
    result = add_study.add_study(b"page one text", ".txt", META, conn=conn,
                                 extractor=lambda doc_id, pages: calls.append(pages) or RECORDS)

    assert result.doc_id == "mustafa_et_al_2012" and result.records == 2
    assert calls == [["page one text"]]
    assert (raw / "mustafa_et_al_2012.txt").exists()
    rows = {r["local_name"]: dict(r) for r in conn.execute("SELECT * FROM uses")}
    assert rows["Çaj mali"]["place"] == "Dragash" and rows["Çaj mali"]["geo_precision"] == "record"
    assert rows["Kamomil"]["geo_precision"] == "study"  # no village: study area
    assert rows["Kamomil"]["species"]  # resolved through the seed dictionary
    assert rows["Çaj mali"]["record_origin"] == "AI Extracted"
    assert result.located == {"record": 1, "study": 1, "none": 0}
    assert sorted(enriched) == result.new_species
    with open(seed / "sources.csv", encoding="utf-8") as f:
        assert "mustafa_et_al_2012" in {r["doc_id"] for r in csv.DictReader(f)}


def test_duplicate_id_and_bad_type_are_rejected(workspace):
    _, _, conn, _ = workspace
    with pytest.raises(ValueError, match="already exists"):
        add_study.add_study(b"x", ".txt", {**META, "doc_id": "cross_cultural_sharr_2015"}, conn=conn,
                            extractor=lambda *a: RECORDS)
    with pytest.raises(ValueError, match="PDF"):
        add_study.add_study(b"x", ".docx", META, conn=conn, extractor=lambda *a: RECORDS)


def test_no_records_leaves_nothing_behind(workspace):
    raw, seed, conn, _ = workspace
    before = (seed / "sources.csv").read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        add_study.add_study(b"text", ".txt", META, conn=conn, extractor=lambda *a: [])
    assert not list(raw.iterdir())
    assert (seed / "sources.csv").read_text(encoding="utf-8") == before
    assert conn.execute("SELECT COUNT(*) FROM uses").fetchone()[0] == 0


def test_unicode_hyphens_are_stored_as_plain_hyphens():
    from pipeline.build import plain_hyphens
    rec = {"use": "Anti‑diabetic; Anti‐rheumatic", "quote": "x – y", "page": 5}
    assert plain_hyphens(rec) == {"use": "Anti-diabetic; Anti-rheumatic", "quote": "x - y", "page": 5}


def test_amounts_are_removed_but_the_preparation_stays():
    from pipeline.build import no_doses
    rec = {"preparation": "Macerated roots (200-300 g) mixed honey (1 kg)", "page": 9,
           "administration": "2-3 soup spoons in the morning", "use": "Anti-diabetic"}
    assert no_doses(rec) == {"preparation": "Macerated roots [amount] mixed honey [amount]", "page": 9,
                             "administration": "[amount] in the morning", "use": "Anti-diabetic"}
