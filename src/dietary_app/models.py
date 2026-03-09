from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Set


class DietaryTag(str, Enum):
    HALAL = "halal"
    KOSHER = "kosher"
    HINDU_VEGETARIAN = "hindu_vegetarian"
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"


@dataclass(frozen=True)
class TrustSignals:
    certification_score: float
    community_verification_score: float
    recency_score: float


@dataclass(frozen=True)
class Venue:
    id: str
    name: str
    supported_tags: Set[DietaryTag]
    allergens_present: Set[str] = field(default_factory=set)
    trust_signals: TrustSignals = field(
        default_factory=lambda: TrustSignals(0.0, 0.0, 0.0)
    )


@dataclass(frozen=True)
class SearchRequest:
    required_tags: Set[DietaryTag]
    excluded_allergens: Set[str] = field(default_factory=set)


@dataclass(frozen=True)
class MatchResult:
    venue: Venue
    trust_score: float
    reasons: List[str]
