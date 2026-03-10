from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.models import Restaurant
from backend.app.services.constants import SUPPORTED_ALLERGENS, SUPPORTED_TAGS
from backend.app.services.explanation import build_card_explanation, build_explanation
from backend.app.services.matching import (
    allergens_present,
    matches_required_tags,
    passes_allergen_exclusions,
    restaurant_tags,
)
from backend.app.services.trust_scoring import get_profile, meets_profile_minimums, trust_breakdown


@dataclass
class ParticipantInput:
    participant_name: str
    required_tags: set[str]
    excluded_allergens: set[str]
    profile: str


def list_restaurants(db: Session) -> list[Restaurant]:
    stmt = (
        select(Restaurant)
        .options(selectinload(Restaurant.tags), selectinload(Restaurant.allergen_info))
        .order_by(Restaurant.id)
    )
    return list(db.scalars(stmt).all())


def get_restaurant_by_id(db: Session, restaurant_id: int) -> Restaurant | None:
    stmt = (
        select(Restaurant)
        .where(Restaurant.id == restaurant_id)
        .options(selectinload(Restaurant.tags), selectinload(Restaurant.allergen_info))
    )
    return db.scalars(stmt).first()


def _validate_inputs(required_tags: set[str], excluded_allergens: set[str]) -> None:
    unknown_tags = required_tags - SUPPORTED_TAGS
    if unknown_tags:
        raise ValueError(f"Unsupported tags: {', '.join(sorted(unknown_tags))}")

    unknown_allergens = excluded_allergens - SUPPORTED_ALLERGENS
    if unknown_allergens:
        raise ValueError(f"Unsupported allergens: {', '.join(sorted(unknown_allergens))}")


def _restaurant_summary(row: Restaurant) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "description": row.description,
        "address": row.address,
        "latitude": row.latitude,
        "longitude": row.longitude,
    }


def _normalize_participants(participants: list[dict] | list[object]) -> list[ParticipantInput]:
    normalized: list[ParticipantInput] = []
    for participant in participants:
        name = getattr(participant, "participant_name", None) if not isinstance(participant, dict) else participant.get("participant_name")
        required = getattr(participant, "required_tags", []) if not isinstance(participant, dict) else participant.get("required_tags", [])
        excluded = getattr(participant, "excluded_allergens", []) if not isinstance(participant, dict) else participant.get("excluded_allergens", [])
        profile = getattr(participant, "profile", "balanced") if not isinstance(participant, dict) else participant.get("profile", "balanced")

        required_set = set(required or [])
        excluded_set = set(excluded or [])
        _validate_inputs(required_set, excluded_set)
        get_profile(profile)

        normalized.append(
            ParticipantInput(
                participant_name=name or "participant",
                required_tags=required_set,
                excluded_allergens=excluded_set,
                profile=profile,
            )
        )
    return normalized


def _participant_evaluation(row: Restaurant, participant: ParticipantInput) -> dict:
    tag_match, missing = matches_required_tags(row, participant.required_tags)
    allergen_ok, conflicts = passes_allergen_exclusions(row, participant.excluded_allergens)
    profile = get_profile(participant.profile)
    profile_ok = meets_profile_minimums(row, profile)

    matched_count = len(participant.required_tags) - len(missing)
    tag_ratio = 1.0 if len(participant.required_tags) == 0 else matched_count / max(1, len(participant.required_tags))
    allergen_ratio = 1.0 if len(participant.excluded_allergens) == 0 else 1 - (len(conflicts) / max(1, len(participant.excluded_allergens)))
    participant_fit = round((0.6 * tag_ratio) + (0.25 * allergen_ratio) + (0.15 * (1.0 if profile_ok else 0.0)), 4)

    return {
        "participant_name": participant.participant_name,
        "required_tags_satisfied": tag_match,
        "missing_required_tags": sorted(missing),
        "excluded_allergens_satisfied": allergen_ok,
        "conflicting_allergens": sorted(conflicts),
        "profile": participant.profile,
        "participant_fit_score": participant_fit,
        "hard_satisfied": bool(tag_match and allergen_ok and profile_ok),
    }


def search_restaurants(
    db: Session,
    required_tags: set[str],
    excluded_allergens: set[str],
    profile_name: str,
    group_mode: bool = False,
    participants: list[dict] | list[object] | None = None,
) -> list[dict]:
    _validate_inputs(required_tags, excluded_allergens)
    profile = get_profile(profile_name)

    group_participants = _normalize_participants(participants or []) if group_mode else []
    has_constraints = bool(required_tags or excluded_allergens)

    ranked_candidates: list[dict] = []
    for row in list_restaurants(db):
        rest_tags = restaurant_tags(row)
        present_allergens = allergens_present(row)
        trust_data = trust_breakdown(db, row, profile)
        score = trust_data["final_score"]
        level = trust_data["trust_level"]
        caveats = trust_data["caveats"]

        if group_mode and group_participants:
            participant_satisfaction = [_participant_evaluation(row, p) for p in group_participants]
            group_fit = round(sum(item["participant_fit_score"] for item in participant_satisfaction) / len(participant_satisfaction), 4)
            hard_satisfied_count = sum(1 for item in participant_satisfaction if item["hard_satisfied"])
            no_one_satisfied = hard_satisfied_count == 0 and all(item["participant_fit_score"] < 0.45 for item in participant_satisfaction)
            if no_one_satisfied:
                continue

            excluded_status = [
                {"allergen": allergen, "present": allergen in present_allergens}
                for allergen in sorted({a for p in group_participants for a in p.excluded_allergens})
            ]

            combined_rank = round((0.7 * group_fit) + (0.3 * score), 4)
            full_explanation = (
                f"Group mode: {hard_satisfied_count}/{len(group_participants)} participants fully satisfied. "
                f"Group fit {group_fit}, trust {score} ({level}), combined rank {combined_rank}."
            )
            explanation = f"Group: {hard_satisfied_count}/{len(group_participants)} fully satisfied. Trust {score} ({level}). Rank {combined_rank}."

            ranked_candidates.append(
                {
                    "restaurant": _restaurant_summary(row),
                    "matched_tags": sorted({tag for p in group_participants for tag in (p.required_tags & rest_tags)}),
                    "excluded_allergen_status": excluded_status,
                    "trust_score": score,
                    "group_fit_score": group_fit,
                    "participant_satisfaction": [
                        {
                            "participant_name": item["participant_name"],
                            "required_tags_satisfied": item["required_tags_satisfied"],
                            "missing_required_tags": item["missing_required_tags"],
                            "excluded_allergens_satisfied": item["excluded_allergens_satisfied"],
                            "conflicting_allergens": item["conflicting_allergens"],
                            "profile": item["profile"],
                            "participant_fit_score": item["participant_fit_score"],
                        }
                        for item in participant_satisfaction
                    ],
                    "explanation": explanation,
                    "full_explanation": full_explanation,
                    "trust_level": level,
                    "trust_caveats": caveats,
                    "_rank_score": combined_rank,
                    "_hard_satisfied_count": hard_satisfied_count,
                }
            )
            continue

        tag_match, missing = matches_required_tags(row, required_tags)
        allergen_ok, conflicts = passes_allergen_exclusions(row, excluded_allergens)
        profile_ok = meets_profile_minimums(row, profile)

        if has_constraints and (not tag_match or not allergen_ok or not profile_ok):
            continue

        match_ratio = 1.0 if len(required_tags) == 0 else (len(required_tags) - len(missing)) / len(required_tags)
        allergen_ratio = 1.0 if len(excluded_allergens) == 0 else 1 - (len(conflicts) / len(excluded_allergens))
        preference_score = round((0.65 * match_ratio) + (0.35 * allergen_ratio), 4)

        matched_tags = sorted(required_tags & rest_tags)
        excluded_status = [{"allergen": allergen, "present": allergen in present_allergens} for allergen in sorted(excluded_allergens)]

        full_explanation = build_explanation(
            name=row.name,
            profile_name=profile.name,
            matched_tags=matched_tags,
            excluded_allergen_status=excluded_status,
            trust_score=score,
            trust_level=level,
            trust_caveats=caveats,
        )
        explanation = build_card_explanation(
            profile_name=profile.name,
            matched_tags=matched_tags,
            trust_score=score,
            trust_level=level,
            trust_caveats=caveats,
        )

        rank_score = score if not has_constraints else round((0.7 * score) + (0.3 * preference_score), 4)

        ranked_candidates.append(
            {
                "restaurant": _restaurant_summary(row),
                "matched_tags": matched_tags,
                "excluded_allergen_status": excluded_status,
                "trust_score": score,
                "group_fit_score": None,
                "participant_satisfaction": [],
                "explanation": explanation,
                "full_explanation": full_explanation,
                "trust_level": level,
                "trust_caveats": caveats,
                "_rank_score": rank_score,
            }
        )

    if group_mode and group_participants:
        return sorted(
            ranked_candidates,
            key=lambda item: (item.get("_rank_score", 0), item.get("_hard_satisfied_count", 0), item["trust_score"]),
            reverse=True,
        )

    return sorted(ranked_candidates, key=lambda item: item.get("_rank_score", item["trust_score"]), reverse=True)
