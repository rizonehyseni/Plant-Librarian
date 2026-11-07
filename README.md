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
| **Plant profile** | Search by Albanian or scientific name, or **identify from a photo** (Pl@ntNet, optional free key). **Download a printable fact sheet** and a **QR code** per plant. Fact sheet per plant: uses with page and quote, community, "was the same preparation tested?", PubMed candidates, safety flags, map | No |
| **Search & compare** | Filter and compare records across plants, parts, preparations | No |
| **Map of uses** | All records on one map (village pin or study-area circle), filters by community, study, use and preparation, optional GBIF occurrence heat map, which plants the communities share, flagged plants | No |
| **Research gaps** | Every plant with its preparation verdict, gaps first, CSV export | No |
| **Priorities** | *What should science study next?* (plants used for the same body system by independent groups, preparation untested) and *Knowledge at risk* (plants and uses only one group reports) | No |
| **Ask the librarian** | Chat that answers only from the fact sheets, with sources; ask by typing or **with your voice** (Albanian or English); a small animated botanist greets you | Free `GROQ_API_KEY` |
| **Data quality review** | Check, correct and verify records; automatic PDF check per record (passed / issues, with details); audit log | No |
| **Share family knowledge** | Form to add a traditional use from your family with two consents (sharer and knowledge holder), no names, doses refused; reviewers approve, reject or withdraw; approved entries join the library as *Community Contribution* | No |
| **Add a study** | Upload a new study; the LLM extracts records and they join the map | Free `GROQ_API_KEY` |

## Status and remaining work

Last updated 2026-11-07, evening. **Rule: only free services.** Nobody on the team pays for an API; Groq's
free key is the only LLM key we use. Branch names use `feat/`, `fix/`, `docs/`, `chore/` prefixes; open a PR
per change. CI (tests, offline build, eval) runs on every PR.

### Done ✅

**Data**
- [x] **2 open-access studies, 689 use records, 145 plants** (`make stats`, `docs/numbers.md`):
  - Sharr Mountains, Mustafa et al. 2015 (CC BY 4.0): 569 records, 108 plants, 3 communities (Albanian 167,
    Bosniak/Gorani 252, Turkish 150), parsed from Table 1 without AI, each row matched to its PDF page.
  - Albanian Alps (Rugovë), Mustafa et al. 2012 (CC BY 2.0): 120 records, 88 plants, **extracted with the free
    Groq API**; every record's quote must be found on the cited page. PDF, extraction cache and `sources.csv`
    are committed, so the demo works offline.
- [x] Every plant name confirmed by GBIF. PubMed candidates for 141/145 plants, GBIF occurrences 126,
  Wikidata compounds 131; all responses cached, `OFFLINE=1 make build` reproduces the database.
- [x] **21 plants with a safety flag** from 20 EMA/HMPC rules (each with the EMA URL, no doses).
- [x] Amounts in study tables ("200-300 g") are replaced with `[amount]`: no dose reaches the app.

**Accuracy**
- [x] `make eval`: **42 hand-checked gold rows, recall 40/42 (95%)**; Sharr (table parser) 23/23, Albanian
  Alps (**Groq LLM extraction**) 17/19. The two misses (*Beta vulgaris*, *Brassica oleracea*, p. 5) were not
  extracted.

**Findings (for the slides)**
- [x] Preparation check: 3 plants manually reviewed, 23 same preparation tested in humans, 71 lab/animal only,
  **17 research gaps** (14 only other preparations, 3 no studies), 31 not comparable by keywords.
- [x] **36 research-priority plants**: used for the same body system by 2+ independent groups, preparation
  untested; 15 confirmed in both regions. Top: *Humulus lupulus* (hop, *Bari sherbetit*) for nerves and sleep.
- [x] Communities: **18 plants used by all three Sharr communities**; 11 only Albanian, 24 only Bosniak/Gorani,
  18 only Turkish. **73 plants and 119 uses reported by one group only** (knowledge at risk).

**App** (9 pages, Shqip / English)
- [x] Plant profile with search by Albanian name, **photo identification** (Pl@ntNet), printable **fact sheet**
  and **QR code**; Search & compare; **Map of uses**; Research gaps; **Priorities**.
- [x] **Ask the librarian**: answers only from the fact sheets with sources, **voice questions** (Groq Whisper),
  animated botanist.
- [x] Data quality review with audit log; **Add a study** (upload → extraction → map); **Share family
  knowledge** with two consents, no names, doses refused, reviewer approval and withdrawal.
- [x] Groq key set up and chat working on Rizonë's machine.

**Engineering**
- [x] 61 tests, GitHub Actions CI, `make stats` for slide numbers, demo walk-through in `docs/demo-script.md`.
- [x] `.env` and its editor backups are git-ignored; no keys in the repo.

### Remaining, in order of priority

Tick the box in your PR when you finish an item. ⏱ = rough time.

**1. Verify records — most convincing number for the jury (⏱ 1 h, anyone, no key)**
- [x] **Automatic PDF check** (`pipeline/autocheck.py`, runs in `make build`): **681 of 689 records passed**
  (name, part, preparation, use and quote found on the cited page), **12 have issues**: Sharr table rows that
  start on one page and end on the next, so the parser gave the later page (garlic p.8→7, motherwort p.12→11,
  willow p.16→15, cowberry p.19→18). This is not a human verification; `review_status` is untouched.
- [ ] **0 of 689** records are verified by a person. On **Data quality review**, filter *Automatic PDF check →
  issues* and fix the 12 pages first, then confirm at least 30 (demo plants *Hithi*, *Bari sherbetit*,
  *Kamomil*, and 20 of the AI-extracted Albanian Alps records). Write your name as reviewer and set
  *Manually Reviewed* + *Verified*.

**2. Merge Rrezon's branch (⏱ 10 min, Rrezon)**
- [ ] `codex/rrezon` has 13 new Albanian names and a chamomile allergy rule but no PR yet. Open a PR to `main`.

**3. Deploy a public link (⏱ 30 min, Rizonë + Claude)**
- [ ] Streamlit Community Cloud (free): connect the repo, set `GROQ_API_KEY` (and optionally
  `PLANTNET_API_KEY`) in *Secrets*, then set `APP_URL` to the public link so the QR codes point to it.

**4. Test the live features with real input (⏱ 30 min, needs keys)**
- [ ] Chat: 6 questions, 3 Albanian + 3 English (e.g. "Për çfarë përdoret Hithi?", "Was Bari sherbetit tea
  ever tested?", "A është i sigurt Gëllija?"). Each answer cites existing `R`/`P`/`F` ids and gives no dose.
- [ ] Voice: ask the same in Albanian with the microphone.
- [ ] Photo: get a free Pl@ntNet key (https://my.plantnet.org/ → *Your API key*), add `PLANTNET_API_KEY` to
  `.env`, try a nettle or chamomile photo.

**5. Reviewed modern evidence (⏱ 1-2 h, no key)**
- [ ] `reviewed_evidence.csv` has 4 papers. Read the 8 drafts in `reviewed_evidence_drafts.csv` (from PubMed
  abstracts only, status `draft - needs human check`); move only the confirmed ones into
  `reviewed_evidence.csv` without the `status` column. Never copy a draft over unchecked.

**6. Data fixes (⏱ 1 h)**
- [ ] The Albanian Alps informants are ethnic Albanians (p. 3) but its 120 records have no `community`, so
  the community comparison on **Map of uses** leaves them out. Add a `community` column in `sources.csv`.
- [ ] Optional: free IUCN token (https://api.iucnredlist.org/, non-commercial) → `IUCN_TOKEN` for
  conservation status. The proposal promises "is the plant at risk?"; today only safety flags exist.
- [ ] Check `albanian_names.csv` (67 names, 80 with Rrezon's branch) for wrong pairs.

**7. Licences and clean clone (⏱ 30 min)**
- [ ] Confirm the licence of every source in the table below (Sharr CC BY 4.0, Alps CC BY 2.0, GBIF, PubMed,
  Wikidata, EMA, Pl@ntNet non-commercial); then delete the line "Check every licence before submission".
- [ ] On a clean clone: `pip install -r requirements.txt`, `make test`, `OFFLINE=1 make build`, `make eval`.

**8. Demo and presentation (⏱ 2-3 h)**
- [ ] Slides from the outline in `docs/demo-script.md` with the numbers above, plus the QR code from
  **Share this app** (after item 3).
- [ ] Demo story: search *Hithi* (all three communities) → "was the same tea tested?" → **Priorities** (hop)
  → **Map of uses** → chat by voice → **Add a study** (cached Alps result) → **Share family knowledge**.
- [ ] Rehearse twice. Everything except chat, voice and photo works with `OFFLINE=1`; keep screenshots as a
  fallback for those three.

**Later / nice to have**
- Time slider comparing old and new records (needs dated studies); habitat map; folklore layer kept
  separate from medicine; reviewer sign-in (`st.login`) for the *Share family knowledge* review section.

### About the data

The repo includes a **synthetic test fixture** (hidden in the app) and two real, open-access studies in
`data/raw/`. Sharr Mountains: 569 community-labelled medicinal-use rows across 108 plant taxa from Table 1
(Albanian, Bosniak/Gorani and Turkish reports), each matched to its PDF page; table-derived, not LLM output.
The paper reports 114 medicinal taxa overall, so some taxa without a clearly labelled, page-verifiable row are
absent, and its food and handicraft tables are not loaded. Albanian Alps: 120 rows extracted with Groq.

Regenerate the Sharr table cache without an API key with `python -m pipeline.extract_sharr_table`.
The script reads the committed article XML and PDF, separates the ALB, BOG (Bosniak/Gorani),
and TUR labels, excludes fungi, and requires each record's table text to match its PDF page.

`eval/gold.csv` contains 42 real-study examples (23 Sharr, 19 Albanian Alps) whose local name, plant part,
preparation, reported use and page were checked against the source PDF. The synthetic fixture rows are
excluded from `make eval`. A gold row counts as found when a record has the same page, community, local name,
part, preparation and use, and the same plant, written either as in the study or as the GBIF accepted name
(e.g. *Chamomilla recutita* = *Matricaria chamomilla*). The rows are a sample, so `make eval` reports recall,
not precision, per study: the Sharr rows check the table parser, the Albanian Alps rows check the LLM.

### What needs an API key

Everything runs on free services. No paid key is needed.

- `GROQ_API_KEY` (free at https://console.groq.com/keys) is used to extract plant-use records
  from a study that has no cached extraction, and by the chat page. Extraction uses
  `GROQ_EXTRACT_MODEL` (default `openai/gpt-oss-120b`) with a strict JSON schema, two pages per
  request (`GROQ_PAGES_PER_CALL`), and waits and retries when the free rate limit is hit.
  Every extracted record must have its quote found on the cited page, or it is dropped. For a
  table row the model joins the cells with "..."; each piece must then be on that page.
  The build stores plain hyphens and replaces amounts in a study's table ("200-300 g",
  "2-3 soup spoons") with `[amount]`, so no doses reach the app.
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

## Printable fact sheet and QR codes

- **Download fact sheet** on each plant profile gives a standalone HTML page (`app/factsheet.py`): every use with
  community, place and study page, the preparation verdict, reviewed papers, PubMed candidates, safety flags,
  citations and licences, the disclaimer, and a QR code back to the profile. Open it and print to PDF; no extra
  software is needed.
- **QR code** next to it opens the plant's profile on a phone; **Share this app** in the sidebar shows a QR code
  for the whole app (for the slides). QR codes are inline SVG from the `qrcode` package (free, no image library).
- The QR codes use `APP_URL` when set (put the public link there after deploying), otherwise the address the
  browser used, so on `localhost` they only work on the same computer.

After pulling, run `pip install -r requirements.txt` once for `qrcode`.

## Family knowledge with consent

**Share family knowledge** (Curation) lets anyone add a use they learned at home. `pipeline/contributions.py`:

- needs two consents: the person sharing (CC BY 4.0) and the person who holds the knowledge;
- collects no names of people (only *grandmother*, *neighbour*, ...) and refuses amounts or schedules
  (`200 g`, `2 filxhanë`, `3 times a day`), so no dose is ever stored;
- keeps every entry `pending` in `data/contributions/contributions.csv` until a reviewer approves it;
  approved entries enter the library as source *Community contributions (shared with consent)*, origin
  *Community Contribution*, placed on the map at the chosen village or region, and still `Needs Review` on
  the Data quality page;
- lets a reviewer withdraw a published entry at any time, which removes it from the library.

`make build` adds the approved entries from the CSV, so commit that file to keep them. In this prototype anyone
can review; a real deployment would limit the reviewer section to signed-in reviewers.

## Identify a plant from a photo

On **Plant profile**, switch on *Identify a plant from a photo*, take a photo or upload one, and say what it shows
(leaf, flower, fruit, bark, or not sure). `pipeline/photo.py` sends it to the [Pl@ntNet](https://my.plantnet.org/)
API, which is free for non-commercial use with an account (`PLANTNET_API_KEY` in `.env`, daily quota). The top 3
suggestions are shown with Pl@ntNet's confidence and matched to the library (same species, or same genus), with a
button to open the profile. The page says it is a suggestion, not a confirmed identification, and never to collect or
use a plant on the basis of a photo. Photos are not stored. Without the key the toggle shows how to get one.

To get the key: create an account at https://my.plantnet.org/, open *Your API key* in the account settings, copy it,
add `PLANTNET_API_KEY=...` to `.env`, and restart `make app`.

## Ask with your voice

On **Ask the librarian**, press the microphone (`st.audio_input`), speak, press again. `pipeline/voice.py`
sends the recording to Groq's free Whisper model (`GROQ_WHISPER_MODEL`, default `whisper-large-v3`) with the
interface language as a hint and a short prompt of Albanian plant names, then asks the text like a typed
question. Recordings are not stored. Same free `GROQ_API_KEY` as the chat. The animated botanist on that page
is inline SVG with CSS (no JavaScript, no external files) and stops moving when the system asks for reduced
motion.

## Research priorities and knowledge at risk

`pipeline/priorities.py` uses written rules only, no AI. Each use text is sorted into a body system by
keywords (respiratory, digestive, skin and wounds, nerves and sleep, ...). A **group** is one community in
one study (e.g. Turkish in the 2015 Sharr study; the 2012 Albanian Alps study is one group because it does not
split by community).

- **What should science study next?** A plant is a priority when 2+ independent groups use it for the same
  body system and its preparation verdict is *Only other preparations*, *No studies found* or *Same
  preparation, lab/animal only*. Score: 10 per group, +15 per extra study region, +20 if the preparation was
  never tested, plus a small bonus for many records. These are hypotheses to study, not evidence.
- **Knowledge at risk:** plants that only one group reports, and uses of a known plant that only one group
  reports. A plant missing from a study does not prove that community never knew it (studies asked different
  people), so this list gets more reliable with every study added.

Both views are on the **Priorities** page, with CSV export.

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
| Photo identification | [Pl@ntNet API](https://my.plantnet.org/) (optional) | Free for non-commercial use |
| LLM extraction, chat, speech to text | [Groq](https://console.groq.com/) free tier (`gpt-oss-120b`, Whisper) | Groq terms of use |
| Family knowledge | Entries shared in the app with two consents (`data/contributions/`) | CC BY 4.0, given by the contributor |

Check every licence before submission.

## Known limitations

- The Albanian name dictionary is a small seed and must be checked against the studies.
- Preparation and study-type tags are keyword rules; they can mislabel abstracts.
- logP below 1 as "water-soluble" is a rough screening cut-off, not a measurement.
- IUCN global assessments miss many Balkan plants; add national red lists where possible.
- The place gazetteer is small and hand-made; villages not in it fall back to the study area.
- Body-system categories on the Priorities page come from keywords in the use text; a few uses stay
  uncategorised and some can be mis-sorted.
- *Knowledge at risk* compares only the studies in the library: absence from a study is not proof that a
  community does not know a plant.
- Photo identification and speech to text are suggestions from external models and can be wrong.
