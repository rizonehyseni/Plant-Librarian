"""Research priorities and knowledge at risk. NO AI and no network: keyword rules and counts.

A *group* is one community in one study (e.g. Turkish in the 2015 Sharr study, or the whole
2012 Albanian Alps study, which does not split by community). Two groups that report the
same plant for the same kind of complaint did so independently, which is a stronger signal
than one group reporting it many times.

- research_priorities: plants used for the same body system by 2+ independent groups whose
  traditional preparation has not been tested (no study with the same preparation tag), or
  only in the lab. These are the strongest candidates for new studies.
- knowledge_at_risk: plants and uses that only one group reported. If that group stops
  passing the knowledge on, nothing else in the library records it.
"""
from collections import defaultdict

# Body-system categories from keywords in the English use text. Order matters only for display.
CATEGORIES = {
    "respiratory": ("tussive", "cough", "bronch", "expector", "influenza", "flu", "asthma", "respirat", "lung",
                    "pneumon", "throat", "cold", "sinus", "tubercul"),
    "digestive": ("stomach", "diarrh", "constipat", "digest", "appetiz", "carminat", "spasmolyt", "hemorrhoid",
                  "haemorrhoid", "ulcer", "gastr", "colic", "acid", "intestin", "laxat", "nausea", "vomit", "emetic", "igestive"),
    "liver": ("hepat", "liver", "bile", "gall"),
    "urinary": ("urinar", "kidney", "lithontrip", "diuret", "renal", "prostat", "bladder"),
    "heart_blood": ("hypertens", "circulat", "cholester", "coagul", "anemi", "anaemi", "heart", "hart ", "cardi", "blood",
                    "varic", "edema", "oedema"),
    "metabolic": ("diabet", "thyroid", "obes", "weight"),
    "skin": ("wound", "skin", "eczem", "burn", "wart", "acne", "dandruff", "alopecia", "cutaneous", "vulnerar",
             "depigment", "perspir", "abscess", "dermat", "hair", "saraxha", "boil"),
    "musculoskeletal": ("rheumat", "back pain", "skeletal", "joint", "arthrit", "bone", "muscle", "sprain"),
    "nervous": ("relax", "insomnia", "headache", "head-ache", "head ache", "sedat", "nerv", "migraine", "sleep", "anxi", "depress"),
    "infection": ("bacter", "microb", "fung", "mycot", "parasit", "malari", "antisept", "viral", "lice"),
    "immune_allergy": ("immun", "allerg"),
    "cancer": ("cancer", "tumo"),
    "reproductive": ("menstru", "galactogog", "fertil", "steril", "pregnan", "gynec", "uter", "lactat", "birth"),
    "eye_ear_mouth": ("eye", "ear", "oral", "tooth", "dental", "halitosis", "gum", "mouth"),
    "fever_inflammation": ("pyret", "fever", "inflamm"),
}
# "tuberculosis" in "cutaneous tuberculosis" (saraxha) is a skin disease, not a lung one.
NOT_RESPIRATORY = ("cutaneous", "saraxha")

GAP_VERDICTS = {"different", "none"}  # studies exist but none with this preparation, or no studies
LAB_VERDICTS = {"lab"}


def categories(use: str | None) -> set[str]:
    text = (use or "").lower()
    found = {cat for cat, words in CATEGORIES.items() if any(w in text for w in words)}
    if "respiratory" in found and any(w in text for w in NOT_RESPIRATORY) and \
            not any(w in text for w in CATEGORIES["respiratory"] if w != "tubercul"):
        found.discard("respiratory")
    return found


def group_of(row: dict, study_label: dict[str, str] | None = None) -> str:
    study = (study_label or {}).get(row["doc_id"], row["doc_id"])
    return f"{study} · {row['community']}" if row.get("community") else study


def _support(rows: list[dict], study_label: dict[str, str] | None) -> dict:
    """(species, category) -> {group: record count}."""
    support: dict[tuple, dict] = defaultdict(lambda: defaultdict(int))
    for r in rows:
        if not r.get("species"):
            continue
        for cat in categories(r.get("use")):
            support[(r["species"], cat)][group_of(r, study_label)] += 1
    return support


def research_priorities(rows: list[dict], verdicts: dict[str, dict], study_label: dict[str, str] | None = None,
                        min_groups: int = 2) -> list[dict]:
    """Plants used for one body system by >= min_groups independent groups, with an untested preparation.

    `verdicts` maps species -> a pipeline.compare result (verdict, papers, matching, traditional_text).
    """
    support = _support(rows, study_label)
    best: dict[str, dict] = {}
    for (species, cat), groups in support.items():
        v = verdicts.get(species)
        if not v or len(groups) < min_groups or v["verdict"] not in GAP_VERDICTS | LAB_VERDICTS:
            continue
        gap = v["verdict"] in GAP_VERDICTS
        studies = {g.split(" · ")[0] for g in groups}
        # independent groups count most; a second region and an untested preparation add to it
        score = len(groups) * 10 + (len(studies) - 1) * 15 + (20 if gap else 0) + min(sum(groups.values()), 20) / 2
        entry = {"species": species, "category": cat, "groups": sorted(groups), "n_groups": len(groups),
                 "records": sum(groups.values()), "studies": len(studies), "verdict": v["verdict"], "gap": gap,
                 "papers": v.get("papers", 0), "traditional_text": v.get("traditional_text", ""),
                 "score": score, "other_categories": []}
        if species not in best or score > best[species]["score"]:
            if species in best:
                entry["other_categories"] = [best[species]["category"], *best[species]["other_categories"]]
            best[species] = entry
        else:
            best[species]["other_categories"].append(cat)
    return sorted(best.values(), key=lambda e: (-e["score"], e["species"]))


def knowledge_at_risk(rows: list[dict], study_label: dict[str, str] | None = None) -> dict:
    """Plants and (plant, use category) pairs that only one group reported."""
    plant_groups: dict[str, set] = defaultdict(set)
    plant_records: dict[str, int] = defaultdict(int)
    local: dict[str, set] = defaultdict(set)
    for r in rows:
        if r.get("species"):
            plant_groups[r["species"]].add(group_of(r, study_label))
            plant_records[r["species"]] += 1
            if r.get("local_name"):
                local[r["species"]].add(r["local_name"])
    groups = sorted({g for gs in plant_groups.values() for g in gs})
    unique_plants = sorted(
        ({"species": sp, "group": next(iter(gs)), "records": plant_records[sp],
          "local_names": ", ".join(sorted(local[sp]))} for sp, gs in plant_groups.items() if len(gs) == 1),
        key=lambda p: (p["group"], p["species"]))
    support = _support(rows, study_label)
    unique_uses = sorted(
        ({"species": sp, "category": cat, "group": next(iter(gs)), "records": sum(gs.values())}
         for (sp, cat), gs in support.items() if len(gs) == 1 and len(plant_groups[sp]) > 1),
        key=lambda u: (u["group"], u["species"], u["category"]))
    per_group = {g: {"plants": sum(g in gs for gs in plant_groups.values()),
                     "only_here": sum(p["group"] == g for p in unique_plants),
                     "unique_uses": sum(u["group"] == g for u in unique_uses)} for g in groups}
    return {"groups": groups, "per_group": per_group, "unique_plants": unique_plants, "unique_uses": unique_uses,
            "plants": len(plant_groups)}


def study_labels(conn) -> dict[str, str]:
    """Short study names for display: study area + year, e.g. 'Malet e Sharrit 2015'."""
    import re
    out = {}
    for doc_id, area, citation in conn.execute("SELECT doc_id, study_area, citation FROM sources"):
        year = re.search(r"\b(19|20)\d{2}\b", citation or "")
        out[doc_id] = " ".join(x for x in (area or doc_id, year.group(0) if year else "") if x)
    return out
