"""Share family knowledge with consent; reviewers approve before anything is published."""
import csv
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ for ui.py
from pipeline import contributions as contrib  # noqa: E402
from pipeline.config import DB_PATH, SEED  # noqa: E402
from pipeline.db import connect  # noqa: E402
from i18n import lang, t  # noqa: E402
from ui import page_header, section  # noqa: E402

ERRORS = {
    "missing": "Write at least the plant name and what it is used for.",
    "consent": "Both consents are needed before anything can be saved.",
    "dose": "Please remove amounts and schedules (grams, cups, spoons, times a day). The library never shows doses.",
    "reviewer": "Write the reviewer's name first.",
}

page_header("volunteer_activism", "Curation", "Share family knowledge",
            "Add a traditional use you learned from your family. Nothing is published until a reviewer checks it, "
            "and it can be withdrawn at any time.")

with st.container(border=True):
    st.markdown("**" + t("Before you share") + "**")
    st.markdown(t("- Share only what the person who holds the knowledge agreed to share.\n"
                  "- Do not write names of people; *grandmother* or *neighbour* is enough.\n"
                  "- Do not write amounts or how often to take it: the library never shows doses.\n"
                  "- A reviewer reads every entry before it appears, marked as a community contribution.\n"
                  "- To withdraw an entry later, ask a reviewer: it is removed from the library."))

with open(SEED / "places.csv", encoding="utf-8") as f:
    places = [p["place"] for p in csv.DictReader(f)]

section("edit", "Your entry")
with st.form("share-knowledge", clear_on_submit=True):
    c1, c2 = st.columns(2)
    local_name = c1.text_input(t("Plant name as your family says it"), placeholder="Çaj mali, Hithi, Kamomil…")
    scientific = c2.text_input(t("Scientific name, if you know it (optional)"), placeholder="Sideritis scardica")
    c3, c4 = st.columns(2)
    part = c3.text_input(t("Part used"), placeholder=t("leaves, flowers, root…"))
    preparation = c4.text_input(t("How it is prepared"), placeholder=t("tea, boiled, ointment with butter…"))
    use = st.text_area(t("What it is used for"), placeholder=t("e.g. cough in winter, small wounds"))
    c5, c6 = st.columns(2)
    location = c5.selectbox(t("Where it is used"), places, index=None, placeholder=t("Village, town or region"))
    holder = c6.selectbox(t("Who holds this knowledge"), contrib.HOLDERS, index=None,
                          format_func=lambda h: t(h.capitalize()), placeholder=t("Optional, no names"))
    consent_share = st.checkbox(t("I agree that this entry is shared publicly in the library under CC BY 4.0."))
    consent_holder = st.checkbox(t("The person who holds this knowledge agreed that it is shared."))
    sent = st.form_submit_button(t("Send for review"), icon=":material/send:", type="primary")

if sent:
    try:
        new_id = contrib.submit({
            "local_name": local_name, "scientific_name": scientific, "part_used": part, "preparation": preparation,
            "use": use, "location": location, "knowledge_holder": holder, "language": lang(),
            "consent_share": consent_share, "consent_holder": consent_holder})
    except ValueError as exc:
        st.error(t(ERRORS.get(str(exc), str(exc))), icon=":material/error:")
    else:
        st.success(t("Thank you. Entry #{n} is waiting for a reviewer.", n=new_id), icon=":material/check_circle:")

# ---------------------------------------------------------------- reviewers
st.divider()
section("verified_user", "For reviewers",
        "In this prototype anyone can review. A real deployment would limit this to signed-in reviewers.")
reviewer = st.text_input(t("Reviewer name"), key="contrib_reviewer", placeholder="A. Hoxha")
pending = contrib.entries("pending")
approved = contrib.entries("approved")
m = st.columns(3)
m[0].metric(t("Waiting for review"), len(pending), border=True)
m[1].metric(t("Published"), len(approved), border=True)
m[2].metric(t("Rejected or withdrawn"), len(contrib.entries("rejected")) + len(contrib.entries("withdrawn")),
            border=True)


def act(entry: dict, status: str) -> None:
    try:
        updated = contrib.set_status(int(entry["id"]), status, reviewer, st.session_state.get(f"note-{entry['id']}", ""))
    except ValueError as exc:
        st.error(t(ERRORS.get(str(exc), str(exc))))
        return
    if DB_PATH.exists():
        conn = connect()
        try:
            if status == "approved":
                contrib.publish(conn, updated)
            elif status == "withdrawn":
                contrib.unpublish(conn, int(entry["id"]))
        finally:
            conn.close()
    st.toast(t("Entry #{n}: {s}", n=entry["id"], s=t(status)), icon=":material/done:")
    st.rerun()


for e in pending:
    with st.container(border=True):
        st.markdown(f"**#{e['id']} · {e['local_name']}**" + (f" · *{e['scientific_name']}*" if e["scientific_name"] else ""))
        st.markdown(f"{e['use']}  \n:gray-badge[{e['part_used'] or '—'}] :green-badge[{e['preparation'] or '—'}] "
                    f":blue-badge[:material/location_on: {e['location'] or '—'}] "
                    + (f":violet-badge[{t(e['knowledge_holder'].capitalize())}]" if e["knowledge_holder"] else ""))
        st.text_input(t("Reviewer note"), key=f"note-{e['id']}", label_visibility="collapsed",
                      placeholder=t("What was checked?"))
        b1, b2, _ = st.columns([1, 1, 3])
        if b1.button(t("Approve"), key=f"ok-{e['id']}", icon=":material/check:", type="primary", width="stretch"):
            act(e, "approved")
        if b2.button(t("Reject"), key=f"no-{e['id']}", icon=":material/close:", width="stretch"):
            act(e, "rejected")
if not pending:
    st.caption(t("No entries are waiting for review."))

if approved:
    with st.expander(t("Published entries ({n})", n=len(approved)), icon=":material/public:"):
        for e in approved:
            left, right = st.columns([4, 1], vertical_alignment="center")
            left.markdown(f"**#{e['id']} · {e['local_name']}**: {e['use']} · {e['location'] or '—'} · "
                          f"{t('reviewed by {r}', r=e['reviewer'])}")
            if right.button(t("Withdraw"), key=f"wd-{e['id']}", icon=":material/undo:", width="stretch"):
                act(e, "withdrawn")
        st.caption(t("Commit data/contributions/contributions.csv to keep published entries after `make build`."))

st.caption(":material/info: " + t("Traditional-use reports, not proof that a remedy works. Not medical advice."))
