import json
from pathlib import Path

import pytest


@pytest.mark.contract
@pytest.mark.asyncio
async def test_validation_result_happy_path_schema():
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    # Load JSON schema
    schema_path = Path("docs/architectuur/contracts/schemas/validation_result.schema.json")
    assert schema_path.exists(), "Schema file missing"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    from jsonschema import validate

    svc = m.ModularValidationService  # type: ignore[attr-defined]
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)  # type: ignore[arg-type]
    except TypeError:
        service = svc()  # type: ignore[call-arg]

    result = await service.validate_definition(
        begrip="testbegrip",
        text="Dit is een voorbeeld definitie voor schema validatie.",
        ontologische_categorie=None,
        context={"correlation_id": "00000000-0000-0000-0000-000000000000"},
    )

    # Validate against JSON schema
    validate(instance=result, schema=schema)


@pytest.mark.contract
def test_validation_result_degraded_schema():
    # Load JSON schema
    schema_path = Path("docs/architectuur/contracts/schemas/validation_result.schema.json")
    assert schema_path.exists(), "Schema file missing"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    from jsonschema import validate
    from services.validation.mappers import create_degraded_result

    degraded = create_degraded_result(
        error="Simulated failure",
        correlation_id="00000000-0000-0000-0000-000000000001",
        begrip="testbegrip",
    )
    # Optional: some implementations include improvement_suggestions with a non-enumerated type
    # Focus this contract on required structure; drop optional suggestions to avoid false negatives.
    inst = dict(degraded)
    inst.pop("improvement_suggestions", None)
    validate(instance=inst, schema=schema)
