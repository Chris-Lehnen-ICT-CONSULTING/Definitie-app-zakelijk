import json
from pathlib import Path

import pytest

pytestmark = [pytest.mark.contract]

#: Het contractschema is verplichte invoer uit de checkout. Het pad wordt vanaf
#: dít bestand afgeleid en niet vanaf de werkmap: draait de suite met een
#: tijdelijke CWD (runner, xdist-worker, IDE), dan moet hij exact hetzelfde
#: schema lezen in plaats van het stil niet te vinden.
SCHEMA_MAP = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "architectuur"
    / "contracts"
    / "schemas"
)
SCHEMA_BESTAND = "validation_result.schema.json"


def _lees_schema(naam: str = SCHEMA_BESTAND) -> dict:
    """Lees een contractschema uit de checkout.

    Ontbreekt het bestand, dan is dat een harde fout (`FileNotFoundError`) en
    géén skip: een gemist schema mag niet als "niets te toetsen" wegvallen.
    """
    return json.loads((SCHEMA_MAP / naam).read_text(encoding="utf-8"))


@pytest.mark.contract
@pytest.mark.asyncio
async def test_validation_result_happy_path_schema():
    import services.validation.modular_validation_service as m

    schema = _lees_schema()

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
    schema = _lees_schema()

    from jsonschema import validate

    from services.validation.mappers import create_degraded_result

    degraded = create_degraded_result(
        error="Simulated failure",
        correlation_id="00000000-0000-0000-0000-000000000001",
        begrip="testbegrip",
    )
    validate(instance=degraded, schema=schema)


def _schema() -> dict:
    return _lees_schema()


@pytest.mark.contract
def test_schema_wordt_repository_relatief_gelezen(tmp_path, monkeypatch):
    """De schemainvoer hangt aan de checkout, niet aan de werkmap.

    RED-discriminator voor DEF-519: met een CWD-relatief pad viel deze suite in
    een tijdelijke werkmap om (`Schema file missing`). Beide takken staan hier
    expliciet: hetzelfde schema vanuit een vreemde CWD, én een ontbrekend
    bestand dat hard faalt in plaats van te skippen.
    """
    vanuit_repo = _lees_schema()
    monkeypatch.chdir(tmp_path)
    assert _lees_schema() == vanuit_repo
    assert SCHEMA_MAP.is_absolute()

    with pytest.raises(FileNotFoundError):
        _lees_schema("er-is-geen-validation_result.schema.json")


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
        "validation_status": "validated",  # DEF-624: verplicht veld
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
        "validation_status": "validated",  # DEF-624: verplicht veld
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
        "validation_status": "validated",  # DEF-624: verplicht veld
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
def test_statusset_heeft_geen_tweede_waarheid():
    """De vijf resultaatstatussen staan op vier plekken; hier sluiten ze.

    `ResultStatus` (runtime), `runtime_contract.result_status` (root-SSOT),
    de enum in dit JSON-schema en `RuleResultStatus` (TypedDict-binding).
    De eerste twee worden al door test_root_ssot_contract.py aan elkaar
    gebonden; zonder deze test konden schema en Literal stil uit elkaar
    lopen — precies de tweede waarheid die DEF-606 wil uitbannen.
    """
    from typing import get_args

    from services.validation.interfaces import RuleResultStatus
    from toetsregels.runtime_contract import ResultStatus

    runtime = {status.value for status in ResultStatus}
    schema_enum = set(
        _schema()["properties"]["rule_statuses"]["additionalProperties"]["enum"]
    )
    binding = set(get_args(RuleResultStatus))

    assert schema_enum == runtime, (
        f"JSON-schema en ResultStatus lopen uiteen: "
        f"alleen in schema {sorted(schema_enum - runtime)}, "
        f"alleen in runtime {sorted(runtime - schema_enum)}"
    )
    assert binding == runtime, (
        f"RuleResultStatus en ResultStatus lopen uiteen: "
        f"alleen in binding {sorted(binding - runtime)}, "
        f"alleen in runtime {sorted(runtime - binding)}"
    )


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


# ---------------------------------------------------------------------------
# DEF-835 WP3 (contract 2.3.0): de echte INT-02 O2-evaluatoruitkomst tegen het
# echte schema. `assessment` en `signals` zijn alleen voor INT-02 en de al
# bestaande INT-03 toegestaan; andere regels en onbekende velden blijven dicht.
# ---------------------------------------------------------------------------

CONTRACTDOC = SCHEMA_MAP.parent / "validation_result_contract.md"
REGELS_MAP = Path(__file__).resolve().parents[3] / "src" / "toetsregels" / "regels"
O2_SCENARIO_S = (
    "pass",
    "fail",
    "fail_discretie",
    "insufficient",
    "not_applicable",
    "niet_beoordeeld",
    "historisch",
    "niet_uitgevoerd",
    "fout",
)


def _schemafouten(rule_results: dict) -> list:
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(_schema()["properties"]["rule_results"])
    return list(validator.iter_errors(json.loads(json.dumps(rule_results))))


def _o2_detail(scenario: str) -> dict:
    """Het echte `rule_result` van de O2-evaluator (DEF-835 WP3)."""
    from tests.unit.validation.test_def835_int02_evaluator import o2_uitkomsten

    detail = o2_uitkomsten()[scenario].metadata.get("rule_result")
    assert isinstance(detail, dict), f"{scenario}: evaluator levert geen rule_result"
    return detail


@pytest.mark.contract
def test_contractversie_2_4_0_is_de_centrale_publieke_versie():
    """Merge met main: DEF-768 (ESS-05) volgt als 2.4.0 op DEF-835 (2.3.0)."""
    from services.validation.interfaces import CONTRACT_VERSION

    assert CONTRACT_VERSION == "2.4.0"
    assert "Contractversie 2.4.0" in _schema()["description"]
    tekst = CONTRACTDOC.read_text(encoding="utf-8")
    assert "- **Versie**: 2.4.0 (SemVer)" in tekst
    assert "\n| 2.4.0 |" in tekst
    assert "\n| 2.3.0 |" in tekst


@pytest.mark.contract
@pytest.mark.parametrize("scenario", O2_SCENARIO_S)
def test_echte_int02_o2_uitkomst_past_in_het_schema(scenario):
    detail = _o2_detail(scenario)
    assert {"assessment", "signals"} <= set(detail)
    assert detail["score"] is None
    assert _schemafouten({"INT-02": detail}) == []


@pytest.mark.contract
def test_o2_schemadekking_omvat_alle_zes_statussen():
    statussen = {_o2_detail(s)["status"] for s in O2_SCENARIO_S}
    assert statussen == {
        "pass",
        "fail",
        "review_required",
        "not_evaluated",
        "error",
        "not_applicable",
    }


@pytest.mark.contract
@pytest.mark.parametrize(
    ("veld", "waarde"),
    [
        ("signals", "\\bmoet\\b"),
        ("signals", [1]),
        ("signals", None),
        ("assessment", "beoordeeld"),
        ("assessment", ["pass"]),
        ("score", 0.0),
    ],
)
def test_int02_velden_hebben_expliciete_typen(veld, waarde):
    detail = _o2_detail("fail")
    assert _schemafouten({"INT-02": detail}) == []
    assert _schemafouten({"INT-02": {**detail, veld: waarde}}), (veld, waarde)


@pytest.mark.contract
@pytest.mark.parametrize("assessment", [None, {}], ids=["null", "object"])
def test_schema_staat_int02_assessment_en_signals_toe(assessment):
    # Los van de evaluator: het schema zelf moet de 2.3.0-velden voor INT-02
    # aanvaarden (naast de echte uitvoer hierboven).
    uitkomst = {
        "status": "review_required",
        "score": None,
        "contract_version": None,
        "fingerprint": None,
        "parts": [],
        "review": None,
        "assessment": assessment,
        "signals": [],
    }
    assert _schemafouten({"INT-02": uitkomst}) == []


@pytest.mark.contract
def test_int02_assessment_null_en_lege_signalen_zijn_geldig():
    detail = _o2_detail("niet_beoordeeld")
    assert detail["assessment"] is None
    assert _schemafouten({"INT-02": {**detail, "signals": []}}) == []


@pytest.mark.contract
def test_onbekend_veld_in_int02_uitkomst_blijft_geweigerd():
    detail = _o2_detail("pass")
    fouten = _schemafouten({"INT-02": {**detail, "verzonnen_veld": True}})
    assert any("verzonnen_veld" in fout.message for fout in fouten)


@pytest.mark.contract
@pytest.mark.parametrize("regel", ["CON-01", "ESS-04", "INT-01"])
def test_assessment_en_signals_blijven_dicht_voor_andere_regels(regel):
    basis = {
        "status": "review_required",
        "score": None,
        "contract_version": None,
        "fingerprint": None,
        "parts": [],
        "review": None,
    }
    assert _schemafouten({regel: basis}) == []
    for veld, waarde in (("assessment", None), ("assessment", {}), ("signals", [])):
        assert _schemafouten({regel: {**basis, veld: waarde}}), (regel, veld)


@pytest.mark.contract
def test_echte_int02_uitkomst_onder_andere_regel_wordt_geweigerd():
    detail = _o2_detail("pass")
    assert _schemafouten({"ESS-04": detail})
    zonder = {k: v for k, v in detail.items() if k not in ("assessment", "signals")}
    assert _schemafouten({"ESS-04": zonder}) == []


@pytest.mark.contract
@pytest.mark.asyncio
async def test_bestaande_regeluitkomsten_blijven_geldig():
    resultaat = await _echt_resultaat()
    assert _schemafouten(resultaat["rule_results"]) == []


@pytest.mark.contract
def test_bestaande_int03_uitkomst_met_beoordeling_blijft_geldig():
    from services.validation.evaluators.base import EvaluationDeps
    from services.validation.evaluators.pronoun_reference_assessment import (
        PronounReferenceAssessmentEvaluator,
    )
    from services.validation.types_internal import EvaluationContext
    from tests.fixtures.def772_fakes import BINDING, bouw_int03_beoordeling
    from toetsregels.runtime_contract import (
        RequiredInput,
        build_rule_record,
        lees_regelbestand,
    )

    tekst = "Voorziening die een gebeurtenis vastlegt zodat die kan worden nagegaan."
    context = {"organisatorische_context": ["Synthetische Organisatie"]}
    record = build_rule_record("INT-03", lees_regelbestand(REGELS_MAP / "INT-03.json"))
    metadata = {
        **context,
        "record_text": tekst,
        "definition": {"toelichting": "Synthetische toelichting."},
        "int03_assessment": bouw_int03_beoordeling(
            "proefbegrip", tekst, context, "Synthetische toelichting."
        ),
        "int03_binding": BINDING.als_dict(),
    }
    uitkomst = PronounReferenceAssessmentEvaluator().evaluate(
        record,
        EvaluationContext(
            raw_text=tekst, cleaned_text=tekst, begrip="proefbegrip", metadata=metadata
        ),
        EvaluationDeps(support=None, available_inputs=frozenset(RequiredInput)),
    )
    detail = uitkomst.metadata["rule_result"]
    assert isinstance(detail["assessment"], dict)
    assert _schemafouten({"INT-03": detail}) == []


@pytest.mark.contract
def test_o1_ne_uitkomst_van_int02_blijft_geldig():
    from services.validation.evaluators.judgment_review import (
        int02_niet_uitgevoerd,
        int02_niet_uitgevoerd_uitkomst,
    )
    from toetsregels.runtime_contract import build_rule_record, lees_regelbestand

    record = build_rule_record("INT-02", lees_regelbestand(REGELS_MAP / "INT-02.json"))
    melding = int02_niet_uitgevoerd("", True)
    assert melding is not None
    detail = int02_niet_uitgevoerd_uitkomst(melding, record).metadata["rule_result"]
    assert _schemafouten({"INT-02": detail}) == []


@pytest.mark.contract
def test_typeddict_documenteert_int02_assessment_en_signals():
    import inspect

    from services.validation.interfaces import RuleResult

    assert {"assessment", "signals"} <= set(RuleResult.__annotations__)
    bron = inspect.getsource(RuleResult)
    assert "INT-02" in bron
    assert "INT-03" in bron
