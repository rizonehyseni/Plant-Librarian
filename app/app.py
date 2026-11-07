"""EthnoHack plant librarian: app entry point and navigation (`make app`)."""
import streamlit as st

from ui import apply_theme

st.set_page_config(page_title="Plant librarian · EthnoHack", page_icon=":material/eco:", layout="wide")
apply_theme()

pages = {
    "Explore": [
        st.Page("pages/plant_profile.py", title="Plant profile", icon=":material/local_florist:", default=True),
        st.Page("pages/2_Explore_Advanced_Search.py", title="Search & compare",
                icon=":material/travel_explore:", url_path="search"),
        st.Page("pages/4_Research_Gaps.py", title="Research gaps", icon=":material/science:", url_path="gaps"),
    ],
    "Assistant": [
        st.Page("pages/3_Ask_the_Librarian.py", title="Ask the librarian", icon=":material/forum:", url_path="ask"),
    ],
    "Curation": [
        st.Page("pages/1_Data_Quality_Review.py", title="Data quality review",
                icon=":material/fact_check:", url_path="review"),
        st.Page("pages/5_Add_a_Study.py", title="Add a study", icon=":material/upload_file:", url_path="add"),
    ],
}
page = st.navigation(pages)

with st.sidebar:
    st.caption(":material/info: Research prototype. Traditional-use reports are not proof that a remedy "
               "works, and nothing here is medical advice.")

page.run()
