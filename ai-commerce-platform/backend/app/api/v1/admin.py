"""Operator (admin) API — the drop-shipping control room.

All endpoints require role=admin. The operator reviews agent-sourced purchase
orders, approves them, executes assisted purchases, and records shipping.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents import purchasing, sourcing
from app.api.deps import get_current_admin
from app.core.database import get_db
from app.core.utils import unique_slug
from app.models.analytics import AnalyticsEvent
from app.models.coupon import Coupon
from app.models.order import Order
from app.models.product import Product
from app.models.purchase_order import PO_STATUSES, PurchaseOrder
from app.models.supplier import Supplier, SupplierOffer
from app.models.user import User
from app.schemas.fulfillment import (
    DashboardOut,
    MarkPurchasedIn,
    OfferIn,
    OfferOut,
    OfferPatch,
    POEventOut,
    PurchaseOrderOut,
    RejectIn,
    ShipIn,
    SupplierIn,
    SupplierOut,
    SupplierPatch,
)
from app.schemas.coupon import CouponIn, CouponOut, CouponPatch
from app.schemas.merchant import (
    AnalyticsOut,
    CustomerOut,
    FunnelStep,
    ProductAdminOut,
    ProductIn,
    ProductPatch,
    TopItem,
)
from app.services import fulfillment_service

router = APIRouter(dependencies=[Depends(get_current_admin)])


# ---------- helpers ----------

def _po_out(po: PurchaseOrder) -> PurchaseOrderOut:
    offer = po.offer
    supplier = offer.supplier if offer else None
    item = po.order_item
    return PurchaseOrderOut(
        id=po.id,
        order_id=po.order_id,
        order_item_id=po.order_item_id,
        supplier_offer_id=po.supplier_offer_id,
        status=po.status,
        quantity=po.quantity,
        expected_cost=po.expected_cost,
        actual_cost=po.actual_cost,
        supplier_order_ref=po.supplier_order_ref,
        tracking_no=po.tracking_no,
        carrier=po.carrier,
        created_at=po.created_at,
        product_name=item.product_name if item else None,
        supplier_name=supplier.name if supplier else None,
        supplier_url=offer.url if offer else None,
        customer_address=po.order.shipping_address if po.order else None,
        selling_total=item.total_price if item else None,
        events=[POEventOut.model_validate(e) for e in po.events],
    )


def _get_po(db: Session, po_id: int) -> PurchaseOrder:
    po = db.get(PurchaseOrder, po_id)
    if po is None:
        raise HTTPException(status_code=404, detail="أمر الشراء غير موجود")
    return po


# ---------- dashboard ----------

@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)) -> DashboardOut:
    counts = {s: 0 for s in PO_STATUSES}
    for status_val, n in db.execute(
        select(PurchaseOrder.status, func.count(PurchaseOrder.id)).group_by(PurchaseOrder.status)
    ).all():
        counts[status_val] = n

    today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc)
    orders_today = db.scalar(
        select(func.count(Order.id)).where(Order.created_at >= today_start)
    ) or 0

    revenue = db.scalar(
        select(func.coalesce(func.sum(Order.total_amount), 0)).where(Order.status != "cancelled")
    ) or Decimal("0")
    open_cost = db.scalar(
        select(func.coalesce(func.sum(PurchaseOrder.expected_cost), 0)).where(
            PurchaseOrder.status.notin_(("cancelled", "failed"))
        )
    ) or Decimal("0")

    margin = None
    if revenue and Decimal(str(revenue)) > 0:
        margin = float(
            (Decimal(str(revenue)) - Decimal(str(open_cost))) / Decimal(str(revenue)) * 100
        )

    return DashboardOut(
        po_counts=counts,
        orders_today=orders_today,
        revenue_total=revenue,
        expected_cost_open=open_cost,
        estimated_margin_percent=margin,
    )


# ---------- purchase orders ----------

@router.get("/purchase-orders", response_model=list[PurchaseOrderOut])
def list_purchase_orders(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[PurchaseOrderOut]:
    stmt = select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).limit(200)
    if status:
        stmt = stmt.where(PurchaseOrder.status == status)
    return [_po_out(po) for po in db.scalars(stmt)]


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderOut)
def get_purchase_order(po_id: int, db: Session = Depends(get_db)) -> PurchaseOrderOut:
    return _po_out(_get_po(db, po_id))


@router.post("/purchase-orders/{po_id}/approve")
def approve_po(po_id: int, db: Session = Depends(get_db)) -> dict:
    """Operator approval — hands the PO to the purchasing agent."""
    po = _get_po(db, po_id)
    if po.status != "awaiting_approval":
        raise HTTPException(status_code=409, detail=f"لا يمكن الموافقة من الحالة '{po.status}'")
    fulfillment_service.record_event(db, po, "وافق المشغّل على أمر الشراء", actor="operator")
    result = purchasing.execute_purchase(db, po)
    return {"po": _po_out(_get_po(db, po_id)).model_dump(), **result}


@router.post("/purchase-orders/{po_id}/reject", response_model=PurchaseOrderOut)
def reject_po(po_id: int, payload: RejectIn, db: Session = Depends(get_db)) -> PurchaseOrderOut:
    po = _get_po(db, po_id)
    target = "cancelled" if payload.cancel else "pending_sourcing"
    fulfillment_service.transition(
        db, po, target, actor="operator", note=f"رفض المشغّل: {payload.note}"
    )
    return _po_out(po)


@router.post("/purchase-orders/{po_id}/resource", response_model=PurchaseOrderOut)
def resource_po(po_id: int, db: Session = Depends(get_db)) -> PurchaseOrderOut:
    """Re-run sourcing for a pending_sourcing PO (e.g. after adding offers)."""
    po = _get_po(db, po_id)
    if po.status not in ("pending_sourcing", "failed"):
        raise HTTPException(status_code=409, detail=f"لا يمكن إعادة التوريد من الحالة '{po.status}'")
    item = po.order_item
    offer, reason = sourcing.pick_offer(db, item.product_id, Decimal(str(item.unit_price)))
    if offer is None:
        fulfillment_service.record_event(db, po, f"إعادة توريد: {reason}", actor="agent")
        return _po_out(po)
    po.supplier_offer_id = offer.id
    po.expected_cost = sourcing.landed_cost(offer) * po.quantity
    fulfillment_service.transition(db, po, "awaiting_approval", actor="agent", note=reason)
    return _po_out(po)


@router.post("/purchase-orders/{po_id}/mark-purchased", response_model=PurchaseOrderOut)
def mark_purchased(po_id: int, payload: MarkPurchasedIn, db: Session = Depends(get_db)) -> PurchaseOrderOut:
    """Operator confirms the assisted purchase was placed at the supplier."""
    po = _get_po(db, po_id)
    po.supplier_order_ref = payload.supplier_order_ref
    if payload.actual_cost is not None:
        po.actual_cost = payload.actual_cost
    fulfillment_service.transition(
        db, po, "purchased", actor="operator",
        note=f"تم الشراء — مرجع المورد: {payload.supplier_order_ref}",
    )
    return _po_out(po)


@router.post("/purchase-orders/{po_id}/ship", response_model=PurchaseOrderOut)
def ship_po(po_id: int, payload: ShipIn, db: Session = Depends(get_db)) -> PurchaseOrderOut:
    po = _get_po(db, po_id)
    po.tracking_no = payload.tracking_no
    po.carrier = payload.carrier
    fulfillment_service.transition(
        db, po, "shipped", actor="operator",
        note=f"شُحن للعميل — تتبع: {payload.tracking_no}" + (f" ({payload.carrier})" if payload.carrier else ""),
    )
    return _po_out(po)


@router.post("/purchase-orders/{po_id}/deliver", response_model=PurchaseOrderOut)
def deliver_po(po_id: int, db: Session = Depends(get_db)) -> PurchaseOrderOut:
    po = _get_po(db, po_id)
    fulfillment_service.transition(db, po, "delivered", actor="operator", note="تم التسليم للعميل")
    return _po_out(po)


# ---------- suppliers ----------

@router.get("/suppliers", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(get_db)) -> list[Supplier]:
    return list(db.scalars(select(Supplier).order_by(Supplier.name)))


@router.post("/suppliers", response_model=SupplierOut, status_code=201)
def create_supplier(payload: SupplierIn, db: Session = Depends(get_db)) -> Supplier:
    if db.scalar(select(Supplier).where(Supplier.slug == payload.slug)):
        raise HTTPException(status_code=409, detail="slug مستخدم بالفعل")
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.patch("/suppliers/{supplier_id}", response_model=SupplierOut)
def patch_supplier(supplier_id: int, payload: SupplierPatch, db: Session = Depends(get_db)) -> Supplier:
    supplier = db.get(Supplier, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="المورد غير موجود")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(supplier, k, v)
    db.commit()
    db.refresh(supplier)
    return supplier


# ---------- supplier offers ----------

@router.get("/offers", response_model=list[OfferOut])
def list_offers(
    product_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[SupplierOffer]:
    stmt = select(SupplierOffer)
    if product_id:
        stmt = stmt.where(SupplierOffer.product_id == product_id)
    return list(db.scalars(stmt.limit(500)))


@router.post("/offers", response_model=OfferOut, status_code=201)
def create_offer(payload: OfferIn, db: Session = Depends(get_db)) -> SupplierOffer:
    offer = SupplierOffer(**payload.model_dump())
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@router.patch("/offers/{offer_id}", response_model=OfferOut)
def patch_offer(offer_id: int, payload: OfferPatch, db: Session = Depends(get_db)) -> SupplierOffer:
    offer = db.get(SupplierOffer, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="العرض غير موجود")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(offer, k, v)
    db.commit()
    db.refresh(offer)
    return offer


# ---------- product management ----------

def _product_out(db: Session, p: Product) -> ProductAdminOut:
    offer_count = db.scalar(
        select(func.count(SupplierOffer.id)).where(SupplierOffer.product_id == p.id)
    ) or 0
    out = ProductAdminOut.model_validate(p)
    out.offer_count = offer_count
    return out


@router.get("/products", response_model=list[ProductAdminOut])
def admin_list_products(db: Session = Depends(get_db)) -> list[ProductAdminOut]:
    rows = db.scalars(select(Product).order_by(Product.created_at.desc()).limit(500))
    return [_product_out(db, p) for p in rows]


@router.post("/products", response_model=ProductAdminOut, status_code=201)
def admin_create_product(payload: ProductIn, db: Session = Depends(get_db)) -> ProductAdminOut:
    slug = payload.slug or unique_slug(
        payload.name, lambda s: db.scalar(select(Product).where(Product.slug == s)) is not None
    )
    if db.scalar(select(Product).where(Product.slug == slug)):
        raise HTTPException(status_code=409, detail="الـ slug مستخدم بالفعل")
    data = payload.model_dump()
    data["slug"] = slug
    product = Product(**data)
    db.add(product)
    db.commit()
    db.refresh(product)
    return _product_out(db, product)


@router.patch("/products/{product_id}", response_model=ProductAdminOut)
def admin_patch_product(
    product_id: int, payload: ProductPatch, db: Session = Depends(get_db)
) -> ProductAdminOut:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(product, k, v)
    db.commit()
    db.refresh(product)
    return _product_out(db, product)


# ---------- customers ----------

@router.get("/customers", response_model=list[CustomerOut])
def admin_list_customers(db: Session = Depends(get_db)) -> list[CustomerOut]:
    # Aggregate order count + spend per customer in one pass.
    stats = {
        row.user_id: (row.n, row.spent)
        for row in db.execute(
            select(
                Order.user_id.label("user_id"),
                func.count(Order.id).label("n"),
                func.coalesce(func.sum(Order.total_amount), 0).label("spent"),
            )
            .where(Order.user_id.isnot(None), Order.status != "cancelled")
            .group_by(Order.user_id)
        ).all()
    }
    users = db.scalars(
        select(User).where(User.role == "customer").order_by(User.created_at.desc()).limit(500)
    )
    out: list[CustomerOut] = []
    for u in users:
        n, spent = stats.get(u.id, (0, 0))
        out.append(
            CustomerOut(
                id=u.id,
                email=u.email,
                first_name=u.first_name,
                last_name=u.last_name,
                phone=u.phone,
                created_at=u.created_at,
                order_count=n,
                total_spent=spent,
            )
        )
    return out


# ---------- analytics ----------

@router.get("/analytics", response_model=AnalyticsOut)
def admin_analytics(days: int = Query(default=30, ge=1, le=365), db: Session = Depends(get_db)) -> AnalyticsOut:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    ev = AnalyticsEvent

    def count(evtype: str) -> int:
        return db.scalar(
            select(func.count(ev.id)).where(ev.event_type == evtype, ev.created_at >= since)
        ) or 0

    def uniq(evtype: str | None = None) -> int:
        stmt = select(func.count(func.distinct(ev.session_id))).where(ev.created_at >= since)
        if evtype:
            stmt = stmt.where(ev.event_type == evtype)
        return db.scalar(stmt) or 0

    unique_visitors = uniq()
    page_views = count("page_view")
    product_views = count("product_view")
    searches = count("search")
    add_to_cart = count("add_to_cart")
    begin_checkout = count("begin_checkout")
    orders = count("purchase")

    conv = round(orders / unique_visitors * 100, 1) if unique_visitors else 0.0

    funnel = [
        FunnelStep(key="visit", label="زيارة", count=unique_visitors),
        FunnelStep(key="product_view", label="مشاهدة منتج", count=uniq("product_view")),
        FunnelStep(key="add_to_cart", label="إضافة للسلة", count=uniq("add_to_cart")),
        FunnelStep(key="begin_checkout", label="بدء الدفع", count=uniq("begin_checkout")),
        FunnelStep(key="purchase", label="شراء", count=uniq("purchase")),
    ]

    # Top viewed products (join product name).
    top_products = [
        TopItem(label=name or f"#{pid}", count=n)
        for pid, name, n in db.execute(
            select(ev.product_id, Product.name, func.count(ev.id))
            .join(Product, Product.id == ev.product_id, isouter=True)
            .where(ev.event_type == "product_view", ev.created_at >= since, ev.product_id.isnot(None))
            .group_by(ev.product_id, Product.name)
            .order_by(func.count(ev.id).desc())
            .limit(8)
        ).all()
    ]

    top_searches = [
        TopItem(label=q, count=n)
        for q, n in db.execute(
            select(ev.query, func.count(ev.id))
            .where(ev.event_type == "search", ev.created_at >= since, ev.query.isnot(None))
            .group_by(ev.query)
            .order_by(func.count(ev.id).desc())
            .limit(8)
        ).all()
    ]

    daily = [
        TopItem(label=str(day), count=n)
        for day, n in db.execute(
            select(func.date(ev.created_at), func.count(func.distinct(ev.session_id)))
            .where(ev.created_at >= since)
            .group_by(func.date(ev.created_at))
            .order_by(func.date(ev.created_at))
        ).all()
    ]

    return AnalyticsOut(
        days=days,
        unique_visitors=unique_visitors,
        page_views=page_views,
        product_views=product_views,
        searches=searches,
        add_to_cart=add_to_cart,
        orders=orders,
        conversion_rate=conv,
        funnel=funnel,
        top_products=top_products,
        top_searches=top_searches,
        daily_visitors=daily,
    )


# ---------- coupons ----------

@router.get("/coupons", response_model=list[CouponOut])
def admin_list_coupons(db: Session = Depends(get_db)) -> list[Coupon]:
    return list(db.scalars(select(Coupon).order_by(Coupon.created_at.desc())))


@router.post("/coupons", response_model=CouponOut, status_code=201)
def admin_create_coupon(payload: CouponIn, db: Session = Depends(get_db)) -> Coupon:
    code = payload.code.strip().upper()
    if db.scalar(select(Coupon).where(func.upper(Coupon.code) == code)):
        raise HTTPException(status_code=409, detail="كود الخصم مستخدم بالفعل")
    if payload.kind not in ("percent", "fixed"):
        raise HTTPException(status_code=400, detail="نوع الخصم يجب أن يكون percent أو fixed")
    data = payload.model_dump()
    data["code"] = code
    coupon = Coupon(**data)
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.patch("/coupons/{coupon_id}", response_model=CouponOut)
def admin_patch_coupon(coupon_id: int, payload: CouponPatch, db: Session = Depends(get_db)) -> Coupon:
    coupon = db.get(Coupon, coupon_id)
    if coupon is None:
        raise HTTPException(status_code=404, detail="كود الخصم غير موجود")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(coupon, k, v)
    db.commit()
    db.refresh(coupon)
    return coupon
