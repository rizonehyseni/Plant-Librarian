from pipeline.evidence import classify_prep, classify_study, classify_traditional


def test_preparation_classes():
    assert classify_prep("Antioxidant activity of an aqueous infusion") == "aqueous"
    assert classify_prep("Ethanolic extract reduced inflammation") == "ethanolic"
    assert classify_prep("Composition of the essential oil obtained by hydrodistillation") == "essential_oil"


def test_study_types():
    assert classify_study("A randomized double-blind trial in patients") == "human"
    assert classify_study("Effects in rats after oral dosing") == "animal"
    assert classify_study("Cytotoxicity in a cancer cell line") == "in_vitro"


def test_traditional_preparation():
    assert classify_traditional("decoction") == "aqueous"
    assert classify_traditional("macerated in rakia") == "ethanolic"
