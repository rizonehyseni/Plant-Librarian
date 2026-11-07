"""Map of recorded uses: every study record on one map, with filters and community overlap."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ for ui.py
from pipeline.atlas import community_overlap, place_summary  # noqa: E402
from pipeline.config import DB_PATH  # noqa: E402
from pipeline.db import connect  # noqa: E402
from i18n import t  # noqa: E402
from ui import page_header, section  # noqa: E402

page_header("map", "Explore", "Map of recorded uses",
            "Where each traditional use was recorded, across all studies in the library. Filter by community, "
            "plant, use or preparation, and see which plants the communities share.")

if not DB_PATH.exists():
    st.error(t("No database yet. Run `make build` first, then reopen this page."), icon=":material/database:")
    st.stop()


@st.cache_data(show_spinner=False)
def load(database_mtime: int):
    del database_mtime
    conn = connect()
    try:
        uses = pd.read_sql_query(
            "SELECT u.*, s.title AS study FROM uses u LEFT JOIN sources s ON s.doc_id = u.doc_id "
            "WHERE u.species IS NOT NULL AND u.doc_id != 'sample_fixture'", conn)
        occ = pd.read_sql_query("SELECT species, lat, lon FROM occurrences WHERE lat IS NOT NULL", conn)
        flags = pd.read_sql_query("SELECT species, kind, level FROM flags", conn)
    finally:
        conn.close()
    return uses, occ, flags


uses, occ, flags = load(DB_PATH.stat().st_mtime_ns)
if uses.empty:
    st.info(t("The database has no plant-use records yet."))
    st.stop()
uses["community"] = uses.community.fillna("Not stated")

# ---------------------------------------------------------------- filters
with st.container(border=True):
    c1, c2 = st.columns(2)
    communities = sorted(uses.community.unique())
    chosen_comm = c1.multiselect(t("Community"), communities, default=communities, format_func=t)
    studies = sorted(uses.study.dropna().unique())
    chosen_study = c2.multiselect(t("Study"), studies, default=studies)
    c3, c4, c5 = st.columns([1.2, 1, 1])
    use_query = c3.text_input(t("Use contains"), placeholder=t("cough, wound, stomach…"), icon=":material/search:")
    prep_labels = {"aqueous": "Water-based (tea, decoction)", "oil": "Oil or fat", "ethanolic": "Alcohol",
                   "essential_oil": "Essential oil", "other": "Other or eaten"}
    preps = sorted(uses.prep_class.dropna().unique())
    chosen_prep = c4.multiselect(t("Preparation"), preps, default=preps, format_func=lambda p: t(prep_labels.get(p, p)))
    plant = c5.selectbox(t("Plant"), ["All plants"] + sorted(uses.species.unique()), format_func=t)

view = uses[uses.community.isin(chosen_comm) & uses.study.isin(chosen_study) & uses.prep_class.isin(chosen_prep)]
if use_query:
    view = view[view.use.str.contains(use_query, case=False, na=False)]
if plant != "All plants":
    view = view[view.species == plant]

m = st.columns(4)
m[0].metric(t("Use records"), len(view), border=True)
m[1].metric(t("Plants"), view.species.nunique(), border=True)
m[2].metric(t("Communities"), view.community.nunique(), border=True)
m[3].metric(t("Studies"), view.doc_id.nunique(), border=True)
if view.empty:
    st.warning(t("No record matches these filters."))
    st.stop()

# ---------------------------------------------------------------- map
section("location_on", "Where the uses were recorded",
        "Green pin: the record names a village or town. Grey circle: only the study area is known, so the circle "
        "marks the region, not a spot. Circle size grows with the number of records.")
import folium  # noqa: E402
from folium.plugins import HeatMap  # noqa: E402
from streamlit_folium import st_folium  # noqa: E402

places = place_summary(view.to_dict("records"))
show_occ = st.toggle(t("Also show where these plants grow (GBIF occurrences)"), value=False,
                     help=t("GBIF points are where the plant was observed, not where a use was recorded."))
fmap = folium.Map(location=[42.3, 20.6], zoom_start=8, tiles="OpenStreetMap")
for p in places:
    popup = (f"<b>{p['place']}</b> ({t('village/town') if p['precision'] == 'record' else t('study area')})<br>"
             f"{p['records']} {t('records')} · {t('{n} plants', n=p['plants'])}<br>"
             f"{t('Communities')}: {', '.join(t(c) for c in p['communities']) or t('Not stated')}<br>"
             f"{t('Most reported')}: {', '.join(p['top_plants'])}")
    if p["precision"] == "record":
        folium.Marker([p["lat"], p["lon"]], tooltip=f"{p['place']}: {p['records']} {t('records')}",
                      popup=folium.Popup(popup, max_width=340),
                      icon=folium.Icon(color="darkgreen", icon="leaf", prefix="fa")).add_to(fmap)
    else:
        folium.CircleMarker([p["lat"], p["lon"]], radius=min(10 + p["records"] ** 0.5 * 1.5, 45),
                            color="#52665a", fill=True, fill_opacity=.25,
                            tooltip=f"{p['place']} ({t('study area')}): {p['records']} {t('records')}",
                            popup=folium.Popup(popup, max_width=340)).add_to(fmap)
if show_occ:
    pts = occ[occ.species.isin(view.species.unique())]
    if pts.empty:
        st.caption(t("No GBIF occurrences are loaded for these plants."))
    else:
        HeatMap(pts[["lat", "lon"]].values.tolist(), radius=9, blur=12, min_opacity=.3).add_to(fmap)
        st.caption(t("{n} GBIF occurrence points for {k} of the filtered plants.", n=len(pts), k=pts.species.nunique()))
st_folium(fmap, height=480, use_container_width=True, key="overview-map")

# ---------------------------------------------------------------- communities
if view.community.nunique() > 1:
    st.write("")
    section("diversity_3", "Which plants do the communities share?",
            "Counts plants with at least one use record per community in the current filter.")
    o = community_overlap(view.to_dict("records"))
    cols = st.columns(len(o["communities"]) + 1)
    cols[0].metric(t("Used by all"), len(o["shared_all"]), border=True)
    for col, c in zip(cols[1:], o["communities"]):
        col.metric(t("Only {c}", c=t(c)), len(o["only"][c]), border=True, help=t("{n} plants in total", n=o['per_community'][c]))
    matrix = (view.groupby(["species", "community"]).size().unstack(fill_value=0)
              .assign(total=lambda d: d.sum(axis=1)).sort_values("total", ascending=False))
    st.dataframe(matrix, width="stretch",
                 column_config={c: st.column_config.ProgressColumn(t(c), min_value=0, max_value=int(matrix[c].max()),
                                                                   format="%d")
                                for c in o["communities"]})
    with st.expander(t("Plants used by one community only"), icon=":material/person_pin:"):
        for c in o["communities"]:
            st.markdown(f"**{t(c)}** ({len(o['only'][c])}): " + (", ".join(f"*{s}*" for s in o["only"][c]) or t("none")))

# ---------------------------------------------------------------- risk
risky = flags[flags.species.isin(view.species.unique())]
if not risky.empty:
    st.write("")
    section("health_and_safety", "Plants with a safety or conservation flag",
            "From the project's limited rule list; no flag does not mean safe.")
    st.dataframe(risky.merge(view.groupby("species").size().rename("records").reset_index(), on="species"),
                 hide_index=True, width="stretch")

st.caption(":material/info: " + t("Traditional-use reports, not proof that a remedy works. Not medical advice."))
