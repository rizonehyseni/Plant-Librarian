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

The repo includes a **synthetic test fixture** and one real, open-access Sharr Mountains
study (`data/raw/cross_cultural_sharr_2015.pdf`). The committed extraction cache contains
569 community-labelled medicinal-use rows across 108 plant taxa from Table 1. These include
Albanian, Bosniak/Gorani, and Turkish reports, each matched to its source PDF page; they are
table-derived records, not Claude output. The paper reports 114 medicinal taxa overall, so
some taxa without a clearly labelled, page-verifiable use row are still absent. The separate
food and handicraft tables are not loaded in the app. The app hides the synthetic fixture.

Regenerate the Sharr table cache without an API key with `python -m pipeline.extract_sharr_table`.
The script reads the committed article XML and PDF, separates the ALB, BOG (Bosniak/Gorani),
and TUR labels, excludes fungi, and requires each record's table text to match its PDF page.

`eval/gold.csv` contains 23 real-study examples whose local name, plant part, preparation,
reported use and page were checked against the source PDF. The synthetic fixture rows remain
in the file for reference but are excluded from `make eval`. A gold row counts as found when a
record has the same page, community, local name, part, preparation and use, and the same plant,
written either as in the study or as the GBIF accepted name (e.g. *Chamomilla recutita* =
*Matricaria chamomilla*). Combined local-name aliases are matched individually. The 23 rows
are a small sample, so `make eval` reports recall, not precision. The current Sharr records
come from the table parser, not from Claude, so this checks the parser.

### What needs an API key

- The Anthropic key is used only to extract plant-use records from a study that has no
  cached extraction. Without the key, that study is skipped by extraction.
- The GBIF, PubMed and Wikidata lookups run during a normal online build and do not use
  the Anthropic key. Their responses are cached under `data/cache/api/`.
- `OFFLINE=1` makes the build use saved API responses. It cannot fetch missing data; an
  uncached study with no Anthropic key will have no extracted records.
- IUCN conservation lookups need the separate optional `IUCN_TOKEN`.
- The chat page (**Ask the librarian**) needs `GROQ_API_KEY` (free at https://console.groq.com/keys).
  `GROQ_MODEL` picks the model (default `openai/gpt-oss-120b`).

## Was the same preparation tested?

`pipeline/compare.py` compares each plant's traditional preparation (e.g. infusion → water-based)
with the preparation tags of its top PubMed results, using rules only (no AI). Each plant gets one verdict:

| Verdict | Meaning |
| --- | --- |
| Manually reviewed | A paper in `reviewed_evidence.csv` was checked against this preparation |
| Same preparation, human study tagged | A candidate with the same preparation tag is tagged as a human study |
| Same preparation, lab/animal only | Same preparation tag, but no human study tag |
| Only other preparations | **Research gap**: studies exist, none with the preparation people use |
| No studies found | **Research gap**: no PubMed candidates |
| Not comparable by keywords | Eaten fresh, fat ointment etc.; keyword tags cannot compare it |

The verdict is shown on each plant profile. The **Research gaps** page lists all plants with
the gaps first and can export the table as CSV. The chat assistant uses the same check. The
tags are keyword guesses on the top 40 PubMed results, so a verdict points to papers to read.
It is not a review.

## Chat assistant

`app/pages/3_Ask_the_Librarian.py` answers questions in Albanian or English **only from the
fact sheets**, with sources. `pipeline/chat.py` finds the plants named in the question
(scientific, genus or local/dialect name, fuzzy) without AI, builds their fact sheets as numbered
lines and sends only those lines to the Groq model:

| Id | What it cites |
| --- | --- |
| `R12` | Traditional use record (study, page) |
| `E1` | Manually reviewed modern study (`reviewed_evidence.csv`) |
| `P123456` | PubMed candidate, unreviewed keyword match |
| `F1` | Safety or conservation flag |

The model must cite every claim, say when the data does not contain the answer, and never give
doses. The page lists the cited sources under each answer. A question that names no plant
("which plants were used for coughs?") gets a compact index of all records and all flags.
Follow-up questions ("is it safe?") reuse the plant from the earlier question. Each fact sheet
also counts how many PubMed candidates carry the same preparation tag as the traditional use
(the "was the same tea tested?" check). These tags are keyword rules, not a review.

The cached API searches are candidates, not a reviewed scientific conclusion. The app
labels the PubMed keyword tags as preliminary. Manually reviewed comparisons are kept
separate in `data/seed/reviewed_evidence.csv`.

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
| Places | `pipeline/places.py` | Puts each use record on the map: its `location` is matched against the gazetteer `data/seed/places.csv` (exact, inside a phrase, then fuzzy); if no place is named, the study's `study_area` is used | No |

AI is used only to turn unstructured text into rows. Risk, conservation status and evidence
level come from written rules and open databases. Every API and LLM response is cached in
`data/cache/`, so `OFFLINE=1 make build` reproduces the database without network access.

## Adding a study

1. Put the PDF in `data/raw/` (use a short file name, e.g. `mustafa2012.pdf`).
2. Add a row to `data/seed/sources.csv` with title, citation, URL, licence and `study_area`
   (the region the study covers, e.g. `Malet e Sharrit`; it must be a place or alias in
   `data/seed/places.csv`). Records that name no village are located there (`geo_precision = study`).
3. Set `ANTHROPIC_API_KEY` in `.env` before the first build if you want Claude to extract
   this study. Otherwise, provide a checked extraction cache at
   `data/cache/extract/<name>.json`. A cached extraction is used before any API call.
4. Run `make build`. Network lookup responses are cached under `data/cache/api/`.
5. Hand-check extracted records against the paper and add verified examples to
   `eval/gold.csv`, then run `make eval`.

## Where each use was recorded

`make build` stores a place for every use record in the `uses` table: `place`, `lat`, `lon` and
`geo_precision`. `record` means the record names the village or town; `study` means only the
study area is known, so the coordinates mark the region, not a spot; empty means the record
cannot be placed. The app can use these columns to draw a map of recorded uses.

To add a place, add a row to `data/seed/places.csv`: the Albanian name, `|`-separated aliases
(definite forms such as `Prizreni`, Serbian/Macedonian spellings), coordinates (WGS84), country
code and `town` or `region`. Aliases shorter than 4 letters (e.g. `Has`) only match exactly, so
English words in a location do not put a pin on the map. Coordinates are town centres or rough
region centroids. Run `make build` again afterwards.

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
- The place gazetteer is small and hand-made; villages not in it fall back to the study area.
