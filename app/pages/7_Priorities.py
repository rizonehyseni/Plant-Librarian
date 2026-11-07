"""Research priorities and knowledge at risk: what science should study next, and what only one group remembers."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ for ui.py
from pipeline.compare import compare_all  # noqa: E402
from pipeline.config import DB_PATH  # noqa: E402
from pipeline.db import connect  # noqa: E402
from pipeline.priorities import knowledge_at_risk, research_priorities, study_labels  # noqa: E402
from i18n import t  # noqa: E402
from ui import page_header, section  # noqa: E402

CATEGORY_LABEL = {
    "respiratory": "Respiratory", "digestive": "Digestive", "liver": "Liver and bile", "urinary": "Urinary and kidney",
    "heart_blood": "Heart and blood", "metabolic": "Diabetes and metabolism", "skin": "Skin and wounds",
    "musculoskeletal": "Joints and muscles", "nervous": "Nerves and sleep", "infection": "Infections and parasites",
    "immune_allergy": "Immunity and allergy", "cancer": "Cancer", "reproductive": "Women's health",
    "eye_ear_mouth": "Eyes, ears and mouth", "fever_inflammation": "Fever and inflammation",
}


def cat(c: str) -> str:
    return t(CATEGORY_LABEL.get(c, c))


def group(g: str) -> str:
    """'Malet e Sharrit 2015 · Turkish' with the community translated."""
    study, _, community = g.partition(" · ")
    return f"{study} · {t(community)}" if community else study


page_header("target", "Explore", "Priorities",
            "Which plants should science study next, and which knowledge only one community still holds. "
            "Computed from the library with written rules, no AI.")

if not DB_PATH.exists():
    st.error(t("No database yet. Run `make build` first, then reopen this page."), icon=":material/database:")
    st.stop()


@st.cache_data(show_spinner=False)
def load(database_mtime: int):
    del database_mtime
    conn = connect()
    try:
        rows = [dict(r) for r in conn.execute(
            "SELECT doc_id, community, species, local_name, use FROM uses "
            "WHERE species IS NOT NULL AND doc_id != 'sample_fixture'")]
        verdicts = {r["species"]: r for r in compare_all(conn)}
        labels = study_labels(conn)
    finally:
        conn.close()
    return rows, verdicts, labels


rows, verdicts, labels = load(DB_PATH.stat().st_mtime_ns)
if not rows:
    st.info(t("The database has no plant-use records yet."))
    st.stop()

view = st.segmented_control(
    t("View"), ["priorities", "risk"], default="priorities", required=True, key="priorities_view",
    format_func=lambda v: t("What should science study next?") if v == "priorities" else t("Knowledge at risk"),
    label_visibility="collapsed")

# ---------------------------------------------------------------- research priorities
if view == "priorities":
    prio = research_priorities(rows, verdicts, labels)
    gaps = [p for p in prio if p["gap"]]
    cross = [p for p in prio if p["studies"] > 1]
    m = st.columns(3)
    m[0].metric(t("Priority plants"), len(prio), border=True,
                help=t("Used for the same body system by 2+ independent groups, preparation not tested in humans"))
    m[1].metric(t("Preparation never tested"), len(gaps), border=True,
                help=t("Studies exist, but none with the preparation people use, or no studies at all"))
    m[2].metric(t("Confirmed in 2+ regions"), len(cross), border=True,
                help=t("Reported in more than one study region"))
    st.caption(":material/info: " + t(
        "A group is one community in one study. When separate groups use a plant for the same kind of complaint, "
        "the use was passed on independently: a stronger reason to test it. Ranking: independent groups, then a "
        "second region, then whether the preparation was never tested. This is a list of hypotheses to study, not "
        "evidence that a remedy works."))

    section("science", "Top candidates for new studies")
    if not prio:
        st.info(t("No plant meets the rule yet. Add more studies to find independent reports."))
    for n, p in enumerate(prio[:10], 1):
        v = verdicts[p["species"]]
        local = v.get("local_names") or ""
        with st.container(border=True):
            left, right = st.columns([5, 1], vertical_alignment="center")
            with left:
                st.markdown(f"#### {n}. *{p['species']}*" + (f" · {local}" if local else ""))
                badge = ":red-badge[:material/report: " + t(v["label"]) + "]" if p["gap"] else \
                    ":orange-badge[:material/biotech: " + t(v["label"]) + "]"
                st.markdown(f":blue-badge[:material/stethoscope: {cat(p['category'])}] "
                            f":green-badge[:material/groups: {t('{n} independent groups', n=p['n_groups'])}] "
                            + (f":violet-badge[:material/public: {t('{n} regions', n=p['studies'])}] "
                               if p["studies"] > 1 else "") + badge)
                prep = ", ".join(t(x) for x in p["traditional_text"].split(", "))
                groups = ", ".join(group(g) for g in p["groups"])
                if p["gap"]:
                    st.markdown(t("Reported by: {groups}. People prepare it {prep}; of {papers} PubMed candidates, "
                                  "none is tagged with this preparation.", groups=groups, prep=prep, papers=p["papers"]))
                else:
                    st.markdown(t("Reported by: {groups}. People prepare it {prep}; {matching} of {papers} PubMed "
                                  "candidates use this preparation, all in the lab or in animals.", groups=groups,
                                  prep=prep, matching=v.get("matching", 0), papers=p["papers"]))
                if p["other_categories"]:
                    st.caption(t("Also used for: {cats}", cats=", ".join(cat(c) for c in p["other_categories"])))
            with right:
                if st.button(t("Open profile"), key=f"prio-{p['species']}", width="stretch",
                             icon=":material/arrow_forward:"):
                    st.switch_page("pages/plant_profile.py", query_params={"species": p["species"]})

    if len(prio) > 10:
        with st.expander(t("All {n} priority plants", n=len(prio)), icon=":material/table_chart:"):
            table = pd.DataFrame([{
                t("Plant"): p["species"], t("Body system"): cat(p["category"]),
                t("Independent groups"): p["n_groups"], t("Regions"): p["studies"], t("Records"): p["records"],
                t("Verdict"): t(verdicts[p["species"]]["label"]), t("PubMed candidates"): p["papers"],
            } for p in prio])
            st.dataframe(table, hide_index=True, width="stretch")
            st.download_button(t("Download as CSV"), table.to_csv(index=False).encode("utf-8"),
                               file_name="ethnohack_research_priorities.csv", mime="text/csv",
                               icon=":material/download:")

# ---------------------------------------------------------------- knowledge at risk
else:
    risk = knowledge_at_risk(rows, labels)
    m = st.columns(3)
    m[0].metric(t("Plants known by one group only"), len(risk["unique_plants"]), border=True,
                help=t("No other community or study in the library reports this plant"))
    m[1].metric(t("Uses known by one group only"), len(risk["unique_uses"]), border=True,
                help=t("The plant is known elsewhere, but this use is reported by one group only"))
    m[2].metric(t("Groups compared"), len(risk["groups"]), border=True)
    st.caption(":material/info: " + t(
        "If the people of that group stop passing it on, nothing else in the library records this knowledge. A "
        "plant missing from one study does not prove the others never knew it; the studies asked different people "
        "in different places. More studies make this list more reliable."))

    section("groups", "Unique knowledge per group")
    per = pd.DataFrame([{t("Group"): group(g), t("Plants reported"): d["plants"],
                         t("Plants only this group reports"): d["only_here"],
                         t("Uses only this group reports"): d["unique_uses"]} for g, d in risk["per_group"].items()])
    st.dataframe(per, hide_index=True, width="stretch",
                 column_config={t("Plants only this group reports"): st.column_config.ProgressColumn(
                     t("Plants only this group reports"), min_value=0, format="%d",
                     max_value=int(per[t("Plants only this group reports")].max() or 1))})

    section("person_pin", "Plants only one group reports")
    chosen = st.pills(t("Group"), risk["groups"], selection_mode="multi", default=risk["groups"], format_func=group,
                      key="risk_groups")
    plants = [p for p in risk["unique_plants"] if p["group"] in (chosen or [])]
    if plants:
        st.dataframe(pd.DataFrame([{t("Plant"): p["species"], t("Local name"): p["local_names"],
                                    t("Group"): group(p["group"]), t("Records"): p["records"]} for p in plants]),
                     hide_index=True, width="stretch")
    with st.expander(t("Uses only one group reports ({n})", n=len(risk["unique_uses"])), icon=":material/list:"):
        uses = [u for u in risk["unique_uses"] if u["group"] in (chosen or [])]
        st.dataframe(pd.DataFrame([{t("Plant"): u["species"], t("Body system"): cat(u["category"]),
                                    t("Group"): group(u["group"]), t("Records"): u["records"]} for u in uses]),
                     hide_index=True, width="stretch")

st.caption(":material/info: " + t("Traditional-use reports, not proof that a remedy works. Not medical advice."))
