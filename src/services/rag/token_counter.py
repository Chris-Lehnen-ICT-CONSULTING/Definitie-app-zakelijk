"""
Token counting voor RAG chunking.

Wrapper om tiktoken voor exact token tellen.
"""

from __future__ import annotations

import logging

import tiktoken

logger = logging.getLogger(__name__)

# Lazy-loaded encoder (module-level singleton)
_encoder: tiktoken.Encoding | None = None


def _get_encoder() -> tiktoken.Encoding:
    """Haal de tiktoken encoder op (lazy-loaded singleton)."""
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding("cl100k_base")
    return _encoder


def tel_tokens(tekst: str) -> int:
    """Exact token count via tiktoken (cl100k_base / GPT-4)."""
    if not tekst:
        return 0
    return len(_get_encoder().encode(tekst))
