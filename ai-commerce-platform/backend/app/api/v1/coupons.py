"""Public coupon validation — lets the storefront preview a discount before checkout."""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.coupon import CouponValidateIn, CouponValidateOut
from app.services import coupon_service

router = APIRouter()


@router.post("/validate", response_model=CouponValidateOut)
def validate(payload: CouponValidateIn, db: Session = Depends(get_db)) -> CouponValidateOut:
    subtotal = Decimal(str(payload.subtotal))
    coupon = coupon_service.find_valid(db, payload.code, subtotal)  # raises 400/404 if invalid
    discount = coupon_service.compute_discount(coupon, subtotal)
    return CouponValidateOut(
        code=coupon.code,
        kind=coupon.kind,
        discount=discount,
        new_total=max(Decimal("0"), subtotal - discount),
    )
