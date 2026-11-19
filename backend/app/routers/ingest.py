from fastapi import APIRouter, BackgroundTasks

from app.schemas import IngestRequest, IngestResponse
from app.services import ingestion

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse, status_code=202)
def ingest(request: IngestRequest, background_tasks: BackgroundTasks):
    """Save a note or URL. Fetching and embedding happen in the background.

    Check GET /items to see the status change from 'pending' to 'ready' or 'failed'.
    """
    item_id = ingestion.create_item(request)
    background_tasks.add_task(ingestion.process_item, item_id)
    return IngestResponse(id=item_id, status="pending")
