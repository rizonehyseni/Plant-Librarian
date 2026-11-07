"""EthnoHack plant librarian: app entry point and navigation (`make app`)."""
import streamlit as st

from factsheet import app_url, qr_png
from i18n import LANGUAGES, t
from ui import apply_theme

st.set_page_config(page_title="Plant librarian · EthnoHack", page_icon=":material/eco:", layout="wide")
apply_theme()


@st.cache_resource(show_spinner=False)
def ensure_database() -> bool:
    """On a fresh server (e.g. Streamlit Cloud) there is no database yet: build it from the committed caches.

    Runs once per server, offline (no API calls, about 10 seconds), in a separate process so OFFLINE=1
    does not affect the running app.
    """
    import os
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    if (root / "data" / "ethnohack.db").exists():
        return True
    subprocess.run([sys.executable, "-m", "pipeline.build"], cwd=root, check=True,
                   env={**os.environ, "OFFLINE": "1"}, capture_output=True)
    return True


with st.spinner("Building the plant library for the first time (about 10 seconds)…"):
    ensure_database()

# A shared link can pick the language once: ?lang=en (for English-speaking judges) or ?lang=sq.
if "lang" not in st.session_state:
    st.session_state.lang = LANGUAGES.get(st.query_params.get("lang", "sq"), "Shqip")

with st.sidebar:
    # Rendered in the entrypoint on every run, so the choice holds on every page.
    st.segmented_control(":material/translate: Gjuha · Language", list(LANGUAGES.values()), key="lang",
                         required=True)

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
        st.Page("pages/8_Share_Knowledge.py", title=t("Share family knowledge"), icon=":material/volunteer_activism:",
                url_path="share"),
    ],
}
page = st.navigation(pages)

with st.sidebar:
    with st.popover(t("Share this app"), icon=":material/qr_code_2:", width="stretch"):
        st.image(qr_png(app_url()), width=200, alt=t("QR code for the app link"))
        st.caption(t("Scan to open the app on a phone.") + f"  \n`{app_url()}`")
        if "localhost" in app_url() or "127.0.0.1" in app_url():
            st.caption(":material/info: " + t("This is a local address. Set APP_URL to the public link after deploying."))
    st.caption(":material/info: " + t("Research prototype. Traditional-use reports are not proof that a remedy works, "
                                      "and nothing here is medical advice."))

page.run()
