"""Small shared helpers."""
from __future__ import annotations

import re
import secrets


def slugify(text: str) -> str:
    """
    Create a lowercase, URL-friendly slug while preserving Unicode word characters.
    
    Returns:
    	str: The normalized slug, or a random hexadecimal token when the input produces an empty slug.
    """
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^\w\-]", "", text, flags=re.UNICODE)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or secrets.token_hex(4)


def unique_slug(text: str, exists) -> str:
    """
    Generate a unique URL-friendly slug from the provided text.
    
    Parameters:
        text (str): The text to convert into a slug.
        exists (Callable[[str], bool]): A predicate that reports whether a slug is already taken.
    
    Returns:
        str: The first generated slug that is not already taken.
    """
    base = slugify(text)
    slug = base
    while exists(slug):
        slug = f"{base}-{secrets.token_hex(2)}"
    return slug
