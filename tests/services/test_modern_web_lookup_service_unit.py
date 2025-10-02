import asyncio
import time

import pytest

from services.interfaces import LookupRequest, LookupResult, WebSource
from services.modern_web_lookup_service import ModernWebLookupService


@pytest.mark.asyncio()
async def test_parallel_lookup_concurrency_and_timeout(monkeypatch):
    # Patch providers with small delays
    from tests.fixtures.web_lookup_mocks import SRUServiceStub, wikipedia_lookup_stub

    async def slow_wiki(term: str, language: str = "nl"):
        await asyncio.sleep(0.3)
        return await wikipedia_lookup_stub(term, language)

    class SlowSRU(SRUServiceStub):
        async def search(self, *a, **k):  # type: ignore[override]
            await asyncio.sleep(0.3)
            return await super().search(*a, **k)

    monkeypatch.setattr(
        "services.web_lookup.wikipedia_service.wikipedia_lookup", slow_wiki
    )
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", SlowSRU)

    svc = ModernWebLookupService()
    req = LookupRequest(
        term="authenticatie", sources=["wikipedia", "overheid"], max_results=2
    )

    start = time.perf_counter()
    results = await svc.lookup(req)
    elapsed = time.perf_counter() - start

    # Concurrency: total elapsed should be closer to 0.3s than 0.6s
    assert elapsed < 0.55, f"Expected concurrent lookups, took {elapsed:.2f}s"
    assert isinstance(results, list) and len(results) >= 1


@pytest.mark.asyncio()
async def test_error_handling_returns_empty_results(monkeypatch):
    # Providers raise → service should handle and return []
    async def broken_wiki(*a, **k):
        raise RuntimeError("boom")

    class BrokenSRU:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def search(self, *a, **k):
            raise RuntimeError("sru boom")

    monkeypatch.setattr(
        "services.web_lookup.wikipedia_service.wikipedia_lookup", broken_wiki
    )
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", BrokenSRU)

    svc = ModernWebLookupService()
    req = LookupRequest(term="x", sources=["wikipedia", "overheid"], max_results=2)

    results = await svc.lookup(req)
    assert results == []


@pytest.mark.asyncio()
async def test_ranking_and_dedup(monkeypatch):
    # Return two items with same URL/content but different weights to test dedup
    def make_result(
        name: str, url: str, score: float, is_juridical: bool, text: str
    ) -> LookupResult:
        return LookupResult(
            term="t",
            source=WebSource(
                name=name, url=url, confidence=score, is_juridical=is_juridical
            ),
            definition=text,
            success=True,
        )

    async def wiki(term: str, language: str = "nl"):
        return make_result("Wikipedia", "https://example.org/x", 0.7, False, "A")

    class SRUWithDup:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def search(self, *a, **k):
            # Same URL to force URL-based dedup, higher score
            return [make_result("Overheid.nl", "https://example.org/x", 1.0, True, "A")]

    monkeypatch.setattr("services.web_lookup.wikipedia_service.wikipedia_lookup", wiki)
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", SRUWithDup)

    svc = ModernWebLookupService()
    req = LookupRequest(term="t", sources=["wikipedia", "overheid"], max_results=5)
    results = await svc.lookup(req)

    # Dedup should collapse to single best (juridical/higher score)
    assert len(results) == 1
    assert "Overheid" in results[0].source.name
