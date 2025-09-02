"""Tests for batch validation functionality."""

import pytest
from typing import List
import asyncio


@pytest.mark.unit
@pytest.mark.asyncio
async def test_batch_validate_interface():
    """Test that batch_validate method exists and works."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

    # Test with multiple items
    items = [
        {"begrip": "test1", "text": "Eerste test definitie met voldoende inhoud."},
        {"begrip": "test2", "text": "Tweede test definitie ook met inhoud."},
        {"begrip": "test3", "text": "Derde."},  # Short, will have violations
    ]

    results = await service.batch_validate(items)

    # Results length must match input length
    assert len(results) == len(items), f"Expected {len(items)} results, got {len(results)}"

    # Each result must be a valid ValidationResult
    for i, result in enumerate(results):
        assert isinstance(result, dict), f"Result {i} must be a dict"
        assert "overall_score" in result, f"Result {i} missing overall_score"
        assert "is_acceptable" in result, f"Result {i} missing is_acceptable"
        assert "violations" in result, f"Result {i} missing violations"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_batch_validate_order_preservation():
    """Test that batch results are returned in same order as input."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

    # Items with predictable quality order
    items = [
        {"begrip": "empty", "text": ""},  # Will fail
        {"begrip": "good", "text": "Een goede definitie met voldoende uitleg en context voor validatie."},  # Will pass
        {"begrip": "short", "text": "Te kort."},  # Will fail
        {"begrip": "perfect", "text": "Een uitstekende definitie die alle vereisten vervult met duidelijke uitleg, goede structuur, en voldoende detail om het concept volledig te begrijpen."},  # Will pass
    ]

    results = await service.batch_validate(items)

    # Check order preserved by checking acceptability pattern
    assert results[0]["is_acceptable"] is False, "Empty text should fail"
    assert results[1]["is_acceptable"] is True, "Good definition should pass"
    assert results[2]["is_acceptable"] is False, "Short text should fail"
    assert results[3]["is_acceptable"] is True, "Perfect definition should pass"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_batch_validate_with_max_concurrency():
    """Test batch validation with concurrency control."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

    # Create many items to test concurrency
    items = [
        {"begrip": f"test{i}", "text": f"Test definitie nummer {i} met voldoende inhoud."}
        for i in range(10)
    ]

    # Test sequential (max_concurrency=1)
    results_seq = await service.batch_validate(items, max_concurrency=1)
    assert len(results_seq) == 10

    # Test parallel (max_concurrency=5)
    results_par = await service.batch_validate(items, max_concurrency=5)
    assert len(results_par) == 10

    # Results should be identical regardless of concurrency
    for i in range(10):
        assert results_seq[i]["overall_score"] == results_par[i]["overall_score"], \
            f"Item {i}: scores differ between sequential and parallel"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_batch_validate_individual_failure_handling():
    """Test that individual failures don't crash entire batch."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

    # Mix of valid and problematic items
    items = [
        {"begrip": "normal", "text": "Normale definitie met goede inhoud."},
        {"begrip": "empty", "text": ""},  # Edge case
        {"begrip": "unicode", "text": "Definitie met emoji 😀 en speciale tekens ñ."},
        {"begrip": None, "text": "Begrip is None"},  # Invalid begrip
        {"begrip": "normal2", "text": "Nog een normale definitie."},
    ]

    results = await service.batch_validate(items)

    # All items should return results (degraded for failures)
    assert len(results) == len(items), "Must return result for each item"

    # Check that valid items still processed correctly
    assert results[0]["is_acceptable"] in [True, False], "Normal item should have valid result"
    assert results[4]["is_acceptable"] in [True, False], "Last normal item should have valid result"

    # Invalid items should have degraded results
    assert results[3]["is_acceptable"] is False, "Invalid begrip should fail"
    if "system" in results[3] and "error" in results[3]["system"]:
        assert results[3]["system"]["error"] is not None, "Error should be recorded"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_batch_validate_with_validation_request_objects():
    """Test batch validation using ValidationRequest dataclass."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )
    i = pytest.importorskip(
        "services.validation.interfaces",
        reason="interfaces module needed for ValidationRequest",
    )

    svc = m.ModularValidationService
    ValidationRequest = getattr(i, "ValidationRequest", None)
    ValidationContext = getattr(i, "ValidationContext", None)

    if not ValidationRequest:
        pytest.skip("ValidationRequest not found")

    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

    # Create ValidationRequest objects
    context = ValidationContext(correlation_id="batch-123") if ValidationContext else None

    requests = [
        ValidationRequest(
            begrip="req1",
            text="Eerste request definitie.",
            ontologische_categorie="concept",
            context=context,
        ),
        ValidationRequest(
            begrip="req2",
            text="Tweede request definitie met meer detail.",
            ontologische_categorie="proces",
            context=context,
        ),
    ]

    results = await service.batch_validate(requests)

    assert len(results) == 2
    for result in results:
        assert "overall_score" in result
        assert "system" in result
        if context:
            assert result["system"]["correlation_id"] == "batch-123"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_batch_validate_empty_input():
    """Test batch validation with empty input list."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

    # Empty list should return empty results
    results = await service.batch_validate([])
    assert results == [], "Empty input should return empty list"

    # None input should be handled gracefully
    results = await service.batch_validate(None)
    assert results == [], "None input should return empty list"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_batch_validate_performance_benefit():
    """Test that batch validation is more efficient than sequential calls."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    import time

    svc = m.ModularValidationService
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

    items = [
        {"begrip": f"test{i}", "text": f"Test definitie {i} met inhoud."}
        for i in range(5)
    ]

    # Time sequential individual calls
    start_seq = time.time()
    results_seq = []
    for item in items:
        result = await service.validate_definition(
            begrip=item["begrip"],
            text=item["text"],
        )
        results_seq.append(result)
    time_seq = time.time() - start_seq

    # Time batch call with concurrency
    start_batch = time.time()
    results_batch = await service.batch_validate(items, max_concurrency=3)
    time_batch = time.time() - start_batch

    # Batch should be faster (or at least not significantly slower)
    # We allow some margin for overhead
    assert time_batch <= time_seq * 1.2, \
        f"Batch ({time_batch:.2f}s) should not be much slower than sequential ({time_seq:.2f}s)"

    # Results should be equivalent
    assert len(results_batch) == len(results_seq)
