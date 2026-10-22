import json

import httpx
import pytest
from fastapi.testclient import TestClient

import llm
from app_final import Profile, QUESTIONS, create_app, personalize


@pytest.fixture
def profile():
    return Profile(full_name="Test", birth_date="1987-10-06", wish="New project",
                   answers=dict(direction=0, change=1, resource=2, element=3, step=0))


@pytest.fixture(autouse=True)
def enable_llm(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")


def completion(content, finish="stop"):
    return {"choices": [{"finish_reason": finish, "message": {"content": content}}]}


def valid_message():
    return {"title": "2027", "intro": "A personal message", "chapters": [
        {"title": str(i), "text": "A small step"} for i in range(3)
    ]}


def test_llm_endpoint_preserves_talisman_and_download(monkeypatch, profile):
    captured = []

    def fetch(payload):
        captured.append(payload)
        return completion(json.dumps(valid_message()))

    monkeypatch.setattr(llm, "_fetch_completion", fetch)
    with TestClient(create_app()) as client:
        response = client.post("/api/predictions", json=profile.model_dump(mode="json"))
        result = response.json()
        assert response.status_code == 200
        assert result["mode"] == "llm"
        assert result["intro"] == "A personal message"
        assert result["talisman"] == personalize(profile)["talisman"]
        svg = client.post("/api/talisman.svg", json=profile.model_dump(mode="json"))
        assert svg.text == result["svg"]
    assert len(captured) == 1
    sent = json.loads(captured[0]["messages"][1]["content"])
    assert sent["answers"][0]["answer"] == QUESTIONS[0]["options"][0]
    assert len(sent["answers"]) == 5
    assert sent["symbolic_profile"]["western"]["sign"] == "Весы"
    assert sent["symbolic_profile"]["chinese"]["animal"] == "Кролик"
    assert result["symbolic_profile"] == sent["symbolic_profile"]
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("bad", [
    {}, completion("not json"), completion("{}"), completion("{}", "length"),
    completion(json.dumps({**valid_message(), "chapters": []})),
    completion(json.dumps({**valid_message(), "svg": "<script/>"})),
])
def test_invalid_response_falls_back(monkeypatch, profile, bad):
    monkeypatch.setattr(llm, "_fetch_completion", lambda payload: bad)
    baseline = personalize(profile)
    assert llm.enrich(profile, QUESTIONS, baseline) == baseline


def test_timeout_falls_back_without_logging_private_data(monkeypatch, profile, caplog):
    def fail(payload):
        raise httpx.ReadTimeout(profile.full_name + profile.wish)

    monkeypatch.setattr(llm, "_fetch_completion", fail)
    baseline = personalize(profile)
    assert llm.enrich(profile, QUESTIONS, baseline) == baseline
    assert profile.full_name not in caplog.text
    assert profile.wish not in caplog.text
    # A failed request must release the generation slot.
    monkeypatch.setattr(llm, "_fetch_completion", lambda payload: completion(json.dumps(valid_message())))
    assert llm.enrich(profile, QUESTIONS, baseline)["mode"] == "llm"


def test_busy_and_disabled_do_not_call_model(monkeypatch, profile):
    def unexpected(payload):
        pytest.fail("Model must not be called")

    monkeypatch.setattr(llm, "_fetch_completion", unexpected)
    baseline = personalize(profile)
    assert llm._slot.acquire(blocking=False)
    try:
        assert llm.enrich(profile, QUESTIONS, baseline) == baseline
    finally:
        llm._slot.release()
    monkeypatch.setenv("LLM_ENABLED", "false")
    assert llm.enrich(profile, QUESTIONS, baseline) == baseline
