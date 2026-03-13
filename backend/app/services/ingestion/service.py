from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models import Restaurant, RestaurantImportSource
from backend.app.services.ingestion.models import IngestionRequest, IngestionResult, ProviderPlaceRecord
from backend.app.services.ingestion.osm_provider import OSMOverpassProvider
from backend.app.services.ingestion.provider_base import PlaceIngestionProvider


@dataclass(frozen=True)
class ImportSummary:
    restaurant_id: int
    action: str


class RestaurantIngestionService:
    def __init__(self, providers: dict[str, PlaceIngestionProvider] | None = None):
        self.providers = providers or {
            "osm": OSMOverpassProvider(
                overpass_url=settings.osm_overpass_url,
                nominatim_url=settings.osm_nominatim_url,
                user_agent=settings.osm_user_agent,
            )
        }

    def run_import(self, db: Session, provider_name: str, request: IngestionRequest) -> IngestionResult:
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")

        records = provider.fetch_places(request)
        created_count = 0
        updated_count = 0
        skipped_count = 0
        imported_ids: list[int] = []

        for record in records:
            summary = self._upsert_record(db, record)
            if summary is None:
                skipped_count += 1
                continue

            imported_ids.append(summary.restaurant_id)
            if summary.action == "created":
                created_count += 1
            else:
                updated_count += 1

        db.commit()
        unique_ids = sorted(set(imported_ids))
        return IngestionResult(
            created_count=created_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
            imported_restaurant_ids=unique_ids,
        )

    def _upsert_record(self, db: Session, record: ProviderPlaceRecord) -> ImportSummary | None:
        if not record.name:
            return None

        source_stmt = select(RestaurantImportSource).where(
            RestaurantImportSource.source_name == record.source_name,
            RestaurantImportSource.source_id == record.source_id,
        )
        source_row = db.scalars(source_stmt).first()

        if source_row:
            restaurant = db.get(Restaurant, source_row.restaurant_id)
            if restaurant is None:
                return None
            self._apply_restaurant_updates(restaurant, record)
            source_row.imported_at = datetime.utcnow()
            source_row.freshness_at = record.freshness_at
            source_row.raw_source_payload = json.dumps(record.raw_payload, ensure_ascii=False)
            return ImportSummary(restaurant_id=restaurant.id, action="updated")

        restaurant = self._find_existing_restaurant(db, record)
        if restaurant is None:
            restaurant = Restaurant(
                name=record.name,
                description=None,
                address=record.address,
                latitude=record.latitude,
                longitude=record.longitude,
                certification_score=0.0,
                community_verification_score=0.0,
                recency_score=0.0,
            )
            db.add(restaurant)
            db.flush()
            action = "created"
        else:
            self._apply_restaurant_updates(restaurant, record)
            action = "updated"

        source = RestaurantImportSource(
            restaurant_id=restaurant.id,
            source_name=record.source_name,
            source_id=record.source_id,
            imported_at=datetime.utcnow(),
            freshness_at=record.freshness_at,
            raw_source_payload=json.dumps(record.raw_payload, ensure_ascii=False),
        )
        db.add(source)
        db.flush()
        return ImportSummary(restaurant_id=restaurant.id, action=action)

    def _find_existing_restaurant(self, db: Session, record: ProviderPlaceRecord) -> Restaurant | None:
        if record.latitude is not None and record.longitude is not None:
            nearby_stmt = select(Restaurant).where(
                func.lower(Restaurant.name) == record.name.lower(),
                Restaurant.latitude.is_not(None),
                Restaurant.longitude.is_not(None),
                func.abs(Restaurant.latitude - record.latitude) <= 0.0008,
                func.abs(Restaurant.longitude - record.longitude) <= 0.0008,
            )
            candidate = db.scalars(nearby_stmt).first()
            if candidate:
                return candidate

        if record.address:
            addr_stmt = select(Restaurant).where(
                func.lower(Restaurant.name) == record.name.lower(),
                func.lower(Restaurant.address) == record.address.lower(),
            )
            candidate = db.scalars(addr_stmt).first()
            if candidate:
                return candidate

        return None

    def _apply_restaurant_updates(self, restaurant: Restaurant, record: ProviderPlaceRecord) -> None:
        if not restaurant.address and record.address:
            restaurant.address = record.address
        if restaurant.latitude is None and record.latitude is not None:
            restaurant.latitude = record.latitude
        if restaurant.longitude is None and record.longitude is not None:
            restaurant.longitude = record.longitude


_service_singleton = RestaurantIngestionService()


def run_ingestion_job(
    db: Session,
    provider: str,
    mode: str,
    *,
    query: str | None = None,
    min_lat: float | None = None,
    min_lon: float | None = None,
    max_lat: float | None = None,
    max_lon: float | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
    country_code: str | None = None,
    limit: int = 200,
) -> IngestionResult:
    request = IngestionRequest(
        mode=mode,  # type: ignore[arg-type]
        query=query,
        min_lat=min_lat,
        min_lon=min_lon,
        max_lat=max_lat,
        max_lon=max_lon,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        country_code=country_code,
        limit=limit,
    )
    return _service_singleton.run_import(db=db, provider_name=provider, request=request)


def available_providers() -> Sequence[str]:
    return tuple(sorted(_service_singleton.providers.keys()))
