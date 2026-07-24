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
    """
    Search active products using full-text matching with a name-based fallback.
    
    Parameters:
        q (str): Free-text search query.
        limit (int): Maximum number of products to return.
    
    Returns:
        list[Product]: Active products matching the query, ranked by relevance when full-text matches are found.
    """
    # 'simple' config: neutral tokenizer, correct for the Arabic catalog.
    tsquery = func.websearch_to_tsquery("simple", q)
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
