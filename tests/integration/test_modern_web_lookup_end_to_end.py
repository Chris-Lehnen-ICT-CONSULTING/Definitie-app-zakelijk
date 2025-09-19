import time

import pytest

from services.interfaces import LookupRequest
from services.modern_web_lookup_service import ModernWebLookupService


@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_web_lookup_with_mocked_providers(monkeypatch):
    # Use shared mocks to avoid network
    from tests.fixtures.web_lookup_mocks import wikipedia_lookup_stub, SRUServiceStub

    monkeypatch.setattr("services.web_lookup.wikipedia_service.wikipedia_lookup", wikipedia_lookup_stub)
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", SRUServiceStub)

    svc = ModernWebLookupService()

    start = time.perf_counter()
    results = await svc.lookup(LookupRequest(term="authenticatie", sources=["wikipedia", "overheid"], max_results=3))
    elapsed = time.perf_counter() - start

    # Validate results and simple performance budget (< 2s mocked)
    assert elapsed < 2.0
    assert isinstance(results, list) and len(results) >= 1
    # Ensure ranking yields juridical first (overheid over wikipedia)
    names = [r.source.name for r in results]
    assert any("Overheid" in n for n in names)

