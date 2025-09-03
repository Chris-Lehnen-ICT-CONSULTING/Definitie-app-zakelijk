"""
Contracts and shared types for Web Lookup (Epic 3).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class LookupErrorType(Enum):
    TIMEOUT = "Provider timeout exceeded"
    NETWORK = "Network connection failed"
    PARSE = "Response parsing failed"
    RATE_LIMIT = "Rate limit exceeded"
    AUTH = "Authentication failed"
    INVALID_RESPONSE = "Invalid/empty response"


@dataclass
class WebLookupResult:
    # Core
    provider: str
    source_label: str
    title: str
    url: str
    snippet: str
    score: float

    # Usage Tracking
    used_in_prompt: bool
    position_in_prompt: int

    # Metadata
    retrieved_at: datetime
    content_hash: str
    error: str | None | None = None

    # Juridical
    legal_refs: list[str] | None = None
    is_authoritative: bool = False
    legal_weight: float = 0.0

    # Linguistic
    is_plurale_tantum: bool = False
    requires_singular_check: bool = False

    # Caching
    cache_key: str = ""
    ttl_seconds: int = 3600
