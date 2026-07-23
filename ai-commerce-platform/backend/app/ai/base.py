"""Pluggable AI provider abstraction.

The platform is AI-first but budget-zero: the default `stub` provider answers
from the product catalog with NO API key and NO cost. Setting AI_PROVIDER to
`anthropic` or `openai` (plus the matching key) swaps in a real LLM with no
code changes at any call site.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.config import settings


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    def chat(self, message: str, history: list[dict], context: str) -> str:
        """Return an assistant reply grounded in `context` (catalog + policies)."""
        raise NotImplementedError


def get_provider() -> AIProvider:
    """Factory: choose a provider from settings, falling back to the stub.

    Falls back to the stub whenever the selected provider is missing its key,
    so the platform never hard-fails on a misconfiguration.
    """
    provider = (settings.AI_PROVIDER or "stub").lower()

    if provider == "anthropic" and settings.ANTHROPIC_API_KEY:
        from app.ai.anthropic_provider import AnthropicProvider

        return AnthropicProvider()
    if provider == "openai" and settings.OPENAI_API_KEY:
        from app.ai.openai_provider import OpenAIProvider

        return OpenAIProvider()

    from app.ai.stub import StubProvider

    return StubProvider()
