"""Build the offline extraction cache from the Sharr paper's medicinal-use table.

This deterministic table parser is specific to the paper's JATS XML. It keeps
only plant rows carrying an ALB local-name label and a non-zero Albanian use
count. Each extracted row must also match its taxon, local name, preparation,
and use text to exactly one page in the supplied PDF.
"""
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
XML_PATH = ROOT / "data" / "raw" / "cross_cultural_sharr_2015.xml"
PDF_PATH = ROOT / "data" / "raw" / "cross_cultural_sharr_2015.pdf"
CACHE_PATH = ROOT / "data" / "cache" / "extract" / "cross_cultural_sharr_2015.json"

# Table 1 includes mushrooms as well as plants; those taxa are outside this app.
NON_PLANT_FAMILIES = {"Agaricaceae", "Amanitaceae"}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", text))


def _expanded_rows(table):
    """Expand HTML rowspans so every table row has the same column positions."""
    active = {}
    for row in table.findall(".//tr")[1:]:
        values = {}
        for column, (value, remaining) in list(active.items()):
            values[column] = value
            if remaining == 1:
                del active[column]
            else:
                active[column] = (value, remaining - 1)

        column = 0
        cells = row.findall("th") + row.findall("td")
        for cell in cells:
            while column in values:
                column += 1
            value = " ".join("".join(cell.itertext()).split())
            rowspan = int(cell.attrib.get("rowspan", "1"))
            values[column] = value
            if rowspan > 1:
                active[column] = (value, rowspan - 1)
            column += 1
        yield values


def _taxon_fields(taxon: str) -> tuple[str, str]:
    families = re.findall(r"\(([^()]*)\)", taxon)
    if not families:
        raise ValueError(f"No family found in table taxon: {taxon}")
    family = families[-1]
    name = taxon.replace(f"({family})", "", 1).strip()
    name = re.sub(r"\s+\d{2}/Pz/.*$", "", name).strip()
    return name, family


def _page_for_record(pages: list[str], fields: list[str]) -> int:
    tokens = _norm(" ".join(fields)).split()
    hits = [i for i, page in enumerate(pages, start=1) if all(t in page for t in tokens if len(t) > 2)]
    if len(hits) != 1:
        raise ValueError(f"Expected one PDF page for {fields!r}; found {hits}")
    return hits[0]


def _key(record: dict) -> tuple[str, str, str, str]:
    name = record.get("name_in_text") or ""
    binomial = " ".join(name.split()[:2])
    return tuple(_norm(value) for value in (
        binomial, record.get("local_name", ""), record.get("part_used", ""), record.get("preparation", "")
    ))


def _same_use(table_use: str, reviewed_use: str) -> bool:
    return _norm(table_use).replace(" ", "") in _norm(reviewed_use).replace(" ", "")


def extract_records() -> list[dict]:
    article = ET.parse(XML_PATH).getroot()
    tables = article.findall(".//table-wrap")
    table = next(t for t in tables if t.findtext("label") == "Table 1")
    with pymupdf.open(PDF_PATH) as pdf:
        pages = [_norm(page.get_text()) for page in pdf]

    records = []
    for row in _expanded_rows(table):
        if len(row) < 13 or not row.get(2, "").endswith("ALB"):
            continue
        try:
            alb_use_count = int(row[6])
        except (KeyError, ValueError):
            continue
        if alb_use_count <= 0:
            continue

        taxon = row.get(0, "")
        name, family = _taxon_fields(taxon)
        if family in NON_PLANT_FAMILIES:
            continue

        local_with_group = row[2]
        local_name = local_with_group[:-3].strip()
        part_used = row.get(3, "").strip(" ,;")
        preparation = row.get(4, "").strip(" ,;")
        use = row.get(5, "").strip(" ,;")
        page = _page_for_record(
            pages, [" ".join(taxon.split()[:2]), local_name, part_used, preparation, use]
        )
        records.append({
            "local_name": local_name,
            "name_in_text": name,
            "family": family,
            "part_used": part_used,
            "preparation": preparation,
            "administration": None,
            "use": use,
            "location": None,
            "page": page,
            "quote": f"{local_with_group} {row.get(3, '')} {row.get(4, '')} {row.get(5, '')}".strip(),
        })

    # Retain the three hand-reviewed summaries already in the cache; they cover
    # their corresponding table rows and contain more readable use wording.
    existing = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    for reviewed in existing:
        key = _key(reviewed)
        match = next((i for i, row in enumerate(records)
                      if _key(row) == key and _same_use(row["use"], reviewed["use"])), None)
        if match is None:
            raise ValueError(f"Could not match existing reviewed record to Table 1: {reviewed}")
        records[match] = reviewed
    return records


def main():
    records = extract_records()
    CACHE_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    taxa = {" ".join(r["name_in_text"].split()[:2]) for r in records}
    print(f"wrote {len(records)} ALB-labelled plant-use records from {len(taxa)} taxa")
    print("every row matched to one PDF page; no API key used")


if __name__ == "__main__":
    main()
