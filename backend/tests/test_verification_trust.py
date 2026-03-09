from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models import OwnerClaim, Restaurant, User


@pytest.fixture()
def client_and_session(tmp_path):
    db_file = tmp_path / "test_verification_trust.db"
    database_url = f"sqlite:///{db_file}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False}, future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        db.add(
            Restaurant(
                name="Trust Place",
                certification_score=0.8,
                community_verification_score=0.7,
                recency_score=0.8,
            )
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
    yield test_client, TestingSessionLocal
    app.dependency_overrides.clear()


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/auth/register",
        json={"email": email, "display_name": email.split("@")[0], "password": "StrongPass123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _set_role(SessionLocal, email: str, role: str):
    with SessionLocal() as db:
        user = db.scalars(select(User).where(User.email == email)).first()
        assert user is not None
        user.role = role
        db.commit()


def test_verification_and_contradiction_impact_trust_score(client_and_session):
    client, SessionLocal = client_and_session

    owner_token = _register(client, "ownertrust@example.com")
    admin_token = _register(client, "admintrust@example.com")
    reporter_token = _register(client, "reportertrust@example.com")
    _set_role(SessionLocal, "admintrust@example.com", "admin")

    base_detail = client.get("/restaurants/1")
    assert base_detail.status_code == 200
    base_score = base_detail.json()["trust_breakdown"]["final_score"]

    claim_resp = client.post(
        "/restaurants/1/claims",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"notes": "I own this listing"},
    )
    assert claim_resp.status_code == 200

    with SessionLocal() as db:
        claim = db.scalars(select(OwnerClaim).where(OwnerClaim.restaurant_id == 1)).first()
        assert claim is not None
        claim_id = claim.id

    doc_resp = client.post(
        f"/owner/claims/{claim_id}/verification-documents",
        headers={"Authorization": f"Bearer {owner_token}"},
        files={
            "document_type": (None, "business_license"),
            "notes": (None, "Submitted for verification"),
            "metadata_filename": (None, "license.pdf"),
            "metadata_mime_type": (None, "application/pdf"),
        },
    )
    assert doc_resp.status_code == 200
    doc_id = doc_resp.json()["id"]

    after_submit_detail = client.get("/restaurants/1")
    assert after_submit_detail.status_code == 200
    after_submit_score = after_submit_detail.json()["trust_breakdown"]["final_score"]
    assert after_submit_score >= base_score

    approve_resp = client.patch(
        f"/moderation/verification-documents/{doc_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "approved", "note": "Docs valid"},
    )
    assert approve_resp.status_code == 200

    after_approve_detail = client.get("/restaurants/1")
    assert after_approve_detail.status_code == 200
    after_approve_score = after_approve_detail.json()["trust_breakdown"]["final_score"]
    assert after_approve_score >= after_submit_score

    contradiction = client.post(
        "/restaurants/1/reports",
        headers={"Authorization": f"Bearer {reporter_token}"},
        json={"report_type": "inaccurate_halal_status", "description": "Potential contradiction"},
    )
    assert contradiction.status_code == 200

    after_contradiction_detail = client.get("/restaurants/1")
    assert after_contradiction_detail.status_code == 200
    after_contradiction_score = after_contradiction_detail.json()["trust_breakdown"]["final_score"]
    assert after_contradiction_score < after_approve_score

    trust_events = client.get("/restaurants/1/trust-events")
    assert trust_events.status_code == 200
    assert len(trust_events.json()["events"]) >= 3
