from importlib import import_module

from pipeline.db import connect

stats = import_module("eval.stats")

USES = [  # doc_id, species, community, prep_class, review_status, local_name
    ("s1", "Urtica dioica", "Albanian", "aqueous", "Verified", "Hithi"),
    ("s1", "Urtica dioica", "Turkish", "aqueous", "Needs Review", "Yakici"),
    ("s1", "Humulus lupulus", "Albanian", "aqueous", "Needs Review", "Bari sherbetit"),
    ("s1", "Allium sativum", "Turkish", "other", "Needs Review", "Sarimsak"),
    ("sample_fixture", "Sideritis scardica", "Albanian", "aqueous", "Verified", "Çaj mali"),
]


def make_db(tmp_path):
    conn = connect(tmp_path / "t.db")
    conn.executemany(
        "INSERT INTO uses (doc_id, page, species, community, prep_class, review_status, local_name, "
        "part_used, preparation, use) VALUES (?, 1, ?, ?, ?, ?, ?, 'leaves', 'infusion', 'cough')", USES)
    conn.executemany("INSERT INTO evidence (species, pmid, prep_class, study_type) VALUES (?, ?, ?, ?)", [
        ("Urtica dioica", "1", "aqueous", "human"),
        ("Humulus lupulus", "2", "ethanolic", "animal"),
        ("Sideritis scardica", "3", "aqueous", "human"),
    ])
    conn.execute("INSERT INTO occurrences VALUES ('Urtica dioica', 42, 20, 2020)")
    conn.execute("INSERT INTO flags VALUES ('Allium sativum', 'risk', 'caution', 'n', 's')")
    conn.execute("INSERT INTO flags VALUES ('Sideritis scardica', 'risk', 'warning', 'n', 's')")
    conn.commit()
    return conn


def test_stats_counts_exclude_fixture(tmp_path):
    gold = tmp_path / "gold.csv"
    gold.write_text("doc_id,page,local_name,species,part_used,preparation,use,community\n"
                    "s1,1,Hithi,Urtica dioica,leaves,infusion,cough,Albanian\n"
                    "s1,1,Missing,Abies alba,bark,infusion,cough,Albanian\n", encoding="utf-8")
    s = stats.compute(make_db(tmp_path), gold_path=gold, reviewed={})

    assert (s["studies"], s["records"], s["plants"]) == (1, 4, 3)
    assert s["records_per_community"] == {"Albanian": 2, "Turkish": 2}
    assert s["shared_all"] == 1 and s["only"] == {"Albanian": 1, "Turkish": 1}
    assert s["verdicts"]["human"] == 1 and s["verdicts"]["different"] == 1
    assert s["verdicts"]["not_comparable"] == 1 and s["gaps"] == 1
    assert (s["with_pubmed"], s["with_gbif"], s["with_compounds"]) == (2, 1, 0)
    assert s["flagged_plants"] == 1 and s["flags"] == {"risk / caution": 1}
    assert s["verified"] == 1
    assert (s["eval"]["hits"], s["eval"]["gold"]) == (1, 2)

    md = stats.to_markdown(s)
    assert "| Research gaps (only other preparations + no studies) | 1 |" in md
    assert "Sideritis" not in md
    assert "Eval recall" in stats.to_text(s)
