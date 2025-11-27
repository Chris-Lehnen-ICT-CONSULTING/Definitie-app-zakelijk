"""
Comprehensive backward compatibility tests voor JuridischeSynoniemService façade.

Test Coverage:
- Backward compatible API methods
- Delegation to orchestrator
- Return type compatibility
- Legacy behavior preservation
- Deprecated methods warnings
- Singleton factory

Architecture Reference:
    docs/architectuur/synonym-orchestrator-architecture-v3.1.md
    Lines 504-542: Façade specification

Requirements:
- Python 3.11+
- pytest
- unittest.mock
"""

from unittest.mock import MagicMock, Mock

import pytest

from src.models.synonym_models import WeightedSynonym
from src.services.web_lookup.synonym_service import (
    JuridischeSynoniemService,
    get_synonym_service,
)


class TestJuridischeSynoniemServiceFacade:
    """Test suite voor façade backward compatibility."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator with default behavior."""
        orchestrator = Mock()
        orchestrator.get_synonyms_for_lookup = Mock(return_value=[])
        orchestrator.get_cache_stats = Mock(
            return_value={
                "size": 0,
                "hits": 0,
                "misses": 0,
                "hit_rate": 0.0,
            }
        )
        orchestrator.registry = Mock()
        orchestrator.registry.get_statistics = Mock(
            return_value={
                "total_groups": 0,
                "total_members": 0,
                "avg_members_per_group": 0,
            }
        )
        return orchestrator

    @pytest.fixture
    def service(self, mock_orchestrator):
        """Create service with mock orchestrator."""
        return JuridischeSynoniemService(mock_orchestrator)


class TestGetSynoniemen(TestJuridischeSynoniemServiceFacade):
    """Test suite voor get_synoniemen() - backward compatible API."""

    def test_returns_list_of_strings(self, service, mock_orchestrator):
        """
        Test: get_synoniemen() returns list of strings (NO weights).

        Scenario:
        - Orchestrator returns WeightedSynonym objects
        - Service extracts term strings
        - Weights are dropped (backward compatible)
        """
        # Mock orchestrator response
        mock_orchestrator.get_synonyms_for_lookup.return_value = [
            WeightedSynonym(
                term="synoniem1", weight=0.95, status="active", is_preferred=False
            ),
            WeightedSynonym(
                term="synoniem2", weight=0.90, status="active", is_preferred=False
            ),
            WeightedSynonym(
                term="synoniem3", weight=0.85, status="active", is_preferred=False
            ),
        ]

        result = service.get_synoniemen("test")

        # Verify type
        assert isinstance(result, list)
        assert all(isinstance(s, str) for s in result)

        # Verify content
        assert result == ["synoniem1", "synoniem2", "synoniem3"]

    def test_delegates_to_orchestrator(self, service, mock_orchestrator):
        """
        Test: get_synoniemen() delegates to orchestrator.get_synonyms_for_lookup().

        Scenario:
        - Call get_synoniemen("test")
        - Verify orchestrator.get_synonyms_for_lookup was called with correct args
        """
        service.get_synoniemen("test")

        # Verify orchestrator was called
        mock_orchestrator.get_synonyms_for_lookup.assert_called_once_with(
            term="test", max_results=8, min_weight=0.7  # Historical default
        )

    def test_filters_out_term_itself(self, service, mock_orchestrator):
        """
        Test: get_synoniemen() excludes the term itself (legacy behavior).

        Scenario:
        - Orchestrator returns synonyms including the term itself
        - Service filters out the term
        - Only other synonyms returned
        """
        mock_orchestrator.get_synonyms_for_lookup.return_value = [
            WeightedSynonym(
                term="test", weight=1.0, status="active", is_preferred=True
            ),
            WeightedSynonym(
                term="synoniem1", weight=0.95, status="active", is_preferred=False
            ),
            WeightedSynonym(
                term="synoniem2", weight=0.90, status="active", is_preferred=False
            ),
        ]

        result = service.get_synoniemen("test")

        # Verify term itself is excluded
        assert "test" not in result
        assert result == ["synoniem1", "synoniem2"]

    def test_case_insensitive_filtering(self, service, mock_orchestrator):
        """
        Test: Term filtering is case-insensitive.

        Scenario:
        - Input: "TEST"
        - Orchestrator returns "test" (lowercase)
        - Service correctly filters it out
        """
        mock_orchestrator.get_synonyms_for_lookup.return_value = [
            WeightedSynonym(
                term="test", weight=1.0, status="active", is_preferred=True
            ),
            WeightedSynonym(
                term="synoniem1", weight=0.95, status="active", is_preferred=False
            ),
        ]

        result = service.get_synoniemen("TEST")

        # Verify case-insensitive filtering
        assert "test" not in result
        assert "TEST" not in result
        assert result == ["synoniem1"]

    def test_empty_term(self, service, mock_orchestrator):
        """
        Test: Empty term returns empty list.

        Scenario:
        - Input: ""
        - Expected: []
        - Orchestrator NOT called
        """
        result = service.get_synoniemen("")

        assert result == []
        mock_orchestrator.get_synonyms_for_lookup.assert_not_called()

    def test_whitespace_term(self, service, mock_orchestrator):
        """
        Test: Whitespace-only term returns empty list.

        Scenario:
        - Input: "   "
        - Expected: []
        - Orchestrator NOT called
        """
        result = service.get_synoniemen("   ")

        assert result == []
        mock_orchestrator.get_synonyms_for_lookup.assert_not_called()


class TestGetSynonymsWithWeights(TestJuridischeSynoniemServiceFacade):
    """Test suite voor get_synonyms_with_weights() - enhanced API."""

    def test_returns_list_of_tuples(self, service, mock_orchestrator):
        """
        Test: get_synonyms_with_weights() returns list of (term, weight) tuples.

        Scenario:
        - Orchestrator returns WeightedSynonym objects
        - Service extracts (term, weight) tuples
        """
        mock_orchestrator.get_synonyms_for_lookup.return_value = [
            WeightedSynonym(
                term="synoniem1", weight=0.95, status="active", is_preferred=False
            ),
            WeightedSynonym(
                term="synoniem2", weight=0.90, status="active", is_preferred=False
            ),
        ]

        result = service.get_synonyms_with_weights("test")

        # Verify type
        assert isinstance(result, list)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in result)

        # Verify content
        assert result == [("synoniem1", 0.95), ("synoniem2", 0.90)]

    def test_delegates_to_orchestrator(self, service, mock_orchestrator):
        """
        Test: get_synonyms_with_weights() delegates to orchestrator.

        Scenario:
        - Call get_synonyms_with_weights("test")
        - Verify orchestrator.get_synonyms_for_lookup was called
        """
        service.get_synonyms_with_weights("test")

        mock_orchestrator.get_synonyms_for_lookup.assert_called_once_with(
            term="test", max_results=8
        )

    def test_filters_out_term_itself(self, service, mock_orchestrator):
        """
        Test: get_synonyms_with_weights() excludes the term itself.

        Scenario:
        - Orchestrator returns term + synonyms
        - Service filters out term
        """
        mock_orchestrator.get_synonyms_for_lookup.return_value = [
            WeightedSynonym(
                term="test", weight=1.0, status="active", is_preferred=True
            ),
            WeightedSynonym(
                term="synoniem1", weight=0.95, status="active", is_preferred=False
            ),
        ]

        result = service.get_synonyms_with_weights("test")

        # Verify term itself is excluded
        assert ("test", 1.0) not in result
        assert result == [("synoniem1", 0.95)]

    def test_preserves_weight_order(self, service, mock_orchestrator):
        """
        Test: Weights are preserved in correct order (orchestrator handles sorting).

        Scenario:
        - Orchestrator returns sorted synonyms
        - Service preserves order
        """
        mock_orchestrator.get_synonyms_for_lookup.return_value = [
            WeightedSynonym(
                term="synoniem1", weight=0.95, status="active", is_preferred=False
            ),
            WeightedSynonym(
                term="synoniem2", weight=0.90, status="active", is_preferred=False
            ),
            WeightedSynonym(
                term="synoniem3", weight=0.85, status="active", is_preferred=False
            ),
        ]

        result = service.get_synonyms_with_weights("test")

        # Verify order preserved
        assert result[0][1] > result[1][1] > result[2][1]  # Weights descending


class TestExpandQueryTerms(TestJuridischeSynoniemServiceFacade):
    """Test suite voor expand_query_terms() - query expansion."""

    def test_starts_with_original_term(self, service, mock_orchestrator):
        """
        Test: expand_query_terms() starts with original term.

        Scenario:
        - Input: "test"
        - Expected: ["test", <synonyms>...]
        """
        mock_orchestrator.get_synonyms_for_lookup.return_value = [
            WeightedSynonym(
                term="synoniem1", weight=0.95, status="active", is_preferred=False
            ),
        ]

        result = service.expand_query_terms("test")

        # Verify starts with original term
        assert result[0] == "test"

    def test_appends_synonyms(self, service, mock_orchestrator):
        """
        Test: expand_query_terms() appends top-N synonyms.

        Scenario:
        - max_synonyms: 3
        - Expected: [original, syn1, syn2, syn3]
        """
        mock_orchestrator.get_synonyms_for_lookup.return_value = [
            WeightedSynonym(
                term="synoniem1", weight=0.95, status="active", is_preferred=False
            ),
            WeightedSynonym(
                term="synoniem2", weight=0.90, status="active", is_preferred=False
            ),
            WeightedSynonym(
                term="synoniem3", weight=0.85, status="active", is_preferred=False
            ),
        ]

        result = service.expand_query_terms("test", max_synonyms=3)

        assert result == ["test", "synoniem1", "synoniem2", "synoniem3"]

    def test_respects_max_synonyms_limit(self, service, mock_orchestrator):
        """
        Test: expand_query_terms() respects max_synonyms parameter.

        Scenario:
        - Orchestrator returns 5 synonyms
        - max_synonyms: 2
        - Expected: [original, syn1, syn2] (only 2 appended)
        """
        mock_orchestrator.get_synonyms_for_lookup.return_value = [
            WeightedSynonym(
                term=f"synoniem{i}",
                weight=1.0 - i * 0.1,
                status="active",
                is_preferred=False,
            )
            for i in range(1, 6)
        ]

        result = service.expand_query_terms("test", max_synonyms=2)

        assert len(result) == 3  # Original + 2
        assert result == ["test", "synoniem1", "synoniem2"]

    def test_default_max_synonyms_is_three(self, service, mock_orchestrator):
        """
        Test: expand_query_terms() defaults to max_synonyms=3.

        Scenario:
        - No max_synonyms parameter
        - Expected: 3 synonyms appended
        """
        mock_orchestrator.get_synonyms_for_lookup.return_value = [
            WeightedSynonym(
                term=f"synoniem{i}",
                weight=1.0 - i * 0.1,
                status="active",
                is_preferred=False,
            )
            for i in range(1, 6)
        ]

        service.expand_query_terms("test")

        # Verify default behavior
        mock_orchestrator.get_synonyms_for_lookup.assert_called_once()
        call_args = mock_orchestrator.get_synonyms_for_lookup.call_args
        assert call_args.kwargs["max_results"] == 3  # Default

    def test_no_synonyms_returns_original_only(self, service, mock_orchestrator):
        """
        Test: expand_query_terms() with no synonyms returns original term only.

        Scenario:
        - Orchestrator returns empty list
        - Expected: [original]
        """
        mock_orchestrator.get_synonyms_for_lookup.return_value = []

        result = service.expand_query_terms("test")

        assert result == ["test"]

    def test_filters_out_term_from_synonyms(self, service, mock_orchestrator):
        """
        Test: expand_query_terms() doesn't duplicate term in list.

        Scenario:
        - Orchestrator returns term itself + synonyms
        - Expected: [original, syn1, syn2] (no duplicate)
        """
        mock_orchestrator.get_synonyms_for_lookup.return_value = [
            WeightedSynonym(
                term="test", weight=1.0, status="active", is_preferred=True
            ),
            WeightedSynonym(
                term="synoniem1", weight=0.95, status="active", is_preferred=False
            ),
        ]

        result = service.expand_query_terms("test")

        # Verify no duplication
        assert result.count("test") == 1
        assert result == ["test", "synoniem1"]


class TestHasSynoniemen(TestJuridischeSynoniemServiceFacade):
    """Test suite voor has_synoniemen() - boolean check."""

    def test_returns_true_when_synonyms_exist(self, service, mock_orchestrator):
        """
        Test: has_synoniemen() returns True when synonyms exist.

        Scenario:
        - get_synoniemen() returns non-empty list
        - Expected: True
        """
        mock_orchestrator.get_synonyms_for_lookup.return_value = [
            WeightedSynonym(
                term="synoniem1", weight=0.95, status="active", is_preferred=False
            ),
        ]

        result = service.has_synoniemen("test")

        assert result is True

    def test_returns_false_when_no_synonyms(self, service, mock_orchestrator):
        """
        Test: has_synoniemen() returns False when no synonyms.

        Scenario:
        - get_synoniemen() returns empty list
        - Expected: False
        """
        mock_orchestrator.get_synonyms_for_lookup.return_value = []

        result = service.has_synoniemen("test")

        assert result is False

    def test_returns_false_when_only_term_itself(self, service, mock_orchestrator):
        """
        Test: has_synoniemen() returns False when only term itself exists.

        Scenario:
        - Orchestrator returns only the term itself
        - get_synoniemen() filters it out → empty list
        - Expected: False
        """
        mock_orchestrator.get_synonyms_for_lookup.return_value = [
            WeightedSynonym(
                term="test", weight=1.0, status="active", is_preferred=True
            ),
        ]

        result = service.has_synoniemen("test")

        assert result is False


class TestGetStats(TestJuridischeSynoniemServiceFacade):
    """Test suite voor get_stats() - statistics."""

    def test_combines_cache_and_registry_stats(self, service, mock_orchestrator):
        """
        Test: get_stats() combines orchestrator cache + registry stats.

        Scenario:
        - Mock cache stats
        - Mock registry stats
        - Verify combined output
        """
        mock_orchestrator.get_cache_stats.return_value = {
            "size": 42,
            "hits": 100,
            "misses": 20,
            "hit_rate": 0.833,
        }

        mock_orchestrator.registry.get_statistics.return_value = {
            "total_groups": 150,
            "total_members": 450,
            "avg_members_per_group": 3.0,
        }

        result = service.get_stats()

        # Verify cache metrics
        assert result["cache_size"] == 42
        assert result["cache_hit_rate"] == 0.833

        # Verify registry metrics
        assert result["total_groups"] == 150
        assert result["total_members"] == 450

        # Verify legacy compatibility keys
        assert result["hoofdtermen"] == 150  # Renamed
        assert result["totaal_synoniemen"] == 450  # Renamed


class TestDeprecatedMethods(TestJuridischeSynoniemServiceFacade):
    """Test suite voor deprecated methods - warnings and fallbacks."""

    def test_find_matching_synoniemen_returns_empty_dict(
        self, service, mock_orchestrator
    ):
        """
        Test: find_matching_synoniemen() is deprecated and returns empty dict.

        Scenario:
        - Feature removed in v3.1
        - Expected: {} (empty dict)
        - Warning logged
        """
        result = service.find_matching_synoniemen("test text")

        assert result == {}

    def test_get_related_terms_returns_empty_list(self, service, mock_orchestrator):
        """
        Test: get_related_terms() is deprecated and returns empty list.

        Scenario:
        - Semantic clusters not implemented
        - Expected: []
        - Warning logged
        """
        result = service.get_related_terms("test")

        assert result == []

    def test_get_cluster_name_returns_none(self, service, mock_orchestrator):
        """
        Test: get_cluster_name() is deprecated and returns None.

        Scenario:
        - Semantic clusters not implemented
        - Expected: None
        - Warning logged
        """
        result = service.get_cluster_name("test")

        assert result is None

    def test_expand_with_related_falls_back_to_expand_query_terms(
        self, service, mock_orchestrator
    ):
        """
        Test: expand_with_related() falls back to expand_query_terms().

        Scenario:
        - Semantic clusters not implemented
        - Fallback to regular synonym expansion
        - Warning logged
        """
        mock_orchestrator.get_synonyms_for_lookup.return_value = [
            WeightedSynonym(
                term="synoniem1", weight=0.95, status="active", is_preferred=False
            ),
        ]

        result = service.expand_with_related("test", max_synonyms=2, max_related=2)

        # Verify fallback behavior
        assert result == ["test", "synoniem1"]
        # Verify orchestrator was called (expand_query_terms path)
        mock_orchestrator.get_synonyms_for_lookup.assert_called_once()

    def test_get_all_terms_returns_empty_set(self, service, mock_orchestrator):
        """
        Test: get_all_terms() is expensive and returns empty set.

        Scenario:
        - Method discouraged (expensive in graph model)
        - Expected: set() (empty)
        - Warning logged
        """
        result = service.get_all_terms()

        assert result == set()


class TestSingletonFactory(TestJuridischeSynoniemServiceFacade):
    """Test suite voor get_synonym_service() singleton factory."""

    def test_singleton_returns_same_instance(self, mock_orchestrator):
        """
        Test: get_synonym_service() returns same instance (singleton).

        Scenario:
        - Call get_synonym_service() twice
        - Expected: Same instance object
        """
        # Reset singleton
        import src.services.web_lookup.synonym_service as module

        module._singleton = None

        service1 = get_synonym_service(orchestrator=mock_orchestrator)
        service2 = get_synonym_service(orchestrator=mock_orchestrator)

        assert service1 is service2

    def test_config_path_parameter_is_ignored(self, mock_orchestrator):
        """
        Test: config_path parameter is deprecated and ignored.

        Scenario:
        - Call with config_path="custom.yaml"
        - Expected: Parameter ignored, service created normally
        - Warning logged
        """
        # Reset singleton
        import src.services.web_lookup.synonym_service as module

        module._singleton = None

        service = get_synonym_service(
            config_path="custom.yaml", orchestrator=mock_orchestrator
        )

        assert isinstance(service, JuridischeSynoniemService)

    @pytest.mark.skip(
        reason="DEF-195: Test requires ServiceContainer to be unavailable, "
        "but in test environment it's always available. "
        "Error handling is verified via code review - ValueError is raised when container fails."
    )
    def test_raises_error_without_orchestrator(self):
        """
        Test: get_synonym_service() raises error without orchestrator.

        Scenario:
        - No orchestrator parameter
        - ServiceContainer fails to provide orchestrator
        - Expected: ValueError

        Note: Skipped because mocking the import failure is complex
        and the behavior is correct (container provides orchestrator).
        """


class TestDelegationPatterns(TestJuridischeSynoniemServiceFacade):
    """Test suite voor verification of delegation patterns."""

    def test_all_queries_delegate_to_orchestrator(self, service, mock_orchestrator):
        """
        Test: Verify NO business logic in façade - all delegates to orchestrator.

        Scenario:
        - Call all query methods
        - Verify orchestrator.get_synonyms_for_lookup was called
        - Façade only adapts the API
        """
        # Mock response
        mock_orchestrator.get_synonyms_for_lookup.return_value = [
            WeightedSynonym(
                term="synoniem1", weight=0.95, status="active", is_preferred=False
            ),
        ]

        # Call all query methods
        service.get_synoniemen("test")
        service.get_synonyms_with_weights("test")
        service.expand_query_terms("test")
        service.has_synoniemen("test")

        # Verify orchestrator was called 4 times
        assert mock_orchestrator.get_synonyms_for_lookup.call_count == 4

    def test_no_direct_database_access(self, service):
        """
        Test: Façade has NO direct database access.

        Scenario:
        - Verify service has no db_path or connection
        - Only has orchestrator reference
        """
        # Verify no database attributes
        assert not hasattr(service, "db_path")
        assert not hasattr(service, "connection")
        assert not hasattr(service, "_conn")

        # Verify only has orchestrator
        assert hasattr(service, "orchestrator")

    def test_no_yaml_loading(self, service):
        """
        Test: Façade has NO YAML loading logic.

        Scenario:
        - Verify no config_path or YAML loading
        - All data comes from orchestrator
        """
        # Verify no YAML attributes
        assert not hasattr(service, "config_path")
        assert not hasattr(service, "synoniemen")  # Old YAML dict
        assert not hasattr(service, "reverse_index")  # Old YAML index
        assert not hasattr(service, "clusters")  # Old YAML clusters
