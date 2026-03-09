from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.models import Favorite, Restaurant


def add_favorite(db: Session, user_id: int, restaurant_id: int) -> None:
    existing = db.scalars(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.restaurant_id == restaurant_id)
    ).first()
    if existing:
        return

    favorite = Favorite(user_id=user_id, restaurant_id=restaurant_id)
    db.add(favorite)
    db.commit()


def remove_favorite(db: Session, user_id: int, restaurant_id: int) -> bool:
    favorite = db.scalars(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.restaurant_id == restaurant_id)
    ).first()
    if not favorite:
        return False

    db.delete(favorite)
    db.commit()
    return True


def list_favorite_restaurants(db: Session, user_id: int) -> list[Restaurant]:
    stmt = (
        select(Restaurant)
        .join(Favorite, Favorite.restaurant_id == Restaurant.id)
        .where(Favorite.user_id == user_id)
        .options(selectinload(Restaurant.tags), selectinload(Restaurant.allergen_info))
        .order_by(Restaurant.id)
    )
    return list(db.scalars(stmt).all())


def is_favorited(db: Session, user_id: int, restaurant_id: int) -> bool:
    return (
        db.scalars(select(Favorite).where(Favorite.user_id == user_id, Favorite.restaurant_id == restaurant_id)).first()
        is not None
    )
