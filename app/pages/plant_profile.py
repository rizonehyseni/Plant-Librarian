"""Plant profile: a sourced fact sheet for one plant."""
import hashlib
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz, process

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ for ui.py
from pipeline import photo  # noqa: E402
from pipeline.compare import compare_species  # noqa: E402
from pipeline.config import DB_PATH, IUCN_TOKEN, SEED  # noqa: E402
from pipeline.db import connect  # noqa: E402
from pipeline.names import normalize  # noqa: E402
from factsheet import fact_sheet_html, profile_url, qr_svg  # noqa: E402
from i18n import lang, summary_sentence, t  # noqa: E402
from ui import hero, section  # noqa: E402

VERDICT_BADGE = {  # verdict -> (badge colour, Material icon)
    "reviewed": ("blue", "verified"), "human": ("green", "groups"), "lab": ("orange", "biotech"),
    "different": ("red", "report"), "none": ("red", "search_off"), "not_comparable": ("gray", "help"),
}

if not DB_PATH.exists():
    st.error(t("No database yet. Run `make build` first."), icon=":material/database:")
    st.stop()

conn = connect()
q = lambda sql, *a: pd.read_sql_query(sql, conn, params=a)

# The checked demo records are real paper excerpts. Synthetic fixtures stay out of this view.
uses = q("SELECT * FROM uses WHERE species IS NOT NULL AND doc_id != ?", "sample_fixture")
if uses.empty:
    st.warning(t("The database has no resolved records yet."))
    st.stop()

hero(
    "EthnoHack 2026 · Traditional knowledge",
    "Plant librarian",
    "Type a plant name the way people say it. See how it is used and prepared, what modern studies "
    "tested, and whether it carries a risk. Every line links to its source.",
    chips=[("menu_book", t("{n} study records", n=len(uses))), ("eco", t("{n} plants", n=uses.species.nunique())),
           ("link", t("Every line sourced")), ("health_and_safety", t("No doses, not medical advice"))],
)

# Search by a local or scientific name, then choose the resolved species.
choices = {
    normalize(alias.strip()): species_name
    for local, species_name in zip(uses.local_name, uses.species)
    for alias in str(local).split("/")
}
choices.update({normalize(sp): sp for sp in uses.species.unique()})
species_list = sorted(uses.species.unique())
search_col, select_col = st.columns([1.2, 1], gap="medium")
with search_col:
    query = st.text_input(
        t("Search a plant name"),
        placeholder=t("Try Mullaga, Lule qeni, or Origanum vulgare"),
        help=t("Search by the local (Albanian) name printed in the study or by scientific name."),
        icon=":material/search:",
    )
# Identify from a photo (Pl@ntNet). Behind a toggle so the browser asks for the camera only when wanted.
if st.toggle(t("Identify a plant from a photo"), key="photo_on", help=t("Pl@ntNet suggests the species from a photo of a leaf, flower, fruit or bark.")):
    with st.container(border=True):
        if not photo.PLANTNET_API_KEY:
            st.info(t("Add a free `PLANTNET_API_KEY` to `.env` (account at https://my.plantnet.org/), then restart the app."),
                    icon=":material/key:")
        else:
            src_col, organ_col = st.columns([1, 1.4], vertical_alignment="bottom")
            source = src_col.segmented_control(t("Photo"), ["camera", "upload"], default="upload", required=True,
                                               format_func=lambda s: t("Camera") if s == "camera" else t("Upload"),
                                               key="photo_source")
            organ = organ_col.pills(t("What is in the photo?"), list(photo.ORGANS), default="auto", key="photo_organ",
                                    format_func=lambda o: t({"auto": "Not sure", "leaf": "Leaf", "flower": "Flower",
                                                             "fruit": "Fruit", "bark": "Bark"}[o]))
            image = (st.camera_input(t("Take a photo"), key="photo_cam") if source == "camera"
                     else st.file_uploader(t("Upload a photo"), type=["jpg", "jpeg", "png"], key="photo_file"))
            if image is not None:
                digest = hashlib.sha1(image.getvalue() + str(organ).encode()).hexdigest()
                if st.session_state.get("photo_digest") != digest:  # each photo is sent once
                    with st.spinner(t("Pl@ntNet is looking at the photo…")):
                        try:
                            found = photo.identify(image.getvalue(), organ=organ or "auto", lang=lang())
                            st.session_state.photo_results = photo.match_library(found, species_list)
                            st.session_state.photo_digest = digest
                        except Exception as exc:  # noqa: BLE001
                            st.session_state.photo_results = None
                            st.error(str(exc), icon=":material/error:")
                results = st.session_state.get("photo_results")
                if results == []:
                    st.warning(t("Pl@ntNet did not recognise a plant. Try a sharper photo of one leaf or flower."))
                for n, r in enumerate((results or [])[:3]):
                    with st.container(border=True):
                        name_col, pick_col = st.columns([4, 1.3], vertical_alignment="center")
                        common = f" · {', '.join(r['common_names'][:2])}" if r["common_names"] else ""
                        name_col.markdown(f"**{n + 1}. *{r['species']}***{common}")
                        name_col.progress(min(r["score"], 1.0), text=t("Pl@ntNet confidence: {p}%", p=round(r["score"] * 100)))
                        if r["match"] == "species":
                            name_col.markdown(":green-badge[:material/check_circle: " + t("In the library") + "]")
                        elif r["match"] == "genus":
                            name_col.markdown(":orange-badge[:material/account_tree: " + t("Same genus in the library: {s}",
                                              s=", ".join(r["library_species"])) + "]")
                        else:
                            name_col.markdown(":gray-badge[" + t("Not in the library yet") + "]")
                        if r["library_species"] and pick_col.button(t("Open profile"), key=f"photo-pick-{n}",
                                                                     icon=":material/arrow_forward:", width="stretch"):
                            st.session_state.photo_pick = r["library_species"][0]
                st.caption(":material/info: " + t("A suggestion from Pl@ntNet with its confidence, not a confirmed "
                                                  "identification. Never collect or use a plant on the basis of a photo."))

requested_species = st.query_params.get("species")
if st.session_state.get("photo_pick") in species_list:
    default = st.session_state.pop("photo_pick")
elif requested_species in species_list:
    default = requested_species
elif query:
    hit = process.extractOne(normalize(query), choices.keys(), scorer=fuzz.WRatio)
    default = choices[hit[0]] if hit and hit[1] >= 70 else species_list[0]
else:
    # Open on a plant with source-linked, manually reviewed comparison records.
    default = "Althaea officinalis" if "Althaea officinalis" in species_list else species_list[0]
with select_col:
    species = st.selectbox(t("Plant profile"), species_list, index=species_list.index(default))

sp_uses = uses[uses.species == species]
evidence = q("SELECT * FROM evidence WHERE species = ?", species)
flags = q("SELECT * FROM flags WHERE species = ?", species)
compounds = q("SELECT * FROM compounds WHERE species = ?", species)
occ = q("SELECT * FROM occurrences WHERE species = ?", species)
reviewed_evidence = pd.read_csv(SEED / "reviewed_evidence.csv")
reviewed_evidence = reviewed_evidence[reviewed_evidence.species == species]
sources = q("SELECT * FROM sources")
demo_sources = sources[sources.doc_id != "sample_fixture"]
source_by_id = {row.doc_id: row for _, row in demo_sources.iterrows()}
prep_check = compare_species(
    sp_uses.to_dict("records"), evidence.to_dict("records"), reviewed_evidence.to_dict("records"))

# ---------------------------------------------------------------- plant header
family = sp_uses.family.dropna()
local_names = ", ".join(sorted(set(sp_uses.local_name.dropna()))) or t("not recorded")
st.write("")
st.markdown(f"## *{species}*")
color, icon = VERDICT_BADGE[prep_check["verdict"]]
st.markdown(
    f":gray-badge[:material/park: {family.iloc[0] if len(family) else t('Family not listed')}] "
    f":green-badge[:material/translate: {local_names}] "
    f":{color}-badge[:material/{icon}: {t(prep_check['label'])}]"
)
metric_cols = st.columns(4)
metric_cols[0].metric(t("Study use reports"), len(sp_uses), border=True)
metric_cols[1].metric(t("Reviewed papers"), len(reviewed_evidence), border=True)
metric_cols[2].metric(t("PubMed candidates"), len(evidence), border=True, help=t("Unreviewed keyword matches"))
metric_cols[3].metric(t("Safety flags"), len(flags), border=True, help=t("From the project's limited rule list"))
with st.container(horizontal=True, vertical_alignment="center"):
    st.download_button(
        t("Download fact sheet"), icon=":material/print:", file_name=f"{species.replace(' ', '_')}_fact_sheet.html",
        mime="text/html", help=t("A printable page with every use, source, study and flag. Open it and print to PDF."),
        data=fact_sheet_html(species, family.iloc[0] if len(family) else None, local_names, sp_uses, prep_check,
                             reviewed_evidence, evidence, flags, demo_sources).encode("utf-8"))
    with st.popover(t("QR code"), icon=":material/qr_code_2:"):
        st.html(f'<div style="width:180px;background:#fff;padding:8px;border-radius:8px">'
                f'{qr_svg(profile_url(species))}</div>')
        st.caption(t("Scan to open this plant's profile.") + f"  \n`{profile_url(species)}`")

# ---------------------------------------------------------------- 1 traditional use
st.write("")
section("menu_book", "What the study reports",
        "Reports documented by researchers. They are not proof that a remedy works.")
for _, u in sp_uses.iterrows():
    src = source_by_id.get(u.doc_id)
    with st.container(border=True):
        st.markdown(f"#### {u.use}")
        place = u.place or u.location or t("Study region only")
        st.markdown(
            f":green-badge[:material/water_drop: {(u.preparation or t('Preparation not stated')).capitalize()}] "
            f":orange-badge[:material/spa: {(u.part_used or t('Part not stated')).capitalize()}] "
            f"{f':blue-badge[:material/groups: {t(u.community)}] ' if u.community else ''}"
            f":gray-badge[:material/location_on: {place}]"
        )
        page_label = (t("printed page {page}", page=int(u.page)) if pd.notna(u.page)
                      else t("shared with consent, reviewed"))
        if src is not None and not src.url:
            st.caption(f":material/volunteer_activism: {t(src.title)} · {page_label}")
        elif src is not None:
            st.caption(f":material/description: [{src.title}]({src.url}) · " + page_label)
        else:
            st.caption(f":material/description: {u.doc_id} · " + page_label)
        if u.quote:
            with st.expander(t("Excerpt from the paper"), icon=":material/format_quote:"):
                st.markdown(f"> {u.quote}")

# ---------------------------------------------------------------- 2 modern studies
st.write("")
section("science", "What modern studies tested",
        "The comparison describes preparation similarity. It does not confirm that the traditional use is effective.")
with st.container(border=True):
    st.markdown("#### " + t("Was the same preparation tested?"))
    st.markdown(f":{color}-badge[:material/{icon}: {t(prep_check['label'])}]")
    st.write(summary_sentence(prep_check))
    if prep_check["verdict"] in {"human", "lab", "different"}:
        check_cols = st.columns(3)
        check_cols[0].metric(t("PubMed candidates"), prep_check["papers"])
        check_cols[1].metric(t("Same preparation tag"), prep_check["matching"])
        check_cols[2].metric(t("…tagged as human study"), prep_check["matching_human"])
    if prep_check["matching_papers"] and prep_check["verdict"] != "reviewed":
        with st.expander(t("Candidates tagged with the same preparation"), icon=":material/article:"):
            for p in prep_check["matching_papers"][:10]:
                st.markdown(f"- [{p['title']}](https://pubmed.ncbi.nlm.nih.gov/{p['pmid']}/) · {p['year']} · "
                            f"{str(p.get('study_type') or 'other').replace('_', ' ')}")
    st.caption(t("Automatic check from keyword tags on the top PubMed results; read the paper before relying on it. "
                 "The Research gaps page shows this for every plant."))

if reviewed_evidence.empty:
    st.info(t("No modern study has been manually checked against this plant's reported preparation yet."),
            icon=":material/pending:")
else:
    for _, study in reviewed_evidence.iterrows():
        with st.container(border=True):
            st.markdown(f"#### [{study.title}]({study.url})")
            st.markdown(f":blue-badge[:material/verified: {t('Reviewed')}] :gray-badge[{study.year}] "
                        f":green-badge[:material/water_drop: {study.preparation}]")
            st.write(study.summary)
            st.markdown(f"**{t('Preparation comparison:')}** {study.comparison}")
            st.caption(f":material/info: {study.limitation}")

if evidence.empty:
    st.caption(t("No additional PubMed candidates are loaded for this plant."))
else:
    with st.expander(t("All PubMed candidates ({n})", n=len(evidence)), icon=":material/library_books:"):
        st.caption(t("Keyword-matched candidates, not reviewed conclusions. Automated preparation and study-type labels can be wrong."))
        evidence["link"] = "https://pubmed.ncbi.nlm.nih.gov/" + evidence.pmid + "/"
        evidence = evidence.rename(columns={"prep_class": "Preparation tag", "study_type": "Study-type tag"})
        st.dataframe(
            evidence[["year", "title", "Preparation tag", "Study-type tag", "link"]],
            hide_index=True, width="stretch",
            column_config={"link": st.column_config.LinkColumn("PubMed", display_text="Open")},
        )

# ---------------------------------------------------------------- 3 safety
st.write("")
section("health_and_safety", "Safety and conservation")
if flags.empty:
    st.info(t("No item in the project's **limited safety-rule list** matched this plant. The list is incomplete, "
              "so this is not an all-clear or a safety assessment."), icon=":material/info:")
else:
    for _, f in flags.iterrows():
        box = st.error if f.level == "warning" else st.warning
        box(f"**{f.kind.title()} ({f.level}):** {f.note}  \nSource: {f.source}", icon=":material/warning:")
if not IUCN_TOKEN and not any(flags.kind == "conservation"):
    st.caption(":material/pending: IUCN conservation status has not been checked; this lookup needs an IUCN token.")

# ---------------------------------------------------------------- 4 maps
st.write("")
section("map", "Where the uses were recorded",
        "Green pin: the record names a village or town. Grey pin: the study names only its region, so the marker "
        "is approximate.")
import folium  # noqa: E402
from streamlit_folium import st_folium  # noqa: E402

TILES = "OpenStreetMap"
use_points = sp_uses.dropna(subset=["lat", "lon"])
if use_points.empty:
    st.markdown(t("No study-area coordinates are available for these records."))
else:
    center = [float(use_points.lat.mean()), float(use_points.lon.mean())]
    use_map = folium.Map(location=center, zoom_start=8, tiles=TILES)
    for _, u in use_points.drop_duplicates(subset=["lat", "lon"]).iterrows():
        location = u.place or u.location or t("Study area")
        exact = u.geo_precision == "record"
        folium.Marker(
            [u.lat, u.lon], tooltip=location,
            popup=f"{t('Village or town named in the record') if exact else t('Approximate study-area location')}: {location}",
            icon=folium.Icon(color="darkgreen" if exact else "gray", icon="leaf", prefix="fa"),
        ).add_to(use_map)
    st_folium(use_map, height=380, use_container_width=True, key="study-area-map-v2")

with st.expander(t("Where this plant grows · GBIF ({n} records)", n=len(occ)), icon=":material/public:"):
    st.caption(t("Occurrence points come from GBIF. They are not locations where the study recorded traditional use, and "
                 "individual points have not been checked against the paper."))
    if occ.empty:
        st.markdown(t("Occurrence data have not been loaded for this plant yet."))
    else:
        occurrence_map = folium.Map(location=[42.4, 20.8], zoom_start=7, tiles=TILES)
        for _, o in occ.dropna(subset=["lat", "lon"]).iterrows():
            folium.CircleMarker([o.lat, o.lon], radius=3, color="#2f6b4f", fill=True, fill_opacity=.7).add_to(occurrence_map)
        st_folium(occurrence_map, height=320, use_container_width=True, key="occurrence-map")

if not compounds.empty:
    with st.expander(t("Experimental compound screening"), icon=":material/experiment:"):
        share = compounds.water_soluble.mean()
        st.write(f"The compound list comes from Wikidata/LOTUS. RDKit estimates logP for available structures; **{share:.0%}** fall below this project's rough logP < 1 cutoff. This does not show that a traditional preparation extracts those compounds or has a medical effect.")
        st.dataframe(compounds[["compound", "logp", "water_soluble"]].sort_values("logp"), hide_index=True, width="stretch")

# ---------------------------------------------------------------- sources
st.write("")
with st.expander(t("Sources, methods, and current limits"), icon=":material/menu_book:"):
    used_doc_ids = set(sp_uses.doc_id.dropna())
    plant_sources = demo_sources[demo_sources.doc_id.isin(used_doc_ids)]
    for _, source in plant_sources.iterrows():
        st.markdown(f"**[{source.title}]({source.url})**  ·  {source.citation}  ·  Licence: {source.licence}")
    st.caption(f"The library holds {len(uses)} medicinal-use reports from {uses.doc_id.nunique()} "
               f"stud{'y' if uses.doc_id.nunique() == 1 else 'ies'}. Each record keeps its study page and quote; "
               "Sharr Mountains records come from Table 1 of the 2015 paper and are labelled by community. Food and "
               "handicraft tables are not loaded. These are traditional-use reports, not proof of medical effectiveness.")

# Release the SQLite file between Streamlit reruns so the offline build can rebuild it on Windows.
conn.close()
