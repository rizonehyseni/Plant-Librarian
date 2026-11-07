"""SQLite schema. One row per traditional use record; everything else hangs off the species."""
import sqlite3

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    doc_id TEXT PRIMARY KEY, title TEXT, citation TEXT, url TEXT, licence TEXT,
    study_area TEXT          -- fallback place for records that name no village
);
CREATE TABLE IF NOT EXISTS uses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT REFERENCES sources(doc_id),
    page INTEGER,
    local_name TEXT,
    name_in_text TEXT,
    community TEXT,
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
    place TEXT,              -- gazetteer place the location resolved to
    lat REAL,
    lon REAL,
    geo_precision TEXT,      -- record | study | NULL (not on the map)
    quote TEXT,
    review_status TEXT NOT NULL DEFAULT 'Needs Review',
    reviewer_note TEXT,
    record_origin TEXT NOT NULL DEFAULT 'AI Extracted',
    auto_check TEXT,         -- passed | issues | no page (automatic PDF check, not a human review)
    auto_check_detail TEXT
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
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id INTEGER NOT NULL REFERENCES uses(id),
    changed_field TEXT,
    previous_value TEXT,
    new_value TEXT,
    timestamp TEXT NOT NULL,
    action TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    reviewer_note TEXT
);
"""


def connect(path=DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    initialize(conn)
    return conn


def initialize(conn: sqlite3.Connection) -> None:
    """Create dashboard tables and safely migrate a database from older versions."""
    conn.executescript(SCHEMA)
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(uses)")}
    additions = {
        "community": "TEXT",
        "review_status": "TEXT NOT NULL DEFAULT 'Needs Review'",
        "reviewer_note": "TEXT",
        "record_origin": "TEXT NOT NULL DEFAULT 'AI Extracted'",
        "auto_check": "TEXT",
        "auto_check_detail": "TEXT",
    }
    for column, definition in additions.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE uses ADD COLUMN {column} {definition}")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_uses_review_status ON uses(review_status)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_record_id ON audit_log(record_id)")
    conn.commit()


def reset(path=DB_PATH) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    return connect(path)
