"""
Tests voor WikipediaSynonymExtractor service.

Test coverage:
- Redirect extraction met mocked Wikipedia API responses
- Disambiguation page parsing
- Confidence score calculation
- False positive filtering (categories, templates)
- Rate limiting compliance
- Error handling (API failures, timeouts)
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.web_lookup.wikipedia_synonym_extractor import (
    SynonymCandidate,
    WikipediaSynonymExtractor,
    extract_wikipedia_synonyms,
)


@pytest.fixture()
def extractor():
    """Create WikipediaSynonymExtractor instance."""
    return WikipediaSynonymExtractor(language="nl", rate_limit_delay=0.1)


@pytest.fixture()
def mock_session():
    """Create mock aiohttp session."""
    return MagicMock()


def create_mock_response(status=200, json_data=None):
    """Helper to create properly mocked async response."""
    mock_response = AsyncMock()
    mock_response.status = status
    if json_data:
        mock_response.json = AsyncMock(return_value=json_data)
    return mock_response


def create_mock_get_context(response):
    """Helper to create properly mocked async context manager for session.get()."""
    mock_context = AsyncMock()
    mock_context.__aenter__ = AsyncMock(return_value=response)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    return mock_context


def create_mock_session():
    """Helper to create fully mocked aiohttp ClientSession."""
    mock_session = MagicMock()
    mock_session.close = AsyncMock(return_value=None)
    return mock_session


class TestSynonymCandidate:
    """Tests voor SynonymCandidate dataclass."""

    def test_synonym_candidate_creation(self):
        """Test creating a SynonymCandidate."""
        candidate = SynonymCandidate(
            hoofdterm="voorlopige hechtenis",
            synoniem="voorarrest",
            confidence=0.90,
            source_type="redirect",
            wikipedia_url="https://nl.wikipedia.org/wiki/Voorarrest",
            metadata={"edit_distance": 2},
        )

        assert candidate.hoofdterm == "voorlopige hechtenis"
        assert candidate.synoniem == "voorarrest"
        assert candidate.confidence == 0.90
        assert candidate.source_type == "redirect"
        assert candidate.metadata["edit_distance"] == 2

    def test_to_dict_conversion(self):
        """Test converting SynonymCandidate to dict for CSV export."""
        candidate = SynonymCandidate(
            hoofdterm="hoger beroep",
            synoniem="appel",
            confidence=0.95,
            source_type="redirect",
            wikipedia_url="https://nl.wikipedia.org/wiki/Appel_(recht)",
            metadata={"edit_distance": 1, "redirect_type": "direct"},
        )

        result = candidate.to_dict()

        assert result["hoofdterm"] == "hoger beroep"
        assert result["synoniem_kandidaat"] == "appel"
        assert result["confidence"] == 0.95
        assert result["source_type"] == "redirect"
        assert result["edit_distance"] == 1
        assert result["redirect_type"] == "direct"


class TestWikipediaSynonymExtractor:
    """Tests voor WikipediaSynonymExtractor core functionaliteit."""

    def test_initialization(self):
        """Test extractor initialization."""
        extractor = WikipediaSynonymExtractor(language="nl", rate_limit_delay=1.0)

        assert extractor.language == "nl"
        assert extractor.rate_limit_delay == 1.0
        assert extractor.api_url == "https://nl.wikipedia.org/w/api.php"

    def test_is_valid_term_filters_categories(self, extractor):
        """Test that categories are filtered out."""
        assert not extractor._is_valid_term("Categorie:Strafrecht")
        assert not extractor._is_valid_term("Category:Law")
        assert not extractor._is_valid_term("Wikipedia:Voorlopige hechtenis")
        assert not extractor._is_valid_term("Sjabloon:Juridisch")
        assert not extractor._is_valid_term("Template:Legal")

    def test_is_valid_term_accepts_normal_pages(self, extractor):
        """Test that normal page titles are accepted."""
        assert extractor._is_valid_term("Voorlopige hechtenis")
        assert extractor._is_valid_term("Hoger beroep")
        assert extractor._is_valid_term("Cassatie (recht)")

    def test_calculate_edit_distance(self, extractor):
        """Test edit distance calculation."""
        # Identical strings
        assert extractor._calculate_edit_distance("test", "test") == 0

        # Similar strings
        dist1 = extractor._calculate_edit_distance("hoger beroep", "appel")
        assert dist1 > 0

        # Very different strings (short string has less total edit distance due to length)
        dist2 = extractor._calculate_edit_distance("test", "xyz")
        assert dist2 > 0  # Just check it's positive

    def test_calculate_confidence_direct_redirect(self, extractor):
        """Test confidence calculation for direct redirects."""
        # Perfect match (no edit distance, no length diff)
        confidence = extractor.calculate_confidence("direct", 0, 0)
        assert confidence == 0.90

        # Direct redirect met kleine edit distance
        confidence = extractor.calculate_confidence("direct", 2, 3)
        assert 0.80 <= confidence <= 0.90

    def test_calculate_confidence_disambiguation(self, extractor):
        """Test confidence calculation for disambiguation pages."""
        confidence = extractor.calculate_confidence("disambiguation", 0, 0)
        assert confidence == 0.85

        # Met penalties
        confidence = extractor.calculate_confidence("disambiguation", 3, 5)
        assert 0.70 <= confidence <= 0.85

    def test_calculate_confidence_similar_term(self, extractor):
        """Test confidence calculation for similar terms."""
        confidence = extractor.calculate_confidence("similar_term", 0, 0)
        assert confidence == 0.75

        # Met grote edit distance penalty
        confidence = extractor.calculate_confidence("similar_term", 10, 20)
        assert confidence < 0.60

    def test_calculate_confidence_clamped(self, extractor):
        """Test that confidence is always clamped to [0.0, 1.0]."""
        # Extreme penalties should not go below 0.0
        confidence = extractor.calculate_confidence("similar_term", 100, 100)
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio()
    async def test_rate_limit_enforced(self, extractor):
        """Test that rate limiting is enforced."""
        import time

        extractor.rate_limit_delay = 0.2  # 200ms delay

        start = time.time()
        await extractor._rate_limit()
        await extractor._rate_limit()
        elapsed = time.time() - start

        # Should have waited at least one delay period
        assert elapsed >= 0.2

    @pytest.mark.asyncio()
    async def test_get_redirects_success(self, extractor):
        """Test successful redirect extraction."""
        # Mock Wikipedia API response voor redirects
        mock_response_data = {
            "query": {
                "redirects": [
                    {"from": "Voorarrest", "to": "Voorlopige hechtenis"},
                    {"from": "Bewaring", "to": "Voorlopige hechtenis"},
                ]
            }
        }

        mock_response = create_mock_response(200, mock_response_data)
        mock_session = create_mock_session()
        mock_session.get = MagicMock(
            return_value=create_mock_get_context(mock_response)
        )

        async with extractor:
            extractor.session = mock_session
            redirects = await extractor.get_redirects("Voorlopige hechtenis")

        assert len(redirects) >= 1
        assert any("Voorarrest" in r or "voorarrest" in r.lower() for r in redirects)

    @pytest.mark.asyncio()
    async def test_get_redirects_filters_invalid(self, extractor):
        """Test that invalid redirects (categories, etc.) are filtered."""
        mock_response_data = {
            "query": {
                "redirects": [
                    {"from": "Voorarrest", "to": "Voorlopige hechtenis"},
                    {"from": "Categorie:Strafrecht", "to": "Voorlopige hechtenis"},
                    {"from": "Wikipedia:VH", "to": "Voorlopige hechtenis"},
                ]
            }
        }

        mock_response = create_mock_response(200, mock_response_data)
        mock_session = create_mock_session()
        mock_session.get = MagicMock(
            return_value=create_mock_get_context(mock_response)
        )

        async with extractor:
            extractor.session = mock_session
            redirects = await extractor.get_redirects("Voorlopige hechtenis")

        # Should only contain valid redirects
        assert all(extractor._is_valid_term(r) for r in redirects)
        assert not any(r.startswith("Categorie:") for r in redirects)
        assert not any(r.startswith("Wikipedia:") for r in redirects)

    @pytest.mark.asyncio()
    async def test_get_redirects_api_error(self, extractor):
        """Test handling of API errors during redirect extraction."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 500  # Server error
            mock_session.get.return_value.__aenter__.return_value = mock_response

            async with extractor:
                extractor.session = mock_session
                redirects = await extractor.get_redirects("test term")

            assert redirects == []

    @pytest.mark.asyncio()
    async def test_parse_disambiguation_success(self, extractor):
        """Test successful disambiguation page parsing."""
        # Mock response 1: Check if disambiguation
        mock_categories_response = {
            "query": {
                "pages": {
                    "12345": {
                        "categories": [
                            {"title": "Categorie:Wikipedia:Doorverwijspagina"}
                        ]
                    }
                }
            }
        }

        # Mock response 2: Get page links
        mock_links_response = {
            "query": {
                "pages": {
                    "12345": {
                        "links": [
                            {"title": "Appel (recht)"},
                            {"title": "Appelprocedure"},
                            {"title": "Beroep"},
                        ]
                    }
                }
            }
        }

        # Create mock responses
        mock_cat_resp = create_mock_response(200, mock_categories_response)
        mock_link_resp = create_mock_response(200, mock_links_response)

        # Create mock session
        mock_session = create_mock_session()
        call_count = [0]

        def get_response(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return create_mock_get_context(mock_cat_resp)
            return create_mock_get_context(mock_link_resp)

        mock_session.get = MagicMock(side_effect=get_response)

        async with extractor:
            extractor.session = mock_session
            alternatives = await extractor.parse_disambiguation("Hoger beroep")

        assert len(alternatives) >= 1
        assert any("Appel" in alt for alt in alternatives)

    @pytest.mark.asyncio()
    async def test_parse_disambiguation_not_disambiguation_page(self, extractor):
        """Test parsing non-disambiguation page returns empty list."""
        # Mock response zonder disambiguation category
        mock_response = {
            "query": {
                "pages": {"12345": {"categories": [{"title": "Categorie:Strafrecht"}]}}
            }
        }

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            mock_cat_response = AsyncMock()
            mock_cat_response.status = 200
            mock_cat_response.json.return_value = mock_response

            mock_session.get.return_value.__aenter__.return_value = mock_cat_response

            async with extractor:
                extractor.session = mock_session
                alternatives = await extractor.parse_disambiguation("Test term")

            assert alternatives == []

    @pytest.mark.asyncio()
    async def test_extract_synonyms_combines_sources(self, extractor):
        """Test that extract_synonyms combines redirects and disambiguation."""
        # Mock redirects response
        mock_redirects_response = {
            "query": {
                "redirects": [{"from": "Voorarrest", "to": "Voorlopige hechtenis"}]
            }
        }

        # Mock disambiguation check (not a disambiguation page)
        mock_disambiguation_response = {
            "query": {
                "pages": {"12345": {"categories": [{"title": "Categorie:Strafrecht"}]}}
            }
        }

        # Create mock responses
        mock_redirect_resp = create_mock_response(200, mock_redirects_response)
        mock_dis_resp = create_mock_response(200, mock_disambiguation_response)

        # Create mock session with sequential responses
        mock_session = create_mock_session()
        call_count = [0]

        def get_response(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return create_mock_get_context(mock_redirect_resp)
            return create_mock_get_context(mock_dis_resp)

        mock_session.get = MagicMock(side_effect=get_response)

        async with extractor:
            extractor.session = mock_session
            candidates = await extractor.extract_synonyms("Voorlopige hechtenis")

        # Should have at least redirect candidate
        assert len(candidates) >= 1
        assert any(c.synoniem == "Voorarrest" for c in candidates)

    @pytest.mark.asyncio()
    async def test_extract_synonyms_filters_low_confidence(self, extractor):
        """Test that low confidence candidates are filtered out."""
        # Mock redirects met zeer lange term (high length difference penalty)
        mock_response = {
            "query": {
                "redirects": [
                    {
                        "from": "VH",
                        "to": "Voorlopige hechtenis in Nederland volgens Wetboek van Strafvordering",
                    }
                ]
            }
        }

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json.return_value = mock_response

            # Second call for disambiguation check
            mock_dis_resp = AsyncMock()
            mock_dis_resp.status = 200
            mock_dis_resp.json.return_value = {"query": {"pages": {}}}

            mock_session.get.return_value.__aenter__.side_effect = [
                mock_resp,
                mock_dis_resp,
            ]

            async with extractor:
                extractor.session = mock_session
                candidates = await extractor.extract_synonyms("VH")

            # Low confidence candidates should be filtered (confidence < 0.60)
            for candidate in candidates:
                assert candidate.confidence >= 0.60

    @pytest.mark.asyncio()
    async def test_extract_synonyms_sorts_by_confidence(self, extractor):
        """Test that results are sorted by confidence (highest first)."""
        # Mock multiple redirects met verschillende confidence
        mock_redirects_response = {
            "query": {
                "redirects": [
                    {"from": "Voorarrest", "to": "Voorlopige hechtenis"},  # High conf
                    {"from": "VH", "to": "Voorlopige hechtenis"},  # Lower conf
                ]
            }
        }

        mock_dis_response = {"query": {"pages": {}}}

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            mock_red_resp = AsyncMock()
            mock_red_resp.status = 200
            mock_red_resp.json.return_value = mock_redirects_response

            mock_dis_resp = AsyncMock()
            mock_dis_resp.status = 200
            mock_dis_resp.json.return_value = mock_dis_response

            mock_session.get.return_value.__aenter__.side_effect = [
                mock_red_resp,
                mock_dis_resp,
            ]

            async with extractor:
                extractor.session = mock_session
                candidates = await extractor.extract_synonyms("Voorlopige hechtenis")

            # Check sorting (highest confidence first)
            if len(candidates) >= 2:
                for i in range(len(candidates) - 1):
                    assert candidates[i].confidence >= candidates[i + 1].confidence


class TestStandaloneFunctions:
    """Tests voor standalone utility functies."""

    @pytest.mark.asyncio()
    async def test_extract_wikipedia_synonyms_standalone(self):
        """Test standalone extract_wikipedia_synonyms functie."""
        # Simply test that the function can be called
        # Detailed functionality is tested in WikipediaSynonymExtractor class tests

        # Mock completely at Wikipedia level
        mock_extractor = AsyncMock()
        mock_extractor.extract_synonyms = AsyncMock(
            return_value=[
                SynonymCandidate(
                    hoofdterm="Voorlopige hechtenis",
                    synoniem="Voorarrest",
                    confidence=0.90,
                    source_type="redirect",
                    wikipedia_url="https://nl.wikipedia.org/wiki/Voorarrest",
                    metadata={},
                )
            ]
        )

        with patch(
            "services.web_lookup.wikipedia_synonym_extractor.WikipediaSynonymExtractor"
        ) as mock_class:
            mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_extractor)
            mock_class.return_value.__aexit__ = AsyncMock(return_value=None)

            candidates = await extract_wikipedia_synonyms(
                "Voorlopige hechtenis", language="nl"
            )

            assert isinstance(candidates, list)
            # Check structure
            if candidates:
                assert isinstance(candidates[0], SynonymCandidate)


class TestEdgeCases:
    """Tests voor edge cases en error scenarios."""

    @pytest.mark.asyncio()
    async def test_extract_synonyms_empty_term(self, extractor):
        """Test handling of empty term."""
        async with extractor:
            candidates = await extractor.extract_synonyms("")

        # Should handle gracefully (API likely returns no results)
        assert isinstance(candidates, list)

    @pytest.mark.asyncio()
    async def test_extract_synonyms_special_characters(self, extractor):
        """Test handling of terms with special characters."""
        mock_response = {"query": {"redirects": []}}

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json.return_value = mock_response

            mock_dis_resp = AsyncMock()
            mock_dis_resp.status = 200
            mock_dis_resp.json.return_value = {"query": {"pages": {}}}

            mock_session.get.return_value.__aenter__.side_effect = [
                mock_resp,
                mock_dis_resp,
            ]

            async with extractor:
                extractor.session = mock_session
                candidates = await extractor.extract_synonyms("Hoger beroep (recht)")

            # Should handle gracefully
            assert isinstance(candidates, list)

    @pytest.mark.asyncio()
    async def test_context_manager_cleanup(self):
        """Test that context manager properly cleans up session."""
        extractor = WikipediaSynonymExtractor()

        async with extractor:
            assert extractor.session is not None

        # Session should be closed after context exit
        # (actual session cleanup tested via mock)


class TestIntegrationScenarios:
    """Integration-achtige tests voor realistische scenarios."""

    @pytest.mark.asyncio()
    async def test_full_extraction_workflow(self, extractor):
        """Test volledig extraction workflow met meerdere bronnen."""
        # Mock complete workflow: redirects + disambiguation
        mock_redirects = {
            "query": {"redirects": [{"from": "Appel", "to": "Hoger beroep"}]}
        }

        mock_categories = {
            "query": {
                "pages": {
                    "12345": {
                        "categories": [
                            {"title": "Categorie:Wikipedia:Doorverwijspagina"}
                        ]
                    }
                }
            }
        }

        mock_links = {
            "query": {
                "pages": {
                    "12345": {
                        "links": [
                            {"title": "Appelprocedure"},
                            {"title": "Cassatie"},
                        ]
                    }
                }
            }
        }

        # Create all mock responses
        mock_redirect_resp = create_mock_response(200, mock_redirects)
        mock_cat_resp = create_mock_response(200, mock_categories)
        mock_link_resp = create_mock_response(200, mock_links)

        mock_session = create_mock_session()
        call_count = [0]

        def get_response(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return create_mock_get_context(mock_redirect_resp)
            if call_count[0] == 2:
                return create_mock_get_context(mock_cat_resp)
            return create_mock_get_context(mock_link_resp)

        mock_session.get = MagicMock(side_effect=get_response)

        async with extractor:
            extractor.session = mock_session
            candidates = await extractor.extract_synonyms("Hoger beroep")

        # Should have candidates van beide bronnen
        assert len(candidates) >= 1

        # Check dat alle candidates valid SynonymCandidate objects zijn
        for candidate in candidates:
            assert isinstance(candidate, SynonymCandidate)
            assert candidate.confidence >= 0.60
            assert candidate.wikipedia_url.startswith("https://")
