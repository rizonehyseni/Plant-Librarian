import sqlite3
from pipeline.db import connect, initialize
from pipeline.quality import audit_history, check_records, dashboard_metrics, fetch_records, filter_records, save_review


def sample_record(**overrides):
    record = {
        "id": 1, "doc_id": "study", "local_name": "Çaj mali", "species": "Origanum vulgare",
        "match_method": "exact", "part_used": "Aerial parts", "preparation": "Infusion",
        "use": "Cough", "geo_precision": "record", "review_status": "Needs Review",
        "record_origin": "Source Table", "source_title": "Study", "source_citation": "Author (2024)",
        "source_url": "https://example.test/study",
    }
    record.update(overrides)
    return record


def test_quality_checks_detect_missing_and_duplicate_data():
    records = [
        sample_record(source_url="", source_title="", species=None, match_method="unresolved", local_name="", part_used="", preparation="", geo_precision="study"),
        sample_record(id=2),
        sample_record(id=3),
    ]
    findings = check_records(records)
    assert {"missing_citation", "missing_source", "unresolved_scientific_name", "unconfirmed_local_name", "missing_preparation", "missing_plant_part", "missing_location"} <= set(findings[1])
    assert "potential_duplicate" in findings[2] and "potential_duplicate" in findings[3]


def test_dashboard_metrics_and_filters():
    records = [sample_record(id=1, review_status="Verified"), sample_record(id=2, species=None, record_origin="AI Extracted", geo_precision="study")]
    findings = check_records(records)
    metrics = dashboard_metrics(records, findings)
    assert metrics["total"] == 2 and metrics["verified"] == 1
    assert metrics["ai_extracted"] == 1 and metrics["unresolved_names"] == 1
    assert filter_records(records, findings, review_status="Verified") == [records[0]]
    assert filter_records(records, findings, issue="missing_location") == [records[1]]


def test_migration_preserves_existing_records_and_review_actions(tmp_path):
    path = tmp_path / "legacy.db"
    legacy = sqlite3.connect(path)  # an old database, created before connect() migrated
    conn = legacy
    conn.execute("CREATE TABLE uses (id INTEGER PRIMARY KEY, doc_id TEXT, local_name TEXT, species TEXT, match_method TEXT, part_used TEXT, preparation TEXT, use TEXT, geo_precision TEXT)")
    conn.execute("CREATE TABLE sources (doc_id TEXT PRIMARY KEY, title TEXT, citation TEXT, url TEXT, licence TEXT, study_area TEXT)")
    conn.execute("INSERT INTO sources VALUES ('study', 'Study', 'Author (2024)', 'https://example.test/study', '', '')")
    conn.execute("INSERT INTO uses (id, doc_id, local_name, species, match_method, part_used, preparation, use, geo_precision) VALUES (1, 'study', 'Çaj mali', 'Origanum vulgare', 'exact', 'Aerial parts', 'Infusion', 'Cough', 'record')")
    conn.commit()
    legacy.close()

    conn = connect(path)  # migrates the old schema
    initialize(conn)  # running it again is harmless
    record = fetch_records(conn)[0]
    assert record["species"] == "Origanum vulgare"
    assert record["review_status"] == "Needs Review" and record["record_origin"] == "AI Extracted"

    history = save_review(conn, 1, {"record_origin": "Manually Reviewed", "review_status": "Verified", "preparation": "Decoction"}, "Local Reviewer", "Checked against page 4")
    assert len(history) == 3
    updated = fetch_records(conn)[0]
    assert updated["review_status"] == "Verified" and updated["preparation"] == "Decoction"
    assert audit_history(conn, 1)[0]["reviewer_note"] == "Checked against page 4"


def test_ai_record_cannot_be_verified_without_manual_review(tmp_path):
    conn = connect(tmp_path / "review.db")
    initialize(conn)
    conn.execute("INSERT INTO sources VALUES ('study', 'Study', 'Author', 'https://example.test', '', '')")
    conn.execute("INSERT INTO uses (doc_id, local_name, species, match_method, part_used, preparation, use, geo_precision) VALUES ('study', 'Name', 'Plant species', 'exact', 'leaf', 'tea', 'use', 'record')")
    conn.commit()

    try:
        save_review(conn, 1, {"review_status": "Verified"}, "Reviewer")
    except ValueError as exc:
        assert "AI-extracted" in str(exc)
    else:
        raise AssertionError("AI record was verified without manual review")
