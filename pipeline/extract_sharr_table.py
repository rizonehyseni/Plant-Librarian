"""Build the offline extraction cache from the Sharr paper's medicinal-use table.

This deterministic parser keeps plant-use reports with a non-zero count for
Albanian, Bosniak/Gorani, or Turkish communities. Every result is page-matched
to the source PDF.
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
COMMUNITIES = {"ALB": "Albanian", "BOG": "Bosniak/Gorani", "TUR": "Turkish"}


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


def _folk_names(value: str) -> dict[str, set[str]]:
    """Read one or more local names with the paper's community suffixes."""
    out = {code: set() for code in COMMUNITIES}
    for match in re.finditer(r"(.+?)(ALB|BOG|TUR)(?=\s|$)", value):
        name = match.group(1).strip()
        if name:
            out[match.group(2)].add(name)
    return out


def _page_for_record(pages: list[str], fields: list[str]) -> int:
    taxon, local_names, part, preparation, use = fields[0], fields[1:-3], fields[-3], fields[-2], fields[-1]
    significant = lambda value: [t for t in _norm(value).split() if len(t) > 2]
    part_tokens, prep_tokens = significant(part), significant(preparation)
    use_phrase = _norm(use)
    taxon_tokens = significant(taxon)
    aliases = [significant(name) for name in local_names if significant(name)]

    def has_alias(page: str) -> bool:
        return any(all(token in page for token in alias) for alias in aliases)

    hits = [i for i, page in enumerate(pages, start=1)
            if has_alias(page) and all(token in page for token in part_tokens + prep_tokens)
            and use_phrase in page]
    taxon_hits = [i for i in hits if all(token in pages[i - 1] for token in taxon_tokens)]
    if len(taxon_hits) == 1:
        return taxon_hits[0]
    if not hits:
        # Long table rows may continue onto the next printed page after the
        # taxon, local name, part, and preparation have appeared.
        context_pages = {i for i, page in enumerate(pages, start=1)
                         if all(token in page for token in taxon_tokens)
                         and has_alias(page)
                         and all(token in page for token in part_tokens + prep_tokens)}
        hits = [i for i, page in enumerate(pages, start=1)
                if i - 1 in context_pages and use_phrase in page]
    if len(hits) != 1:
        raise ValueError(f"Expected one PDF page for {fields!r}; found {hits}")
    return hits[0]


def extract_records() -> list[dict]:
    article = ET.parse(XML_PATH).getroot()
    tables = article.findall(".//table-wrap")
    table = next(t for t in tables if t.findtext("label") == "Table 1")
    with pymupdf.open(PDF_PATH) as pdf:
        pages = [_norm(page.get_text()) for page in pdf]

    rows = list(_expanded_rows(table))
    names_by_taxon: dict[str, dict[str, set[str]]] = {}
    for row in rows:
        taxon = row.get(0, "")
        groups = names_by_taxon.setdefault(taxon, {code: set() for code in COMMUNITIES})
        for code, names in _folk_names(row.get(2, "")).items():
            groups[code].update(names)

    records = []
    seen_use_rows = set()
    for row in rows:
        if len(row) < 13 or not any(_folk_names(row.get(2, "")).values()):
            continue
        taxon = row.get(0, "")
        try:
            name, family = _taxon_fields(taxon)
            counts = {code: int(row[column]) for code, column in (("ALB", 6), ("BOG", 7), ("TUR", 8))}
        except (KeyError, ValueError):
            continue
        if family in NON_PLANT_FAMILIES:
            continue

        part_used = row.get(3, "").strip(" ,;")
        preparation = row.get(4, "").strip(" ,;")
        use = row.get(5, "").strip(" ,;")
        if not part_used or not preparation or not use:
            continue
        # Several community-name rows repeat one disease/preparation record
        # with different citation counts. The app stores the report once and
        # does not present those counts as a per-record measurement.
        use_key = (taxon, part_used, preparation, use)
        if use_key in seen_use_rows:
            continue
        seen_use_rows.add(use_key)

        for code, label in COMMUNITIES.items():
            local_names = sorted(names_by_taxon[taxon][code])
            if counts[code] <= 0 or not local_names:
                continue
            local_name = " / ".join(local_names)
            page = _page_for_record(
                pages, [" ".join(taxon.split()[:2]), *local_names, part_used, preparation, use]
            )
            records.append({
                "local_name": local_name,
                "name_in_text": name,
                "family": family,
                "community": label,
                "part_used": part_used,
                "preparation": preparation,
                "administration": None,
                "use": use,
                "location": None,
                "page": page,
                "quote": f"{' / '.join(local_names)} {row.get(3, '')} {row.get(4, '')} {row.get(5, '')}".strip(),
                "record_origin": "Source Table",  # parsed from Table 1, not by the LLM
            })

    return records


def main():
    records = extract_records()
    CACHE_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    taxa = {" ".join(r["name_in_text"].split()[:2]) for r in records}
    counts = {label: sum(row["community"] == label for row in records) for label in COMMUNITIES.values()}
    print(f"wrote {len(records)} plant-use records from {len(taxa)} taxa: {counts}")
    print("every row matched to one PDF page; no API key used")


if __name__ == "__main__":
    main()
