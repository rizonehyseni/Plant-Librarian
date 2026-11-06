import sqlite3

from pipeline import chat
from pipeline.db import initialize


def make_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    initialize(conn)
    conn.execute("INSERT INTO sources (doc_id, title, citation, url, licence) VALUES "
                 "('sharr', 'Sharr study', 'Mustafa 2015', 'https://example.org/sharr', 'CC BY 4.0')")
    rows = [
        ("sharr", 8, "Mullaga", "Althaea officinalis", "Flowers", "Infusion", "aqueous", "Anti-tussive"),
        ("sharr", 9, "Lule djellı", "Helianthus annuus", "Seeds", "Raw", "other", "Digestive"),
        ("sharr", 13, "Çaj mali", "Origanum vulgare", "Aerial parts", "Infusion", "aqueous", "Influenza"),
        ("sample_fixture", 1, "Kamomili", "Matricaria chamomilla", "Flowers", "Infusion", "aqueous", "Fixture only"),
    ]
    conn.executemany(
        "INSERT INTO uses (doc_id, page, local_name, species, part_used, preparation, prep_class, use) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
    conn.execute("INSERT INTO evidence VALUES ('Althaea officinalis', '111', 'Tea study', '2020', 'aqueous', 'in_vitro')")
    conn.execute("INSERT INTO evidence VALUES ('Althaea officinalis', '222', 'Ethanol study', '2019', 'ethanolic', 'animal')")
    conn.execute("INSERT INTO flags VALUES ('Origanum vulgare', 'risk', 'caution', 'Test note', 'Test rule')")
    return conn


def test_finds_plants_by_local_dialect_and_scientific_names():
    plants = chat.load_plants(make_db())
    assert chat.find_plants("Si përdoret mullagja?", plants) == ["Althaea officinalis"]
    assert chat.find_plants("caj mali per grip", plants) == ["Origanum vulgare"]
    assert chat.find_plants("Origanum vulgare", plants) == ["Origanum vulgare"]
    assert chat.find_plants("lule djelli", plants) == ["Helianthus annuus"]
    assert chat.find_plants("Which plants help a cough?", plants) == []


def test_fixture_records_are_never_used():
    plants = chat.load_plants(make_db())
    assert "Matricaria chamomilla" not in plants


def test_plant_context_has_citable_records_evidence_and_preparation_comparison():
    r = chat.retrieve(make_db(), "Mullaga")
    assert r.plants == ["Althaea officinalis"]
    assert "[R1]" in r.context and "page 8" in r.context
    assert "[P111]" in r.context and "1 of 2" in r.context  # one candidate tagged aqueous like the tea
    assert "LIMITED safety list" in r.context
    assert r.sources["P111"]["url"] == "https://pubmed.ncbi.nlm.nih.gov/111/"


def test_question_without_plant_gets_overview_with_flags():
    r = chat.retrieve(make_db(), "Which plants are risky?")
    assert r.plants == []
    assert "[F1] Origanum vulgare" in r.context and "[R3]" in r.context


def test_follow_up_reuses_plant_from_history():
    history = [{"role": "user", "content": "Tell me about çaj mali"}, {"role": "assistant", "content": "..."}]
    r = chat.retrieve(make_db(), "A është e rrezikshme?", history)
    assert r.plants == ["Origanum vulgare"]
    assert "[F1] risk (caution)" in r.context


def test_cited_ids_keep_only_known_ids_in_order():
    sources = {"R1": {}, "P111": {}, "F1": {}}
    text = "Infusion [R1]. Lab study [P111][R1]. Risk [F1, R1]. Made up [R99]."
    assert chat.cited_ids(text, sources) == ["R1", "P111", "F1"]


def test_messages_put_context_in_system_prompt_and_keep_history():
    r = chat.retrieve(make_db(), "Mullaga")
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    msgs = chat.build_messages("Mullaga?", r, history)
    assert msgs[0]["role"] == "system" and "CONTEXT:" in msgs[0]["content"] and "[R1]" in msgs[0]["content"]
    assert [m["role"] for m in msgs[1:]] == ["user", "assistant", "user"]
