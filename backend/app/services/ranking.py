from __future__ import annotations


def rank_by_trust(results: list[dict]) -> list[dict]:
    return sorted(results, key=lambda item: item["trust_score"], reverse=True)
