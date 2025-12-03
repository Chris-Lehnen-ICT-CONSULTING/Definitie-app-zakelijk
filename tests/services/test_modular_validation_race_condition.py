"""Tests for DEF-244: Race condition fix in ModularValidationService.

These tests verify that concurrent validations do not cross-contaminate begrip values
when the same ModularValidationService instance is shared. The fix moved `begrip` from
a shared instance variable (`self._current_begrip`) to the immutable `EvaluationContext`.

Before the fix: Concurrent validations would overwrite each other's begrip values,
causing incorrect validation results (e.g., wrong circular definition detection).

After the fix: Each validation uses its own `EvaluationContext.begrip`, ensuring
complete isolation between concurrent requests.
"""

from __future__ import annotations

import asyncio

import pytest


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.regression
async def test_concurrent_validation_begrip_isolation():
    """CRITICAL: Concurrent validations must use their own begrip values.

    This test reproduces DEF-244: when multiple validations run concurrently
    on the same service instance, the begrip must be isolated per-validation.

    Each definition text contains ONLY its own begrip, so if cross-contamination
    occurs (validation for "alpha" uses begrip "beta"), the circular definition
    check would fail to detect the issue.
    """
    from services.validation.modular_validation_service import ModularValidationService

    # Single shared instance (this is how production uses it)
    service = ModularValidationService(
        toetsregel_manager=None,
        cleaning_service=None,
        config=None,
    )

    # Each text contains ONLY its own begrip - cross-contamination would break detection
    test_cases = [
        {
            "begrip": "alpha",
            "text": "Het begrip alpha is een testconcept dat circulair verwijst naar alpha zelf.",
            "expected_circular": True,
        },
        {
            "begrip": "beta",
            "text": "Het begrip beta wordt hier gedefinieerd met verwijzing naar beta.",
            "expected_circular": True,
        },
        {
            "begrip": "gamma",
            "text": "Het begrip gamma is een definitie die gamma bevat.",
            "expected_circular": True,
        },
        {
            "begrip": "delta",
            "text": "Dit is een correcte definitie zonder zelfverwijzing naar het begrip.",
            "expected_circular": False,  # Does NOT contain "delta"
        },
        {
            "begrip": "epsilon",
            "text": "Epsilon wordt gedefinieerd als een Griekse letter genaamd epsilon.",
            "expected_circular": True,
        },
    ]

    # Run ALL validations concurrently
    tasks = [
        service.validate_definition(
            begrip=tc["begrip"],
            text=tc["text"],
            ontologische_categorie=None,
            context={"correlation_id": f"race-test-{tc['begrip']}"},
        )
        for tc in test_cases
    ]

    results = await asyncio.gather(*tasks)

    # Verify each result matches expected outcome
    for tc, result in zip(test_cases, results, strict=True):
        violation_codes = [v.get("code", "") for v in result.get("violations", [])]
        has_circular = "CON-CIRC-001" in violation_codes

        assert has_circular == tc["expected_circular"], (
            f"Race condition detected for begrip='{tc['begrip']}': "
            f"expected circular={tc['expected_circular']}, got circular={has_circular}. "
            f"Violations: {violation_codes}. "
            f"This indicates begrip isolation failure in concurrent validation."
        )


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.regression
async def test_batch_validate_begrip_isolation():
    """Batch validation with max_concurrency > 1 must isolate begrip per item.

    The batch_validate method uses asyncio.gather internally when max_concurrency > 1,
    which could trigger race conditions if begrip is not properly isolated.
    """
    from services.validation.modular_validation_service import ModularValidationService

    service = ModularValidationService(
        toetsregel_manager=None,
        cleaning_service=None,
        config=None,
    )

    # Items with unique begrips, each containing their own begrip in text
    items = [
        {
            "begrip": f"begrip_{i}",
            "text": f"Dit is begrip_{i} met verwijzing naar begrip_{i}.",
        }
        for i in range(10)
    ]

    # Run with max_concurrency=5 to trigger parallel execution
    results = await service.batch_validate(items, max_concurrency=5)

    # Each result should have CON-CIRC-001 violation
    for i, result in enumerate(results):
        violation_codes = [v.get("code", "") for v in result.get("violations", [])]
        assert "CON-CIRC-001" in violation_codes, (
            f"Item {i} (begrip_{i}) should have circular violation. "
            f"Got violations: {violation_codes}. Race condition likely."
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sequential_validation_baseline():
    """Baseline: Sequential validations should always work correctly.

    This establishes that the validation logic is correct when no concurrency
    is involved, serving as a control for the concurrent tests.
    """
    from services.validation.modular_validation_service import ModularValidationService

    service = ModularValidationService(
        toetsregel_manager=None,
        cleaning_service=None,
        config=None,
    )

    test_cases = [
        ("aardvark", "Het begrip aardvark verwijst naar aardvark.", True),
        ("zebra", "Dit is een definitie zonder zelfverwijzing.", False),
        ("camel", "De camel is een dier dat camel heet.", True),
    ]

    # Run sequentially (await each before starting next)
    for begrip, text, expect_circular in test_cases:
        result = await service.validate_definition(
            begrip=begrip,
            text=text,
            context={"correlation_id": f"seq-{begrip}"},
        )

        violation_codes = [v.get("code", "") for v in result.get("violations", [])]
        has_circular = "CON-CIRC-001" in violation_codes

        assert has_circular == expect_circular, (
            f"Sequential test failed for '{begrip}': "
            f"expected circular={expect_circular}, got {has_circular}"
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_batch_validate_sequential_vs_parallel_parity():
    """Sequential (max_concurrency=1) and parallel must produce identical results.

    If results differ, it indicates a race condition or isolation issue.
    """
    from services.validation.modular_validation_service import ModularValidationService

    service = ModularValidationService(
        toetsregel_manager=None,
        cleaning_service=None,
        config=None,
    )

    # Mix of circular and non-circular definitions
    items = [
        {"begrip": "zon", "text": "De zon is een ster genaamd zon."},  # Circular
        {"begrip": "maan", "text": "Een satelliet die om de aarde draait."},  # Not
        {"begrip": "aarde", "text": "De planeet aarde is waar wij wonen op aarde."},
        {"begrip": "mars", "text": "Een rode planeet in ons zonnestelsel."},  # Not
        {"begrip": "venus", "text": "Venus is een planeet genaamd venus."},  # Circular
    ]

    # Run sequentially (guaranteed correct)
    results_seq = await service.batch_validate(items, max_concurrency=1)

    # Run in parallel
    results_par = await service.batch_validate(items, max_concurrency=5)

    # Compare violation codes for each item
    for i, (seq, par) in enumerate(zip(results_seq, results_par, strict=True)):
        seq_codes = sorted([v.get("code", "") for v in seq.get("violations", [])])
        par_codes = sorted([v.get("code", "") for v in par.get("violations", [])])

        # CON-CIRC-001 presence should match
        seq_has_circ = "CON-CIRC-001" in seq_codes
        par_has_circ = "CON-CIRC-001" in par_codes

        assert seq_has_circ == par_has_circ, (
            f"Item {i} ({items[i]['begrip']}): Sequential and parallel differ. "
            f"Sequential has CON-CIRC-001: {seq_has_circ}, "
            f"Parallel has CON-CIRC-001: {par_has_circ}. "
            f"This indicates a race condition."
        )


@pytest.mark.unit
def test_evaluation_context_begrip_field():
    """EvaluationContext must have begrip field for thread-safe passing."""
    from services.validation.types_internal import EvaluationContext

    # Create context with begrip
    ctx = EvaluationContext.from_params(
        text="test text",
        cleaned="test text",
        begrip="TestBegrip",
    )

    assert ctx.begrip == "TestBegrip", "begrip field should be set"
    assert hasattr(ctx, "begrip"), "EvaluationContext must have begrip attribute"


@pytest.mark.unit
def test_evaluation_context_begrip_default():
    """EvaluationContext.begrip should default to empty string."""
    from services.validation.types_internal import EvaluationContext

    # Create context without begrip
    ctx = EvaluationContext.from_params(
        text="test text",
        cleaned="test text",
    )

    assert ctx.begrip == "", "begrip should default to empty string"


@pytest.mark.unit
def test_evaluation_context_immutability():
    """EvaluationContext must be immutable (frozen dataclass)."""
    from dataclasses import FrozenInstanceError

    from services.validation.types_internal import EvaluationContext

    ctx = EvaluationContext.from_params(
        text="test",
        begrip="original",
    )

    # Attempting to modify should raise FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        ctx.begrip = "modified"  # type: ignore[misc]
