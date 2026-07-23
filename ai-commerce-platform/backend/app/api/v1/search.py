from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import Product
from app.schemas.catalog import ProductOut

router = APIRouter()


@router.get("", response_model=list[ProductOut])
def search_products(
    q: str = Query(min_length=1, description="free-text query"),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[Product]:
    """Full-text search over the products GIN(search_vector) index.

    Uses websearch_to_tsquery so natural phrases ("wireless headphones under budget")
    work without special syntax. Ranked by ts_rank; falls back to ILIKE if the
    tsquery yields nothing (e.g. very short/partial tokens).
    """
    tsquery = func.websearch_to_tsquery("english", q)
    stmt = (
        select(Product)
        .where(Product.is_active.is_(True), Product.search_vector.op("@@")(tsquery))
        .order_by(func.ts_rank(Product.search_vector, tsquery).desc())
        .limit(limit)
    )
    results = list(db.scalars(stmt))
    if results:
        return results

    like = f"%{q}%"
    fallback = (
        select(Product)
        .where(Product.is_active.is_(True), Product.name.ilike(like))
        .limit(limit)
    )
    return list(db.scalars(fallback))
