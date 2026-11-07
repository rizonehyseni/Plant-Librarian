from pipeline.atlas import community_overlap, place_summary


def row(species, community, place="Malet e Sharrit", lat=42.05, lon=20.85, precision="study", doc="s1"):
    return {"species": species, "community": community, "place": place, "lat": lat, "lon": lon,
            "geo_precision": precision, "doc_id": doc}


ROWS = [
    row("Matricaria chamomilla", "Albanian"), row("Matricaria chamomilla", "Turkish"),
    row("Matricaria chamomilla", "Bosniak/Gorani"), row("Matricaria chamomilla", "Albanian"),
    row("Urtica dioica", "Albanian"), row("Urtica dioica", "Turkish"),
    row("Abies alba", "Albanian"),
    row("Sideritis scardica", None, place="Dragash", lat=42.06, lon=20.65, precision="record", doc="s2"),
    {**row("Unplaced", "Albanian"), "lat": None, "lon": None},
]


def test_overlap_counts_shared_and_unique_plants():
    o = community_overlap(ROWS)
    assert o["communities"] == ["Albanian", "Bosniak/Gorani", "Turkish"]
    assert o["shared_all"] == ["Matricaria chamomilla"]
    assert o["shared_some"] == ["Urtica dioica"]
    assert o["only"]["Albanian"] == ["Abies alba", "Unplaced"]
    assert o["per_community"]["Turkish"] == 2


def test_places_group_records_and_skip_unplaced():
    places = place_summary(ROWS)
    assert [p["place"] for p in places] == ["Malet e Sharrit", "Dragash"]
    sharr = places[0]
    assert sharr["records"] == 7 and sharr["plants"] == 3
    assert sharr["top_plants"][0] == "Matricaria chamomilla"
    assert sharr["precision"] == "study" and places[1]["precision"] == "record"
