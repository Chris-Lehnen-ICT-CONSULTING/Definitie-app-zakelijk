import pytest

pytestmark = pytest.mark.smoke_web_lookup


@pytest.mark.asyncio
async def test_wetgeving_parked_attempt_propagates(monkeypatch):
    """Simuleer Wetgeving.nl 503 'parked' en controleer dat attempt info doorkomt."""

    from services.interfaces import LookupRequest, LookupResult, WebSource
    from services.modern_web_lookup_service import ModernWebLookupService

    class _StubSRUService:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def search(self, term: str, endpoint: str, max_records: int = 3):
            # Geen resultaten
            return []

        def get_attempts(self):
            # Parked attempt zoals SRUService zou registreren
            return [
                {
                    "endpoint": "Wetgeving.nl",
                    "status": 503,
                    "parked": True,
                    "reason": "503 service unavailable",
                    "strategy": "dc",
                    "url": "https://wetten.overheid.nl/SRU/Search?...",
                }
            ]

    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", _StubSRUService)

    svc = ModernWebLookupService()
    req = LookupRequest(term="Sv", sources=["wetgeving"], max_results=1, timeout=1)
    res = await svc.lookup(req)

    # Geen resultaten, maar attempts moeten wel gelogd zijn
    assert res == []
    debug = getattr(svc, "_last_debug", None)
    assert debug
    assert isinstance(debug.get("attempts"), list)
    assert any(
        a.get("parked") is True for a in debug["attempts"]
    )  # parked attempt aanwezig
