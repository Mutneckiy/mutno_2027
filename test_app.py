from datetime import date, timedelta
from xml.etree import ElementTree

import pytest
from fastapi.testclient import TestClient

from app_final import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def profile():
    return {"full_name": "Андрей", "birth_date": "1987-10-06", "wish": "Создать свой проект", "answers": {"direction": 0, "change": 1, "resource": 2, "element": 3, "step": 0}}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "mode": "template"}


def test_version_uses_environment(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "test-version")
    with TestClient(create_app()) as client:
        assert client.get("/version").json() == {"version": "test-version"}


def test_home_and_assets(client):
    response = client.get("/")
    assert response.status_code == 200
    assert 'id="profile-form"' in response.text
    for asset in ["app.js", "style.css", "mark.svg"]:
        assert client.get(f"/static/{asset}").status_code == 200


def test_five_questions(client):
    questions = client.get("/api/questions").json()["questions"]
    assert len(questions) == 5
    assert len({q["id"] for q in questions}) == 5
    assert all(len(q["options"]) == 4 for q in questions)


def test_talisman_catalog(client):
    assert len(client.get("/api/talismans").json()["talismans"]) == 4


def test_prediction_personalization_and_valid_svg(client, profile):
    response = client.post("/api/predictions", json=profile)
    assert response.status_code == 200
    prediction = response.json()
    assert profile["full_name"] in prediction["intro"]
    assert profile["wish"] in prediction["chapters"][0]["text"]
    assert len(prediction["chapters"]) == 3
    assert prediction["year"] == 2027
    assert ElementTree.fromstring(prediction["svg"]).tag == "{http://www.w3.org/2000/svg}svg"
    assert response.headers["cache-control"] == "no-store"


def test_same_input_is_reproducible(client, profile):
    assert client.post("/api/predictions", json=profile).json() == client.post("/api/predictions", json=profile).json()


def test_answers_change_message(client, profile):
    first = client.post("/api/predictions", json=profile).json()
    profile["answers"]["resource"] = 0
    second = client.post("/api/predictions", json=profile).json()
    assert first["chapters"][1] != second["chapters"][1]


@pytest.mark.parametrize("invalid", [{}, {"direction": 0}, {"direction": True, "change": 0, "resource": 0, "element": 0, "step": 0}, {"direction": 4, "change": 0, "resource": 0, "element": 0, "step": 0}])
def test_invalid_answers(client, profile, invalid):
    profile["answers"] = invalid
    assert client.post("/api/predictions", json=profile).status_code == 422


@pytest.mark.parametrize("field,value", [("full_name", "   "), ("wish", "x"), ("wish", "x" * 601), ("birth_date", "1899-12-31"), ("birth_date", (date.today() + timedelta(days=1)).isoformat())])
def test_invalid_fields(client, profile, field, value):
    profile[field] = value
    assert client.post("/api/predictions", json=profile).status_code == 422


def test_svg_download(client, profile):
    response = client.post("/api/talisman.svg", json=profile)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert "attachment" in response.headers["content-disposition"]
    assert "<script" not in response.text
    assert profile["full_name"] not in response.text
    ElementTree.fromstring(response.text)


def test_personal_data_is_not_logged(client, profile, caplog):
    with caplog.at_level("INFO", logger="mutno"):
        client.post("/api/predictions", json=profile)
    assert "status=200" in caplog.text
    for value in [profile["full_name"], profile["wish"], profile["birth_date"]]:
        assert value not in caplog.text
