"""
End-to-end integration tests voor Brave Search in web lookup flow.

Test de volledige integratie van Brave Search in ModernWebLookupService,
inclusief ranking, deduplicatie en mixing met andere providers.
"""

import pytest

from services.interfaces import LookupRequest, LookupResult, WebSource
from services.modern_web_lookup_service import ModernWebLookupService


@pytest.mark.asyncio
async def test_brave_search_integrated_in_lookup_flow(monkeypatch):
    """Test dat Brave Search wordt aangeroepen in normale lookup flow."""

    brave_called = False

    # Mock Brave Search service
    class MockBraveService:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def lookup(self, term: str):
            nonlocal brave_called
            brave_called = True
            return LookupResult(
                term=term,
                source=WebSource(
                    name="Brave Search",
                    url="https://brave.com/search",
                    confidence=0.85,
                    api_type="brave_mcp",
                ),
                definition="Brave Search result",
                success=True,
            )

    # Mock andere services om ze te disablen
    async def mock_wiki(*args, **kwargs):
        return None

    class MockSRU:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def search(self, *args, **kwargs):
            return []

        def get_attempts(self):
            return []

    monkeypatch.setattr(
        "services.web_lookup.brave_search_service.BraveSearchService", MockBraveService
    )
    monkeypatch.setattr(
        "services.web_lookup.wikipedia_service.wikipedia_lookup", mock_wiki
    )
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", MockSRU)

    service = ModernWebLookupService()
    request = LookupRequest(term="rechtspersoon", max_results=5)

    results = await service.lookup(request)

    assert brave_called, "Brave Search should be called"
    assert len(results) > 0
    # Check dat Brave Search result in resultaten zit
    brave_results = [r for r in results if "Brave" in r.source.name]
    assert len(brave_results) > 0, "Brave Search result should be in results"


@pytest.mark.asyncio
async def test_brave_search_mixed_with_wikipedia(monkeypatch):
    """Test mixing van Brave Search en Wikipedia resultaten."""

    # Mock Brave Search
    class MockBraveService:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def lookup(self, term: str):
            return LookupResult(
                term=term,
                source=WebSource(
                    name="Brave Search",
                    url="https://example.com/brave",
                    confidence=0.85,
                    api_type="brave_mcp",
                ),
                definition="Brave definition",
                success=True,
            )

    # Mock Wikipedia
    async def mock_wiki(term: str, language: str = "nl"):
        return LookupResult(
            term=term,
            source=WebSource(
                name="Wikipedia",
                url="https://nl.wikipedia.org/wiki/Test",
                confidence=0.70,
                api_type="mediawiki",
            ),
            definition="Wikipedia definition",
            success=True,
        )

    # Disable SRU
    class MockSRU:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def search(self, *args, **kwargs):
            return []

        def get_attempts(self):
            return []

    monkeypatch.setattr(
        "services.web_lookup.brave_search_service.BraveSearchService", MockBraveService
    )
    monkeypatch.setattr(
        "services.web_lookup.wikipedia_service.wikipedia_lookup", mock_wiki
    )
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", MockSRU)

    service = ModernWebLookupService()
    request = LookupRequest(term="test", max_results=5)

    results = await service.lookup(request)

    # Should have both Brave and Wikipedia results
    assert len(results) >= 2, "Should have multiple results"
    sources = [r.source.name for r in results]
    assert any("Brave" in s for s in sources), "Should have Brave Search result"
    assert any("Wikipedia" in s for s in sources), "Should have Wikipedia result"


@pytest.mark.asyncio
async def test_brave_search_ranking_with_confidence(monkeypatch):
    """Test dat Brave Search correct wordt gerankt op basis van confidence."""

    # Mock Brave Search met hoge confidence
    class MockBraveService:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def lookup(self, term: str):
            return LookupResult(
                term=term,
                source=WebSource(
                    name="Brave Search",
                    url="https://example.com/brave",
                    confidence=0.95,  # Hoge confidence
                    api_type="brave_mcp",
                ),
                definition="High confidence Brave result",
                success=True,
            )

    # Mock Wikipedia met lagere confidence
    async def mock_wiki(term: str, language: str = "nl"):
        return LookupResult(
            term=term,
            source=WebSource(
                name="Wikipedia",
                url="https://nl.wikipedia.org/wiki/Test",
                confidence=0.65,  # Lagere confidence
                api_type="mediawiki",
            ),
            definition="Lower confidence Wikipedia result",
            success=True,
        )

    class MockSRU:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def search(self, *args, **kwargs):
            return []

        def get_attempts(self):
            return []

    monkeypatch.setattr(
        "services.web_lookup.brave_search_service.BraveSearchService", MockBraveService
    )
    monkeypatch.setattr(
        "services.web_lookup.wikipedia_service.wikipedia_lookup", mock_wiki
    )
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", MockSRU)

    service = ModernWebLookupService()
    request = LookupRequest(term="test", max_results=5)

    results = await service.lookup(request)

    # Brave Search (0.95) should be ranked higher than Wikipedia (0.65)
    assert len(results) >= 1
    # First result should be Brave Search due to higher confidence
    assert "Brave" in results[0].source.name, "Brave Search should be ranked first"


@pytest.mark.asyncio
async def test_brave_search_in_juridical_context(monkeypatch):
    """Test dat Brave Search wordt gebruikt in juridische context."""

    brave_called = False

    class MockBraveService:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def lookup(self, term: str):
            nonlocal brave_called
            brave_called = True
            return LookupResult(
                term=term,
                source=WebSource(
                    name="Brave Search",
                    url="https://rechtspraak.nl/test",
                    confidence=0.90,
                    is_juridical=True,  # Juridische bron
                    api_type="brave_mcp",
                ),
                definition="Juridische definitie via Brave",
                success=True,
            )

    async def mock_wiki(*args, **kwargs):
        return None

    class MockSRU:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def search(self, *args, **kwargs):
            return []

        def get_attempts(self):
            return []

    monkeypatch.setattr(
        "services.web_lookup.brave_search_service.BraveSearchService", MockBraveService
    )
    monkeypatch.setattr(
        "services.web_lookup.wikipedia_service.wikipedia_lookup", mock_wiki
    )
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", MockSRU)

    service = ModernWebLookupService()
    # Juridische context → Brave Search moet worden aangeroepen
    request = LookupRequest(
        term="onherroepelijk vonnis", context="Strafrecht | Wetboek van Strafvordering"
    )

    results = await service.lookup(request)

    assert brave_called, "Brave Search should be called for juridical context"
    assert len(results) > 0


@pytest.mark.asyncio
async def test_brave_search_deduplication(monkeypatch):
    """Test deduplicatie van Brave Search resultaten met andere bronnen."""

    # Mock Brave Search en Wikipedia met ZELFDE URL
    class MockBraveService:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def lookup(self, term: str):
            return LookupResult(
                term=term,
                source=WebSource(
                    name="Brave Search",
                    url="https://duplicate.com/page",  # Duplicate URL
                    confidence=0.85,
                    api_type="brave_mcp",
                ),
                definition="Same content",
                success=True,
            )

    async def mock_wiki(term: str, language: str = "nl"):
        return LookupResult(
            term=term,
            source=WebSource(
                name="Wikipedia",
                url="https://duplicate.com/page",  # Duplicate URL
                confidence=0.70,
                api_type="mediawiki",
            ),
            definition="Same content",
            success=True,
        )

    class MockSRU:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def search(self, *args, **kwargs):
            return []

        def get_attempts(self):
            return []

    monkeypatch.setattr(
        "services.web_lookup.brave_search_service.BraveSearchService", MockBraveService
    )
    monkeypatch.setattr(
        "services.web_lookup.wikipedia_service.wikipedia_lookup", mock_wiki
    )
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", MockSRU)

    service = ModernWebLookupService()
    request = LookupRequest(term="test", max_results=5)

    results = await service.lookup(request)

    # Deduplication should keep only one result
    assert len(results) == 1, f"Duplicate URL should be deduplicated, got {len(results)} results"
    # Either Brave or Wikipedia - doesn't matter which wins, dedup is what counts
    assert results[0].source.url == "https://duplicate.com/page"


@pytest.mark.asyncio
async def test_brave_search_configuration_loaded():
    """Test dat Brave Search configuratie correct wordt geladen."""

    service = ModernWebLookupService()

    # Check dat brave_search in sources staat
    assert "brave_search" in service.sources, "Brave Search should be in sources"

    brave_config = service.sources["brave_search"]
    assert brave_config.name == "Brave Search"
    assert brave_config.api_type == "brave_mcp"
    assert brave_config.enabled is True
    assert brave_config.confidence_weight == 0.85  # Van config


@pytest.mark.asyncio
async def test_brave_search_in_source_determination():
    """Test dat Brave Search in source determination logica zit."""

    service = ModernWebLookupService()

    # Test juridische query
    request_jur = LookupRequest(term="artikel 51 sr")
    sources_jur = service._determine_sources(request_jur)
    assert (
        "brave_search" in sources_jur
    ), "Brave Search should be in juridical source list"

    # Test algemene query
    request_gen = LookupRequest(term="algemeen begrip")
    sources_gen = service._determine_sources(request_gen)
    assert (
        "brave_search" in sources_gen
    ), "Brave Search should be in general source list"


@pytest.mark.asyncio
async def test_brave_search_provider_key_inference():
    """Test dat provider key correct wordt afgeleid voor Brave Search."""

    service = ModernWebLookupService()

    # Test result met Brave Search naam
    result = LookupResult(
        term="test",
        source=WebSource(
            name="Brave Search",
            url="https://example.com",
            confidence=0.85,
            api_type="brave_mcp",
        ),
        definition="test",
        success=True,
    )

    provider_key = service._infer_provider_key(result)
    assert provider_key == "brave_search", f"Expected 'brave_search', got '{provider_key}'"
