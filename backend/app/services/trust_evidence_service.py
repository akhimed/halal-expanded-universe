from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import TrustEvidence, User

TRUST_EVIDENCE_TYPES = {
    "imported_source_signal",
    "owner_submitted_claim",
    "owner_submitted_document",
    "moderator_approval",
    "community_report",
    "contradiction_report",
    "manual_note",
}


def create_trust_evidence(
    db: Session,
    *,
    restaurant_id: int,
    claim_key: str,
    evidence_type: str,
    stance: str,
    status: str,
    confidence_weight: float = 1.0,
    source_label: str | None = None,
    source_url: str | None = None,
    summary: str | None = None,
) -> TrustEvidence:
    if evidence_type not in TRUST_EVIDENCE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported trust evidence type")
    if stance not in {"supports", "contradicts", "neutral"}:
        raise HTTPException(status_code=400, detail="Unsupported trust evidence stance")
    if status not in {"pending", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Unsupported trust evidence status")

    row = TrustEvidence(
        restaurant_id=restaurant_id,
        claim_key=claim_key,
        evidence_type=evidence_type,
        stance=stance,
        status=status,
        confidence_weight=max(0.0, min(confidence_weight, 1.5)),
        source_label=source_label,
        source_url=source_url,
        summary=summary,
        captured_at=datetime.utcnow(),
    )
    db.add(row)
    return row


def list_trust_evidence(db: Session, *, status: str | None = None) -> list[TrustEvidence]:
    stmt = select(TrustEvidence).order_by(TrustEvidence.created_at.desc())
    if status:
        stmt = stmt.where(TrustEvidence.status == status)
    return list(db.scalars(stmt).all())


def moderate_trust_evidence(db: Session, *, moderator: User, evidence_id: int, status: str) -> TrustEvidence:
    if status not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Invalid trust evidence status")

    row = db.scalars(select(TrustEvidence).where(TrustEvidence.id == evidence_id)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Trust evidence not found")

    _ = moderator
    row.status = status
    db.commit()
    db.refresh(row)
    return row
