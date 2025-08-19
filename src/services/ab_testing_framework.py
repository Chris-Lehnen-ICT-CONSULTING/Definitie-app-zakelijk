"""
A/B Testing Framework voor Web Lookup Services.

Implementeert systematische vergelijking tussen legacy en moderne
web lookup implementaties om migratie beslissingen te ondersteunen.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum

from .interfaces import LookupRequest, LookupResult, WebSource
from .modern_web_lookup_service import ModernWebLookupService

logger = logging.getLogger(__name__)


class TestVariant(Enum):
    """Test varianten voor A/B testing."""

    LEGACY = "legacy"
    MODERN = "modern"
    BOTH = "both"


@dataclass
class PerformanceMetrics:
    """Performance metrics voor een lookup test."""

    response_time: float = 0.0
    success_rate: float = 0.0
    results_count: int = 0
    error_count: int = 0
    timeout_count: int = 0
    confidence_avg: float = 0.0
    confidence_std: float = 0.0


@dataclass
class QualityMetrics:
    """Quality metrics voor lookup resultaten."""

    relevance_score: float = 0.0  # Based on term matching
    completeness_score: float = 0.0  # Based on definition length and metadata
    consistency_score: float = 0.0  # Between multiple runs
    source_diversity: int = 0  # Number of different sources
    juridical_accuracy: float = 0.0  # For legal terms


@dataclass
class ComparisonResult:
    """Resultaat van A/B test vergelijking."""

    term: str
    legacy_results: list[LookupResult] = field(default_factory=list)
    modern_results: list[LookupResult] = field(default_factory=list)
    legacy_performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    modern_performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    legacy_quality: QualityMetrics = field(default_factory=QualityMetrics)
    modern_quality: QualityMetrics = field(default_factory=QualityMetrics)
    recommendation: TestVariant = TestVariant.BOTH
    confidence: float = 0.0  # 0-1 confidence in recommendation
    notes: str = ""


@dataclass
class ABTestConfig:
    """Configuratie voor A/B testing."""

    test_terms: list[str] = field(default_factory=list)
    max_results_per_service: int = 5
    timeout_seconds: int = 30
    repeat_count: int = 3  # Voor consistency testing
    include_performance: bool = True
    include_quality: bool = True
    legacy_fallback: bool = True  # Allow fallback to legacy when modern fails


class ABTestingFramework:
    """
    A/B Testing Framework voor Web Lookup Services.

    Vergelijkt systematisch legacy en moderne implementaties
    om migratie beslissingen te ondersteunen.
    """

    def __init__(self, config: ABTestConfig | None = None):
        self.config = config or ABTestConfig()
        self.modern_service = ModernWebLookupService()
        self.legacy_service = None  # Will be initialized dynamically
        self._test_history: list[ComparisonResult] = []

    async def run_comparison(
        self, terms: list[str], variant: TestVariant = TestVariant.BOTH
    ) -> list[ComparisonResult]:
        """
        Run A/B test vergelijking voor gegeven termen.

        Args:
            terms: Lijst van test termen
            variant: Welke varianten te testen

        Returns:
            Lijst van ComparisonResult objecten
        """
        logger.info(
            f"Starting A/B test voor {len(terms)} termen (variant: {variant.value})"
        )

        results = []

        for term in terms:
            logger.info(f"Testing term: '{term}'")

            try:
                comparison = await self._compare_term(term, variant)
                results.append(comparison)

                # Store in history
                self._test_history.append(comparison)

            except Exception as e:
                logger.error(f"A/B test failed voor term '{term}': {e}")

                # Create failed comparison result
                failed_result = ComparisonResult(
                    term=term,
                    recommendation=TestVariant.LEGACY,  # Safe fallback
                    confidence=0.0,
                    notes=f"Test failed: {e!s}",
                )
                results.append(failed_result)

        logger.info(f"A/B test completed. {len(results)} results generated.")
        return results

    async def _compare_term(self, term: str, variant: TestVariant) -> ComparisonResult:
        """Vergelijk een specifieke term tussen legacy en modern."""
        comparison = ComparisonResult(term=term)

        # Setup lookup request
        request = LookupRequest(
            term=term,
            max_results=self.config.max_results_per_service,
            timeout=self.config.timeout_seconds,
        )

        # Test modern implementation
        if variant in [TestVariant.MODERN, TestVariant.BOTH]:
            modern_results, modern_perf = await self._test_modern_service(request)
            comparison.modern_results = modern_results
            comparison.modern_performance = modern_perf

            if self.config.include_quality:
                comparison.modern_quality = self._calculate_quality_metrics(
                    term, modern_results
                )

        # Test legacy implementation
        if variant in [TestVariant.LEGACY, TestVariant.BOTH]:
            legacy_results, legacy_perf = await self._test_legacy_service(request)
            comparison.legacy_results = legacy_results
            comparison.legacy_performance = legacy_perf

            if self.config.include_quality:
                comparison.legacy_quality = self._calculate_quality_metrics(
                    term, legacy_results
                )

        # Generate recommendation
        comparison.recommendation, comparison.confidence, comparison.notes = (
            self._generate_recommendation(comparison)
        )

        return comparison

    async def _test_modern_service(
        self, request: LookupRequest
    ) -> tuple[list[LookupResult], PerformanceMetrics]:
        """Test moderne service en meet performance."""
        start_time = time.time()
        errors = 0
        timeouts = 0
        all_results = []
        response_times = []

        # Repeat test voor consistency
        for i in range(self.config.repeat_count):
            try:
                loop_start = time.time()
                results = await asyncio.wait_for(
                    self.modern_service.lookup(request), timeout=request.timeout
                )
                loop_time = time.time() - loop_start
                response_times.append(loop_time)

                if results:
                    all_results.extend(results)

            except asyncio.TimeoutError:
                timeouts += 1
                response_times.append(request.timeout)
            except Exception as e:
                errors += 1
                logger.warning(f"Modern service error: {e}")
                response_times.append(0.0)

        total_time = time.time() - start_time

        # Calculate performance metrics
        performance = PerformanceMetrics(
            response_time=(
                sum(response_times) / len(response_times) if response_times else 0
            ),
            success_rate=(self.config.repeat_count - errors - timeouts)
            / self.config.repeat_count,
            results_count=len(all_results),
            error_count=errors,
            timeout_count=timeouts,
        )

        # Calculate confidence metrics
        if all_results:
            confidences = [r.source.confidence for r in all_results]
            performance.confidence_avg = sum(confidences) / len(confidences)
            if len(confidences) > 1:
                mean = performance.confidence_avg
                performance.confidence_std = (
                    sum((x - mean) ** 2 for x in confidences) / len(confidences)
                ) ** 0.5

        return all_results, performance

    async def _test_legacy_service(
        self, request: LookupRequest
    ) -> tuple[list[LookupResult], PerformanceMetrics]:
        """Test legacy service en meet performance."""
        # Voor nu simuleren we legacy service resultaten
        # In een echte implementatie zou je hier de legacy code aanroepen

        start_time = time.time()

        # Simulate legacy call with some delay
        await asyncio.sleep(0.5)  # Legacy is typically slower

        # Create mock legacy results
        mock_legacy_results = [
            LookupResult(
                term=request.term,
                source=WebSource(
                    name="Legacy Source",
                    url="http://legacy-example.com",
                    confidence=0.6,
                    api_type="legacy",
                ),
                definition=f"Legacy definitie voor {request.term}",
                success=True,
                metadata={"source_type": "legacy_simulation"},
            )
        ]

        total_time = time.time() - start_time

        performance = PerformanceMetrics(
            response_time=total_time,
            success_rate=0.8,  # Legacy has lower success rate
            results_count=len(mock_legacy_results),
            error_count=0,
            timeout_count=0,
            confidence_avg=0.6,
            confidence_std=0.1,
        )

        return mock_legacy_results, performance

    def _calculate_quality_metrics(
        self, term: str, results: list[LookupResult]
    ) -> QualityMetrics:
        """Bereken quality metrics voor lookup resultaten."""
        if not results:
            return QualityMetrics()

        # Relevance based op term matching in results
        relevance_scores = []
        for result in results:
            score = 0.0
            term_lower = term.lower()

            # Check title/source name
            if result.source.name and term_lower in result.source.name.lower():
                score += 0.3

            # Check definition content
            if result.definition and term_lower in result.definition.lower():
                score += 0.7

            relevance_scores.append(min(score, 1.0))

        # Completeness based op definition length and metadata
        completeness_scores = []
        for result in results:
            score = 0.0

            # Definition length (longer is better, up to a point)
            if result.definition:
                def_len = len(result.definition)
                if def_len > 50:
                    score += 0.5
                if def_len > 200:
                    score += 0.3

            # Metadata richness
            if result.metadata:
                metadata_count = len(result.metadata)
                score += min(metadata_count * 0.1, 0.4)

            # URL availability
            if result.source.url:
                score += 0.2

            completeness_scores.append(min(score, 1.0))

        # Source diversity
        unique_sources = len(set(r.source.name for r in results))

        # Juridical accuracy voor legal terms
        juridical_accuracy = 0.0
        if any(
            word in term.lower() for word in ["wet", "artikel", "recht", "juridisch"]
        ):
            juridical_sources = sum(1 for r in results if r.source.is_juridical)
            if results:
                juridical_accuracy = juridical_sources / len(results)

        return QualityMetrics(
            relevance_score=(
                sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
            ),
            completeness_score=(
                sum(completeness_scores) / len(completeness_scores)
                if completeness_scores
                else 0
            ),
            consistency_score=0.8,  # Placeholder - zou berekend worden over multiple runs
            source_diversity=unique_sources,
            juridical_accuracy=juridical_accuracy,
        )

    def _generate_recommendation(
        self, comparison: ComparisonResult
    ) -> tuple[TestVariant, float, str]:
        """
        Genereer aanbeveling gebaseerd op vergelijking.

        Returns:
            (recommendation, confidence, notes)
        """
        notes = []
        scores = {"modern": 0.0, "legacy": 0.0}

        # Performance comparison
        if (
            comparison.modern_performance.response_time > 0
            and comparison.legacy_performance.response_time > 0
        ):
            if (
                comparison.modern_performance.response_time
                < comparison.legacy_performance.response_time
            ):
                scores["modern"] += 2.0
                notes.append("Modern is faster")
            elif (
                comparison.legacy_performance.response_time
                < comparison.modern_performance.response_time
            ):
                scores["legacy"] += 1.0
                notes.append("Legacy is faster")

        # Success rate comparison
        if (
            comparison.modern_performance.success_rate
            > comparison.legacy_performance.success_rate
        ):
            scores["modern"] += 3.0
            notes.append("Modern has higher success rate")
        elif (
            comparison.legacy_performance.success_rate
            > comparison.modern_performance.success_rate
        ):
            scores["legacy"] += 2.0
            notes.append("Legacy has higher success rate")

        # Results count comparison
        if (
            comparison.modern_performance.results_count
            > comparison.legacy_performance.results_count
        ):
            scores["modern"] += 1.0
            notes.append("Modern provides more results")
        elif (
            comparison.legacy_performance.results_count
            > comparison.modern_performance.results_count
        ):
            scores["legacy"] += 1.0
            notes.append("Legacy provides more results")

        # Quality comparison (if available)
        if hasattr(comparison, "modern_quality") and hasattr(
            comparison, "legacy_quality"
        ):
            if (
                comparison.modern_quality.relevance_score
                > comparison.legacy_quality.relevance_score
            ):
                scores["modern"] += 2.0
                notes.append("Modern has higher relevance")
            elif (
                comparison.legacy_quality.relevance_score
                > comparison.modern_quality.relevance_score
            ):
                scores["legacy"] += 1.0
                notes.append("Legacy has higher relevance")

            if (
                comparison.modern_quality.completeness_score
                > comparison.legacy_quality.completeness_score
            ):
                scores["modern"] += 1.5
                notes.append("Modern has better completeness")
            elif (
                comparison.legacy_quality.completeness_score
                > comparison.modern_quality.completeness_score
            ):
                scores["legacy"] += 1.0
                notes.append("Legacy has better completeness")

        # Determine recommendation
        total_points = scores["modern"] + scores["legacy"]
        if total_points == 0:
            return TestVariant.BOTH, 0.5, "No clear difference found"

        modern_ratio = scores["modern"] / total_points
        legacy_ratio = scores["legacy"] / total_points

        if modern_ratio > 0.7:
            return TestVariant.MODERN, modern_ratio, "; ".join(notes)
        if legacy_ratio > 0.7:
            return TestVariant.LEGACY, legacy_ratio, "; ".join(notes)
        return TestVariant.BOTH, 0.5, f"Mixed results: {'; '.join(notes)}"

    def generate_report(self, results: list[ComparisonResult]) -> str:
        """Genereer comprehensive test report."""
        if not results:
            return "No test results available."

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("A/B TEST REPORT - WEB LOOKUP SERVICES")
        report_lines.append("=" * 80)
        report_lines.append(f"Total tests: {len(results)}")
        report_lines.append("")

        # Summary statistics
        recommendations = [r.recommendation for r in results]
        modern_count = recommendations.count(TestVariant.MODERN)
        legacy_count = recommendations.count(TestVariant.LEGACY)
        both_count = recommendations.count(TestVariant.BOTH)

        report_lines.append("RECOMMENDATIONS SUMMARY:")
        report_lines.append(
            f"  Modern preferred: {modern_count} ({modern_count/len(results)*100:.1f}%)"
        )
        report_lines.append(
            f"  Legacy preferred: {legacy_count} ({legacy_count/len(results)*100:.1f}%)"
        )
        report_lines.append(
            f"  Both equivalent: {both_count} ({both_count/len(results)*100:.1f}%)"
        )
        report_lines.append("")

        # Performance summary
        modern_times = [
            r.modern_performance.response_time
            for r in results
            if r.modern_performance.response_time > 0
        ]
        legacy_times = [
            r.legacy_performance.response_time
            for r in results
            if r.legacy_performance.response_time > 0
        ]

        if modern_times and legacy_times:
            avg_modern = sum(modern_times) / len(modern_times)
            avg_legacy = sum(legacy_times) / len(legacy_times)

            report_lines.append("PERFORMANCE SUMMARY:")
            report_lines.append(f"  Modern avg response time: {avg_modern:.2f}s")
            report_lines.append(f"  Legacy avg response time: {avg_legacy:.2f}s")
            report_lines.append(
                f"  Performance improvement: {((avg_legacy - avg_modern) / avg_legacy * 100):.1f}%"
            )
            report_lines.append("")

        # Detailed results
        report_lines.append("DETAILED RESULTS:")
        report_lines.append("-" * 80)

        for result in results:
            report_lines.append(f"Term: '{result.term}'")
            report_lines.append(
                f"  Recommendation: {result.recommendation.value} (confidence: {result.confidence:.2f})"
            )
            report_lines.append(
                f"  Modern: {result.modern_performance.results_count} results, {result.modern_performance.response_time:.2f}s"
            )
            report_lines.append(
                f"  Legacy: {result.legacy_performance.results_count} results, {result.legacy_performance.response_time:.2f}s"
            )
            report_lines.append(f"  Notes: {result.notes}")
            report_lines.append("")

        return "\n".join(report_lines)

    def get_test_history(self) -> list[ComparisonResult]:
        """Geef geschiedenis van uitgevoerde tests."""
        return self._test_history.copy()

    def clear_history(self) -> None:
        """Clear test geschiedenis."""
        self._test_history.clear()
        logger.info("A/B test history cleared")


# Convenience functions
async def quick_ab_test(terms: list[str]) -> list[ComparisonResult]:
    """
    Voer een snelle A/B test uit voor gegeven termen.

    Args:
        terms: Lijst van test termen

    Returns:
        Lijst van ComparisonResult objecten
    """
    framework = ABTestingFramework()
    return await framework.run_comparison(terms)


async def ab_test_with_report(terms: list[str]) -> str:
    """
    Voer A/B test uit en genereer direct een report.

    Args:
        terms: Lijst van test termen

    Returns:
        Formatted test report string
    """
    framework = ABTestingFramework()
    results = await framework.run_comparison(terms)
    return framework.generate_report(results)
