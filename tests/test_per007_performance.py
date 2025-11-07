"""
PER-007 Performance Benchmark Tests
These tests run after GREEN phase to ensure performance requirements are met.
"""

import time

import pytest

from services.definition_generator_context import EnrichedContext, HybridContextManager
from services.interfaces import GenerationRequest
from services.prompts.prompt_service_v2 import PromptServiceV2


class TestPerformance:
    """Performance benchmarks - run after GREEN phase implementation"""

    @pytest.mark.benchmark()
    @pytest.mark.performance()
    def test_context_processing_under_100ms(self):
        """Context processing must complete in < 100ms"""
        # GIVEN: Complex request with all context types
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["OM", "DJI", "Rechtspraak", "CJIB", "KMAR"],
            juridische_context=["Strafrecht", "Bestuursrecht", "Civiel recht"],
            wettelijke_basis=["Art. 27 Sv", "Art. 67 Sv", "AWB", "BW", "WvSr"],
        )

        manager = HybridContextManager()

        # WHEN: Processing context multiple times
        times = []
        iterations = 100

        for _ in range(iterations):
            start = time.perf_counter()
            result = manager._build_base_context(request)
            end = time.perf_counter()
            times.append(end - start)

        # THEN: Average time should be under 100ms
        avg_time = sum(times) / len(times) * 1000  # Convert to ms
        max_time = max(times) * 1000

        assert avg_time < 100, f"Average time {avg_time:.2f}ms exceeds 100ms limit"
        assert max_time < 200, f"Max time {max_time:.2f}ms exceeds 200ms limit"

        # Verify correctness
        assert len(result["organisatorisch"]) == 5
        assert len(result["juridisch"]) == 3
        assert len(result["wettelijk"]) == 5

    @pytest.mark.benchmark()
    @pytest.mark.performance()
    def test_deduplication_performance(self):
        """Deduplication must be efficient even with large lists"""
        # GIVEN: Large list with many duplicates
        base_orgs = ["OM", "DJI", "Rechtspraak", "CJIB"]
        large_list = base_orgs * 50  # 200 items with lots of duplicates

        request = GenerationRequest(begrip="test", organisatorische_context=large_list)

        manager = HybridContextManager()

        # WHEN: Processing with deduplication
        times = []
        for _ in range(50):
            start = time.perf_counter()
            result = manager._build_base_context(request)
            end = time.perf_counter()
            times.append(end - start)

        # THEN: Fast and correct
        avg_time = sum(times) / len(times) * 1000  # ms
        assert avg_time < 50, f"Deduplication took {avg_time:.2f}ms, exceeds 50ms limit"

        # Verify deduplication worked and preserved order
        assert (
            result["organisatorisch"] == base_orgs
        ), f"Deduplication failed. Got {result['organisatorisch']}"

    @pytest.mark.benchmark()
    @pytest.mark.performance()
    def test_ui_formatting_performance(self):
        """UI preview generation must be fast"""
        # GIVEN: Complex context
        context = EnrichedContext(
            base_context={
                "organisatorisch": ["OM", "DJI", "Rechtspraak", "CJIB", "KMAR"],
                "juridisch": ["Strafrecht", "Bestuursrecht", "Civiel recht"],
                "wettelijk": ["Art. 27 Sv", "Art. 67 Sv", "AWB", "BW", "WvSr"],
                "domein": ["Justice", "Security"],
                "technisch": [],
                "historisch": [],
            },
            sources=[],
            expanded_terms={
                "OM": "Openbaar Ministerie",
                "DJI": "Dienst Justitiële Inrichtingen",
            },
            confidence_scores={"organisatorisch": 1.0, "juridisch": 0.95},
            metadata={"timestamp": "2025-09-04"},
        )

        # Assuming ContextFormatter will be implemented
        try:
            from services.ui.formatters import ContextFormatter

            formatter = ContextFormatter()
        except ImportError:
            pytest.skip("ContextFormatter not yet implemented")

        # WHEN: Formatting for UI many times
        times = []
        for _ in range(1000):
            start = time.perf_counter()
            result = formatter.format_ui_preview(context)
            end = time.perf_counter()
            times.append(end - start)

        # THEN: Very fast formatting
        avg_time = sum(times) / len(times) * 1000  # ms
        assert avg_time < 1, f"UI formatting took {avg_time:.2f}ms, exceeds 1ms limit"

        # Verify format
        assert "📋 Org:" in result or "Org:" in result
        assert "⚖️ Juridisch:" in result or "Juridisch:" in result

    @pytest.mark.benchmark()
    @pytest.mark.performance()
    def test_astra_validation_performance(self):
        """ASTRA validation must be fast"""
        # GIVEN: Mix of valid, invalid, and custom organizations
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=[
                "OM",
                "DJI",
                "InvalidOrg",
                "CustomOrg",
                "Rechtspraak",
                "FakeOrg",
                "CJIB",
                "KMAR",
                "AnotherCustom",
                "NP",
            ],
        )

        manager = HybridContextManager()

        # WHEN: Processing with validation
        times = []
        for _ in range(100):
            start = time.perf_counter()
            # Validation happens during processing
            manager._build_base_context(request)
            end = time.perf_counter()
            times.append(end - start)

        # THEN: Validation adds minimal overhead
        avg_time = sum(times) / len(times) * 1000  # ms
        assert (
            avg_time < 10
        ), f"ASTRA validation took {avg_time:.2f}ms, exceeds 10ms limit"

    @pytest.mark.benchmark()
    @pytest.mark.performance()
    def test_end_to_end_flow_performance(self):
        """Complete context flow must be under 200ms"""
        # GIVEN: Full request
        request = GenerationRequest(
            begrip="verdachte",
            organisatorische_context=["OM", "DJI", "Anders...", "CustomOrg"],
            juridische_context=["Strafrecht", "Anders...", "CustomJur"],
            wettelijke_basis=["Art. 27 Sv", "Art. 67 Sv", "Anders...", "CustomWet"],
        )

        # WHEN: Complete flow
        times = []
        for _ in range(50):
            start = time.perf_counter()

            # Step 1: Process context
            manager = HybridContextManager()
            base_context = manager._build_base_context(request)

            # Step 2: Create enriched context
            enriched = EnrichedContext(
                base_context=base_context,
                sources=[],
                expanded_terms={},
                confidence_scores={},
                metadata={},
            )

            # Step 3: Format for UI (if formatter exists)
            try:
                from services.ui.formatters import ContextFormatter

                formatter = ContextFormatter()
                formatter.format_ui_preview(enriched)
            except ImportError:
                pass

            # Step 4: Format for prompt
            prompt_service = PromptServiceV2()
            prompt_service._convert_request_to_context(request)

            end = time.perf_counter()
            times.append(end - start)

        # THEN: Total time under 200ms
        avg_time = sum(times) / len(times) * 1000  # ms
        max_time = max(times) * 1000

        assert avg_time < 200, f"E2E flow took {avg_time:.2f}ms average, exceeds 200ms"
        assert max_time < 400, f"E2E flow took {max_time:.2f}ms max, exceeds 400ms"

    @pytest.mark.benchmark()
    @pytest.mark.performance()
    def test_anders_processing_overhead(self):
        """Anders option processing should add minimal overhead"""
        # GIVEN: Request without Anders
        request_normal = GenerationRequest(
            begrip="test", organisatorische_context=["OM", "DJI", "Rechtspraak"]
        )

        # Request with Anders
        request_anders = GenerationRequest(
            begrip="test",
            organisatorische_context=[
                "OM",
                "Anders...",
                "CustomOrg",
                "DJI",
                "Anders...",
                "Custom2",
            ],
        )

        manager = HybridContextManager()

        # WHEN: Comparing processing times
        times_normal = []
        times_anders = []

        for _ in range(100):
            # Normal processing
            start = time.perf_counter()
            manager._build_base_context(request_normal)
            end = time.perf_counter()
            times_normal.append(end - start)

            # Anders processing
            start = time.perf_counter()
            manager._build_base_context(request_anders)
            end = time.perf_counter()
            times_anders.append(end - start)

        # THEN: Anders adds less than 20% overhead
        avg_normal = sum(times_normal) / len(times_normal)
        avg_anders = sum(times_anders) / len(times_anders)
        overhead_percent = ((avg_anders - avg_normal) / avg_normal) * 100

        assert (
            overhead_percent < 20
        ), f"Anders processing adds {overhead_percent:.1f}% overhead, exceeds 20% limit"

    @pytest.mark.benchmark()
    @pytest.mark.performance()
    def test_memory_efficiency(self):
        """Context processing should be memory efficient"""
        import tracemalloc

        # GIVEN: Large number of context operations
        request = GenerationRequest(
            begrip="test",
            organisatorische_context=["OM", "DJI", "Rechtspraak"] * 10,
            juridische_context=["Strafrecht", "Bestuursrecht"] * 10,
            wettelijke_basis=["Art. 27 Sv", "AWB"] * 10,
        )

        manager = HybridContextManager()

        # WHEN: Processing many times
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        for _ in range(1000):
            result = manager._build_base_context(request)
            # Result should be garbage collected
            del result

        snapshot2 = tracemalloc.take_snapshot()
        tracemalloc.stop()

        # THEN: Memory usage should be reasonable
        stats = snapshot2.compare_to(snapshot1, "lineno")
        total_memory = sum(stat.size_diff for stat in stats)
        memory_mb = total_memory / 1024 / 1024

        assert memory_mb < 10, f"Memory usage {memory_mb:.2f}MB exceeds 10MB limit"

    @pytest.mark.benchmark()
    @pytest.mark.performance()
    def test_concurrent_processing_performance(self):
        """Context processing should handle concurrent requests efficiently"""
        import concurrent.futures
        import threading

        # GIVEN: Multiple concurrent requests
        requests = [
            GenerationRequest(
                begrip=f"test_{i}",
                organisatorische_context=["OM", "DJI", f"Org{i}"],
                juridische_context=["Strafrecht", f"Domain{i}"],
                wettelijke_basis=["Art. 27 Sv", f"Law{i}"],
            )
            for i in range(10)
        ]

        manager = HybridContextManager()

        # WHEN: Processing concurrently
        def process_request(req):
            start = time.perf_counter()
            result = manager._build_base_context(req)
            end = time.perf_counter()
            return end - start, result

        start_time = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_request, req) for req in requests]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        total_time = time.perf_counter() - start_time

        # THEN: Concurrent processing should be efficient
        individual_times = [r[0] for r in results]
        avg_individual = sum(individual_times) / len(individual_times) * 1000
        total_time_ms = total_time * 1000

        # Total time should be less than sum of individual times (parallelism benefit)
        sequential_estimate = sum(individual_times) * 1000
        assert (
            total_time_ms < sequential_estimate * 0.5
        ), f"Concurrent processing too slow: {total_time_ms:.2f}ms"

        # Each request should still be fast
        assert (
            avg_individual < 50
        ), f"Individual processing too slow: {avg_individual:.2f}ms average"
