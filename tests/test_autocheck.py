from pipeline import autocheck

PAGES = (autocheck._flat("Table 1 ... Hithi ALB Aerial parts Infusion Anti-anemic ... Kamomil Flowers Infusion"),
         autocheck._flat("continued ... Bredhi Wood Resin, mixed with fat Anti-fungal"))


def rec(**kw):
    return {"doc_id": "s", "page": 1, "local_name": "Hithi", "part_used": "Aerial parts", "preparation": "Infusion",
            "use": "Anti-anemic", "quote": "Hithi ALB Aerial parts Infusion Anti-anemic", **kw}


def test_record_found_on_its_page_passes(monkeypatch):
    monkeypatch.setattr(autocheck, "_pages", lambda doc: PAGES)
    status, detail = autocheck.check_record(rec())
    assert status == autocheck.PASSED and "not found" not in detail


def test_wrong_page_is_flagged_with_the_right_page(monkeypatch):
    monkeypatch.setattr(autocheck, "_pages", lambda doc: PAGES)
    status, detail = autocheck.check_record(rec(page=2))
    assert status == autocheck.ISSUES and "local name appears on p.1" in detail
    assert autocheck.check_record(rec(page=9))[0] == autocheck.ISSUES


def test_records_without_page_are_not_checked(monkeypatch):
    monkeypatch.setattr(autocheck, "_pages", lambda doc: PAGES)
    assert autocheck.check_record(rec(page=None))[0] == autocheck.NO_PAGE
