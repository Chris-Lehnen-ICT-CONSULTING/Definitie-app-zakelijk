import json
from pathlib import Path

import pytest

pytestmark = [pytest.mark.contract]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_validation_result_happy_path_schema():
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    # Load JSON schema
    schema_path = Path(
        "docs/architectuur/contracts/schemas/validation_result.schema.json"
    )
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
    schema_path = Path(
        "docs/architectuur/contracts/schemas/validation_result.schema.json"
    )
    assert schema_path.exists(), "Schema file missing"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    from jsonschema import validate

    from services.validation.mappers import create_degraded_result

    degraded = create_degraded_result(
        error="Simulated failure",
        correlation_id="00000000-0000-0000-0000-000000000001",
        begrip="testbegrip",
    )
    validate(instance=degraded, schema=schema)


def _schema() -> dict:
    pad = Path("docs/architectuur/contracts/schemas/validation_result.schema.json")
    assert pad.exists(), "Schema file missing"
    return json.loads(pad.read_text(encoding="utf-8"))


async def _echt_resultaat() -> dict:
    """Een resultaat uit het echte productiepad, inclusief regelset."""
    from services.validation.modular_validation_service import ModularValidationService
    from toetsregels.manager import get_toetsregel_manager

    service = ModularValidationService(get_toetsregel_manager(), None, None)
    return await service.validate_definition(
        begrip="toezicht",
        text="toezicht: systematisch volgen van handelingen aan de hand van normen",
        ontologische_categorie=None,
        context={"correlation_id": "00000000-0000-0000-0000-000000000002"},
    )


@pytest.mark.contract
@pytest.mark.asyncio
async def test_nieuwe_velden_zijn_schema_conform():
    """DEF-624 (contract 1.1.0): de drie nieuwe velden zijn gebonden.

    Het schema houdt bewust additionalProperties=false. Dat is de reden dat
    deze PR het contract moest meemigreren: een nieuw veld hoort niet stil
    door te glippen, maar expliciet te worden vastgelegd.
    """
    from jsonschema import validate

    schema = _schema()
    resultaat = await _echt_resultaat()

    for veld in ("rule_statuses", "evaluation_coverage", "review_required"):
        assert veld in resultaat, f"resultaat mist het nieuwe veld {veld!r}"
        # Per veld tegen zijn eigen subschema. Het volledige instance-schema
        # struikelt met de échte regelset over violations[].code: dat patroon
        # (^[A-Z]{3}-[A-Z]{3}-\d{3}$) sluit rule-IDs als VER-03 en DUP_01 uit.
        # Dat gat is ouder dan deze wijziging en wordt hier niet stilzwijgend
        # opgelost door het schema losser te maken.
        validate(instance=resultaat[veld], schema=schema["properties"][veld])


@pytest.mark.contract
@pytest.mark.asyncio
async def test_alleen_toegestane_resultaatstatussen():
    from services.validation.interfaces import CONTRACT_VERSION

    resultaat = await _echt_resultaat()
    assert resultaat["version"] == CONTRACT_VERSION

    toegestaan = {"pass", "fail", "review_required", "not_evaluated", "error"}
    onbekend = sorted(set(resultaat["rule_statuses"].values()) - toegestaan)
    assert not onbekend, f"onbekende resultaatstatussen in het contract: {onbekend}"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_dekkingsblok_telt_op_en_sluit_aan_op_de_statussen():
    """De dekking moet de statussen samenvatten, niet er los van staan."""
    resultaat = await _echt_resultaat()
    dekking = resultaat["evaluation_coverage"]
    statussen = list(resultaat["rule_statuses"].values())

    assert dekking["total"] == len(statussen)
    for sleutel in ("passed", "failed", "review_required", "not_evaluated", "error"):
        verwacht = statussen.count("pass" if sleutel == "passed" else sleutel)
        if sleutel == "failed":
            verwacht = statussen.count("fail")
        assert dekking[sleutel] == verwacht, f"dekking[{sleutel!r}] wijkt af"

    assert dekking["evaluated"] == dekking["passed"] + dekking["failed"]
    assert (
        dekking["evaluated"]
        + dekking["review_required"]
        + dekking["not_evaluated"]
        + dekking["error"]
        == dekking["total"]
    )
    assert dekking["coverage_ratio"] == pytest.approx(
        dekking["evaluated"] / dekking["total"], abs=1e-4
    )


@pytest.mark.contract
@pytest.mark.asyncio
async def test_reviewplicht_is_geen_violation_en_geen_pass():
    """Kern van DEF-624: reviewplicht mag niet als kwaliteit tellen."""
    resultaat = await _echt_resultaat()
    review = resultaat["review_required"]
    assert review, "geen enkele regel is reviewplichtig; verwacht de oordeelregels"

    codes_met_violation = {v.get("code") for v in resultaat["violations"]}
    geslaagd = set(resultaat["passed_rules"])
    for item in review:
        assert set(item) == {"rule_id", "category", "reason", "signals"}
        assert isinstance(item["signals"], list)
        assert (
            item["rule_id"] not in geslaagd
        ), f"{item['rule_id']} is reviewplichtig maar staat in passed_rules"
        assert (
            item["rule_id"] not in codes_met_violation
        ), f"{item['rule_id']} is reviewplichtig maar levert ook een violation"


@pytest.mark.contract
def test_onbekend_veld_wordt_nog_steeds_geweigerd():
    """Het schema is niet losser gemaakt om de tests groen te krijgen."""
    from jsonschema import ValidationError, validate

    schema = _schema()
    assert schema["additionalProperties"] is False

    instantie = {
        "version": "1.1.0",
        "overall_score": 0.8,
        "is_acceptable": True,
        "violations": [],
        "passed_rules": [],
        "detailed_scores": {},
        "system": {"correlation_id": "00000000-0000-0000-0000-000000000003"},
        "verzonnen_veld": True,
    }
    with pytest.raises(ValidationError, match="verzonnen_veld"):
        validate(instance=instantie, schema=schema)


@pytest.mark.contract
def test_ongeldige_resultaatstatus_wordt_geweigerd():
    from jsonschema import ValidationError, validate

    instantie = {
        "version": "1.1.0",
        "overall_score": 0.8,
        "is_acceptable": True,
        "violations": [],
        "passed_rules": [],
        "detailed_scores": {},
        "system": {"correlation_id": "00000000-0000-0000-0000-000000000004"},
        "rule_statuses": {"CON-01": "misschien"},
    }
    with pytest.raises(ValidationError):
        validate(instance=instantie, schema=_schema())


@pytest.mark.contract
def test_incompleet_dekkingsblok_wordt_geweigerd():
    from jsonschema import ValidationError, validate

    instantie = {
        "version": "1.1.0",
        "overall_score": 0.8,
        "is_acceptable": True,
        "violations": [],
        "passed_rules": [],
        "detailed_scores": {},
        "system": {"correlation_id": "00000000-0000-0000-0000-000000000005"},
        "evaluation_coverage": {"evaluated": 3, "total": 5},
    }
    with pytest.raises(ValidationError):
        validate(instance=instantie, schema=_schema())


@pytest.mark.contract
def test_typeddict_dekt_de_schemavelden():
    """TypedDict en JSON-schema mogen niet uit elkaar lopen."""
    from services.validation.interfaces import (
        EvaluationCoverage,
        ReviewRequirement,
        ValidationResult,
    )

    schema = _schema()
    assert set(schema["properties"]) <= set(ValidationResult.__annotations__), (
        "schema kent velden die het TypedDict niet declareert: "
        f"{sorted(set(schema['properties']) - set(ValidationResult.__annotations__))}"
    )
    assert set(EvaluationCoverage.__annotations__) == set(
        schema["properties"]["evaluation_coverage"]["properties"]
    )
    assert set(ReviewRequirement.__annotations__) == set(
        schema["properties"]["review_required"]["items"]["properties"]
    )
