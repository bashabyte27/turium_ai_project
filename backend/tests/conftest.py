import os
import tempfile

# These must be set before the app is imported, because settings are read at import time.
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["EMBEDDING_PROVIDER"] = "hash"
os.environ["LLM_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:  # the "with" runs startup, which creates the tables
        # start every test with an empty database
        with get_db() as db:
            db.execute("DELETE FROM chunks")
            db.execute("DELETE FROM items")
        yield test_client
