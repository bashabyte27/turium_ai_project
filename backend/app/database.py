import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import settings

TABLES = """
CREATE TABLE IF NOT EXISTS items (
    id          TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,      -- 'note' or 'url'
    title       TEXT NOT NULL,
    source_url  TEXT,
    raw_content TEXT,
    status      TEXT NOT NULL,      -- 'pending', 'ready' or 'failed'
    error       TEXT,
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id   TEXT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    position  INTEGER NOT NULL,
    text      TEXT NOT NULL,
    model     TEXT NOT NULL,        -- which embedding model made the vector
    embedding BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_item ON chunks(item_id);
"""


def create_tables():
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    with get_db() as db:
        db.executescript(TABLES)


@contextmanager
def get_db():
    # A new connection per operation keeps things simple and thread-safe.
    db = sqlite3.connect(settings.db_path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
        db.commit()
    finally:
        db.close()
