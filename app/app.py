"""EthnoHack demo: type a plant name the way you say it, get a sourced fact sheet."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz, process

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.config import DB_PATH, IUCN_TOKEN  # noqa: E402
from pipeline.db import connect  # noqa: E402
from pipeline.names import normalize  # noqa: E402

st.set_page_config(page_title="Bimët e Kosovës - EthnoHack", page_icon="🌿", layout="wide")

if not DB_PATH.exists():
    st.error("No database yet. Run `make build` first.")
    st.stop()

conn = connect()
q = lambda sql, *a: pd.read_sql_query(sql, conn, params=a)

st.title("🌿 Plant librarian")
st.caption("Traditional plant knowledge from Kosovo and Albanian-speaking regions, with sources. "
           "Research prototype - not medical advice, and no doses are given.")

# Synthetic fixtures keep the pipeline testable, but should not appear as research data
# in the hackathon demo.
uses = q("SELECT * FROM uses WHERE species IS NOT NULL AND doc_id != ?", "sample_fixture")
if uses.empty:
    st.warning("The database has no resolved records yet.")
    st.stop()

# Search: match what the user types against local names and scientific names.
choices = {normalize(n): sp for n, sp in zip(uses.local_name, uses.species)}
choices.update({normalize(sp): sp for sp in uses.species.unique()})
query = st.text_input("Shkruaj emrin e bimës / Type a plant name", placeholder="p.sh. çaj mali, kamomil, lule basani")
species_list = sorted(uses.species.unique())
if query:
    hit = process.extractOne(normalize(query), choices.keys(), scorer=fuzz.WRatio)
    default = choices[hit[0]] if hit and hit[1] >= 70 else species_list[0]
else:
    default = species_list[0]
species = st.selectbox("Species", species_list, index=species_list.index(default))

sp_uses = uses[uses.species == species]
evidence = q("SELECT * FROM evidence WHERE species = ?", species)
flags = q("SELECT * FROM flags WHERE species = ?", species)
compounds = q("SELECT * FROM compounds WHERE species = ?", species)
occ = q("SELECT * FROM occurrences WHERE species = ?", species)
sources = q("SELECT * FROM sources")
demo_sources = sources[sources.doc_id != "sample_fixture"]
source_by_id = {row.doc_id: row for _, row in demo_sources.iterrows()}

family = sp_uses.family.dropna()
local_names = ", ".join(sorted(set(sp_uses.local_name.dropna())))
st.header(f"*{species}*")
st.caption(f"{family.iloc[0] if len(family) else 'Family not listed'} · Local names: {local_names}")

st.divider()
main_col, map_col = st.columns([1.25, 1], gap="large")

with main_col:
    st.subheader("Traditional use in the study")
    st.caption("These are reports documented by researchers, not proof that a remedy works.")
    for _, u in sp_uses.iterrows():
        src = source_by_id.get(u.doc_id)
        with st.container(border=True):
            st.markdown(f"### {u.use}")
            st.write(
                f"The study records an **{(u.preparation or 'unspecified preparation').lower()}** "
                f"made from the **{(u.part_used or 'part not stated').lower()}** of this plant."
            )
            if u.place or u.location:
                st.caption(f"Recorded location: {u.place or u.location}")
            else:
                st.caption("Recorded in the study area; the paper does not tie this record to a specific village.")
            if src is not None:
                st.markdown(f"Source: [{src.title}]({src.url}) · printed p. {u.page}")
            else:
                st.caption(f"Source: {u.doc_id} · printed p. {u.page}")
            if u.quote:
                with st.expander("Check the paper excerpt"):
                    st.markdown(f"> {u.quote}")

with map_col:
    st.subheader("Where the study took place")
    st.caption("The paper gives a study region, not a village for each plant record. This pin marks the region approximately.")
    import folium
    from streamlit_folium import st_folium

    use_points = sp_uses.dropna(subset=["lat", "lon"])
    if use_points.empty:
        st.info("No study-area coordinates are available for these records.")
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
        st_folium(use_map, height=360, use_container_width=True, key="traditional-use-map")
    with st.expander("GBIF records of this plant growing"):
        st.caption("These are database occurrence records, not locations where the study recorded traditional use. Individual points have not been checked against the source dataset.")
        if occ.empty:
            st.info("Occurrence data have not been loaded for this plant yet.")
        else:
            occurrence_map = folium.Map(location=[42.4, 20.8], zoom_start=7, tiles="OpenStreetMap")
            for _, o in occ.dropna(subset=["lat", "lon"]).iterrows():
                folium.CircleMarker([o.lat, o.lon], radius=3, color="#2e7d32", fill=True).add_to(occurrence_map)
            st_folium(occurrence_map, height=320, use_container_width=True, key="occurrence-map")

st.divider()
evidence_col, safety_col = st.columns(2, gap="large")
with evidence_col:
    st.subheader("Modern research checked against the traditional preparation")
    reviewed_path = Path(__file__).resolve().parent.parent / "data" / "seed" / "reviewed_evidence.csv"
    reviewed_evidence = pd.read_csv(reviewed_path)
    reviewed_evidence = reviewed_evidence[reviewed_evidence.species == species]
    if reviewed_evidence.empty:
        st.info("No modern study has been manually checked against this plant’s reported preparation yet.")
    else:
        for _, study in reviewed_evidence.iterrows():
            with st.container(border=True):
                st.markdown(f"**[{study.title}](https://pubmed.ncbi.nlm.nih.gov/{study.pmid}/)** ({study.year})")
                st.write(study.summary)
                st.caption(f"Limit: {study.limitation}")

    st.subheader("Other possible PubMed matches")
    if evidence.empty:
        st.info("Not loaded yet. This means we have no results in this demo—not that no research exists.")
    else:
        st.info("These PubMed search results are candidate matches, not a reviewed evidence summary. Preparation and study-type labels are inferred from title/abstract keywords and can be wrong.")
        with st.expander(f"Review {len(evidence)} candidate PubMed records"):
            evidence["link"] = "https://pubmed.ncbi.nlm.nih.gov/" + evidence.pmid + "/"
            evidence = evidence.rename(columns={"prep_class": "Keyword preparation tag", "study_type": "Keyword study-type tag"})
            st.dataframe(evidence[["year", "title", "Keyword preparation tag", "Keyword study-type tag", "link"]], hide_index=True,
                         use_container_width=True, column_config={"link": st.column_config.LinkColumn("Open PubMed record")})
with safety_col:
    st.subheader("Safety and conservation")
    if flags.empty:
        st.info("No safety warning matched the project’s current rules. This is not a safety guarantee.")
    else:
        for _, f in flags.iterrows():
            box = st.error if f.level == "warning" else st.warning
            box(f"**{f.kind.title()} ({f.level}):** {f.note}  \nSource: {f.source}")
    if not IUCN_TOKEN and not any(flags.kind == "conservation"):
        st.caption("IUCN conservation status has not been checked; the project needs an IUCN token for that lookup.")

if not compounds.empty:
    with st.expander("Explore compound screening (experimental)"):
        share = compounds.water_soluble.mean()
        st.write(f"The compound list comes from Wikidata/LOTUS. RDKit estimates logP for available structures; **{share:.0%}** fall below this project’s rough logP < 1 cutoff. This does not show that a traditional preparation extracts those compounds or has a medical effect.")
        st.dataframe(compounds[["compound", "logp", "water_soluble"]].sort_values("logp"), hide_index=True)

st.divider()
st.subheader("Source for these records")
used_doc_ids = set(sp_uses.doc_id.dropna())
plant_sources = demo_sources[demo_sources.doc_id.isin(used_doc_ids)]
for _, source in plant_sources.iterrows():
    st.markdown(f"**[{source.title}]({source.url})**  ·  {source.citation}  ·  Licence: {source.licence}")
st.caption("This demo contains three manually checked records from a cross-cultural Sharr Mountains study. The table labels the local names shown here as Albanian (ALB); use reports may span study populations. Automated extraction has not been run. Traditional reports do not establish medical effectiveness.")

with st.sidebar:
    st.header("About this demo")
    st.write("Search a local or scientific plant name to see a sourced study record.")
    st.caption(f"{len(uses)} checked records · {uses.species.nunique()} plants")
