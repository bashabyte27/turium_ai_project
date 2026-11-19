from fastapi import APIRouter

from app.config import settings
from app.logger import log
from app.schemas import QueryRequest, QueryResponse
from app.services import answering, search

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    """Find the most relevant saved chunks and answer the question using them."""
    top_k = request.top_k or settings.top_k
    chunks = search.find_relevant_chunks(request.question.strip(), top_k)
    response = answering.build_answer(request.question.strip(), chunks)
    log("query_answered", chunks_found=len(chunks), mode=response.mode)
    return response
