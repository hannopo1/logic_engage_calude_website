"""Public analytics ingest — the storefront posts interaction events here.

No auth: keyed by the anonymous X-Session-Id header (same id the cart uses),
plus the logged-in user when available. Silently ignores unknown event types
so a bad client can never break the funnel.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional
from app.core.database import get_db
from app.models.analytics import EVENT_TYPES, AnalyticsEvent
from app.models.user import User
from app.schemas.merchant import EventIn

router = APIRouter()


@router.post("", status_code=202)
def track(
    payload: EventIn,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> dict:
    """
    Record a storefront analytics event when its event type is recognized.
    
    Parameters:
        payload (EventIn): Event data to record.
        x_session_id (str | None): Anonymous session identifier from the request header.
    
    Returns:
        dict: A result containing `ok=True` when the event is recorded, or `ok=False` for an unrecognized event type.
    """
    if payload.event_type not in EVENT_TYPES:
        return {"ok": False}
    db.add(
        AnalyticsEvent(
            event_type=payload.event_type,
            session_id=x_session_id,
            user_id=user.id if user else None,
            path=payload.path,
            product_id=payload.product_id,
            query=payload.query,
        )
    )
    db.commit()
    return {"ok": True}
