from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app


@pytest.fixture()
def client(tmp_path):
    db_file = tmp_path / "test_auth.db"
    database_url = f"sqlite:///{db_file}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False}, future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_register_and_login_and_current_user(client: TestClient):
    reg = client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "display_name": "New User",
            "password": "MySecurePass1",
        },
    )
    assert reg.status_code == 200
    reg_payload = reg.json()
    assert reg_payload["user"]["role"] == "user"
    assert "access_token" in reg_payload

    login = client.post(
        "/auth/login",
        json={"email": "newuser@example.com", "password": "MySecurePass1"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "newuser@example.com"


def test_login_invalid_password(client: TestClient):
    client.post(
        "/auth/register",
        json={
            "email": "badpass@example.com",
            "display_name": "Bad Pass",
            "password": "MySecurePass1",
        },
    )

    response = client.post(
        "/auth/login",
        json={"email": "badpass@example.com", "password": "wrong-pass"},
    )
    assert response.status_code == 401


def test_current_user_requires_auth(client: TestClient):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_auth_rate_limit_enforced(client: TestClient):
    last_response = None
    for _ in range(21):
        last_response = client.post(
            "/auth/login",
            json={"email": "missing@example.com", "password": "wrong"},
        )

    assert last_response is not None
    assert last_response.status_code == 429
    assert last_response.json()["error"]["code"] == "http_error"
