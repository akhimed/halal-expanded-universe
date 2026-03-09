from __future__ import annotations

import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.models import AuditLog, OwnerClaim, Restaurant, User

OWNER_CLAIM_STATUSES = {"pending", "approved", "rejected"}


def submit_owner_claim(
    db: Session,
    *,
    current_user: User,
    restaurant: Restaurant,
    notes: str | None,
) -> OwnerClaim:
    existing = db.scalars(
        select(OwnerClaim).where(
            OwnerClaim.user_id == current_user.id,
            OwnerClaim.restaurant_id == restaurant.id,
            OwnerClaim.status.in_(["pending", "approved"]),
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Claim already exists for this restaurant")

    claim = OwnerClaim(
        user_id=current_user.id,
        restaurant_id=restaurant.id,
        status="pending",
        notes=notes,
    )
    db.add(claim)
    db.flush()

    audit = AuditLog(
        actor_user_id=current_user.id,
        entity_type="owner_claim",
        entity_id=str(claim.id),
        action="submitted",
        metadata_json=json.dumps(
            {
                "restaurant_id": restaurant.id,
                "status": claim.status,
                "has_notes": bool(notes),
            }
        ),
    )
    db.add(audit)
    db.commit()
    db.refresh(claim)
    return claim


def list_owner_claims(db: Session, user_id: int) -> list[OwnerClaim]:
    stmt = (
        select(OwnerClaim)
        .where(OwnerClaim.user_id == user_id)
        .options(selectinload(OwnerClaim.restaurant))
        .order_by(OwnerClaim.created_at.desc())
    )
    return list(db.scalars(stmt).all())
