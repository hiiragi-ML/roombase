from fastapi.testclient import TestClient

from app.main import app

def test_me_requires_login():
    with TestClient(app) as client:
        response = client.get("/api/auth/me")

    assert response.status_code == 401