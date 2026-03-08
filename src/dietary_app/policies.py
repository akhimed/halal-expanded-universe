from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class RankingProfile:
    name: str
    certification_weight: float
    community_weight: float
    recency_weight: float
    min_certification: float = 0.0
    min_community: float = 0.0
    min_recency: float = 0.0


PROFILES: Dict[str, RankingProfile] = {
    "balanced": RankingProfile(
        name="balanced",
        certification_weight=0.45,
        community_weight=0.35,
        recency_weight=0.20,
    ),
    "strict": RankingProfile(
        name="strict",
        certification_weight=0.60,
        community_weight=0.25,
        recency_weight=0.15,
        min_certification=0.80,
        min_community=0.60,
        min_recency=0.50,
    ),
    "community_first": RankingProfile(
        name="community_first",
        certification_weight=0.25,
        community_weight=0.55,
        recency_weight=0.20,
        min_community=0.70,
    ),
}


def get_profile(name: str) -> RankingProfile:
    profile = PROFILES.get(name)
    if not profile:
        available = ", ".join(sorted(PROFILES))
        raise ValueError(f"Unknown profile '{name}'. Available: {available}")
    return profile
