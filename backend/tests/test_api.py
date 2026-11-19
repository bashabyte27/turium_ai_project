from app.services import fetcher


def add_note(client, content):
    response = client.post("/ingest", json={"type": "note", "content": content})
    assert response.status_code == 202
    return response.json()["id"]


def test_note_is_saved_and_becomes_ready(client):
    item_id = add_note(client, "The office wifi password is stored in the blue notebook.")
    items = client.get("/items").json()["items"]
    item = next(i for i in items if i["id"] == item_id)
    assert item["status"] == "ready"
    assert item["source_type"] == "note"
    assert item["chunk_count"] >= 1


def test_question_returns_answer_with_sources(client):
    add_note(client, "Our deployment happens every Friday at 4pm using the release script.")
    add_note(client, "Bananas are rich in potassium and grow in tropical climates.")

    response = client.post("/query", json={"question": "When does deployment happen?"})
    assert response.status_code == 200
    body = response.json()
    assert body["sources"]
    assert "deployment" in body["sources"][0]["snippet"].lower()
    assert "[1]" in body["answer"] or "[2]" in body["answer"]


def test_note_without_content_is_rejected(client):
    response = client.post("/ingest", json={"type": "note"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_url_item_needs_a_valid_url(client):
    response = client.post("/ingest", json={"type": "url", "url": "not a url"})
    assert response.status_code == 422


def test_short_question_is_rejected(client):
    response = client.post("/query", json={"question": "hi"})
    assert response.status_code == 422


def test_failed_url_is_marked_failed_with_reason(client, monkeypatch):
    def broken_fetch(url):
        raise fetcher.FetchError("The site answered with HTTP 404.")

    monkeypatch.setattr(fetcher, "fetch_page", broken_fetch)
    response = client.post("/ingest", json={"type": "url", "url": "https://example.com/missing"})
    item_id = response.json()["id"]

    item = next(i for i in client.get("/items").json()["items"] if i["id"] == item_id)
    assert item["status"] == "failed"
    assert "404" in item["error"]


def test_url_is_fetched_and_searchable(client, monkeypatch):
    monkeypatch.setattr(
        fetcher, "fetch_page",
        lambda url: ("Rust Guide", "Rust uses ownership and borrowing to guarantee memory safety."),
    )
    client.post("/ingest", json={"type": "url", "url": "https://example.com/rust"})
    body = client.post("/query", json={"question": "How does Rust guarantee memory safety?"}).json()
    assert body["sources"][0]["title"] == "Rust Guide"
    assert body["sources"][0]["source_url"] == "https://example.com/rust"


def test_private_addresses_are_blocked():
    try:
        fetcher.check_not_private("http://127.0.0.1:8000/secret")
        assert False, "should have been blocked"
    except fetcher.FetchError:
        pass


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
