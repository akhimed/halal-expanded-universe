from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models import Report, Restaurant, TrustEvidence, TrustEvent, VerificationDocument

EVIDENCE_TYPE_WEIGHT = {
    "imported_source_signal": 0.06,
    "owner_submitted_claim": 0.03,
    "owner_submitted_document": 0.08,
    "moderator_approval": 0.1,
    "community_report": 0.04,
    "contradiction_report": 0.08,
    "manual_note": 0.02,
}


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

    evidence_rows = list(db.scalars(select(TrustEvidence).where(TrustEvidence.restaurant_id == restaurant.id)).all())
    now = datetime.now(timezone.utc)
    evidence_net = 0.0
    evidence_support_count = 0
    evidence_contradiction_count = 0
    evidence_by_type: dict[str, dict[str, float | int]] = {}
    freshness_sum = 0.0
    approved_count = 0
    for row in evidence_rows:
        age_days = max(0.0, (now - row.captured_at.replace(tzinfo=timezone.utc)).total_seconds() / 86400.0)
        freshness = max(0.25, 1.0 - (age_days / 365.0))
        freshness_sum += freshness
        status_weight = 1.0 if row.status == "approved" else (0.55 if row.status == "pending" else 0.0)
        if row.status == "approved":
            approved_count += 1
        stance_multiplier = 1.0 if row.stance == "supports" else (-1.0 if row.stance == "contradicts" else 0.0)
        if row.stance == "supports":
            evidence_support_count += 1
        if row.stance == "contradicts":
            evidence_contradiction_count += 1
        base_weight = EVIDENCE_TYPE_WEIGHT.get(row.evidence_type, 0.03)
        contribution = base_weight * stance_multiplier * status_weight * freshness * row.confidence_weight
        evidence_net += contribution
        bucket = evidence_by_type.setdefault(row.evidence_type, {"count": 0, "impact": 0.0})
        bucket["count"] = int(bucket["count"]) + 1
        bucket["impact"] = round(float(bucket["impact"]) + contribution, 4)

    evidence_freshness = round((freshness_sum / len(evidence_rows)) if evidence_rows else 0.0, 4)
    conflicting_claims = evidence_support_count > 0 and evidence_contradiction_count > 0

    final_score = max(
        0.0,
        min(1.0, base + owner_verification_submitted + moderation_approval - contradiction_penalty + event_delta + evidence_net),
    )

    final_score = round(final_score, 4)
    level = trust_level(final_score)
    caveats = trust_caveats(
        recency_score=restaurant.recency_score,
        contradiction_penalty=contradiction_penalty,
        approved_docs=approved_docs,
        final_score=final_score,
        evidence_freshness=evidence_freshness,
        conflicting_claims=conflicting_claims,
    )

    return {
        "base_score": round(base, 4),
        "score_band": trust_score_band(level),
        "score_band_label": trust_score_band_label(level),
        "owner_verification_submitted": owner_verification_submitted,
        "moderation_approval": moderation_approval,
        "contradiction_penalty": round(contradiction_penalty, 4),
        "event_delta": round(event_delta, 4),
        "recency_component": round(profile.recency_weight * restaurant.recency_score, 4),
        "evidence_net": round(evidence_net, 4),
        "evidence_freshness": evidence_freshness,
        "evidence_counts": {
            "total": len(evidence_rows),
            "approved": approved_count,
            "supports": evidence_support_count,
            "contradictions": evidence_contradiction_count,
        },
        "evidence_by_type": evidence_by_type,
        "conflicting_claims": conflicting_claims,
        "final_score": final_score,
        "trust_level": level,
        "low_confidence": level == "low" or evidence_freshness < 0.5,
        "caveats": caveats,
    }


def trust_score(db: Session, restaurant: Restaurant, profile: RankingProfile) -> float:
    return trust_breakdown(db, restaurant, profile)["final_score"]


def trust_level(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.6:
        return "medium"
    return "low"




def trust_score_band(level: str) -> str:
    if level == "high":
        return "0.80-1.00"
    if level == "medium":
        return "0.60-0.79"
    return "0.00-0.59"


def trust_score_band_label(level: str) -> str:
    if level == "high":
        return "High trust"
    if level == "medium":
        return "Medium trust"
    return "Low trust"

def trust_caveats(
    *,
    recency_score: float,
    contradiction_penalty: float,
    approved_docs: int,
    final_score: float,
    evidence_freshness: float,
    conflicting_claims: bool,
) -> list[str]:
    caveats: list[str] = []

    if final_score < 0.6:
        caveats.append("Low-confidence listing: use caution and verify details before visiting.")
    if contradiction_penalty > 0:
        caveats.append("Active contradiction reports are lowering trust while moderators review evidence.")
    if approved_docs == 0:
        caveats.append("No moderator-approved owner verification documents are on file yet.")
    if recency_score < 0.6:
        caveats.append("Recent verification activity is limited, so details may be outdated.")
    if evidence_freshness < 0.5:
        caveats.append("Most trust evidence is stale; confidence is reduced until newer sources are reviewed.")
    if conflicting_claims:
        caveats.append("Conflicting trust evidence exists across sources; moderator resolution is in progress.")

    return caveats


def meets_profile_minimums(restaurant: Restaurant, profile: RankingProfile) -> bool:
    return (
        restaurant.certification_score >= profile.min_certification
        and restaurant.community_verification_score >= profile.min_community
        and restaurant.recency_score >= profile.min_recency
    )
