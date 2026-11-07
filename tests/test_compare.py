import sqlite3

from pipeline.compare import compare_all, compare_species, summary_sentence
from pipeline.db import initialize

TEA = [{"prep_class": "aqueous"}]


def paper(pmid, prep, kind, year="2020"):
    return {"pmid": pmid, "title": f"Paper {pmid}", "year": year, "prep_class": prep, "study_type": kind}


def test_verdicts_follow_the_evidence_ladder():
    assert compare_species(TEA, [], [{"title": "x"}])["verdict"] == "reviewed"
    assert compare_species(TEA, [paper("1", "aqueous", "human")])["verdict"] == "human"
    assert compare_species(TEA, [paper("1", "aqueous", "animal")])["verdict"] == "lab"
    assert compare_species(TEA, [paper("1", "ethanolic", "human")])["verdict"] == "different"
    assert compare_species(TEA, [])["verdict"] == "none"
    assert compare_species([{"prep_class": "other"}], [paper("1", "aqueous", "human")])["verdict"] == "not_comparable"


def test_only_untested_preparations_are_research_gaps():
    assert compare_species(TEA, [paper("1", "ethanolic", "human")])["gap"]
    assert compare_species(TEA, [])["gap"]
    assert not compare_species(TEA, [paper("1", "aqueous", "animal")])["gap"]
    assert not compare_species([{"prep_class": "oil"}], [])["gap"]


def test_counts_and_order_human_first_then_newest():
    papers = [paper("1", "aqueous", "animal", "2021"), paper("2", "aqueous", "human", "2010"),
              paper("3", "aqueous", "in_vitro", "2023"), paper("4", "ethanolic", "human")]
    r = compare_species(TEA + [{"prep_class": "other"}], papers)
    assert (r["papers"], r["matching"], r["matching_human"]) == (4, 3, 1)
    assert [p["pmid"] for p in r["matching_papers"]] == ["2", "3", "1"]
    assert "3 of 4 PubMed candidates" in summary_sentence(r)


def test_missing_tags_from_pandas_are_treated_as_other():
    nan = float("nan")
    r = compare_species([{"prep_class": nan}], [{"pmid": "1", "prep_class": nan, "study_type": nan, "year": nan}])
    assert r["verdict"] == "not_comparable"


def test_compare_all_puts_gaps_first_and_skips_fixture():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    initialize(conn)
    conn.executemany("INSERT INTO uses (doc_id, local_name, species, prep_class) VALUES (?, ?, ?, ?)", [
        ("study", "Çaj mali", "Origanum vulgare", "aqueous"),
        ("study", "Hithi", "Urtica dioica", "aqueous"),
        ("sample_fixture", "Kamomili", "Matricaria chamomilla", "aqueous"),
    ])
    conn.execute("INSERT INTO evidence VALUES ('Origanum vulgare', '1', 't', '2020', 'aqueous', 'animal')")
    conn.execute("INSERT INTO evidence VALUES ('Urtica dioica', '2', 't', '2020', 'ethanolic', 'human')")
    rows = compare_all(conn, reviewed={})
    assert [(r["species"], r["verdict"]) for r in rows] == [("Urtica dioica", "different"), ("Origanum vulgare", "lab")]
    assert rows[0]["local_names"] == "Hithi"
