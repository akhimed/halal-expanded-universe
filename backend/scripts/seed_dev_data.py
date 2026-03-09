from __future__ import annotations

from sqlalchemy import select

from backend.app.db.session import SessionLocal
from backend.app.models import Restaurant, RestaurantAllergenInfo, RestaurantTag, User
from backend.app.services.security import hash_password


def seed() -> None:
    with SessionLocal() as db:
        existing = db.scalar(select(Restaurant.id).limit(1))
        if existing:
            print("Seed skipped: restaurants already exist")
            return

        user = User(
            email="demo@example.com",
            display_name="Demo User",
            password_hash=hash_password("DemoPass123"),
            role="admin",
        )

        r1 = Restaurant(
            name="Saffron Garden",
            description="Halal-friendly Indian restaurant",
            address="123 Main St",
            latitude=43.6532,
            longitude=-79.3832,
            certification_score=0.95,
            community_verification_score=0.80,
            recency_score=0.90,
        )
        r1.tags = [RestaurantTag(tag="halal"), RestaurantTag(tag="vegetarian")]
        r1.allergen_info = [RestaurantAllergenInfo(allergen="dairy", present=True)]

        r2 = Restaurant(
            name="Green Karma Kitchen",
            description="Plant-forward Hindu vegetarian menu",
            address="22 Oak Ave",
            latitude=43.6712,
            longitude=-79.3611,
            certification_score=0.70,
            community_verification_score=0.90,
            recency_score=0.88,
        )
        r2.tags = [
            RestaurantTag(tag="hindu_vegetarian"),
            RestaurantTag(tag="vegan"),
            RestaurantTag(tag="vegetarian"),
        ]
        r2.allergen_info = [RestaurantAllergenInfo(allergen="nuts", present=True)]

        r3 = Restaurant(
            name="Olive & Fig Kosher Bistro",
            description="Kosher-certified Mediterranean",
            address="9 Sunset Blvd",
            latitude=43.6426,
            longitude=-79.3871,
            certification_score=0.92,
            community_verification_score=0.85,
            recency_score=0.80,
        )
        r3.tags = [RestaurantTag(tag="kosher"), RestaurantTag(tag="vegetarian")]
        r3.allergen_info = [RestaurantAllergenInfo(allergen="gluten", present=True)]

        db.add_all([user, r1, r2, r3])
        db.commit()
        print("Seeded users/restaurants")


if __name__ == "__main__":
    seed()
