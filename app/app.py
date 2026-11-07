"""EthnoHack: a sourced plant-use profile for traditional knowledge."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz, process

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.compare import compare_species, summary_sentence  # noqa: E402
from pipeline.config import DB_PATH, IUCN_TOKEN  # noqa: E402
from pipeline.db import connect  # noqa: E402
from pipeline.names import normalize  # noqa: E402

st.set_page_config(page_title="Plant librarian · EthnoHack", page_icon="🌿", layout="wide")
st.markdown(
    """
    <style>
      :root { --ethno-ink: #20352a; --ethno-green: #174c35; --ethno-leaf: #26734d; }
      html, body, .stApp, [data-testid="stAppViewContainer"],
      [data-testid="stMain"], .main { background: #f1efe5 !important; }
      [data-testid="stHeader"] { background: transparent; }
      .block-container { max-width: 1220px; padding-top: 1.5rem; padding-bottom: 4rem; }
      [data-testid="stAppViewContainer"] *, [data-testid="stMain"] * { color: var(--ethno-ink); }
      h1, h2, h3 { color: var(--ethno-green) !important; letter-spacing: -0.025em; }
      h1 { font-size: 2.65rem !important; }
      a, a:visited { color: var(--ethno-leaf) !important; }
      .ethno-hero {
        background: linear-gradient(120deg, #123d2b 0%, #236447 70%, #3b7954 100%);
        border: 1px solid #315f46; border-radius: 22px; padding: 28px 34px;
        margin: 4px 0 22px; box-shadow: 0 10px 28px rgba(27, 61, 42, .13);
      }
      .ethno-hero .eyebrow { color: #c5dbc7 !important; font-size: .76rem;
        font-weight: 700; letter-spacing: .14em; text-transform: uppercase; margin: 0 0 8px; }
      .ethno-hero .hero-title { color: #fffdf5 !important; margin: 0;
        font-size: 2.6rem; font-weight: 750; line-height: 1.15; letter-spacing: -0.03em; }
      .ethno-hero .sub { color: #edf4e9 !important; font-size: 1.04rem;
        max-width: 780px; margin: 8px 0 0; }
      [data-testid="stVerticalBlockBorderWrapper"] {
        background: #e4ebdf !important; border: 1px solid #c7d4c4 !important;
        border-radius: 16px !important;
      }
      [data-testid="stMetric"] {
        background: #dfe9db !important; border: 1px solid #bacdb8 !important;
        border-radius: 14px; padding: 14px 18px;
      }
      [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] *,
      [data-testid="stMetricValue"], [data-testid="stMetricValue"] *,
      [data-testid="stMetricDelta"] { color: #20352a !important; }
      [data-testid="stTextInput"] input,
      [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background: #fffdf7 !important; color: #20352a !important;
        border-color: #b8c9b8 !important; border-radius: 10px;
      }
      [data-testid="stSelectbox"] [data-baseweb="select"] * { color: #20352a !important; }
      div[data-testid="stExpander"] {
        background: #e4ebdf !important; border: 1px solid #c7d4c4;
        border-radius: 12px;
      }
      [data-testid="stSidebar"] { background: #e4ebdf; }
    </style>
    """,
    unsafe_allow_html=True,
)

if not DB_PATH.exists():
    st.error("No database yet. Run `make build` first.")
    st.stop()

conn = connect()
q = lambda sql, *a: pd.read_sql_query(sql, conn, params=a)

# The checked demo records are real paper excerpts. Synthetic fixtures stay out of this view.
uses = q("SELECT * FROM uses WHERE species IS NOT NULL AND doc_id != ?", "sample_fixture")
if uses.empty:
    st.warning("The database has no resolved records yet.")
    st.stop()

st.markdown(
    """
    <div class="ethno-hero">
      <p class="eyebrow">EthnoHack · Traditional knowledge</p>
      <div class="hero-title">🌿 Plant librarian</div>
      <p class="sub">Explore plant-use records documented in studies, then see what modern research tested.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("Research prototype · Sources are shown throughout · Not medical advice")

# Search by a local or scientific name, then choose the resolved species.
choices = {normalize(n): sp for n, sp in zip(uses.local_name, uses.species)}
choices.update({normalize(sp): sp for sp in uses.species.unique()})
species_list = sorted(uses.species.unique())
search_col, select_col = st.columns([1.2, 1], gap="medium")
with search_col:
    query = st.text_input(
        "Search a plant name",
        placeholder="Try Mullaga, Lule qeni, or Origanum vulgare",
        help="You can search by the local name printed in the study or by scientific name.",
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
reviewed_path = Path(__file__).resolve().parent.parent / "data" / "seed" / "reviewed_evidence.csv"
reviewed_evidence = pd.read_csv(reviewed_path)
reviewed_evidence = reviewed_evidence[reviewed_evidence.species == species]
sources = q("SELECT * FROM sources")
demo_sources = sources[sources.doc_id != "sample_fixture"]
source_by_id = {row.doc_id: row for _, row in demo_sources.iterrows()}

family = sp_uses.family.dropna()
local_names = ", ".join(sorted(set(sp_uses.local_name.dropna())))
st.header(f"*{species}*")
st.caption(f"{family.iloc[0] if len(family) else 'Family not listed'}  ·  Local name: {local_names}")
metric_cols = st.columns(3)
metric_cols[0].metric("Study use reports", len(sp_uses))
metric_cols[1].metric("Reviewed research papers", len(reviewed_evidence))
metric_cols[2].metric("PubMed candidates · unreviewed", len(evidence))
st.caption(f"GBIF distribution records available: {len(occ)} · These show reported plant occurrences, not traditional-use locations.")

st.divider()
st.subheader("1 · What the study reports")
st.caption("These are reports documented by researchers. They are not proof that a remedy works.")
for _, u in sp_uses.iterrows():
    src = source_by_id.get(u.doc_id)
    with st.container(border=True):
        st.markdown(f"### {u.use}")
        detail_cols = st.columns([1, 1, 1.25])
        detail_cols[0].markdown(f"**Preparation**  \n{(u.preparation or 'Not stated').title()}")
        detail_cols[1].markdown(f"**Plant part**  \n{(u.part_used or 'Not stated').title()}")
        detail_cols[2].markdown(f"**Recorded location**  \n{u.place or u.location or 'Study region only; no village specified'}")
        if src is not None:
            st.markdown(f"Source: [{src.title}]({src.url}) · printed page {u.page}")
        else:
            st.caption(f"Source: {u.doc_id} · printed page {u.page}")
        if u.quote:
            with st.expander("View the excerpt from the paper"):
                st.markdown(f"> {u.quote}")

st.divider()
st.subheader("2 · What modern studies tested")
st.caption("The comparison describes preparation similarity. It does not confirm that the traditional use is effective.")
prep_check = compare_species(
    sp_uses.to_dict("records"), evidence.to_dict("records"), reviewed_evidence.to_dict("records"))
with st.container(border=True):
    st.markdown(f"#### Was the same preparation tested? · {prep_check['label']}")
    st.write(summary_sentence(prep_check))
    if prep_check["verdict"] in {"human", "lab", "different"}:
        check_cols = st.columns(3)
        check_cols[0].metric("PubMed candidates", prep_check["papers"])
        check_cols[1].metric("Same preparation tag", prep_check["matching"])
        check_cols[2].metric("…tagged as human study", prep_check["matching_human"])
    if prep_check["matching_papers"] and prep_check["verdict"] != "reviewed":
        with st.expander("Candidates tagged with the same preparation"):
            for p in prep_check["matching_papers"][:10]:
                st.markdown(f"- [{p['title']}](https://pubmed.ncbi.nlm.nih.gov/{p['pmid']}/) · {p['year']} · "
                            f"{str(p.get('study_type') or 'other').replace('_', ' ')}")
    st.caption("Automatic check from keyword tags on the top PubMed results; read the paper before relying on it. "
               "See the Research gaps page for every plant.")
if reviewed_evidence.empty:
    st.markdown("No modern study has been manually checked against this plant’s reported preparation yet.")
else:
    for _, study in reviewed_evidence.iterrows():
        with st.container(border=True):
            st.markdown(f"#### [{study.title}]({study.url}) · {study.year}")
            st.markdown(f"**Preparation tested:** {study.preparation}")
            st.write(study.summary)
            st.markdown(f"**Preparation comparison:** {study.comparison}")
            st.caption(f"Limit: {study.limitation}")

if evidence.empty:
    st.caption("No additional PubMed candidates are loaded for this plant.")
else:
    with st.expander(f"Other possible PubMed matches ({len(evidence)})"):
        st.caption("These are keyword-matched candidates, not reviewed conclusions. Automated preparation and study-type labels can be wrong.")
        evidence["link"] = "https://pubmed.ncbi.nlm.nih.gov/" + evidence.pmid + "/"
        evidence = evidence.rename(columns={"prep_class": "Keyword preparation tag", "study_type": "Keyword study-type tag"})
        st.dataframe(
            evidence[["year", "title", "Keyword preparation tag", "Keyword study-type tag", "link"]],
            hide_index=True,
            use_container_width=True,
            column_config={"link": st.column_config.LinkColumn("Open PubMed record")},
        )

st.divider()
st.subheader("3 · Safety and conservation")
if flags.empty:
    st.markdown("No item in the project’s **limited safety-rule list** matched this plant. The list is incomplete, so this is not an all-clear or a safety assessment.")
else:
    for _, f in flags.iterrows():
        box = st.error if f.level == "warning" else st.warning
        box(f"**{f.kind.title()} ({f.level}):** {f.note}  \nSource: {f.source}")
if not IUCN_TOKEN and not any(flags.kind == "conservation"):
    st.caption("IUCN conservation status has not been checked; this lookup needs an IUCN token.")

st.divider()
st.subheader("4 · Where the study took place")
st.caption("The paper reports a study region, not a village for each plant record. The marker is approximate.")
import folium
from streamlit_folium import st_folium

use_points = sp_uses.dropna(subset=["lat", "lon"])
if use_points.empty:
    st.markdown("No study-area coordinates are available for these records.")
else:
    center = [float(use_points.lat.mean()), float(use_points.lon.mean())]
    use_map = folium.Map(location=center, zoom_start=8, tiles="OpenStreetMap")
    for _, u in use_points.drop_duplicates(subset=["lat", "lon"]).iterrows():
        location = u.place or u.location or "Sharr Mountains study area"
        folium.Marker(
            [u.lat, u.lon], tooltip=location,
            popup=f"Approximate study-area location: {location}",
            icon=folium.Icon(color="green"),
        ).add_to(use_map)
    st_folium(use_map, height=380, use_container_width=True, key="study-area-map-v2")

with st.expander(f"GBIF records of where this plant grows ({len(occ)} records)"):
    st.caption("Occurrence points come from GBIF. They are not locations where the study recorded traditional use, and individual points have not been checked against the paper.")
    if occ.empty:
        st.markdown("Occurrence data have not been loaded for this plant yet.")
    else:
        occurrence_map = folium.Map(location=[42.4, 20.8], zoom_start=7, tiles="OpenStreetMap")
        for _, o in occ.dropna(subset=["lat", "lon"]).iterrows():
            folium.CircleMarker([o.lat, o.lon], radius=3, color="#2e7d32", fill=True).add_to(occurrence_map)
        st_folium(occurrence_map, height=320, use_container_width=True, key="occurrence-map")

if not compounds.empty:
    with st.expander("Experimental compound screening"):
        share = compounds.water_soluble.mean()
        st.write(f"The compound list comes from Wikidata/LOTUS. RDKit estimates logP for available structures; **{share:.0%}** fall below this project’s rough logP < 1 cutoff. This does not show that a traditional preparation extracts those compounds or has a medical effect.")
        st.dataframe(compounds[["compound", "logp", "water_soluble"]].sort_values("logp"), hide_index=True)

st.divider()
with st.expander("Sources, methods, and current limits"):
    used_doc_ids = set(sp_uses.doc_id.dropna())
    plant_sources = demo_sources[demo_sources.doc_id.isin(used_doc_ids)]
    for _, source in plant_sources.iterrows():
        st.markdown(f"**[{source.title}]({source.url})**  ·  {source.citation}  ·  Licence: {source.licence}")
    st.caption("This version contains 74 ALB-labelled medicinal-use rows from Table 1 of the 2015 Sharr Mountains paper, across 51 plant taxa. Each row is matched to its PDF page. The paper reports 114 medicinal taxa overall; other community rows and its separate food and handicraft tables are not loaded here. These are traditional-use reports, not proof of medical effectiveness.")

with st.sidebar:
    st.header("About this project")
    st.write("A sourced digital librarian for traditional plant-use records. It connects what a study reports with modern research, safety sources, and maps.")
    st.caption(f"{len(uses)} checked records · {uses.species.nunique()} plants")

# Release the SQLite file between Streamlit reruns so the offline build can rebuild it on Windows.
conn.close()
