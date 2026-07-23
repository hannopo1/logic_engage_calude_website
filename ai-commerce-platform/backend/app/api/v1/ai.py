from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.base import get_provider
from app.core.database import get_db
from app.models.order import OrderItem
from app.models.product import Product
from app.schemas.ai import ChatRequest, ChatResponse, RecommendResponse
from app.schemas.catalog import ProductOut

router = APIRouter()

_MAX_CONTEXT_PRODUCTS = 60


def _build_context(db: Session) -> tuple[str, list[Product]]:
    """Compact catalog + policy context for the assistant (RAG-lite grounding)."""
    products = list(
        db.scalars(
            select(Product).where(Product.is_active.is_(True)).limit(_MAX_CONTEXT_PRODUCTS)
        )
    )
    lines = [
        f"{p.name} — {p.price} — {(p.description or '')[:120]} "
        f"[category_id={p.category_id}, tags={p.tags or ''}, in_stock={p.stock_qty}]"
        for p in products
    ]
    policies = [
        "الإرجاع مقبول خلال 14 يوماً من الاستلام للمنتجات غير المستخدمة.",
        "الشحن القياسي 2-5 أيام عمل داخل مصر.",
        "الدفع عند الاستلام (كاش) متاح لكل الطلبات.",
        "الأسعار بالجنيه المصري وتشمل كل الرسوم.",
    ]
    context = "PRODUCTS:\n" + "\n".join(lines) + "\n\nPOLICIES:\n" + "\n".join(policies)
    return context, products


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    context, products = _build_context(db)
    provider = get_provider()
    history = [m.model_dump() for m in payload.history]
    reply = provider.chat(payload.message, history, context)

    # Surface any catalog products whose name appears in the reply.
    referenced = [p for p in products if p.name.lower() in reply.lower()][:6]
    return ChatResponse(
        reply=reply,
        provider=provider.name,
        products=[ProductOut.model_validate(p) for p in referenced],
    )


@router.get("/recommend/{product_id}", response_model=RecommendResponse)
def recommend(product_id: int, db: Session = Depends(get_db)) -> RecommendResponse:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Content-based: same category, then shared tags. Excludes the seed product.
    similar_stmt = (
        select(Product)
        .where(
            Product.id != product.id,
            Product.is_active.is_(True),
            Product.category_id == product.category_id,
        )
        .limit(6)
    )
    similar = list(db.scalars(similar_stmt))

    # Collaborative-lite: products co-occurring in the same orders ("also bought").
    order_ids = select(OrderItem.order_id).where(OrderItem.product_id == product.id)
    also_stmt = (
        select(Product, func.count(OrderItem.id).label("freq"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .where(OrderItem.order_id.in_(order_ids), Product.id != product.id)
        .group_by(Product.id)
        .order_by(func.count(OrderItem.id).desc())
        .limit(6)
    )
    also_bought = [row[0] for row in db.execute(also_stmt).all()]

    return RecommendResponse(
        similar=[ProductOut.model_validate(p) for p in similar],
        also_bought=[ProductOut.model_validate(p) for p in also_bought],
    )
