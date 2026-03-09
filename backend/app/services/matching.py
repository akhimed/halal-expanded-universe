from __future__ import annotations

from backend.app.models import Restaurant


def restaurant_tags(restaurant: Restaurant) -> set[str]:
    return {tag.tag for tag in restaurant.tags}


def allergens_present(restaurant: Restaurant) -> set[str]:
    return {item.allergen for item in restaurant.allergen_info if item.present}


def matches_required_tags(restaurant: Restaurant, required_tags: set[str]) -> tuple[bool, set[str]]:
    tags = restaurant_tags(restaurant)
    missing = required_tags - tags
    return (len(missing) == 0, missing)


def passes_allergen_exclusions(
    restaurant: Restaurant,
    excluded_allergens: set[str],
) -> tuple[bool, set[str]]:
    present = allergens_present(restaurant)
    conflicts = excluded_allergens & present
    return (len(conflicts) == 0, conflicts)
