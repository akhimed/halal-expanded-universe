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
    db_file = tmp_path / "test_owner_claims.db"
    database_url = f"sqlite:///{db_file}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False}, future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        db.add(Restaurant(name="Claimable Listing", certification_score=0.9, community_verification_score=0.8, recency_score=0.7))
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
        json={"email": "owner-flow@example.com", "display_name": "Owner Flow", "password": "StrongPass123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_submit_claim_records_audit_and_pending_status(client_and_session):
    client, SessionLocal = client_and_session
    token = _register_and_token(client)

    response = client.post(
        "/restaurants/1/claims",
        headers={"Authorization": f"Bearer {token}"},
        json={"notes": "I own this location and can provide documents."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["restaurant_id"] == 1

    with SessionLocal() as db:
        audit = db.scalars(select(AuditLog).where(AuditLog.entity_type == "owner_claim").order_by(AuditLog.id.desc())).first()
        assert audit is not None
        assert audit.action == "submitted"
        metadata = json.loads(audit.metadata_json or "{}")
        assert metadata["restaurant_id"] == 1
        assert metadata["status"] == "pending"


def test_duplicate_claim_is_rejected(client_and_session):
    client, _ = client_and_session
    token = _register_and_token(client)

    first = client.post(
        "/restaurants/1/claims",
        headers={"Authorization": f"Bearer {token}"},
        json={"notes": "first"},
    )
    assert first.status_code == 200

    second = client.post(
        "/restaurants/1/claims",
        headers={"Authorization": f"Bearer {token}"},
        json={"notes": "second"},
    )
    assert second.status_code == 400


def test_owner_dashboard_lists_claims(client_and_session):
    client, _ = client_and_session
    token = _register_and_token(client)

    submit = client.post(
        "/restaurants/1/claims",
        headers={"Authorization": f"Bearer {token}"},
        json={"notes": "claim note"},
    )
    assert submit.status_code == 200

    dashboard = client.get("/owner/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert dashboard.status_code == 200
    payload = dashboard.json()
    assert len(payload["claims"]) == 1
    assert payload["claims"][0]["status"] == "pending"
    assert payload["claims"][0]["restaurant"]["name"] == "Claimable Listing"
    assert "trust_score" in payload["claims"][0]
    assert payload["claims"][0]["evidence_status"]["pending"] >= 0
    assert isinstance(payload["claims"][0]["pending_moderation_items"], list)
    assert payload["pending_moderation_total"] >= 1


def test_owner_can_submit_certification_evidence(client_and_session):
    client, _ = client_and_session
    token = _register_and_token(client)

    submit = client.post(
        "/restaurants/1/claims",
        headers={"Authorization": f"Bearer {token}"},
        json={"notes": "claim note"},
    )
    assert submit.status_code == 200
    claim_id = submit.json()["id"]

    evidence = client.post(
        f"/owner/claims/{claim_id}/certification-evidence",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "certification_type": (None, "halal"),
            "notes": (None, "Current cert attached"),
            "file": ("halal-cert.pdf", b"dummy-pdf", "application/pdf"),
        },
    )

    assert evidence.status_code == 200
    payload = evidence.json()
    assert payload["document_type"] == "halal_certificate"
    assert payload["status"] == "pending"
