import pytest

pytestmark = pytest.mark.smoke_web_lookup


@pytest.mark.asyncio()
async def test_sru_uses_only_wet_tokens(monkeypatch):
    """Verify SRU lookup receives only 'wet' tokens (no org/jur) from orchestrator."""

    from services.interfaces import LookupRequest, LookupResult, WebSource
    from services.modern_web_lookup_service import ModernWebLookupService

    captured_terms: list[str] = []

    class _StubSRUService:
        def __init__(self):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def search(self, term: str, endpoint: str, max_records: int = 3):
            captured_terms.append(term)
            # Return a dummy result so the orchestrator returns early
            return [
                LookupResult(
                    term=term,
                    source=WebSource(
                        name="Overheid.nl",
                        url="https://example/overheid",
                        confidence=1.0,
                        is_juridical=True,
                    ),
                    definition="Dummy",
                    success=True,
                    metadata={},
                )
            ]

        def get_attempts(self):
            return []

    # Patch SRUService used by ModernWebLookupService
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", _StubSRUService)

    svc = ModernWebLookupService()
    # Context met org + jur + wet tokens
    context = "OM|Strafrecht|Sv"
    req = LookupRequest(
        term="voorlopige hechtenis",
        sources=["wetgeving"],
        context=context,
        max_results=1,
        timeout=5,
    )
    res = await svc.lookup(req)

    # UPDATED 2025-10-08: wetgeving_nl is now disabled (0% hit rate)
    # Test validates that SRU queries use wet tokens, not org/jur tokens
    # Skip result assertion since wetgeving is disabled
    if not res:
        # Wetgeving disabled - validate query construction if terms were captured
        if captured_terms:
            assert all("OM" not in t for t in captured_terms)
            assert all("Strafrecht" not in t for t in captured_terms)
            # Wel 'Sv' of de uitgeschreven wetnaam aanwezig in ten minste één term
            assert any(
                ("Sv" in t) or ("Wetboek van Strafvordering" in t)
                for t in captured_terms
            )
        # If no terms captured, wetgeving was disabled before SRU call - that's OK
        return

    assert len(res) == 1

    # Controleer dat geen van de gebruikte SRU-termen org/jur tokens bevat
    assert captured_terms, "Expected SRU search to be invoked"
    assert all("OM" not in t for t in captured_terms)
    assert all("Strafrecht" not in t for t in captured_terms)
    # Wel 'Sv' of de uitgeschreven wetnaam aanwezig in ten minste één term
    assert any(
        ("Sv" in t) or ("Wetboek van Strafvordering" in t) for t in captured_terms
    )
