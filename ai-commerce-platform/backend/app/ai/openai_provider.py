"""OpenAI-backed assistant. Active only when AI_PROVIDER=openai and a key is set.

Uses the Chat Completions API over HTTP (httpx) to avoid a hard SDK dependency.
"""
from __future__ import annotations

import httpx

from app.ai.base import AIProvider
from app.core.config import settings

_SYSTEM = (
    "You are a helpful shopping assistant for an e-commerce store. "
    "Answer ONLY using the catalog and policy context provided. If the answer "
    "is not in the context, say you don't have that information. Never invent "
    "prices, stock, or products. Be concise and friendly. "
    "Reply in Arabic (Egyptian market) unless the customer writes in another language."
)


class OpenAIProvider(AIProvider):
    name = "openai"

    def chat(self, message: str, history: list[dict], context: str) -> str:
        """
        Generate a shopping assistant response using the provided conversation and catalog context.
        
        Parameters:
            message (str): The customer's question.
            history (list[dict]): Previous conversation turns.
            context (str): Catalog and policy information available to the assistant.
        
        Returns:
            str: The assistant's response.
        
        Raises:
            httpx.HTTPStatusError: If the OpenAI API request returns a non-success status.
        """
        messages = [{"role": "system", "content": _SYSTEM}]
        for turn in history[-6:]:
            role = "assistant" if turn.get("role") == "assistant" else "user"
            messages.append({"role": role, "content": turn.get("content", "")})
        messages.append(
            {"role": "user", "content": f"Context:\n{context}\n\nCustomer question: {message}"}
        )

        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": settings.OPENAI_MODEL, "max_tokens": 512, "messages": messages},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
