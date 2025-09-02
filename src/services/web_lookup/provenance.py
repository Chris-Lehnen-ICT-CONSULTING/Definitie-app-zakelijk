"""
Provenance helpers to project lookup results into definition metadata (Epic 3).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def build_provenance(results: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a list of simplified source dicts for UI/storage.

    Retains essential fields and sorts by score descending.
    """
    simplified: list[dict[str, Any]] = []
    for r in results or []:
        simplified.append(
            {
                "provider": r.get("provider"),
                "title": r.get("title"),
                "url": r.get("url"),
                "snippet": r.get("snippet"),
                "score": float(r.get("score", 0.0) or 0.0),
                "used_in_prompt": bool(r.get("used_in_prompt", False)),
                "retrieved_at": r.get("retrieved_at"),
            }
        )

    simplified.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return simplified
