from __future__ import annotations

import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import AuditLog, OwnerClaim, Report, User
from backend.app.services.trust_event_service import create_trust_event

ALLOWED_REPORT_STATUSES = {"open", "under_review", "resolved", "rejected"}
ALLOWED_OWNER_CLAIM_STATUSES = {"approved", "rejected"}


def list_reports(db: Session, status: str | None = None) -> list[Report]:
    stmt = select(Report).order_by(Report.created_at.desc())
    if status:
        stmt = stmt.where(Report.status == status)
    return list(db.scalars(stmt).all())


def update_report_status(
    db: Session,
    *,
    moderator: User,
    report_id: int,
    status: str,
    note: str | None,
) -> Report:
    if status not in ALLOWED_REPORT_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid report status")

    report = db.scalars(select(Report).where(Report.id == report_id)).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    previous = report.status
    report.status = status

    audit = AuditLog(
        actor_user_id=moderator.id,
        entity_type="report",
        entity_id=str(report.id),
        action="status_updated",
        metadata_json=json.dumps(
            {
                "previous_status": previous,
                "new_status": status,
                "note": note,
                "moderator_role": moderator.role,
            }
        ),
    )
    db.add(audit)
    if status in {"resolved", "rejected"} and report.restaurant_id:
        create_trust_event(
            db,
            restaurant_id=report.restaurant_id,
            event_type=f"report_{status}",
            delta=0.01 if status == "resolved" else -0.01,
            actor_user_id=moderator.id,
            metadata={"report_id": report.id},
        )
    db.commit()
    db.refresh(report)
    return report


def list_owner_claims(db: Session, status: str | None = None) -> list[OwnerClaim]:
    stmt = select(OwnerClaim).order_by(OwnerClaim.created_at.desc())
    if status:
        stmt = stmt.where(OwnerClaim.status == status)
    return list(db.scalars(stmt).all())


def moderate_owner_claim(
    db: Session,
    *,
    moderator: User,
    claim_id: int,
    status: str,
    note: str | None,
) -> OwnerClaim:
    if status not in ALLOWED_OWNER_CLAIM_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid owner claim status")

    claim = db.scalars(select(OwnerClaim).where(OwnerClaim.id == claim_id)).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Owner claim not found")

    previous = claim.status
    claim.status = status

    audit = AuditLog(
        actor_user_id=moderator.id,
        entity_type="owner_claim",
        entity_id=str(claim.id),
        action="status_updated",
        metadata_json=json.dumps(
            {
                "previous_status": previous,
                "new_status": status,
                "note": note,
                "moderator_role": moderator.role,
            }
        ),
    )
    db.add(audit)
    create_trust_event(
        db,
        restaurant_id=claim.restaurant_id,
        event_type=f"owner_claim_{status}",
        delta=0.05 if status == "approved" else -0.03,
        actor_user_id=moderator.id,
        metadata={"owner_claim_id": claim.id},
    )
    db.commit()
    db.refresh(claim)
    return claim
