# Team status and remaining work

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
- [x] 65 tests, GitHub Actions CI, `make stats` for slide numbers, demo walk-through in `docs/demo-script.md`.
- [x] `.env` and its editor backups are git-ignored; no keys in the repo.

### Remaining, in order of priority

Tick the box in your PR when you finish an item. ⏱ = rough time.

**1. Verify records — most convincing number for the jury (⏱ 1 h, anyone, no key)**
- [x] **Automatic PDF check** (`pipeline/autocheck.py`, runs in `make build`): **677 of 689 records passed**
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
- [x] Live at https://plant-librarian.streamlit.app (`GROQ_API_KEY` and `APP_URL` in *Secrets*).

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
- [x] Slides: `docs/submission/slides.pdf` (10 slides, `make slides`); Devpost text in `docs/submission/devpost.md`.
- [ ] Demo story: search *Hithi* (all three communities) → "was the same tea tested?" → **Priorities** (hop)
  → **Map of uses** → chat by voice → **Add a study** (cached Alps result) → **Share family knowledge**.
- [ ] Rehearse twice. Everything except chat, voice and photo works with `OFFLINE=1`; keep screenshots as a
  fallback for those three.

**Later / nice to have**
- Time slider comparing old and new records (needs dated studies); habitat map; folklore layer kept
  separate from medicine; reviewer sign-in (`st.login`) for the *Share family knowledge* review section.
