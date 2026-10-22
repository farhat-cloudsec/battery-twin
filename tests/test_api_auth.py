import os

# These must be set before the app is imported, because the API reads them at startup.
os.environ["ADMIN_PASSWORD"] = "test-admin-password"
os.environ["JWT_SECRET"] = "test-secret"

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_is_public():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_latest_requires_token():
    response = client.get("/cells/cell1/latest")
    assert response.status_code == 401


def test_alerts_requires_token():
    response = client.get("/alerts")
    assert response.status_code == 401


def test_garbage_token_is_rejected():
    response = client.get(
        "/alerts", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


def test_login_with_wrong_password_is_rejected():
    response = client.post(
        "/auth/login", data={"username": "admin", "password": "wrong-password"}
    )
    assert response.status_code == 401


def test_login_with_correct_password_returns_token():
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "test-admin-password"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20