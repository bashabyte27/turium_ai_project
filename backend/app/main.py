import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.errors import add_error_handlers
from app.logger import log, setup_logging
from app.routers import ingest, items, query

setup_logging()


@asynccontextmanager
async def lifespan(app):
    create_tables()
    log("app_started")
    yield


app = FastAPI(title="AI Knowledge Inbox", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = uuid.uuid4().hex[:8]
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    log(
        "request",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        ms=round((time.perf_counter() - started) * 1000),
    )
    return response


add_error_handlers(app)
app.include_router(ingest.router)
app.include_router(items.router)
app.include_router(query.router)


@app.get("/health")
def health():
    return {"status": "ok"}
