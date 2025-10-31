"""
Unit tests for ModernWebLookupService with fully mocked providers.

No network calls are made; MediaWiki and SRU providers are patched to stubs.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import List

import pytest

# Ensure src on path
sys.path.insert(0, str(Path(__file__).parents[3] / "src"))

from services.interfaces import LookupRequest
from services.modern_web_lookup_service import ModernWebLookupService

# DISABLED: fixtures removed - will restore incrementally
# from tests.fixtures.web_lookup_mocks import SRUServiceStub, wikipedia_lookup_stub

# Skip all tests in this file until fixtures are restored
pytestmark = pytest.mark.skip(reason="Fixtures removed, will restore incrementally")


@pytest.mark.asyncio
async def test_parallel_lookup_mediawiki_and_sru(monkeypatch):
    """Lookup uses both MediaWiki and SRU providers concurrently and returns results."""
    # Patch MediaWiki wikipedia lookup
    monkeypatch.setattr(
        "services.web_lookup.wikipedia_service.wikipedia_lookup",
        wikipedia_lookup_stub,
        raising=False,
    )
    # Patch SRU service to return one result
    monkeypatch.setattr(
        "services.web_lookup.sru_service.SRUService",
        SRUServiceStub,
        raising=False,
    )

    svc = ModernWebLookupService()
    req = LookupRequest(
        term="authenticatie", sources=["wikipedia", "overheid"], max_results=2
    )
    results = await svc.lookup(req)

    assert isinstance(results, list)
    assert len(results) == 2
    # Provider/source labels present and confidence applied
    names = {r.source.name for r in results}
    assert {"Wikipedia", "Overheid.nl"}.issubset(names)
    # Confidence weights are applied (>0)
    assert all((r.source.confidence or 0.0) > 0 for r in results)


@pytest.mark.asyncio
async def test_error_in_sru_does_not_break_other_providers(monkeypatch):
    """SRU error is handled; MediaWiki result is still returned."""
    # MediaWiki ok
    monkeypatch.setattr(
        "services.web_lookup.wikipedia_service.wikipedia_lookup",
        wikipedia_lookup_stub,
        raising=False,
    )
    # SRU raises on search
    monkeypatch.setattr(
        "services.web_lookup.sru_service.SRUService",
        lambda: SRUServiceStub(raise_on_search=True),
        raising=False,
    )

    svc = ModernWebLookupService()
    req = LookupRequest(
        term="rechtspraak", sources=["wikipedia", "overheid"], max_results=2
    )
    results = await svc.lookup(req)

    # Only wikipedia survives
    assert len(results) >= 1
    assert any(r.source.name == "Wikipedia" for r in results)


@pytest.mark.asyncio
async def test_lookup_single_source(monkeypatch):
    """lookup_single_source returns a single LookupResult for the requested provider."""
    monkeypatch.setattr(
        "services.web_lookup.wikipedia_service.wikipedia_lookup",
        wikipedia_lookup_stub,
        raising=False,
    )
    svc = ModernWebLookupService()
    result = await svc.lookup_single_source("authenticatie", "wikipedia")
    assert result is not None
    assert result.source.name == "Wikipedia"
