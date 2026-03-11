from __future__ import annotations


def build_explanation(
    *,
    name: str,
    profile_name: str,
    matched_tags: list[str],
    excluded_allergen_status: list[dict[str, bool]],
    trust_score: float,
    trust_level: str,
    trust_caveats: list[str],
) -> str:
    safe_allergens = [item["allergen"] for item in excluded_allergen_status if not item["present"]]
    band_text = {
        "high": "High trust band (0.80-1.00)",
        "medium": "Medium trust band (0.60-0.79)",
        "low": "Low trust band (0.00-0.59)",
    }.get(trust_level, "Unrated trust band")
    caveat_text = " ".join(f"Caveat: {item}" for item in trust_caveats) if trust_caveats else "No active caveats."
    return (
        f"{name} matched required tags ({', '.join(matched_tags) if matched_tags else 'none required'}) "
        f"using the {profile_name} profile. "
        f"Excluded allergens clear: {', '.join(safe_allergens) if safe_allergens else 'none'}. "
        f"Computed trust score: {trust_score} ({trust_level}). {band_text}. "
        "Trust reflects weighted certification, community verification, recency, owner verification submission, "
        "moderation approval bonus, contradiction penalties, and trust-event adjustments. "
        f"{caveat_text}".strip()
    )


def build_card_explanation(
    *,
    profile_name: str,
    matched_tags: list[str],
    trust_score: float,
    trust_level: str,
    trust_caveats: list[str] | None = None,
) -> str:
    matched_label = ", ".join(matched_tags) if matched_tags else "no required tags"
    band_short = {"high": "80-100", "medium": "60-79", "low": "0-59"}.get(trust_level, "unknown")
    return f"{profile_name}: {matched_label}. Trust {trust_score} ({trust_level}, band {band_short})."
