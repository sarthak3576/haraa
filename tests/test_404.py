from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, follow_redirects=False)


def test_unknown_path_returns_friendly_404():
    response = client.get("/this-page-does-not-exist")
    assert response.status_code == 404
    assert b"We couldn't find that page" in response.content
