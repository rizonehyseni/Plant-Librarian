"""Research gaps: for every plant, was the preparation people use ever tested?"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ for ui.py
from pipeline.compare import VERDICTS, compare_all  # noqa: E402
from pipeline.config import DB_PATH  # noqa: E402
from pipeline.db import connect  # noqa: E402
from ui import page_header, section  # noqa: E402

page_header("science", "Explore", "Research gaps",
            "Was the preparation people actually use, such as a hot tea, ever tested? Plants with no matching studies are listed first.")
st.caption(":material/info: Compares each plant's traditional preparation with the keyword tags of its top "
           "PubMed results. A screening list of what to read or study next, not a review and not evidence "
           "that a remedy works.")

if not DB_PATH.exists():
    st.error("No database yet. Run `make build` first, then reopen this page.", icon=":material/database:")
    st.stop()


@st.cache_data(show_spinner="Comparing preparations…")
def load(database_mtime: int):
    del database_mtime
    conn = connect()
    try:
        return compare_all(conn)
    finally:
        conn.close()


rows = load(DB_PATH.stat().st_mtime_ns)
if not rows:
    st.info("The database has no plant-use records yet.")
    st.stop()

counts = {v: sum(r["verdict"] == v for r in rows) for v in VERDICTS}
metric_cols = st.columns(5)
metric_cols[0].metric("Plants", len(rows), border=True)
metric_cols[1].metric("Research gaps", sum(r["gap"] for r in rows), border=True,
                      help="No PubMed candidate is tagged with the preparation people use, or there are no studies at all.")
metric_cols[2].metric("Lab / animal only", counts["lab"], border=True,
                      help="Same preparation tag, but no human-study tag")
metric_cols[3].metric("Human study tagged", counts["human"], border=True,
                      help="Same preparation tag and a human-study tag")
metric_cols[4].metric("Manually reviewed", counts["reviewed"], border=True)

labels = {v: VERDICTS[v][0] for v in VERDICTS}
filter_cols = st.columns([2, 1])
with filter_cols[0]:
    chosen = st.multiselect("Show verdicts", list(labels.values()), default=list(labels.values()))
with filter_cols[1]:
    query = st.text_input("Filter by plant or local name", placeholder="e.g. Humulus, Mullaga",
                          icon=":material/search:")
visible = [r for r in rows if r["label"] in chosen
           and (not query or query.lower() in f"{r['species']} {r['local_names']}".lower())]

gaps = [r for r in visible if r["gap"]]
if gaps:
    section("report", "Plants whose traditional preparation has not been studied")
    for r in gaps:
        with st.container(border=True):
            title_col, button_col = st.columns([5, 1])
            with title_col:
                st.markdown(f"#### *{r['species']}*")
                st.markdown(f":green-badge[:material/translate: {r['local_names'] or 'no local name'}] "
                            f":red-badge[:material/report: {r['label']}]")
                st.markdown(r["explanation"])
                tags = ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in sorted(r["prep_tags"].items()))
                st.caption(f"Traditional preparation: {r['traditional_text']} · "
                           f"{r['papers']} PubMed candidates" + (f" · tags: {tags}" if tags else ""))
            with button_col:
                if st.button("Open profile", key=f"gap-{r['species']}", width="stretch",
                             icon=":material/arrow_forward:"):
                    st.switch_page("pages/plant_profile.py", query_params={"species": r["species"]})

section("table_chart", f"All plants · {len(visible)}")
table = pd.DataFrame([{
    "Plant": r["species"],
    "Local name": r["local_names"],
    "Traditional preparation": r["traditional_text"],
    "Verdict": r["label"],
    "PubMed candidates": r["papers"],
    "Same preparation tag": r["matching"],
    "…of which human": r["matching_human"],
    "Reviewed papers": len(r["reviewed"]),
} for r in visible])
if table.empty:
    st.info("No plants match this filter.")
else:
    st.dataframe(table, hide_index=True, width="stretch")
    st.download_button("Download as CSV", table.to_csv(index=False).encode("utf-8"),
                       file_name="ethnohack_research_gaps.csv", mime="text/csv", icon=":material/download:")

with st.expander("How the verdict is decided", icon=":material/rule:"):
    for v, (label, explanation, gap) in VERDICTS.items():
        st.markdown(f"- **{label}**{' (research gap)' if gap else ''}: {explanation}")
    st.caption("Traditional preparations are classified by keyword (infusion, decoction, tea → water-based; "
               "tincture, rakia → alcohol). PubMed papers are tagged from title and abstract keywords and only "
               "the top 40 results per plant are checked, so tags can be wrong or missing.")
