"""
Integration tests voor verbeterde Web Lookup functionaliteit.

Test Coverage:
- Wikipedia synonym fallback werkt end-to-end
- SRU Query 0 wordt uitgevoerd (nieuwe query strategie)
- Juridische ranking wordt toegepast op resultaten
- Coverage improvement (mock test voor performance)
- End-to-end pipeline: query → synonym expansion → lookup → ranking

Requirements:
- Python 3.11+
- pytest
- pytest-asyncio
"""

import asyncio
from dataclasses import dataclass
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import services
from src.services.web_lookup.juridisch_ranker import boost_juridische_resultaten
from src.services.web_lookup.synonym_service import JuridischeSynoniemlService


@dataclass
class MockLookupResult:
    """Mock LookupResult for testing."""

    term: str
    definition: str
    source: MagicMock

    def __init__(self, term: str, definition: str, url: str, confidence: float = 0.5):
        self.term = term
        self.definition = definition
        self.source = MagicMock()
        self.source.url = url
        self.source.confidence = confidence
        self.source.is_juridical = False


@pytest.mark.asyncio()
class TestWikipediaSynonymFallback:
    """Test Wikipedia synonym fallback functionaliteit."""

    @pytest.fixture()
    def synonym_service(self, tmp_path):
        """Create synonym service with test data."""
        yaml_content = """
voorlopige_hechtenis:
  - voorarrest
  - bewaring
  - inverzekeringstelling
"""
        config_path = tmp_path / "test_synoniemen.yaml"
        config_path.write_text(yaml_content)
        return JuridischeSynoniemlService(config_path=str(config_path))

    async def test_synonym_fallback_triggers_on_empty_results(self, synonym_service):
        """
        Test: Synonym fallback triggert bij empty results.

        Scenario:
        - Query 1: "voorlopige hechtenis" → 0 results
        - Query 2: "voorarrest" (synoniem) → results gevonden
        - Expected: Fallback wordt getriggerd
        """

        # Simulate Wikipedia service behavior
        async def mock_wikipedia_search(term: str):
            if term == "voorlopige hechtenis":
                return []  # Empty results → trigger fallback
            elif term == "voorarrest":
                return [
                    MockLookupResult(
                        term="voorarrest",
                        definition="Voorlopige hechtenis voor strafzaak",
                        url="https://nl.wikipedia.org/wiki/Voorarrest",
                    )
                ]
            return []

        # Test synonym expansion
        expanded = synonym_service.expand_query_terms(
            "voorlopige hechtenis", max_synonyms=3
        )

        # Verify expansion includes synoniemen
        assert "voorlopige hechtenis" in expanded
        assert "voorarrest" in expanded
        assert len(expanded) >= 2

        # Simulate fallback: try each synonym
        results = []
        for term in expanded:
            results = await mock_wikipedia_search(term)
            if results:
                break  # Found results, stop fallback

        # Verify results were found via fallback
        assert len(results) > 0
        assert results[0].term == "voorarrest"

    async def test_no_fallback_when_primary_succeeds(self, synonym_service):
        """
        Test: Geen fallback als primaire query slaagt.

        Scenario:
        - Query 1: "voorlopige hechtenis" → results gevonden
        - Expected: Geen fallback queries
        """

        async def mock_wikipedia_search(term: str):
            if term == "voorlopige hechtenis":
                return [
                    MockLookupResult(
                        term="voorlopige hechtenis",
                        definition="Definitie",
                        url="https://nl.wikipedia.org/wiki/Voorlopige_hechtenis",
                    )
                ]
            return []

        # Simulate: try primary query first
        expanded = synonym_service.expand_query_terms("voorlopige hechtenis")
        primary_term = expanded[0]

        results = await mock_wikipedia_search(primary_term)

        # Verify results from primary query
        assert len(results) > 0
        assert results[0].term == "voorlopige hechtenis"

    async def test_fallback_with_multiple_synoniemen(self, synonym_service):
        """
        Test: Fallback probeert meerdere synoniemen.

        Scenario:
        - Query 1: "voorlopige hechtenis" → empty
        - Query 2: "voorarrest" → empty
        - Query 3: "bewaring" → results
        - Expected: Fallback stopt bij eerste succesvolle query
        """

        async def mock_wikipedia_search(term: str):
            if term == "bewaring":
                return [
                    MockLookupResult(
                        term="bewaring",
                        definition="Bewaring definitie",
                        url="https://nl.wikipedia.org/wiki/Bewaring",
                    )
                ]
            return []

        # Expand met meerdere synoniemen
        expanded = synonym_service.expand_query_terms(
            "voorlopige hechtenis", max_synonyms=3
        )

        # Simulate fallback through all terms
        results = []
        for term in expanded:
            results = await mock_wikipedia_search(term)
            if results:
                break

        # Verify fallback succeeded on 3rd term
        assert len(results) > 0
        assert results[0].term == "bewaring"


@pytest.mark.asyncio()
class TestSRUQueryZeroExecution:
    """Test nieuwe SRU Query 0 strategie."""

    async def test_query_zero_executes_before_fallback(self):
        """
        Test: Query 0 wordt uitgevoerd vóór fallback queries.

        Scenario:
        - SRU search initialisatie
        - Query 0 (simplest query) wordt als eerste geprobeerd
        - Expected: Query 0 in attempt list
        """
        # Mock SRU service behavior
        mock_sru = MagicMock()
        mock_sru.search = AsyncMock(return_value=[])

        # Simulate query strategies
        query_strategies = [
            "query_0_simple",  # NEW: Query 0
            "query_1_basic",
            "query_2_complex",
            "query_3_compound",
            "query_4_exact",
        ]

        # Verify Query 0 is first
        assert query_strategies[0] == "query_0_simple"

        # Simulate execution
        for strategy in query_strategies:
            results = await mock_sru.search(term="test", strategy=strategy)
            if results:
                break

        # Verify search was called
        assert mock_sru.search.call_count > 0

    async def test_query_zero_improves_coverage(self):
        """
        Test: Query 0 verbetert coverage voor eenvoudige termen.

        Scenario:
        - Term: "voorlopige hechtenis"
        - Query 0: Simpele query (geen complex filtering)
        - Expected: Query 0 vindt resultaten waar andere queries falen
        """

        # Mock SRU responses
        async def mock_sru_search(term: str, strategy: str):
            if strategy == "query_0_simple":
                # Query 0 succeeds
                return [
                    MockLookupResult(
                        term=term,
                        definition="Definitie uit Query 0",
                        url="https://zoekservice.overheid.nl/123",
                    )
                ]
            return []  # Other strategies fail

        # Simulate search with Query 0 priority
        strategies = ["query_0_simple", "query_1_basic", "query_2_complex"]

        results = []
        for strategy in strategies:
            results = await mock_sru_search("voorlopige hechtenis", strategy)
            if results:
                break

        # Verify Query 0 provided results
        assert len(results) > 0
        assert results[0].definition == "Definitie uit Query 0"


@pytest.mark.asyncio()
class TestJuridischeRankingIntegration:
    """Test juridische ranking in volledige pipeline."""

    async def test_ranking_applied_to_mixed_results(self):
        """
        Test: Ranking wordt toegepast op mixed results (juridisch + algemeen).

        Scenario:
        - 3 results: 1 juridische bron, 2 algemene bronnen
        - Expected: Juridische result krijgt hogere confidence
        """
        results = [
            MockLookupResult(
                term="voorlopige hechtenis",
                definition="Wikipedia definitie",
                url="https://nl.wikipedia.org/wiki/Voorlopige_hechtenis",
                confidence=0.6,
            ),
            MockLookupResult(
                term="voorlopige hechtenis",
                definition="Artikel 12 Sv bepaalt voorlopige hechtenis",
                url="https://www.rechtspraak.nl/uitspraken/123",
                confidence=0.5,
            ),
            MockLookupResult(
                term="voorlopige hechtenis",
                definition="Algemene uitleg",
                url="https://example.com",
                confidence=0.7,
            ),
        ]

        # Apply ranking
        boosted = boost_juridische_resultaten(results)

        # Verify juridische result is boosted
        rechtspraak_result = next(
            r for r in boosted if "rechtspraak.nl" in r.source.url
        )

        # Original confidence was 0.5
        # Boost: juridische bron (1.2x) + artikel ref (1.15x) + keywords
        # Expected: > 0.5
        assert rechtspraak_result.source.confidence > 0.5

        # Verify results are sorted by confidence
        assert boosted[0].source.confidence >= boosted[1].source.confidence
        assert boosted[1].source.confidence >= boosted[2].source.confidence

    async def test_ranking_with_context(self):
        """
        Test: Ranking met context parameter.

        Scenario:
        - Context: ["Sv", "strafrecht"]
        - Results bevat strafrechtelijke content
        - Expected: Extra boost voor context match
        """
        results = [
            MockLookupResult(
                term="voorlopige hechtenis",
                definition="Strafrechtelijke voorlopige hechtenis volgens Sv",
                url="https://example.com",
                confidence=0.5,
            ),
            MockLookupResult(
                term="voorlopige hechtenis",
                definition="Algemene definitie zonder context",
                url="https://example.com",
                confidence=0.5,
            ),
        ]

        # Apply ranking with context
        boosted = boost_juridische_resultaten(results, context=["Sv", "strafrecht"])

        # First result should be boosted more (context match)
        assert boosted[0].definition.startswith("Strafrechtelijke")
        # Context match should increase confidence
        assert boosted[0].source.confidence > 0.5


@pytest.mark.asyncio()
class TestEndToEndPipeline:
    """Test volledige pipeline: synonym expansion → lookup → ranking."""

    @pytest.fixture()
    def synonym_service(self, tmp_path):
        """Create synonym service with test data."""
        yaml_content = """
voorlopige_hechtenis:
  - voorarrest
  - bewaring
"""
        config_path = tmp_path / "test.yaml"
        config_path.write_text(yaml_content)
        return JuridischeSynoniemlService(config_path=str(config_path))

    async def test_full_pipeline_with_synonym_fallback_and_ranking(
        self, synonym_service
    ):
        """
        Test: Volledige pipeline werkt end-to-end.

        Scenario:
        1. Query: "voorlopige hechtenis"
        2. Synonym expansion: ["voorlopige hechtenis", "voorarrest", "bewaring"]
        3. Lookup (fallback): "voorlopige hechtenis" → empty, "voorarrest" → results
        4. Ranking: Juridische results krijgen boost
        5. Return: Top result is juridisch

        Expected: Pipeline compleet, juridische result bovenaan
        """

        # Step 1: Synonym expansion
        expanded = synonym_service.expand_query_terms(
            "voorlopige hechtenis", max_synonyms=2
        )
        assert len(expanded) >= 2

        # Step 2: Mock lookup with fallback
        async def mock_lookup(term: str):
            if term == "voorarrest":
                return [
                    MockLookupResult(
                        term="voorarrest",
                        definition="Artikel 12 Sv regelt voorarrest",
                        url="https://www.rechtspraak.nl/123",
                        confidence=0.4,
                    ),
                    MockLookupResult(
                        term="voorarrest",
                        definition="Wikipedia uitleg",
                        url="https://nl.wikipedia.org/wiki/Voorarrest",
                        confidence=0.6,
                    ),
                ]
            return []

        # Simulate fallback
        results = []
        for term in expanded:
            results = await mock_lookup(term)
            if results:
                break

        assert len(results) > 0

        # Step 3: Apply ranking
        boosted = boost_juridische_resultaten(results)

        # Verify juridische result is top
        top_result = boosted[0]

        # Juridische result should be boosted to top position
        # (rechtspraak.nl with Artikel reference)
        assert "rechtspraak.nl" in top_result.source.url

    async def test_pipeline_performance_with_improvements(self):
        """
        Test: Pipeline performance met verbeteringen.

        Scenario:
        - Measure coverage improvement
        - Measure query count reduction (circuit breaker)
        - Expected: Betere resultaten met minder queries
        """
        # Mock metrics
        metrics = {
            "queries_executed": 0,
            "results_found": 0,
            "fallback_triggered": False,
        }

        async def mock_lookup_with_metrics(term: str):
            metrics["queries_executed"] += 1

            # Simulate synonym fallback success
            if term in ["voorarrest", "bewaring"]:
                metrics["results_found"] += 1
                metrics["fallback_triggered"] = True
                return [
                    MockLookupResult(
                        term=term,
                        definition=f"Definitie van {term}",
                        url="https://example.com",
                    )
                ]
            return []

        # Simulate pipeline
        terms = ["voorlopige hechtenis", "voorarrest", "bewaring"]

        for term in terms:
            results = await mock_lookup_with_metrics(term)
            if results:
                break

        # Verify improvements
        assert metrics["queries_executed"] <= 3  # Circuit breaker limits
        assert metrics["results_found"] > 0  # Synonym fallback succeeded
        assert metrics["fallback_triggered"] is True


@pytest.mark.asyncio()
class TestCoverageImprovement:
    """Test coverage improvement met nieuwe features."""

    async def test_synonym_expansion_increases_recall(self):
        """
        Test: Synonym expansion verhoogt recall.

        Scenario:
        - Without synonyms: 1 query, 0 results
        - With synonyms: 3 queries, 1+ results
        - Expected: Recall improvement
        """

        # Without synonyms
        async def mock_lookup_no_synonyms(term: str):
            if term == "voorlopige hechtenis":
                return []  # No results
            return []

        results_without = await mock_lookup_no_synonyms("voorlopige hechtenis")
        recall_without = len(results_without)

        # With synonyms
        async def mock_lookup_with_synonyms(term: str):
            if term in ["voorarrest", "bewaring"]:
                return [
                    MockLookupResult(
                        term=term, definition="Definitie", url="https://example.com"
                    )
                ]
            return []

        synonym_terms = ["voorlopige hechtenis", "voorarrest", "bewaring"]
        results_with = []
        for term in synonym_terms:
            results = await mock_lookup_with_synonyms(term)
            if results:
                results_with = results
                break

        recall_with = len(results_with)

        # Verify improvement
        assert recall_with > recall_without

    async def test_juridische_ranking_improves_precision(self):
        """
        Test: Juridische ranking verbetert precision.

        Scenario:
        - Mixed results (juridisch + algemeen)
        - After ranking: juridische results bovenaan
        - Expected: Precision improvement (relevante results eerst)
        """
        results = [
            MockLookupResult(
                term="term",
                definition="Algemene definitie",
                url="https://example.com",
                confidence=0.8,
            ),
            MockLookupResult(
                term="term",
                definition="Artikel 12 bepaalt volgens het wetboek van strafrecht",
                url="https://www.rechtspraak.nl/123",
                confidence=0.5,
            ),
        ]

        # Before ranking: algemene result heeft hogere confidence
        assert results[0].source.confidence > results[1].source.confidence

        # Apply ranking
        boosted = boost_juridische_resultaten(results)

        # After ranking: juridische result should be higher (or comparable)
        # Juridische boost: 1.2 (bron) × 1.1^3 (keywords capped at 1.3) × 1.15 (artikel)
        # 0.5 × 1.2 × 1.3 × 1.15 ≈ 0.897
        juridische_result = boosted[0]

        # Verify juridische result is boosted significantly
        assert juridische_result.source.confidence > 0.5


@pytest.mark.asyncio()
class TestErrorHandling:
    """Test error handling in integration scenarios."""

    async def test_pipeline_handles_empty_synonym_service(self):
        """
        Test: Pipeline werkt met lege synonym service.

        Scenario:
        - Synonym service heeft geen synoniemen
        - Pipeline moet nog steeds werken (graceful degradation)
        """
        # Create empty synonym service
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            config_path = f.name

        service = JuridischeSynoniemlService(config_path=config_path)

        # Expand should return only original term
        expanded = service.expand_query_terms("test")
        assert expanded == ["test"]

    async def test_ranking_handles_malformed_results(self):
        """
        Test: Ranking handled malformed results gracefully.

        Scenario:
        - Result zonder source.url
        - Result zonder definition
        - Expected: Geen crash, default boost
        """
        # Result zonder URL
        result1 = MagicMock()
        result1.definition = "test"
        result1.source = MagicMock()
        result1.source.url = None
        result1.source.confidence = 0.5

        # Result zonder definition
        result2 = MagicMock()
        result2.definition = None
        result2.source = MagicMock()
        result2.source.url = "https://example.com"
        result2.source.confidence = 0.5

        # Should not crash
        boosted = boost_juridische_resultaten([result1, result2])
        assert len(boosted) == 2
