"""
Ranking and deduplication for Web Lookup results (Epic 3).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


def _canonical_url(url: str) -> str:
    if not url:
        return ""
    try:
        p = urlparse(url)
        # Normalize scheme/host lower, remove default ports, strip trailing slash
        netloc = p.hostname or ""
        path = (p.path or "/").rstrip("/")
        canon = f"{p.scheme.lower()}://{netloc.lower()}{path}"
        if p.query:
            canon += f"?{p.query}"
        return canon
    except Exception:
        return url.strip().rstrip("/").lower()


def _final_score(item: dict[str, Any], provider_weights: dict[str, float]) -> float:
    w = provider_weights.get(item.get("provider", ""), 1.0)
    try:
        base = float(item.get("score", 0.0))
    except Exception:
        base = 0.0
    return w * base


def rank_and_dedup(
    items: list[dict[str, Any]], provider_weights: dict[str, float]
) -> list[dict[str, Any]]:
    """Apply deterministic ranking and deduplication.

    Dedup rules:
      1) Primary: canonical URL
      2) Secondary: content_hash

    Sorting:
      1) final_score DESC
      2) is_authoritative DESC
      3) title ASC
      4) url ASC
    """
    # Phase 1: dedup by content hash (keeps single best per hash across different URLs)
    by_hash: dict[str, dict[str, Any]] = {}

    def _better(a: dict[str, Any] | None, b: dict[str, Any]) -> dict[str, Any]:
        if a is None:
            return b
        return (
            a
            if _final_score(a, provider_weights) >= _final_score(b, provider_weights)
            else b
        )

    no_hash_items: list[dict[str, Any]] = []
    for it in items or []:
        ch = str(it.get("content_hash", "") or "")
        if ch:
            by_hash[ch] = _better(by_hash.get(ch), it)
        else:
            no_hash_items.append(it)

    # Phase 2: dedup no-hash items by canonical URL
    by_url: dict[str, dict[str, Any]] = {}
    for it in no_hash_items:
        url = _canonical_url(str(it.get("url", "")))
        if url:
            by_url[url] = _better(by_url.get(url), it)
        else:
            # No url, keep best by identity group
            key = f"_id_{id(it)}"
            by_url[key] = _better(by_url.get(key), it)

    deduped = list(by_hash.values()) + list(by_url.values())

    # Sort deterministically
    def _key(x: dict[str, Any]):
        return (
            -_final_score(x, provider_weights),
            -int(bool(x.get("is_authoritative", False))),
            str(x.get("title", "")),
            _canonical_url(str(x.get("url", ""))),
        )

    return sorted(deduped, key=_key)
