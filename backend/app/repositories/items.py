import uuid
from datetime import datetime, timezone

from app.database import get_db


def add_item(source_type, title, source_url, raw_content):
    item_id = uuid.uuid4().hex
    created_at = datetime.now(timezone.utc).isoformat()
    with get_db() as db:
        db.execute(
            "INSERT INTO items (id, source_type, title, source_url, raw_content, status, created_at)"
            " VALUES (?, ?, ?, ?, ?, 'pending', ?)",
            (item_id, source_type, title, source_url, raw_content, created_at),
        )
    return item_id


def get_item(item_id):
    with get_db() as db:
        row = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    return dict(row) if row else None


def list_items():
    """Newest first. Only a short preview of the content is returned."""
    with get_db() as db:
        rows = db.execute(
            "SELECT id, source_type, title, source_url, status, error, created_at,"
            " substr(coalesce(raw_content, ''), 1, 200) AS preview,"
            " (SELECT count(*) FROM chunks WHERE chunks.item_id = items.id) AS chunk_count"
            " FROM items ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def mark_ready(item_id, title, raw_content):
    with get_db() as db:
        db.execute(
            "UPDATE items SET status = 'ready', title = ?, raw_content = ?, error = NULL WHERE id = ?",
            (title, raw_content, item_id),
        )


def mark_failed(item_id, error):
    with get_db() as db:
        db.execute("UPDATE items SET status = 'failed', error = ? WHERE id = ?", (error, item_id))
