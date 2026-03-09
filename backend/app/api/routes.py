from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.dietary_app.engine import search_venues
from src.dietary_app.models import DietaryTag, SearchRequest
from src.dietary_app.sample_data import SAMPLE_VENUES

from .schemas import SearchRequestSchema, SearchResponseSchema, SearchResultSchema

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"ok": True, "service": "backend"}


@router.post("/api/v1/search", response_model=SearchResponseSchema)
def search(payload: SearchRequestSchema) -> SearchResponseSchema:
    try:
        request = SearchRequest(
            required_tags={DietaryTag(tag) for tag in payload.required_tags},
            excluded_allergens=set(payload.excluded_allergens),
        )
        results = search_venues(SAMPLE_VENUES, request, profile_name=payload.profile)
        return SearchResponseSchema(
            results=[
                SearchResultSchema(
                    id=item.venue.id,
                    name=item.venue.name,
                    supported_tags=sorted(tag.value for tag in item.venue.supported_tags),
                    allergens_present=sorted(item.venue.allergens_present),
                    trust_score=item.trust_score,
                    reasons=item.reasons,
                )
                for item in results
            ]
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
