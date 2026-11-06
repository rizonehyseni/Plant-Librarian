from pipeline.db import connect, initialize
from pipeline.explore import compare_plants, filter_options, load_records, page_records, search_and_filter, sort_records


def record(record_id, **overrides):
    data = {
        "id": record_id, "local_name": "Çaj mali", "species": "Sideritis scardica",
        "use": "Respiratory support", "part_used": "Flowers", "preparation": "Infusion",
        "location_label": "Malet e Sharrit", "evidence_types": {"Traditional use", "human"},
        "safety_levels": {"caution"}, "safety_flags": [{"level": "caution", "note": "Check medicines."}],
        "review_status": "Verified", "aliases": {"caj mali", "mountain tea"}, "use_count": 2,
        "doc_id": "study",
    }
    data.update(overrides)
    return data


def test_search_supports_albanian_scientific_partial_alias_and_use_text():
    rows = [record(1), record(2, local_name="Kamomili", species="Matricaria chamomilla", use="Digestive discomfort", aliases={"kamomil"})]
    assert search_and_filter(rows, query="çaj mali") == [rows[0]]
    assert search_and_filter(rows, query="sideritis") == [rows[0]]
    assert search_and_filter(rows, query="mountain") == [rows[0]]
    assert search_and_filter(rows, query="digestive") == [rows[1]]


def test_filters_combine_actual_record_values_and_options():
    rows = [record(1), record(2, part_used="Roots", preparation="Decoction", location_label="Rugovë", evidence_types={"Traditional use", "animal"}, safety_levels=set(), review_status="Needs Review")]
    results = search_and_filter(rows, parts=["Roots"], preparations=["Decoction"], locations=["Rugovë"], evidence_types=["animal"], review_statuses=["Needs Review"])
    assert results == [rows[1]]
    options = filter_options(rows)
    assert options["parts"] == ["Flowers", "Roots"]
    assert options["evidence"] == ["Traditional use", "animal", "human"]
    assert options["safety"] == ["caution"]


def test_sorting_and_pagination_are_stable():
    rows = [record(3, local_name="Z", use_count=1), record(1, local_name="A", use_count=4), record(2, local_name="B", review_status="Needs Review", use_count=2)]
    assert [row["id"] for row in sort_records(rows, "Plant name")] == [1, 2, 3]
    assert [row["id"] for row in sort_records(rows, "Number of documented uses")] == [1, 2, 3]
    assert [row["id"] for row in sort_records(rows, "Verification status")] == [1, 3, 2]
    page, total_pages = page_records(rows, page=2, page_size=2)
    assert total_pages == 2 and page == [rows[2]]


def test_comparison_uses_only_available_database_fields_and_caps_at_three():
    rows = [
        record(1), record(2, species="Matricaria chamomilla", local_name="Kamomili", safety_flags=[]),
        record(3, species="Origanum vulgare", local_name="Rigon", evidence_types={"Traditional use", "in_vitro"}),
        record(4, species="Althaea officinalis", local_name="Mullaga"),
    ]
    comparison = compare_plants(rows, ["Sideritis scardica", "Matricaria chamomilla", "Origanum vulgare", "Althaea officinalis"])
    assert [plant["species"] for plant in comparison] == ["Sideritis scardica", "Matricaria chamomilla", "Origanum vulgare"]
    assert comparison[0]["uses"] == ["Respiratory support"]
    assert comparison[1]["safety_flags"] == []


def test_load_records_joins_existing_evidence_and_safety_data(tmp_path):
    conn = connect(tmp_path / "explore.db")
    initialize(conn)
    conn.execute("INSERT INTO sources VALUES ('study', 'Study', 'Citation', 'https://example.test', '', '')")
    conn.execute(
        """
        INSERT INTO uses (doc_id, local_name, species, match_method, part_used, preparation, use, place, geo_precision)
        VALUES ('study', 'Rigon', 'Origanum vulgare', 'exact', 'Flowers', 'Infusion', 'Cough', 'Malet e Sharrit', 'study')
        """
    )
    conn.execute("INSERT INTO evidence VALUES ('Origanum vulgare', '123', 'Paper', '2024', 'aqueous', 'human')")
    conn.execute("INSERT INTO flags VALUES ('Origanum vulgare', 'risk', 'caution', 'Check medicines.', 'Source')")
    conn.commit()

    loaded = load_records(conn)
    assert len(loaded) == 1
    assert loaded[0]["location_label"] == "Malet e Sharrit"
    assert loaded[0]["evidence_types"] == {"Traditional use", "human"}
    assert loaded[0]["safety_levels"] == {"caution"}
