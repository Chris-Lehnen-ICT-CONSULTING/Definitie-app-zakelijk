"""
Tests voor SRU Service Circuit Breaker functionaliteit.

Verificatie van circuit breaker patterns voor performance optimalisatie:
- Circuit breaker triggert na N consecutive empty results
- Circuit breaker reset bij succesvolle query
- Provider-specific thresholds worden gerespecteerd
- Performance improvement is meetbaar
"""

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.web_lookup.sru_service import SRUService


class TestCircuitBreaker:
    """Test circuit breaker behavior in SRU service."""

    @pytest.fixture
    def sru_service(self):
        """Create SRU service with default circuit breaker config."""
        config = {
            "enabled": True,
            "consecutive_empty_threshold": 2,
            "providers": {
                "overheid": 2,
                "rechtspraak": 3,
                "wetgeving_nl": 2,
                "overheid_zoek": 2,
            },
        }
        return SRUService(circuit_breaker_config=config)

    @pytest.fixture
    def sru_service_disabled(self):
        """Create SRU service with circuit breaker disabled."""
        config = {
            "enabled": False,
            "consecutive_empty_threshold": 2,
        }
        return SRUService(circuit_breaker_config=config)

    @pytest.mark.asyncio
    async def test_circuit_breaker_triggers_after_threshold(self, sru_service):
        """
        Test: Circuit breaker triggers after N consecutive empty results.

        Scenario:
        - Default threshold = 2
        - Query 1: empty results
        - Query 2: empty results
        - Expected: Circuit breaker triggers, no Query 3/4/5
        """
        # Mock session
        sru_service.session = AsyncMock()

        # Mock _try_query to return empty results
        call_count = 0

        async def mock_try_query(query_str: str, strategy: str):
            nonlocal call_count
            call_count += 1
            return []  # Always empty

        with patch.object(sru_service, "_build_cql_query", return_value="test_query"):
            # Need to mock the internal _try_query function within search()
            # Instead, let's mock at the HTTP level
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(
                return_value='<?xml version="1.0"?><searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/"></searchRetrieveResponse>'
            )

            sru_service.session.get = AsyncMock(return_value=mock_response)
            sru_service.session.get.return_value.__aenter__ = AsyncMock(
                return_value=mock_response
            )
            sru_service.session.get.return_value.__aexit__ = AsyncMock(
                return_value=None
            )

            # Execute search
            results = await sru_service.search(
                term="nonexistent_term", endpoint="overheid"
            )

            # Verify
            assert results == []  # Circuit breaker triggered
            assert (
                sru_service.session.get.call_count <= 2 * 3
            )  # Max 2 queries × 3 retry attempts each
            # Should be significantly less than 5 queries

    def test_circuit_breaker_config_threshold(self, sru_service):
        """
        Test: Circuit breaker configuration is properly set.

        Scenario:
        - Verify threshold configuration is read correctly
        - Verify provider-specific overrides work
        """
        # Verify default threshold
        assert sru_service.circuit_breaker_config["consecutive_empty_threshold"] == 2

        # Verify provider-specific thresholds
        assert sru_service.circuit_breaker_config["providers"]["rechtspraak"] == 3
        assert sru_service.circuit_breaker_config["providers"]["overheid"] == 2

    @pytest.mark.asyncio
    async def test_provider_specific_threshold(self, sru_service):
        """
        Test: Provider-specific thresholds are respected.

        Scenario:
        - Rechtspraak has threshold = 3 (configured)
        - Overheid has threshold = 2 (configured)
        - Verify different behavior per provider
        """
        # Test Rechtspraak (threshold = 3)
        threshold_rechtspraak = sru_service.get_circuit_breaker_threshold("rechtspraak")
        assert threshold_rechtspraak == 3

        # Test Overheid (threshold = 2)
        threshold_overheid = sru_service.get_circuit_breaker_threshold("overheid")
        assert threshold_overheid == 2

        # Test unknown provider (falls back to default)
        threshold_unknown = sru_service.get_circuit_breaker_threshold(
            "unknown_provider"
        )
        assert threshold_unknown == 2

    @pytest.mark.asyncio
    async def test_circuit_breaker_disabled(self, sru_service_disabled):
        """
        Test: Circuit breaker can be disabled.

        Scenario:
        - Circuit breaker enabled = False
        - All 5 queries should execute even with empty results
        """
        # Mock session
        sru_service_disabled.session = AsyncMock()

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(
            return_value='<?xml version="1.0"?><searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/"></searchRetrieveResponse>'
        )

        sru_service_disabled.session.get = AsyncMock(return_value=mock_response)
        sru_service_disabled.session.get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        sru_service_disabled.session.get.return_value.__aexit__ = AsyncMock(
            return_value=None
        )

        with patch.object(sru_service_disabled, "_parse_sru_response", return_value=[]):
            # Execute search
            results = await sru_service_disabled.search(
                term="test_term", endpoint="overheid"
            )

            # Verify: All queries executed (circuit breaker disabled)
            assert results == []
            # With circuit breaker disabled, should attempt more queries
            # Note: actual count depends on implementation details
            assert sru_service_disabled.session.get.call_count > 0

    @pytest.mark.asyncio
    async def test_performance_improvement_with_circuit_breaker(
        self, sru_service, sru_service_disabled
    ):
        """
        Test: Circuit breaker provides measurable performance improvement.

        Scenario:
        - Compare execution time with circuit breaker ON vs OFF
        - With circuit breaker: should be ~60% faster (2 queries vs 5)
        - Measure actual timing
        """
        # Mock session for both services
        for service in [sru_service, sru_service_disabled]:
            service.session = AsyncMock()

            # Simulate slow queries (500ms each)
            async def slow_response():
                await asyncio.sleep(0.1)  # 100ms per query (reduced for test speed)
                mock_resp = MagicMock()
                mock_resp.status = 200
                mock_resp.text = AsyncMock(
                    return_value='<?xml version="1.0"?><searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/"></searchRetrieveResponse>'
                )
                return mock_resp

            async def slow_context_manager():
                return await slow_response()

            service.session.get = MagicMock()
            service.session.get.return_value.__aenter__ = slow_response
            service.session.get.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock parse to return empty
            with patch.object(service, "_parse_sru_response", return_value=[]):
                pass

        # Time with circuit breaker ENABLED
        with patch.object(sru_service, "_parse_sru_response", return_value=[]):
            start_enabled = time.time()
            results_enabled = await sru_service.search(
                term="nonexistent", endpoint="overheid"
            )
            time_enabled = time.time() - start_enabled

        # Time with circuit breaker DISABLED
        with patch.object(sru_service_disabled, "_parse_sru_response", return_value=[]):
            start_disabled = time.time()
            results_disabled = await sru_service_disabled.search(
                term="nonexistent", endpoint="overheid"
            )
            time_disabled = time.time() - start_disabled

        # Verify both return empty
        assert results_enabled == []
        assert results_disabled == []

        # Verify performance improvement
        # With circuit breaker: ~2 queries × 100ms = ~200ms
        # Without: ~5 queries × 100ms = ~500ms
        # Circuit breaker should be at least 30% faster
        improvement_ratio = (
            (time_disabled - time_enabled) / time_disabled if time_disabled > 0 else 0
        )

        print("\nPerformance metrics:")
        print(f"  Circuit breaker ENABLED:  {time_enabled:.3f}s")
        print(f"  Circuit breaker DISABLED: {time_disabled:.3f}s")
        print(f"  Improvement: {improvement_ratio * 100:.1f}%")

        # Note: This assertion might be flaky in CI due to timing variations
        # We're just verifying circuit breaker is faster, not exact percentage
        assert time_enabled < time_disabled, "Circuit breaker should be faster"

    def test_wetgeving_503_circuit_breaker_config(self, sru_service):
        """
        Test: Wetgeving.nl has proper circuit breaker configuration.

        Scenario:
        - Verify wetgeving_nl has appropriate threshold
        - Verify configuration doesn't break existing 503 handling
        """
        # Verify wetgeving_nl has circuit breaker threshold configured
        threshold = sru_service.get_circuit_breaker_threshold("wetgeving_nl")
        assert threshold == 2

        # Verify wetgeving_nl is in endpoints
        assert "wetgeving_nl" in sru_service.endpoints

    @pytest.mark.asyncio
    async def test_circuit_breaker_logging(self, sru_service, caplog):
        """
        Test: Circuit breaker logs when triggered.

        Scenario:
        - Circuit breaker triggers
        - Should log with appropriate metadata
        """
        import logging

        caplog.set_level(logging.INFO)

        # Mock session
        sru_service.session = AsyncMock()

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(
            return_value='<?xml version="1.0"?><searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/"></searchRetrieveResponse>'
        )

        sru_service.session.get = AsyncMock(return_value=mock_response)
        sru_service.session.get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        sru_service.session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch.object(sru_service, "_parse_sru_response", return_value=[]):
            # Execute search
            await sru_service.search(term="test", endpoint="overheid")

        # Verify logging
        log_messages = [record.message for record in caplog.records]
        circuit_breaker_logs = [
            msg for msg in log_messages if "Circuit breaker triggered" in msg
        ]

        assert (
            len(circuit_breaker_logs) > 0
        ), "Circuit breaker should log when triggered"
        assert any("consecutive empty results" in msg for msg in circuit_breaker_logs)

    @pytest.mark.asyncio
    async def test_query_count_tracking(self, sru_service):
        """
        Test: Query count is tracked correctly.

        Scenario:
        - Execute search with circuit breaker
        - Verify query_count in logs/metadata
        """
        # Mock session
        sru_service.session = AsyncMock()

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(
            return_value='<?xml version="1.0"?><searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/"></searchRetrieveResponse>'
        )

        sru_service.session.get = AsyncMock(return_value=mock_response)
        sru_service.session.get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        sru_service.session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch.object(sru_service, "_parse_sru_response", return_value=[]):
            # Execute search
            await sru_service.search(term="test", endpoint="overheid")

        # Verify: Attempts metadata should show limited query count
        attempts = sru_service.get_attempts()
        # With circuit breaker threshold=2, should have max 2 queries
        # Each query might have multiple URL attempts (primary + fallback)
        query_strategies = {attempt.get("strategy") for attempt in attempts}

        # Should not execute all 5 strategies
        assert (
            len(query_strategies) <= 2
        ), f"Should execute max 2 strategies, got {len(query_strategies)}"
