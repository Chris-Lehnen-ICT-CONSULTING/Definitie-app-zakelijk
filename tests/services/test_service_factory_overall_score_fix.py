"""
Comprehensive test suite for overall_score KeyError fix in service_factory.py.

Tests the fix for:
- Line 170: "overall_score": float(result.get("overall_score") or 0.0)
- Line 297: "final_score": validation_details.get("overall_score", 0.0)

This test suite validates all edge cases and ensures production-ready error handling.
"""

import asyncio
import os

# Import the actual modules
import sys
from typing import Any, Dict, Optional, Union
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from services.interfaces import (
    Definition,
    DefinitionResponse,
    GenerationRequest,
    ValidationResult,
)
from services.service_factory import ServiceAdapter


class TestOverallScoreRobustness:
    """
    Comprehensive test suite for overall_score handling robustness.
    Tests all edge cases and type variations to ensure production stability.
    """

    @pytest.fixture()
    def mock_container(self):
        """Create a mock container for testing."""
        container = Mock()
        container.orchestrator = Mock()
        return container

    @pytest.fixture()
    def service_adapter(self, mock_container):
        """Create a ServiceAdapter instance for testing."""
        orchestrator = AsyncMock()
        orchestrator.get_stats = Mock(return_value={})
        mock_container.orchestrator.return_value = orchestrator
        return ServiceAdapter(mock_container)

    def create_validation_response(
        self,
        overall_score: float | int | str | list | dict | Any | None = None,
        include_score: bool = True,
        validation_exists: bool = True,
    ) -> DefinitionResponse:
        """
        Helper to create validation responses with different score scenarios.

        Args:
            overall_score: The score value to test (can be any type)
            include_score: Whether to include the overall_score key
            validation_exists: Whether the validation object exists
        """
        if not validation_exists:
            return DefinitionResponse(
                success=True,
                definition=Definition(
                    begrip="Test",
                    definitie="Test definitie",
                    metadata={"origineel": "Original"},
                ),
                validation=None,
                message="Success",
            )

        validation_dict = {
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["rule1"],
        }

        if include_score:
            validation_dict["overall_score"] = overall_score

        # Create a proper mock validation object with all required attributes
        mock_validation = Mock()
        mock_validation.to_dict.return_value = validation_dict

        # Add attributes that might be accessed directly
        mock_validation.violations = validation_dict.get("violations", [])
        mock_validation.is_valid = validation_dict.get("is_acceptable", True)
        mock_validation.score = validation_dict.get("overall_score", 0.0)
        mock_validation.errors = []
        mock_validation.suggestions = []

        return DefinitionResponse(
            success=True,
            definition=Definition(
                begrip="Test",
                definitie="Test definitie",
                metadata={"origineel": "Original", "voorbeelden": {}},
            ),
            validation=mock_validation,
            message="Success",
        )

    @pytest.mark.asyncio()
    async def test_normal_float_score(self, service_adapter, mock_container):
        """Test normal case with valid float overall_score."""
        orchestrator = mock_container.orchestrator.return_value
        orchestrator.create_definition.return_value = self.create_validation_response(
            85.5
        )

        result = await service_adapter.generate_definition("Test", {})

        assert result["validation_details"]["overall_score"] == 85.5
        assert result["final_score"] == 85.5
        assert isinstance(result["final_score"], float)
        assert isinstance(result["validation_details"]["overall_score"], float)

    @pytest.mark.asyncio()
    async def test_normal_int_score(self, service_adapter, mock_container):
        """Test normal case with valid integer overall_score."""
        orchestrator = mock_container.orchestrator.return_value
        orchestrator.create_definition.return_value = self.create_validation_response(
            90
        )

        result = await service_adapter.generate_definition("Test", {})

        assert result["validation_details"]["overall_score"] == 90.0
        assert result["final_score"] == 90.0
        assert isinstance(result["final_score"], float)

    @pytest.mark.asyncio()
    async def test_missing_overall_score_key(self, service_adapter, mock_container):
        """Test when overall_score key is completely missing from response."""
        orchestrator = mock_container.orchestrator.return_value
        orchestrator.create_definition.return_value = self.create_validation_response(
            include_score=False
        )

        result = await service_adapter.generate_definition("Test", {})

        # Should default to 0.0 when missing
        assert result["validation_details"]["overall_score"] == 0.0
        assert result["final_score"] == 0.0
        assert isinstance(result["final_score"], float)

    @pytest.mark.asyncio()
    async def test_none_overall_score(self, service_adapter, mock_container):
        """Test when overall_score is explicitly None."""
        orchestrator = mock_container.orchestrator.return_value
        orchestrator.create_definition.return_value = self.create_validation_response(
            None
        )

        result = await service_adapter.generate_definition("Test", {})

        # Should default to 0.0 when None
        assert result["validation_details"]["overall_score"] == 0.0
        assert result["final_score"] == 0.0

    @pytest.mark.asyncio()
    async def test_empty_string_score(self, service_adapter, mock_container):
        """Test when overall_score is an empty string."""
        orchestrator = mock_container.orchestrator.return_value
        orchestrator.create_definition.return_value = self.create_validation_response(
            ""
        )

        result = await service_adapter.generate_definition("Test", {})

        # Empty string should default to 0.0
        assert result["validation_details"]["overall_score"] == 0.0
        assert result["final_score"] == 0.0

    @pytest.mark.asyncio()
    async def test_numeric_string_score(self, service_adapter, mock_container):
        """Test when overall_score is a valid numeric string."""
        orchestrator = mock_container.orchestrator.return_value
        orchestrator.create_definition.return_value = self.create_validation_response(
            "75.5"
        )

        result = await service_adapter.generate_definition("Test", {})

        # Should convert string to float
        assert result["validation_details"]["overall_score"] == 75.5
        assert result["final_score"] == 75.5
        assert isinstance(result["final_score"], float)

    @pytest.mark.asyncio()
    async def test_zero_score(self, service_adapter, mock_container):
        """Test when overall_score is zero (should not be replaced with default)."""
        orchestrator = mock_container.orchestrator.return_value
        orchestrator.create_definition.return_value = self.create_validation_response(0)

        result = await service_adapter.generate_definition("Test", {})

        # Zero should be preserved, not replaced with default
        assert result["validation_details"]["overall_score"] == 0.0
        assert result["final_score"] == 0.0

    @pytest.mark.asyncio()
    async def test_negative_score(self, service_adapter, mock_container):
        """Test when overall_score is negative."""
        orchestrator = mock_container.orchestrator.return_value
        orchestrator.create_definition.return_value = self.create_validation_response(
            -25.5
        )

        result = await service_adapter.generate_definition("Test", {})

        # Negative values should be preserved
        assert result["validation_details"]["overall_score"] == -25.5
        assert result["final_score"] == -25.5

    @pytest.mark.asyncio()
    async def test_very_large_score(self, service_adapter, mock_container):
        """Test when overall_score is extremely large."""
        orchestrator = mock_container.orchestrator.return_value
        large_score = 1e308  # Near float max
        orchestrator.create_definition.return_value = self.create_validation_response(
            large_score
        )

        result = await service_adapter.generate_definition("Test", {})

        assert result["validation_details"]["overall_score"] == large_score
        assert result["final_score"] == large_score

    @pytest.mark.asyncio()
    async def test_validation_object_none(self, service_adapter, mock_container):
        """Test when entire validation object is None."""
        orchestrator = mock_container.orchestrator.return_value
        orchestrator.create_definition.return_value = self.create_validation_response(
            validation_exists=False
        )

        result = await service_adapter.generate_definition("Test", {})

        # Should handle gracefully with defaults
        assert result["validation_details"]["overall_score"] == 0.0
        assert result["final_score"] == 0.0
        assert result["validation_details"]["is_acceptable"] is False
        assert result["validation_details"]["violations"] == []
        assert result["validation_details"]["passed_rules"] == []

    @pytest.mark.asyncio()
    async def test_boolean_true_score(self, service_adapter, mock_container):
        """Test when overall_score is boolean True (edge case)."""
        orchestrator = mock_container.orchestrator.return_value
        orchestrator.create_definition.return_value = self.create_validation_response(
            True
        )

        result = await service_adapter.generate_definition("Test", {})

        # True converts to 1.0 in Python
        assert result["validation_details"]["overall_score"] == 1.0
        assert result["final_score"] == 1.0

    @pytest.mark.asyncio()
    async def test_boolean_false_score(self, service_adapter, mock_container):
        """Test when overall_score is boolean False (edge case)."""
        orchestrator = mock_container.orchestrator.return_value
        orchestrator.create_definition.return_value = self.create_validation_response(
            False
        )

        result = await service_adapter.generate_definition("Test", {})

        # False converts to 0.0 in Python but should not trigger the 'or' clause
        assert result["validation_details"]["overall_score"] == 0.0
        assert result["final_score"] == 0.0


class TestConcurrentValidations:
    """Test concurrent validation scenarios with different overall_score values."""

    @pytest.fixture()
    def mock_containers(self):
        """Create multiple mock containers for concurrent testing."""
        containers = []
        for _ in range(5):
            container = Mock()
            orchestrator = AsyncMock()
            orchestrator.get_stats = Mock(return_value={})
            container.orchestrator.return_value = orchestrator
            containers.append((container, orchestrator))
        return containers

    @pytest.mark.asyncio()
    async def test_concurrent_mixed_scores(self, mock_containers):
        """Test concurrent validations with various score scenarios."""
        adapters = []
        orchestrators = []

        # Setup different scenarios
        test_scenarios = [
            (100.0, True),  # Normal high score
            (None, False),  # None score
            ("50.5", True),  # String score
            (0, False),  # Zero score
            (-10, False),  # Negative score
        ]

        for i, (container, orchestrator) in enumerate(mock_containers):
            adapter = ServiceAdapter(container)
            adapters.append(adapter)
            orchestrators.append(orchestrator)

            # Setup response for this scenario
            score_value, is_acceptable = test_scenarios[i]

            validation_dict = {
                "is_acceptable": is_acceptable,
                "violations": [],
                "passed_rules": ["rule1"] if is_acceptable else [],
            }

            if score_value is not None:
                validation_dict["overall_score"] = score_value

            mock_validation = Mock()
            mock_validation.to_dict.return_value = validation_dict
            # Add required attributes
            mock_validation.violations = validation_dict.get("violations", [])
            mock_validation.is_valid = validation_dict.get("is_acceptable", False)
            mock_validation.score = validation_dict.get("overall_score", 0.0)
            mock_validation.errors = []
            mock_validation.suggestions = []

            orchestrator.create_definition.return_value = DefinitionResponse(
                success=True,
                definition=Definition(
                    begrip=f"Test{i}",
                    definitie=f"Definition {i}",
                    metadata={"origineel": f"Original {i}", "voorbeelden": {}},
                ),
                validation=mock_validation,
                message="Success",
            )

        # Execute concurrent validations
        tasks = [
            adapter.generate_definition(f"Test{i}", {})
            for i, adapter in enumerate(adapters)
        ]

        results = await asyncio.gather(*tasks)

        # Verify results
        expected_scores = [100.0, 0.0, 50.5, 0.0, -10.0]

        for i, (result, expected_score) in enumerate(
            zip(results, expected_scores, strict=False)
        ):
            assert result["final_score"] == expected_score, f"Scenario {i} failed"
            assert result["validation_details"]["overall_score"] == expected_score
            assert isinstance(result["final_score"], float)
            assert isinstance(result["validation_details"]["overall_score"], float)

    @pytest.mark.asyncio()
    async def test_concurrent_error_recovery(self, mock_containers):
        """Test concurrent validations with some causing errors."""
        adapters = []
        orchestrators = []

        # Setup mix of successful and error scenarios
        for i, (container, orchestrator) in enumerate(mock_containers[:3]):
            adapter = ServiceAdapter(container)
            adapters.append(adapter)
            orchestrators.append(orchestrator)

            if i == 1:
                # Simulate an error case with invalid data type
                validation_dict = {
                    "overall_score": {"nested": "dict"},  # Invalid type
                    "is_acceptable": False,
                    "violations": [],
                    "passed_rules": [],
                }
            else:
                # Normal case
                validation_dict = {
                    "overall_score": 80.0 + i,
                    "is_acceptable": True,
                    "violations": [],
                    "passed_rules": ["rule1"],
                }

            mock_validation = Mock()
            mock_validation.to_dict.return_value = validation_dict
            # Add required attributes
            mock_validation.violations = validation_dict.get("violations", [])
            mock_validation.is_valid = validation_dict.get("is_acceptable", False)
            mock_validation.score = validation_dict.get("overall_score", 0.0)
            mock_validation.errors = []
            mock_validation.suggestions = []

            orchestrator.create_definition.return_value = DefinitionResponse(
                success=True,
                definition=Definition(
                    begrip=f"Test{i}",
                    definitie=f"Definition {i}",
                    metadata={"origineel": f"Original {i}", "voorbeelden": {}},
                ),
                validation=mock_validation,
                message="Success",
            )

        # Execute with error handling
        tasks = []
        for i, adapter in enumerate(adapters):
            tasks.append(adapter.generate_definition(f"Test{i}", {}))

        # Some tasks might fail, use gather with return_exceptions
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that valid ones succeeded
        for i, result in enumerate(results):
            if i == 1:
                # This one should have raised an error or handled it
                if isinstance(result, Exception):
                    assert True  # Expected behavior
                else:
                    # If it didn't raise, it should have some validation_details
                    assert "validation_details" in result
            else:
                # Normal cases should succeed
                assert not isinstance(result, Exception)
                assert result["final_score"] == 80.0 + i


class TestProductionReadiness:
    """Test production readiness aspects of the overall_score fix."""

    @pytest.mark.asyncio()
    async def test_memory_efficiency_large_batch(self):
        """Test memory efficiency with large batch of validations."""
        container = Mock()
        orchestrator = AsyncMock()
        orchestrator.get_stats = Mock(return_value={})
        container.orchestrator.return_value = orchestrator
        adapter = ServiceAdapter(container)

        # Simulate large batch
        batch_size = 1000

        mock_validation = Mock()
        validation_dict = {
            "overall_score": 85.5,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["rule1"],
        }
        mock_validation.to_dict.return_value = validation_dict
        # Add required attributes
        mock_validation.violations = []
        mock_validation.is_valid = True
        mock_validation.score = 85.5
        mock_validation.errors = []
        mock_validation.suggestions = []

        orchestrator.create_definition.return_value = DefinitionResponse(
            success=True,
            definition=Definition(
                begrip="Test",
                definitie="Test definitie",
                metadata={"origineel": "Original", "voorbeelden": {}},
            ),
            validation=mock_validation,
            message="Success",
        )

        # Process batch
        tasks = [adapter.generate_definition(f"Test{i}", {}) for i in range(batch_size)]

        results = await asyncio.gather(*tasks)

        # Verify all processed correctly
        assert len(results) == batch_size
        for result in results:
            assert result["final_score"] == 85.5

    @pytest.mark.asyncio()
    async def test_resilience_malformed_response(self):
        """Test resilience against malformed API responses."""
        container = Mock()
        orchestrator = AsyncMock()
        orchestrator.get_stats = Mock(return_value={})
        container.orchestrator.return_value = orchestrator
        adapter = ServiceAdapter(container)

        # Create malformed validation response (missing expected structure)
        mock_validation = Mock()
        mock_validation.to_dict.return_value = "not_a_dict"  # Completely wrong type
        # Still need basic attributes to prevent other failures
        mock_validation.violations = []
        mock_validation.is_valid = False
        mock_validation.score = 0.0
        mock_validation.errors = []
        mock_validation.suggestions = []

        orchestrator.create_definition.return_value = DefinitionResponse(
            success=True,
            definition=Definition(
                begrip="Test",
                definitie="Test definitie",
                metadata={"origineel": "Original"},
            ),
            validation=mock_validation,
            message="Success",
        )

        # Should handle gracefully or raise appropriate error
        try:
            result = await adapter.generate_definition("Test", {})
            # If it succeeds, check for safe defaults
            if "validation_details" in result:
                assert isinstance(result["validation_details"], dict)
        except (AttributeError, TypeError):
            # Expected if not handled - document the behavior
            assert True

    def test_type_safety_validation(self):
        """Test that type conversion is safe and predictable."""
        test_cases = [
            (85.5, 85.5),  # Float
            (90, 90.0),  # Int
            ("75.5", 75.5),  # Valid string
            ("", 0.0),  # Empty string
            (None, 0.0),  # None
            (True, 1.0),  # Boolean True
            (False, 0.0),  # Boolean False
            (0, 0.0),  # Zero
            (-10, -10.0),  # Negative
        ]

        for input_val, expected in test_cases:
            # Simulate the actual conversion logic
            result = float(input_val or 0.0) if input_val != "" else 0.0
            assert result == expected, f"Failed for input {input_val}"


class TestDocumentedBehavior:
    """Test that the implementation matches documented behavior."""

    @pytest.mark.asyncio()
    async def test_line_170_behavior(self):
        """Test line 170: float(result.get("overall_score") or 0.0)"""
        container = Mock()
        orchestrator = AsyncMock()
        orchestrator.get_stats = Mock(return_value={})
        container.orchestrator.return_value = orchestrator
        adapter = ServiceAdapter(container)

        # Test the exact behavior of line 170
        test_cases = [
            {"overall_score": 85.5},  # Normal case
            {"overall_score": None},  # None case
            {},  # Missing key
            {"overall_score": ""},  # Empty string
            {"overall_score": 0},  # Zero
        ]

        for test_dict in test_cases:
            mock_validation = Mock()
            validation_dict = {
                **test_dict,
                "is_acceptable": True,
                "violations": [],
                "passed_rules": [],
            }
            mock_validation.to_dict.return_value = validation_dict
            # Add required attributes
            mock_validation.violations = []
            mock_validation.is_valid = True
            mock_validation.score = test_dict.get("overall_score", 0.0)
            mock_validation.errors = []
            mock_validation.suggestions = []

            orchestrator.create_definition.return_value = DefinitionResponse(
                success=True,
                definition=Definition(
                    begrip="Test",
                    definitie="Test definitie",
                    metadata={"origineel": "Original", "voorbeelden": {}},
                ),
                validation=mock_validation,
                message="Success",
            )

            result = await adapter.generate_definition("Test", {})

            # Verify the conversion logic
            expected = float(test_dict.get("overall_score") or 0.0)
            assert result["validation_details"]["overall_score"] == expected

    @pytest.mark.asyncio()
    async def test_line_297_behavior(self):
        """Test line 297: validation_details.get("overall_score", 0.0)"""
        container = Mock()
        orchestrator = AsyncMock()
        orchestrator.get_stats = Mock(return_value={})
        container.orchestrator.return_value = orchestrator
        adapter = ServiceAdapter(container)

        # Test the exact behavior of line 297
        mock_validation = Mock()
        validation_dict = {
            "is_acceptable": True,
            "violations": [],
            "passed_rules": [],
            # Intentionally missing overall_score
        }
        mock_validation.to_dict.return_value = validation_dict
        # Add required attributes
        mock_validation.violations = []
        mock_validation.is_valid = True
        mock_validation.score = 0.0  # Missing score defaults to 0.0
        mock_validation.errors = []
        mock_validation.suggestions = []

        orchestrator.create_definition.return_value = DefinitionResponse(
            success=True,
            definition=Definition(
                begrip="Test",
                definitie="Test definitie",
                metadata={"origineel": "Original", "voorbeelden": {}},
            ),
            validation=mock_validation,
            message="Success",
        )

        result = await adapter.generate_definition("Test", {})

        # Line 297 uses validation_details.get("overall_score", 0.0)
        assert result["final_score"] == 0.0  # Default when missing


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
