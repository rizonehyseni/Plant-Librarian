# Devpost page: copy and paste

Fields in the order Devpost asks for them. Numbers come from `docs/numbers.md` (`make stats`); if the
data changes, update them from there.

---

## Project name

Plant librarian

## Tagline (max 200 characters)

Traditional plant knowledge from Kosovo and Albania, read from the studies, checked against modern science, and every line linked to its source.

## Track

Track 1: Traditional knowledge

## Team

Rizonë Hyseni, Dua Bilalli, Sara Kycyku, Rrezon Ibishi

## Links

- Live app: https://plant-librarian.streamlit.app/?lang=en
- Code: https://github.com/rizonehyseni/Plant-Librarian
- Slides: `docs/submission/slides.pdf` in the repo

## Built with

python, streamlit, sqlite, groq, gpt-oss-120b, whisper, gbif, pubmed, wikidata, plantnet, folium, rapidfuzz, pymupdf, github-actions

---

## About the project (story)

### Inspiration

In the villages of the Sharr Mountains and the Albanian Alps, older people still know which plant to pick for a cough, for sleep or for a wound. Researchers have written this knowledge down in open-access studies, and scientists publish thousands of papers on the same plants. But nobody connects the two. The knowledge is scattered across PDFs with different table formats, the same plant has a different name in every village (*Hithi*, *Kopriva* and *Yakici* are all nettle), and modern studies usually test something people never use: an essential oil or an alcohol extract instead of the tea a grandmother actually drinks.

We wanted one question to take seconds instead of days: **"Was the tea my grandmother drinks ever tested?"**

### What it does

Plant librarian is a bilingual (Albanian and English) web app built on traditional-use records from open studies of Kosovo.

- **Plant profile:** type a plant's name the way people say it, in dialect or Latin, or identify it from a photo. You see how each community uses and prepares it, the study page and exact quote behind every line, what modern studies tested, and any safety flag. It never shows a dose.
- **Was the same preparation tested?** For every plant we compare the traditional preparation (tea, decoction, ointment…) with the preparations tested in PubMed papers. **17 plants are research gaps**: studies exist, but none tests what people actually use.
- **Priorities:** 36 plants are used for the same complaint by two or more independent groups, and their preparation was never tested in people. Top of the list: hop (*Bari sherbetit*), drunk as a tea for sleep and nerves in both regions; none of 40 PubMed papers tests the tea.
- **Knowledge at risk:** 73 plants and 119 uses are reported by one group only. If that group stops passing them on, nothing else records them.
- **Map of uses:** where each use was recorded, and which plants the Albanian, Bosniak/Gorani and Turkish communities share (18 plants are used by all three).
- **Ask the librarian:** a chat in Albanian or English, by text or voice, that answers only from our fact sheets and cites every claim.
- **Add a study:** upload a new open-access PDF; the AI reads it into rows and the plants appear on the map.
- **Share family knowledge:** families can add what they know, with two consents, no names, doses refused, and publication only after a reviewer approves. Entries can be withdrawn.
- **Fact sheet and QR:** print a sourced one-page fact sheet for any plant or share it with a QR code.

### How we built it

1. **Read:** two open-access studies (Sharr Mountains, Mustafa et al. 2015, CC BY 4.0; Albanian Alps/Rugovë, Mustafa et al. 2012, CC BY 2.0). The Sharr table is parsed with rules; the Alps study is extracted with a free LLM on Groq (`gpt-oss-120b`) with a strict JSON schema.
2. **Ground:** each extracted row must quote the study, and it is kept only if that quote is found on the cited PDF page. An automatic check runs on every build.
3. **Name:** dialect names are matched with fuzzy search and every plant is confirmed against GBIF.
4. **Compare:** PubMed candidates, GBIF occurrences, Wikidata/LOTUS compounds and EMA/HMPC safety rules. Verdicts, priorities and knowledge-at-risk are written rules, not AI.
5. **Show:** a Streamlit app with SQLite, Folium maps, Groq Whisper for voice and Pl@ntNet for photos, deployed free on Streamlit Community Cloud.

AI is used only where text has to become a table (reading studies, transcribing voice, phrasing answers from our own fact sheets). Everything that must be right (safety, evidence level, priorities) comes from rules and open databases. Every API response is cached, so one command rebuilds the whole library offline. 65 tests run in GitHub Actions.

**Strict rule: only free services.** Nothing in the project needs a paid key.

### Results

- 689 use records, 145 plants, 3 communities, 2 studies; every record has a page and a quote.
- 95% recall (40 of 42) on hand-checked gold rows; 677 of 689 records pass the automatic PDF check, and the 12 that fail are flagged for a person to fix.
- 141 of 145 plants have PubMed candidates; 21 carry an EMA/HMPC safety flag.

### Challenges we ran into

- **Dialect names:** the same plant has many local names, and the same name can mean different plants. We combined fuzzy matching, a curated Albanian name list and GBIF confirmation.
- **Hallucinations:** an LLM can invent a plausible use. We made the quote mandatory and drop any row whose quote is not on the cited page.
- **Messy PDFs:** table rows that run across pages, scanned appendices with no text, and API limits on the free tier. We made the extraction resumable and retried rejected chunks page by page.
- **Honesty:** a machine check is not a human verification. Records stay "Needs review" until a named person verifies them, and the app always says that traditional use is not proof that a remedy works.

### Accomplishments that we're proud of

- A concrete, sourced list of plants that science should test next, built from what local communities actually do.
- Knowledge from three communities side by side, showing both shared heritage and what only one group still remembers.
- Fully bilingual, voice-enabled and usable by non-researchers, while every line stays traceable to a page in a study.

### What we learned

Traditional knowledge and modern science often talk about the same plant but not the same preparation. Grounding every AI output in a source page made the AI useful instead of risky. Consent and doses need to be designed in from the start, not added later.

### What's next for Plant librarian

- More open studies from Kosovo and Albania (Gollobordo, southern Kosovo).
- Verification of records with local experts and universities.
- Conservation status, to show whether a plant itself is at risk.
- The priority list offered to pharmacy and biology students as thesis topics.
- Collecting family knowledge in schools and villages, with consent.

*Research prototype. Traditional use is not proof that a remedy works, and nothing here is medical advice.*
