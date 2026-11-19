from fastapi import APIRouter

from app.repositories import items as items_repo
from app.schemas import ItemsResponse

router = APIRouter()


@router.get("/items", response_model=ItemsResponse)
def get_items():
    """All saved items, newest first."""
    return ItemsResponse(items=items_repo.list_items())
