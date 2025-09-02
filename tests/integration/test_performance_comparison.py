"""
Performance vergelijking tussen legacy en nieuwe services.

Deze tests meten en vergelijken de performance karakteristieken
om te verifiëren dat de nieuwe architectuur geen significante
performance regressie introduceert.
"""
import pytest
import asyncio
import time
import statistics
from unittest.mock import patch, Mock
from typing import List, Tuple
import memory_profiler
import cProfile
import pstats
import io

from services.unified_definition_service_v2 import UnifiedDefinitionService
from services.service_factory import get_definition_service


class TestPerformanceComparison:
    """Performance vergelijking test suite."""

    @pytest.fixture
    def mock_fast_gpt(self):
        """Mock GPT met snelle response."""
        return "Een snelle test definitie voor performance metingen."

    @pytest.fixture
    def standard_context(self):
        """Standard test context."""
        return {
            'organisatorisch': ['Test Org'],
            'domein': ['Test Domain']
        }

    async def measure_execution_time(
        self,
        service,
        begrip: str,
        context: dict,
        iterations: int = 10
    ) -> Tuple[float, float, List[float]]:
        """
        Meet execution tijd over meerdere iteraties.

        Returns:
            Tuple van (gemiddelde, std deviatie, alle metingen)
        """
        times = []

        with patch('prompt_builder.stuur_prompt_naar_gpt', return_value="Test def"):
            for i in range(iterations):
                start = time.perf_counter()
                result = await service.generate_definition(
                    begrip=f"{begrip}_{i}",
                    context_dict=context
                )
                end = time.perf_counter()

                if result['success']:
                    times.append(end - start)

        avg_time = statistics.mean(times) if times else 0
        std_dev = statistics.stdev(times) if len(times) > 1 else 0

        return avg_time, std_dev, times

    @pytest.mark.asyncio
    async def test_basic_performance_comparison(self, standard_context):
        """Basis performance vergelijking tussen services."""
        # Legacy service
        legacy_service = UnifiedDefinitionService.get_instance()
        legacy_avg, legacy_std, legacy_times = await self.measure_execution_time(
            legacy_service, "legacy_test", standard_context
        )

        # New service
        with patch.dict('os.environ', {'USE_NEW_SERVICES': 'true'}):
            new_service = get_definition_service()
            new_avg, new_std, new_times = await self.measure_execution_time(
                new_service, "new_test", standard_context
            )

        # Report resultaten
        print(f"\n=== Performance Comparison ===")
        print(f"Legacy Service:")
        print(f"  Average: {legacy_avg*1000:.2f}ms")
        print(f"  Std Dev: {legacy_std*1000:.2f}ms")
        print(f"  Min/Max: {min(legacy_times)*1000:.2f}ms / {max(legacy_times)*1000:.2f}ms")

        print(f"\nNew Service:")
        print(f"  Average: {new_avg*1000:.2f}ms")
        print(f"  Std Dev: {new_std*1000:.2f}ms")
        print(f"  Min/Max: {min(new_times)*1000:.2f}ms / {max(new_times)*1000:.2f}ms")

        print(f"\nPerformance difference: {((new_avg/legacy_avg)-1)*100:.1f}%")

        # Assert nieuwe service niet meer dan 20% langzamer
        assert new_avg < legacy_avg * 1.2, f"New service is {((new_avg/legacy_avg)-1)*100:.1f}% slower"

    @pytest.mark.asyncio
    async def test_concurrent_performance(self):
        """Test performance onder concurrent load."""
        async def run_concurrent_requests(service, count: int):
            """Run meerdere concurrent requests."""
            start = time.perf_counter()

            tasks = []
            with patch('prompt_builder.stuur_prompt_naar_gpt', return_value="Test def"):
                for i in range(count):
                    task = service.generate_definition(
                        begrip=f"concurrent_test_{i}",
                        context_dict={'domein': ['Test']}
                    )
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

            end = time.perf_counter()

            success_count = sum(1 for r in results
                              if isinstance(r, dict) and r.get('success'))

            return end - start, success_count

        # Test met verschillende concurrent loads
        loads = [5, 10, 20]

        print("\n=== Concurrent Performance Test ===")

        for load in loads:
            # Legacy
            legacy_service = UnifiedDefinitionService.get_instance()
            legacy_time, legacy_success = await run_concurrent_requests(legacy_service, load)

            # New
            with patch.dict('os.environ', {'USE_NEW_SERVICES': 'true'}):
                new_service = get_definition_service()
                new_time, new_success = await run_concurrent_requests(new_service, load)

            print(f"\nLoad: {load} concurrent requests")
            print(f"Legacy: {legacy_time:.3f}s ({legacy_success}/{load} success)")
            print(f"New:    {new_time:.3f}s ({new_success}/{load} success)")
            print(f"Difference: {((new_time/legacy_time)-1)*100:.1f}%")

            # Verify nieuwe service schaalt vergelijkbaar
            assert new_time < legacy_time * 1.5, f"New service doesn't scale well at {load} concurrent"

    @pytest.mark.asyncio
    async def test_memory_usage_comparison(self):
        """Vergelijk memory usage tussen services."""
        import tracemalloc

        async def measure_memory_usage(service, iterations=5):
            """Meet memory usage over meerdere iterations."""
            tracemalloc.start()

            # Baseline
            baseline = tracemalloc.take_snapshot()

            # Run iterations
            with patch('prompt_builder.stuur_prompt_naar_gpt', return_value="Test def"):
                for i in range(iterations):
                    await service.generate_definition(
                        begrip=f"memory_test_{i}",
                        context_dict={'domein': ['Test']}
                    )

            # Measure
            current = tracemalloc.take_snapshot()
            stats = current.compare_to(baseline, 'lineno')

            total_memory = sum(stat.size_diff for stat in stats)
            tracemalloc.stop()

            return total_memory

        # Legacy memory usage
        legacy_service = UnifiedDefinitionService.get_instance()
        legacy_memory = await measure_memory_usage(legacy_service)

        # New service memory usage
        with patch.dict('os.environ', {'USE_NEW_SERVICES': 'true'}):
            new_service = get_definition_service()
            new_memory = await measure_memory_usage(new_service)

        print(f"\n=== Memory Usage Comparison ===")
        print(f"Legacy Service: {legacy_memory/1024:.2f} KB")
        print(f"New Service:    {new_memory/1024:.2f} KB")
        print(f"Difference:     {(new_memory-legacy_memory)/1024:.2f} KB")

        # New service mag niet meer dan 50% meer memory gebruiken
        # (dependency injection heeft overhead)
        assert new_memory < legacy_memory * 1.5, "New service uses too much memory"

    @pytest.mark.asyncio
    async def test_startup_performance(self):
        """Test startup/initialization performance."""
        import importlib

        # Legacy service startup
        legacy_start = time.perf_counter()
        # Force nieuwe import
        if 'services.unified_definition_service_v2' in sys.modules:
            importlib.reload(sys.modules['services.unified_definition_service_v2'])
        legacy_service = UnifiedDefinitionService.get_instance()
        legacy_end = time.perf_counter()
        legacy_startup = legacy_end - legacy_start

        # New service startup
        new_start = time.perf_counter()
        with patch.dict('os.environ', {'USE_NEW_SERVICES': 'true'}):
            # Force nieuwe import
            if 'services.service_factory' in sys.modules:
                importlib.reload(sys.modules['services.service_factory'])
            new_service = get_definition_service()
        new_end = time.perf_counter()
        new_startup = new_end - new_start

        print(f"\n=== Startup Performance ===")
        print(f"Legacy Service: {legacy_startup*1000:.2f}ms")
        print(f"New Service:    {new_startup*1000:.2f}ms")
        print(f"Difference:     {(new_startup-legacy_startup)*1000:.2f}ms")

        # Startup mag niet te veel langzamer zijn
        assert new_startup < legacy_startup + 0.1, "New service startup too slow"

    @pytest.mark.asyncio
    async def test_cache_effectiveness(self):
        """Test cache effectiveness in beide implementaties."""
        # Zelfde begrip meerdere keren voor cache test
        begrip = "cache_test_begrip"
        context = {'domein': ['Test']}

        async def test_cache(service, name):
            times = []

            with patch('prompt_builder.stuur_prompt_naar_gpt', return_value="Cached def") as mock_gpt:
                # Eerste call - geen cache
                start = time.perf_counter()
                result1 = await service.generate_definition(begrip, context)
                end = time.perf_counter()
                times.append(end - start)

                # Reset mock count
                initial_calls = mock_gpt.call_count

                # Tweede call - mogelijk gecached
                start = time.perf_counter()
                result2 = await service.generate_definition(begrip, context)
                end = time.perf_counter()
                times.append(end - start)

                # Check of cache gebruikt werd
                cached = mock_gpt.call_count == initial_calls

                return times, cached

        # Test legacy
        legacy_service = UnifiedDefinitionService.get_instance()
        legacy_times, legacy_cached = await test_cache(legacy_service, "Legacy")

        # Test new
        with patch.dict('os.environ', {'USE_NEW_SERVICES': 'true'}):
            new_service = get_definition_service()
            new_times, new_cached = await test_cache(new_service, "New")

        print(f"\n=== Cache Effectiveness ===")
        print(f"Legacy - First: {legacy_times[0]*1000:.2f}ms, Second: {legacy_times[1]*1000:.2f}ms")
        print(f"  Cached: {legacy_cached}")
        print(f"New - First: {new_times[0]*1000:.2f}ms, Second: {new_times[1]*1000:.2f}ms")
        print(f"  Cached: {new_cached}")

        # Als legacy caching heeft, moet new ook caching hebben
        if legacy_cached:
            assert new_cached or new_times[1] < new_times[0] * 0.5, "New service cache not effective"

    @pytest.mark.asyncio
    async def test_error_handling_performance(self):
        """Test performance impact van error handling."""
        async def measure_error_handling(service):
            """Meet tijd voor error scenarios."""
            error_times = []
            success_times = []

            # Success case
            with patch('prompt_builder.stuur_prompt_naar_gpt', return_value="Success"):
                start = time.perf_counter()
                result = await service.generate_definition("test", {})
                end = time.perf_counter()
                if result['success']:
                    success_times.append(end - start)

            # Error cases
            with patch('prompt_builder.stuur_prompt_naar_gpt', side_effect=Exception("Test error")):
                for i in range(5):
                    start = time.perf_counter()
                    result = await service.generate_definition(f"error_test_{i}", {})
                    end = time.perf_counter()
                    error_times.append(end - start)

            return statistics.mean(success_times), statistics.mean(error_times)

        # Legacy
        legacy_service = UnifiedDefinitionService.get_instance()
        legacy_success, legacy_error = await measure_error_handling(legacy_service)

        # New
        with patch.dict('os.environ', {'USE_NEW_SERVICES': 'true'}):
            new_service = get_definition_service()
            new_success, new_error = await measure_error_handling(new_service)

        print(f"\n=== Error Handling Performance ===")
        print(f"Legacy - Success: {legacy_success*1000:.2f}ms, Error: {legacy_error*1000:.2f}ms")
        print(f"New - Success: {new_success*1000:.2f}ms, Error: {new_error*1000:.2f}ms")

        # Error handling mag niet veel trager zijn dan success
        assert new_error < new_success * 2, "Error handling too slow in new service"


class TestResourceUsage:
    """Test resource usage en cleanup."""

    @pytest.mark.asyncio
    async def test_connection_cleanup(self):
        """Test dat connections proper opgeruimd worden."""
        import gc

        # Track open connections/resources
        initial_objects = len(gc.get_objects())

        # Create en gebruik services
        for i in range(10):
            if i % 2 == 0:
                service = UnifiedDefinitionService.get_instance()
            else:
                with patch.dict('os.environ', {'USE_NEW_SERVICES': 'true'}):
                    service = get_definition_service()

            with patch('prompt_builder.stuur_prompt_naar_gpt', return_value="Test"):
                await service.generate_definition(f"cleanup_test_{i}", {})

        # Force garbage collection
        gc.collect()

        # Check object count
        final_objects = len(gc.get_objects())

        print(f"\n=== Resource Cleanup Test ===")
        print(f"Initial objects: {initial_objects}")
        print(f"Final objects: {final_objects}")
        print(f"Difference: {final_objects - initial_objects}")

        # Mag niet te veel objects lekken
        assert final_objects - initial_objects < 1000, "Possible memory leak detected"


if __name__ == "__main__":
    # Run met verbose output voor performance details
    pytest.main([__file__, "-v", "-s", "-k", "performance"])
