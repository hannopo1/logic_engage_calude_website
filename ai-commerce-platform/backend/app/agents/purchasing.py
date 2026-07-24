"""Purchasing agent — executes an approved PO according to the configured mode.

Modes (settings.AGENT_MODE):
  assisted   → build the complete purchase package (supplier link, qty, max
               price, customer ship-to address) and hold at `purchasing` until
               the operator confirms with the supplier order reference.
  simulation → execute instantly through SimulationConnector (fake ref, $0).
  api        → dispatch to the supplier's official connector; unconfigured
               connectors log a clear event and fall back to assisted flow.

We deliberately never automate a supplier's retail checkout (ToS/ban risk);
`api` mode only works through official connectors in agents/connectors.py.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.agents.connectors import NotConfiguredError, SimulationConnector, get_connector
from app.core.config import settings
from app.models.purchase_order import PurchaseOrder
from app.services import fulfillment_service


def build_purchase_package(po: PurchaseOrder) -> dict:
    """
    Build the data required to place a purchase order.
    
    Parameters:
        po (PurchaseOrder): The approved purchase order and its selected offer.
    
    Returns:
        dict: A purchase package containing supplier, product, pricing, quantity, currency, shipping, and execution instructions.
    """
    offer = po.offer
    supplier = offer.supplier if offer else None
    max_unit = (
        (Decimal(str(offer.supplier_price)) * Decimal("1.05")).quantize(Decimal("0.01"))
        if offer
        else None
    )
    return {
        "purchase_order_id": po.id,
        "supplier": supplier.name if supplier else None,
        "supplier_mode": supplier.mode if supplier else None,
        "product_url": offer.url if offer else None,
        "external_sku": offer.external_sku if offer else None,
        "quantity": po.quantity,
        "max_unit_price": str(max_unit) if max_unit else None,  # +5% price-drift guard
        "expected_total_cost": str(po.expected_cost) if po.expected_cost is not None else None,
        "currency": offer.currency if offer else settings.CURRENCY,
        "ship_to_address": po.order.shipping_address,
        "instructions": (
            "نفّذ الشراء على حساب المورد الرسمي، واستخدم عنوان العميل أعلاه كعنوان الشحن، "
            "ولا تتجاوز السعر الأقصى للوحدة. بعد الإتمام سجّل مرجع طلب المورد والتكلفة الفعلية."
        ),
    }


def execute_purchase(db: Session, po: PurchaseOrder) -> dict:
    """
    Execute an approved purchase according to the configured agent mode.
    
    Parameters:
        po (PurchaseOrder): The approved purchase order to execute.
    
    Returns:
        dict: A result payload containing the execution mode, outcome, and purchase package.
            Automatic modes report a purchased outcome; assisted flows report that operator
            execution is pending.
    """
    mode = settings.AGENT_MODE.lower()
    supplier = po.offer.supplier if po.offer else None

    # Simulation: full-auto with zero real money — for demos and tests.
    if mode == "simulation":
        fulfillment_service.transition(
            db, po, "purchasing", actor="agent", note="وضع المحاكاة: بدء تنفيذ الشراء", commit=False
        )
        result = SimulationConnector().place_order(po, po.order.shipping_address or "")
        po.supplier_order_ref = result.supplier_order_ref
        po.actual_cost = po.expected_cost
        fulfillment_service.transition(
            db, po, "purchased", actor="agent",
            note=f"تم الشراء آلياً (محاكاة) — مرجع المورد: {result.supplier_order_ref}",
        )
        return {"mode": "simulation", "result": "purchased", "package": build_purchase_package(po)}

    # API mode: only through official connectors.
    if mode == "api" and supplier is not None and supplier.mode == "api":
        connector = get_connector(supplier.slug)
        if connector is not None:
            try:
                fulfillment_service.transition(
                    db, po, "purchasing", actor="agent",
                    note=f"تنفيذ عبر API الرسمي للمورد '{supplier.name}'", commit=False,
                )
                result = connector.place_order(po, po.order.shipping_address or "")
                po.supplier_order_ref = result.supplier_order_ref
                po.actual_cost = po.expected_cost
                fulfillment_service.transition(
                    db, po, "purchased", actor="agent",
                    note=f"تم الشراء عبر API — مرجع المورد: {result.supplier_order_ref}",
                )
                return {"mode": "api", "result": "purchased", "package": build_purchase_package(po)}
            except NotConfiguredError as exc:
                db.rollback()
                fulfillment_service.transition(
                    db, po, "purchasing", actor="agent",
                    note=f"API غير مُهيّأ ({exc}) — تحويل للمسار المساعَد بانتظار تنفيذ المشغّل",
                )
                return {"mode": "assisted-fallback", "result": "awaiting_operator", "package": build_purchase_package(po)}

    # Default: assisted — hand the operator a ready-to-execute package.
    fulfillment_service.transition(
        db, po, "purchasing", actor="agent",
        note="حزمة الشراء جاهزة — بانتظار تنفيذ المشغّل وتسجيل مرجع المورد",
    )
    return {"mode": "assisted", "result": "awaiting_operator", "package": build_purchase_package(po)}
