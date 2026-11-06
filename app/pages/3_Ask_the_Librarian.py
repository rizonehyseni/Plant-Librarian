"""Chat assistant that answers only from the plant fact sheets, with sources."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pipeline import chat  # noqa: E402
from pipeline.config import DB_PATH, GROQ_API_KEY, GROQ_MODEL  # noqa: E402
from pipeline.db import connect  # noqa: E402

st.set_page_config(page_title="Ask the librarian · EthnoHack", page_icon="💬", layout="wide")
st.markdown(
    """
    <style>
      :root { --ethno-ink: #20352a; --ethno-green: #174c35; --ethno-leaf: #26734d; }
      html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main { background: #f1efe5 !important; }
      [data-testid="stHeader"] { background: transparent; }
      .block-container { max-width: 980px; padding-top: 1.5rem; padding-bottom: 6rem; }
      [data-testid="stAppViewContainer"] *, [data-testid="stMain"] * { color: var(--ethno-ink); }
      h1, h2, h3 { color: var(--ethno-green) !important; letter-spacing: -0.025em; }
      a, a:visited { color: var(--ethno-leaf) !important; }
      [data-testid="stChatMessage"] { background: #e4ebdf; border: 1px solid #c7d4c4; border-radius: 14px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("💬 Ask the librarian")
st.caption(
    "Answers come only from this project's fact sheets: the study records, reviewed papers, "
    "PubMed candidates and safety rules. Every claim links to its source. Research prototype, not medical advice."
)

if not DB_PATH.exists():
    st.error("No database yet. Run `make build` first, then reopen this page.")
    st.stop()
if not GROQ_API_KEY:
    st.warning("Set `GROQ_API_KEY` in `.env` to use the assistant (free key: https://console.groq.com/keys), then restart the app.")
    st.stop()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # {"role", "content", "citations"}


def show_citations(citations):
    if not citations:
        return
    with st.expander(f"Sources ({len(citations)})"):
        for c in citations:
            label = f"[{c['url']}]({c['url']})" if c.get("url") else ""
            st.markdown(f"**[{c['id']}]** {c['label']}  \n{label}")


with st.sidebar:
    st.header("Try asking")
    examples = [
        "Si përdoret Mullaga dhe a është testuar i njëjti çaj?",
        "Which plants were used for coughs?",
        "A ka rreziqe dëllinja?",
        "What did modern studies test for Origanum vulgare?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.pending_question = ex
    st.divider()
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
    st.caption(f"Model: {GROQ_MODEL} via Groq")

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        show_citations(msg.get("citations"))

question = st.chat_input("Ask about a plant, its uses, studies or risks…")
question = question or st.session_state.pop("pending_question", None)

if question:
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history]
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Reading the fact sheets…"):
            conn = connect()
            try:
                result = chat.answer(conn, question, history)
            except Exception as exc:  # noqa: BLE001
                result = None
                st.error(str(exc))
            finally:
                conn.close()
        if result:
            st.markdown(result["answer"])
            show_citations(result["citations"])
            st.session_state.chat_history.append(
                {"role": "assistant", "content": result["answer"], "citations": result["citations"]})
