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
cp .env.example .env        # add your free GROQ_API_KEY (https://console.groq.com/keys)
make build                  # rebuild data/ethnohack.db from data/raw
make app                    # open the demo at http://localhost:8501
make test                   # unit tests
make eval                   # accuracy against eval/gold.csv
```

CI (GitHub Actions, `.github/workflows/tests.yml`) runs `make test`, an offline `make build` and `make eval` on every PR.

No `make` (Windows)? Run the commands from the Makefile directly, e.g. `python -m pipeline.build`.

## App pages

| Page | What it shows | Needs a key? |
| --- | --- | --- |
| **Language** | Sidebar toggle Shqip / English (default Shqip) for all interface text; study data stays in the language of the source | No |
| **Plant profile** | Fact sheet per plant: uses with page and quote, community, "was the same preparation tested?", PubMed candidates, safety flags, map | No |
| **Search & compare** | Filter and compare records across plants, parts, preparations | No |
| **Map of uses** | All records on one map (village pin or study-area circle), filters by community, study, use and preparation, optional GBIF occurrence heat map, which plants the communities share, flagged plants | No |
| **Research gaps** | Every plant with its preparation verdict, gaps first, CSV export | No |
| **Ask the librarian** | Chat that answers only from the fact sheets, with sources | Free `GROQ_API_KEY` |
| **Data quality review** | Check, correct and verify records; audit log | No |
| **Add a study** | Upload a new study; the LLM extracts records and they join the map | Free `GROQ_API_KEY` |

## Status and remaining work

Last updated 2026-11-07. **Rule: only free services.** Nobody on the team pays for an API; Groq's free
key is the only LLM key we use. Branch names use `feat/`, `fix/`, `docs/`, `chore/` prefixes; open a PR
per change.

### Done

- Pipeline: ingest, extraction (Groq free, strict schema, quote must be found on the cited page),
  dialect-tolerant names with GBIF, PubMed evidence tags, safety rules, Wikidata compounds, places.
- Data: Sharr Mountains study (Mustafa et al. 2015), **569 use records, 108 plants, 3 communities**
  (Albanian 167, Bosniak/Gorani 252, Turkish 150), all from Table 1 by the table parser, each matched to
  its PDF page. Every plant name is confirmed by GBIF. PubMed candidates
  are loaded for all 108 plants, GBIF occurrences for 96, Wikidata compounds for 102 (`make stats`); all responses are
  cached in `data/cache/api/`, so `OFFLINE=1 make build` reproduces the database.
- Preparation check (**Research gaps** page): 3 plants manually reviewed, 18 with a same-preparation
  human study tag, 50 same preparation in lab/animal only, **11 research gaps** (studies exist, none with
  the preparation people use), 26 not comparable by keywords.
- Communities: **18 plants are used by all three communities**; 11 only by Albanians, 24 only by
  Bosniaks/Gorani, 18 only by Turks (**Map of uses** page).
- `make eval`: 23 hand-checked gold rows, recall 23/23, local name to plant 23/23 (this checks the
  table parser; LLM extraction has no gold rows yet).
- App: the seven pages above. 46 tests pass (`make test`). `make stats` writes the slide numbers to `docs/numbers.md`; the demo walk-through is in `docs/demo-script.md`.

### Remaining, in order of priority

Tick a box in your PR when you finish an item.

**1. Free Groq key (5 min, everyone who runs the demo)**
- [ ] Create a key at https://console.groq.com/keys (free) and put `GROQ_API_KEY=...` in `.env`.
  Never commit `.env`.

**2. Chat assistant check (30 min)**
- [ ] With the key set, open **Ask the librarian** and ask at least 6 questions, 3 in Albanian and 3 in
  English, e.g. "Për çfarë përdoret kamomili?", "Which plants were used for coughs?", "Is St John's wort
  safe?". Each answer must cite `R`/`P`/`F` ids that exist and must refuse doses.
- [ ] Write the questions that worked into the demo script (item 8).

**3. Add a second study, the "new study" demo (1-2 h, needs item 1)**
- [ ] Download Mustafa et al. 2012, *Medical ethnobotany of the Albanian Alps in Kosovo*, J Ethnobiol
  Ethnomed 8:6: PDF https://ethnobiomed.biomedcentral.com/track/pdf/10.1186/1746-4269-8-6 (PMC3285519).
  Confirm the licence on the article page.
- [ ] `make app` → **Add a study**: short id `albanian_alps_2012`, study area **Rugovë** (Kosovo side;
  `Bjeshkët e Nemuna` in `places.csv` sits on the Albanian/Montenegrin side). Groq's free rate limit can
  make this take a few minutes; the page waits and retries.
- [ ] Spot-check 20 extracted records against the PDF (page and quote) on **Data quality review**.
- [ ] Add 15-20 checked rows from this study to `eval/gold.csv`, run `make eval`, and write the recall
  here. These are the first gold rows for LLM extraction.
- [ ] Commit `data/raw/albanian_alps_2012.pdf`, `data/cache/extract/albanian_alps_2012.json`,
  `data/seed/sources.csv` and the new files under `data/cache/api/`, so `OFFLINE=1 make build`
  reproduces the demo.
- [ ] If Groq is not available on demo day, the cached extraction still works offline.

**4. Review records (1 h, no key)**
- [ ] All 573 records are `Needs Review`. On **Data quality review**, verify at least 30 records against
  the PDF (pick the most reported plants). The number of verified records goes on a slide.

**5. Reviewed modern evidence (1-2 h, no key)**
- [ ] `data/seed/reviewed_evidence.csv` has 4 papers. Add 5-10 more for the plants shown in the demo
  (e.g. *Matricaria chamomilla*, *Hypericum perforatum*, *Sideritis scardica*, *Urtica dioica*): read the
  PubMed abstract and fill preparation, comparison and limitation. These turn a plant's verdict into
  "Manually reviewed".
- `data/seed/reviewed_evidence_drafts.csv` holds 8 draft rows filled from PubMed abstracts only (status `draft - needs human check`); the app does not read it.
- A human must read each full paper and check the preparation, comparison and limitation before trusting a draft.
- Move only confirmed rows into `reviewed_evidence.csv` (drop the `status` column); never copy a draft over unchecked.

**6. Safety and names seed data (1 h, no key)**
- [ ] `data/seed/risk_rules.csv` has 5 rules. Add EMA/HMPC monograph rules for other plants in the data
  that have one (check the EMA herbal list; cite the URL; no doses).
- [ ] Optional: request a free IUCN token (https://api.iucnredlist.org/, non-commercial) and set
  `IUCN_TOKEN` for conservation flags.
- [ ] Check `data/seed/albanian_names.csv` (67 names) against the studies for wrong pairs.

**7. Licences and repo hygiene (30 min)**
- [ ] Confirm the licence of every study in `data/seed/sources.csv` and every data source in the
  licence table below; remove the line "Check every licence before submission" when done.
- [ ] `make test` green, `OFFLINE=1 make build && make eval` runs on a clean clone, no `.env` or keys in
  git history (`git log -p | grep -i "api_key="` shows only empty values).

**8. Demo and presentation (2-3 h)**
- [ ] Demo script (5 min): profile of a plant by its Albanian name → "was the same tea tested?" →
  Research gaps → Map of uses (community overlap) → chat question → Add a study (or show the cached
  result).
- [ ] Rehearse with `OFFLINE=1` and no network, so nothing depends on live APIs.
- [ ] Slides with the numbers above: records, plants, communities, plants shared by all three
  communities, research gaps, eval recall, verified records. Take screenshots as a fallback.

**Later / nice to have** (from the proposal's "other ideas", only if time is left)
- Time slider comparing old and new records (needs dated studies).
- Conservation layer on the map (needs IUCN or a national red list).
- Family recipes with consent; folklore layer kept separate from medicine; habitat map.

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

Everything runs on free services. No paid key is needed.

- `GROQ_API_KEY` (free at https://console.groq.com/keys) is used to extract plant-use records
  from a study that has no cached extraction, and by the chat page. Extraction uses
  `GROQ_EXTRACT_MODEL` (default `openai/gpt-oss-120b`) with a strict JSON schema, two pages per
  request (`GROQ_PAGES_PER_CALL`), and waits and retries when the free rate limit is hit.
  Every extracted record must have its quote found on the cited page, or it is dropped.
- `ANTHROPIC_API_KEY` is optional (paid) and used only with `EXTRACT_PROVIDER=anthropic`.
- The GBIF, PubMed and Wikidata lookups run during a normal online build and do not use
  an LLM key. Their responses are cached under `data/cache/api/`.
- `OFFLINE=1` makes the build use saved API responses. It cannot fetch missing data; an
  uncached study with no LLM key will have no extracted records.
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
| 2 Extract | `pipeline/extract.py` | An LLM (Groq, free; Anthropic optional) reads each study and returns plant-use records (plant, part, preparation, use, page, verbatim quote) | **Yes** |
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

**In the app:** open **Add a study** (Curation), upload the PDF, fill in title, citation, link, licence and
study area, and press *Read the study*. `pipeline/add_study.py` saves the file to `data/raw/`, appends the
study to `data/seed/sources.csv`, lets the LLM extract the records (free `GROQ_API_KEY`; the result is
cached in `data/cache/extract/`), matches names and places, and looks up evidence, flags and maps only for
plants new to the database. The page shows the new records on a map with page and quote. Commit the new
files under `data/` to keep them. If nothing is extracted, nothing is saved.

**By hand:**

1. Put the PDF in `data/raw/` (use a short file name, e.g. `mustafa2012.pdf`).
2. Add a row to `data/seed/sources.csv` with title, citation, URL, licence and `study_area`
   (the region the study covers, e.g. `Malet e Sharrit`; it must be a place or alias in
   `data/seed/places.csv`). Records that name no village are located there (`geo_precision = study`).
3. Set the free `GROQ_API_KEY` in `.env` before the first build if you want the LLM to extract
   this study. Otherwise, provide a checked extraction cache at
   `data/cache/extract/<name>.json`. A cached extraction is used before any API call.
4. Run `make build`. Network lookup responses are cached under `data/cache/api/`.
5. Hand-check extracted records against the paper and add verified examples to
   `eval/gold.csv`, then run `make eval`.

## Where each use was recorded

`make build` stores a place for every use record in the `uses` table: `place`, `lat`, `lon` and
`geo_precision`. `record` means the record names the village or town; `study` means only the
study area is known, so the coordinates mark the region, not a spot; empty means the record
cannot be placed. The **Map of uses** page draws these columns (`pipeline/atlas.py` groups records by place
and counts the plants each community shares).

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
