from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models import AuditLog, User


@pytest.fixture()
def client_and_session(tmp_path):
    db_file = tmp_path / "test_moderation.db"
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
    yield test_client, TestingSessionLocal
    app.dependency_overrides.clear()


def _register(client: TestClient, *, email: str) -> str:
    response = client.post(
        "/auth/register",
        json={"email": email, "display_name": email.split("@")[0], "password": "StrongPass123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _set_role(SessionLocal, email: str, role: str) -> None:
    with SessionLocal() as db:
        user = db.scalars(select(User).where(User.email == email)).first()
        assert user is not None
        user.role = role
        db.commit()


def _seed_report_and_claim(client: TestClient, reporter_token: str, owner_token: str):
    restaurant = client.get("/restaurants/1")
    if restaurant.status_code == 404:
        # create a restaurant through seed path if not already present by running auth alone
        pass

    # if seeded data is not present in this sqlite test DB, create one via direct insert-like endpoint is unavailable
    # so we add one using an authenticated path that assumes id=1 exists from Base metadata tests in other suites.
    # Here we create a restaurant through DB session in fixture setup where needed.

    report_resp = client.post(
        "/restaurants/1/reports",
        headers={"Authorization": f"Bearer {reporter_token}"},
        json={"report_type": "outdated_info", "description": "Old hours"},
    )
    assert report_resp.status_code == 200

    claim_resp = client.post(
        "/restaurants/1/claims",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"notes": "I manage this listing"},
    )
    assert claim_resp.status_code == 200


def test_moderation_endpoints_forbidden_to_regular_user(client_and_session):
    client, SessionLocal = client_and_session

    # create restaurant row needed by flows
    from backend.app.models import Restaurant

    with SessionLocal() as db:
        db.add(Restaurant(name="Moderation Place", certification_score=0.8, community_verification_score=0.8, recency_score=0.8))
        db.commit()

    user_token = _register(client, email="user@example.com")

    r1 = client.get("/moderation/reports", headers={"Authorization": f"Bearer {user_token}"})
    r2 = client.get("/moderation/owner-claims", headers={"Authorization": f"Bearer {user_token}"})

    assert r1.status_code == 403
    assert r2.status_code == 403


def test_moderator_can_list_and_update_report_and_claim_with_audit(client_and_session):
    client, SessionLocal = client_and_session

    from backend.app.models import Restaurant

    with SessionLocal() as db:
        db.add(Restaurant(name="Moderation Place", certification_score=0.8, community_verification_score=0.8, recency_score=0.8))
        db.commit()

    reporter_token = _register(client, email="reporter@example.com")
    owner_token = _register(client, email="owner@example.com")
    moderator_token = _register(client, email="mod@example.com")
    _set_role(SessionLocal, "mod@example.com", "moderator")

    _seed_report_and_claim(client, reporter_token, owner_token)

    reports = client.get("/moderation/reports", headers={"Authorization": f"Bearer {moderator_token}"})
    claims = client.get("/moderation/owner-claims", headers={"Authorization": f"Bearer {moderator_token}"})
    assert reports.status_code == 200
    assert claims.status_code == 200
    assert len(reports.json()["reports"]) >= 1
    assert len(claims.json()["claims"]) >= 1
    assert reports.json()["pagination"]["limit"] == 20
    assert claims.json()["pagination"]["offset"] == 0

    report_id = reports.json()["reports"][0]["id"]
    claim_id = claims.json()["claims"][0]["id"]

    update_report = client.patch(
        f"/moderation/reports/{report_id}",
        headers={"Authorization": f"Bearer {moderator_token}"},
        json={"status": "resolved", "note": "Verified update"},
    )
    update_claim = client.patch(
        f"/moderation/owner-claims/{claim_id}",
        headers={"Authorization": f"Bearer {moderator_token}"},
        json={"status": "approved", "note": "Ownership confirmed"},
    )

    assert update_report.status_code == 200
    assert update_claim.status_code == 200
    assert update_report.json()["status"] == "resolved"
    assert update_claim.json()["status"] == "approved"

    with SessionLocal() as db:
        audit_entries = db.scalars(select(AuditLog).where(AuditLog.action == "status_updated").order_by(AuditLog.id)).all()
        assert len(audit_entries) >= 2
        payloads = [json.loads(item.metadata_json or "{}") for item in audit_entries]
        assert any(p.get("new_status") == "resolved" and p.get("note") == "Verified update" for p in payloads)
        assert any(p.get("new_status") == "approved" and p.get("note") == "Ownership confirmed" for p in payloads)
        assert any(item.entity_type == "report" for item in audit_entries)
        assert any(item.entity_type == "owner_claim" for item in audit_entries)


def test_admin_can_moderate(client_and_session):
    client, SessionLocal = client_and_session

    from backend.app.models import Restaurant

    with SessionLocal() as db:
        db.add(Restaurant(name="Admin Place", certification_score=0.9, community_verification_score=0.7, recency_score=0.8))
        db.commit()

    reporter_token = _register(client, email="reporter2@example.com")
    admin_token = _register(client, email="admin@example.com")
    _set_role(SessionLocal, "admin@example.com", "admin")

    report_resp = client.post(
        "/restaurants/1/reports",
        headers={"Authorization": f"Bearer {reporter_token}"},
        json={"report_type": "other", "description": "Needs review"},
    )
    assert report_resp.status_code == 200
    report_id = report_resp.json()["id"]

    update = client.patch(
        f"/moderation/reports/{report_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "under_review", "note": "triage"},
    )
    assert update.status_code == 200
    assert update.json()["status"] == "under_review"


def test_report_moderation_writes_audit_log_with_note(client_and_session):
    client, SessionLocal = client_and_session

    from backend.app.models import Restaurant

    with SessionLocal() as db:
        db.add(Restaurant(name="Audit Place", certification_score=0.8, community_verification_score=0.8, recency_score=0.8))
        db.commit()

    reporter_token = _register(client, email="audit-reporter@example.com")
    moderator_token = _register(client, email="audit-mod@example.com")
    _set_role(SessionLocal, "audit-mod@example.com", "moderator")

    report_resp = client.post(
        "/restaurants/1/reports",
        headers={"Authorization": f"Bearer {reporter_token}"},
        json={"report_type": "outdated_info", "description": "hours changed"},
    )
    assert report_resp.status_code == 200
    report_id = report_resp.json()["id"]

    update = client.patch(
        f"/moderation/reports/{report_id}",
        headers={"Authorization": f"Bearer {moderator_token}"},
        json={"status": "under_review", "note": "triage started"},
    )
    assert update.status_code == 200

    with SessionLocal() as db:
        audit = db.scalars(
            select(AuditLog)
            .where(AuditLog.entity_type == "report", AuditLog.entity_id == str(report_id), AuditLog.action == "status_updated")
            .order_by(AuditLog.id.desc())
        ).first()
        assert audit is not None
        metadata = json.loads(audit.metadata_json or "{}")
        assert metadata["new_status"] == "under_review"
        assert metadata["note"] == "triage started"
