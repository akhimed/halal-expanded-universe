from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal

from pydantic import AnyUrl, BaseModel, EmailStr, Field


SearchProfileLiteral = Literal["balanced", "strict", "community_first"]
ReportTypeLiteral = Literal[
    "inaccurate_halal_status",
    "inaccurate_kosher_status",
    "allergen_risk",
    "alcohol_served",
    "outdated_info",
    "other",
]


class UserRead(BaseModel):
    id: int
    email: str
    display_name: str
    role: str
    created_at: datetime


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class FavoriteActionResponse(BaseModel):
    status: str
    restaurant_id: int


class FavoriteRestaurantSummary(BaseModel):
    id: int
    name: str
    description: str | None
    address: str | None
    latitude: float | None
    longitude: float | None


class FavoriteListResponse(BaseModel):
    favorites: List[FavoriteRestaurantSummary]


class CreateReportRequest(BaseModel):
    report_type: ReportTypeLiteral
    description: str | None = Field(default=None, max_length=2000)
    evidence_url: AnyUrl | None = None


class ReportResponse(BaseModel):
    id: int
    restaurant_id: int | None
    report_type: str | None
    description: str | None
    evidence_url: str | None
    status: str
    created_at: datetime


class ModerationReportItem(BaseModel):
    id: int
    user_id: int | None
    restaurant_id: int | None
    report_type: str | None
    description: str | None
    evidence_url: str | None
    status: str
    created_at: datetime


class ModerationReportsResponse(BaseModel):
    reports: List[ModerationReportItem]
    pagination: dict[str, int] | None = None


class UpdateReportStatusRequest(BaseModel):
    status: Literal["open", "under_review", "resolved", "rejected"]
    note: str | None = None


class CreateOwnerClaimRequest(BaseModel):
    notes: str | None = None


class OwnerClaimStatusResponse(BaseModel):
    id: int
    user_id: int
    restaurant_id: int
    status: Literal["pending", "approved", "rejected"]
    notes: str | None
    created_at: datetime


class OwnerClaimDashboardItem(BaseModel):
    id: int
    status: Literal["pending", "approved", "rejected"]
    notes: str | None
    created_at: datetime
    restaurant: FavoriteRestaurantSummary


class OwnerDashboardResponse(BaseModel):
    claims: List[OwnerClaimDashboardItem]


class ModerationOwnerClaimItem(BaseModel):
    id: int
    user_id: int
    restaurant_id: int
    status: str
    notes: str | None
    created_at: datetime


class ModerationOwnerClaimsResponse(BaseModel):
    claims: List[ModerationOwnerClaimItem]
    pagination: dict[str, int] | None = None


class ModerateOwnerClaimRequest(BaseModel):
    status: Literal["approved", "rejected"]
    note: str | None = None


class VerificationDocumentResponse(BaseModel):
    id: int
    owner_user_id: int
    restaurant_id: int
    owner_claim_id: int
    document_type: str
    original_filename: str | None
    storage_path: str | None
    mime_type: str | None
    notes: str | None
    status: str
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    created_at: datetime


class OwnerVerificationDocumentsResponse(BaseModel):
    documents: List[VerificationDocumentResponse]
    pagination: dict[str, int] | None = None


class ModerateVerificationDocumentRequest(BaseModel):
    status: Literal["approved", "rejected"]
    note: str | None = None


class TrustEventResponse(BaseModel):
    id: int
    restaurant_id: int
    event_type: str
    delta: float
    actor_user_id: int | None
    metadata_json: str | None
    created_at: datetime


class TrustEventsListResponse(BaseModel):
    events: List[TrustEventResponse]


class RestaurantTagRead(BaseModel):
    tag: str


class RestaurantAllergenInfoRead(BaseModel):
    allergen: str
    present: bool


class RestaurantRead(BaseModel):
    id: int
    name: str
    description: str | None
    address: str | None
    latitude: float | None
    longitude: float | None
    certification_score: float
    community_verification_score: float
    recency_score: float
    trust_breakdown: dict[str, Any] | None = None
    tags: List[RestaurantTagRead] = Field(default_factory=list)
    allergen_info: List[RestaurantAllergenInfoRead] = Field(default_factory=list)


class GroupParticipantSchema(BaseModel):
    participant_name: str = Field(min_length=1, max_length=120)
    required_tags: List[str] = Field(default_factory=list)
    excluded_allergens: List[str] = Field(default_factory=list)
    profile: SearchProfileLiteral = "balanced"


class SearchRequestSchema(BaseModel):
    required_tags: List[str] = Field(default_factory=list)
    excluded_allergens: List[str] = Field(default_factory=list)
    profile: SearchProfileLiteral = "balanced"
    group_mode: bool = False
    participants: List[GroupParticipantSchema] = Field(default_factory=list)
    location_query: str | None = Field(default=None, max_length=200)
    location_latitude: float | None = None
    location_longitude: float | None = None


class RestaurantSummarySchema(BaseModel):
    id: int
    name: str
    description: str | None
    address: str | None
    latitude: float | None
    longitude: float | None


class ExcludedAllergenStatusSchema(BaseModel):
    allergen: str
    present: bool


class ParticipantSatisfactionSchema(BaseModel):
    participant_name: str
    required_tags_satisfied: bool
    missing_required_tags: List[str] = Field(default_factory=list)
    excluded_allergens_satisfied: bool
    conflicting_allergens: List[str] = Field(default_factory=list)
    profile: str
    participant_fit_score: float


class SearchResultSchema(BaseModel):
    restaurant: RestaurantSummarySchema
    matched_tags: List[str]
    excluded_allergen_status: List[ExcludedAllergenStatusSchema]
    trust_score: float
    distance_km: float | None = None
    trust_level: str
    trust_caveats: List[str] = Field(default_factory=list)
    group_fit_score: float | None = None
    participant_satisfaction: List[ParticipantSatisfactionSchema] = Field(default_factory=list)
    explanation: str
    full_explanation: str


class SearchLocationSchema(BaseModel):
    query: str
    label: str
    latitude: float
    longitude: float


class SearchResponseSchema(BaseModel):
    results: List[SearchResultSchema]
    search_location: SearchLocationSchema | None = None
