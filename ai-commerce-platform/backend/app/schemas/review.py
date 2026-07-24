from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    title: str | None = Field(default=None, max_length=120)
    body: str = Field(min_length=1)


class ReviewOut(BaseModel):
    id: int
    rating: int
    title: str | None = None
    body: str
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewSummary(BaseModel):
    average: float
    count: int
    distribution: dict[int, int]  # {1:.., 2:.., ... 5:..}


class ReviewBlock(BaseModel):
    """What the product page needs in one call: summary + approved reviews."""

    summary: ReviewSummary
    items: list[ReviewOut]


class AdminReviewOut(BaseModel):
    id: int
    product_id: int
    user_id: int
    rating: int
    title: str | None = None
    body: str
    is_verified: bool
    is_approved: bool
    created_at: datetime

    model_config = {"from_attributes": True}
