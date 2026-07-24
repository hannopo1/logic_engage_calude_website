from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.catalog import ProductList, ProductOut
from app.schemas.review import ReviewBlock, ReviewIn, ReviewOut, ReviewSummary
from app.services import review_service

router = APIRouter()


def _with_ratings(db: Session, products: list[Product]) -> list[ProductOut]:
    """
    Serialize products with approved-review rating summaries.
    
    Parameters:
    	products (list[Product]): Products to serialize and enrich with rating data.
    
    Returns:
    	list[ProductOut]: Serialized products with average approved rating and review count.
    """
    stats = review_service.approved_stats_map(db, [p.id for p in products])
    out: list[ProductOut] = []
    for p in products:
        item = ProductOut.model_validate(p)
        avg, count = stats.get(p.id, (0.0, 0))
        item.rating_avg = avg
        item.rating_count = count
        out.append(item)
    return out


@router.get("", response_model=ProductList)
def list_products(
    db: Session = Depends(get_db),
    category: str | None = Query(default=None, description="category slug"),
    min_price: float | None = None,
    max_price: float | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
) -> ProductList:
    """
    List active products with optional category, price, and pagination filters.
    
    Parameters:
    	category (str | None): Category slug used to filter products.
    	min_price (float | None): Minimum product price, inclusive.
    	max_price (float | None): Maximum product price, inclusive.
    	page (int): One-based page number.
    	page_size (int): Number of products per page.
    
    Returns:
    	ProductList: Paginated products with the total matching product count.
    """
    stmt = select(Product).where(Product.is_active.is_(True))
    if category:
        cat = db.scalar(select(Category).where(Category.slug == category))
        if cat:
            stmt = stmt.where(Product.category_id == cat.id)
    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = list(
        db.scalars(
            stmt.order_by(Product.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
    )
    return ProductList(
        items=_with_ratings(db, rows),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{slug}", response_model=ProductOut)
def get_product(slug: str, db: Session = Depends(get_db)) -> ProductOut:
    """
    Retrieve an active product by its slug.
    
    Parameters:
        slug (str): The product slug used to identify the product.
    
    Returns:
        ProductOut: The product enriched with approved review rating data.
    
    Raises:
        HTTPException: If no active product matches the slug.
    """
    product = db.scalar(select(Product).where(Product.slug == slug, Product.is_active.is_(True)))
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return _with_ratings(db, [product])[0]


@router.get("/{slug}/reviews", response_model=ReviewBlock)
def get_product_reviews(slug: str, db: Session = Depends(get_db)) -> ReviewBlock:
    """
    Retrieve the approved reviews and rating summary for a product.
    
    Parameters:
    	slug (str): The product's URL slug.
    	db (Session): The database session.
    
    Returns:
    	ReviewBlock: The product's rating summary and approved reviews.
    
    Raises:
    	HTTPException: If no product matches the slug.
    """
    product = db.scalar(select(Product).where(Product.slug == slug))
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ReviewBlock(
        summary=ReviewSummary(**review_service.summary(db, product.id)),
        items=[ReviewOut.model_validate(r) for r in review_service.list_approved(db, product.id)],
    )


@router.post("/{product_id}/reviews", response_model=ReviewOut, status_code=201)
def create_product_review(
    product_id: int,
    payload: ReviewIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReviewOut:
    """
    Create a review for a product.
    
    Parameters:
        product_id (int): Identifier of the product being reviewed.
        payload (ReviewIn): Review rating, title, and body.
    
    Returns:
        ReviewOut: The newly created review.
    
    Raises:
        HTTPException: If the product does not exist.
    """
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    review = review_service.create_review(
        db, user, product, payload.rating, payload.body, payload.title
    )
    return ReviewOut.model_validate(review)
