from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class SearchRequestSchema(BaseModel):
    required_tags: List[str] = Field(default_factory=list)
    excluded_allergens: List[str] = Field(default_factory=list)
    profile: str = "balanced"


class SearchResultSchema(BaseModel):
    id: str
    name: str
    supported_tags: List[str]
    allergens_present: List[str]
    trust_score: float
    reasons: List[str]


class SearchResponseSchema(BaseModel):
    results: List[SearchResultSchema]
