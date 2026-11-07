"""Research gaps: for every plant, was the preparation people use ever tested?"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pipeline.compare import VERDICTS, compare_all  # noqa: E402
from pipeline.config import DB_PATH  # noqa: E402
from pipeline.db import connect  # noqa: E402

st.set_page_config(page_title="Research gaps · EthnoHack", page_icon="🧪", layout="wide")
st.markdown(
    """
    <style>
      :root { --ethno-ink: #20352a; --ethno-green: #174c35; --ethno-leaf: #26734d; }
      html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main { background: #f1efe5 !important; }
      [data-testid="stHeader"] { background: transparent; }
      .block-container { max-width: 1220px; padding-top: 1.5rem; padding-bottom: 4rem; }
      [data-testid="stAppViewContainer"] *, [data-testid="stMain"] * { color: var(--ethno-ink); }
      h1, h2, h3 { color: var(--ethno-green) !important; letter-spacing: -0.025em; }
      [data-testid="stMetric"] { background: #dfe9db !important; border: 1px solid #bacdb8 !important; border-radius: 14px; padding: 14px 18px; }
      [data-testid="stVerticalBlockBorderWrapper"] { background: #e4ebdf !important; border: 1px solid #c7d4c4 !important; border-radius: 16px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🧪 Research gaps")
st.caption(
    "Was the preparation people actually use (for example a hot tea) ever tested? This page compares "
    "each plant's traditional preparation with the keyword tags of its top PubMed results. It is a screening "
    "list of what to read or study next, not a review and not evidence that a remedy works."
)

if not DB_PATH.exists():
    st.error("No database yet. Run `make build` first, then reopen this page.")
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
metric_cols[0].metric("Plants", len(rows))
metric_cols[1].metric("Research gaps", sum(r["gap"] for r in rows),
                      help="No PubMed candidate is tagged with the preparation people use, or there are no studies at all.")
metric_cols[2].metric("Same prep · lab/animal only", counts["lab"])
metric_cols[3].metric("Same prep · human study tagged", counts["human"])
metric_cols[4].metric("Manually reviewed", counts["reviewed"])

labels = {v: VERDICTS[v][0] for v in VERDICTS}
chosen = st.multiselect("Show verdicts", list(labels.values()), default=list(labels.values()))
query = st.text_input("Filter by plant or local name", placeholder="e.g. Humulus, Mullaga")
visible = [r for r in rows if r["label"] in chosen
           and (not query or query.lower() in f"{r['species']} {r['local_names']}".lower())]

gaps = [r for r in visible if r["gap"]]
if gaps:
    st.subheader("Plants whose traditional preparation has not been studied")
    for r in gaps:
        with st.container(border=True):
            title_col, button_col = st.columns([5, 1])
            with title_col:
                st.markdown(f"### *{r['species']}* · {r['local_names'] or 'no local name'}")
                st.markdown(f"**{r['label']}.** {r['explanation']}")
                tags = ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in sorted(r["prep_tags"].items()))
                st.caption(f"Traditional preparation: {r['traditional_text']} · "
                           f"{r['papers']} PubMed candidates" + (f" · tags: {tags}" if tags else ""))
            with button_col:
                if st.button("Open profile", key=f"gap-{r['species']}", use_container_width=True):
                    st.query_params["species"] = r["species"]
                    st.switch_page("app.py")

st.subheader(f"All plants · {len(visible)}")
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
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.download_button("Download as CSV", table.to_csv(index=False).encode("utf-8"),
                       file_name="ethnohack_research_gaps.csv", mime="text/csv")

with st.expander("How the verdict is decided"):
    for v, (label, explanation, gap) in VERDICTS.items():
        st.markdown(f"- **{label}**{' (research gap)' if gap else ''}: {explanation}")
    st.caption("Traditional preparations are classified by keyword (infusion, decoction, tea → water-based; "
               "tincture, rakia → alcohol). PubMed papers are tagged from title and abstract keywords and only "
               "the top 40 results per plant are checked, so tags can be wrong or missing.")
