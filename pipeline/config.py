"""Paths and settings shared by every pipeline step."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _load_streamlit_secrets() -> None:
    """On Streamlit Community Cloud keys live in st.secrets; copy plain string values into the environment.

    Values already in the environment (or .env) win. Does nothing when there is no secrets.toml.
    """
    try:
        import streamlit as st
        for name, value in st.secrets.to_dict().items():
            if isinstance(value, str) and value and not os.getenv(name):
                os.environ[name] = value.strip()
    except Exception:  # no streamlit, no secrets file, or a broken one: fall back to .env only
        pass


_load_streamlit_secrets()

DATA = ROOT / "data"
RAW = DATA / "raw"              # study PDFs / text files go here
INTERIM = DATA / "interim"      # extracted page text (rebuildable, not committed)
SEED = DATA / "seed"            # hand-curated dictionaries and rules
CACHE = DATA / "cache"          # LLM + API responses, committed so builds are reproducible offline
DB_PATH = DATA / "ethnohack.db"

MODEL = os.getenv("ETHNO_MODEL", "claude-opus-5-5")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
NCBI_EMAIL = os.getenv("NCBI_EMAIL", "")
IUCN_TOKEN = os.getenv("IUCN_TOKEN", "")
# Chat assistant (app page "Ask the librarian"); free key at https://console.groq.com/keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# Set OFFLINE=1 to use only cached responses (e.g. during the live demo).
OFFLINE = os.getenv("OFFLINE", "0") == "1"
