from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.api.schemas import (
    AdminImportRequest,
    AdminImportResponse,
    AdminProvidersResponse,
    AuthTokenResponse,
    CreateOwnerClaimRequest,
    CreateReportRequest,
    FavoriteActionResponse,
    FavoriteListResponse,
    FavoriteRestaurantSummary,
    LoginRequest,
    ModerateOwnerClaimRequest,
    ModerateVerificationDocumentRequest,
    ModerationOwnerClaimItem,
    ModerationOwnerClaimsResponse,
    ModerationReportItem,
    ModerationReportsResponse,
    OwnerClaimDashboardItem,
    OwnerClaimStatusResponse,
    OwnerDashboardResponse,
    OwnerVerificationDocumentsResponse,
    RegisterRequest,
    ReportResponse,
    RestaurantRead,
    SearchRequestSchema,
    SearchResponseSchema,
    SearchResultSchema,
    SearchLocationSchema,
    TrustEventResponse,
    TrustEventsListResponse,
    UpdateReportStatusRequest,
    UserRead,
    VerificationDocumentResponse,
)
from backend.app.db.session import get_db
from backend.app.models import OwnerClaim, TrustEvent, User
from backend.app.services.auth_service import login_user, register_user
from backend.app.services.favorite_service import add_favorite, list_favorite_restaurants, remove_favorite
from backend.app.services.moderation_service import (
    list_owner_claims as list_owner_claims_for_moderation,
    list_reports,
    moderate_owner_claim,
    update_report_status,
)
from backend.app.services.owner_claim_service import list_owner_claims, submit_owner_claim
from backend.app.services.report_service import create_report
from backend.app.services.location_service import ResolvedLocation, resolve_location
from backend.app.services.ingestion import available_providers, run_ingestion_job
from backend.app.services.restaurant_service import (
    get_restaurant_by_id,
    list_restaurants,
    search_restaurants,
)
from backend.app.services.rate_limit import auth_rate_limit, report_rate_limit
from backend.app.services.trust_scoring import PROFILES, trust_breakdown
from backend.app.services.verification_service import (
    list_owner_documents,
    list_verification_documents,
    moderate_verification_document,
    submit_verification_document_with_storage,
)

router = APIRouter()


def _user_read_model(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        created_at=user.created_at,
    )


def _verification_doc_model(doc) -> VerificationDocumentResponse:
    return VerificationDocumentResponse(
        id=doc.id,
        owner_user_id=doc.owner_user_id,
        restaurant_id=doc.restaurant_id,
        owner_claim_id=doc.owner_claim_id,
        document_type=doc.document_type,
        original_filename=doc.original_filename,
        storage_path=doc.storage_path,
        mime_type=doc.mime_type,
        notes=doc.notes,
        status=doc.status,
        reviewed_by_user_id=doc.reviewed_by_user_id,
        reviewed_at=doc.reviewed_at,
        created_at=doc.created_at,
    )


@router.get("/health")
def health() -> dict:
    return {"ok": True, "service": "backend"}


@router.get("/admin/import/providers", response_model=AdminProvidersResponse)
def list_import_providers(
    admin: User = Depends(require_roles("admin")),
) -> AdminProvidersResponse:
    _ = admin
    return AdminProvidersResponse(providers=list(available_providers()))


@router.post("/admin/import/restaurants", response_model=AdminImportResponse)
def import_restaurants(
    payload: AdminImportRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
) -> AdminImportResponse:
    _ = admin
    try:
        result = run_ingestion_job(
            db,
            provider=payload.provider,
            mode=payload.mode,
            query=payload.query,
            min_lat=payload.min_lat,
            min_lon=payload.min_lon,
            max_lat=payload.max_lat,
            max_lon=payload.max_lon,
            latitude=payload.latitude,
            longitude=payload.longitude,
            radius_km=payload.radius_km,
            country_code=payload.country_code,
            limit=payload.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AdminImportResponse(
        provider=payload.provider,
        mode=payload.mode,
        created_count=result.created_count,
        updated_count=result.updated_count,
        skipped_count=result.skipped_count,
        imported_restaurant_ids=result.imported_restaurant_ids,
    )


@router.post("/auth/register", response_model=AuthTokenResponse)
def register(
    payload: RegisterRequest,
    _rate_limited: None = Depends(auth_rate_limit),
    db: Session = Depends(get_db),
) -> AuthTokenResponse:
    _ = _rate_limited
    user = register_user(db, payload.email, payload.display_name, payload.password)
    _user, token = login_user(db, payload.email, payload.password)
    return AuthTokenResponse(access_token=token, user=_user_read_model(user))


@router.post("/auth/login", response_model=AuthTokenResponse)
def login(
    payload: LoginRequest,
    _rate_limited: None = Depends(auth_rate_limit),
    db: Session = Depends(get_db),
) -> AuthTokenResponse:
    _ = _rate_limited
    user, token = login_user(db, payload.email, payload.password)
    return AuthTokenResponse(access_token=token, user=_user_read_model(user))


@router.get("/auth/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return _user_read_model(current_user)


@router.get("/favorites", response_model=FavoriteListResponse)
def favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FavoriteListResponse:
    items = list_favorite_restaurants(db, current_user.id)
    return FavoriteListResponse(
        favorites=[
            FavoriteRestaurantSummary(
                id=item.id,
                name=item.name,
                description=item.description,
                address=item.address,
                latitude=item.latitude,
                longitude=item.longitude,
            )
            for item in items
        ]
    )


@router.post("/favorites/{restaurant_id}", response_model=FavoriteActionResponse)
def add_favorite_endpoint(
    restaurant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FavoriteActionResponse:
    restaurant = get_restaurant_by_id(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    add_favorite(db, current_user.id, restaurant_id)
    return FavoriteActionResponse(status="saved", restaurant_id=restaurant_id)


@router.delete("/favorites/{restaurant_id}", response_model=FavoriteActionResponse)
def remove_favorite_endpoint(
    restaurant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FavoriteActionResponse:
    removed = remove_favorite(db, current_user.id, restaurant_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Favorite not found")

    return FavoriteActionResponse(status="removed", restaurant_id=restaurant_id)


@router.post("/restaurants/{restaurant_id}/claims", response_model=OwnerClaimStatusResponse)
def submit_restaurant_claim(
    restaurant_id: int,
    payload: CreateOwnerClaimRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OwnerClaimStatusResponse:
    restaurant = get_restaurant_by_id(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    claim = submit_owner_claim(
        db,
        current_user=current_user,
        restaurant=restaurant,
        notes=payload.notes,
    )
    return OwnerClaimStatusResponse(
        id=claim.id,
        user_id=claim.user_id,
        restaurant_id=claim.restaurant_id,
        status=claim.status,
        notes=claim.notes,
        created_at=claim.created_at,
    )


@router.get("/owner/dashboard", response_model=OwnerDashboardResponse)
def owner_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OwnerDashboardResponse:
    claims = list_owner_claims(db, current_user.id)
    return OwnerDashboardResponse(
        claims=[
            OwnerClaimDashboardItem(
                id=claim.id,
                status=claim.status,
                notes=claim.notes,
                created_at=claim.created_at,
                restaurant=FavoriteRestaurantSummary(
                    id=claim.restaurant.id,
                    name=claim.restaurant.name,
                    description=claim.restaurant.description,
                    address=claim.restaurant.address,
                    latitude=claim.restaurant.latitude,
                    longitude=claim.restaurant.longitude,
                ),
            )
            for claim in claims
        ]
    )


@router.get("/owner/verification-documents", response_model=OwnerVerificationDocumentsResponse)
def owner_verification_documents(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OwnerVerificationDocumentsResponse:
    docs = list_owner_documents(db, current_user.id)
    total = len(docs)
    page_docs = docs[offset : offset + limit]
    return OwnerVerificationDocumentsResponse(
        documents=[_verification_doc_model(doc) for doc in page_docs],
        pagination={"total": total, "limit": limit, "offset": offset},
    )


@router.post("/owner/claims/{claim_id}/verification-documents", response_model=VerificationDocumentResponse)
async def submit_verification_document(
    claim_id: int,
    document_type: str = Form(...),
    notes: str | None = Form(None),
    metadata_filename: str | None = Form(None),
    metadata_mime_type: str | None = Form(None),
    file: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VerificationDocumentResponse:
    claim = db.scalars(select(OwnerClaim).where(OwnerClaim.id == claim_id)).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Owner claim not found")

    doc = await submit_verification_document_with_storage(
        db,
        current_user=current_user,
        claim=claim,
        document_type=document_type,
        notes=notes,
        file=file,
        metadata_filename=metadata_filename,
        metadata_mime_type=metadata_mime_type,
    )
    return _verification_doc_model(doc)


@router.get("/moderation/reports", response_model=ModerationReportsResponse)
def moderation_reports(
    status: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    moderator: User = Depends(require_roles("moderator", "admin")),
) -> ModerationReportsResponse:
    _ = moderator
    rows = list_reports(db, status=status)
    total = len(rows)
    page_rows = rows[offset : offset + limit]
    return ModerationReportsResponse(
        reports=[
            ModerationReportItem(
                id=row.id,
                user_id=row.user_id,
                restaurant_id=row.restaurant_id,
                report_type=row.report_type,
                description=row.description,
                evidence_url=row.evidence_url,
                status=row.status,
                created_at=row.created_at,
            )
            for row in page_rows
        ],
        pagination={"total": total, "limit": limit, "offset": offset},
    )


@router.patch("/moderation/reports/{report_id}", response_model=ModerationReportItem)
def moderation_update_report(
    report_id: int,
    payload: UpdateReportStatusRequest,
    db: Session = Depends(get_db),
    moderator: User = Depends(require_roles("moderator", "admin")),
) -> ModerationReportItem:
    row = update_report_status(db, moderator=moderator, report_id=report_id, status=payload.status, note=payload.note)
    return ModerationReportItem(
        id=row.id,
        user_id=row.user_id,
        restaurant_id=row.restaurant_id,
        report_type=row.report_type,
        description=row.description,
        evidence_url=row.evidence_url,
        status=row.status,
        created_at=row.created_at,
    )


@router.get("/moderation/owner-claims", response_model=ModerationOwnerClaimsResponse)
def moderation_owner_claims(
    status: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    moderator: User = Depends(require_roles("moderator", "admin")),
) -> ModerationOwnerClaimsResponse:
    _ = moderator
    rows = list_owner_claims_for_moderation(db, status=status)
    total = len(rows)
    page_rows = rows[offset : offset + limit]
    return ModerationOwnerClaimsResponse(
        claims=[
            ModerationOwnerClaimItem(
                id=row.id,
                user_id=row.user_id,
                restaurant_id=row.restaurant_id,
                status=row.status,
                notes=row.notes,
                created_at=row.created_at,
            )
            for row in page_rows
        ],
        pagination={"total": total, "limit": limit, "offset": offset},
    )


@router.patch("/moderation/owner-claims/{claim_id}", response_model=ModerationOwnerClaimItem)
def moderation_update_owner_claim(
    claim_id: int,
    payload: ModerateOwnerClaimRequest,
    db: Session = Depends(get_db),
    moderator: User = Depends(require_roles("moderator", "admin")),
) -> ModerationOwnerClaimItem:
    row = moderate_owner_claim(db, moderator=moderator, claim_id=claim_id, status=payload.status, note=payload.note)
    return ModerationOwnerClaimItem(
        id=row.id,
        user_id=row.user_id,
        restaurant_id=row.restaurant_id,
        status=row.status,
        notes=row.notes,
        created_at=row.created_at,
    )


@router.get("/moderation/verification-documents", response_model=OwnerVerificationDocumentsResponse)
def moderation_verification_documents(
    status: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    moderator: User = Depends(require_roles("moderator", "admin")),
) -> OwnerVerificationDocumentsResponse:
    _ = moderator
    docs = list_verification_documents(db, status=status)
    total = len(docs)
    page_docs = docs[offset : offset + limit]
    return OwnerVerificationDocumentsResponse(
        documents=[_verification_doc_model(doc) for doc in page_docs],
        pagination={"total": total, "limit": limit, "offset": offset},
    )


@router.patch("/moderation/verification-documents/{document_id}", response_model=VerificationDocumentResponse)
def moderation_update_verification_document(
    document_id: int,
    payload: ModerateVerificationDocumentRequest,
    db: Session = Depends(get_db),
    moderator: User = Depends(require_roles("moderator", "admin")),
) -> VerificationDocumentResponse:
    doc = moderate_verification_document(
        db,
        moderator=moderator,
        document_id=document_id,
        status=payload.status,
        note=payload.note,
    )
    return _verification_doc_model(doc)


@router.post("/restaurants/{restaurant_id}/reports", response_model=ReportResponse)
def create_restaurant_report(
    restaurant_id: int,
    payload: CreateReportRequest,
    current_user: User = Depends(get_current_user),
    _rate_limited: None = Depends(report_rate_limit),
    db: Session = Depends(get_db),
) -> ReportResponse:
    _ = _rate_limited
    restaurant = get_restaurant_by_id(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    report = create_report(
        db,
        current_user=current_user,
        restaurant_id=restaurant_id,
        report_type=payload.report_type,
        description=payload.description,
        evidence_url=str(payload.evidence_url) if payload.evidence_url is not None else None,
    )

    return ReportResponse(
        id=report.id,
        restaurant_id=report.restaurant_id,
        report_type=report.report_type,
        description=report.description,
        evidence_url=report.evidence_url,
        status=report.status,
        created_at=report.created_at,
    )


@router.get("/restaurants/{restaurant_id}/trust-events", response_model=TrustEventsListResponse)
def restaurant_trust_events(restaurant_id: int, db: Session = Depends(get_db)) -> TrustEventsListResponse:
    events = list(
        db.scalars(select(TrustEvent).where(TrustEvent.restaurant_id == restaurant_id).order_by(TrustEvent.created_at.desc())).all()
    )
    return TrustEventsListResponse(
        events=[
            TrustEventResponse(
                id=e.id,
                restaurant_id=e.restaurant_id,
                event_type=e.event_type,
                delta=e.delta,
                actor_user_id=e.actor_user_id,
                metadata_json=e.metadata_json,
                created_at=e.created_at,
            )
            for e in events
        ]
    )


@router.get("/restaurants", response_model=list[RestaurantRead])
def restaurants(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[RestaurantRead]:
    rows = list_restaurants(db)
    rows = rows[offset : offset + limit]
    profile = PROFILES["balanced"]
    return [
        RestaurantRead(
            id=row.id,
            name=row.name,
            description=row.description,
            address=row.address,
            latitude=row.latitude,
            longitude=row.longitude,
            certification_score=row.certification_score,
            community_verification_score=row.community_verification_score,
            recency_score=row.recency_score,
            trust_breakdown=trust_breakdown(db, row, profile),
            tags=[{"tag": tag.tag} for tag in row.tags],
            allergen_info=[{"allergen": info.allergen, "present": info.present} for info in row.allergen_info],
        )
        for row in rows
    ]


@router.get("/restaurants/{restaurant_id}", response_model=RestaurantRead)
def restaurant_detail(restaurant_id: int, db: Session = Depends(get_db)) -> RestaurantRead:
    row = get_restaurant_by_id(db, restaurant_id)
    if not row:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return RestaurantRead(
        id=row.id,
        name=row.name,
        description=row.description,
        address=row.address,
        latitude=row.latitude,
        longitude=row.longitude,
        certification_score=row.certification_score,
        community_verification_score=row.community_verification_score,
        recency_score=row.recency_score,
        trust_breakdown=trust_breakdown(db, row, PROFILES["balanced"]),
        tags=[{"tag": tag.tag} for tag in row.tags],
        allergen_info=[{"allergen": info.allergen, "present": info.present} for info in row.allergen_info],
    )


@router.post("/search", response_model=SearchResponseSchema)
def search(payload: SearchRequestSchema, db: Session = Depends(get_db)) -> SearchResponseSchema:
    try:
        search_location: ResolvedLocation | None = None
        if payload.location_latitude is not None and payload.location_longitude is not None:
            search_location = ResolvedLocation(
                query=payload.location_query or "coordinate",
                label=payload.location_query or "Custom location",
                latitude=payload.location_latitude,
                longitude=payload.location_longitude,
            )
        elif payload.location_query:
            search_location = resolve_location(payload.location_query)

        results = search_restaurants(
            db,
            required_tags=set(payload.required_tags),
            excluded_allergens=set(payload.excluded_allergens),
            profile_name=payload.profile,
            group_mode=payload.group_mode,
            participants=payload.participants,
            location=search_location,
        )
        location_payload = None
        if search_location is not None:
            location_payload = SearchLocationSchema(
                query=search_location.query,
                label=search_location.label,
                latitude=search_location.latitude,
                longitude=search_location.longitude,
            )
        return SearchResponseSchema(results=[SearchResultSchema(**item) for item in results], search_location=location_payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
