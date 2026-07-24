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
    """
    Extract meaningful lowercase tokens from text.
    
    Parameters:
        text (str): Text to tokenize.
    
    Returns:
        list[str]: Tokens excluding stopwords and single-character words.
    """
    return [t for t in re.findall(r"[\w']+", text.lower()) if t not in _STOPWORDS and len(t) > 1]


class StubProvider(AIProvider):
    name = "stub"

    def chat(self, message: str, history: list[dict], context: str) -> str:
        """
        Finds the context lines that best match the user's message and presents up to four results.
        
        Parameters:
            message (str): The user's request used to identify matching context lines.
            history (list[dict]): Prior conversation messages.
            context (str): Product entries and policy facts to search.
        
        Returns:
            str: An Arabic response containing the closest matching context lines, or a fallback message when no matches are found.
        """
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
                "لم أجد تطابقاً قريباً في الكتالوج لطلبك. "
                "جرّب ذكر نوع المنتج أو الاستخدام أو ميزانيتك وسأقترح خيارات. "
                "(المساعد يعمل في وضع تجريبي بلا اتصال — أضف مفتاح API لتفعيل الذكاء الكامل.)"
            )

        bullet = "\n".join(f"• {line}" for line in top)
        return (
            "هذا ما وجدته مطابقاً لطلبك:\n\n"
            f"{bullet}\n\n"
            "تريد تفاصيل أكثر عن أي منها أو مقارنة بينها؟ "
            "(المساعد يعمل في وضع تجريبي بلا اتصال — أضف مفتاح API لتفعيل الذكاء الكامل.)"
        )
