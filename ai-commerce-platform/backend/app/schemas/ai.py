from __future__ import annotations

from pydantic import BaseModel

from app.schemas.catalog import ProductOut


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    provider: str
    products: list[ProductOut] = []  # products referenced in the answer


class RecommendResponse(BaseModel):
    similar: list[ProductOut] = []
    also_bought: list[ProductOut] = []
