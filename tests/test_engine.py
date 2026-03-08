import unittest

from src.dietary_app.engine import calculate_trust_score, search_venues
from src.dietary_app.models import DietaryTag, SearchRequest, TrustSignals, Venue
from src.dietary_app.policies import get_profile


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.venues = [
            Venue(
                id="a",
                name="Halal House",
                supported_tags={DietaryTag.HALAL, DietaryTag.VEGETARIAN},
                allergens_present={"dairy"},
                trust_signals=TrustSignals(1.0, 0.8, 0.5),
            ),
            Venue(
                id="b",
                name="Vegan Valley",
                supported_tags={
                    DietaryTag.VEGAN,
                    DietaryTag.VEGETARIAN,
                    DietaryTag.HINDU_VEGETARIAN,
                },
                allergens_present=set(),
                trust_signals=TrustSignals(0.7, 0.9, 1.0),
            ),
        ]

    def test_calculate_trust_score(self) -> None:
        score = calculate_trust_score(self.venues[0], profile=get_profile("balanced"))
        self.assertAlmostEqual(score, 0.83)

    def test_search_filters_missing_tags(self) -> None:
        request = SearchRequest(required_tags={DietaryTag.KOSHER})
        matches = search_venues(self.venues, request)
        self.assertEqual(matches, [])

    def test_search_filters_allergen_conflict(self) -> None:
        request = SearchRequest(
            required_tags={DietaryTag.HALAL}, excluded_allergens={"dairy"}
        )
        matches = search_venues(self.venues, request)
        self.assertEqual(matches, [])

    def test_search_sorts_by_trust_score(self) -> None:
        request = SearchRequest(required_tags={DietaryTag.VEGETARIAN})
        matches = search_venues(self.venues, request)

        self.assertEqual(len(matches), 2)
        self.assertGreaterEqual(matches[0].trust_score, matches[1].trust_score)

    def test_strict_profile_enforces_thresholds(self) -> None:
        request = SearchRequest(required_tags={DietaryTag.VEGETARIAN})
        matches = search_venues(self.venues, request, profile_name="strict")

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].venue.name, "Halal House")


if __name__ == "__main__":
    unittest.main()
