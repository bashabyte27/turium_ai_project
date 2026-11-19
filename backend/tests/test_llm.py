import os

import httpx
import pytest

from app import llm
from app.config import settings
from app.errors import AppError


class FakeResponse:
    """Looks like the response we get back from the Gemini / OpenAI chat API."""

    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error", request=httpx.Request("POST", "http://test"), response=httpx.Response(self.status_code)
            )

    def json(self):
        return self.data


def good_reply(text):
    return FakeResponse({"choices": [{"message": {"content": text}}]})


def add_note(client, content):
    assert client.post("/ingest", json={"type": "note", "content": content}).status_code == 202


@pytest.fixture
def gemini_on(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_api_key", "")


def test_llm_is_off_without_any_key():
    assert llm.llm_is_configured() is False


def test_llm_is_on_when_gemini_key_is_set(gemini_on):
    assert llm.llm_is_configured() is True


def test_gemini_request_uses_gemini_url_model_and_key(gemini_on, monkeypatch):
    seen = {}

    def fake_post(url, json, headers, timeout):
        seen.update(url=url, model=json["model"], auth=headers["Authorization"], prompt=json["messages"][1]["content"])
        return good_reply("  Friday [1]  ")

    monkeypatch.setattr(httpx, "post", fake_post)
    answer = llm.ask_llm("When do we deploy?", ["We deploy on Friday."])

    assert answer == "Friday [1]"
    assert seen["url"] == settings.gemini_base_url + "/chat/completions"
    assert seen["model"] == settings.gemini_model
    assert seen["auth"] == "Bearer test-key"
    assert "[1] We deploy on Friday." in seen["prompt"]


def test_llm_api_key_wins_over_gemini_key(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "gemini-key")
    monkeypatch.setattr(settings, "llm_api_key", "other-key")
    seen = {}

    def fake_post(url, json, headers, timeout):
        seen.update(url=url, auth=headers["Authorization"])
        return good_reply("ok")

    monkeypatch.setattr(httpx, "post", fake_post)
    llm.ask_llm("question?", ["some text"])

    assert seen["url"].startswith(settings.llm_base_url)
    assert seen["auth"] == "Bearer other-key"


def test_bad_reply_from_llm_raises_app_error(gemini_on, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: FakeResponse({"unexpected": True}))
    with pytest.raises(AppError) as error:
        llm.ask_llm("question?", ["some text"])
    assert error.value.status_code == 502


def test_query_returns_llm_answer_in_llm_mode(client, gemini_on, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: good_reply("Deployment is on Friday at 4pm [1]."))
    add_note(client, "Our deployment happens every Friday at 4pm using the release script.")

    body = client.post("/query", json={"question": "When does deployment happen?"}).json()

    assert body["mode"] == "llm"
    assert body["answer"] == "Deployment is on Friday at 4pm [1]."
    assert body["sources"]


def test_query_falls_back_to_quoted_answer_when_llm_fails(client, gemini_on, monkeypatch):
    def broken_post(*args, **kwargs):
        raise httpx.ConnectError("Gemini is down")

    monkeypatch.setattr(httpx, "post", broken_post)
    add_note(client, "Our deployment happens every Friday at 4pm using the release script.")

    response = client.post("/query", json={"question": "When does deployment happen?"})

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "extractive"
    assert "Friday" in body["answer"]


# This one calls the real Gemini API, so it is skipped unless you ask for it:
#   GEMINI_LIVE_KEY=your-key python -m pytest tests/test_llm.py -k live
@pytest.mark.skipif(not os.environ.get("GEMINI_LIVE_KEY"), reason="set GEMINI_LIVE_KEY to run")
def test_live_gemini_answers_from_the_sources(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", os.environ["GEMINI_LIVE_KEY"])
    monkeypatch.setattr(settings, "llm_api_key", "")
    add_note(client, "Our team deploys to production every Friday afternoon. Rollbacks use the revert script.")
    add_note(client, "Bananas are rich in potassium and grow in tropical climates.")

    body = client.post("/query", json={"question": "When does the team deploy?"}).json()

    assert body["mode"] == "llm"
    assert "friday" in body["answer"].lower()
    assert "[1]" in body["answer"]
