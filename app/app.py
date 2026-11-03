"""EthnoHack demo: type a plant name the way you say it, get a sourced fact sheet."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz, process

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.config import DB_PATH  # noqa: E402
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

uses = q("SELECT * FROM uses WHERE species IS NOT NULL")
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

left, right = st.columns([3, 2])
with left:
    st.header(f"*{species}*")
    fam = sp_uses.family.dropna()
    st.write(f"**Family:** {fam.iloc[0] if len(fam) else 'unknown'}  ·  "
             f"**Local names:** {', '.join(sorted(set(sp_uses.local_name)))}")

    for _, f in flags.iterrows():
        box = st.error if f.level == "warning" else st.warning
        box(f"**{f.kind.title()} ({f.level}):** {f.note}  \nSource: {f.source}")

    st.subheader("How people use it")
    st.dataframe(sp_uses[["use", "part_used", "preparation", "administration", "location", "doc_id", "page"]],
                 hide_index=True, use_container_width=True)
    with st.expander("Quotes from the sources"):
        for _, u in sp_uses.iterrows():
            st.markdown(f"> {u.quote}  \n— `{u.doc_id}`, p. {u.page} · name match: {u.match_method}")

    st.subheader("What science tested")
    if evidence.empty:
        st.info("No PubMed studies found (or evidence step not run yet).")
    else:
        trad = set(sp_uses.prep_class)
        counts = evidence.prep_class.value_counts()
        aqueous = int(counts.get("aqueous", 0))
        if "aqueous" in trad:
            msg = (f"People prepare it with water (tea/decoction). Of {len(evidence)} studies found, "
                   f"**{aqueous}** tested a water-based preparation.")
            (st.success if aqueous else st.warning)(msg)
        c1, c2 = st.columns(2)
        c1.bar_chart(counts, horizontal=True)
        c2.bar_chart(evidence.study_type.value_counts(), horizontal=True)
        evidence["link"] = "https://pubmed.ncbi.nlm.nih.gov/" + evidence.pmid + "/"
        st.dataframe(evidence[["year", "title", "prep_class", "study_type", "link"]], hide_index=True,
                     use_container_width=True, column_config={"link": st.column_config.LinkColumn()})

    if not compounds.empty:
        st.subheader("Does the tea even extract it?")
        share = compounds.water_soluble.mean()
        st.write(f"{len(compounds)} known compounds (Wikidata/LOTUS). **{share:.0%}** have logP < 1, "
                 "a rough sign they dissolve in hot water. Screening estimate, not a measurement.")
        st.dataframe(compounds[["compound", "logp", "water_soluble"]].sort_values("logp"), hide_index=True)

with right:
    st.subheader("Where it grows (GBIF)")
    if occ.empty:
        st.info("No occurrence records cached.")
    else:
        import folium
        from streamlit_folium import st_folium

        m = folium.Map(location=[42.4, 20.8], zoom_start=7, tiles="CartoDB positron")
        for _, o in occ.iterrows():
            folium.CircleMarker([o.lat, o.lon], radius=3, color="#2e7d32", fill=True).add_to(m)
        st_folium(m, height=450, use_container_width=True)

with st.sidebar:
    st.header("Sources")
    for _, s in sources.iterrows():
        st.markdown(f"**{s.doc_id}**: {s.title}  \n{s.citation}  \nLicence: {s.licence}")
    st.metric("Records", len(uses))
    st.metric("Species", uses.species.nunique())
