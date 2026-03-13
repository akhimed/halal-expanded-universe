from __future__ import annotations

from datetime import datetime
import math
from typing import Any

import httpx

from backend.app.services.ingestion.models import IngestionRequest, ProviderPlaceRecord
from backend.app.services.ingestion.provider_base import PlaceIngestionProvider


class OSMOverpassProvider(PlaceIngestionProvider):
    source_name = "osm_overpass"

    def __init__(
        self,
        overpass_url: str = "https://overpass-api.de/api/interpreter",
        nominatim_url: str = "https://nominatim.openstreetmap.org/search",
        user_agent: str = "halal-expanded-universe-ingestion/1.0",
        timeout_seconds: float = 30.0,
    ):
        self.overpass_url = overpass_url
        self.nominatim_url = nominatim_url
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds

    def fetch_places(self, request: IngestionRequest) -> list[ProviderPlaceRecord]:
        bbox = self._resolve_bbox(request)
        overpass_query = self._build_restaurant_query(*bbox, limit=request.limit)
        payload = self._fetch_overpass(overpass_query)
        return self._normalize_elements(payload)

    def _resolve_bbox(self, request: IngestionRequest) -> tuple[float, float, float, float]:
        if request.mode == "bbox":
            if None in (request.min_lat, request.min_lon, request.max_lat, request.max_lon):
                raise ValueError("bbox mode requires min_lat, min_lon, max_lat, and max_lon")
            return request.min_lat, request.min_lon, request.max_lat, request.max_lon

        if request.mode in {"city", "postal_code"}:
            if not request.query:
                raise ValueError(f"{request.mode} mode requires query")
            return self._geocode_to_bbox(request.query, request.country_code)

        if request.mode == "radius":
            if request.latitude is None or request.longitude is None or request.radius_km is None:
                raise ValueError("radius mode requires latitude, longitude, and radius_km")
            delta_lat = request.radius_km / 111.0
            cos_lat = max(0.1, abs(math.cos(math.radians(request.latitude))))
            delta_lon = request.radius_km / (111.0 * cos_lat)
            return (
                request.latitude - delta_lat,
                request.longitude - delta_lon,
                request.latitude + delta_lat,
                request.longitude + delta_lon,
            )

        raise ValueError(f"Unsupported ingestion mode: {request.mode}")

    def _geocode_to_bbox(self, query: str, country_code: str | None) -> tuple[float, float, float, float]:
        params: dict[str, Any] = {
            "q": query,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": 1,
        }
        if country_code:
            params["countrycodes"] = country_code.lower()

        with httpx.Client(timeout=self.timeout_seconds, headers={"User-Agent": self.user_agent}) as client:
            response = client.get(self.nominatim_url, params=params)
            response.raise_for_status()
            data = response.json()

        if not data:
            raise ValueError(f"No geocoding result found for query: {query}")

        bbox = data[0].get("boundingbox")
        if not bbox or len(bbox) != 4:
            raise ValueError("Geocoding result did not include bounding box")

        south, north, west, east = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
        return south, west, north, east

    def _build_restaurant_query(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float, limit: int) -> str:
        return f"""
[out:json][timeout:25];
(
  node[\"amenity\"=\"restaurant\"]({min_lat},{min_lon},{max_lat},{max_lon});
  way[\"amenity\"=\"restaurant\"]({min_lat},{min_lon},{max_lat},{max_lon});
  relation[\"amenity\"=\"restaurant\"]({min_lat},{min_lon},{max_lat},{max_lon});
);
out center {limit};
""".strip()

    def _fetch_overpass(self, query: str) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout_seconds, headers={"User-Agent": self.user_agent}) as client:
            response = client.post(self.overpass_url, data={"data": query})
            response.raise_for_status()
            return response.json()

    def _normalize_elements(self, payload: dict[str, Any]) -> list[ProviderPlaceRecord]:
        records: list[ProviderPlaceRecord] = []
        for element in payload.get("elements", []):
            tags = element.get("tags", {}) or {}
            name = tags.get("name")
            if not name:
                continue

            lat, lon = self._extract_coordinates(element)
            source_id = f"{element.get('type', 'unknown')}/{element.get('id')}"
            address = self._format_address(tags)
            records.append(
                ProviderPlaceRecord(
                    source_name=self.source_name,
                    source_id=source_id,
                    name=name,
                    address=address,
                    latitude=lat,
                    longitude=lon,
                    raw_payload=element,
                    freshness_at=datetime.utcnow(),
                )
            )
        return records

    def _extract_coordinates(self, element: dict[str, Any]) -> tuple[float | None, float | None]:
        if "lat" in element and "lon" in element:
            return float(element["lat"]), float(element["lon"])

        center = element.get("center")
        if isinstance(center, dict) and "lat" in center and "lon" in center:
            return float(center["lat"]), float(center["lon"])

        return None, None

    def _format_address(self, tags: dict[str, Any]) -> str | None:
        fields = [
            tags.get("addr:housenumber"),
            tags.get("addr:street"),
            tags.get("addr:city"),
            tags.get("addr:postcode"),
            tags.get("addr:country"),
        ]
        chunks = [str(chunk).strip() for chunk in fields if chunk]
        if chunks:
            return ", ".join(chunks)

        fallback = tags.get("addr:full")
        return str(fallback).strip() if fallback else None
