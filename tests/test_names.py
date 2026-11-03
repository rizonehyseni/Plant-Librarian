from pipeline.names import match_local, normalize


def test_normalize_strips_diacritics_and_suffix():
    assert normalize("Çaj Mali") == "caj mali"
    assert normalize("Kamomili") == "kamomil"


def test_exact_and_fuzzy_dialect_match():
    assert match_local("kamomili")[0] == "Matricaria chamomilla"
    species, method, _ = match_local("Sherebela")
    assert species == "Salvia officinalis" and method in {"exact", "fuzzy"}


def test_unknown_name_stays_unresolved():
    assert match_local("xyzqw")[1] == "unresolved"
