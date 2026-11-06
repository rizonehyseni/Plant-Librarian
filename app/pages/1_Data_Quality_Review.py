"""Local data-quality dashboard and human review workflow."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pipeline.config import DB_PATH  # noqa: E402
from pipeline.db import connect  # noqa: E402
from pipeline.quality import (  # noqa: E402
    ISSUE_LABELS,
    RECORD_ORIGINS,
    REVIEW_STATUSES,
    audit_history,
    check_records,
    dashboard_metrics,
    fetch_records,
    filter_records,
    issue_messages,
    save_review,
)

st.set_page_config(page_title="Data Quality & Review · EthnoHack", page_icon="🔎", layout="wide")
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
      [data-testid="stTextInput"] input, [data-testid="stSelectbox"] [data-baseweb="select"] > div, [data-testid="stTextArea"] textarea { background: #fffdf7 !important; border-color: #b8c9b8 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🔎 Data Quality & Review")
st.caption("Local review workspace. Changes are stored in SQLite with a record-level audit trail.")

if not DB_PATH.exists():
    st.error("No database yet. Run `make build` first, then reopen this page.")
    st.stop()

conn = connect()
records = fetch_records(conn)
if not records:
    st.info("The database has no plant-use records to review.")
    conn.close()
    st.stop()

findings = check_records(records)
metrics = dashboard_metrics(records, findings)
metric_labels = [
    ("Total records", "total"), ("Verified", "verified"), ("Needs review", "needs_review"),
    ("AI-extracted", "ai_extracted"), ("Missing citations", "missing_citations"),
    ("Unresolved names", "unresolved_names"), ("No specific location", "without_specific_locations"),
]
for column, (label, key) in zip(st.columns(4), metric_labels[:4]):
    column.metric(label, metrics[key])
for column, (label, key) in zip(st.columns(3), metric_labels[4:]):
    column.metric(label, metrics[key])

st.divider()
st.subheader("Review queue")
filter_columns = st.columns(3)
with filter_columns[0]:
    status_filter = st.selectbox("Review status", ["All", *REVIEW_STATUSES])
with filter_columns[1]:
    species_options = sorted({record["species"] for record in records if record.get("species")})
    species_filter = st.selectbox("Plant species", ["All", *species_options])
with filter_columns[2]:
    issue_filter = st.selectbox("Data quality issue", ["All", *ISSUE_LABELS])

filtered = filter_records(
    records,
    findings,
    review_status=None if status_filter == "All" else status_filter,
    species=None if species_filter == "All" else species_filter,
    issue=None if issue_filter == "All" else issue_filter,
)
table_rows = []
for record in filtered:
    table_rows.append({
        "ID": record["id"],
        "Local name": record.get("local_name") or "—",
        "Scientific name": record.get("species") or "Unresolved",
        "Traditional use": record.get("use") or "—",
        "Plant part": record.get("part_used") or "—",
        "Preparation": record.get("preparation") or "—",
        "Source / page": f"{record.get('source_title') or record.get('doc_id') or 'Missing'} · {record.get('page') or '—'}",
        "Location": record.get("location") or record.get("place") or "Not specific",
        "Review status": record.get("review_status"),
        "Warnings": "\n".join(issue_messages(findings[record["id"]])) or "None",
    })
st.dataframe(pd.DataFrame(table_rows), hide_index=True, use_container_width=True, height=400)

record_by_id = {record["id"]: record for record in filtered}
if not record_by_id:
    st.info("No records match these filters.")
    conn.close()
    st.stop()

st.divider()
st.subheader("Inspect and review a record")
selected_id = st.selectbox(
    "Select record", list(record_by_id),
    format_func=lambda record_id: f"#{record_id} · {record_by_id[record_id].get('local_name') or 'Unnamed'} · {record_by_id[record_id].get('species') or 'Unresolved'}",
)
selected = record_by_id[selected_id]
if findings[selected_id]:
    st.warning(" | ".join(issue_messages(findings[selected_id])))
else:
    st.success("No automatic data-quality warnings for this record.")

with st.form("review-record"):
    form_columns = st.columns(2)
    with form_columns[0]:
        local_name = st.text_input("Local plant name", value=selected.get("local_name") or "")
        species = st.text_input("Scientific plant name", value=selected.get("species") or "")
        plant_part = st.text_input("Plant part", value=selected.get("part_used") or "")
        preparation = st.text_input("Preparation", value=selected.get("preparation") or "")
        traditional_use = st.text_area("Traditional use", value=selected.get("use") or "")
    with form_columns[1]:
        location = st.text_input("Recorded location", value=selected.get("location") or "")
        page = st.text_input("Source page", value=str(selected.get("page") or ""))
        origin = st.selectbox("Record origin", RECORD_ORIGINS, index=RECORD_ORIGINS.index(selected.get("record_origin") or "AI Extracted"))
        review_status = st.selectbox("Review status", REVIEW_STATUSES, index=REVIEW_STATUSES.index(selected.get("review_status") or "Needs Review"))
        reviewer = st.text_input("Local reviewer", placeholder="e.g. A. Hoxha")
    reviewer_note = st.text_area("Reviewer note", value=selected.get("reviewer_note") or "", placeholder="What was checked or corrected?")
    saved = st.form_submit_button("Save review")

if saved:
    updates = {
        "local_name": local_name, "species": species, "part_used": plant_part,
        "preparation": preparation, "use": traditional_use, "location": location,
        "page": page or None, "record_origin": origin, "review_status": review_status,
        "reviewer_note": reviewer_note,
    }
    try:
        save_review(conn, selected_id, updates, reviewer, reviewer_note)
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.success("Review saved. The audit log has been updated.")
        st.rerun()

with st.expander("Change history", expanded=True):
    history = audit_history(conn, selected_id)
    if history:
        history_frame = pd.DataFrame(history).rename(columns={
            "changed_field": "Field", "previous_value": "Previous", "new_value": "New",
            "timestamp": "Timestamp", "action": "Action", "reviewer": "Reviewer", "reviewer_note": "Note",
        })
        st.dataframe(history_frame[["Timestamp", "Action", "Field", "Previous", "New", "Reviewer", "Note"]], hide_index=True, use_container_width=True)
    else:
        st.caption("No review actions have been recorded for this record.")

conn.close()
