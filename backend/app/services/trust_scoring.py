from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models import Report, Restaurant, TrustEvent, VerificationDocument


@dataclass(frozen=True)
class RankingProfile:
    name: str
    certification_weight: float
    community_weight: float
    recency_weight: float
    min_certification: float = 0.0
    min_community: float = 0.0
    min_recency: float = 0.0


PROFILES: dict[str, RankingProfile] = {
    "balanced": RankingProfile("balanced", 0.50, 0.30, 0.20, min_certification=0.40, min_community=0.40),
    "strict": RankingProfile(
        "strict", 0.68, 0.17, 0.15, min_certification=0.80, min_community=0.55, min_recency=0.55
    ),
    "community_first": RankingProfile(
        "community_first", 0.22, 0.63, 0.15, min_certification=0.45, min_community=0.75
    ),
}


def get_profile(profile_name: str) -> RankingProfile:
    profile = PROFILES.get(profile_name)
    if not profile:
        raise ValueError(f"Unsupported profile '{profile_name}'.")
    return profile


def _contradiction_report_count(db: Session, restaurant_id: int) -> int:
    contradiction_types = {"inaccurate_halal_status", "inaccurate_kosher_status", "allergen_risk", "alcohol_served"}
    return int(
        db.scalar(
            select(func.count(Report.id)).where(
                Report.restaurant_id == restaurant_id,
                Report.report_type.in_(tuple(contradiction_types)),
                Report.status.in_(["open", "under_review"]),
            )
        )
        or 0
    )


def trust_breakdown(db: Session, restaurant: Restaurant, profile: RankingProfile) -> dict:
    base = (
        profile.certification_weight * restaurant.certification_score
        + profile.community_weight * restaurant.community_verification_score
        + profile.recency_weight * restaurant.recency_score
    )

    submitted_docs = int(
        db.scalar(
            select(func.count(VerificationDocument.id)).where(
                VerificationDocument.restaurant_id == restaurant.id,
            )
        )
        or 0
    )
    approved_docs = int(
        db.scalar(
            select(func.count(VerificationDocument.id)).where(
                VerificationDocument.restaurant_id == restaurant.id,
                VerificationDocument.status == "approved",
            )
        )
        or 0
    )
    contradiction_count = _contradiction_report_count(db, restaurant.id)
    event_delta = float(
        db.scalar(
            select(func.coalesce(func.sum(TrustEvent.delta), 0.0)).where(TrustEvent.restaurant_id == restaurant.id)
        )
        or 0.0
    )

    owner_verification_submitted = 0.05 if submitted_docs > 0 else 0.0
    moderation_approval = 0.1 if approved_docs > 0 else 0.0
    contradiction_penalty = min(0.2, contradiction_count * 0.05)

    final_score = max(0.0, min(1.0, base + owner_verification_submitted + moderation_approval - contradiction_penalty + event_delta))

    return {
        "base_score": round(base, 4),
        "owner_verification_submitted": owner_verification_submitted,
        "moderation_approval": moderation_approval,
        "contradiction_penalty": round(contradiction_penalty, 4),
        "event_delta": round(event_delta, 4),
        "recency_component": round(profile.recency_weight * restaurant.recency_score, 4),
        "final_score": round(final_score, 4),
    }


def trust_score(db: Session, restaurant: Restaurant, profile: RankingProfile) -> float:
    return trust_breakdown(db, restaurant, profile)["final_score"]


def meets_profile_minimums(restaurant: Restaurant, profile: RankingProfile) -> bool:
    return (
        restaurant.certification_score >= profile.min_certification
        and restaurant.community_verification_score >= profile.min_community
        and restaurant.recency_score >= profile.min_recency
    )
