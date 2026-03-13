from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models import Restaurant, RestaurantImportSource, User
from backend.app.services.ingestion.models import IngestionRequest, ProviderPlaceRecord
from backend.app.services.ingestion.provider_base import PlaceIngestionProvider
from backend.app.services.ingestion.service import RestaurantIngestionService


class StubProvider(PlaceIngestionProvider):
    source_name = "stub"

    def __init__(self, records: list[ProviderPlaceRecord]):
        self._records = records

    def fetch_places(self, request: IngestionRequest):
        return self._records


@pytest.fixture()
def db_session(tmp_path):
    db_file = tmp_path / "test_ingest.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False}, future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        yield db


@pytest.fixture()
def client(tmp_path):
    db_file = tmp_path / "test_ingest_api.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False}, future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    test_client.testing_session_local = TestingSessionLocal
    yield test_client
    app.dependency_overrides.clear()


def test_ingestion_service_deduplicates_source_ids(db_session):
    provider_records = [
        ProviderPlaceRecord(
            source_name="osm_overpass",
            source_id="node/100",
            name="Spice Route",
            address="10 Main St, Test City",
            latitude=43.1,
            longitude=-79.2,
            raw_payload={"id": 100},
            freshness_at=datetime.utcnow(),
        ),
        ProviderPlaceRecord(
            source_name="osm_overpass",
            source_id="node/100",
            name="Spice Route",
            address="10 Main St, Test City",
            latitude=43.1,
            longitude=-79.2,
            raw_payload={"id": 100, "version": 2},
            freshness_at=datetime.utcnow(),
        ),
    ]
    service = RestaurantIngestionService(providers={"stub": StubProvider(provider_records)})

    result = service.run_import(db_session, "stub", request=IngestionRequest(mode="city", query="Test"))

    restaurant_count = db_session.scalar(select(func.count()).select_from(Restaurant))
    source_count = db_session.scalar(select(func.count()).select_from(RestaurantImportSource))
    assert result.created_count == 1
    assert result.updated_count == 1
    assert restaurant_count == 1
    assert source_count == 1


def _register_and_login(client: TestClient, email: str, role: str = "admin") -> str:
    client.post(
        "/auth/register",
        json={"email": email, "display_name": "Importer", "password": "ImportPass123"},
    )

    with client.testing_session_local() as db:
        user = db.scalars(select(User).where(User.email == email)).first()
        assert user is not None
        user.role = role
        db.commit()

    login = client.post("/auth/login", json={"email": email, "password": "ImportPass123"})
    return login.json()["access_token"]


def test_admin_import_endpoint_runs_ingestion(client: TestClient):
    from backend.app.services.ingestion import service as ingestion_service

    provider_records = [
        ProviderPlaceRecord(
            source_name="osm_overpass",
            source_id="node/501",
            name="Atlas Kitchen",
            address="55 Atlas Rd",
            latitude=40.0,
            longitude=-73.0,
            raw_payload={"id": 501},
        )
    ]
    original_service = ingestion_service._service_singleton
    ingestion_service._service_singleton = RestaurantIngestionService(providers={"osm": StubProvider(provider_records)})

    try:
        token = _register_and_login(client, "admin-import@example.com", role="admin")
        response = client.post(
            "/admin/import/restaurants",
            headers={"Authorization": f"Bearer {token}"},
            json={"provider": "osm", "mode": "city", "query": "New York"},
        )
    finally:
        ingestion_service._service_singleton = original_service

    assert response.status_code == 200
    body = response.json()
    assert body["created_count"] == 1
    assert body["updated_count"] == 0
    assert len(body["imported_restaurant_ids"]) == 1


def test_admin_import_endpoint_requires_admin_role(client: TestClient):
    token = _register_and_login(client, "user-import@example.com", role="user")
    response = client.post(
        "/admin/import/restaurants",
        headers={"Authorization": f"Bearer {token}"},
        json={"provider": "osm", "mode": "city", "query": "Toronto"},
    )

    assert response.status_code == 403
