from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, model_validator


class IngestRequest(BaseModel):
    type: Literal["note", "url"]
    content: Optional[str] = None  # needed for notes
    url: Optional[HttpUrl] = None  # needed for urls
    title: Optional[str] = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def check_fields(self):
        if self.type == "note" and not (self.content and self.content.strip()):
            raise ValueError("A note needs non-empty 'content'.")
        if self.type == "url" and self.url is None:
            raise ValueError("A url item needs 'url'.")
        return self


class IngestResponse(BaseModel):
    id: str
    status: str


class Item(BaseModel):
    id: str
    source_type: str
    title: str
    source_url: Optional[str]
    status: str
    error: Optional[str]
    created_at: datetime
    preview: str
    chunk_count: int


class ItemsResponse(BaseModel):
    items: list[Item]


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    top_k: Optional[int] = Field(default=None, ge=1, le=20)


class Source(BaseModel):
    number: int  # matches the [1], [2] citations in the answer
    item_id: str
    title: str
    source_url: Optional[str]
    snippet: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    mode: Literal["llm", "extractive", "none"]
    sources: list[Source]
