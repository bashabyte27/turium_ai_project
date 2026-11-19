import numpy as np

from app.database import get_db


def save_chunks(item_id, texts, vectors, model):
    """Replace all chunks of an item with the new ones."""
    rows = [
        (item_id, position, text, model, vector.astype(np.float32).tobytes())
        for position, (text, vector) in enumerate(zip(texts, vectors))
    ]
    with get_db() as db:
        db.execute("DELETE FROM chunks WHERE item_id = ?", (item_id,))
        db.executemany(
            "INSERT INTO chunks (item_id, position, text, model, embedding) VALUES (?, ?, ?, ?, ?)",
            rows,
        )


def load_chunks(model):
    """Return (chunk info list, matrix of vectors) for every ready item.

    Only chunks made with the same embedding model are used, because vectors
    from different models cannot be compared.
    """
    with get_db() as db:
        rows = db.execute(
            "SELECT chunks.item_id, chunks.text, chunks.embedding, items.title, items.source_url"
            " FROM chunks JOIN items ON items.id = chunks.item_id"
            " WHERE items.status = 'ready' AND chunks.model = ?",
            (model,),
        ).fetchall()
    if not rows:
        return [], None
    vectors = np.vstack([np.frombuffer(row["embedding"], dtype=np.float32) for row in rows])
    chunks = [
        {
            "item_id": row["item_id"],
            "text": row["text"],
            "title": row["title"],
            "source_url": row["source_url"],
        }
        for row in rows
    ]
    return chunks, vectors
