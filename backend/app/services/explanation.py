from __future__ import annotations


def build_explanation(
    *,
    name: str,
    profile_name: str,
    matched_tags: list[str],
    excluded_allergen_status: list[dict[str, bool]],
    trust_score: float,
) -> str:
    safe_allergens = [item["allergen"] for item in excluded_allergen_status if not item["present"]]
    return (
        f"{name} matched required tags ({', '.join(matched_tags) if matched_tags else 'none required'}) "
        f"using the {profile_name} profile. "
        f"Excluded allergens clear: {', '.join(safe_allergens) if safe_allergens else 'none'}. "
        f"Computed trust score: {trust_score}."
    )
