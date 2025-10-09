"""
Unit tests voor Brave Search service.

Test coverage:
- Succesvolle lookups met verschillende result types
- Confidence scoring op basis van position en match quality
- Juridische bron detectie
- Error handling en graceful degradation
- MCP wrapper functionaliteit
- Synoniemen fallback
"""

import pytest

from services.interfaces import LookupResult, WebSource
from services.web_lookup.brave_search_service import BraveSearchService


@pytest.mark.asyncio
async def test_brave_search_successful_lookup():
    """Test succesvolle Brave Search lookup met mock MCP functie."""

    # Mock MCP search function
    async def mock_mcp_search(query: str, count: int):
        return [
            {
                "Title": "Rechtspersoon - Wikipedia",
                "Description": "Een rechtspersoon is een juridische constructie waardoor een organisatie zelfstandig rechten en plichten heeft.",
                "URL": "https://nl.wikipedia.org/wiki/Rechtspersoon",
            }
        ]

    async with BraveSearchService(
        count=5, enable_synonyms=False, mcp_search_function=mock_mcp_search
    ) as service:
        result = await service.lookup("rechtspersoon")

        assert result is not None
        assert result.success is True
        assert result.term == "rechtspersoon"
        assert "juridische constructie" in result.definition.lower()
        assert result.source.name == "Brave Search"
        assert "wikipedia.org" in result.source.url


@pytest.mark.asyncio
async def test_brave_search_confidence_scoring():
    """Test confidence scoring op basis van positie en match kwaliteit."""

    async def mock_mcp_search(query: str, count: int):
        return [
            {
                "Title": "rechtspersoon",  # Exacte match
                "Description": "Definitie van rechtspersoon",
                "URL": "https://example.com/1",
            },
            {
                "Title": "Over rechtspersonen en organisaties",  # Bevat term
                "Description": "Info over rechtspersonen",
                "URL": "https://example.com/2",
            },
            {
                "Title": "Juridische begrippen",  # Geen match
                "Description": "Verschillende begrippen",
                "URL": "https://example.com/3",
            },
        ]

    async with BraveSearchService(
        count=5, enable_synonyms=False, mcp_search_function=mock_mcp_search
    ) as service:
        result = await service.lookup("rechtspersoon")

        assert result is not None
        # Exacte title match (position 0) → hoge confidence (0.90 + 0.10 boost)
        assert result.source.confidence >= 0.95
        assert result.source.url == "https://example.com/1"


@pytest.mark.asyncio
async def test_brave_search_juridical_detection():
    """Test detectie van juridische bronnen."""

    async def mock_mcp_juridical(query: str, count: int):
        return [
            {
                "Title": "Artikel 1 Wetboek van Strafrecht",
                "Description": "Wettekst artikel 1 Sr",
                "URL": "https://wetten.overheid.nl/BWBR0001854/2024-01-01#Boek1",
            }
        ]

    async with BraveSearchService(
        count=5, enable_synonyms=False, mcp_search_function=mock_mcp_juridical
    ) as service:
        result = await service.lookup("artikel 1 sr")

        assert result is not None
        assert result.source.is_juridical is True
        assert "overheid.nl" in result.source.url


@pytest.mark.asyncio
async def test_brave_search_non_juridical():
    """Test niet-juridische bronnen."""

    async def mock_mcp_general(query: str, count: int):
        return [
            {
                "Title": "Python programming",
                "Description": "Learn Python basics",
                "URL": "https://python.org/docs",
            }
        ]

    async with BraveSearchService(
        count=5, enable_synonyms=False, mcp_search_function=mock_mcp_general
    ) as service:
        result = await service.lookup("python")

        assert result is not None
        assert result.source.is_juridical is False


@pytest.mark.asyncio
async def test_brave_search_no_results():
    """Test handling van lege resultaten."""

    async def mock_mcp_empty(query: str, count: int):
        return []

    async with BraveSearchService(
        count=5, enable_synonyms=False, mcp_search_function=mock_mcp_empty
    ) as service:
        result = await service.lookup("nonexistentterm12345")

        assert result is None


@pytest.mark.asyncio
async def test_brave_search_error_handling():
    """Test error handling bij MCP failures."""

    async def mock_mcp_error(query: str, count: int):
        raise RuntimeError("MCP tool failed")

    async with BraveSearchService(
        count=5, enable_synonyms=False, mcp_search_function=mock_mcp_error
    ) as service:
        result = await service.lookup("test")

        # MCP error → returns None (graceful degradation)
        assert result is None


@pytest.mark.asyncio
async def test_brave_search_metadata():
    """Test metadata in results."""

    async def mock_mcp_search(query: str, count: int):
        return [
            {
                "Title": "Test Result",
                "Description": "Test description",
                "URL": "https://example.com/test",
            }
        ]

    async with BraveSearchService(
        count=5, enable_synonyms=False, mcp_search_function=mock_mcp_search
    ) as service:
        result = await service.lookup("test")

        assert result is not None
        assert "title" in result.metadata
        assert "search_position" in result.metadata
        assert "is_juridical" in result.metadata
        assert "retrieved_at" in result.metadata
        assert "content_hash" in result.metadata
        assert result.metadata["search_engine"] == "brave"


@pytest.mark.asyncio
async def test_brave_search_context():
    """Test context field formatting."""

    async def mock_mcp_search(query: str, count: int):
        return [
            {
                "Title": "Rechtspersoon volgens CBS",
                "Description": "Definitie rechtspersoon",
                "URL": "https://cbs.nl/rechtspersoon",
            }
        ]

    async with BraveSearchService(
        count=5, enable_synonyms=False, mcp_search_function=mock_mcp_search
    ) as service:
        result = await service.lookup("rechtspersoon")

        assert result is not None
        assert result.context == "Brave Search: Rechtspersoon volgens CBS"


@pytest.mark.asyncio
async def test_brave_search_cbs_juridical_detection():
    """Test dat CBS wordt herkend als juridische bron."""

    async def mock_mcp_cbs(query: str, count: int):
        return [
            {
                "Title": "Rechtspersoon | CBS",
                "Description": "Een juridische constructie waardoor een organisatie, net als een natuurlijke persoon, in het recht als rechtssubject is erkend als drager van wettelijke rechten en plichten.",
                "URL": "https://www.cbs.nl/nl-nl/onze-diensten/methoden/begrippen/rechtspersoon",
            }
        ]

    async with BraveSearchService(
        count=5, enable_synonyms=False, mcp_search_function=mock_mcp_cbs
    ) as service:
        result = await service.lookup("rechtspersoon")

        assert result is not None
        assert result.source.is_juridical is True, "CBS should be detected as juridical"
        assert "cbs.nl" in result.source.url


@pytest.mark.asyncio
async def test_brave_search_position_confidence_decay():
    """Test dat confidence afneemt per positie."""

    async def mock_mcp_multiple(query: str, count: int):
        return [
            {"Title": "Result 1", "Description": "First", "URL": "https://ex.com/1"},
            {"Title": "Result 2", "Description": "Second", "URL": "https://ex.com/2"},
            {"Title": "Result 3", "Description": "Third", "URL": "https://ex.com/3"},
        ]

    async with BraveSearchService(
        count=5, enable_synonyms=False, mcp_search_function=mock_mcp_multiple
    ) as service:
        result = await service.lookup("test")

        # Should get result from position 0 (best) with highest confidence
        assert result is not None
        # Position 0 = base 0.90
        assert result.source.confidence >= 0.85


@pytest.mark.asyncio
async def test_brave_search_juridical_keyword_detection():
    """Test detectie van juridische keywords in title/description."""

    async def mock_mcp_juridical_keyword(query: str, count: int):
        return [
            {
                "Title": "Juridisch advies over strafrecht",
                "Description": "Informatie over artikel 51 Wetboek van Strafrecht",
                "URL": "https://example.com/advies",
            }
        ]

    async with BraveSearchService(
        count=5, enable_synonyms=False, mcp_search_function=mock_mcp_juridical_keyword
    ) as service:
        result = await service.lookup("strafrecht")

        assert result is not None
        # Should be marked juridical based on keywords
        assert result.source.is_juridical is True


@pytest.mark.asyncio
async def test_brave_search_standalone_function():
    """Test standalone brave_search_lookup functie."""
    from services.web_lookup.brave_search_service import brave_search_lookup

    async def mock_mcp_search(query: str, count: int):
        return [
            {
                "Title": "Test",
                "Description": "Test description",
                "URL": "https://example.com",
            }
        ]

    result = await brave_search_lookup(
        "test", count=5, mcp_search_function=mock_mcp_search
    )

    assert result is not None
    assert result.success is True
    assert result.term == "test"


@pytest.mark.asyncio
async def test_brave_search_without_mcp_function():
    """Test graceful degradation zonder MCP functie."""

    # Service zonder MCP function → should handle gracefully
    async with BraveSearchService(count=5, enable_synonyms=False) as service:
        result = await service.lookup("test")

        # Should return None (geen crash)
        assert result is None


@pytest.mark.asyncio
async def test_brave_search_confidence_boost_for_title_prefix():
    """Test confidence boost voor title prefix matches."""

    async def mock_mcp_prefix(query: str, count: int):
        return [
            {
                "Title": "rechtspersoon in het Nederlands recht",  # Prefix match
                "Description": "Uitleg",
                "URL": "https://example.com",
            }
        ]

    async with BraveSearchService(
        count=5, enable_synonyms=False, mcp_search_function=mock_mcp_prefix
    ) as service:
        result = await service.lookup("rechtspersoon")

        assert result is not None
        # Prefix match → boost (base 0.90 + 0.08)
        assert result.source.confidence >= 0.95


@pytest.mark.asyncio
async def test_brave_search_confidence_for_description_match():
    """Test confidence voor term in description."""

    async def mock_mcp_desc(query: str, count: int):
        return [
            {
                "Title": "Juridische begrippen",  # Geen match in title
                "Description": "Uitleg over rechtspersoon en andere begrippen",  # Match in desc
                "URL": "https://example.com",
            }
        ]

    async with BraveSearchService(
        count=5, enable_synonyms=False, mcp_search_function=mock_mcp_desc
    ) as service:
        result = await service.lookup("rechtspersoon")

        assert result is not None
        # Term in description → kleine boost (base 0.90 + 0.03)
        assert 0.88 <= result.source.confidence <= 0.95
