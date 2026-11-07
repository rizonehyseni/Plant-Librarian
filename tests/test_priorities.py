from pipeline.priorities import categories, knowledge_at_risk, research_priorities


def row(species, use, community=None, doc="sharr", local="x"):
    return {"species": species, "use": use, "community": community, "doc_id": doc, "local_name": local}


ROWS = [
    # Hop: insomnia in three independent groups across two studies
    row("Humulus lupulus", "Insomnia", "Albanian"), row("Humulus lupulus", "Neurorelaxant", "Turkish"),
    row("Humulus lupulus", "Relaxant", doc="alps"),
    # Nettle: well tested (human verdict) so never a priority
    row("Urtica dioica", "Anti-tussive", "Albanian"), row("Urtica dioica", "Bronchitis", "Turkish"),
    # One group only
    row("Abies alba", "Anti-fungal", "Albanian", local="Bredhi"),
    row("Humulus lupulus", "Wound healing", "Turkish"),
]
VERDICTS = {"Humulus lupulus": {"verdict": "different", "papers": 40, "traditional_text": "water-based"},
            "Urtica dioica": {"verdict": "human", "papers": 38},
            "Abies alba": {"verdict": "none", "papers": 0}}
LABELS = {"sharr": "Sharr 2015", "alps": "Alps 2012"}


def test_categories_from_use_text():
    assert categories("Anti-tussive, bronchitis") == {"respiratory"}
    assert categories("“Saraxha” (cutaneous tuberculosis)") == {"skin"}
    assert categories("Insomnia") == {"nervous"}
    assert categories("drunk as a tea") == set()


def test_priorities_need_independent_groups_and_untested_preparation():
    p = research_priorities(ROWS, VERDICTS, LABELS)
    assert [e["species"] for e in p] == ["Humulus lupulus"]  # nettle tested in humans, fir in one group
    hop = p[0]
    assert hop["category"] == "nervous" and hop["n_groups"] == 3 and hop["studies"] == 2 and hop["gap"]
    assert "Alps 2012" in hop["groups"] and "Sharr 2015 · Turkish" in hop["groups"]


def test_knowledge_at_risk_lists_plants_and_uses_of_one_group():
    k = knowledge_at_risk(ROWS, LABELS)
    assert [p["species"] for p in k["unique_plants"]] == ["Abies alba"]
    assert k["unique_plants"][0]["group"] == "Sharr 2015 · Albanian"
    # wound healing with hop is reported only by the Turkish group
    assert {"species": "Humulus lupulus", "category": "skin", "group": "Sharr 2015 · Turkish", "records": 1} \
        in k["unique_uses"]
    assert k["per_group"]["Sharr 2015 · Albanian"]["only_here"] == 1
