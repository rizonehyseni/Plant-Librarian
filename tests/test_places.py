from pipeline.places import locate, locate_record, normalize


def test_normalize_strips_diacritics_and_punctuation():
    assert normalize("Shtërpcë, Kosovo") == "shterpce kosovo"
    assert normalize("Đakovica") == "djakovica"


def test_exact_alias_and_slavic_spelling():
    assert locate("Prizreni")["place"] == "Prizren"
    assert locate("Uroševac")["place"] == "Ferizaj"
    assert locate("Prizren")["geo_method"] == "exact"


def test_place_inside_a_phrase():
    hit = locate("village near Dragash, Kosovo")
    assert hit["place"] == "Dragash" and hit["geo_method"] == "phrase"
    # the longest alias wins: the whole mountain range, not a fragment
    assert locate("pastures of the Sharr Mountains")["place"] == "Malet e Sharrit"


def test_fuzzy_dialect_ending():
    hit = locate("Dragashe")
    assert hit["place"] == "Dragash" and hit["geo_method"] == "fuzzy"


def test_short_alias_not_matched_inside_text():
    # "Has" is a region, but the English word "has" must not put a pin on the map
    assert locate("it has no stated village") is None
    assert locate("Has")["place"] == "Has"


def test_unknown_and_empty():
    assert locate("village A") is None
    assert locate(None) is None and locate("") is None


def test_record_falls_back_to_study_area():
    r = locate_record("village A", "Malet e Sharrit")
    assert r["place"] == "Malet e Sharrit" and r["geo_precision"] == "study"
    r = locate_record("Rugova", "Malet e Sharrit")
    assert r["place"] == "Rugovë" and r["geo_precision"] == "record"
    assert locate_record(None, None)["lat"] is None
