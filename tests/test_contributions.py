import sqlite3

import pytest

from pipeline import contributions as c
from pipeline import names
from pipeline.db import initialize

FORM = {"local_name": "Çaj mali", "scientific_name": "", "part_used": "aerial parts", "preparation": "infusion",
        "use": "cough in winter", "location": "Dragash", "knowledge_holder": "grandmother", "language": "sq",
        "consent_share": True, "consent_holder": True}


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "PATH", tmp_path / "contributions.csv")
    monkeypatch.setattr(names, "gbif_match", lambda name: {})


def test_submit_needs_both_consents_and_refuses_doses(store):
    with pytest.raises(ValueError, match="consent"):
        c.submit({**FORM, "consent_holder": False})
    with pytest.raises(ValueError, match="dose"):
        c.submit({**FORM, "use": "drink 2 filxhanë a day for cough"})
    with pytest.raises(ValueError, match="dose"):
        c.submit({**FORM, "preparation": "200 g in 1 l water"})
    with pytest.raises(ValueError, match="missing"):
        c.submit({**FORM, "use": " "})
    assert c.submit(FORM) == 1 and c.entries("pending")[0]["local_name"] == "Çaj mali"


def test_only_approved_entries_are_published_and_can_be_withdrawn(store):
    first = c.submit(FORM)
    c.submit({**FORM, "local_name": "Hithi", "use": "anemia"})
    assert c.approved_records() == []
    with pytest.raises(ValueError, match="reviewer"):
        c.set_status(first, "approved", " ")
    entry = c.set_status(first, "approved", "A. Hoxha", "checked with the family")
    recs = c.approved_records()
    assert len(recs) == 1 and recs[0]["record_origin"] == c.ORIGIN and recs[0]["quote"].startswith("Contribution #1:")

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    initialize(conn)
    assert c.publish(conn, entry) == 1
    row = conn.execute("SELECT * FROM uses").fetchone()
    assert row["place"] == "Dragash" and row["record_origin"] == c.ORIGIN and row["review_status"] == "Needs Review"
    assert c.unpublish(conn, first) == 1
    assert conn.execute("SELECT COUNT(*) FROM uses").fetchone()[0] == 0
