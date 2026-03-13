from __future__ import annotations

import json
from datetime import datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import AuditLog, OwnerClaim, User, VerificationDocument
from backend.app.services.file_storage import storage_backend
from backend.app.services.trust_evidence_service import create_trust_evidence
from backend.app.services.trust_event_service import create_trust_event


async def submit_verification_document_with_storage(
    db: Session,
    *,
    current_user: User,
    claim: OwnerClaim,
    document_type: str,
    notes: str | None,
    file: UploadFile | None,
    metadata_filename: str | None,
    metadata_mime_type: str | None,
) -> VerificationDocument:
    if claim.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot submit documents for another user claim")

    original_filename = metadata_filename
    mime_type = metadata_mime_type
    storage_path: str | None = None

    if file:
        stored = await storage_backend.save_upload(file)
        original_filename = stored.original_filename
        mime_type = stored.mime_type
        storage_path = stored.storage_path

    doc = VerificationDocument(
        owner_user_id=current_user.id,
        restaurant_id=claim.restaurant_id,
        owner_claim_id=claim.id,
        document_type=document_type,
        original_filename=original_filename,
        storage_path=storage_path,
        mime_type=mime_type,
        notes=notes,
        status="pending",
    )
    db.add(doc)
    db.flush()

    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            entity_type="verification_document",
            entity_id=str(doc.id),
            action="submitted",
            metadata_json=json.dumps({"claim_id": claim.id, "document_type": document_type, "has_file": bool(file)}),
        )
    )
    create_trust_event(
        db,
        restaurant_id=claim.restaurant_id,
        event_type="owner_verification_submitted",
        delta=0.01,
        actor_user_id=current_user.id,
        metadata={"verification_document_id": doc.id},
    )
    create_trust_evidence(
        db,
        restaurant_id=claim.restaurant_id,
        claim_key=document_type,
        evidence_type="owner_submitted_document",
        stance="supports",
        status="pending",
        confidence_weight=1.0,
        source_label=original_filename,
        summary=notes,
    )

    db.commit()
    db.refresh(doc)
    return doc


def list_owner_documents(db: Session, owner_user_id: int) -> list[VerificationDocument]:
    return list(
        db.scalars(
            select(VerificationDocument)
            .where(VerificationDocument.owner_user_id == owner_user_id)
            .order_by(VerificationDocument.created_at.desc())
        ).all()
    )


def list_verification_documents(db: Session, status: str | None = None) -> list[VerificationDocument]:
    stmt = select(VerificationDocument).order_by(VerificationDocument.created_at.desc())
    if status:
        stmt = stmt.where(VerificationDocument.status == status)
    return list(db.scalars(stmt).all())


def moderate_verification_document(
    db: Session,
    *,
    moderator: User,
    document_id: int,
    status: str,
    note: str | None,
) -> VerificationDocument:
    if status not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Invalid document status")

    doc = db.scalars(select(VerificationDocument).where(VerificationDocument.id == document_id)).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Verification document not found")

    previous = doc.status
    doc.status = status
    doc.reviewed_by_user_id = moderator.id
    doc.reviewed_at = datetime.utcnow()

    db.add(
        AuditLog(
            actor_user_id=moderator.id,
            entity_type="verification_document",
            entity_id=str(doc.id),
            action="status_updated",
            metadata_json=json.dumps({"previous_status": previous, "new_status": status, "note": note}),
        )
    )

    create_trust_event(
        db,
        restaurant_id=doc.restaurant_id,
        event_type=f"verification_document_{status}",
        delta=0.08 if status == "approved" else -0.04,
        actor_user_id=moderator.id,
        metadata={"verification_document_id": doc.id},
    )
    create_trust_evidence(
        db,
        restaurant_id=doc.restaurant_id,
        claim_key=doc.document_type,
        evidence_type="moderator_approval",
        stance="supports" if status == "approved" else "contradicts",
        status="approved",
        confidence_weight=1.2 if status == "approved" else 1.0,
        source_label=f"moderator:{moderator.id}",
        summary=note,
    )

    db.commit()
    db.refresh(doc)
    return doc
