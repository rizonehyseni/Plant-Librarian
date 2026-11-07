"""Chat assistant that answers only from the plant fact sheets, with sources."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ for ui.py
from pipeline import chat  # noqa: E402
from pipeline.config import DB_PATH, GROQ_API_KEY, GROQ_MODEL  # noqa: E402
from pipeline.db import connect  # noqa: E402
from ui import page_header  # noqa: E402

AVATARS = {"user": ":material/person:", "assistant": ":material/local_florist:"}
EXAMPLES = [  # (icon, question): each one shows a different part of the fact sheets
    ("local_cafe", "How is Mullaga prepared, and was the same tea ever tested?"),
    ("pulmonology", "Which plants were traditionally used for coughs?"),
    ("health_and_safety", "Are there any safety warnings for Juniperus communis?"),
    ("science", "What did modern studies test for Origanum vulgare?"),
]

page_header("forum", "Assistant", "Ask the librarian",
            "Ask in English or Albanian. Answers come only from this project's fact sheets (study records, "
            "reviewed papers, PubMed candidates and safety rules), and every claim links to its source.")

if not DB_PATH.exists():
    st.error("No database yet. Run `make build` first, then reopen this page.", icon=":material/database:")
    st.stop()
if not GROQ_API_KEY:
    st.warning("Set `GROQ_API_KEY` in `.env` to use the assistant (free key: https://console.groq.com/keys), "
               "then restart the app.", icon=":material/key:")
    st.stop()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # {"role", "content", "citations"}


def show_citations(citations):
    if not citations:
        return
    with st.expander(f"Sources ({len(citations)})", icon=":material/link:"):
        for c in citations:
            link = f" · [open]({c['url']})" if c.get("url") else ""
            st.markdown(f":green-badge[{c['id']}] {c['label']}{link}")


def ask(question: str) -> None:
    st.session_state.pending_question = question


with st.sidebar:
    st.markdown("**Try asking**")
    for icon, question in EXAMPLES:
        st.button(question, icon=f":material/{icon}:", width="stretch", on_click=ask, args=(question,),
                  key=f"side-{question}")
    st.write("")
    if st.button("Clear conversation", icon=":material/delete_sweep:", width="stretch", type="tertiary"):
        st.session_state.chat_history = []
        st.rerun()
    st.caption(f":material/memory: {GROQ_MODEL} via Groq")

if not st.session_state.chat_history and "pending_question" not in st.session_state:
    st.markdown("##### Start with one of these")
    cols = st.columns(2)
    for n, (icon, question) in enumerate(EXAMPLES):
        with cols[n % 2]:
            st.button(question, icon=f":material/{icon}:", width="stretch", on_click=ask, args=(question,),
                      key=f"card-{question}")
    st.caption(":material/info: Research prototype. The assistant never gives doses and is not medical advice.")

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"], avatar=AVATARS[msg["role"]]):
        st.markdown(msg["content"])
        show_citations(msg.get("citations"))

question = st.chat_input("Ask about a plant, its uses, studies or risks…")
question = question or st.session_state.pop("pending_question", None)

if question:
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history]
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user", avatar=AVATARS["user"]):
        st.markdown(question)
    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        with st.spinner("Reading the fact sheets…"):
            conn = connect()
            try:
                result = chat.answer(conn, question, history)
            except Exception as exc:  # noqa: BLE001
                result = None
                st.error(str(exc), icon=":material/error:")
            finally:
                conn.close()
        if result:
            st.markdown(result["answer"])
            show_citations(result["citations"])
            st.session_state.chat_history.append(
                {"role": "assistant", "content": result["answer"], "citations": result["citations"]})
    if result:
        st.rerun()  # hide the starter cards once the conversation has begun
