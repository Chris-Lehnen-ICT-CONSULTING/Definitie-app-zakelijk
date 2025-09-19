#!/usr/bin/env python3
"""
Quick test script for ModernWebLookupService.

Usage:
  source .venv/bin/activate
  python scripts/test_web_lookup.py toetsing

Prints number of results and a compact summary for each.
Respects env var WEB_LOOKUP_TIMEOUT_SECONDS.
"""

import asyncio
import os
import sys
from typing import Any


async def main(term: str) -> int:
    try:
        from services.modern_web_lookup_service import ModernWebLookupService
        from services.interfaces import LookupRequest
    except Exception as e:
        print(f"Import error: {e}")
        return 2

    timeout = float(os.getenv("WEB_LOOKUP_TIMEOUT_SECONDS", "6.0"))
    print(f"Testing web lookup for term: '{term}' (timeout={timeout}s)")

    service = ModernWebLookupService()
    req = LookupRequest(term=term, max_results=3, include_examples=False, timeout=timeout)
    try:
        results = await service.lookup(req)
    except Exception as e:
        print(f"Lookup error: {type(e).__name__}: {e}")
        return 3

    n = len(results) if results else 0
    print(f"Results: {n}")
    for i, r in enumerate(results or []):
        title = None
        if isinstance(getattr(r, "metadata", None), dict):
            title = r.metadata.get("dc_title") or r.metadata.get("wikipedia_title")
        title = title or getattr(r.source, "name", "")
        url = getattr(r.source, "url", "") or ""
        conf = getattr(r.source, "confidence", 0.0)
        print(f"{i+1}. {getattr(r.source, 'name', '')} — {title} (score={conf:.2f}) {url}")

    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_web_lookup.py <term>")
        sys.exit(1)
    term = " ".join(sys.argv[1:])
    sys.exit(asyncio.run(main(term)))
