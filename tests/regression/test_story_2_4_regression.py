"""
Story 2.4 Regression Test Suite

Regression tests to ensure Story 2.4 interface migration doesn't break existing functionality.
These tests focus on backward compatibility and performance regression detection.

Test Categories:
1. API Endpoint Compatibility Tests
2. Service Response Format Tests
3. Performance Regression Tests
4. Business Logic Consistency Tests
5. Legacy Integration Tests
"""

import asyncio
import json
import time
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.container import ServiceContainer
from services.interfaces import (
    Definition,
    DefinitionResponseV2,
    GenerationRequest,
    ValidationResult,
)
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2


class TestStory24RegressionSuite:
    """Regression tests for Story 2.4 interface migration."""

    @pytest.fixture()
    def container(self):
        """Service container fixture."""
        return ServiceContainer()

    @pytest.fixture()
    def baseline_generation_request(self):
        """Standard generation request for consistent testing."""
        return GenerationRequest(
            id="test-id",
            begrip="automatisering",
            context="informatiesystemen",
            ontologische_categorie="proces",
            actor="regression-test",
        )

    @pytest.fixture()
    def expected_validation_result_structure(self):
        """Expected validation result structure for regression testing."""
        return {
            "version": str,
            "overall_score": float,
            "is_acceptable": bool,
            "violations": list,
            "passed_rules": list,
            "detailed_scores": dict,
            "system": dict,
        }

    # ========================================
    # REGRESSION TEST 1: API RESPONSE FORMATS
    # ========================================

    @pytest.mark.regression()
    @pytest.mark.asyncio()
    async def test_definition_response_v2_format_preserved(
        self, container, baseline_generation_request
    ):
        """Regression test: DefinitionResponseV2 format must remain consistent."""
        orchestrator = container.get_orchestrator()

        # Mock services for consistent responses
        self._setup_mocked_services(orchestrator)

        response = await orchestrator.create_definition(baseline_generation_request)

        # Verify response structure hasn't changed
        assert isinstance(response, DefinitionResponseV2)

        # Critical fields that external consumers depend on
        assert hasattr(response, "success")
        assert hasattr(response, "definition")
        assert hasattr(response, "validation_result")
        assert hasattr(response, "metadata")
        assert hasattr(response, "error")

        # Verify definition object structure
        if response.definition:
            assert hasattr(response.definition, "begrip")
            assert hasattr(response.definition, "definitie")
            assert hasattr(response.definition, "ontologische_categorie")
            assert hasattr(response.definition, "valid")
            assert hasattr(response.definition, "validation_violations")

        print("✅ DefinitionResponseV2 format regression test passed")

    @pytest.mark.regression()
    @pytest.mark.asyncio()
    async def test_validation_result_format_preserved(
        self,
        container,
        baseline_generation_request,
        expected_validation_result_structure,
    ):
        """Regression test: ValidationResult format must remain consistent."""
        orchestrator = container.get_orchestrator()
        self._setup_mocked_services(orchestrator)

        response = await orchestrator.create_definition(baseline_generation_request)

        if response.validation_result:
            validation_result = response.validation_result

            # Verify all expected fields are present with correct types
            for field, expected_type in expected_validation_result_structure.items():
                assert field in validation_result, f"Missing field: {field}"
                if validation_result[field] is not None:
                    assert isinstance(
                        validation_result[field], expected_type
                    ), f"Field {field} has wrong type: {type(validation_result[field])} != {expected_type}"

            # Critical validation fields
            assert isinstance(validation_result["overall_score"], int | float)
            assert 0.0 <= validation_result["overall_score"] <= 1.0
            assert isinstance(validation_result["is_acceptable"], bool)

        print("✅ ValidationResult format regression test passed")

    # ========================================
    # REGRESSION TEST 2: PERFORMANCE
    # ========================================

    @pytest.mark.regression()
    @pytest.mark.asyncio()
    async def test_no_performance_regression(
        self, container, baseline_generation_request
    ):
        """Regression test: Story 2.4 must not introduce significant performance degradation."""
        orchestrator = container.get_orchestrator()
        self._setup_mocked_services(orchestrator)

        # Performance baseline measurement
        execution_times = []

        # Run multiple iterations for statistical relevance
        for _ in range(5):
            start_time = time.perf_counter()

            response = await orchestrator.create_definition(baseline_generation_request)

            end_time = time.perf_counter()
            execution_time = end_time - start_time
            execution_times.append(execution_time)

            assert response.success, "Generation should succeed for performance test"

        # Calculate performance metrics
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)

        # Performance regression thresholds
        MAX_ACCEPTABLE_AVG_TIME = 0.5  # 500ms average
        MAX_ACCEPTABLE_MAX_TIME = 1.0  # 1s maximum

        assert (
            avg_time < MAX_ACCEPTABLE_AVG_TIME
        ), f"Performance regression detected: average time {avg_time:.3f}s > {MAX_ACCEPTABLE_AVG_TIME}s"
        assert (
            max_time < MAX_ACCEPTABLE_MAX_TIME
        ), f"Performance regression detected: max time {max_time:.3f}s > {MAX_ACCEPTABLE_MAX_TIME}s"

        print(
            f"✅ Performance regression test passed: avg={avg_time:.3f}s, max={max_time:.3f}s"
        )

    # ========================================
    # REGRESSION TEST 3: BUSINESS LOGIC CONSISTENCY
    # ========================================

    @pytest.mark.regression()
    @pytest.mark.asyncio()
    async def test_business_logic_consistency(
        self, container, baseline_generation_request
    ):
        """Regression test: Business logic outcomes must remain consistent."""
        orchestrator = container.get_orchestrator()

        # Setup deterministic mocking for consistent business logic testing
        self._setup_deterministic_mocks(orchestrator)

        response = await orchestrator.create_definition(baseline_generation_request)

        # Business logic assertions that should remain stable
        assert response.success is True
        assert response.definition is not None
        assert response.definition.begrip == baseline_generation_request.begrip
        assert (
            response.definition.ontologische_categorie
            == baseline_generation_request.ontologische_categorie
        )

        # Validation should have been performed
        assert response.validation_result is not None
        assert "overall_score" in response.validation_result
        assert "is_acceptable" in response.validation_result

        # Metadata should contain expected orchestrator information
        assert response.metadata is not None
        assert "orchestrator_version" in response.metadata
        assert response.metadata["orchestrator_version"] == "v2.0"

        print("✅ Business logic consistency regression test passed")

    @pytest.mark.regression()
    @pytest.mark.asyncio()
    async def test_validation_scores_consistency(self, container):
        """Regression test: Validation scoring logic must remain consistent."""
        orchestrator = container.get_orchestrator()

        # Test with known input that should produce consistent validation scores
        test_request = GenerationRequest(
            id="test-id",
            begrip="regressietest",
            context="gestandaardiseerde testcontext",
            ontologische_categorie="object",
            actor="regression-test",
        )

        # Mock with realistic validation scores
        self._setup_realistic_validation_mocks(orchestrator)

        response = await orchestrator.create_definition(test_request)

        validation_result = response.validation_result

        # Validation scoring consistency checks
        assert validation_result["overall_score"] >= 0.0
        assert validation_result["overall_score"] <= 1.0

        # Detailed scores should be consistent
        if "detailed_scores" in validation_result:
            for category, score in validation_result["detailed_scores"].items():
                assert isinstance(score, int | float)
                assert 0.0 <= score <= 1.0, f"Score {score} for {category} out of range"

        print("✅ Validation scores consistency regression test passed")

    # ========================================
    # REGRESSION TEST 4: ERROR HANDLING
    # ========================================

    @pytest.mark.regression()
    @pytest.mark.asyncio()
    async def test_error_handling_regression(
        self, container, baseline_generation_request
    ):
        """Regression test: Error handling behavior must remain consistent."""
        orchestrator = container.get_orchestrator()

        # Mock services to trigger various error conditions
        orchestrator.prompt_service.build_generation_prompt = AsyncMock(
            side_effect=Exception("Prompt service error")
        )

        response = await orchestrator.create_definition(baseline_generation_request)

        # Error response should be structured and not crash
        assert isinstance(response, DefinitionResponseV2)
        assert response.success is False
        assert response.error is not None
        assert "Prompt service error" in response.error

        # Metadata should still be populated even on error
        assert response.metadata is not None
        assert "generation_id" in response.metadata
        assert "error_type" in response.metadata

        print("✅ Error handling regression test passed")

    # ========================================
    # REGRESSION TEST 5: INTERFACE COMPATIBILITY
    # ========================================

    @pytest.mark.regression()
    def test_orchestrator_interface_compatibility(self, container):
        """Regression test: Orchestrator interface must remain compatible."""
        orchestrator = container.get_orchestrator()

        # Verify critical methods still exist
        required_methods = [
            "create_definition",
            "update_definition",
            "validate_and_save",
        ]

        for method_name in required_methods:
            assert hasattr(orchestrator, method_name), f"Missing method: {method_name}"

        # Verify orchestrator is still DefinitionOrchestratorV2
        assert isinstance(orchestrator, DefinitionOrchestratorV2)

        print("✅ Orchestrator interface compatibility regression test passed")

    @pytest.mark.regression()
    def test_validation_service_interface_change_handled(self, container):
        """Regression test: ValidationOrchestratorInterface integration properly handled."""
        orchestrator = container.get_orchestrator()

        # Verify validation service has new interface
        validation_service = orchestrator.validation_service

        # Should have ValidationOrchestratorInterface methods
        required_interface_methods = [
            "validate_text",
            "validate_definition",
            "batch_validate",
        ]

        for method_name in required_interface_methods:
            assert hasattr(
                validation_service, method_name
            ), f"ValidationOrchestratorInterface missing method: {method_name}"

        print("✅ Validation service interface change regression test passed")

    # ========================================
    # HELPER METHODS
    # ========================================

    def _setup_mocked_services(self, orchestrator):
        """Setup standard mocked services for regression testing."""
        orchestrator.prompt_service.build_generation_prompt = AsyncMock(
            return_value=Mock(
                text="Standard regression test prompt",
                token_count=100,
                components_used=["base"],
            )
        )

        orchestrator.ai_service.generate_definition = AsyncMock(
            return_value=Mock(
                text="automatisering: het gebruik van technologie om processen te automatiseren.",
                model="gpt-4",
                tokens_used=150,
            )
        )

        orchestrator.cleaning_service.clean_text = AsyncMock(
            return_value=Mock(
                cleaned_text="automatisering: het gebruik van technologie om processen te automatiseren."
            )
        )

    def _setup_deterministic_mocks(self, orchestrator):
        """Setup deterministic mocks for consistent business logic testing."""
        self._setup_mocked_services(orchestrator)

        # Override with deterministic validation result
        orchestrator.validation_service.validate_text = AsyncMock(
            return_value={
                "version": "1.0.0",
                "overall_score": 0.85,
                "is_acceptable": True,
                "violations": [],
                "passed_rules": ["VAL-EMP-001", "VAL-LEN-001", "ESS-CONT-001"],
                "detailed_scores": {
                    "taal": 0.9,
                    "juridisch": 0.8,
                    "structuur": 0.85,
                    "samenhang": 0.85,
                },
                "system": {
                    "correlation_id": "deterministic-test-id",
                    "engine_version": "2.0.0",
                    "timestamp": "2024-01-01T00:00:00Z",
                },
            }
        )

    def _setup_realistic_validation_mocks(self, orchestrator):
        """Setup realistic validation mocks for scoring consistency tests."""
        self._setup_mocked_services(orchestrator)

        orchestrator.validation_service.validate_text = AsyncMock(
            return_value={
                "version": "1.0.0",
                "overall_score": 0.75,
                "is_acceptable": True,
                "violations": [
                    {
                        "code": "STR-TERM-001",
                        "severity": "warning",
                        "message": "Terminology could be improved",
                        "rule_id": "STR-TERM-001",
                        "category": "structuur",
                    }
                ],
                "passed_rules": ["VAL-EMP-001", "VAL-LEN-001", "CON-CIRC-001"],
                "detailed_scores": {
                    "taal": 0.85,
                    "juridisch": 0.70,
                    "structuur": 0.65,
                    "samenhang": 0.80,
                },
                "system": {
                    "correlation_id": "realistic-test-id",
                    "engine_version": "2.0.0",
                    "profile_used": "standard",
                    "duration_ms": 250,
                },
            }
        )


class TestStory24RegressionEdgeCases:
    """Edge case regression tests for Story 2.4."""

    @pytest.mark.regression()
    @pytest.mark.asyncio()
    async def test_empty_text_validation_regression(self):
        """Regression test: Empty text validation should still work."""
        from services.orchestrators.validation_orchestrator_v2 import (
            ValidationOrchestratorV2,
        )

        mock_service = AsyncMock()
        mock_service.validate_definition.return_value = {
            "overall_score": 0.0,
            "is_acceptable": False,
            "violations": [{"code": "VAL-EMP-001", "message": "Empty definition"}],
            "system": {"correlation_id": "empty-test"},
        }

        orchestrator = ValidationOrchestratorV2(mock_service)

        result = await orchestrator.validate_text("begrip", "")

        assert result["is_acceptable"] is False
        assert any(v.get("code") == "VAL-EMP-001" for v in result.get("violations", []))

        print("✅ Empty text validation regression test passed")

    @pytest.mark.regression()
    @pytest.mark.asyncio()
    async def test_unicode_handling_regression(self):
        """Regression test: Unicode text handling should remain consistent."""
        from services.orchestrators.validation_orchestrator_v2 import (
            ValidationOrchestratorV2,
        )

        mock_service = AsyncMock()
        mock_service.validate_definition.return_value = {
            "overall_score": 0.8,
            "is_acceptable": True,
            "violations": [],
            "system": {"correlation_id": "unicode-test"},
        }

        orchestrator = ValidationOrchestratorV2(mock_service)

        unicode_text = "begrip: een definîtie met specìale karakters en émoji 🚀"
        result = await orchestrator.validate_text("unicode-begrip", unicode_text)

        assert result["is_acceptable"] is True

        # Verify underlying service received unicode text correctly
        call_args = mock_service.validate_definition.call_args
        assert unicode_text in call_args[1]["text"]

        print("✅ Unicode handling regression test passed")

    @pytest.mark.regression()
    @pytest.mark.asyncio()
    async def test_concurrent_validation_regression(self):
        """Regression test: Concurrent validation should still work properly."""
        from services.orchestrators.validation_orchestrator_v2 import (
            ValidationOrchestratorV2,
        )

        mock_service = AsyncMock()
        mock_service.validate_definition.return_value = {
            "overall_score": 0.8,
            "is_acceptable": True,
            "violations": [],
            "system": {"correlation_id": "concurrent-test"},
        }

        orchestrator = ValidationOrchestratorV2(mock_service)

        # Run concurrent validations
        tasks = [
            orchestrator.validate_text(f"begrip{i}", f"definitie {i}") for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 5
        assert all(result["is_acceptable"] for result in results)

        print("✅ Concurrent validation regression test passed")
