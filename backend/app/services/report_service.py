from __future__ import annotations

import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.models import AuditLog, Report, User
from backend.app.services.trust_event_service import create_trust_event

REPORT_TYPES = {
    "inaccurate_halal_status",
    "inaccurate_kosher_status",
    "allergen_risk",
    "alcohol_served",
    "outdated_info",
    "other",
}


def create_report(
    db: Session,
    *,
    current_user: User,
    restaurant_id: int,
    report_type: str,
    description: str | None,
    evidence_url: str | None,
) -> Report:
    if report_type not in REPORT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid report type")

    report = Report(
        user_id=current_user.id,
        restaurant_id=restaurant_id,
        reason=report_type,
        report_type=report_type,
        description=description,
        evidence_url=evidence_url,
        status="open",
    )
    db.add(report)
    db.flush()

    audit = AuditLog(
        actor_user_id=current_user.id,
        entity_type="report",
        entity_id=str(report.id),
        action="created",
        metadata_json=json.dumps(
            {
                "restaurant_id": restaurant_id,
                "report_type": report_type,
                "has_description": bool(description),
                "has_evidence_url": bool(evidence_url),
            }
        ),
    )
    db.add(audit)

    if report_type in {"inaccurate_halal_status", "inaccurate_kosher_status", "allergen_risk", "alcohol_served"}:
        create_trust_event(
            db,
            restaurant_id=restaurant_id,
            event_type="contradiction_report_submitted",
            delta=-0.02,
            actor_user_id=current_user.id,
            metadata={"report_id": report.id, "report_type": report_type},
        )
    db.commit()
    db.refresh(report)
    return report
