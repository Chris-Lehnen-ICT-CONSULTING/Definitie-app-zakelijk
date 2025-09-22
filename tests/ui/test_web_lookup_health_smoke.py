import pytest


@pytest.mark.asyncio
async def test_web_lookup_health_smoke(monkeypatch):
    """Headless smoketest voor Web Lookup Health Check met mocks (geen netwerk).

    Simuleert de health-check flow door per provider exact één resultaat te
    retourneren via gemockte SRU en Wikipedia services.
    """

    from services.interfaces import LookupResult, WebSource, LookupRequest

    # Stub SRUService context manager met search()
    class _StubSRUService:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def search(self, term: str, endpoint: str, max_records: int = 1, collection=None):
            name_map = {
                "wetgeving_nl": "Wetgeving.nl",
                "overheid": "Overheid.nl",
                "rechtspraak": "Rechtspraak.nl",
                "overheid_zoek": "Overheid.nl Zoekservice",
            }
            name = name_map.get(endpoint, endpoint)
            return [
                LookupResult(
                    term=term,
                    source=WebSource(name=name, url=f"https://example/{endpoint}", confidence=1.0, is_juridical=True),
                    definition=f"Result for {term}",
                    success=True,
                    metadata={},
                )
            ]

    # Stub wikipedia_lookup function
    async def _stub_wikipedia_lookup(term: str):
        return LookupResult(
            term=term,
            source=WebSource(name="Wikipedia", url="https://example/wiki", confidence=0.8, is_juridical=False),
            definition=f"Wiki {term}",
            success=True,
            metadata={"wikipedia_title": term.title()},
        )

    # Patch de paden die ModernWebLookupService runtime importeert
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", _StubSRUService)
    monkeypatch.setattr(
        "services.web_lookup.wikipedia_service.wikipedia_lookup",
        _stub_wikipedia_lookup,
    )

    from services.modern_web_lookup_service import ModernWebLookupService

    svc = ModernWebLookupService()
    providers = ["wetgeving", "overheid", "rechtspraak", "wikipedia"]
    terms = {
        "wetgeving": "Wetboek",  # Wetgeving.nl
        "overheid": "ministerie",
        "rechtspraak": "ECLI:NL",
        "wikipedia": "Nederland",
    }

    for p in providers:
        req = LookupRequest(term=terms[p], sources=[p], max_results=1)
        res = await svc.lookup(req)
        assert res and len(res) == 1
        r = res[0]
        assert r.success is True
        assert r.source and r.source.name
        # URL en confidence ingevuld door stub
        assert r.source.url and r.source.confidence > 0.0

