"""Add a study: give the librarian a study it has never seen and watch it join the map."""
import csv
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ for ui.py
from pipeline import config, extract  # noqa: E402
from pipeline.add_study import add_study, slugify  # noqa: E402
from pipeline.db import connect  # noqa: E402
from i18n import t  # noqa: E402
from ui import page_header, section  # noqa: E402

page_header("upload_file", "Curation", "Add a study",
            "Upload an open ethnobotanical study the librarian has never seen. An AI model reads it, the plant "
            "names are matched, and every record lands on the map with its page and quote.")

if not config.DB_PATH.exists():
    st.error(t("No database yet. Run `make build` first, then reopen this page."), icon=":material/database:")
    st.stop()

if extract.provider() is None or config.OFFLINE:
    st.warning("Reading a new study needs a free `GROQ_API_KEY` in `.env` (https://console.groq.com/keys) and "
               "`OFFLINE` unset. Without it, only a study with a checked extraction in "
               "`data/cache/extract/<id>.json` can be added.", icon=":material/key:")
elif extract.provider() == "groq":
    st.caption(f":material/bolt: Extraction runs on Groq's free tier (`{extract.GROQ_EXTRACT_MODEL}`), "
               f"{extract.GROQ_PAGES_PER_CALL} pages per request. A 15-page study can take a few minutes because of "
               "the free rate limit. Records whose quote is not found on the cited page are dropped.")

with open(config.SEED / "places.csv", encoding="utf-8") as f:
    places = list(csv.DictReader(f))
areas = [p["place"] for p in places if p["kind"] == "region"] + [p["place"] for p in places if p["kind"] != "region"]

with st.form("add-study", border=True):
    upload = st.file_uploader(t("Study file"), type=["pdf", "txt"],
                              help="An open-access PDF with selectable text, or a plain-text file.")
    left, right = st.columns(2)
    title = left.text_input(t("Title"), placeholder="Medicinal plants of the Rugova highlands")
    doc_id = right.text_input(t("Short id (optional)"), placeholder="mustafa2012",
                              help="Used as the file name. Taken from the title if empty.")
    citation = st.text_input(t("Citation"), placeholder="Author A, Author B. Journal. Year;Vol:Pages. doi:…")
    left, right = st.columns(2)
    url = left.text_input(t("Link to the study"), placeholder="https://…")
    licence = right.text_input(t("Licence"), placeholder="CC BY 4.0")
    study_area = st.selectbox(t("Study area"), areas, index=areas.index("Malet e Sharrit") if "Malet e Sharrit" in areas else 0,
                              help=t("Records that name no village are put here on the map."))
    st.caption(":material/info: Check that the licence allows reuse. The file is saved to `data/raw/` and the "
               "study to `data/seed/sources.csv`, so `make build` reproduces it.")
    submitted = st.form_submit_button(t("Read the study"), icon=":material/auto_stories:", type="primary")

if submitted:
    if upload is None or not (title or doc_id):
        st.error(t("Choose a file and give the study a title."))
        st.stop()
    meta = {"doc_id": doc_id or title, "title": title or doc_id, "citation": citation, "url": url,
            "licence": licence, "study_area": study_area}
    try:
        with st.status("Reading the study…", expanded=True) as status:
            st.write(f"Saving `{slugify(meta['doc_id'])}{Path(upload.name).suffix.lower()}` and extracting the text")
            st.write("The AI model is pulling out plant, part, preparation and use, with page and quote")
            result = add_study(upload.getvalue(), Path(upload.name).suffix, meta)
            st.write(f"Matched {len(result.species)} plants; looked up evidence for {len(result.new_species)} new ones")
            status.update(label="Study added", state="complete", expanded=False)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    except Exception as exc:  # noqa: BLE001 - show API errors instead of a traceback
        st.error(f"Could not read the study: {type(exc).__name__}: {str(exc)[:200]}")
        st.stop()
    st.session_state["added_doc"] = result.doc_id

doc = st.session_state.get("added_doc")
conn = connect()
if doc:
    rows = pd.read_sql_query("SELECT * FROM uses WHERE doc_id = ?", conn, params=(doc,))
    new_species = set(rows.species.dropna()) - set(pd.read_sql_query(
        "SELECT DISTINCT species FROM uses WHERE doc_id NOT IN (?, ?)", conn, params=(doc, "sample_fixture")).species)
    st.success(f"**{doc}** added: {len(rows)} records, {rows.species.nunique()} plants, "
               f"{len(new_species)} new to the library.", icon=":material/check_circle:")
    a, b, c, d = st.columns(4)
    a.metric(t("Records"), len(rows))
    b.metric(t("Plants"), rows.species.nunique())
    c.metric(t("New plants"), len(new_species))
    d.metric(t("Placed by village"), int((rows.geo_precision == "record").sum()))

    section("map", "Where the new records were made",
            "Green: the record names a village or town. Grey: only the study area is known.")
    import folium  # noqa: E402
    from streamlit_folium import st_folium  # noqa: E402

    points = rows.dropna(subset=["lat", "lon"])
    if points.empty:
        st.markdown("None of the records could be placed on the map.")
    else:
        fmap = folium.Map(location=[float(points.lat.mean()), float(points.lon.mean())], zoom_start=8,
                          tiles="OpenStreetMap")
        for (lat, lon, place, precision), group in points.groupby(["lat", "lon", "place", "geo_precision"]):
            plants = ", ".join(sorted(group.species.dropna().unique())[:12])
            folium.Marker(
                [lat, lon], tooltip=f"{place}: {len(group)} records",
                popup=folium.Popup(f"<b>{place}</b> ({'village/town' if precision == 'record' else 'study area'})"
                                   f"<br>{plants}", max_width=320),
                icon=folium.Icon(color="darkgreen" if precision == "record" else "gray", icon="leaf", prefix="fa"),
            ).add_to(fmap)
        st_folium(fmap, height=420, use_container_width=True, key=f"new-study-map-{doc}")

    section("menu_book", "Extracted records", "Check each row against the page and quote. "
            "Correct or verify them on the Data quality review page.")
    shown = rows.assign(new=rows.species.isin(new_species).map({True: "new", False: ""}))
    st.dataframe(shown[["page", "local_name", "species", "new", "part_used", "preparation", "use", "place",
                        "match_method", "quote"]],
                 hide_index=True, width="stretch")
    profile = st.selectbox("Open a plant profile", sorted(rows.species.dropna().unique()))
    st.page_link("pages/plant_profile.py", label=f"Open {profile}", icon=":material/local_florist:",
                 query_params={"species": profile})

st.write("")
section("library_books", "Studies in the library")
sources = pd.read_sql_query(
    "SELECT s.doc_id, s.title, s.study_area, s.licence, COUNT(u.id) AS records FROM sources s "
    "LEFT JOIN uses u ON u.doc_id = s.doc_id WHERE s.doc_id != 'sample_fixture' GROUP BY s.doc_id", conn)
st.dataframe(sources, hide_index=True, width="stretch")
conn.close()
