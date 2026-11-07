"""Explore, filter and compare sourced traditional plant-use records."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ for ui.py
from pipeline.config import DB_PATH  # noqa: E402
from pipeline.db import connect  # noqa: E402
from pipeline.explore import (  # noqa: E402
    TRADITIONAL_EVIDENCE,
    compare_plants,
    filter_options,
    load_records,
    page_records,
    search_and_filter,
    sort_records,
)
from i18n import t  # noqa: E402
from ui import page_header, section  # noqa: E402

FILTER_KEYS = (
    "explore_query", "explore_species", "explore_parts", "explore_preparations",
    "explore_uses", "explore_locations", "explore_evidence", "explore_safety",
    "explore_status",
)


def clear_filters():
    for key in FILTER_KEYS:
        st.session_state[key] = [] if key != "explore_query" else ""


@st.cache_data(show_spinner="Loading plant records…")
def cached_records(database_mtime: int):
    del database_mtime
    connection = connect()
    try:
        return load_records(connection)
    finally:
        connection.close()


def display_values(values: list[str]) -> str:
    return ", ".join(values) if values else t("Not available in current data")


page_header("travel_explore", "Explore", "Search & compare",
            "Search every documented use by name, use, part or preparation, filter the records, and compare up to three plants side by side.")

if not DB_PATH.exists():
    st.error(t("No database yet. Run `make build` first, then reopen this page."))
    st.stop()

records = cached_records(DB_PATH.stat().st_mtime_ns)
if not records:
    st.info("The database has no resolved plant-use records to explore.")
    st.stop()

options = filter_options(records)
search_column, clear_column = st.columns([5, 1])
with search_column:
    query = st.text_input(
        t("Search names, aliases, uses, or descriptions"),
        placeholder=t("Try Çaj mali, Origanum, kamomil, or respiratory"),
        key="explore_query", icon=":material/search:",
    )
with clear_column:
    st.write("")
    st.button(t("Clear filters"), on_click=clear_filters, width="stretch", icon=":material/filter_alt_off:")

with st.expander(t("Advanced filters"), expanded=True, icon=":material/tune:"):
    first_row = st.columns(3)
    with first_row[0]:
        selected_species = st.multiselect(t("Plant species"), options["species"], key="explore_species")
        selected_parts = st.multiselect(t("Plant parts"), options["parts"], key="explore_parts")
        selected_preparations = st.multiselect(t("Preparation methods"), options["preparations"], key="explore_preparations")
    with first_row[1]:
        selected_uses = st.multiselect(t("Traditional uses"), options["uses"], key="explore_uses")
        selected_locations = st.multiselect(t("Geographic locations"), options["locations"], key="explore_locations")
        selected_evidence = st.multiselect(t("Evidence type"), options["evidence"], key="explore_evidence")
    with first_row[2]:
        selected_safety = st.multiselect(t("Safety or risk status"), options["safety"], key="explore_safety")
        selected_status = st.multiselect(t("Record verification status"), options["review_status"], key="explore_status")
        order = st.selectbox(t("Sort results"), ["Plant name", "Scientific name", "Number of documented uses", "Verification status"],
                             format_func=t)

filtered = search_and_filter(
    records, query=query, species=selected_species, parts=selected_parts,
    preparations=selected_preparations, uses=selected_uses, locations=selected_locations,
    evidence_types=selected_evidence, safety_levels=selected_safety,
    review_statuses=selected_status,
)
ordered = sort_records(filtered, order)
section("list_alt", t("Matching records · {n}", n=len(ordered)))

if not ordered:
    st.info(t("No records match this search and filter combination. Clear filters or try a broader term."))
else:
    visible, total_pages = page_records(ordered, page=1)
    if total_pages > 1:
        page_number = st.selectbox(t("Result page"), list(range(1, total_pages + 1)))
        visible, _ = page_records(ordered, page=page_number)
    for record in visible:
        with st.container(border=True):
            title_column, action_column = st.columns([5, 1])
            with title_column:
                st.markdown(f"### {record.get('local_name') or 'Unnamed plant'} · *{record['species']}*")
                st.caption(f"Verification: {record.get('review_status', 'Not reviewed')} · {record.get('use_count', 1)} documented use record(s)")
            with action_column:
                if st.button(t("Open profile"), key=f"profile-{record['id']}", width="stretch", icon=":material/arrow_forward:"):
                    st.switch_page("pages/plant_profile.py", query_params={"species": record["species"]})
            detail_columns = st.columns(3)
            detail_columns[0].markdown(f"**{t('Traditional use')}**  \n{record.get('use') or 'Not available'}")
            detail_columns[1].markdown(f"**{t('Plant part / preparation')}**  \n{record.get('part_used') or 'Not available'} · {record.get('preparation') or 'Not available'}")
            detail_columns[2].markdown(f"**{t('Recorded location')}**  \n{record.get('location_label') or 'Not specific in current data'}")
            modern_types = sorted(item for item in record["evidence_types"] if item != TRADITIONAL_EVIDENCE)
            st.caption(f"Traditional evidence: documented study record. Modern study tags: {display_values(modern_types)}.")
            if record["safety_flags"]:
                st.warning(" · ".join(f"{flag.get('level', 'flag').title()}: {flag.get('note', '')}" for flag in record["safety_flags"]))
            else:
                st.caption("No item in the project's limited safety-rule list matched this plant; this is not a safety assessment.")

st.divider()
section("compare_arrows", "Compare plants")
comparison_species = st.multiselect(
    t("Select up to three plant profiles"), options["species"], max_selections=3,
    placeholder=t("Choose plants to compare"),
)
if comparison_species:
    comparison = compare_plants(records, comparison_species)
    comparison_columns = st.columns(len(comparison))
    for column, plant in zip(comparison_columns, comparison):
        with column:
            st.markdown(f"### *{plant['species']}*")
            st.markdown(f"**{t('Local names')}**  \n{display_values(plant['local_names'])}")
            st.markdown(f"**{t('Documented uses')}**  \n{display_values(plant['uses'])}")
            st.markdown(f"**{t('Plant parts')}**  \n{display_values(plant['parts'])}")
            st.markdown(f"**{t('Preparations')}**  \n{display_values(plant['preparations'])}")
            st.markdown(f"**{t('Locations')}**  \n{display_values(plant['locations'])}")
            modern_types = [item for item in plant["evidence_types"] if item != TRADITIONAL_EVIDENCE]
            st.markdown(f"**{t('Modern study tags')}**  \n{display_values(modern_types)}")
            st.markdown(f"**{t('Verification')}**  \n{display_values(plant['review_statuses'])}")
            if plant["safety_flags"]:
                st.markdown(f"**{t('Safety information')}**")
                for flag in plant["safety_flags"]:
                    st.caption(f"{flag.get('level', 'flag').title()}: {flag.get('note', 'Not available')}")
            else:
                st.markdown("**Safety information**  \nNot available in the current safety-rule list.")
else:
    st.caption(t("Choose one to three plants to compare only the information available in this database."))
