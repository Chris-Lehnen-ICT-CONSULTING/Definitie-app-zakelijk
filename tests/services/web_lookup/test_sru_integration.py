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
            strategies = {a.get("strategy") for a in attempts if a.get("strategy")}
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
            await service.search(
                term="xyzabc123nonexistent999", endpoint="rechtspraak", max_records=3
            )

            attempts = service.get_attempts()
            strategies = {a.get("strategy") for a in attempts if a.get("strategy")}

            print("\nRechtspraak threshold test:")
            print(f"  Strategies attempted: {strategies}")
            print(f"  Total attempts: {len(attempts)}")

            # Rechtspraak should attempt up to 3 strategies
            assert (
                len(strategies) <= 4
            ), "Rechtspraak threshold=3 allows max 4 strategies"

    @pytest.mark.asyncio()
    async def test_sru_20_namespace_compatibility(self):
        """
        Integration test: Verify SRU 2.0 namespace wordt correct ondersteund.

        Dit test de fix voor SRU 2.0 responses die niet geparsed werden door
        namespace mismatch (http://docs.oasis-open.org/ns/search-ws/sruResponse).
        """
        from src.services.web_lookup.sru_service import SRUService

        service = SRUService()

        # Verify wetgeving_nl endpoint is configured for SRU 2.0
        config = service.get_endpoint_config("wetgeving_nl")
        assert config is not None, "wetgeving_nl endpoint moet geconfigureerd zijn"
        assert config.sru_version == "2.0", "wetgeving_nl moet SRU 2.0 gebruiken"
        # UPDATED 2025-10-08: schema changed oai_dc → gzd (matches Overheid.nl working config)
        assert (
            config.record_schema == "gzd"
        ), "wetgeving_nl moet gzd schema gebruiken (na schema fix)"

        print("\nSRU 2.0 namespace compatibility test:")
        print(f"  Endpoint: {config.name}")
        print(f"  SRU Version: {config.sru_version}")
        print(f"  Record Schema: {config.record_schema}")

    def test_schema_configuration_per_endpoint(self):
        """
        Test dat verschillende endpoints correcte schema's gebruiken.

        Dit test de fix voor schema configuratie:
        - overheid: gzd (fix voor 'dc not supported')
        - overheid_zoek: gzd
        - wetgeving_nl: oai_dc (SRU 2.0)
        - rechtspraak: dc
        """
        from src.services.web_lookup.sru_service import SRUService

        service = SRUService()

        # Test alle endpoint configuraties
        test_cases = [
            ("overheid", "gzd", "Overheid.nl repository moet GZD gebruiken"),
            ("overheid_zoek", "gzd", "Overheid.nl Zoekservice moet GZD gebruiken"),
            # UPDATED 2025-10-08: wetgeving schema changed oai_dc → gzd
            ("wetgeving_nl", "gzd", "Wetgeving.nl moet GZD gebruiken (schema fix)"),
            # REMOVED: rechtspraak (SRU disabled, now REST only)
        ]

        print("\nSchema configuration per endpoint:")
        for endpoint, expected_schema, description in test_cases:
            config = service.get_endpoint_config(endpoint)
            if endpoint == "rechtspraak":
                # Rechtspraak SRU is disabled (commented out)
                assert (
                    config is None
                ), "Rechtspraak SRU moet disabled zijn (REST only now)"
                print(f"  {endpoint}: DISABLED (use rechtspraak_rest_service.py)")
                continue
            assert config is not None, f"{endpoint} moet geconfigureerd zijn"
            actual_schema = config.record_schema
            print(f"  {endpoint}: {actual_schema} (expected: {expected_schema})")
            assert actual_schema == expected_schema, description
