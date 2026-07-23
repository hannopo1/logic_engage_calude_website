"""Small shared helpers."""
from __future__ import annotations

import re
import secrets


def slugify(text: str) -> str:
    """URL-safe slug that preserves Arabic letters.

    Lowercases, collapses whitespace to single hyphens, and drops characters
    that are not letters/digits/hyphens (Unicode-aware, so Arabic is kept).
    """
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^\w\-]", "", text, flags=re.UNICODE)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or secrets.token_hex(4)


def unique_slug(text: str, exists) -> str:
    """Return a slug not already taken. `exists(slug) -> bool`."""
    base = slugify(text)
    slug = base
    while exists(slug):
        slug = f"{base}-{secrets.token_hex(2)}"
    return slug
