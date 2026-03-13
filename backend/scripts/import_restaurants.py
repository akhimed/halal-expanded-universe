from __future__ import annotations

import argparse

from backend.app.db.session import SessionLocal
from backend.app.services.ingestion import run_ingestion_job


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import restaurants from real-world place providers")
    parser.add_argument("--provider", default="osm", help="Provider key (default: osm)")
    parser.add_argument("--mode", choices=["city", "postal_code", "bbox", "radius"], required=True)
    parser.add_argument("--query", help="City name or postal code depending on mode")
    parser.add_argument("--country-code", help="Optional 2-letter country code for geocoding")
    parser.add_argument("--min-lat", type=float)
    parser.add_argument("--min-lon", type=float)
    parser.add_argument("--max-lat", type=float)
    parser.add_argument("--max-lon", type=float)
    parser.add_argument("--latitude", type=float)
    parser.add_argument("--longitude", type=float)
    parser.add_argument("--radius-km", type=float)
    parser.add_argument("--limit", type=int, default=200)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    with SessionLocal() as db:
        result = run_ingestion_job(
            db,
            provider=args.provider,
            mode=args.mode,
            query=args.query,
            min_lat=args.min_lat,
            min_lon=args.min_lon,
            max_lat=args.max_lat,
            max_lon=args.max_lon,
            latitude=args.latitude,
            longitude=args.longitude,
            radius_km=args.radius_km,
            country_code=args.country_code,
            limit=args.limit,
        )

    print(
        "Import complete:",
        {
            "provider": args.provider,
            "mode": args.mode,
            "created": result.created_count,
            "updated": result.updated_count,
            "skipped": result.skipped_count,
            "imported_restaurant_ids": result.imported_restaurant_ids,
        },
    )


if __name__ == "__main__":
    main()
