import logging

from app import embedder
from app.config import settings
from app.errors import AppError
from app.logger import log
from app.repositories import chunks as chunks_repo
from app.repositories import items as items_repo
from app.services.chunking import chunk_text
from app.services import fetcher


def create_item(request):
    """Save a new item as 'pending' and return its id. This part is fast."""
    if request.type == "note":
        content = request.content.strip()
        if len(content) > settings.max_note_chars:
            raise AppError(
                422, "validation_error",
                f"The note is too long ({len(content)} characters, the limit is {settings.max_note_chars}).",
            )
        title = request.title or content[:60].replace("\n", " ")
        return items_repo.add_item("note", title, None, content)

    url = str(request.url)
    return items_repo.add_item("url", request.title or url, url, None)


def process_item(item_id):
    """Fetch the page (for URLs), split it, embed it and store it. Runs in the background.

    This never raises. If something goes wrong the item is marked 'failed' with the reason.
    """
    item = items_repo.get_item(item_id)
    if item is None:
        log("ingest_item_not_found", logging.WARNING, item_id=item_id)
        return

    log("ingest_started", item_id=item_id, source_type=item["source_type"])
    try:
        title = item["title"]
        text = item["raw_content"]

        if item["source_type"] == "url":
            page_title, text = fetcher.fetch_page(item["source_url"])
            if title == item["source_url"]:  # the user didn't give a custom title
                title = page_title

        pieces = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        vectors = embedder.embed(pieces)
        chunks_repo.save_chunks(item_id, pieces, vectors, embedder.model_name())
        items_repo.mark_ready(item_id, title, text)
        log("ingest_done", item_id=item_id, chunks=len(pieces))

    except fetcher.FetchError as error:
        log("ingest_failed", logging.WARNING, item_id=item_id, reason=str(error))
        items_repo.mark_failed(item_id, str(error))
    except Exception as error:
        log("ingest_crashed", logging.ERROR, item_id=item_id, error=repr(error))
        items_repo.mark_failed(item_id, "Something went wrong while processing this item.")
