from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models import AuditLog, Restaurant


@pytest.fixture()
def client_and_session(tmp_path):
    db_file = tmp_path / "test_reports.db"
    database_url = f"sqlite:///{db_file}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False}, future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        db.add(Restaurant(name="Reportable Place", certification_score=0.8, community_verification_score=0.8, recency_score=0.8))
        db.commit()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client, TestingSessionLocal
    app.dependency_overrides.clear()


def _register_and_token(client: TestClient) -> str:
    response = client.post(
        "/auth/register",
        json={"email": "reporter@example.com", "display_name": "Reporter", "password": "StrongPass123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_report_submission_and_audit_log(client_and_session):
    client, SessionLocal = client_and_session
    token = _register_and_token(client)

    response = client.post(
        "/restaurants/1/reports",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "report_type": "allergen_risk",
            "description": "Menu now includes unlisted peanuts.",
            "evidence_url": "pending-upload://photo-1",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["report_type"] == "allergen_risk"
    assert payload["status"] == "open"

    with SessionLocal() as db:
        audit = db.scalars(select(AuditLog).where(AuditLog.entity_type == "report").order_by(AuditLog.id.desc())).first()
        assert audit is not None
        assert audit.action == "created"
        metadata = json.loads(audit.metadata_json or "{}")
        assert metadata["report_type"] == "allergen_risk"


def test_report_type_validation(client_and_session):
    client, _ = client_and_session
    token = _register_and_token(client)

    response = client.post(
        "/restaurants/1/reports",
        headers={"Authorization": f"Bearer {token}"},
        json={"report_type": "not_a_real_type"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"


def test_report_rate_limit_enforced(client_and_session):
    client, _ = client_and_session
    token = _register_and_token(client)

    last_response = None
    for idx in range(31):
        last_response = client.post(
            "/restaurants/1/reports",
            headers={"Authorization": f"Bearer {token}"},
            json={"report_type": "other", "description": f"bulk-{idx}"},
        )

    assert last_response is not None
    assert last_response.status_code == 429
    assert last_response.json()["error"]["code"] == "http_error"


def test_report_requires_auth(client_and_session):
    client, _ = client_and_session
    response = client.post("/restaurants/1/reports", json={"report_type": "outdated_info"})
    assert response.status_code == 401
