from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models import Restaurant


@pytest.fixture()
def client(tmp_path):
    db_file = tmp_path / "test_favorites.db"
    database_url = f"sqlite:///{db_file}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False}, future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        db.add_all(
            [
                Restaurant(name="A", certification_score=0.8, community_verification_score=0.8, recency_score=0.8),
                Restaurant(name="B", certification_score=0.8, community_verification_score=0.8, recency_score=0.8),
            ]
        )
        db.commit()

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


def _register_and_token(client: TestClient) -> str:
    response = client.post(
        "/auth/register",
        json={"email": "fav@example.com", "display_name": "Fav User", "password": "StrongPass123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_add_list_remove_favorite_flow(client: TestClient):
    token = _register_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    add = client.post("/favorites/1", headers=headers)
    assert add.status_code == 200
    assert add.json()["status"] == "saved"

    listed = client.get("/favorites", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["favorites"]) == 1
    assert listed.json()["favorites"][0]["id"] == 1

    remove = client.delete("/favorites/1", headers=headers)
    assert remove.status_code == 200
    assert remove.json()["status"] == "removed"

    listed_after = client.get("/favorites", headers=headers)
    assert listed_after.status_code == 200
    assert listed_after.json()["favorites"] == []


def test_favorites_requires_auth(client: TestClient):
    response = client.get("/favorites")
    assert response.status_code == 401


def test_adding_same_favorite_is_idempotent(client: TestClient):
    token = _register_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    first = client.post("/favorites/1", headers=headers)
    assert first.status_code == 200

    second = client.post("/favorites/1", headers=headers)
    assert second.status_code == 200

    listed = client.get("/favorites", headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["favorites"]] == [1]


def test_remove_missing_favorite_returns_404(client: TestClient):
    token = _register_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete("/favorites/2", headers=headers)
    assert response.status_code == 404
