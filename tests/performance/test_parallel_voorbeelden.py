"""
Performance test for parallel voorbeelden generation.

Tests the performance improvement from sequential to parallel execution
of AI voorbeelden calls using asyncio.gather().

Expected results:
- Sequential execution: ~12s (6 calls × 2s each)
- Parallel execution: ~2s (max of all concurrent calls)
- Speedup: ~10s (83% improvement)
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from voorbeelden.unified_voorbeelden import (
    ExampleRequest,
    ExampleType,
    GenerationMode,
    genereer_alle_voorbeelden_async,
)


@pytest.fixture()
def mock_ai_response():
    """Mock AI response for testing."""
    return ["Voorbeeld 1", "Voorbeeld 2", "Voorbeeld 3"]


@pytest.fixture()
def test_context():
    """Test context data."""
    return {
        "organisatorisch": ["Test Organisatie"],
        "juridisch": ["Testrecht"],
        "wettelijk": ["Test Wet"],
    }


@pytest.mark.asyncio()
async def test_parallel_execution_performance(test_context):
    """Test that parallel execution is significantly faster than sequential."""

    # Simulate AI call delay (2 seconds each)
    SIMULATED_AI_DELAY = 0.5  # Using 0.5s for faster tests

    async def mock_generate_async(request: ExampleRequest):
        """Mock async generation with simulated delay."""
        await asyncio.sleep(SIMULATED_AI_DELAY)
        # Return appropriate mock data based on type
        if request.example_type == ExampleType.TOELICHTING:
            return ["Mock toelichting"]
        return ["Mock item 1", "Mock item 2", "Mock item 3"]

    # Patch the generator's _generate_resilient method
    with patch(
        "voorbeelden.unified_voorbeelden.get_examples_generator"
    ) as mock_get_generator:
        mock_generator = MagicMock()
        mock_generator._generate_resilient = mock_generate_async
        mock_get_generator.return_value = mock_generator

        # Measure parallel execution time
        start_time = time.time()
        result = await genereer_alle_voorbeelden_async(
            begrip="test begrip",
            definitie="test definitie",
            context_dict=test_context,
        )
        parallel_duration = time.time() - start_time

        # Verify results structure
        assert isinstance(result, dict)
        assert "voorbeeldzinnen" in result
        assert "praktijkvoorbeelden" in result
        assert "tegenvoorbeelden" in result
        assert "synoniemen" in result
        assert "antoniemen" in result
        assert "toelichting" in result

        # Performance assertion: parallel execution should take ~SIMULATED_AI_DELAY seconds
        # (max of concurrent calls), not 6 * SIMULATED_AI_DELAY (sequential)
        expected_parallel_time = SIMULATED_AI_DELAY * 1.5  # Allow 50% overhead
        expected_sequential_time = SIMULATED_AI_DELAY * 6 * 0.8  # 80% of sequential

        print("\n⚡ Performance Results:")
        print(f"   Parallel execution: {parallel_duration:.2f}s")
        print(f"   Expected max (parallel): {expected_parallel_time:.2f}s")
        print(f"   Would be sequential: {SIMULATED_AI_DELAY * 6:.2f}s")
        print(
            f"   Speedup: {((SIMULATED_AI_DELAY * 6) / parallel_duration):.1f}x faster"
        )

        # Assert parallel execution is significantly faster than sequential
        assert (
            parallel_duration < expected_sequential_time
        ), f"Parallel execution ({parallel_duration:.2f}s) should be faster than sequential ({expected_sequential_time:.2f}s)"

        # Assert parallel execution is close to single call time (within 50% overhead)
        assert (
            parallel_duration < expected_parallel_time
        ), f"Parallel execution ({parallel_duration:.2f}s) should be close to single call time ({expected_parallel_time:.2f}s)"


@pytest.mark.asyncio()
async def test_parallel_error_handling(test_context):
    """Test that individual call failures don't break entire batch."""

    call_count = 0

    async def mock_generate_with_errors(request: ExampleRequest):
        """Mock that fails for specific types."""
        nonlocal call_count
        call_count += 1

        # Fail on synoniemen and antoniemen
        if request.example_type in [ExampleType.SYNONIEMEN, ExampleType.ANTONIEMEN]:
            msg = f"Simulated error for {request.example_type.value}"
            raise RuntimeError(msg)

        await asyncio.sleep(0.1)
        if request.example_type == ExampleType.TOELICHTING:
            return ["Mock toelichting"]
        return ["Mock item 1", "Mock item 2"]

    with patch(
        "voorbeelden.unified_voorbeelden.get_examples_generator"
    ) as mock_get_generator:
        mock_generator = MagicMock()
        mock_generator._generate_resilient = mock_generate_with_errors
        mock_get_generator.return_value = mock_generator

        result = await genereer_alle_voorbeelden_async(
            begrip="test begrip",
            definitie="test definitie",
            context_dict=test_context,
        )

        # Verify all 6 types were attempted
        assert call_count == 6

        # Verify successful types have data
        assert len(result["voorbeeldzinnen"]) > 0
        assert len(result["praktijkvoorbeelden"]) > 0
        assert len(result["tegenvoorbeelden"]) > 0
        assert result["toelichting"] != ""

        # Verify failed types have empty defaults
        assert result["synoniemen"] == []
        assert result["antoniemen"] == []


@pytest.mark.asyncio()
async def test_real_world_timing_comparison():
    """
    Simulate real-world AI call timing to demonstrate speedup.

    This test uses realistic timing assumptions:
    - Each AI call: 2 seconds
    - Sequential: 6 × 2s = 12s
    - Parallel: max(2s) = 2s
    - Expected speedup: 10s (83% improvement)
    """

    REALISTIC_AI_DELAY = 0.2  # 0.2s for test speed (scales to 2s in production)

    async def realistic_mock_generate(request: ExampleRequest):
        """Realistic mock with variable delays."""
        # Simulate different call durations
        delays = {
            ExampleType.VOORBEELDZINNEN: REALISTIC_AI_DELAY * 0.9,
            ExampleType.PRAKTIJKVOORBEELDEN: REALISTIC_AI_DELAY * 1.1,
            ExampleType.TEGENVOORBEELDEN: REALISTIC_AI_DELAY * 1.0,
            ExampleType.SYNONIEMEN: REALISTIC_AI_DELAY * 0.8,
            ExampleType.ANTONIEMEN: REALISTIC_AI_DELAY * 0.85,
            ExampleType.TOELICHTING: REALISTIC_AI_DELAY * 0.95,
        }

        await asyncio.sleep(delays.get(request.example_type, REALISTIC_AI_DELAY))

        if request.example_type == ExampleType.TOELICHTING:
            return ["Mock toelichting voor begrip"]
        return [f"Mock {request.example_type.value} item {i}" for i in range(3)]

    with patch(
        "voorbeelden.unified_voorbeelden.get_examples_generator"
    ) as mock_get_generator:
        mock_generator = MagicMock()
        mock_generator._generate_resilient = realistic_mock_generate
        mock_get_generator.return_value = mock_generator

        # Time parallel execution
        start = time.time()
        result = await genereer_alle_voorbeelden_async(
            begrip="identiteitsbehandeling",
            definitie="Het proces waarbij identiteit wordt vastgesteld en geverifieerd",
            context_dict={
                "organisatorisch": ["Strafrechtketen"],
                "juridisch": ["Strafrecht"],
                "wettelijk": ["Wetboek van Strafrecht"],
            },
        )
        parallel_time = time.time() - start

        # Calculate theoretical sequential time
        sequential_time = REALISTIC_AI_DELAY * 6

        # Calculate speedup
        speedup = sequential_time / parallel_time
        time_saved = sequential_time - parallel_time
        improvement_pct = (time_saved / sequential_time) * 100

        print("\n🚀 Real-World Performance Simulation:")
        print(f"   Parallel execution: {parallel_time:.3f}s")
        print(f"   Sequential would be: {sequential_time:.3f}s")
        print(f"   Speedup: {speedup:.1f}x")
        print(f"   Time saved: {time_saved:.3f}s")
        print(f"   Improvement: {improvement_pct:.0f}%")

        # Scale to production (10x)
        prod_parallel = parallel_time * 10
        prod_sequential = sequential_time * 10
        prod_saved = prod_sequential - prod_parallel

        print("\n📊 Scaled to Production (10x):")
        print(f"   Parallel: ~{prod_parallel:.1f}s")
        print(f"   Sequential: ~{prod_sequential:.1f}s")
        print(f"   Saved: ~{prod_saved:.1f}s per generation")

        # Assertions
        assert speedup > 4.0, f"Expected >4x speedup, got {speedup:.1f}x"
        assert (
            improvement_pct > 75
        ), f"Expected >75% improvement, got {improvement_pct:.0f}%"

        # Verify all types generated
        assert all(
            key in result
            for key in [
                "voorbeeldzinnen",
                "praktijkvoorbeelden",
                "tegenvoorbeelden",
                "synoniemen",
                "antoniemen",
                "toelichting",
            ]
        )


if __name__ == "__main__":
    # Run tests directly for quick verification
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
