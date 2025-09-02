"""
Tests voor A/B Testing Framework.

Comprehensive test suite voor de A/B testing functionaliteit
die legacy en moderne web lookup implementaties vergelijkt.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import asdict

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.ab_testing_framework import (
    ABTestingFramework, ABTestConfig, TestVariant,
    ComparisonResult, PerformanceMetrics, QualityMetrics,
    quick_ab_test, ab_test_with_report
)
from services.interfaces import LookupRequest, LookupResult, WebSource


class TestABTestingFramework:
    """Test class voor ABTestingFramework."""

    @pytest.fixture
    def framework(self):
        """Maak een test A/B testing framework instance."""
        config = ABTestConfig(
            test_terms=["test", "recht", "wet"],
            max_results_per_service=3,
            timeout_seconds=5,
            repeat_count=2
        )
        return ABTestingFramework(config)

    @pytest.fixture
    def sample_lookup_results(self):
        """Sample lookup resultaten voor testing."""
        return [
            LookupResult(
                term="test",
                source=WebSource(
                    name="Test Source",
                    url="https://test.com",
                    confidence=0.8,
                    api_type="test"
                ),
                definition="Test definitie",
                success=True,
                metadata={"type": "test"}
            )
        ]

    def test_framework_initialization(self, framework):
        """Test framework initialization."""
        assert framework.config.max_results_per_service == 3
        assert framework.config.timeout_seconds == 5
        assert framework.config.repeat_count == 2
        assert framework.modern_service is not None
        assert framework.legacy_service is None
        assert len(framework._test_history) == 0

    def test_ab_test_config_defaults(self):
        """Test ABTestConfig default waarden."""
        config = ABTestConfig()

        assert config.test_terms == []
        assert config.max_results_per_service == 5
        assert config.timeout_seconds == 30
        assert config.repeat_count == 3
        assert config.include_performance is True
        assert config.include_quality is True
        assert config.legacy_fallback is True

    def test_performance_metrics_initialization(self):
        """Test PerformanceMetrics initialization."""
        metrics = PerformanceMetrics()

        assert metrics.response_time == 0.0
        assert metrics.success_rate == 0.0
        assert metrics.results_count == 0
        assert metrics.error_count == 0
        assert metrics.timeout_count == 0
        assert metrics.confidence_avg == 0.0
        assert metrics.confidence_std == 0.0

    def test_quality_metrics_initialization(self):
        """Test QualityMetrics initialization."""
        metrics = QualityMetrics()

        assert metrics.relevance_score == 0.0
        assert metrics.completeness_score == 0.0
        assert metrics.consistency_score == 0.0
        assert metrics.source_diversity == 0
        assert metrics.juridical_accuracy == 0.0

    def test_comparison_result_initialization(self):
        """Test ComparisonResult initialization."""
        result = ComparisonResult(term="test")

        assert result.term == "test"
        assert result.legacy_results == []
        assert result.modern_results == []
        assert isinstance(result.legacy_performance, PerformanceMetrics)
        assert isinstance(result.modern_performance, PerformanceMetrics)
        assert isinstance(result.legacy_quality, QualityMetrics)
        assert isinstance(result.modern_quality, QualityMetrics)
        assert result.recommendation == TestVariant.BOTH
        assert result.confidence == 0.0
        assert result.notes == ""

    @pytest.mark.asyncio
    async def test_test_modern_service_success(self, framework, sample_lookup_results):
        """Test moderne service testing met success."""
        request = LookupRequest(term="test", max_results=2, timeout=5)

        with patch.object(framework.modern_service, 'lookup') as mock_lookup:
            mock_lookup.return_value = sample_lookup_results

            results, performance = await framework._test_modern_service(request)

            assert len(results) == len(sample_lookup_results) * framework.config.repeat_count
            assert performance.success_rate == 1.0
            assert performance.error_count == 0
            assert performance.timeout_count == 0
            assert performance.response_time > 0

    @pytest.mark.asyncio
    async def test_test_modern_service_with_errors(self, framework):
        """Test moderne service testing met errors."""
        request = LookupRequest(term="test", max_results=2, timeout=5)

        with patch.object(framework.modern_service, 'lookup') as mock_lookup:
            mock_lookup.side_effect = [Exception("API Error"), Exception("Network Error"), Exception("Third Error")]

            results, performance = await framework._test_modern_service(request)

            assert len(results) == 0
            assert performance.success_rate == 0.0  # All calls failed
            assert performance.error_count == 3

    @pytest.mark.asyncio
    async def test_test_modern_service_with_timeout(self, framework):
        """Test moderne service testing met timeout."""
        request = LookupRequest(term="test", max_results=2, timeout=1)

        # Mock een slow response
        async def slow_lookup(*args, **kwargs):
            await asyncio.sleep(2)  # Longer than timeout
            return []

        with patch.object(framework.modern_service, 'lookup', side_effect=slow_lookup):
            results, performance = await framework._test_modern_service(request)

            assert len(results) == 0
            assert performance.timeout_count > 0

    @pytest.mark.asyncio
    async def test_test_legacy_service(self, framework):
        """Test legacy service testing (mock implementation)."""
        request = LookupRequest(term="test", max_results=2, timeout=5)

        results, performance = await framework._test_legacy_service(request)

        # Legacy service is mocked, so we get consistent results
        assert len(results) == 1
        assert results[0].term == "test"
        assert results[0].source.name == "Legacy Source"
        assert results[0].source.api_type == "legacy"
        assert performance.success_rate == 0.8  # Mock value
        assert performance.response_time > 0

    def test_calculate_quality_metrics_empty(self, framework):
        """Test quality metrics berekening met lege resultaten."""
        metrics = framework._calculate_quality_metrics("test", [])

        assert metrics.relevance_score == 0.0
        assert metrics.completeness_score == 0.0
        assert metrics.source_diversity == 0
        assert metrics.juridical_accuracy == 0.0

    def test_calculate_quality_metrics_with_results(self, framework, sample_lookup_results):
        """Test quality metrics berekening met resultaten."""
        # Add some variety to test data
        results = sample_lookup_results + [
            LookupResult(
                term="test",
                source=WebSource(
                    name="Different Source",
                    url="https://different.com",
                    confidence=0.9,
                    api_type="test",
                    is_juridical=True
                ),
                definition="Uitgebreide definitie van test term met veel meer inhoud en details",
                success=True,
                metadata={"type": "extended", "category": "legal", "references": 3}
            )
        ]

        metrics = framework._calculate_quality_metrics("test", results)

        assert metrics.relevance_score > 0  # Should find "test" in definitions
        assert metrics.completeness_score > 0  # Should score on definition length and metadata
        assert metrics.source_diversity == 2  # Two different sources
        assert metrics.juridical_accuracy == 0.0  # Not a juridical term

    def test_calculate_quality_metrics_juridical_term(self, framework, sample_lookup_results):
        """Test quality metrics voor juridische termen."""
        # Make source juridical
        sample_lookup_results[0].source.is_juridical = True

        metrics = framework._calculate_quality_metrics("wet", sample_lookup_results)

        assert metrics.juridical_accuracy == 1.0  # All sources are juridical for juridical term

    def test_generate_recommendation_modern_wins(self, framework):
        """Test recommendation generation wanneer modern wint."""
        comparison = ComparisonResult(
            term="test",
            modern_performance=PerformanceMetrics(
                response_time=1.0,
                success_rate=1.0,
                results_count=5
            ),
            legacy_performance=PerformanceMetrics(
                response_time=2.0,
                success_rate=0.8,
                results_count=3
            ),
            modern_quality=QualityMetrics(
                relevance_score=0.9,
                completeness_score=0.8
            ),
            legacy_quality=QualityMetrics(
                relevance_score=0.7,
                completeness_score=0.6
            )
        )

        recommendation, confidence, notes = framework._generate_recommendation(comparison)

        assert recommendation == TestVariant.MODERN
        assert confidence > 0.7
        assert "Modern is faster" in notes
        assert "Modern has higher success rate" in notes

    def test_generate_recommendation_legacy_wins(self, framework):
        """Test recommendation generation wanneer legacy wint."""
        comparison = ComparisonResult(
            term="test",
            modern_performance=PerformanceMetrics(
                response_time=3.0,
                success_rate=0.6,
                results_count=2
            ),
            legacy_performance=PerformanceMetrics(
                response_time=1.0,
                success_rate=1.0,
                results_count=5
            ),
            modern_quality=QualityMetrics(
                relevance_score=0.6,
                completeness_score=0.5
            ),
            legacy_quality=QualityMetrics(
                relevance_score=0.9,
                completeness_score=0.8
            )
        )

        recommendation, confidence, notes = framework._generate_recommendation(comparison)

        assert recommendation == TestVariant.LEGACY
        assert confidence > 0.7
        assert "Legacy is faster" in notes
        assert "Legacy has higher success rate" in notes

    def test_generate_recommendation_mixed_results(self, framework):
        """Test recommendation generation met mixed results."""
        comparison = ComparisonResult(
            term="test",
            modern_performance=PerformanceMetrics(
                response_time=1.0,
                success_rate=0.8,
                results_count=3
            ),
            legacy_performance=PerformanceMetrics(
                response_time=1.0,
                success_rate=0.8,
                results_count=3
            )
        )

        recommendation, confidence, notes = framework._generate_recommendation(comparison)

        assert recommendation == TestVariant.BOTH
        assert confidence == 0.5
        assert "Mixed results" in notes

    def test_generate_recommendation_no_data(self, framework):
        """Test recommendation generation zonder data."""
        comparison = ComparisonResult(term="test")

        recommendation, confidence, notes = framework._generate_recommendation(comparison)

        assert recommendation == TestVariant.BOTH
        assert confidence == 0.5
        assert "No clear difference found" in notes

    @pytest.mark.asyncio
    async def test_compare_term_modern_only(self, framework, sample_lookup_results):
        """Test vergelijking van één term - alleen modern."""
        with patch.object(framework.modern_service, 'lookup') as mock_lookup:
            mock_lookup.return_value = sample_lookup_results

            comparison = await framework._compare_term("test", TestVariant.MODERN)

            assert comparison.term == "test"
            assert len(comparison.modern_results) > 0
            assert len(comparison.legacy_results) == 0
            assert comparison.modern_performance.results_count > 0
            assert comparison.recommendation is not None

    @pytest.mark.asyncio
    async def test_compare_term_legacy_only(self, framework):
        """Test vergelijking van één term - alleen legacy."""
        comparison = await framework._compare_term("test", TestVariant.LEGACY)

        assert comparison.term == "test"
        assert len(comparison.modern_results) == 0
        assert len(comparison.legacy_results) > 0
        assert comparison.legacy_performance.results_count > 0
        assert comparison.recommendation is not None

    @pytest.mark.asyncio
    async def test_compare_term_both(self, framework, sample_lookup_results):
        """Test vergelijking van één term - beide implementaties."""
        with patch.object(framework.modern_service, 'lookup') as mock_lookup:
            mock_lookup.return_value = sample_lookup_results

            comparison = await framework._compare_term("test", TestVariant.BOTH)

            assert comparison.term == "test"
            assert len(comparison.modern_results) > 0
            assert len(comparison.legacy_results) > 0
            assert comparison.modern_performance.results_count > 0
            assert comparison.legacy_performance.results_count > 0
            assert comparison.recommendation is not None

    @pytest.mark.asyncio
    async def test_run_comparison_success(self, framework, sample_lookup_results):
        """Test volledige A/B test vergelijking."""
        with patch.object(framework.modern_service, 'lookup') as mock_lookup:
            mock_lookup.return_value = sample_lookup_results

            terms = ["test1", "test2"]
            results = await framework.run_comparison(terms, TestVariant.BOTH)

            assert len(results) == 2
            assert all(isinstance(r, ComparisonResult) for r in results)
            assert len(framework._test_history) == 2

    @pytest.mark.asyncio
    async def test_run_comparison_with_errors(self, framework):
        """Test A/B test vergelijking met errors."""
        with patch.object(framework, '_compare_term') as mock_compare:
            mock_compare.side_effect = [
                ComparisonResult(term="test1"),
                Exception("Comparison failed")
            ]

            terms = ["test1", "test2"]
            results = await framework.run_comparison(terms)

            assert len(results) == 2
            assert results[0].term == "test1"
            assert results[1].term == "test2"
            assert results[1].recommendation == TestVariant.LEGACY  # Safe fallback
            assert "Test failed" in results[1].notes

    def test_generate_report_empty(self, framework):
        """Test report generation met lege resultaten."""
        report = framework.generate_report([])

        assert "No test results available" in report

    def test_generate_report_with_results(self, framework):
        """Test report generation met resultaten."""
        results = [
            ComparisonResult(
                term="test1",
                recommendation=TestVariant.MODERN,
                confidence=0.8,
                modern_performance=PerformanceMetrics(response_time=1.0, results_count=3),
                legacy_performance=PerformanceMetrics(response_time=2.0, results_count=2),
                notes="Modern is faster"
            ),
            ComparisonResult(
                term="test2",
                recommendation=TestVariant.LEGACY,
                confidence=0.7,
                modern_performance=PerformanceMetrics(response_time=3.0, results_count=1),
                legacy_performance=PerformanceMetrics(response_time=1.5, results_count=4),
                notes="Legacy has more results"
            )
        ]

        report = framework.generate_report(results)

        assert "A/B TEST REPORT" in report
        assert "Total tests: 2" in report
        assert "Modern preferred: 1 (50.0%)" in report
        assert "Legacy preferred: 1 (50.0%)" in report
        assert "Both equivalent: 0 (0.0%)" in report
        assert "PERFORMANCE SUMMARY" in report
        assert "DETAILED RESULTS" in report
        assert "test1" in report
        assert "test2" in report

    def test_get_test_history(self, framework):
        """Test test history retrieval."""
        # Add some history
        framework._test_history = [
            ComparisonResult(term="test1"),
            ComparisonResult(term="test2")
        ]

        history = framework.get_test_history()

        assert len(history) == 2
        assert history[0].term == "test1"
        assert history[1].term == "test2"

        # Ensure it's a copy
        history.clear()
        assert len(framework._test_history) == 2

    def test_clear_history(self, framework):
        """Test clearing test history."""
        # Add some history
        framework._test_history = [
            ComparisonResult(term="test1"),
            ComparisonResult(term="test2")
        ]

        framework.clear_history()

        assert len(framework._test_history) == 0


class TestStandaloneFunctions:
    """Test standalone convenience functions."""

    @pytest.mark.asyncio
    async def test_quick_ab_test(self):
        """Test quick_ab_test convenience function."""
        with patch.object(ABTestingFramework, 'run_comparison') as mock_run:
            mock_results = [ComparisonResult(term="test")]
            mock_run.return_value = mock_results

            results = await quick_ab_test(["test"])

            assert results == mock_results
            mock_run.assert_called_once_with(["test"])

    @pytest.mark.asyncio
    async def test_ab_test_with_report(self):
        """Test ab_test_with_report convenience function."""
        with patch.object(ABTestingFramework, 'run_comparison') as mock_run, \
             patch.object(ABTestingFramework, 'generate_report') as mock_report:

            mock_results = [ComparisonResult(term="test")]
            mock_run.return_value = mock_results
            mock_report.return_value = "Test Report"

            report = await ab_test_with_report(["test"])

            assert report == "Test Report"
            mock_run.assert_called_once_with(["test"])
            mock_report.assert_called_once_with(mock_results)


# Integration tests
@pytest.mark.integration
class TestABTestingFrameworkIntegration:
    """Integration tests voor A/B Testing Framework."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("RUN_INTEGRATION_TESTS"),
                       reason="Integration tests disabled")
    async def test_real_ab_comparison(self):
        """Test echte A/B comparison met real services."""
        config = ABTestConfig(
            test_terms=["recht"],
            max_results_per_service=2,
            timeout_seconds=10,
            repeat_count=1
        )

        framework = ABTestingFramework(config)

        results = await framework.run_comparison(["recht"], TestVariant.MODERN)

        if results:
            assert len(results) == 1
            result = results[0]
            assert result.term == "recht"
            assert result.recommendation is not None
            assert result.confidence >= 0.0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
