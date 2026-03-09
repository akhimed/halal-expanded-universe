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
    db_file = tmp_path / "test_smoke_e2e.db"
    database_url = f"sqlite:///{db_file}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False}, future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        db.add(Restaurant(name="Smoke Test Bistro", certification_score=0.8, community_verification_score=0.7, recency_score=0.9))
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


def test_smoke_user_journey(client: TestClient):
    health = client.get("/health")
    assert health.status_code == 200

    register = client.post(
        "/auth/register",
        json={"email": "smoke@example.com", "display_name": "Smoke User", "password": "StrongPass123"},
    )
    assert register.status_code == 200
    token = register.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200

    search = client.post(
        "/search",
        json={"required_tags": [], "excluded_allergens": [], "profile": "balanced"},
    )
    assert search.status_code == 200

    report = client.post(
        "/restaurants/1/reports",
        headers={"Authorization": f"Bearer {token}"},
        json={"report_type": "outdated_info", "description": "smoke check"},
    )
    assert report.status_code == 200
