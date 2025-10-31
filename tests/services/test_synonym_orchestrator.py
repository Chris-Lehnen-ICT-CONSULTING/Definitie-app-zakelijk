"""
Unit tests voor SynonymOrchestrator.

Test Coverage:
- Cache behavior (8 tests)
- Version counter / race conditions (3 tests)
- Governance policy (4 tests)
- GPT-4 enrichment (7 tests)
- Error handling (2 tests)
- Thread safety (1 test)
- Health check (3 tests)
- Cache stats reset (1 test)
- Edge cases (2 tests)

Total: 31 tests with >94% coverage

Architecture Reference:
    docs/architectuur/synonym-orchestrator-architecture-v3.1.md
    Lines 326-502: SynonymOrchestrator specification
"""

import asyncio
import sys
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Voeg src toe aan path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.config.synonym_config import SynonymConfiguration, SynonymPolicy
from src.models.synonym_models import WeightedSynonym
from src.repositories.synonym_registry import SynonymRegistry
from src.services.gpt4_synonym_suggester import GPT4SynonymSuggester, SynonymSuggestion
from src.services.synonym_orchestrator import SynonymOrchestrator

# ========================================
# FIXTURES
# ========================================


@pytest.fixture
def mock_registry():
    """Mock SynonymRegistry voor testing."""
    mock = Mock(spec=SynonymRegistry)
    mock.get_statistics.return_value = {
        "total_groups": 10,
        "total_members": 50,
        "members_by_status": {"active": 40, "ai_pending": 10},
    }
    return mock


@pytest.fixture
def mock_gpt4():
    """Mock GPT4SynonymSuggester voor testing."""
    mock = Mock(spec=GPT4SynonymSuggester)
    # suggest_synonyms is async, so use AsyncMock
    mock.suggest_synonyms = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def strict_config():
    """Strict policy configuratie."""
    return SynonymConfiguration(
        policy=SynonymPolicy.STRICT,
        min_synonyms_threshold=5,
        gpt4_timeout_seconds=30,
        cache_ttl_seconds=3600,
        cache_max_size=1000,
        min_weight_for_weblookup=0.7,
    )


@pytest.fixture
def pragmatic_config():
    """Pragmatic policy configuratie."""
    return SynonymConfiguration(
        policy=SynonymPolicy.PRAGMATIC,
        min_synonyms_threshold=5,
        gpt4_timeout_seconds=30,
        cache_ttl_seconds=3600,
        cache_max_size=1000,
        min_weight_for_weblookup=0.7,
    )


@pytest.fixture
def orchestrator(mock_registry, mock_gpt4, strict_config):
    """Create orchestrator met mocked dependencies en strict config."""
    with patch(
        "src.services.synonym_orchestrator.get_synonym_config",
        return_value=strict_config,
    ):
        return SynonymOrchestrator(registry=mock_registry, gpt4_suggester=mock_gpt4)


@pytest.fixture
def sample_synonyms():
    """Sample synonym data voor tests."""
    return [
        WeightedSynonym(
            term="advocaat",
            weight=0.95,
            status="active",
            is_preferred=True,
            usage_count=100,
        ),
        WeightedSynonym(
            term="rechtsbijstandverlener",
            weight=0.85,
            status="active",
            is_preferred=False,
            usage_count=50,
        ),
        WeightedSynonym(
            term="juridisch adviseur",
            weight=0.75,
            status="active",
            is_preferred=False,
            usage_count=30,
        ),
    ]


# ========================================
# CACHE BEHAVIOR TESTS (8 tests)
# ========================================


class TestCacheBehavior:
    """Test cache functionaliteit."""

    def test_cache_hit_on_repeated_query(
        self, orchestrator, mock_registry, sample_synonyms
    ):
        """Test cache returns dezelfde data bij herhaalde query zonder registry te raken."""
        # Arrange
        mock_registry.get_synonyms.return_value = sample_synonyms
        term = "raadsman"

        # Act - eerste query (cache miss)
        result1 = orchestrator.get_synonyms_for_lookup(term)
        # Tweede query (cache hit)
        result2 = orchestrator.get_synonyms_for_lookup(term)

        # Assert
        assert result1 == result2
        assert len(result1) == 3
        # Registry moet slechts 1x aangeroepen worden (bij cache miss)
        assert mock_registry.get_synonyms.call_count == 1
        # Cache hits moet 1 zijn
        assert orchestrator._cache_hits == 1
        assert orchestrator._cache_misses == 1

    def test_cache_miss_queries_registry(
        self, orchestrator, mock_registry, sample_synonyms
    ):
        """Test cache miss queried registry en slaat resultaat op."""
        # Arrange
        mock_registry.get_synonyms.return_value = sample_synonyms
        term = "raadsman"

        # Act
        result = orchestrator.get_synonyms_for_lookup(term)

        # Assert
        assert len(result) == 3
        assert result[0].term == "advocaat"
        # Registry moet aangeroepen worden
        mock_registry.get_synonyms.assert_called_once()
        # Cache stats
        assert orchestrator._cache_hits == 0
        assert orchestrator._cache_misses == 1
        # Entry moet in cache zitten
        assert "raadsman" in orchestrator._cache

    def test_cache_ttl_expiration(self, orchestrator, mock_registry, sample_synonyms):
        """Test TTL expiration verwijdert oude entries."""
        # Arrange
        mock_registry.get_synonyms.return_value = sample_synonyms
        term = "raadsman"

        # Stel korte TTL in (1 second)
        orchestrator.config.cache_ttl_seconds = 1

        # Act - eerste query (cache miss)
        result1 = orchestrator.get_synonyms_for_lookup(term)
        assert orchestrator._cache_hits == 0
        assert orchestrator._cache_misses == 1

        # Wacht tot cache expired
        time.sleep(1.1)

        # Tweede query (cache miss door TTL expiration)
        result2 = orchestrator.get_synonyms_for_lookup(term)

        # Assert
        assert result1 == result2
        # Beide queries moeten cache miss zijn (expired)
        assert orchestrator._cache_hits == 0  # Geen hits
        assert orchestrator._cache_misses == 2  # Twee misses
        # Registry moet 2x aangeroepen worden
        assert mock_registry.get_synonyms.call_count == 2

    def test_cache_invalidation_single_term(
        self, orchestrator, mock_registry, sample_synonyms
    ):
        """Test cache invalidation voor enkele term."""
        # Arrange
        mock_registry.get_synonyms.return_value = sample_synonyms
        term = "raadsman"

        # Act - cache entry
        orchestrator.get_synonyms_for_lookup(term)
        assert "raadsman" in orchestrator._cache

        # Invalidate
        orchestrator.invalidate_cache(term)

        # Assert
        # Entry moet verwijderd zijn
        assert "raadsman" not in orchestrator._cache
        # Version moet verhoogd zijn
        assert orchestrator._cache_version == 1

        # Nieuwe query moet registry opnieuw raken
        orchestrator.get_synonyms_for_lookup(term)
        assert mock_registry.get_synonyms.call_count == 2

    def test_cache_flush_all_terms(self, orchestrator, mock_registry, sample_synonyms):
        """Test cache flush verwijdert alle entries."""
        # Arrange
        mock_registry.get_synonyms.return_value = sample_synonyms

        # Cache multiple terms
        orchestrator.get_synonyms_for_lookup("raadsman")
        orchestrator.get_synonyms_for_lookup("advocaat")
        orchestrator.get_synonyms_for_lookup("jurist")

        assert len(orchestrator._cache) == 3

        # Act - flush all
        orchestrator.invalidate_cache(None)  # None = flush all

        # Assert
        assert len(orchestrator._cache) == 0
        # Version moet verhoogd zijn
        assert orchestrator._cache_version == 1

    def test_cache_lru_eviction_at_max_size(self, orchestrator, mock_registry):
        """Test LRU eviction bij max_size."""
        # Arrange
        orchestrator.config.cache_max_size = 3
        mock_registry.get_synonyms.return_value = [
            WeightedSynonym(
                term="syn1",
                weight=0.9,
                status="active",
                is_preferred=False,
                usage_count=10,
            )
        ]

        # Act - cache 4 entries (max_size = 3)
        orchestrator.get_synonyms_for_lookup("term1")
        orchestrator.get_synonyms_for_lookup("term2")
        orchestrator.get_synonyms_for_lookup("term3")
        orchestrator.get_synonyms_for_lookup("term4")  # Should evict term1

        # Assert
        assert len(orchestrator._cache) == 3
        # Oldest entry (term1) moet verwijderd zijn
        assert "term1" not in orchestrator._cache
        # Nieuwste entries moeten er nog zijn
        assert "term2" in orchestrator._cache
        assert "term3" in orchestrator._cache
        assert "term4" in orchestrator._cache

    def test_cache_hit_rate_calculation(
        self, orchestrator, mock_registry, sample_synonyms
    ):
        """Test cache hit rate berekening."""
        # Arrange
        mock_registry.get_synonyms.return_value = sample_synonyms

        # Act - mix van hits en misses
        orchestrator.get_synonyms_for_lookup("term1")  # Miss
        orchestrator.get_synonyms_for_lookup("term1")  # Hit
        orchestrator.get_synonyms_for_lookup("term1")  # Hit
        orchestrator.get_synonyms_for_lookup("term2")  # Miss

        # Assert
        hit_rate = orchestrator.cache_hit_rate
        assert hit_rate == 0.5  # 2 hits / 4 total queries
        assert orchestrator._cache_hits == 2
        assert orchestrator._cache_misses == 2

    def test_cache_stats_reporting(self, orchestrator, mock_registry, sample_synonyms):
        """Test cache stats reporting."""
        # Arrange
        mock_registry.get_synonyms.return_value = sample_synonyms

        # Act - enkele queries
        orchestrator.get_synonyms_for_lookup("term1")
        orchestrator.get_synonyms_for_lookup("term1")

        stats = orchestrator.get_cache_stats()

        # Assert
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["max_size"] == 1000
        assert stats["ttl_seconds"] == 3600


# ========================================
# VERSION COUNTER / RACE CONDITION TESTS (3 tests)
# ========================================


class TestVersionCounter:
    """Test version counter voor race condition prevention."""

    def test_version_mismatch_detection(
        self, orchestrator, mock_registry, sample_synonyms
    ):
        """Test version mismatch detectie bij stale cache entries."""
        # Arrange
        mock_registry.get_synonyms.return_value = sample_synonyms
        term = "raadsman"

        # Cache entry met version 0
        orchestrator.get_synonyms_for_lookup(term)
        assert orchestrator._cache_version == 0

        # Simuleer invalidation (increment version)
        orchestrator.invalidate_cache(term)
        assert orchestrator._cache_version == 1

        # Nieuwe entry cachen (met version 1)
        mock_registry.get_synonyms.return_value = [
            WeightedSynonym(
                term="new",
                weight=0.9,
                status="active",
                is_preferred=False,
                usage_count=5,
            )
        ]
        result = orchestrator.get_synonyms_for_lookup(term)

        # Assert - nieuwe data moet gereturned worden
        assert len(result) == 1
        assert result[0].term == "new"

    def test_version_increment_on_invalidation(self, orchestrator):
        """Test version increment bij invalidation."""
        # Arrange
        initial_version = orchestrator._cache_version

        # Act - invalidate (single term)
        orchestrator.invalidate_cache("term1")

        # Assert
        assert orchestrator._cache_version == initial_version + 1

        # Act - invalidate (flush all)
        orchestrator.invalidate_cache(None)

        # Assert
        assert orchestrator._cache_version == initial_version + 2

    def test_stale_cache_entry_rejected_after_version_change(
        self, orchestrator, mock_registry, sample_synonyms
    ):
        """Test stale cache entry wordt rejected na version change."""
        # Arrange
        mock_registry.get_synonyms.return_value = sample_synonyms
        term = "raadsman"

        # Cache entry
        orchestrator.get_synonyms_for_lookup(term)

        # Manually increment version (simuleert invalidation door andere thread)
        orchestrator._cache_version += 1

        # Act - query moet cache miss zijn (version mismatch)
        orchestrator.get_synonyms_for_lookup(term)

        # Assert
        # Moet registry opnieuw raken (cache miss)
        assert mock_registry.get_synonyms.call_count == 2
        # Entry moet verwijderd zijn uit cache
        # (nieuwe entry met nieuwe version wordt toegevoegd)
        stored_version = orchestrator._cache[term][2]
        assert stored_version == orchestrator._cache_version


# ========================================
# GOVERNANCE POLICY TESTS (4 tests)
# ========================================


class TestGovernancePolicy:
    """Test governance policy enforcement."""

    def test_strict_policy_only_active_status(self, mock_registry, mock_gpt4):
        """Test STRICT policy returnt alleen 'active' status."""
        # Arrange
        strict_cfg = SynonymConfiguration(policy=SynonymPolicy.STRICT)
        with patch(
            "src.services.synonym_orchestrator.get_synonym_config",
            return_value=strict_cfg,
        ):
            orch = SynonymOrchestrator(mock_registry, mock_gpt4)
            mock_registry.get_synonyms.return_value = []

            # Act
            orch.get_synonyms_for_lookup("term")

            # Assert - moet queried hebben met alleen 'active'
            call_args = mock_registry.get_synonyms.call_args
            assert call_args[1]["statuses"] == ["active"]

    def test_pragmatic_policy_includes_ai_pending(self, mock_registry, mock_gpt4):
        """Test PRAGMATIC policy includeert 'active' + 'ai_pending'."""
        # Arrange
        pragmatic_cfg = SynonymConfiguration(policy=SynonymPolicy.PRAGMATIC)
        with patch(
            "src.services.synonym_orchestrator.get_synonym_config",
            return_value=pragmatic_cfg,
        ):
            orch = SynonymOrchestrator(mock_registry, mock_gpt4)
            mock_registry.get_synonyms.return_value = []

            # Act
            orch.get_synonyms_for_lookup("term")

            # Assert - moet queried hebben met active + ai_pending
            call_args = mock_registry.get_synonyms.call_args
            assert call_args[1]["statuses"] == ["active", "ai_pending"]

    def test_policy_switching_behavior(self, orchestrator, mock_registry):
        """Test policy switching gedrag."""
        # Arrange - start met STRICT
        assert orchestrator.config.policy == SynonymPolicy.STRICT
        mock_registry.get_synonyms.return_value = []

        # Act - query met STRICT
        orchestrator.get_synonyms_for_lookup("term1")
        call1 = mock_registry.get_synonyms.call_args[1]["statuses"]

        # Switch naar PRAGMATIC
        orchestrator.config.policy = SynonymPolicy.PRAGMATIC
        orchestrator.get_synonyms_for_lookup("term2")
        call2 = mock_registry.get_synonyms.call_args[1]["statuses"]

        # Assert
        assert call1 == ["active"]
        assert call2 == ["active", "ai_pending"]

    def test_min_weight_threshold_enforcement(self, orchestrator, mock_registry):
        """Test min_weight threshold wordt doorgegeven aan registry."""
        # Arrange
        orchestrator.config.min_weight_for_weblookup = 0.7
        mock_registry.get_synonyms.return_value = []

        # Act
        orchestrator.get_synonyms_for_lookup("term", min_weight=0.8)

        # Assert - custom min_weight moet gebruikt worden
        call_args = mock_registry.get_synonyms.call_args
        assert call_args[1]["min_weight"] == 0.8

        # Act - zonder custom min_weight
        orchestrator.get_synonyms_for_lookup("term2")

        # Assert - default uit config moet gebruikt worden
        call_args = mock_registry.get_synonyms.call_args
        assert call_args[1]["min_weight"] == 0.7


# ========================================
# GPT-4 ENRICHMENT TESTS (3 tests)
# ========================================


class TestGPT4Enrichment:
    """Test GPT-4 enrichment flow."""

    @pytest.mark.asyncio
    async def test_fast_path_sufficient_synonyms_no_gpt4(
        self, orchestrator, mock_registry, mock_gpt4, sample_synonyms
    ):
        """Test fast path: voldoende synoniemen aanwezig, geen GPT-4 call."""
        # Arrange
        mock_registry.get_synonyms.return_value = sample_synonyms  # 3 synonyms
        term = "raadsman"

        # Act
        result, ai_count = await orchestrator.ensure_synonyms(term, min_count=3)

        # Assert
        assert len(result) == 3
        assert ai_count == 0
        # GPT-4 moet NIET aangeroepen worden
        mock_gpt4.suggest_synonyms.assert_not_called()

    @pytest.mark.asyncio
    async def test_slow_path_gpt4_called_when_insufficient(
        self, orchestrator, mock_registry, mock_gpt4
    ):
        """Test slow path: GPT-4 wordt aangeroepen bij onvoldoende synoniemen."""
        # Arrange
        # Eerste query: slechts 2 synonyms
        initial_synonyms = [
            WeightedSynonym(
                term="advocaat",
                weight=0.9,
                status="active",
                is_preferred=True,
                usage_count=10,
            ),
            WeightedSynonym(
                term="jurist",
                weight=0.8,
                status="active",
                is_preferred=False,
                usage_count=5,
            ),
        ]
        mock_registry.get_synonyms.return_value = initial_synonyms

        # GPT-4 suggesties
        gpt4_suggestions = [
            SynonymSuggestion(
                synoniem="rechtsbijstandverlener", confidence=0.85, rationale="Test"
            ),
            SynonymSuggestion(
                synoniem="juridisch adviseur", confidence=0.75, rationale="Test"
            ),
        ]
        mock_gpt4.suggest_synonyms.return_value = gpt4_suggestions

        # Mock group creation
        mock_group = Mock()
        mock_group.id = 123
        mock_registry.get_or_create_group.return_value = mock_group
        mock_registry.add_group_member.return_value = 1

        # Na enrichment: 4 synonyms (2 original + 2 AI)
        enriched_synonyms = [
            *initial_synonyms,
            WeightedSynonym(
                term="rechtsbijstandverlener",
                weight=0.85,
                status="ai_pending",
                is_preferred=False,
                usage_count=0,
            ),
            WeightedSynonym(
                term="juridisch adviseur",
                weight=0.75,
                status="ai_pending",
                is_preferred=False,
                usage_count=0,
            ),
        ]

        # Setup registry mock voor verschillende calls
        call_count = 0

        def get_synonyms_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return initial_synonyms
            return enriched_synonyms

        mock_registry.get_synonyms.side_effect = get_synonyms_side_effect

        term = "raadsman"

        # Act
        result, ai_count = await orchestrator.ensure_synonyms(term, min_count=5)

        # Assert
        assert ai_count == 2  # 2 AI suggestions toegevoegd
        # GPT-4 moet aangeroepen zijn
        mock_gpt4.suggest_synonyms.assert_called_once()
        # Group moet aangemaakt zijn
        mock_registry.get_or_create_group.assert_called_once_with(
            canonical_term=term, created_by="gpt4_enrichment"
        )
        # Members moeten toegevoegd zijn
        assert mock_registry.add_group_member.call_count == 2

    @pytest.mark.asyncio
    async def test_gpt4_timeout_handling(self, orchestrator, mock_registry, mock_gpt4):
        """Test GPT-4 timeout handling."""
        # Arrange
        mock_registry.get_synonyms.return_value = []  # Geen synonyms

        # GPT-4 timeout simuleren
        async def timeout_side_effect(*args, **kwargs):
            await asyncio.sleep(10)  # Langer dan timeout
            return []

        mock_gpt4.suggest_synonyms.side_effect = timeout_side_effect
        orchestrator.config.gpt4_timeout_seconds = 0.1  # Korte timeout

        term = "raadsman"

        # Act
        result, ai_count = await orchestrator.ensure_synonyms(term, min_count=5)

        # Assert - moet gracefully falen
        assert ai_count == 0
        assert len(result) == 0  # Existing (leeg) wordt gereturned

    @pytest.mark.asyncio
    async def test_gpt4_empty_suggestions_handling(
        self, orchestrator, mock_registry, mock_gpt4
    ):
        """Test handling van lege GPT-4 suggesties."""
        # Arrange
        initial_synonyms = [
            WeightedSynonym(
                term="advocaat",
                weight=0.9,
                status="active",
                is_preferred=True,
                usage_count=10,
            ),
        ]
        mock_registry.get_synonyms.return_value = initial_synonyms
        # GPT-4 returnt geen suggesties
        mock_gpt4.suggest_synonyms.return_value = []

        term = "raadsman"

        # Act
        result, ai_count = await orchestrator.ensure_synonyms(term, min_count=5)

        # Assert - moet bestaande synonyms returnen
        assert ai_count == 0
        assert len(result) == 1
        # Group creation moet NIET aangeroepen worden
        mock_registry.get_or_create_group.assert_not_called()

    @pytest.mark.asyncio
    async def test_gpt4_generic_exception_handling(
        self, orchestrator, mock_registry, mock_gpt4
    ):
        """Test generic exception handling in enrichment flow."""
        # Arrange
        mock_registry.get_synonyms.return_value = []  # Geen synonyms

        # GPT-4 gooit exception
        mock_gpt4.suggest_synonyms.side_effect = RuntimeError("API error")

        term = "raadsman"

        # Act
        result, ai_count = await orchestrator.ensure_synonyms(term, min_count=5)

        # Assert - moet gracefully falen
        assert ai_count == 0
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_empty_term_in_ensure_synonyms(self, orchestrator, mock_registry):
        """Test empty term handling in ensure_synonyms."""
        # Act & Assert
        result1, count1 = await orchestrator.ensure_synonyms("")
        assert result1 == []
        assert count1 == 0

        result2, count2 = await orchestrator.ensure_synonyms("   ")
        assert result2 == []
        assert count2 == 0

        # Registry moet NIET aangeroepen worden
        mock_registry.get_synonyms.assert_not_called()


# ========================================
# ERROR HANDLING TESTS (2 tests)
# ========================================


class TestErrorHandling:
    """Test error handling."""

    def test_registry_query_failure_graceful_degradation(
        self, orchestrator, mock_registry
    ):
        """Test graceful degradation bij registry failure."""
        # Arrange
        mock_registry.get_synonyms.side_effect = Exception("Database error")

        # Act
        result = orchestrator.get_synonyms_for_lookup("term")

        # Assert - moet empty list returnen (geen exception)
        assert result == []

    def test_empty_term_handling(self, orchestrator, mock_registry):
        """Test empty term handling."""
        # Act & Assert
        assert orchestrator.get_synonyms_for_lookup("") == []
        assert orchestrator.get_synonyms_for_lookup("   ") == []
        assert orchestrator.get_synonyms_for_lookup(None) == []

        # Registry moet NIET aangeroepen worden
        mock_registry.get_synonyms.assert_not_called()


# ========================================
# THREAD SAFETY TEST (1 test)
# ========================================


class TestThreadSafety:
    """Test thread safety."""

    def test_concurrent_access_to_cache(
        self, orchestrator, mock_registry, sample_synonyms
    ):
        """Test concurrent cache toegang is thread-safe."""
        # Arrange
        mock_registry.get_synonyms.return_value = sample_synonyms
        errors = []
        results = []

        def query_cache(term_index):
            """Worker thread functie."""
            try:
                term = f"term{term_index}"
                # Multiple queries per thread
                for _ in range(10):
                    result = orchestrator.get_synonyms_for_lookup(term)
                    results.append((term, len(result)))
                    # Kleine delay om race conditions te provoceren
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        # Act - 10 threads die concurrent cache toegang doen
        threads = []
        for i in range(10):
            thread = threading.Thread(target=query_cache, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait voor alle threads
        for thread in threads:
            thread.join()

        # Assert
        assert len(errors) == 0, f"Thread errors: {errors}"
        # Alle queries moeten succesvol zijn
        assert len(results) == 100  # 10 threads * 10 queries
        # Cache moet consistent blijven
        assert len(orchestrator._cache) == 10  # 10 unieke termen


# ========================================
# ADDITIONAL TESTS
# ========================================


class TestHealthCheck:
    """Test health check functionaliteit."""

    def test_health_check_healthy_status(self, orchestrator, mock_registry):
        """Test health check met healthy status."""
        # Arrange
        mock_registry.get_statistics.return_value = {
            "total_groups": 100,
            "total_members": 500,
        }

        # Cache enkele queries voor goede hit rate
        mock_registry.get_synonyms.return_value = [
            WeightedSynonym(
                term="syn",
                weight=0.9,
                status="active",
                is_preferred=False,
                usage_count=1,
            )
        ]
        orchestrator.get_synonyms_for_lookup("term1")
        orchestrator.get_synonyms_for_lookup("term1")

        # Act
        health = orchestrator.get_health_check()

        # Assert
        assert health["status"] in ["healthy", "warning"]
        assert "cache_stats" in health
        assert "registry_stats" in health
        assert "config" in health

    def test_health_check_empty_registry_warning(self, orchestrator, mock_registry):
        """Test health check met lege registry geeft warning."""
        # Arrange
        mock_registry.get_statistics.return_value = {
            "total_groups": 0,
            "total_members": 0,
        }

        # Act
        health = orchestrator.get_health_check()

        # Assert
        assert health["status"] == "warning"
        assert any("empty" in w.lower() for w in health["warnings"])

    def test_health_check_unhealthy_on_exception(self, orchestrator, mock_registry):
        """Test health check unhealthy bij exception."""
        # Arrange
        mock_registry.get_statistics.side_effect = Exception("DB error")

        # Act
        health = orchestrator.get_health_check()

        # Assert
        assert health["status"] == "unhealthy"
        assert "error" in health


class TestCacheStatsReset:
    """Test cache statistics reset."""

    def test_reset_cache_stats(self, orchestrator, mock_registry, sample_synonyms):
        """Test reset cache statistics."""
        # Arrange
        mock_registry.get_synonyms.return_value = sample_synonyms
        orchestrator.get_synonyms_for_lookup("term1")
        orchestrator.get_synonyms_for_lookup("term1")

        assert orchestrator._cache_hits > 0
        assert orchestrator._cache_misses > 0

        # Act
        orchestrator.reset_cache_stats()

        # Assert
        assert orchestrator._cache_hits == 0
        assert orchestrator._cache_misses == 0
        # Cache entries moeten blijven
        assert len(orchestrator._cache) > 0


class TestEdgeCases:
    """Test edge cases."""

    def test_max_results_limiting(self, orchestrator, mock_registry):
        """Test max_results parameter limiteert output."""
        # Arrange
        many_synonyms = [
            WeightedSynonym(
                term=f"syn{i}",
                weight=0.9,
                status="active",
                is_preferred=False,
                usage_count=i,
            )
            for i in range(20)
        ]
        mock_registry.get_synonyms.return_value = many_synonyms

        # Act
        result = orchestrator.get_synonyms_for_lookup("term", max_results=3)

        # Assert
        assert len(result) == 3

    def test_normalized_term_handling(
        self, orchestrator, mock_registry, sample_synonyms
    ):
        """Test term normalization (lowercase, strip)."""
        # Arrange
        mock_registry.get_synonyms.return_value = sample_synonyms

        # Act - verschillende capitalisatie en whitespace
        orchestrator.get_synonyms_for_lookup("  RAADSMAN  ")
        orchestrator.get_synonyms_for_lookup("raadsman")
        orchestrator.get_synonyms_for_lookup("Raadsman")

        # Assert - allemaal zelfde normalized term, dus 1 cache entry + 2 hits
        assert len(orchestrator._cache) == 1
        assert "raadsman" in orchestrator._cache
        assert orchestrator._cache_hits == 2
        assert orchestrator._cache_misses == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
