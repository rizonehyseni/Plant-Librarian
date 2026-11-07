"""Was the same preparation tested? (proposal step 4)

Compares how people prepare a plant (the study's preparation, classified by
evidence.classify_traditional) with the preparation tags of the PubMed candidates for that
plant (evidence.classify_prep). Rule-based, no AI. The PubMed tags are keyword guesses, so the
verdict is a screening hint for what to read next, not a review; manually reviewed papers
in data/seed/reviewed_evidence.csv always come first.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from typing import Any, Iterable, Mapping

from .config import SEED

# traditional class -> PubMed preparation tags that count as "the same kind of preparation"
SAME_PREP = {"aqueous": {"aqueous"}, "ethanolic": {"ethanolic"}}
TRADITIONAL_LABEL = {
    "aqueous": "water-based (tea, infusion, decoction)",
    "ethanolic": "alcohol-based (tincture, rakia)",
    "oil": "macerated in oil",
    "other": "eaten, fat ointment or other",
}
PREP_LABEL = {
    "aqueous": "water-based", "ethanolic": "alcohol extract", "essential_oil": "essential oil",
    "compound": "isolated compound", "other": "not stated / other",
}

# Verdicts, best evidence first. "gap" marks a research gap worth showing to judges.
VERDICTS = {
    "reviewed": ("Manually reviewed", "A team member checked a paper against this preparation.", False),
    "human": ("Same preparation, human study tagged", "At least one candidate tagged with the same preparation is tagged as a human study.", False),
    "lab": ("Same preparation, lab/animal only", "Candidates with the same preparation tag exist, but none is tagged as a human study.", False),
    "different": ("Only other preparations", "Studies exist, but none is tagged with the preparation people use.", True),
    "none": ("No studies found", "PubMed returned no candidate papers for this plant.", True),
    "not_comparable": ("Not comparable by keywords", "The traditional preparation (e.g. eaten fresh, fat ointment) has no matching keyword tag.", False),
}


def load_reviewed(path=None) -> dict[str, list[dict[str, str]]]:
    path = path or SEED / "reviewed_evidence.csv"
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                out[row["species"]].append(row)
    return dict(out)


def _cls(value: Any) -> str:
    """Tag or "other"; pandas gives NaN (a float) for missing values."""
    return value if isinstance(value, str) and value else "other"


def _paper_order(paper: Mapping[str, Any]) -> tuple:
    """Human studies first, then newest first."""
    year = str(paper.get("year") or "")
    return (_cls(paper.get("study_type")) != "human", -int(year) if year.isdigit() else 0)


def compare_species(
    uses: Iterable[Mapping[str, Any]],
    papers: Iterable[Mapping[str, Any]],
    reviewed: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Verdict for one plant from its use records, PubMed candidates and reviewed papers."""
    uses, papers, reviewed = list(uses), list(papers), list(reviewed)
    traditional = Counter(_cls(u.get("prep_class")) for u in uses)
    wanted = set().union(*(SAME_PREP.get(c, set()) for c in traditional)) if traditional else set()
    matching = [p for p in papers if _cls(p.get("prep_class")) in wanted]
    human = [p for p in matching if _cls(p.get("study_type")) == "human"]

    if reviewed:
        verdict = "reviewed"
    elif not wanted:
        verdict = "not_comparable"
    elif not papers:
        verdict = "none"
    elif not matching:
        verdict = "different"
    elif human:
        verdict = "human"
    else:
        verdict = "lab"
    label, explanation, gap = VERDICTS[verdict]
    return {
        "verdict": verdict, "label": label, "explanation": explanation, "gap": gap,
        "traditional": dict(traditional),
        "traditional_text": ", ".join(TRADITIONAL_LABEL.get(c, c) for c in sorted(traditional)) or "not stated",
        "papers": len(papers),
        "matching": len(matching),
        "matching_human": len(human),
        "matching_papers": sorted(matching, key=_paper_order),
        "prep_tags": dict(Counter(_cls(p.get("prep_class")) for p in papers)),
        "reviewed": reviewed,
    }


def summary_sentence(result: Mapping[str, Any]) -> str:
    """One plain sentence for the profile page and the chat context."""
    base = f"People prepare it {result['traditional_text']}. "
    v = result["verdict"]
    if v == "reviewed":
        return base + f"{len(result['reviewed'])} paper(s) were manually checked against this preparation."
    if v == "not_comparable":
        return base + "Keyword tags cannot tell whether a study used this kind of preparation."
    if v == "none":
        return base + "No PubMed candidate papers were found."
    if v == "different":
        return base + f"None of the {result['papers']} PubMed candidates is tagged with this preparation."
    return base + (f"{result['matching']} of {result['papers']} PubMed candidates are tagged with the same kind of "
                   f"preparation; {result['matching_human']} of those are tagged as human studies.")


def compare_all(conn, reviewed: Mapping[str, list] | None = None) -> list[dict[str, Any]]:
    """One row per plant in the database (synthetic fixture excluded), research gaps first."""
    reviewed = load_reviewed() if reviewed is None else reviewed
    uses: dict[str, list[dict]] = defaultdict(list)
    local: dict[str, set[str]] = defaultdict(set)
    for row in conn.execute(
        "SELECT species, local_name, prep_class FROM uses WHERE species IS NOT NULL AND doc_id != 'sample_fixture'"
    ):
        uses[row["species"]].append(dict(row))
        if row["local_name"]:
            local[row["species"]].add(row["local_name"])
    papers: dict[str, list[dict]] = defaultdict(list)
    for row in conn.execute("SELECT species, pmid, title, year, prep_class, study_type FROM evidence"):
        papers[row["species"]].append(dict(row))

    rows = []
    for species in uses:
        result = compare_species(uses[species], papers.get(species, []), reviewed.get(species, []))
        rows.append({"species": species, "local_names": ", ".join(sorted(local[species])), **result})
    order = list(VERDICTS)
    return sorted(rows, key=lambda r: (not r["gap"], order.index(r["verdict"]), r["species"]))
