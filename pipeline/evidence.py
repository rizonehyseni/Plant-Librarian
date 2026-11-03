"""Step 4: find modern studies per species on PubMed and tag what was tested.

Tagging is rule-based (keywords in title + abstract) so it is transparent and testable.
The key output is the "same preparation?" check: did science test a water-based
preparation like the tea people actually drink, or only alcohol extracts / oils?
"""
import re
import time
import xml.etree.ElementTree as ET

import requests

from .cache import cached
from .config import NCBI_API_KEY, NCBI_EMAIL

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
MAX_PAPERS = 40

PREP_RULES = [  # first match wins, so the most specific goes first
    ("essential_oil", r"essential oil|volatile oil|hydrodistill"),
    ("aqueous", r"infusion|decoction|aqueous|water extract|hot water|herbal tea|\btea\b|tisane"),
    ("ethanolic", r"ethanol|ethanolic|hydroalcohol|hydro-alcohol|methanol|tincture"),
    ("compound", r"isolated compound|purified|isolated from"),
]
STUDY_RULES = [
    ("human", r"randomi[sz]ed|clinical trial|patients|volunteers|double-blind"),
    ("animal", r"\brats?\b|\bmice\b|\bmouse\b|in vivo"),
    ("in_vitro", r"in vitro|cell line|cells\b|assay|antimicrobial|antioxidant"),
]
TRADITIONAL_PREP_RULES = [
    ("aqueous", r"infusion|decoction|tea|boil|water|macerat.*water"),
    ("ethanolic", r"tincture|raki|rakia|brandy|alcohol"),
    ("oil", r"oil"),
]


def _classify(text: str, rules) -> str:
    text = text.lower()
    for label, pattern in rules:
        if re.search(pattern, text):
            return label
    return "other"


def classify_prep(text: str) -> str:
    return _classify(text, PREP_RULES)


def classify_study(text: str) -> str:
    return _classify(text, STUDY_RULES)


def classify_traditional(preparation: str) -> str:
    return _classify(preparation or "", TRADITIONAL_PREP_RULES)


def _params(**kw):
    if NCBI_API_KEY:
        kw["api_key"] = NCBI_API_KEY
    if NCBI_EMAIL:
        kw["email"] = NCBI_EMAIL
    kw["tool"] = "ethnohack"
    return kw


def pubmed(species: str) -> list[dict]:
    def fetch():
        ids = requests.get(f"{EUTILS}/esearch.fcgi", timeout=30, params=_params(
            db="pubmed", term=f'"{species}"[Title/Abstract]', retmax=MAX_PAPERS,
            sort="relevance", retmode="json",
        )).json()["esearchresult"]["idlist"]
        if not ids:
            return []
        time.sleep(0.4)
        xml = requests.get(f"{EUTILS}/efetch.fcgi", timeout=60, params=_params(
            db="pubmed", id=",".join(ids), retmode="xml",
        )).text
        papers = []
        for art in ET.fromstring(xml).iter("PubmedArticle"):
            title = "".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else ""
            abstract = " ".join("".join(a.itertext()) for a in art.iter("AbstractText"))
            year = art.findtext(".//PubDate/Year") or art.findtext(".//PubDate/MedlineDate") or ""
            papers.append({"pmid": art.findtext(".//PMID"), "title": title, "abstract": abstract, "year": year[:4]})
        time.sleep(0.4)
        return papers

    return cached("pubmed", species, fetch) or []


def run(species: str) -> list[dict]:
    rows = []
    for p in pubmed(species):
        text = f"{p['title']} {p['abstract']}"
        rows.append({
            "species": species, "pmid": p["pmid"], "title": p["title"], "year": p["year"],
            "prep_class": classify_prep(text), "study_type": classify_study(text),
        })
    return rows
