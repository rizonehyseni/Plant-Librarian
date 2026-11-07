# Technical notes

Details behind the README: data, keys, every pipeline step and app feature.

## Pages

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

## Deploy a public link (free, Streamlit Community Cloud)

1. Go to https://share.streamlit.io and sign in with the GitHub account that owns this repo (private repos
   work; Streamlit asks for permission once).
2. **Create app** → *Deploy a public app from GitHub*: repository `rizonehyseni/Plant-Librarian`, branch `main`,
   main file `app/app.py`. Under *Advanced settings* pick **Python 3.12**.
3. In *Advanced settings → Secrets* paste (TOML, quotes required):
   ```toml
   GROQ_API_KEY = "gsk_..."
   # optional
   PLANTNET_API_KEY = "..."
   APP_URL = "https://<your-app>.streamlit.app"
   ```
   Streamlit Cloud also exposes these as environment variables, which is how the app reads them.
4. **Deploy.** The first start installs the requirements (a few minutes) and then builds the database from
   the committed caches, offline, in about 10 seconds.
5. Copy the app link into the `APP_URL` secret (step 3) so the QR codes point to it, and *Reboot app*.

On the cloud the disk is temporary: reviews, approved family-knowledge entries and studies added in the app
are lost when the app restarts. Make those changes locally and commit them; the cloud copy is for showing.

## About the data

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

## What needs an API key

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
  for the whole app (for the slides). QR codes are PNG images from the `qrcode` package; the printable fact sheet uses an inline SVG one.
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
