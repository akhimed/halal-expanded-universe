from __future__ import annotations

import os
import sqlite3
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models import Restaurant, RestaurantAllergenInfo, RestaurantTag


@pytest.fixture()
def client(tmp_path):
    db_file = tmp_path / "test_api.db"
    database_url = f"sqlite:///{db_file}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False}, future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        r1 = Restaurant(
            name="Halal House",
            certification_score=0.95,
            community_verification_score=0.80,
            recency_score=0.55,
            latitude=43.6510,
            longitude=-79.3470,
        )
        r1.tags = [RestaurantTag(tag="halal"), RestaurantTag(tag="vegetarian")]
        r1.allergen_info = [RestaurantAllergenInfo(allergen="dairy", present=True)]

        r2 = Restaurant(
            name="Vegan Valley",
            certification_score=0.70,
            community_verification_score=0.95,
            recency_score=0.90,
            latitude=43.7000,
            longitude=-79.4000,
        )
        r2.tags = [RestaurantTag(tag="vegan"), RestaurantTag(tag="hindu_vegetarian")]

        r3 = Restaurant(
            name="Balanced Bistro",
            certification_score=0.89,
            community_verification_score=0.75,
            recency_score=0.80,
            latitude=43.9000,
            longitude=-79.7000,
        )
        r3.tags = [RestaurantTag(tag="vegetarian")]

        db.add_all([r1, r2, r3])
        db.commit()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_restaurant_detail(client: TestClient):
    listing = client.get("/restaurants").json()
    restaurant_id = listing[0]["id"]

    response = client.get(f"/restaurants/{restaurant_id}")
    assert response.status_code == 200
    assert response.json()["id"] == restaurant_id


def test_allergen_exclusion(client: TestClient):
    response = client.post(
        "/search",
        json={
            "required_tags": ["halal"],
            "excluded_allergens": ["dairy"],
            "profile": "balanced",
        },
    )
    assert response.status_code == 200
    assert response.json()["results"] == []


def test_strict_vs_balanced_behavior(client: TestClient):
    balanced = client.post(
        "/search",
        json={"required_tags": ["vegan"], "excluded_allergens": [], "profile": "balanced"},
    )
    strict = client.post(
        "/search",
        json={"required_tags": ["vegan"], "excluded_allergens": [], "profile": "strict"},
    )

    assert balanced.status_code == 200
    assert strict.status_code == 200
    assert len(balanced.json()["results"]) == 1
    assert strict.json()["results"] == []


def test_trust_aware_ranking_and_explanation_presence(client: TestClient):
    response = client.post(
        "/search",
        json={"required_tags": ["vegetarian"], "excluded_allergens": [], "profile": "balanced"},
    )
    assert response.status_code == 200

    results = response.json()["results"]
    assert len(results) == 2
    assert results[0]["trust_score"] >= results[1]["trust_score"]
    assert results[0]["restaurant"]["name"] == "Balanced Bistro"
    assert isinstance(results[0]["explanation"], str) and len(results[0]["explanation"]) > 0
    assert len(results[0]["explanation"]) < len(results[0]["full_explanation"])
    assert results[0]["trust_level"] in {"high", "medium", "low"}


def test_search_response_shape(client: TestClient):
    response = client.post(
        "/search",
        json={
            "required_tags": ["vegan", "hindu_vegetarian"],
            "excluded_allergens": ["shellfish", "nuts"],
            "profile": "balanced",
        },
    )
    assert response.status_code == 200
    result = response.json()["results"][0]

    assert "restaurant" in result
    assert "matched_tags" in result
    assert "excluded_allergen_status" in result
    assert "trust_score" in result
    assert "trust_level" in result
    assert "trust_caveats" in result
    assert "explanation" in result
    assert "full_explanation" in result


def test_migration_and_seed_smoke(tmp_path: Path):
    db_file = tmp_path / "migration_seed.db"
    db_url = f"sqlite:///{db_file}"
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url

    subprocess.run(
        ["alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
        check=True,
        env=env,
    )
    subprocess.run(["python", "-m", "backend.scripts.seed_dev_data"], check=True, env=env)
    subprocess.run(["python", "-m", "backend.scripts.seed_dev_data"], check=True, env=env)

    with sqlite3.connect(db_file) as conn:
        restaurant_count = conn.execute("select count(*) from restaurants").fetchone()[0]
        user_count = conn.execute("select count(*) from users").fetchone()[0]

    assert restaurant_count == 10
    assert user_count == 2


def test_group_search_mixed_satisfaction(client: TestClient):
    response = client.post(
        "/search",
        json={
            "group_mode": True,
            "participants": [
                {
                    "participant_name": "Aisha",
                    "required_tags": ["halal"],
                    "excluded_allergens": ["dairy"],
                    "profile": "balanced",
                },
                {
                    "participant_name": "Eli",
                    "required_tags": ["vegan"],
                    "excluded_allergens": [],
                    "profile": "balanced",
                },
            ],
            "profile": "balanced",
        },
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) >= 1
    first = results[0]
    assert "participant_satisfaction" in first
    assert len(first["participant_satisfaction"]) == 2
    names = {item["participant_name"] for item in first["participant_satisfaction"]}
    assert names == {"Aisha", "Eli"}


def test_group_search_combined_ranking_prefers_better_group_fit(client: TestClient):
    response = client.post(
        "/search",
        json={
            "group_mode": True,
            "participants": [
                {
                    "participant_name": "Veg",
                    "required_tags": ["vegan"],
                    "excluded_allergens": [],
                    "profile": "balanced",
                },
                {
                    "participant_name": "Veg2",
                    "required_tags": ["vegetarian"],
                    "excluded_allergens": [],
                    "profile": "balanced",
                },
            ],
            "profile": "balanced",
        },
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) >= 2
    assert results[0]["group_fit_score"] >= results[1]["group_fit_score"]


def test_default_search_without_filters_returns_ranked_results(client: TestClient):
    response = client.post(
        "/search",
        json={"required_tags": [], "excluded_allergens": [], "profile": "balanced"},
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 3
    trust_scores = [item["trust_score"] for item in results]
    assert trust_scores == sorted(trust_scores, reverse=True)


def test_profile_refinement_changes_order_for_community_first(client: TestClient):
    balanced = client.post(
        "/search",
        json={"required_tags": [], "excluded_allergens": [], "profile": "balanced"},
    )
    community_first = client.post(
        "/search",
        json={"required_tags": [], "excluded_allergens": [], "profile": "community_first"},
    )
    assert balanced.status_code == 200
    assert community_first.status_code == 200

    balanced_top = balanced.json()["results"][0]["restaurant"]["name"]
    community_top = community_first.json()["results"][0]["restaurant"]["name"]
    assert community_top == "Vegan Valley"
    assert balanced_top != community_top


def test_group_search_uses_hard_satisfaction_as_tiebreaker(client: TestClient):
    response = client.post(
        "/search",
        json={
            "group_mode": True,
            "participants": [
                {
                    "participant_name": "Hana",
                    "required_tags": ["halal"],
                    "excluded_allergens": [],
                    "profile": "strict",
                },
                {
                    "participant_name": "Rami",
                    "required_tags": ["vegetarian"],
                    "excluded_allergens": [],
                    "profile": "balanced",
                },
            ],
            "profile": "balanced",
        },
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) >= 2
    assert results[0]["restaurant"]["name"] == "Halal House"
    assert "Group:" in results[0]["explanation"]
    assert "Group mode:" in results[0]["full_explanation"]


def test_trust_explanation_includes_level_and_caveats(client: TestClient):
    response = client.post(
        "/search",
        json={"required_tags": ["vegetarian"], "excluded_allergens": [], "profile": "balanced"},
    )
    assert response.status_code == 200
    result = response.json()["results"][0]

    assert result["trust_level"] in {"high", "medium", "low"}
    assert any("No moderator-approved owner verification documents" in item for item in result["trust_caveats"])
    assert "Computed trust score:" in result["full_explanation"]
    assert "Trust reflects certification" in result["full_explanation"]
    assert "Caveat:" in result["full_explanation"]


def test_search_with_location_query_resolves_and_returns_distance(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    from backend.app.services.location_service import ResolvedLocation

    def fake_resolve_location(query: str) -> ResolvedLocation:
        assert query == 'Toronto'
        return ResolvedLocation(query='Toronto', label='Toronto, Ontario, Canada', latitude=43.651, longitude=-79.347)

    monkeypatch.setattr('backend.app.api.routes.resolve_location', fake_resolve_location)

    response = client.post(
        '/search',
        json={
            'required_tags': [],
            'excluded_allergens': [],
            'profile': 'balanced',
            'location_query': 'Toronto',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['search_location']['label'] == 'Toronto, Ontario, Canada'
    assert all('distance_km' in item for item in payload['results'])
    assert payload['results'][0]['distance_km'] is not None


def test_distance_aware_ranking_prefers_nearby_when_location_provided(client: TestClient):
    response = client.post(
        '/search',
        json={
            'required_tags': [],
            'excluded_allergens': [],
            'profile': 'balanced',
            'location_latitude': 43.651,
            'location_longitude': -79.347,
        },
    )

    assert response.status_code == 200
    results = response.json()['results']
    assert len(results) == 3
    assert results[0]['restaurant']['name'] == 'Halal House'
    assert results[0]['distance_km'] <= results[1]['distance_km']
