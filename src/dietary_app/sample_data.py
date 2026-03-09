from __future__ import annotations

from .engine import search_venues
from .models import DietaryTag, SearchRequest, TrustSignals, Venue

SAMPLE_VENUES = [
    Venue(
        id="v1",
        name="Saffron Garden",
        supported_tags={DietaryTag.HALAL, DietaryTag.VEGETARIAN},
        allergens_present={"dairy"},
        trust_signals=TrustSignals(0.95, 0.80, 0.90),
    ),
    Venue(
        id="v2",
        name="Green Karma Kitchen",
        supported_tags={
            DietaryTag.HINDU_VEGETARIAN,
            DietaryTag.VEGAN,
            DietaryTag.VEGETARIAN,
        },
        allergens_present={"nuts"},
        trust_signals=TrustSignals(0.70, 0.90, 0.88),
    ),
    Venue(
        id="v3",
        name="Olive & Fig Kosher Bistro",
        supported_tags={DietaryTag.KOSHER, DietaryTag.VEGETARIAN},
        allergens_present={"gluten"},
        trust_signals=TrustSignals(0.92, 0.85, 0.80),
    ),
]


def demo() -> None:
    request = SearchRequest(
        required_tags={DietaryTag.HINDU_VEGETARIAN, DietaryTag.VEGAN},
        excluded_allergens={"shellfish"},
    )

    for profile in ["balanced", "strict", "community_first"]:
        print(f"\nProfile: {profile}")
        matches = search_venues(SAMPLE_VENUES, request, profile_name=profile)
        for index, match in enumerate(matches, start=1):
            print(f"{index}. {match.venue.name} | trust={match.trust_score}")
            for reason in match.reasons:
                print(f"   - {reason}")


if __name__ == "__main__":
    demo()
