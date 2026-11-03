"""SQLite schema. One row per traditional use record; everything else hangs off the species."""
import sqlite3

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    doc_id TEXT PRIMARY KEY, title TEXT, citation TEXT, url TEXT, licence TEXT
);
CREATE TABLE IF NOT EXISTS uses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT REFERENCES sources(doc_id),
    page INTEGER,
    local_name TEXT,
    name_in_text TEXT,
    species TEXT,            -- accepted scientific name after matching
    gbif_key INTEGER,
    match_method TEXT,       -- exact | fuzzy | gbif | unresolved
    match_score REAL,
    family TEXT,
    part_used TEXT,
    preparation TEXT,
    prep_class TEXT,         -- aqueous | ethanolic | essential_oil | other
    administration TEXT,
    use TEXT,
    location TEXT,
    quote TEXT
);
CREATE TABLE IF NOT EXISTS evidence (
    species TEXT, pmid TEXT, title TEXT, year TEXT, prep_class TEXT, study_type TEXT,
    PRIMARY KEY (species, pmid)
);
CREATE TABLE IF NOT EXISTS flags (
    species TEXT, kind TEXT, level TEXT, note TEXT, source TEXT
);
CREATE TABLE IF NOT EXISTS occurrences (
    species TEXT, lat REAL, lon REAL, year INTEGER
);
CREATE TABLE IF NOT EXISTS compounds (
    species TEXT, compound TEXT, smiles TEXT, logp REAL, water_soluble INTEGER
);
"""


def connect(path=DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def reset(path=DB_PATH) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    conn = connect(path)
    conn.executescript(SCHEMA)
    return conn
