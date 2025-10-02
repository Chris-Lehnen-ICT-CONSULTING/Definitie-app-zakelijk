import importlib
from typing import Any

import pytest


@pytest.mark.unit()
@pytest.mark.contract()
def test_modular_validation_service_import_and_interface():
    """
    Contract: the ModularValidationService exists and exposes the V2 async interface.

    This test intentionally uses importorskip so it documents the expected API before
    the implementation lands. Once implemented, this becomes a hard contract test.
    """
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc_cls = getattr(m, "ModularValidationService", None)
    assert svc_cls is not None, "ModularValidationService class must exist"

    # Validate method signature exists (async validate_definition)
    assert hasattr(svc_cls, "validate_definition"), "validate_definition is required"


@pytest.mark.unit()
@pytest.mark.contract()
@pytest.mark.asyncio()
async def test_validate_definition_returns_schema_like_result():
    """
    Contract: validate_definition returns a dict-shaped result with required keys.

    We only assert the shape here; detailed parity is covered by golden tests.
    If the service isn't present yet, this test is skipped.
    """
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    # Lazy import interfaces for the return type contract keys
    from services.validation.interfaces import CONTRACT_VERSION

    svc = m.ModularValidationService  # type: ignore[attr-defined]

    # Construct with minimal dependencies; concrete manager/cleaning may be injected by the implementation
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)  # type: ignore[arg-type]
    except TypeError:
        # If constructor signature differs (e.g., positional arguments), instantiate with no args for now.
        service = svc()  # type: ignore[call-arg]

    result = await service.validate_definition(
        begrip="testbegrip",
        text="Dit is een voorbeeld definitie.",
        ontologische_categorie=None,
        context={"correlation_id": "00000000-0000-0000-0000-000000000000"},
    )

    # Accept both dict and ValidationResultWrapper (which is dict-like)
    assert isinstance(result, dict) or hasattr(
        result, "__getitem__"
    ), "Result must be a dict-like object"
    for key in (
        "version",
        "overall_score",
        "is_acceptable",
        "violations",
        "passed_rules",
        "detailed_scores",
        "system",
    ):
        assert key in result, f"Missing required key: {key}"

    assert result["version"] == CONTRACT_VERSION
    assert "correlation_id" in result["system"]


@pytest.mark.unit()
@pytest.mark.contract()
@pytest.mark.asyncio()
async def test_deterministic_results_simple():
    """Simple determinism test: two identical calls produce identical results."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

    # Same input
    begrip = "test"
    text = "Een test definitie voor determinisme check."

    # Two calls
    result1 = await service.validate_definition(begrip, text)
    result2 = await service.validate_definition(begrip, text)

    # Must be identical
    assert result1["overall_score"] == result2["overall_score"]
    assert result1["is_acceptable"] == result2["is_acceptable"]
    assert sorted(result1.get("violations", [])) == sorted(
        result2.get("violations", [])
    )
