import asyncio
import time
import pytest


pytestmark = pytest.mark.smoke_web_lookup

@pytest.mark.asyncio
async def test_web_lookup_timeout_budget_respected(monkeypatch):
    """Ensure ModernWebLookupService respects LookupRequest.timeout for SRU.

    Uses a stub SRUService that sleeps longer than the timeout to trigger a timeout.
    """

    from services.interfaces import LookupRequest
    from services.modern_web_lookup_service import ModernWebLookupService

    class _SlowSRUService:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def search(self, term: str, endpoint: str, max_records: int = 3):
            await asyncio.sleep(0.2)
            return []

        def get_attempts(self):
            return []

    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", _SlowSRUService)

    svc = ModernWebLookupService()
    req = LookupRequest(term="t", sources=["overheid"], max_results=1, timeout=0.05)

    start = time.time()
    res = await svc.lookup(req)
    duration = time.time() - start

    # Should return quickly due to timeout and not hang for 0.2s
    assert duration < 0.15, f"Lookup took too long: {duration:.3f}s"
    assert res == []
