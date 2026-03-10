from __future__ import annotations

import math
from dataclasses import dataclass

import httpx


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "halal-expanded-universe/1.0"


@dataclass
class ResolvedLocation:
    query: str
    label: str
    latitude: float
    longitude: float


def normalize_location_query(query: str) -> str:
    return " ".join(query.strip().split())


def resolve_location(query: str) -> ResolvedLocation:
    cleaned_query = normalize_location_query(query)
    if not cleaned_query:
        raise ValueError("Location query is required")

    params = {
        "q": cleaned_query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 1,
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        with httpx.Client(timeout=4.0, follow_redirects=True) as client:
            response = client.get(NOMINATIM_URL, params=params, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ValueError("Location lookup failed. Please try again.") from exc

    payload = response.json()
    if not payload:
        raise ValueError("No location found for that query.")

    top = payload[0]
    return ResolvedLocation(
        query=cleaned_query,
        label=top.get("display_name", cleaned_query),
        latitude=float(top["lat"]),
        longitude=float(top["lon"]),
    )


def haversine_km(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> float:
    earth_radius_km = 6371.0

    d_lat = math.radians(dest_lat - origin_lat)
    d_lng = math.radians(dest_lng - origin_lng)
    lat1 = math.radians(origin_lat)
    lat2 = math.radians(dest_lat)

    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_km * c
