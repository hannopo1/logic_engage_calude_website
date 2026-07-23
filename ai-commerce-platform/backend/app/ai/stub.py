"""Zero-cost, no-key assistant.

RAG-lite: the router builds a `context` string from the catalog + store
policies and passes it here. The stub does keyword overlap scoring against
that context to produce a grounded, deterministic reply. It never invents
prices or facts outside the provided context.
"""
from __future__ import annotations

import re

from app.ai.base import AIProvider

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "for", "is", "are", "i", "you",
    "me", "my", "want", "need", "please", "can", "do", "does", "what", "which",
    "how", "much", "about", "with", "in", "on", "under", "best", "good",
}


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[\w']+", text.lower()) if t not in _STOPWORDS and len(t) > 1]


class StubProvider(AIProvider):
    name = "stub"

    def chat(self, message: str, history: list[dict], context: str) -> str:
        query_tokens = set(_tokens(message))

        # Rank context lines (each line is a product or a policy fact).
        scored: list[tuple[int, str]] = []
        for line in context.splitlines():
            line = line.strip()
            if not line:
                continue
            overlap = len(query_tokens & set(_tokens(line)))
            if overlap:
                scored.append((overlap, line))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [line for _, line in scored[:4]]

        if not top:
            return (
                "I couldn't find a close match in our catalog for that. "
                "Try naming a product type, a use case, or a budget and I'll suggest options. "
                "(Assistant running in offline demo mode — add an API key to enable full AI.)"
            )

        bullet = "\n".join(f"• {line}" for line in top)
        return (
            "Here's what I found that matches your request:\n\n"
            f"{bullet}\n\n"
            "Want more detail on any of these, or a comparison? "
            "(Assistant running in offline demo mode — add an API key to enable full AI.)"
        )
