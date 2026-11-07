# Pitch video script (about 7 minutes, limit 10)

Record the screen and voice (OBS, or Zoom alone with "Record"). Use the slides
(`docs/submission/slides.pdf`) for the pitch parts and the live app for the demo:
https://plant-librarian.streamlit.app/?lang=en

Speakers are a suggestion; swap freely. Speak slowly; one idea per sentence.

**Before recording**
- Open the app once to wake it up (Streamlit Cloud sleeps when nobody uses it), and click every page once.
- Browser zoom 125%, close other tabs and notifications.
- Test the microphone question once; if Groq is slow, skip the voice part rather than wait on camera.
- Say at least once: traditional use is not proof that a remedy works; the app never gives doses.

---

## Part 1: pitch (slides 1-3) · 0:00-1:30

**Slide 1 (title) · Rizonë · 0:00-0:20**
"Hi, we are Rizonë, Dua, Sara and Rrezon, and this is Plant librarian, for Track 1, Traditional knowledge."

**Slide 2 (problem) · Rizonë · 0:20-1:00**
"In the Sharr Mountains and the Albanian Alps, older people still know which plant to pick for a cough, for
sleep or for a wound. Researchers wrote this down in open studies, and scientists publish on the same plants.
But nobody connects the two. The same plant has a different name in every village: Hithi, Kopriva and Yakici
are all nettle. And modern studies usually test an essential oil or an alcohol extract, not the tea people
drink. So a simple question, 'was my grandmother's tea ever tested?', takes a student days."

**Slide 3 (what we built) · Dua · 1:00-1:30**
"Plant librarian reads the studies into rows with the page and exact quote, keeps a row only if that quote is
really on the page, matches dialect names to the right plant with GBIF, and compares each traditional
preparation with what PubMed studies tested. AI only turns text into tables. Everything that must be right,
like safety and evidence, comes from written rules and open databases."

## Part 2: live demo · 1:30-5:30

**Plant profile · Dua · 1:30-2:30**
- Type `Hithi` in the search box.
- "I type the name people use at home. It finds nettle, used by all three communities: Albanian, Bosniak/Gorani
  and Turkish."
- Open one card's **Excerpt from the paper**: "Every use shows the page and the exact quote."
- Scroll to **Was the same preparation tested?**: "People drink it as a tea. Of 38 PubMed papers, the tea was
  only tested in the lab or in animals."
- Show the safety flag and say: "We never show a dose."
- Click **QR code** / **Download fact sheet**: "Anyone can print or share a sourced fact sheet."

**Research gaps and priorities · Sara · 2:30-3:40**
- Open **Priorities**.
- "We ran this check for all 145 plants. 17 are research gaps: studies exist, but none tests what people use."
- Point to hop: "Number one is hop, Bari sherbetit. Albanian and Turkish families in Sharr and people in
  Rugovë drink it as a tea for sleep and nerves. Three independent groups, two regions, and none of 40 papers
  tests the tea. That is a ready thesis topic for a pharmacy student."
- Switch to **Knowledge at risk**: "73 plants and 119 uses are reported by one group only. If they stop passing
  them on, nothing else records them."

**Map of uses · Sara · 3:40-4:10**
- Open **Map of uses**, scroll to the community table.
- "Every record is on the map. 18 plants are shared by all three communities; others belong to one only."

**Ask the librarian · Rrezon · 4:10-5:00**
- Open **Ask the librarian**, click the example question or type "Was Bari sherbetit tea ever tested?"
- "It answers only from our fact sheets and cites every claim." Open **Sources**.
- Press the microphone and say "Për çfarë përdoret Hithi?" "You can also ask by voice, in Albanian."

**Add a study and share knowledge · Rrezon · 5:00-5:30**
- Open **Add a study**: "A new open study goes in here and appears on the map."
- Open **Share family knowledge**: "Families can add what they know, with consent, no names, doses refused, and
  only published after review."

## Part 3: trust and close (slides 8-10) · 5:30-7:00

**Slide 8 (trust) · Dua · 5:30-6:10**
"We measured it. 95% recall on 42 hand-checked rows. 677 of 689 records pass the automatic check against the
PDF, and the 12 that fail are flagged for a person. Records stay 'needs review' until a named person verifies
them. 65 tests, and one command rebuilds everything offline. And everything runs on free services."

**Slide 10 (next) · Rizonë · 6:10-7:00**
"Next: more studies from Kosovo and Albania, verification with local experts, conservation status, and giving
the priority list to students as research topics. Traditional use is not proof that a remedy works; this is a
map of what to test next, built so this knowledge is not lost. Scan the QR code and try it. Thank you."

---

**Upload:** YouTube (Unlisted is fine) or Vimeo, then paste the link on Devpost. Check that it plays when
signed out.
