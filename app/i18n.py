"""Albanian / English interface text.

`t("English text")` returns the Albanian translation when the sidebar language is Shqip,
otherwise the English text. Keys are the English strings themselves, so a missing
translation simply shows English. Placeholders use str.format: t("{n} plants", n=3).
Study data (uses, preparations, quotes) stays in the language of the source.
"""
import streamlit as st

LANGUAGES = {"sq": "Shqip", "en": "English"}

SQ = {
    # ---------------------------------------------------------------- navigation and shared
    "Explore": "Eksploro",
    "Assistant": "Asistenti",
    "Curation": "Kurimi i të dhënave",
    "Plant profile": "Profili i bimës",
    "Search & compare": "Kërko dhe krahaso",
    "Map of uses": "Harta e përdorimeve",
    "Research gaps": "Boshllëqet kërkimore",
    "Ask the librarian": "Pyet bibliotekarin",
    "Data quality review": "Kontrolli i cilësisë",
    "Add a study": "Shto një studim",
    "Language": "Gjuha",
    "Research prototype. Traditional-use reports are not proof that a remedy works, and nothing here is "
    "medical advice.": "Prototip kërkimor. Përdorimet tradicionale nuk janë provë se një ilaç funksionon dhe "
    "asgjë këtu nuk është këshillë mjekësore.",
    "No database yet. Run `make build` first, then reopen this page.":
        "Ende nuk ka databazë. Nisni `make build`, pastaj hapeni sërish këtë faqe.",
    "No database yet. Run `make build` first.": "Ende nuk ka databazë. Nisni `make build`.",
    "Open profile": "Hap profilin",
    "Plants": "Bimë",
    "Plant": "Bima",
    "Local name": "Emri lokal",
    "Loading records…": "Po ngarkohen rekordet…",

    # ---------------------------------------------------------------- plant profile
    "EthnoHack 2026 · Traditional knowledge": "EthnoHack 2026 · Dija tradicionale",
    "Plant librarian": "Bibliotekari i bimëve",
    "Type a plant name the way people say it. See how it is used and prepared, what modern studies "
    "tested, and whether it carries a risk. Every line links to its source.":
        "Shkruani emrin e bimës siç e thonë njerëzit. Shihni si përdoret dhe përgatitet, çfarë kanë testuar "
        "studimet moderne dhe a mbart rrezik. Çdo rresht lidhet me burimin e vet.",
    "{n} study records": "{n} rekorde nga studimet",
    "{n} plants": "{n} bimë",
    "Every line sourced": "Çdo rresht me burim",
    "No doses, not medical advice": "Pa doza, jo këshillë mjekësore",
    "The database has no resolved records yet.": "Databaza nuk ka ende rekorde të zgjidhura.",
    "Search a plant name": "Kërkoni emrin e bimës",
    "Try Mullaga, Lule qeni, or Origanum vulgare": "Provoni Mullaga, Lule qeni ose Origanum vulgare",
    "Search by the local (Albanian) name printed in the study or by scientific name.":
        "Kërkoni me emrin lokal (shqip) siç është në studim ose me emrin shkencor.",
    "Family not listed": "Familja nuk është dhënë",
    "not recorded": "nuk është regjistruar",
    "Study use reports": "Përdorime nga studimet",
    "Reviewed papers": "Artikuj të rishikuar",
    "PubMed candidates": "Kandidatë në PubMed",
    "Unreviewed keyword matches": "Përputhje me fjalë kyçe, të parishikuara",
    "Safety flags": "Flamuj sigurie",
    "From the project's limited rule list": "Nga lista e kufizuar e rregullave të projektit",
    "What the study reports": "Çfarë raporton studimi",
    "Reports documented by researchers. They are not proof that a remedy works.":
        "Raportime të dokumentuara nga kërkuesit. Nuk janë provë se ilaçi funksionon.",
    "Preparation not stated": "Përgatitja nuk është dhënë",
    "Part not stated": "Pjesa nuk është dhënë",
    "Study region only": "Vetëm rajoni i studimit",
    "printed page {page}": "faqja e shtypur {page}",
    "Excerpt from the paper": "Fragment nga artikulli",
    "What modern studies tested": "Çfarë kanë testuar studimet moderne",
    "The comparison describes preparation similarity. It does not confirm that the traditional use is effective.":
        "Krahasimi tregon ngjashmërinë e përgatitjes. Nuk konfirmon se përdorimi tradicional është efektiv.",
    "Was the same preparation tested?": "A u testua e njëjta përgatitje?",
    "Same preparation tag": "Etiketë e së njëjtës përgatitje",
    "…tagged as human study": "…prej tyre studim te njerëzit",
    "Candidates tagged with the same preparation": "Kandidatë me të njëjtën përgatitje",
    "Automatic check from keyword tags on the top PubMed results; read the paper before relying on it. "
    "The Research gaps page shows this for every plant.":
        "Kontroll automatik nga etiketat me fjalë kyçe në rezultatet e para të PubMed; lexoni artikullin para se "
        "të mbështeteni te ai. Faqja Boshllëqet kërkimore e tregon këtë për çdo bimë.",
    "No modern study has been manually checked against this plant's reported preparation yet.":
        "Asnjë studim modern nuk është kontrolluar ende me dorë kundrejt përgatitjes së raportuar për këtë bimë.",
    "Reviewed": "Rishikuar",
    "Preparation comparison:": "Krahasimi i përgatitjes:",
    "No additional PubMed candidates are loaded for this plant.":
        "Nuk ka kandidatë të tjerë PubMed për këtë bimë.",
    "All PubMed candidates ({n})": "Të gjithë kandidatët PubMed ({n})",
    "Keyword-matched candidates, not reviewed conclusions. Automated preparation and study-type labels can be wrong.":
        "Kandidatë sipas fjalëve kyçe, jo përfundime të rishikuara. Etiketat automatike të përgatitjes dhe të "
        "llojit të studimit mund të jenë të gabuara.",
    "Safety and conservation": "Siguria dhe konservimi",
    "No item in the project's **limited safety-rule list** matched this plant. The list is incomplete, "
    "so this is not an all-clear or a safety assessment.":
        "Asnjë rregull nga **lista e kufizuar e sigurisë** nuk përputhet me këtë bimë. Lista është e paplotë, "
        "prandaj kjo nuk do të thotë që bima është e sigurt.",
    "Where the uses were recorded": "Ku u regjistruan përdorimet",
    "Green pin: the record names a village or town. Grey pin: the study names only its region, so the marker "
    "is approximate.": "Pin jeshil: rekordi përmend fshatin ose qytetin. Pin gri: studimi përmend vetëm rajonin, "
    "prandaj shënjuesi është i përafërt.",
    "No study-area coordinates are available for these records.":
        "Nuk ka koordinata të zonës së studimit për këto rekorde.",
    "Study area": "Zona e studimit",
    "Village or town named in the record": "Fshat ose qytet i përmendur në rekord",
    "Approximate study-area location": "Vendndodhje e përafërt e zonës së studimit",
    "Where this plant grows · GBIF ({n} records)": "Ku rritet kjo bimë · GBIF ({n} rekorde)",
    "Occurrence points come from GBIF. They are not locations where the study recorded traditional use, and "
    "individual points have not been checked against the paper.":
        "Pikat vijnë nga GBIF. Nuk janë vendet ku studimi regjistroi përdorimin tradicional dhe nuk janë "
        "kontrolluar një nga një kundrejt artikullit.",
    "Occurrence data have not been loaded for this plant yet.": "Nuk ka ende të dhëna GBIF për këtë bimë.",
    "Experimental compound screening": "Shqyrtim eksperimental i përbërësve",
    "Sources, methods, and current limits": "Burimet, metodat dhe kufizimet",

    # ---------------------------------------------------------------- verdicts (pipeline/compare.py)
    "Manually reviewed": "Rishikuar me dorë",
    "Same preparation, human study tagged": "E njëjta përgatitje, studim te njerëzit",
    "Same preparation, lab/animal only": "E njëjta përgatitje, vetëm laborator/kafshë",
    "Only other preparations": "Vetëm përgatitje të tjera",
    "No studies found": "Nuk u gjetën studime",
    "Not comparable by keywords": "Nuk krahasohet me fjalë kyçe",
    "A team member checked a paper against this preparation.":
        "Një anëtar i ekipit kontrolloi një artikull kundrejt kësaj përgatitjeje.",
    "At least one candidate tagged with the same preparation is tagged as a human study.":
        "Të paktën një kandidat me të njëjtën përgatitje është studim te njerëzit.",
    "Candidates with the same preparation tag exist, but none is tagged as a human study.":
        "Ka kandidatë me të njëjtën përgatitje, por asnjë nuk është studim te njerëzit.",
    "Studies exist, but none is tagged with the preparation people use.":
        "Ka studime, por asnjë me përgatitjen që përdorin njerëzit.",
    "PubMed returned no candidate papers for this plant.": "PubMed nuk ktheu asnjë artikull për këtë bimë.",
    "The traditional preparation (e.g. eaten fresh, fat ointment) has no matching keyword tag.":
        "Përgatitja tradicionale (p.sh. e ngrënë e freskët, melhem me dhjamë) nuk ka etiketë përkatëse.",
    "water-based (tea, infusion, decoction)": "me ujë (çaj, infuzion, zierje)",
    "alcohol-based (tincture, rakia)": "me alkool (tinkturë, raki)",
    "macerated in oil": "e njomur në vaj",
    "eaten, fat ointment or other": "e ngrënë, melhem me dhjamë ose tjetër",
    "not stated": "nuk është dhënë",

    # ---------------------------------------------------------------- research gaps
    "Was the preparation people actually use, such as a hot tea, ever tested? Plants with no matching studies are listed first.":
        "A u testua ndonjëherë përgatitja që përdorin vërtet njerëzit, si çaji i nxehtë? Bimët pa studime "
        "përkatëse dalin të parat.",
    "No PubMed candidate is tagged with the preparation people use, or there are no studies at all.":
        "Asnjë kandidat PubMed nuk ka përgatitjen që përdorin njerëzit, ose nuk ka studime fare.",
    "Same preparation tag, but no human-study tag": "E njëjta përgatitje, por pa studim te njerëzit",
    "Same preparation tag and a human-study tag": "E njëjta përgatitje dhe studim te njerëzit",
    "Lab / animal only": "Vetëm laborator / kafshë",
    "Human study tagged": "Studim te njerëzit",
    "Show verdicts": "Shfaq vlerësimet",
    "Filter by plant or local name": "Filtro sipas bimës ose emrit lokal",
    "Plants whose traditional preparation has not been studied":
        "Bimët, përgatitja tradicionale e të cilave nuk është studiuar",
    "no local name": "pa emër lokal",
    "All plants · {n}": "Të gjitha bimët · {n}",
    "Traditional preparation": "Përgatitja tradicionale",
    "Verdict": "Vlerësimi",
    "…of which human": "…prej tyre te njerëzit",
    "No plants match this filter.": "Asnjë bimë nuk përputhet me këtë filtër.",
    "Download as CSV": "Shkarko si CSV",
    "How the verdict is decided": "Si vendoset vlerësimi",
    " (research gap)": " (boshllëk kërkimor)",
    "The database has no plant-use records yet.": "Databaza nuk ka ende rekorde përdorimi.",

    # ---------------------------------------------------------------- map of uses
    "Map of recorded uses": "Harta e përdorimeve të regjistruara",
    "Where each traditional use was recorded, across all studies in the library. Filter by community, "
    "plant, use or preparation, and see which plants the communities share.":
        "Ku u regjistrua çdo përdorim tradicional, në të gjitha studimet e bibliotekës. Filtroni sipas "
        "komunitetit, bimës, përdorimit ose përgatitjes dhe shihni cilat bimë i ndajnë komunitetet.",
    "Community": "Komuniteti",
    "Study": "Studimi",
    "Use contains": "Përdorimi përmban",
    "cough, wound, stomach…": "kollë, plagë, stomak…",
    "Preparation": "Përgatitja",
    "All plants": "Të gjitha bimët",
    "Water-based (tea, decoction)": "Me ujë (çaj, zierje)",
    "Oil or fat": "Vaj ose dhjamë",
    "Alcohol": "Alkool",
    "Essential oil": "Vaj esencial",
    "Other or eaten": "Tjetër ose e ngrënë",
    "Use records": "Rekorde përdorimi",
    "Communities": "Komunitete",
    "Studies": "Studime",
    "No record matches these filters.": "Asnjë rekord nuk përputhet me këta filtra.",
    "Green pin: the record names a village or town. Grey circle: only the study area is known, so the circle "
    "marks the region, not a spot. Circle size grows with the number of records.":
        "Pin jeshil: rekordi përmend fshatin ose qytetin. Rreth gri: dihet vetëm zona e studimit, ndaj rrethi "
        "shënon rajonin, jo një pikë. Rrethi rritet me numrin e rekordeve.",
    "Also show where these plants grow (GBIF occurrences)": "Shfaq edhe ku rriten këto bimë (GBIF)",
    "GBIF points are where the plant was observed, not where a use was recorded.":
        "Pikat GBIF janë ku është vëzhguar bima, jo ku u regjistrua përdorimi.",
    "No GBIF occurrences are loaded for these plants.": "Nuk ka të dhëna GBIF për këto bimë.",
    "{n} GBIF occurrence points for {k} of the filtered plants.":
        "{n} pika GBIF për {k} nga bimët e filtruara.",
    "Which plants do the communities share?": "Cilat bimë i ndajnë komunitetet?",
    "Counts plants with at least one use record per community in the current filter.":
        "Numëron bimët me të paktën një përdorim për komunitet në filtrin aktual.",
    "Used by all": "Të gjithë i përdorin",
    "Only {c}": "Vetëm {c}",
    "{n} plants in total": "{n} bimë gjithsej",
    "Plants used by one community only": "Bimë që i përdor vetëm një komunitet",
    "none": "asnjë",
    "Plants with a safety or conservation flag": "Bimë me flamur sigurie ose konservimi",
    "From the project's limited rule list; no flag does not mean safe.":
        "Nga lista e kufizuar e rregullave; mungesa e flamurit nuk do të thotë e sigurt.",
    "Traditional-use reports, not proof that a remedy works. Not medical advice.":
        "Raportime të përdorimit tradicional, jo provë se ilaçi funksionon. Jo këshillë mjekësore.",
    "village/town": "fshat/qytet",
    "study area": "zona e studimit",
    "records": "rekorde",
    "Most reported": "Më të raportuarat",
    "not stated (community)": "nuk është dhënë",
    "Albanian": "Shqiptarë",
    "Bosniak/Gorani": "Boshnjakë/Goranë",
    "Turkish": "Turq",
    "Not stated": "Nuk është dhënë",

    # ---------------------------------------------------------------- search & compare
    "Search every documented use by name, use, part or preparation, filter the records, and compare up to three plants side by side.":
        "Kërkoni çdo përdorim të dokumentuar sipas emrit, përdorimit, pjesës ose përgatitjes, filtroni rekordet "
        "dhe krahasoni deri në tri bimë krah për krah.",
    "Search names, aliases, uses, or descriptions": "Kërkoni emra, sinonime, përdorime ose përshkrime",
    "Try Çaj mali, Origanum, kamomil, or respiratory": "Provoni Çaj mali, Origanum, kamomil ose respiratory",
    "Clear filters": "Pastro filtrat",
    "Advanced filters": "Filtra të avancuar",
    "Plant species": "Lloji i bimës",
    "Plant parts": "Pjesët e bimës",
    "Preparation methods": "Mënyrat e përgatitjes",
    "Traditional uses": "Përdorimet tradicionale",
    "Geographic locations": "Vendndodhjet",
    "Evidence type": "Lloji i provës",
    "Safety or risk status": "Statusi i sigurisë",
    "Record verification status": "Statusi i verifikimit",
    "Sort results": "Rendit rezultatet",
    "Matching records · {n}": "Rekorde që përputhen · {n}",
    "No records match this search and filter combination. Clear filters or try a broader term.":
        "Asnjë rekord nuk përputhet. Pastroni filtrat ose provoni një term më të gjerë.",
    "Result page": "Faqja e rezultateve",
    "Traditional use": "Përdorimi tradicional",
    "Plant part / preparation": "Pjesa / përgatitja",
    "Recorded location": "Vendi i regjistruar",
    "Compare plants": "Krahaso bimët",
    "Select up to three plant profiles": "Zgjidhni deri në tri bimë",
    "Choose plants to compare": "Zgjidhni bimët për krahasim",
    "Choose one to three plants to compare only the information available in this database.":
        "Zgjidhni një deri në tri bimë për të krahasuar vetëm të dhënat që ka kjo databazë.",
    "Local names": "Emrat lokalë",
    "Documented uses": "Përdorimet e dokumentuara",
    "Preparations": "Përgatitjet",
    "Locations": "Vendndodhjet",
    "Modern study tags": "Etiketat e studimeve moderne",
    "Verification": "Verifikimi",
    "Safety information": "Informacion sigurie",

    # ---------------------------------------------------------------- ask the librarian
    "Ask in English or Albanian. Answers come only from this project's fact sheets (study records, "
    "reviewed papers, PubMed candidates and safety rules), and every claim links to its source.":
        "Pyetni në shqip ose anglisht. Përgjigjet vijnë vetëm nga fletët e projektit (rekordet e studimeve, "
        "artikujt e rishikuar, kandidatët PubMed dhe rregullat e sigurisë) dhe çdo pohim lidhet me burimin.",
    "Try asking": "Provoni të pyesni",
    "Start with one of these": "Filloni me një nga këto",
    "Clear conversation": "Pastro bisedën",
    "Ask about a plant, its uses, studies or risks…": "Pyetni për një bimë, përdorimet, studimet ose rreziqet…",
    "Reading the fact sheets…": "Po lexohen fletët e bimëve…",
    "Sources ({n})": "Burimet ({n})",
    "Research prototype. The assistant never gives doses and is not medical advice.":
        "Prototip kërkimor. Asistenti nuk jep kurrë doza dhe nuk është këshillë mjekësore.",
    "Set `GROQ_API_KEY` in `.env` to use the assistant (free key: https://console.groq.com/keys), then restart the app.":
        "Vendosni `GROQ_API_KEY` te `.env` për të përdorur asistentin (çelës falas: "
        "https://console.groq.com/keys), pastaj rinisni app-in.",

    # ---------------------------------------------------------------- data quality review
    "Check extracted records against the paper, fix them, and mark them verified. Every change is stored in SQLite with an audit trail.":
        "Kontrolloni rekordet kundrejt artikullit, korrigjojini dhe shënojini të verifikuara. Çdo ndryshim "
        "ruhet me historik.",
    "Total records": "Rekorde gjithsej",
    "Verified": "Të verifikuara",
    "Needs review": "Për rishikim",
    "AI-extracted": "Nxjerrë nga AI",
    "Missing citations": "Pa citim",
    "Unresolved names": "Emra të pazgjidhur",
    "No specific location": "Pa vend të saktë",
    "Review queue": "Radha e rishikimit",
    "Review status": "Statusi i rishikimit",
    "Data quality issue": "Problemi i cilësisë",
    "All": "Të gjitha",
    "No records match these filters.": "Asnjë rekord nuk përputhet me këta filtra.",
    "Inspect and review a record": "Shqyrto dhe rishiko një rekord",
    "Select record": "Zgjidh rekordin",
    "No automatic data-quality warnings for this record.": "Nuk ka paralajmërime automatike për këtë rekord.",
    "Local plant name": "Emri lokal i bimës",
    "Scientific plant name": "Emri shkencor i bimës",
    "Plant part": "Pjesa e bimës",
    "Source page": "Faqja e burimit",
    "Record origin": "Origjina e rekordit",
    "Local reviewer": "Rishikuesi",
    "Reviewer note": "Shënimi i rishikuesit",
    "What was checked or corrected?": "Çfarë u kontrollua ose u korrigjua?",
    "Save review": "Ruaj rishikimin",
    "Review saved. The audit log has been updated.": "Rishikimi u ruajt. Historiku u përditësua.",
    "Change history": "Historiku i ndryshimeve",
    "No review actions have been recorded for this record.": "Nuk ka veprime rishikimi për këtë rekord.",

    # ---------------------------------------------------------------- add a study
    "Upload an open ethnobotanical study the librarian has never seen. An AI model reads it, the plant "
    "names are matched, and every record lands on the map with its page and quote.":
        "Ngarkoni një studim etnobotanik të hapur që bibliotekari s'e ka parë kurrë. Një model AI e lexon, "
        "emrat e bimëve përputhen dhe çdo rekord del në hartë me faqen dhe citatin.",
    "Study file": "Skedari i studimit",
    "Title": "Titulli",
    "Short id (optional)": "Id e shkurtër (opsionale)",
    "Citation": "Citimi",
    "Link to the study": "Lidhja e studimit",
    "Licence": "Licenca",
    "Read the study": "Lexo studimin",
    "Records that name no village are put here on the map.": "Rekordet pa fshat vendosen këtu në hartë.",
    "Choose a file and give the study a title.": "Zgjidhni skedarin dhe jepini studimit një titull.",
    "Studies in the library": "Studimet në bibliotekë",
    "Extracted records": "Rekordet e nxjerra",
    "Where the new records were made": "Ku u regjistruan rekordet e reja",
    "Records": "Rekorde",
    "New plants": "Bimë të reja",
    "Placed by village": "Me fshat të saktë",
    # ---------------------------------------------------------------- added: review values, sort, issues
    "AI Extracted": "Nxjerrë nga AI",
    "Source Table": "Nga tabela e studimit",
    "Manually Reviewed": "Rishikuar me dorë",
    "Needs Review": "Për rishikim",
    "Not available in current data": "Nuk ka të dhëna",
    "Plant name": "Emri i bimës",
    "Scientific name": "Emri shkencor",
    "Number of documented uses": "Numri i përdorimeve",
    "Verification status": "Statusi i verifikimit",
    "tags": "etiketat",
    "invalid_citation": "Citim i pavlefshëm",
    "missing_citation": "Mungon citimi",
    "missing_location": "Mungon vendi",
    "missing_plant_part": "Mungon pjesa e bimës",
    "missing_preparation": "Mungon përgatitja",
    "missing_source": "Mungon burimi",
    "potential_duplicate": "Mundësi dublikimi",
    "unconfirmed_local_name": "Emër lokal i pakonfirmuar",
    "unresolved_scientific_name": "Emër shkencor i pazgjidhur",
    "Check each row against the page and quote. Correct or verify them on the Data quality review page.":
        "Kontrolloni çdo rresht kundrejt faqes dhe citatit. Korrigjojini ose verifikojini te Kontrolli i cilësisë.",
    "Compares each plant's traditional preparation with the keyword tags of its top PubMed results. A screening "
    "list of what to read or study next, not a review and not evidence that a remedy works.":
        "Krahason përgatitjen tradicionale të çdo bime me etiketat e rezultateve të para të PubMed. Një listë "
        "orientuese se çfarë të lexohet ose studiohet më tej, jo rishikim dhe jo provë se ilaçi funksionon.",
    "Green: the record names a village or town. Grey: only the study area is known.":
        "Jeshile: rekordi përmend fshatin ose qytetin. Gri: dihet vetëm zona e studimit.",
    # ---------------------------------------------------------------- priorities
    'Priorities': 'Prioritetet',
    'Which plants should science study next, and which knowledge only one community still holds. Computed from the library with written rules, no AI.': "Cilat bimë duhet t'i studiojë shkenca më pas dhe cilën dije e mban ende vetëm një komunitet. Llogaritur nga biblioteka me rregulla të shkruara, pa AI.",
    'View': 'Pamja',
    'Top candidates for new studies': 'Kandidatët kryesorë për studime të reja',
    'Unique knowledge per group': 'Dija unike sipas grupit',
    'Plants only one group reports': 'Bimë që i raporton vetëm një grup',
    'Priority plants': 'Bimë prioritare',
    'Preparation never tested': 'Përgatitje e patestuar kurrë',
    'Confirmed in 2+ regions': 'E konfirmuar në 2+ rajone',
    'Plants known by one group only': 'Bimë që i njeh vetëm një grup',
    'Uses known by one group only': 'Përdorime që i njeh vetëm një grup',
    'Groups compared': 'Grupe të krahasuara',
    'Group': 'Grupi',
    'Used for the same body system by 2+ independent groups, preparation not tested in humans': 'Përdoren për të njëjtin sistem të trupit nga 2+ grupe të pavarura; përgatitja nuk është testuar te njerëzit',
    'Studies exist, but none with the preparation people use, or no studies at all': 'Ka studime, por asnjë me përgatitjen që përdorin njerëzit, ose nuk ka studime fare',
    'Reported in more than one study region': 'Raportuar në më shumë se një rajon studimi',
    'A group is one community in one study. When separate groups use a plant for the same kind of complaint, the use was passed on independently: a stronger reason to test it. Ranking: independent groups, then a second region, then whether the preparation was never tested. This is a list of hypotheses to study, not evidence that a remedy works.': "Një grup është një komunitet në një studim. Kur grupe të ndryshme e përdorin një bimë për të njëjtin lloj problemi, dija është trashëguar në mënyrë të pavarur: arsye më e fortë për ta testuar. Renditja: grupet e pavarura, pastaj një rajon i dytë, pastaj nëse përgatitja nuk është testuar kurrë. Kjo është listë hipotezash për t'u studiuar, jo provë se ilaçi funksionon.",
    'No plant meets the rule yet. Add more studies to find independent reports.': 'Asnjë bimë nuk e plotëson ende rregullin. Shtoni studime për të gjetur raportime të pavarura.',
    'No other community or study in the library reports this plant': 'Asnjë komunitet ose studim tjetër në bibliotekë nuk e raporton këtë bimë',
    'The plant is known elsewhere, but this use is reported by one group only': 'Bima njihet edhe gjetkë, por këtë përdorim e raporton vetëm një grup',
    'If the people of that group stop passing it on, nothing else in the library records this knowledge. A plant missing from one study does not prove the others never knew it; the studies asked different people in different places. More studies make this list more reliable.': 'Nëse njerëzit e atij grupi pushojnë ta trashëgojnë, asgjë tjetër në bibliotekë nuk e ruan këtë dije. Mungesa e një bime në një studim nuk provon se të tjerët nuk e njihnin; studimet pyetën njerëz të ndryshëm në vende të ndryshme. Më shumë studime e bëjnë këtë listë më të besueshme.',
    'Uses only one group reports ({n})': 'Përdorime që i raporton vetëm një grup ({n})',
    'What should science study next?': 'Çfarë duhet të studiojë shkenca më pas?',
    'Knowledge at risk': 'Dija në rrezik',
    'All {n} priority plants': 'Të gjitha {n} bimët prioritare',
    'Plants reported': 'Bimë të raportuara',
    'Plants only this group reports': 'Bimë që i raporton vetëm ky grup',
    'Uses only this group reports': 'Përdorime që i raporton vetëm ky grup',
    'Reported by: {groups}. People prepare it {prep}; of {papers} PubMed candidates, none is tagged with this preparation.': 'Raportuar nga: {groups}. Njerëzit e përgatitin {prep}; nga {papers} kandidatë PubMed, asnjë nuk ka këtë përgatitje.',
    'Reported by: {groups}. People prepare it {prep}; {matching} of {papers} PubMed candidates use this preparation, all in the lab or in animals.': 'Raportuar nga: {groups}. Njerëzit e përgatitin {prep}; {matching} nga {papers} kandidatë PubMed e përdorin këtë përgatitje, të gjithë në laborator ose te kafshët.',
    'Also used for: {cats}': 'Përdoret edhe për: {cats}',
    'Body system': 'Sistemi i trupit',
    'Independent groups': 'Grupe të pavarura',
    'Regions': 'Rajone',
    '{n} independent groups': '{n} grupe të pavarura',
    '{n} regions': '{n} rajone',
    'Respiratory': 'Frymëmarrja',
    'Digestive': 'Tretja',
    'Liver and bile': 'Mëlçia dhe tëmthi',
    'Urinary and kidney': 'Veshkat dhe rrugët urinare',
    'Heart and blood': 'Zemra dhe gjaku',
    'Diabetes and metabolism': 'Diabeti dhe metabolizmi',
    'Skin and wounds': 'Lëkura dhe plagët',
    'Joints and muscles': 'Nyjet dhe muskujt',
    'Nerves and sleep': 'Nervat dhe gjumi',
    'Infections and parasites': 'Infeksionet dhe parazitët',
    'Immunity and allergy': 'Imuniteti dhe alergjitë',
    'Cancer': 'Kanceri',
    "Women's health": 'Shëndeti i gruas',
    'Eyes, ears and mouth': 'Sytë, veshët dhe goja',
    'Fever and inflammation': 'Temperatura dhe inflamacioni',
    # ---------------------------------------------------------------- voice and botanist
    "Hello! I'm the plant librarian. Ask me about any plant: type it, or press the microphone and say its name the way your grandparents do.": 'Përshëndetje! Jam bibliotekari i bimëve. Më pyet për çdo bimë: shkruaje, ose shtyp mikrofonin dhe thuaje emrin siç e thonë gjyshërit.',
    'Animated botanist waving with a leaf': 'Botanist i animuar që përshëndet me një gjethe',
    'Or ask with your voice': 'Ose pyet me zë',
    'Press the microphone, speak in Albanian or English, press again to stop.': 'Shtyp mikrofonin, fol në shqip ose anglisht, shtyp sërish për ta ndalur.',
    'Listening…': 'Po dëgjoj…',
    'I could not hear a question. Try again a little closer to the microphone.': 'Nuk e dëgjova pyetjen. Provo sërish pak më afër mikrofonit.',
}


def lang() -> str:
    return "en" if st.session_state.get("lang") == "English" else "sq"


def t(text: str, **values) -> str:
    out = SQ.get(text, text) if lang() == "sq" else text
    return out.format(**values) if values else out


def summary_sentence(result: dict) -> str:
    """Albanian/English version of pipeline.compare.summary_sentence."""
    if lang() == "en":
        from pipeline.compare import summary_sentence as english
        return english(result)
    prep = ", ".join(t(p.strip()) for p in result["traditional_text"].split(", "))
    base = f"Njerëzit e përgatitin {prep}. "
    v = result["verdict"]
    if v == "reviewed":
        return base + f"{len(result['reviewed'])} artikull(j) u kontrolluan me dorë kundrejt kësaj përgatitjeje."
    if v == "not_comparable":
        return base + "Etiketat me fjalë kyçe nuk tregojnë dot nëse një studim përdori këtë lloj përgatitjeje."
    if v == "none":
        return base + "Nuk u gjet asnjë artikull kandidat në PubMed."
    if v == "different":
        return base + f"Asnjë nga {result['papers']} kandidatët PubMed nuk ka këtë përgatitje."
    return base + (f"{result['matching']} nga {result['papers']} kandidatët PubMed kanë të njëjtin lloj "
                   f"përgatitjeje; {result['matching_human']} prej tyre janë studime te njerëzit.")
