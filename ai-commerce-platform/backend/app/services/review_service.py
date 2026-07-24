"""Product reviews: verified-purchase gate, listing, and rating summary.

Single source of truth for the public /products/{...}/reviews endpoints. The
policy is verified-purchase-only: a user may review a product only if they have
an order that contains it. New reviews are held for moderation (is_approved=False)
and surface on the storefront only after an operator approves them.
"""
from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.review import Review
from app.models.user import User


def _purchase_order_id(db: Session, user_id: int, product_id: int) -> int | None:
    """The most recent order id in which this user bought this product, or None."""
    return db.scalar(
        select(OrderItem.order_id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.user_id == user_id, OrderItem.product_id == product_id)
        .order_by(OrderItem.order_id.desc())
    )


def create_review(
    db: Session, user: User, product: Product, rating: int, body: str, title: str | None = None
) -> Review:
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="التقييم يجب أن يكون بين 1 و5 نجوم")
    if not (body or "").strip():
        raise HTTPException(status_code=400, detail="نص المراجعة مطلوب")

    order_id = _purchase_order_id(db, user.id, product.id)
    if order_id is None:
        raise HTTPException(
            status_code=403, detail="يمكن تقييم المنتج فقط بعد شرائه من المتجر"
        )

    existing = db.scalar(
        select(Review).where(Review.product_id == product.id, Review.user_id == user.id)
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="لديك مراجعة لهذا المنتج بالفعل")

    review = Review(
        product_id=product.id,
        user_id=user.id,
        order_id=order_id,
        rating=rating,
        title=(title or None),
        body=body.strip(),
        is_verified=True,
        is_approved=False,  # awaits operator moderation
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def list_approved(db: Session, product_id: int) -> list[Review]:
    return list(
        db.scalars(
            select(Review)
            .where(Review.product_id == product_id, Review.is_approved.is_(True))
            .order_by(Review.created_at.desc())
        )
    )


def summary(db: Session, product_id: int) -> dict:
    """Average, count, and 1..5 star distribution over approved reviews."""
    rows = db.execute(
        select(Review.rating, func.count())
        .where(Review.product_id == product_id, Review.is_approved.is_(True))
        .group_by(Review.rating)
    ).all()
    distribution = {star: 0 for star in range(1, 6)}
    total = 0
    weighted = 0
    for rating, count in rows:
        distribution[int(rating)] = count
        total += count
        weighted += int(rating) * count
    average = round(weighted / total, 2) if total else 0.0
    return {
        "average": average,
        "count": total,
        "distribution": distribution,
    }


def approved_stats_map(db: Session, product_ids: list[int]) -> dict[int, tuple[float, int]]:
    """Bulk {product_id: (avg, count)} for a set of products — avoids N+1 in lists."""
    if not product_ids:
        return {}
    rows = db.execute(
        select(Review.product_id, func.avg(Review.rating), func.count())
        .where(Review.product_id.in_(product_ids), Review.is_approved.is_(True))
        .group_by(Review.product_id)
    ).all()
    return {int(pid): (round(float(avg), 2), int(count)) for pid, avg, count in rows}
