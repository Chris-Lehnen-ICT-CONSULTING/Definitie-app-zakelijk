"""
Sanitization utilities for Web Lookup snippets (Epic 3).
"""

from __future__ import annotations

import html
import re

TAG_RE = re.compile(r"<\/?(script|style|iframe|object|embed|form)[^>]*>", re.IGNORECASE)
PROTOCOL_RE = re.compile(r"(?i)\b(?:javascript|vbscript|data):")
HTML_TAGS_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def sanitize_snippet(text: str, max_length: int = 500) -> str:
    """Sanitize provider snippets according to epic policy.

    - Strip dangerous tags (script, style, iframe, object, embed, form)
    - Remove remaining HTML tags
    - Block dangerous protocols (javascript:, data:, vbscript:)
    - Collapse whitespace and truncate to max_length
    - HTML-escape entities to be safe in text UIs
    """
    if not text:
        return ""

    # Remove dangerous tags completely
    cleaned = TAG_RE.sub("", text)
    # Remove all remaining HTML tags but keep inner text
    cleaned = HTML_TAGS_RE.sub(" ", cleaned)
    # Block protocols in any residual text
    cleaned = PROTOCOL_RE.sub("", cleaned)
    # Normalize whitespace
    cleaned = WS_RE.sub(" ", cleaned).strip()
    # Truncate
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    # Escape entities for UI safety
    cleaned = html.escape(cleaned, quote=False)
    return cleaned
