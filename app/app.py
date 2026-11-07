"""EthnoHack plant librarian: app entry point and navigation (`make app`)."""
import streamlit as st

from i18n import LANGUAGES, t
from ui import apply_theme

st.set_page_config(page_title="Plant librarian · EthnoHack", page_icon=":material/eco:", layout="wide")
apply_theme()

with st.sidebar:
    # Rendered in the entrypoint on every run, so the choice holds on every page.
    st.segmented_control(":material/translate: Gjuha · Language", list(LANGUAGES.values()), default="Shqip",
                         key="lang", required=True)

pages = {
    t("Explore"): [
        st.Page("pages/plant_profile.py", title=t("Plant profile"), icon=":material/local_florist:", default=True),
        st.Page("pages/2_Explore_Advanced_Search.py", title=t("Search & compare"),
                icon=":material/travel_explore:", url_path="search"),
        st.Page("pages/6_Map.py", title=t("Map of uses"), icon=":material/map:", url_path="map"),
        st.Page("pages/4_Research_Gaps.py", title=t("Research gaps"), icon=":material/science:", url_path="gaps"),
        st.Page("pages/7_Priorities.py", title=t("Priorities"), icon=":material/target:", url_path="priorities"),
    ],
    t("Assistant"): [
        st.Page("pages/3_Ask_the_Librarian.py", title=t("Ask the librarian"), icon=":material/forum:", url_path="ask"),
    ],
    t("Curation"): [
        st.Page("pages/1_Data_Quality_Review.py", title=t("Data quality review"),
                icon=":material/fact_check:", url_path="review"),
        st.Page("pages/5_Add_a_Study.py", title=t("Add a study"), icon=":material/upload_file:", url_path="add"),
    ],
}
page = st.navigation(pages)

with st.sidebar:
    st.caption(":material/info: " + t("Research prototype. Traditional-use reports are not proof that a remedy works, "
                                      "and nothing here is medical advice."))

page.run()
