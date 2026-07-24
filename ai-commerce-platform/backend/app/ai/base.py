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
        """
        Generate an assistant reply using the conversation history and supplied context.
        
        Parameters:
            message (str): The user's current message.
            history (list[dict]): Previous conversation messages.
            context (str): Reference information, including catalog data and policies.
        
        Returns:
            str: The assistant's context-grounded reply.
        
        Raises:
            NotImplementedError: When called on the base provider instead of a concrete implementation.
        """
        raise NotImplementedError


def get_provider() -> AIProvider:
    """Select an AI provider based on application settings.
    
    Falls back to the stub provider when the configured provider is unsupported or
    its required API key is unavailable.
    
    Returns:
        AIProvider: The configured provider or a stub provider.
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
