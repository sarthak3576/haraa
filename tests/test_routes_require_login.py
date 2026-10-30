"""
These routes all check request.session before touching AWS, so an
unauthenticated request redirects to /login without any network/AWS call --
safe to run offline, with no credentials required.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, follow_redirects=False)

PROTECTED_GET_ROUTES = [
    "/home",
    "/learn",
    "/nptel",
    "/news",
    "/dashboard",
    "/dashboard/export.csv",
    "/calculator",
    "/upload",
    "/disposal-guide",
    "/where-does-it-go",
    "/nearby-centres",
    "/my-scans",
    "/waste-audit",
    "/segregation-game",
    "/collection-reminders",
    "/collection-reminders/calendar.ics",
    "/composting-guide",
    "/poster",
    "/weekly-report",
    "/chat",
    "/model-performance",
    "/about",
]


@pytest.mark.parametrize("path", PROTECTED_GET_ROUTES)
def test_redirects_to_login_when_not_authenticated(path):
    response = client.get(path)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_root_redirects_to_login_when_not_authenticated():
    response = client.get("/")
    assert response.status_code == 307
    assert response.headers["location"] == "/login"


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_page_renders():
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Log in" in response.content


def test_register_page_renders():
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Create an account" in response.content


def test_chat_api_requires_auth():
    response = client.post("/api/chat", json={"message": "hi"})
    assert response.status_code == 401


def test_chatbot_health_requires_auth():
    response = client.get("/api/chatbot/health")
    assert response.status_code == 401


def test_chat_clear_requires_auth():
    response = client.post("/api/chat/clear")
    assert response.status_code == 401


def test_dashboard_goal_requires_auth():
    response = client.post("/dashboard/goal", data={"target_items": "5"})
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_my_scans_log_requires_auth():
    response = client.post("/my-scans/log", data={"scan_id": "x", "weight_kg": "0.5"})
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_segregation_game_score_requires_auth():
    response = client.post("/api/segregation-game/score", json={"score": 10})
    assert response.status_code == 401


def test_learn_quiz_api_requires_auth():
    response = client.post("/api/learn/quiz", json={"section_id": "types", "answers": [0, 0, 0]})
    assert response.status_code == 401


def test_calculator_api_requires_auth():
    response = client.post("/api/calculator", json={"amounts_kg": {"plastic": 1.0}})
    assert response.status_code == 401
