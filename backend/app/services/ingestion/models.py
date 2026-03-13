from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


IngestionMode = Literal["city", "postal_code", "bbox", "radius"]


@dataclass(frozen=True)
class IngestionRequest:
    mode: IngestionMode
    query: str | None = None
    min_lat: float | None = None
    min_lon: float | None = None
    max_lat: float | None = None
    max_lon: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius_km: float | None = None
    country_code: str | None = None
    limit: int = 200


@dataclass(frozen=True)
class ProviderPlaceRecord:
    source_name: str
    source_id: str
    name: str
    address: str | None
    latitude: float | None
    longitude: float | None
    raw_payload: dict[str, Any]
    freshness_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class IngestionResult:
    created_count: int
    updated_count: int
    skipped_count: int
    imported_restaurant_ids: list[int]
