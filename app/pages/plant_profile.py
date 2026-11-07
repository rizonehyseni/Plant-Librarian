"""Plant profile: a sourced fact sheet for one plant."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz, process

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ for ui.py
from pipeline.compare import compare_species, summary_sentence  # noqa: E402
from pipeline.config import DB_PATH, IUCN_TOKEN, SEED  # noqa: E402
from pipeline.db import connect  # noqa: E402
from pipeline.names import normalize  # noqa: E402
from ui import hero, section  # noqa: E402

VERDICT_BADGE = {  # verdict -> (badge colour, Material icon)
    "reviewed": ("blue", "verified"), "human": ("green", "groups"), "lab": ("orange", "biotech"),
    "different": ("red", "report"), "none": ("red", "search_off"), "not_comparable": ("gray", "help"),
}

if not DB_PATH.exists():
    st.error("No database yet. Run `make build` first.", icon=":material/database:")
    st.stop()

conn = connect()
q = lambda sql, *a: pd.read_sql_query(sql, conn, params=a)

# The checked demo records are real paper excerpts. Synthetic fixtures stay out of this view.
uses = q("SELECT * FROM uses WHERE species IS NOT NULL AND doc_id != ?", "sample_fixture")
if uses.empty:
    st.warning("The database has no resolved records yet.")
    st.stop()

hero(
    "EthnoHack 2026 · Traditional knowledge",
    "Plant librarian",
    "Type a plant name the way people say it. See how it is used and prepared, what modern studies "
    "tested, and whether it carries a risk. Every line links to its source.",
    chips=[("menu_book", f"{len(uses)} study records"), ("eco", f"{uses.species.nunique()} plants"),
           ("link", "Every line sourced"), ("health_and_safety", "No doses, not medical advice")],
)

# Search by a local or scientific name, then choose the resolved species.
choices = {normalize(n): sp for n, sp in zip(uses.local_name, uses.species)}
choices.update({normalize(sp): sp for sp in uses.species.unique()})
species_list = sorted(uses.species.unique())
search_col, select_col = st.columns([1.2, 1], gap="medium")
with search_col:
    query = st.text_input(
        "Search a plant name",
        placeholder="Try Mullaga, Lule qeni, or Origanum vulgare",
        help="Search by the local (Albanian) name printed in the study or by scientific name.",
        icon=":material/search:",
    )
requested_species = st.query_params.get("species")
if requested_species in species_list:
    default = requested_species
elif query:
    hit = process.extractOne(normalize(query), choices.keys(), scorer=fuzz.WRatio)
    default = choices[hit[0]] if hit and hit[1] >= 70 else species_list[0]
else:
    # Open on a plant with source-linked, manually reviewed comparison records.
    default = "Althaea officinalis" if "Althaea officinalis" in species_list else species_list[0]
with select_col:
    species = st.selectbox("Plant profile", species_list, index=species_list.index(default))

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
local_names = ", ".join(sorted(set(sp_uses.local_name.dropna()))) or "not recorded"
st.write("")
st.markdown(f"## *{species}*")
color, icon = VERDICT_BADGE[prep_check["verdict"]]
st.markdown(
    f":gray-badge[:material/park: {family.iloc[0] if len(family) else 'Family not listed'}] "
    f":green-badge[:material/translate: {local_names}] "
    f":{color}-badge[:material/{icon}: {prep_check['label']}]"
)
metric_cols = st.columns(4)
metric_cols[0].metric("Study use reports", len(sp_uses), border=True)
metric_cols[1].metric("Reviewed papers", len(reviewed_evidence), border=True)
metric_cols[2].metric("PubMed candidates", len(evidence), border=True, help="Unreviewed keyword matches")
metric_cols[3].metric("Safety flags", len(flags), border=True, help="From the project's limited rule list")

# ---------------------------------------------------------------- 1 traditional use
st.write("")
section("menu_book", "What the study reports",
        "Reports documented by researchers. They are not proof that a remedy works.")
for _, u in sp_uses.iterrows():
    src = source_by_id.get(u.doc_id)
    with st.container(border=True):
        st.markdown(f"#### {u.use}")
        place = u.place or u.location or "Study region only"
        st.markdown(
            f":green-badge[:material/water_drop: {(u.preparation or 'Preparation not stated').capitalize()}] "
            f":orange-badge[:material/spa: {(u.part_used or 'Part not stated').capitalize()}] "
            f":gray-badge[:material/location_on: {place}]"
        )
        if src is not None:
            st.caption(f":material/description: [{src.title}]({src.url}) · printed page {u.page}")
        else:
            st.caption(f":material/description: {u.doc_id} · printed page {u.page}")
        if u.quote:
            with st.expander("Excerpt from the paper", icon=":material/format_quote:"):
                st.markdown(f"> {u.quote}")

# ---------------------------------------------------------------- 2 modern studies
st.write("")
section("science", "What modern studies tested",
        "The comparison describes preparation similarity. It does not confirm that the traditional use is effective.")
with st.container(border=True):
    st.markdown(f"#### Was the same preparation tested?")
    st.markdown(f":{color}-badge[:material/{icon}: {prep_check['label']}]")
    st.write(summary_sentence(prep_check))
    if prep_check["verdict"] in {"human", "lab", "different"}:
        check_cols = st.columns(3)
        check_cols[0].metric("PubMed candidates", prep_check["papers"])
        check_cols[1].metric("Same preparation tag", prep_check["matching"])
        check_cols[2].metric("…tagged as human study", prep_check["matching_human"])
    if prep_check["matching_papers"] and prep_check["verdict"] != "reviewed":
        with st.expander("Candidates tagged with the same preparation", icon=":material/article:"):
            for p in prep_check["matching_papers"][:10]:
                st.markdown(f"- [{p['title']}](https://pubmed.ncbi.nlm.nih.gov/{p['pmid']}/) · {p['year']} · "
                            f"{str(p.get('study_type') or 'other').replace('_', ' ')}")
    st.caption("Automatic check from keyword tags on the top PubMed results; read the paper before relying on it. "
               "The Research gaps page shows this for every plant.")

if reviewed_evidence.empty:
    st.info("No modern study has been manually checked against this plant's reported preparation yet.",
            icon=":material/pending:")
else:
    for _, study in reviewed_evidence.iterrows():
        with st.container(border=True):
            st.markdown(f"#### [{study.title}]({study.url})")
            st.markdown(f":blue-badge[:material/verified: Reviewed] :gray-badge[{study.year}] "
                        f":green-badge[:material/water_drop: {study.preparation}]")
            st.write(study.summary)
            st.markdown(f"**Preparation comparison:** {study.comparison}")
            st.caption(f":material/info: {study.limitation}")

if evidence.empty:
    st.caption("No additional PubMed candidates are loaded for this plant.")
else:
    with st.expander(f"All PubMed candidates ({len(evidence)})", icon=":material/library_books:"):
        st.caption("Keyword-matched candidates, not reviewed conclusions. Automated preparation and study-type labels can be wrong.")
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
    st.info("No item in the project's **limited safety-rule list** matched this plant. The list is incomplete, "
            "so this is not an all-clear or a safety assessment.", icon=":material/info:")
else:
    for _, f in flags.iterrows():
        box = st.error if f.level == "warning" else st.warning
        box(f"**{f.kind.title()} ({f.level}):** {f.note}  \nSource: {f.source}", icon=":material/warning:")
if not IUCN_TOKEN and not any(flags.kind == "conservation"):
    st.caption(":material/pending: IUCN conservation status has not been checked; this lookup needs an IUCN token.")

# ---------------------------------------------------------------- 4 maps
st.write("")
section("map", "Where the study took place",
        "The paper reports a study region, not a village for each plant record. The marker is approximate.")
import folium  # noqa: E402
from streamlit_folium import st_folium  # noqa: E402

TILES = "OpenStreetMap"
use_points = sp_uses.dropna(subset=["lat", "lon"])
if use_points.empty:
    st.markdown("No study-area coordinates are available for these records.")
else:
    center = [float(use_points.lat.mean()), float(use_points.lon.mean())]
    use_map = folium.Map(location=center, zoom_start=8, tiles=TILES)
    for _, u in use_points.drop_duplicates(subset=["lat", "lon"]).iterrows():
        location = u.place or u.location or "Sharr Mountains study area"
        folium.Marker(
            [u.lat, u.lon], tooltip=location,
            popup=f"Approximate study-area location: {location}",
            icon=folium.Icon(color="darkgreen", icon="leaf", prefix="fa"),
        ).add_to(use_map)
    st_folium(use_map, height=380, use_container_width=True, key="study-area-map-v2")

with st.expander(f"Where this plant grows · GBIF ({len(occ)} records)", icon=":material/public:"):
    st.caption("Occurrence points come from GBIF. They are not locations where the study recorded traditional use, and individual points have not been checked against the paper.")
    if occ.empty:
        st.markdown("Occurrence data have not been loaded for this plant yet.")
    else:
        occurrence_map = folium.Map(location=[42.4, 20.8], zoom_start=7, tiles=TILES)
        for _, o in occ.dropna(subset=["lat", "lon"]).iterrows():
            folium.CircleMarker([o.lat, o.lon], radius=3, color="#2f6b4f", fill=True, fill_opacity=.7).add_to(occurrence_map)
        st_folium(occurrence_map, height=320, use_container_width=True, key="occurrence-map")

if not compounds.empty:
    with st.expander("Experimental compound screening", icon=":material/experiment:"):
        share = compounds.water_soluble.mean()
        st.write(f"The compound list comes from Wikidata/LOTUS. RDKit estimates logP for available structures; **{share:.0%}** fall below this project's rough logP < 1 cutoff. This does not show that a traditional preparation extracts those compounds or has a medical effect.")
        st.dataframe(compounds[["compound", "logp", "water_soluble"]].sort_values("logp"), hide_index=True, width="stretch")

# ---------------------------------------------------------------- sources
st.write("")
with st.expander("Sources, methods, and current limits", icon=":material/menu_book:"):
    used_doc_ids = set(sp_uses.doc_id.dropna())
    plant_sources = demo_sources[demo_sources.doc_id.isin(used_doc_ids)]
    for _, source in plant_sources.iterrows():
        st.markdown(f"**[{source.title}]({source.url})**  ·  {source.citation}  ·  Licence: {source.licence}")
    st.caption("This version contains 74 ALB-labelled medicinal-use rows from Table 1 of the 2015 Sharr Mountains paper, across 51 plant taxa. Each row is matched to its PDF page. The paper reports 114 medicinal taxa overall; other community rows and its separate food and handicraft tables are not loaded here. These are traditional-use reports, not proof of medical effectiveness.")

# Release the SQLite file between Streamlit reruns so the offline build can rebuild it on Windows.
conn.close()
