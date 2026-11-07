# Demo script (5 minutes)

A live walk-through for the judges. Every number here comes from `docs/numbers.md`, which
`make stats` regenerates from the database. If the data changes, run `make stats` again and update
the numbers below from that file, never from memory.

> **Say this at least once, early:** traditional use is not proof that a remedy works. The app shows
> what people reported and what modern studies tested. It never gives doses and is not medical advice.

## The two plants

Both were checked against the database with SQL and `pipeline.compare.compare_all`, and both load in
the app (AppTest smoke test: typing the name opens the right profile with the badge shown below).

| Type in the search box | Plant | Why it tells a good story |
| --- | --- | --- |
| `Hithi` | *Urtica dioica* (nettle) | Used by **all three communities** (Albanian *Hithi*, Bosniak/Gorani *Kopriva*, Turkish *Yakici*). The plant with the most records: 36 (13 Albanian, 12 Bosniak/Gorani, 11 Turkish), all infusions of the aerial parts, all from printed page 18 of the study. Verdict **Same preparation, lab/animal only**: of 38 PubMed candidates, 5 carry a water-based tag and none of those 5 is tagged as a human study. |
| `Bari sherbetit` | *Humulus lupulus* (hop) | **Research gap**. Albanians and Turks (Turkish *Amel*) drink an infusion of the aerial parts for insomnia, as an appetiser and to relax (5 records, page 11). Of 40 PubMed candidates, none is tagged water-based: 3 essential oil, 3 alcohol extract, 1 isolated compound, 33 not stated. Verdict **Only other preparations**. |

Backup plants if a judge asks for more:
- `Rrushi` (typed without the special letter; the study prints *Rrushı*) → *Vitis vinifera*: used by all
  three communities **and** a research gap (leaf infusion for hepatitis and immunity; 0 of 40 candidates
  tagged water-based).
- `Kamomil` → *Matricaria chamomilla*: all three communities, verdict **Manually reviewed** (a team member
  read the paper).
- `Gëllija` → *Juniperus communis*: all three communities, has an EMA safety flag (caution).

## Before the demo (checklist)

- [ ] `OFFLINE=1 make build` on the demo laptop (uses only cached API responses, no network needed).
- [ ] `make stats` and check that `docs/numbers.md` matches the slides.
- [ ] `make test` is green.
- [ ] `GROQ_API_KEY` (free) in `.env` if you want to show **Ask the librarian**. The chat needs the
      network to reach Groq; the rest of the app runs offline.
- [ ] `OFFLINE=1 make app`, open http://localhost:8501, browser zoom 125-150 % so the back row can read it.
      Close other tabs and notifications.
- [ ] Click through every step once (warms the caches, the map tiles load).
- [ ] Fallback screenshots in a folder on the desktop: Hithi profile (header and "Was the same
      preparation tested?"), Bari sherbetit profile, Research gaps page, Map of uses with the community
      table, one chat answer with its Sources expanded, Add a study result (if done).
- [ ] Clear the chat ("Clear conversation") so the page starts with the example cards.

## Live script

Times are cumulative. Each step: **click**, then **say** (1-2 sentences).

### 0. Opening (0:00-0:20)
- **Click:** nothing; the app opens on **Plant profile**.
- **Say:** "Grandmothers in the Sharr Mountains know which plants they use, and scientists publish on the
  same plants, but nobody checks whether the science tested what people actually do. Our plant librarian
  reads the studies and makes that check, with a source for every line."

### 1. Plant profile by its Albanian name (0:20-1:20)
- **Click:** the search box, type `Hithi`, press Enter. The profile switches to *Urtica dioica*.
- **Say:** "I typed the name people use at home, not the Latin one; the librarian matches dialect spellings
  and confirms the plant with GBIF."
- **Click:** point to the badges (local names *Hithi, Kopriva, Yakici*) and the metric "Study use reports: 36".
  Open one card's **Excerpt from the paper**.
- **Say:** "Nettle is used by all three communities, Albanian, Bosniak/Gorani and Turkish, 36 records,
  always as a tea of the aerial parts. Every record shows the page and the exact quote from the study."

### 2. "Was the same preparation tested?" (1:20-2:00)
- **Click:** scroll to **What modern studies tested → Was the same preparation tested?**. Open
  **Candidates tagged with the same preparation**.
- **Say:** "People drink nettle as a tea. Of 38 PubMed papers, 5 are tagged water-based and none of those is
  tagged as a human study, so the tea itself was only tested in the lab or in animals. These are keyword
  tags, a pointer to what to read next, not a review."

### 3. Research gaps (2:00-2:50)
- **Click:** sidebar **Research gaps**. Point to the metric "Research gaps: 11".
- **Say:** "We ran that check for all 108 plants. 11 are research gaps: studies exist, but none with the
  preparation people use."
- **Click:** type `Bari sherbetit` in **Filter by plant or local name**, then **Open profile**.
- **Say:** "Hop, *Bari sherbetit*: people here drink it as a tea for sleep. All 40 papers we found test
  essential oil, alcohol extracts or isolated compounds, none the tea. That is a concrete question a
  pharmacy student could take on." Mention the **Download as CSV** button in one phrase.

### 4. Map of uses, community overlap (2:50-3:40)
- **Click:** sidebar **Map of uses**. Show the map, then scroll to **Which plants do the communities share?**
- **Say:** "Every record is on the map; here the study names only the region, so it is a grey circle, not a
  fake village pin. 18 plants are used by all three communities, while 24 are used only by Bosniaks/Gorani,
  18 only by Turks and 11 only by Albanians, shared knowledge and unique knowledge side by side."
- **Click (optional):** **Plant** select → *Urtica dioica* to show its row in the table.

### 5. Ask the librarian (3:40-4:30) — needs the free `GROQ_API_KEY`
- **Click:** sidebar **Ask the librarian**, type `Për çfarë përdoret Hithi?` ("What is nettle used for?").
  Then `Was Bari sherbetit tea ever tested?`. Open **Sources** under the answer.
- **Say:** "You can ask in Albanian or English. The assistant answers only from our fact sheets, cites
  every claim with a record or paper id, and refuses to give doses."
- Optional safety question: `A është i sigurt Gëllija?` ("Is juniper safe?"): the answer should cite the
  EMA caution flag.
- **Fallback if there is no key, no network, or Groq is rate-limited:** the page shows a yellow "Set
  `GROQ_API_KEY`" box. Say "the chat runs on Groq's free tier; here is an answer from our rehearsal" and show
  the screenshot. Or skip it and say "the chat reads exactly the fact sheet you just saw on the profile".
  (These three questions were checked to find the right plant without the LLM, via `pipeline.chat.retrieve`.)

### 6. Add a study (4:30-4:50)
- **If a second study is cached** (`data/cache/extract/albanian_alps_2012.json`, README item 3): **Add a
  study**, upload the PDF with short id `albanian_alps_2012`, study area *Rugovë*, **Read the study**. The
  cached extraction loads without the network; show the new records on the map.
- **Otherwise skip the upload:** open **Add a study**, scroll to **Studies in the library**.
- **Say:** "A new open-access study goes in here: the AI reads it into rows, each with page and quote, and
  rows whose quote is not on the cited page are dropped. The rest of the pipeline uses rules, not AI."

### 7. Close (4:50-5:00)
- **Say:** "569 sourced records, 108 plants, 3 communities, 11 research gaps, built only on free and open
  data. Traditional use is not proof of efficacy; this is a map of what to test next."

## 1-minute fallback version

If time is cut or the laptop fails (use the screenshots if needed):

1. (15 s) Plant profile, type `Hithi`: "Nettle, used by all three communities, 36 records, each with page
   and quote."
2. (15 s) Scroll to **Was the same preparation tested?**: "People drink it as tea; the tea was tested only in
   lab or animal studies."
3. (20 s) **Research gaps**: "11 of 108 plants are gaps. Hop, *Bari sherbetit*, is drunk as a tea for sleep,
   and none of 40 papers tests the tea."
4. (10 s) "Free data only, every line sourced, no doses; traditional use is not proof of efficacy."

## Slide outline (8 slides)

Numbers from `docs/numbers.md` (`make stats`).

1. **Title**: Plant librarian. Traditional plant knowledge of the Sharr Mountains, checked against modern
   studies. Team, EthnoHack 2026.
2. **Problem**: knowledge lives in old studies and family memory; papers rarely test the preparation people
   use (tea vs. extract). No one connects the two.
3. **What we built**: study PDF → AI extraction with page and quote → dialect-tolerant names (GBIF) →
   PubMed, GBIF, Wikidata, safety rules → app. AI only turns text into rows; the rest is rules and open data.
4. **The data**: 1 study (Mustafa et al. 2015), 569 use records, 108 plants, 3 communities (Albanian 167,
   Bosniak/Gorani 252, Turkish 150 records). PubMed candidates for 108 / 108 plants, GBIF occurrences for
   96 / 108, compounds for 102 / 108.
5. **Shared and unique knowledge**: 18 plants used by all 3 communities; only Albanian 11, only
   Bosniak/Gorani 24, only Turkish 18. Map screenshot. Example: *Hithi / Kopriva / Yakici* (nettle).
6. **Was the same preparation tested?** Verdicts: manually reviewed 3, same preparation with human study
   tag 18, lab/animal only 50, only other preparations 11, no studies 0, not comparable 26.
   **11 research gaps**. Example: hop, *Bari sherbetit*, tea for sleep, 0 of 40 papers tagged water-based.
7. **Trust**: every record has page and quote; eval recall 23/23 = 100 % on hand-checked gold rows
   (local name → plant 23/23); verified records: 0 so far, all 569 are "Needs Review" (update after the
   review session); 5 plants carry a safety flag (3 caution, 2 warning, EMA/HMPC); no doses ever.
8. **Next**: add more studies (Albanian Alps 2012), review records with local experts, reviewed evidence
   for the gap plants, conservation layer. Disclaimer: traditional use is not proof of efficacy; not
   medical advice. Only free services.
