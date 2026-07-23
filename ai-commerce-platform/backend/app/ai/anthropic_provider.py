"""Anthropic-backed assistant. Active only when AI_PROVIDER=anthropic and a key is set.

Uses the Messages API over HTTP (httpx) to avoid a hard SDK dependency.
"""
from __future__ import annotations

import httpx

from app.ai.base import AIProvider
from app.core.config import settings

_SYSTEM = (
    "You are a helpful shopping assistant for an e-commerce store. "
    "Answer ONLY using the catalog and policy context provided. If the answer "
    "is not in the context, say you don't have that information. Never invent "
    "prices, stock, or products. Be concise and friendly."
)


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def chat(self, message: str, history: list[dict], context: str) -> str:
        messages = []
        for turn in history[-6:]:
            role = "assistant" if turn.get("role") == "assistant" else "user"
            messages.append({"role": role, "content": turn.get("content", "")})
        messages.append(
            {"role": "user", "content": f"Context:\n{context}\n\nCustomer question: {message}"}
        )

        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.ANTHROPIC_MODEL,
                "max_tokens": 512,
                "system": _SYSTEM,
                "messages": messages,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return "".join(block.get("text", "") for block in data.get("content", [])).strip()
