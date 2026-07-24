"""Coupon validation + discount computation. Single source of truth used by
the checkout flow and the public /coupons/validate endpoint."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.coupon import Coupon


def find_valid(db: Session, code: str, subtotal: Decimal) -> Coupon:
    """
    Validate a coupon code for the specified order subtotal.
    
    Parameters:
        code (str): Coupon code to validate.
        subtotal (Decimal): Order subtotal used to check the coupon's minimum requirement.
    
    Returns:
        Coupon: The valid coupon.
    
    Raises:
        HTTPException: If the coupon is not found or fails activation, expiration, usage-limit, or minimum-order checks.
    """
    code = (code or "").strip().upper()
    coupon = db.scalar(select(Coupon).where(func.upper(Coupon.code) == code))
    if coupon is None:
        raise HTTPException(status_code=404, detail="كود الخصم غير موجود")
    if not coupon.is_active:
        raise HTTPException(status_code=400, detail="كود الخصم غير مفعّل")
    if coupon.expires_at is not None and coupon.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="انتهت صلاحية كود الخصم")
    if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
        raise HTTPException(status_code=400, detail="تم استنفاد كود الخصم")
    if subtotal < Decimal(str(coupon.min_order)):
        raise HTTPException(
            status_code=400,
            detail=f"الحد الأدنى للطلب لاستخدام الكود هو {coupon.min_order} ج.م",
        )
    return coupon


def compute_discount(coupon: Coupon, subtotal: Decimal) -> Decimal:
    """
    Calculate the discount amount for a coupon and subtotal.
    
    Parameters:
        coupon (Coupon): Coupon defining the discount type and value.
        subtotal (Decimal): Order subtotal used to calculate the discount.
    
    Returns:
        Decimal: Discount rounded to two decimal places and capped at the subtotal.
    """
    if coupon.kind == "fixed":
        disc = Decimal(str(coupon.value))
    else:  # percent
        disc = subtotal * Decimal(str(coupon.value)) / Decimal("100")
    disc = disc.quantize(Decimal("0.01"))
    return min(disc, subtotal)
