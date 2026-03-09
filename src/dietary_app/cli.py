from __future__ import annotations

import argparse
import json
from typing import Iterable, Set

from .engine import search_venues
from .models import DietaryTag, SearchRequest
from .sample_data import SAMPLE_VENUES
from .server import run_server


def _parse_csv_set(value: str) -> Set[str]:
    if not value.strip():
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


def _to_tags(raw_tags: Iterable[str]) -> Set[DietaryTag]:
    return {DietaryTag(tag) for tag in raw_tags}


def main() -> None:
    parser = argparse.ArgumentParser(description="Dietary discovery MVP CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search sample venues")
    search_parser.add_argument("--required", default="", help="Comma-separated required tags")
    search_parser.add_argument("--exclude", default="", help="Comma-separated allergens to exclude")
    search_parser.add_argument(
        "--profile",
        default="balanced",
        choices=["balanced", "strict", "community_first"],
        help="Ranking/filter profile",
    )
    search_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format"
    )

    serve_parser = subparsers.add_parser("serve", help="Run local HTTP API")
    serve_parser.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()

    if args.command == "serve":
        run_server(port=args.port)
        return

    required = _to_tags(_parse_csv_set(args.required))
    request = SearchRequest(required_tags=required, excluded_allergens=_parse_csv_set(args.exclude))
    results = search_venues(SAMPLE_VENUES, request, profile_name=args.profile)

    if args.format == "json":
        print(
            json.dumps(
                [
                    {
                        "id": item.venue.id,
                        "name": item.venue.name,
                        "trust_score": item.trust_score,
                        "reasons": item.reasons,
                    }
                    for item in results
                ],
                indent=2,
            )
        )
        return

    if not results:
        print("No matches found.")
        return

    for index, item in enumerate(results, start=1):
        print(f"{index}. {item.venue.name:30} trust={item.trust_score}")
        print(f"   tags={','.join(sorted(tag.value for tag in item.venue.supported_tags))}")


if __name__ == "__main__":
    main()
