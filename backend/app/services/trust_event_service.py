from __future__ import annotations

import json

from sqlalchemy.orm import Session

from backend.app.models import TrustEvent


def create_trust_event(
    db: Session,
    *,
    restaurant_id: int,
    event_type: str,
    delta: float,
    actor_user_id: int | None,
    metadata: dict | None = None,
) -> TrustEvent:
    event = TrustEvent(
        restaurant_id=restaurant_id,
        event_type=event_type,
        delta=delta,
        actor_user_id=actor_user_id,
        metadata_json=json.dumps(metadata or {}),
    )
    db.add(event)
    return event
