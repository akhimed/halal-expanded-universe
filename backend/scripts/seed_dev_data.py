from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from backend.app.db.session import SessionLocal
from backend.app.models import Restaurant, RestaurantAllergenInfo, RestaurantTag, User
from backend.app.services.security import hash_password


@dataclass(frozen=True)
class RestaurantSeed:
    name: str
    description: str
    address: str
    latitude: float
    longitude: float
    certification_score: float
    community_verification_score: float
    recency_score: float
    tags: tuple[str, ...]
    allergens_present: tuple[str, ...]


DEMO_USERS = [
    {
        "email": "demo@example.com",
        "display_name": "Demo Admin",
        "password": "DemoPass123",
        "role": "admin",
    },
    {
        "email": "community_mod@example.com",
        "display_name": "Community Moderator",
        "password": "DemoPass123",
        "role": "moderator",
    },
]

RESTAURANT_SEEDS: tuple[RestaurantSeed, ...] = (
    RestaurantSeed(
        name="Saffron Garden",
        description="Halal-focused Indian kitchen with clearly labeled vegetarian dishes.",
        address="123 Main St",
        latitude=43.6532,
        longitude=-79.3832,
        certification_score=0.97,
        community_verification_score=0.84,
        recency_score=0.93,
        tags=("halal", "vegetarian"),
        allergens_present=("dairy",),
    ),
    RestaurantSeed(
        name="Olive & Fig Kosher Bistro",
        description="Kosher-certified Mediterranean dining with fish and vegetarian mezze.",
        address="9 Sunset Blvd",
        latitude=43.6426,
        longitude=-79.3871,
        certification_score=0.94,
        community_verification_score=0.86,
        recency_score=0.83,
        tags=("kosher", "vegetarian"),
        allergens_present=("gluten", "sesame"),
    ),
    RestaurantSeed(
        name="Green Karma Kitchen",
        description="Strict vegetarian and vegan menu inspired by Hindu dietary practices.",
        address="22 Oak Ave",
        latitude=43.6712,
        longitude=-79.3611,
        certification_score=0.76,
        community_verification_score=0.93,
        recency_score=0.9,
        tags=("hindu_vegetarian", "vegan", "vegetarian"),
        allergens_present=("nuts", "soy"),
    ),
    RestaurantSeed(
        name="Cedar & Crescent Grill",
        description="Mixed grill with a separate halal-certified prep line and non-halal menu section.",
        address="450 Harbour Rd",
        latitude=43.6468,
        longitude=-79.3716,
        certification_score=0.71,
        community_verification_score=0.67,
        recency_score=0.74,
        tags=("halal",),
        allergens_present=("dairy", "egg", "gluten"),
    ),
    RestaurantSeed(
        name="Plant & Pulse Collective",
        description="Community-loved vegan cafe with rotating seasonal bowls.",
        address="18 Willow Lane",
        latitude=43.6594,
        longitude=-79.4012,
        certification_score=0.63,
        community_verification_score=0.95,
        recency_score=0.89,
        tags=("vegan", "vegetarian"),
        allergens_present=("nuts", "sesame", "soy"),
    ),
    RestaurantSeed(
        name="Shalom & Spice Market",
        description="Kosher deli and grocery hybrid; strong certification, fewer recent reviews.",
        address="77 Bayview Crescent",
        latitude=43.6893,
        longitude=-79.3958,
        certification_score=0.91,
        community_verification_score=0.61,
        recency_score=0.46,
        tags=("kosher",),
        allergens_present=("gluten", "soy"),
    ),
    RestaurantSeed(
        name="Harvest Table Bistro",
        description="Vegetarian-leaning neighborhood spot with optional seafood add-ons.",
        address="510 Queen St W",
        latitude=43.6487,
        longitude=-79.3982,
        certification_score=0.58,
        community_verification_score=0.73,
        recency_score=0.82,
        tags=("vegetarian",),
        allergens_present=("shellfish", "dairy", "egg"),
    ),
    RestaurantSeed(
        name="Unity Food Hall",
        description="Multi-concept food hall listing mixed halal, kosher, vegan, and standard vendors.",
        address="201 Front St E",
        latitude=43.6491,
        longitude=-79.3685,
        certification_score=0.66,
        community_verification_score=0.64,
        recency_score=0.78,
        tags=("halal", "kosher", "vegan", "vegetarian"),
        allergens_present=("dairy", "egg", "gluten", "nuts", "shellfish", "sesame", "soy"),
    ),
    RestaurantSeed(
        name="Amber Lantern Eatery",
        description="Edge case: pending paperwork claims halal service but certification cannot be confirmed.",
        address="11 Riverbend Dr",
        latitude=43.7012,
        longitude=-79.3551,
        certification_score=0.22,
        community_verification_score=0.79,
        recency_score=0.91,
        tags=("halal",),
        allergens_present=("dairy",),
    ),
    RestaurantSeed(
        name="Quiet Corner Cafe",
        description="Edge case: sparse listing with incomplete trust signals and limited reporting history.",
        address="315 College St",
        latitude=43.6573,
        longitude=-79.4071,
        certification_score=0.15,
        community_verification_score=0.18,
        recency_score=0.12,
        tags=("vegetarian",),
        allergens_present=(),
    ),
    RestaurantSeed(
        name="Noor Express Shawarma",
        description="Halal-certified quick-service counter with late-night hours and clearly labeled sauces.",
        address="88 Dundas St E",
        latitude=43.6579,
        longitude=-79.3785,
        certification_score=0.92,
        community_verification_score=0.81,
        recency_score=0.88,
        tags=("halal",),
        allergens_present=("dairy", "sesame"),
    ),
    RestaurantSeed(
        name="Beth Din Bakery Cafe",
        description="Kosher bakery cafe serving dairy meals, fish specials, and packaged baked goods.",
        address="402 St Clair Ave W",
        latitude=43.6846,
        longitude=-79.4183,
        certification_score=0.9,
        community_verification_score=0.69,
        recency_score=0.71,
        tags=("kosher", "vegetarian"),
        allergens_present=("dairy", "egg", "gluten", "nuts"),
    ),
    RestaurantSeed(
        name="Root & Ritual Vegan Lab",
        description="Experimental vegan tasting menu with fermentation-heavy dishes and rotating pop-up chefs.",
        address="67 Ossington Ave",
        latitude=43.6465,
        longitude=-79.4193,
        certification_score=0.52,
        community_verification_score=0.94,
        recency_score=0.92,
        tags=("vegan", "vegetarian"),
        allergens_present=("nuts", "soy"),
    ),
    RestaurantSeed(
        name="Meadow Spoon Diner",
        description="Vegetarian comfort-food diner with optional vegan substitutions and kid-friendly menu sections.",
        address="245 Danforth Ave",
        latitude=43.6774,
        longitude=-79.3516,
        certification_score=0.55,
        community_verification_score=0.74,
        recency_score=0.77,
        tags=("vegetarian",),
        allergens_present=("dairy", "egg", "gluten", "soy"),
    ),
    RestaurantSeed(
        name="Crossroads Fire Grill",
        description="Edge case: mixed kitchen markets halal options, but shared prep claims create conflicting community feedback.",
        address="910 Lakeshore Blvd W",
        latitude=43.6294,
        longitude=-79.4481,
        certification_score=0.79,
        community_verification_score=0.31,
        recency_score=0.68,
        tags=("halal", "vegetarian"),
        allergens_present=("dairy", "gluten", "shellfish", "soy"),
    ),
    RestaurantSeed(
        name="Dual Seal Kitchen",
        description="Edge case: restaurant advertises halal and kosher menus but has unverified, stale trust documentation.",
        address="14 Market Square",
        latitude=43.6489,
        longitude=-79.3756,
        certification_score=0.38,
        community_verification_score=0.43,
        recency_score=0.14,
        tags=("halal", "kosher", "mixed"),
        allergens_present=("dairy", "egg", "gluten", "sesame"),
    ),
)


def _upsert_users() -> None:
    with SessionLocal() as db:
        existing_users = {
            user.email: user for user in db.scalars(select(User).where(User.email.in_([u["email"] for u in DEMO_USERS])))
        }
        created = 0
        updated = 0
        for seed_user in DEMO_USERS:
            user = existing_users.get(seed_user["email"])
            if user is None:
                user = User(
                    email=seed_user["email"],
                    display_name=seed_user["display_name"],
                    password_hash=hash_password(seed_user["password"]),
                    role=seed_user["role"],
                )
                db.add(user)
                created += 1
                continue

            user.display_name = seed_user["display_name"]
            user.password_hash = hash_password(seed_user["password"])
            user.role = seed_user["role"]
            updated += 1

        db.commit()

    print(f"Users seeded: {created} created, {updated} updated")


def _upsert_restaurants() -> None:
    with SessionLocal() as db:
        existing = {restaurant.name: restaurant for restaurant in db.scalars(select(Restaurant)).all()}
        created = 0
        updated = 0

        for seed in RESTAURANT_SEEDS:
            restaurant = existing.get(seed.name)
            if restaurant is None:
                restaurant = Restaurant(name=seed.name)
                db.add(restaurant)
                created += 1
            else:
                updated += 1

            restaurant.description = seed.description
            restaurant.address = seed.address
            restaurant.latitude = seed.latitude
            restaurant.longitude = seed.longitude
            restaurant.certification_score = seed.certification_score
            restaurant.community_verification_score = seed.community_verification_score
            restaurant.recency_score = seed.recency_score

            restaurant.tags.clear()
            restaurant.allergen_info.clear()
            db.flush()

            restaurant.tags = [RestaurantTag(tag=tag) for tag in seed.tags]
            restaurant.allergen_info = [
                RestaurantAllergenInfo(allergen=allergen, present=True) for allergen in seed.allergens_present
            ]

        db.commit()

    print(f"Restaurants seeded: {created} created, {updated} updated ({len(RESTAURANT_SEEDS)} total templates)")


def seed() -> None:
    _upsert_users()
    _upsert_restaurants()


if __name__ == "__main__":
    seed()
