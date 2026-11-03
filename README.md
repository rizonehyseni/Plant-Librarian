# EthnoHack 2026: Plant librarian (Track 1, Traditional knowledge)

An AI-assisted digital librarian that reads open ethnobotanical studies from Kosovo and the
Albanian-speaking regions and builds a sourced fact sheet for each medicinal plant: which
plant it is, how people prepare and use it, what modern studies tested (and whether they
tested the same preparation people actually drink), and any safety or conservation flags.

> Research prototype. Not medical advice; no doses are shown. Computational results are
> screening estimates, not established medical facts.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add your ANTHROPIC_API_KEY (others optional)
make build                  # rebuild data/ethnohack.db from data/raw
make app                    # open the demo at http://localhost:8501
make test                   # unit tests
make eval                   # accuracy against eval/gold.csv
```

No `make` (Windows)? Run the commands from the Makefile directly, e.g. `python -m pipeline.build`.

The repo ships with one **synthetic** fixture (`data/raw/sample_fixture.txt`) and its cached
extraction so the whole pipeline runs without an API key. Replace it with real studies.

## How it works

| Step | Module | What it does | AI? |
| --- | --- | --- | --- |
| 1 Ingest | `pipeline/ingest.py` | PDF/text in `data/raw/` to page-numbered text | No |
| 2 Extract | `pipeline/extract.py` | Claude reads each study and returns plant-use records (plant, part, preparation, use, page, verbatim quote) | **Yes** |
| 3 Names | `pipeline/names.py` | Dialect-tolerant matching of Albanian names (`data/seed/albanian_names.csv`, rapidfuzz) confirmed with GBIF | No |
| 4 Evidence | `pipeline/evidence.py` | PubMed search per species; rule-based tags for preparation (aqueous, ethanolic, essential oil) and study type | No |
| 5 Flags | `pipeline/flags.py` | Safety flags from `data/seed/risk_rules.csv`, conservation status from IUCN | No |
| 6 Chemistry | `pipeline/chemistry.py` | Known compounds (Wikidata/LOTUS) and RDKit logP: "does the tea even extract it?" | No |
| Map | `pipeline/geo.py` | GBIF occurrences in Kosovo, Albania, North Macedonia | No |

AI is used only to turn unstructured text into rows. Risk, conservation status and evidence
level come from written rules and open databases. Every API and LLM response is cached in
`data/cache/`, so `OFFLINE=1 make build` reproduces the database without network access.

## Adding a study

1. Put the PDF in `data/raw/` (use a short file name, e.g. `mustafa2012.pdf`).
2. Add a row to `data/seed/sources.csv` with title, citation, URL and licence.
3. Run `make build`. The extraction is cached in `data/cache/extract/<name>.json`.
4. Hand-check some records and add them to `eval/gold.csv`, then run `make eval`.

## Data sources and licences

| Data | Source | Licence |
| --- | --- | --- |
| Traditional uses | Open-access studies listed in `data/seed/sources.csv` | Per study (record it there) |
| Plant names | [GBIF Backbone Taxonomy](https://www.gbif.org/) | CC BY 4.0 |
| Occurrences | [GBIF](https://www.gbif.org/) occurrence search | Per dataset (CC0 / CC BY) |
| Modern evidence | [PubMed](https://pubmed.ncbi.nlm.nih.gov/) E-utilities | NLM terms of use |
| Compounds | [Wikidata](https://www.wikidata.org/) / LOTUS | CC0 |
| Conservation | [IUCN Red List API](https://api.iucnredlist.org/) | IUCN terms of use |
| Safety | EMA/HMPC herbal monographs (URLs in `risk_rules.csv`) | Public documents |

Check every licence before submission.

## Known limitations

- The Albanian name dictionary is a small seed and must be checked against the studies.
- Preparation and study-type tags are keyword rules; they can mislabel abstracts.
- logP below 1 as "water-soluble" is a rough screening cut-off, not a measurement.
- IUCN global assessments miss many Balkan plants; add national red lists where possible.
