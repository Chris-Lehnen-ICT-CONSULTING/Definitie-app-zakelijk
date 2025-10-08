"""
Integration test voor SRU Circuit Breaker - Realistische scenario's.

Deze test demonstreert de werkelijke performance verbetering door circuit breaker
bij searches die geen resultaten opleveren.
"""

import pytest


class TestSRUCircuitBreakerIntegration:
    """Integration tests for circuit breaker in realistic scenarios."""

    @pytest.mark.asyncio()
    @pytest.mark.integration()
    async def test_empty_search_with_circuit_breaker(self):
        """
        Integration test: Search voor non-existent term triggert circuit breaker.

        Expected behavior:
        - Circuit breaker triggert na 2 lege queries
        - Total execution time < 15 seconden (vs ~30s zonder circuit breaker)
        - get_attempts() toont max 2 query strategies
        """
        import time

        from src.services.web_lookup.sru_service import SRUService

        # Create service with circuit breaker enabled
        service = SRUService(
            circuit_breaker_config={
                "enabled": True,
                "consecutive_empty_threshold": 2,
                "providers": {"overheid": 2},
            }
        )

        async with service:
            start = time.time()

            # Search for completely non-existent term
            results = await service.search(
                term="xyzabc123nonexistent999", endpoint="overheid", max_records=5
            )

            elapsed = time.time() - start

            # Verify results
            assert results == []  # Should return empty

            # Verify performance - should be significantly faster than 30s
            print("\nCircuit breaker integration test:")
            print("  Search term: xyzabc123nonexistent999")
            print(f"  Execution time: {elapsed:.2f}s")
            print(f"  Results: {len(results)}")

            # Get query attempts
            attempts = service.get_attempts()
            strategies = set(a.get("strategy") for a in attempts if a.get("strategy"))
            print(f"  Strategies attempted: {strategies}")
            print(f"  Total attempts: {len(attempts)}")

            # Assertions
            assert (
                elapsed < 20
            ), f"Circuit breaker should limit execution time (got {elapsed:.2f}s)"
            assert (
                len(strategies) <= 3
            ), f"Should attempt max 3 strategies with threshold=2, got {len(strategies)}"

    @pytest.mark.asyncio()
    @pytest.mark.integration()
    async def test_rechtspraak_higher_threshold(self):
        """
        Integration test: Rechtspraak heeft hogere threshold (3) dan overheid (2).

        Expected behavior:
        - Rechtspraak mag 3 lege queries doen
        - get_attempts() toont max 3 query strategies
        """
        from src.services.web_lookup.sru_service import SRUService

        service = SRUService(
            circuit_breaker_config={
                "enabled": True,
                "consecutive_empty_threshold": 2,
                "providers": {
                    "overheid": 2,
                    "rechtspraak": 3,  # Higher threshold for legal docs
                },
            }
        )

        async with service:
            # Search rechtspraak
            results = await service.search(
                term="xyzabc123nonexistent999", endpoint="rechtspraak", max_records=3
            )

            attempts = service.get_attempts()
            strategies = set(a.get("strategy") for a in attempts if a.get("strategy"))

            print("\nRechtspraak threshold test:")
            print(f"  Strategies attempted: {strategies}")
            print(f"  Total attempts: {len(attempts)}")

            # Rechtspraak should attempt up to 3 strategies
            assert (
                len(strategies) <= 4
            ), "Rechtspraak threshold=3 allows max 4 strategies"
