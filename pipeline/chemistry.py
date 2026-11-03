"""Innovation step: "does the tea even extract it?"

Gets known compounds for a species from Wikidata (LOTUS natural-products data) and
estimates lipophilicity with RDKit. Low logP = more water-soluble = more likely to end
up in a hot-water infusion. This is a rough screen, labelled as such in the app.
"""
import requests

from .cache import cached

WATER_SOLUBLE_LOGP = 1.0  # rough cut-off; document it as an assumption
SPARQL = """
SELECT DISTINCT ?compoundLabel ?smiles WHERE {
  ?taxon wdt:P225 "%s" .
  ?compound wdt:P703 ?taxon ; wdt:P233 ?smiles .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
} LIMIT 100
"""


def compounds(species: str) -> list[dict]:
    def fetch():
        r = requests.get("https://query.wikidata.org/sparql", timeout=60,
                         params={"query": SPARQL % species, "format": "json"},
                         headers={"User-Agent": "EthnoHack-student-project/0.1"})
        r.raise_for_status()
        return [{"compound": b["compoundLabel"]["value"], "smiles": b["smiles"]["value"]}
                for b in r.json()["results"]["bindings"]]

    return cached("lotus", species, fetch) or []


def logp(smiles: str) -> float | None:
    from rdkit import Chem, RDLogger
    from rdkit.Chem import Crippen

    RDLogger.DisableLog("rdApp.*")
    mol = Chem.MolFromSmiles(smiles)
    return round(Crippen.MolLogP(mol), 2) if mol else None


def run(species: str) -> list[dict]:
    rows = []
    for c in compounds(species):
        value = logp(c["smiles"])
        if value is not None:
            rows.append({"species": species, **c, "logp": value, "water_soluble": int(value < WATER_SOLUBLE_LOGP)})
    return rows
