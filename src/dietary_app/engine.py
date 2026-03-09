from __future__ import annotations

from typing import Iterable, List

from .models import MatchResult, SearchRequest, Venue
from .policies import RankingProfile, get_profile


def calculate_trust_score(venue: Venue, profile: RankingProfile) -> float:
    """Return weighted trust score in range [0, 1]."""
    signals = venue.trust_signals
    score = (
        profile.certification_weight * signals.certification_score
        + profile.community_weight * signals.community_verification_score
        + profile.recency_weight * signals.recency_score
    )
    return round(score, 4)


def _validate_match(venue: Venue, request: SearchRequest, profile: RankingProfile) -> List[str]:
    reasons: List[str] = []

    missing_tags = request.required_tags - venue.supported_tags
    if missing_tags:
        missing = ", ".join(sorted(tag.value for tag in missing_tags))
        reasons.append(f"Missing required tags: {missing}")

    conflicting_allergens = request.excluded_allergens & venue.allergens_present
    if conflicting_allergens:
        allergens = ", ".join(sorted(conflicting_allergens))
        reasons.append(f"Contains excluded allergens: {allergens}")

    signals = venue.trust_signals
    if signals.certification_score < profile.min_certification:
        reasons.append(
            f"Certification below profile minimum ({signals.certification_score} < {profile.min_certification})"
        )
    if signals.community_verification_score < profile.min_community:
        reasons.append(
            "Community verification below profile minimum "
            f"({signals.community_verification_score} < {profile.min_community})"
        )
    if signals.recency_score < profile.min_recency:
        reasons.append(f"Recency below profile minimum ({signals.recency_score} < {profile.min_recency})")

    return reasons


def search_venues(
    venues: Iterable[Venue],
    request: SearchRequest,
    profile_name: str = "balanced",
) -> List[MatchResult]:
    """
    Filter venues by hard constraints and rank by trust score.
    Returns explainable match results sorted descending by trust score.
    """
    profile = get_profile(profile_name)
    matches: List[MatchResult] = []

    for venue in venues:
        failure_reasons = _validate_match(venue, request, profile)
        if failure_reasons:
            continue

        trust_score = calculate_trust_score(venue, profile)
        reasons = [
            "All required dietary tags supported",
            "No excluded allergens found",
            f"Profile used: {profile.name}",
            f"Trust score computed: {trust_score}",
        ]
        matches.append(MatchResult(venue=venue, trust_score=trust_score, reasons=reasons))

    matches.sort(key=lambda item: item.trust_score, reverse=True)
    return matches
