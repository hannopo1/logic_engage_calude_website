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
from app.models.review import Review
from app.schemas.review import AdminReviewOut
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
    """
    Builds an API response representation of a purchase order, including related supplier, product, customer address, and event details.
    
    Returns:
        PurchaseOrderOut: The serialized purchase order data.
    """
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
    """
    Retrieve a purchase order by its identifier.
    
    Parameters:
    	db (Session): Database session used to query the purchase order.
    	po_id (int): Identifier of the purchase order.
    
    Returns:
    	PurchaseOrder: The matching purchase order.
    
    Raises:
    	HTTPException: If no purchase order exists with the specified identifier.
    """
    po = db.get(PurchaseOrder, po_id)
    if po is None:
        raise HTTPException(status_code=404, detail="أمر الشراء غير موجود")
    return po


# ---------- dashboard ----------

@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)) -> DashboardOut:
    """
    Summarize operational order, revenue, cost, and margin metrics.
    
    Returns:
        DashboardOut: Aggregated purchase-order counts, today's order count,
            total revenue, open expected costs, and estimated margin percentage.
    """
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
    """
    List purchase orders, optionally filtered by status.
    
    Parameters:
    	status (str | None): Purchase order status used to filter the results.
    
    Returns:
    	list[PurchaseOrderOut]: Up to 200 purchase orders, ordered from newest to oldest.
    """
    stmt = select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).limit(200)
    if status:
        stmt = stmt.where(PurchaseOrder.status == status)
    return [_po_out(po) for po in db.scalars(stmt)]


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderOut)
def get_purchase_order(po_id: int, db: Session = Depends(get_db)) -> PurchaseOrderOut:
    """
    Retrieve a purchase order by its identifier.
    
    Parameters:
    	po_id (int): The purchase order identifier.
    
    Returns:
    	PurchaseOrderOut: The purchase order details.
    """
    return _po_out(_get_po(db, po_id))


@router.post("/purchase-orders/{po_id}/approve")
def approve_po(po_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Approve a purchase order and initiate its purchase with the supplier.
    
    Args:
        po_id (int): Identifier of the purchase order.
    
    Returns:
        dict: A mapping containing the updated purchase order under ``po`` and the purchase execution result.
    
    Raises:
        HTTPException: If the purchase order does not exist or is not awaiting approval.
    """
    po = _get_po(db, po_id)
    if po.status != "awaiting_approval":
        raise HTTPException(status_code=409, detail=f"لا يمكن الموافقة من الحالة '{po.status}'")
    fulfillment_service.record_event(db, po, "وافق المشغّل على أمر الشراء", actor="operator")
    result = purchasing.execute_purchase(db, po)
    return {"po": _po_out(_get_po(db, po_id)).model_dump(), **result}


@router.post("/purchase-orders/{po_id}/reject", response_model=PurchaseOrderOut)
def reject_po(po_id: int, payload: RejectIn, db: Session = Depends(get_db)) -> PurchaseOrderOut:
    """
    Rejects a purchase order or returns it to sourcing.
    
    Parameters:
        payload (RejectIn): Rejection details, including whether to cancel the order and an optional note.
    
    Returns:
        PurchaseOrderOut: The updated purchase order.
    """
    po = _get_po(db, po_id)
    target = "cancelled" if payload.cancel else "pending_sourcing"
    fulfillment_service.transition(
        db, po, target, actor="operator", note=f"رفض المشغّل: {payload.note}"
    )
    return _po_out(po)


@router.post("/purchase-orders/{po_id}/resource", response_model=PurchaseOrderOut)
def resource_po(po_id: int, db: Session = Depends(get_db)) -> PurchaseOrderOut:
    """Re-run sourcing for a purchase order awaiting a suitable supplier offer.
    
    Parameters:
    	po_id (int): The purchase order identifier.
    	db (Session): The database session.
    
    Returns:
    	PurchaseOrderOut: The purchase order with its sourcing status and details."""
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
    """
    Record shipping details and mark a purchase order as shipped.
    
    Parameters:
        po_id (int): The purchase order identifier.
        payload (ShipIn): The tracking number and optional carrier information.
        db (Session): The database session.
    
    Returns:
        PurchaseOrderOut: The updated purchase order.
    """
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
    """
    Mark a purchase order as delivered.
    
    Parameters:
    	po_id (int): The purchase order identifier.
    
    Returns:
    	PurchaseOrderOut: The updated purchase order.
    """
    po = _get_po(db, po_id)
    fulfillment_service.transition(db, po, "delivered", actor="operator", note="تم التسليم للعميل")
    return _po_out(po)


# ---------- suppliers ----------

@router.get("/suppliers", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(get_db)) -> list[Supplier]:
    """List suppliers ordered by name.
    
    Returns:
    	list[Supplier]: The available suppliers in alphabetical order.
    """
    return list(db.scalars(select(Supplier).order_by(Supplier.name)))


@router.post("/suppliers", response_model=SupplierOut, status_code=201)
def create_supplier(payload: SupplierIn, db: Session = Depends(get_db)) -> Supplier:
    """
    Create a supplier from the provided details.
    
    Parameters:
    	payload (SupplierIn): Supplier details, including a unique slug.
    
    Returns:
    	Supplier: The persisted supplier.
    """
    if db.scalar(select(Supplier).where(Supplier.slug == payload.slug)):
        raise HTTPException(status_code=409, detail="slug مستخدم بالفعل")
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.patch("/suppliers/{supplier_id}", response_model=SupplierOut)
def patch_supplier(supplier_id: int, payload: SupplierPatch, db: Session = Depends(get_db)) -> Supplier:
    """
    Partially updates a supplier and returns the updated supplier.
    
    Parameters:
    	supplier_id (int): The supplier's identifier.
    	payload (SupplierPatch): The fields to update.
    """
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
    """List supplier offers, optionally filtered by product.
    
    Parameters:
    	product_id (int | None): Optional product identifier used to filter the offers.
    
    Returns:
    	list[SupplierOffer]: Up to 500 matching supplier offers.
    """
    stmt = select(SupplierOffer)
    if product_id:
        stmt = stmt.where(SupplierOffer.product_id == product_id)
    return list(db.scalars(stmt.limit(500)))


@router.post("/offers", response_model=OfferOut, status_code=201)
def create_offer(payload: OfferIn, db: Session = Depends(get_db)) -> SupplierOffer:
    """Create and persist a supplier offer.
    
    Parameters:
    	payload (OfferIn): The supplier offer data to create.
    
    Returns:
    	SupplierOffer: The newly created supplier offer.
    """
    offer = SupplierOffer(**payload.model_dump())
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@router.patch("/offers/{offer_id}", response_model=OfferOut)
def patch_offer(offer_id: int, payload: OfferPatch, db: Session = Depends(get_db)) -> SupplierOffer:
    """
    Update the supplied fields of a supplier offer.
    
    Parameters:
        offer_id (int): Identifier of the supplier offer to update.
        payload (OfferPatch): Fields to change on the offer.
    
    Returns:
        SupplierOffer: The updated supplier offer.
    """
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
    """
    Build an administrator-facing product representation with its supplier offer count.
    
    Parameters:
    	db (Session): Database session used to count the product's supplier offers.
    	p (Product): Product to serialize.
    
    Returns:
    	ProductAdminOut: Product data enriched with the number of associated supplier offers.
    """
    offer_count = db.scalar(
        select(func.count(SupplierOffer.id)).where(SupplierOffer.product_id == p.id)
    ) or 0
    out = ProductAdminOut.model_validate(p)
    out.offer_count = offer_count
    return out


@router.get("/products", response_model=list[ProductAdminOut])
def admin_list_products(db: Session = Depends(get_db)) -> list[ProductAdminOut]:
    """List up to 500 products for administrative management.
    
    Returns:
    	list[ProductAdminOut]: Products enriched with their supplier offer counts.
    """
    rows = db.scalars(select(Product).order_by(Product.created_at.desc()).limit(500))
    return [_product_out(db, p) for p in rows]


@router.post("/products", response_model=ProductAdminOut, status_code=201)
def admin_create_product(payload: ProductIn, db: Session = Depends(get_db)) -> ProductAdminOut:
    """
    Create a product with a unique slug and return its administrative representation.
    
    Parameters:
        payload (ProductIn): Product details, including an optional slug.
        db (Session): Database session used to persist the product.
    
    Returns:
        ProductAdminOut: The created product with its supplier-offer count.
    """
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
    """
    Partially updates an administrator-managed product.
    
    Parameters:
    	product_id (int): The identifier of the product to update.
    	payload (ProductPatch): The product fields to change.
    	db (Session): The database session.
    
    Returns:
    	ProductAdminOut: The updated product, including its supplier offer count.
    """
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
    """
    List customers with their non-cancelled order counts and total spending.
    
    Returns:
    	list[CustomerOut]: Up to 500 customers, ordered by creation date descending, with aggregated order statistics.
    """
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
    """
    Summarize visitor activity, shopping funnel performance, and conversion metrics for a recent period.
    
    Parameters:
    	days (int): Number of days to include in the analytics window.
    
    Returns:
    	AnalyticsOut: Aggregated visitor, event, funnel, product, search, and daily visitor metrics.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    ev = AnalyticsEvent

    def count(evtype: str) -> int:
        """
        Count analytics events of a specified type within the reporting period.
        
        Parameters:
        	evtype (str): Event type to count.
        
        Returns:
        	int: Number of matching events recorded during the reporting period.
        """
        return db.scalar(
            select(func.count(ev.id)).where(ev.event_type == evtype, ev.created_at >= since)
        ) or 0

    def uniq(evtype: str | None = None) -> int:
        """
        Count distinct visitor sessions within the analytics time window.
        
        Parameters:
            evtype (str | None): Optional event type used to filter the sessions.
        
        Returns:
            int: Number of distinct sessions matching the filter.
        """
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
    """List coupons for administrative management.
    
    Returns:
    	list[Coupon]: Coupons ordered from newest to oldest.
    """
    return list(db.scalars(select(Coupon).order_by(Coupon.created_at.desc())))


@router.post("/coupons", response_model=CouponOut, status_code=201)
def admin_create_coupon(payload: CouponIn, db: Session = Depends(get_db)) -> Coupon:
    """
    Create a coupon with a normalized, unique code and supported discount type.
    
    Parameters:
        payload (CouponIn): Coupon details, including the code and discount type.
    
    Returns:
        Coupon: The newly created coupon.
    
    Raises:
        HTTPException: If the code is already in use or the discount type is invalid.
    """
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
    """
    Update the specified coupon with the provided fields.
    
    Parameters:
    	coupon_id (int): The coupon's identifier.
    	payload (CouponPatch): Fields to update on the coupon.
    
    Returns:
    	Coupon: The updated coupon.
    """
    coupon = db.get(Coupon, coupon_id)
    if coupon is None:
        raise HTTPException(status_code=404, detail="كود الخصم غير موجود")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(coupon, k, v)
    db.commit()
    db.refresh(coupon)
    return coupon


# ---------- review moderation ----------

@router.get("/reviews", response_model=list[AdminReviewOut])
def admin_list_reviews(
    status: str = Query(default="pending", pattern="^(pending|all)$"),
    db: Session = Depends(get_db),
) -> list[Review]:
    """
    List reviews for moderation, optionally limited to pending reviews.
    
    Parameters:
        status (str): Review filter, either "pending" or "all".
    
    Returns:
        list[Review]: Reviews ordered by creation time, limited to 500 results.
    """
    stmt = select(Review).order_by(Review.created_at.desc()).limit(500)
    if status == "pending":
        stmt = stmt.where(Review.is_approved.is_(False))
    return list(db.scalars(stmt))


@router.post("/reviews/{review_id}/approve", response_model=AdminReviewOut)
def admin_approve_review(review_id: int, db: Session = Depends(get_db)) -> Review:
    """
    Approve a customer review for publication.
    
    Parameters:
        review_id (int): The identifier of the review to approve.
        db (Session): The database session.
    
    Returns:
        Review: The approved review.
    """
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="المراجعة غير موجودة")
    review.is_approved = True
    db.commit()
    db.refresh(review)
    return review


@router.post("/reviews/{review_id}/reject")
def admin_reject_review(review_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Delete a review from the moderation queue.
    
    Parameters:
    	review_id (int): The identifier of the review to delete.
    
    Returns:
    	dict: A dictionary containing `{"deleted": True}`.
    """
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="المراجعة غير موجودة")
    db.delete(review)
    db.commit()
    return {"deleted": True}
