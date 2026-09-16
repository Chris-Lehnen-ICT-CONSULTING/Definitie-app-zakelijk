"""DEF-624 (deellevering 1): fail-closed resultaatcontract.

Een ontbrekende, null of ongeldige `validation_status` is geen uitgevoerd
validatiebewijs. Vóór deze wijziging declareerde het schema `default:
validated`, kopieerde de adapter alleen een aanwezige status door en
verzonnen de conversies geslaagde regels (`BASIC-00x`) en nullen voor een
niet-beschikbare score. Deze suite eist aan de dict-, legacy-object- en
fabriekgrenzen één expliciete onbekend-uitkomst met een concrete
contractreden, zonder verlies van wat de bron wél draagt.

Geen enkele conversie mag een run verzinnen: alleen een producent die
werkelijk evalueerde (ModularValidationService) zet `validated`.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, get_args

import pytest
from jsonschema import Draft202012Validator, ValidationError

from services.interfaces import ValidationResult as DataclassResult
from services.validation import interfaces, mappers, types
from services.validation.interfaces import (
    UNKNOWN_REASON_CONTRACT_STATUS_INVALID,
    UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
    UNKNOWN_REASON_RULESET_INCOMPLETE,
    UNKNOWN_REASON_VALIDATION_ERROR,
    VALIDATION_STATUS_UNKNOWN,
    VALIDATION_STATUS_VALIDATED,
    UnknownReason,
)
from services.validation.result_contract import (
    bepaal_runstatus,
    is_uitgevoerde_run,
    met_expliciete_runstatus,
)

pytestmark = [pytest.mark.unit]

SCHEMA_PAD = (
    Path(__file__).resolve().parents[4]
    / "docs"
    / "architectuur"
    / "contracts"
    / "schemas"
    / "validation_result.schema.json"
)
CORRELATIE = "3f8c1a2e-0000-4000-8000-000000000000"


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PAD.read_text(encoding="utf-8"))


def _resultaat(**extra: Any) -> dict[str, Any]:
    """Een schema-vormig resultaat mét hoge score en groen oordeel, zonder status."""
    basis: dict[str, Any] = {
        "version": interfaces.CONTRACT_VERSION,
        "overall_score": 0.95,
        "is_acceptable": True,
        "violations": [],
        "passed_rules": ["EXAMPLE"],
        "detailed_scores": {"taal": 0.95},
        "system": {"correlation_id": CORRELATIE},
    }
    basis.update(extra)
    return basis


def _volledig_validated() -> dict[str, Any]:
    """Alle velden die een conversie moet doordragen (AC 2)."""
    return _resultaat(
        validation_status=VALIDATION_STATUS_VALIDATED,
        rule_statuses={"CON-01": "pass", "VER-01": "error"},
        rule_results={
            "CON-01": {
                "status": "pass",
                "score": None,
                "contract_version": "con01/1",
                "fingerprint": "abc",
                "parts": [],
                "review": None,
            }
        },
        review_required=[
            {"rule_id": "ESS-01", "category": "taal", "reason": "open", "signals": []}
        ],
        evaluation_coverage={
            "evaluated": 1,
            "passed": 1,
            "failed": 0,
            "review_required": 1,
            "not_evaluated": 0,
            "error": 1,
            "total": 3,
            "coverage_ratio": 0.33,
        },
        source_assessment={"status": "assessed", "fingerprint": "abc"},
        acceptance_gate={"status": "pass", "acceptable": True},
    )


def _volledig_unknown() -> dict[str, Any]:
    return _resultaat(
        validation_status=VALIDATION_STATUS_UNKNOWN,
        unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
        validation_readiness={
            "ready": False,
            "expected_total": 53,
            "loaded_total": 7,
            "missing_rule_ids": ["CON-01"],
            "unexpected_rule_ids": [],
        },
        overall_score=0.0,
        is_acceptable=False,
        passed_rules=[],
        rule_statuses={},
        rule_results={},
        review_required=[],
        evaluation_coverage={
            "evaluated": 0,
            "passed": 0,
            "failed": 0,
            "review_required": 0,
            "not_evaluated": 53,
            "error": 0,
            "total": 53,
            "coverage_ratio": 0.0,
        },
        source_assessment=None,
    )


DOORGEDRAGEN_VELDEN = (
    "validation_status",
    "unknown_reason",
    "validation_readiness",
    "rule_statuses",
    "rule_results",
    "review_required",
    "evaluation_coverage",
    "source_assessment",
)


# ------------------------------------------------ AC 1: de gedeelde statusbepaling


@pytest.mark.parametrize(
    ("invoer", "reden"),
    [
        pytest.param({}, UNKNOWN_REASON_CONTRACT_STATUS_MISSING, id="afwezig"),
        pytest.param(
            {"validation_status": None},
            UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
            id="null",
        ),
        pytest.param(
            {"validation_status": "VALIDATED"},
            UNKNOWN_REASON_CONTRACT_STATUS_INVALID,
            id="verkeerde_schrijfwijze",
        ),
        pytest.param(
            {"validation_status": True},
            UNKNOWN_REASON_CONTRACT_STATUS_INVALID,
            id="boolean",
        ),
        pytest.param(
            {"validation_status": "ok"},
            UNKNOWN_REASON_CONTRACT_STATUS_INVALID,
            id="vreemde_waarde",
        ),
    ],
)
def test_afwezige_null_of_ongeldige_status_is_onbekend(
    invoer: dict[str, Any], reden: str
) -> None:
    runstatus = bepaal_runstatus(_resultaat(**invoer))

    assert runstatus.status == VALIDATION_STATUS_UNKNOWN
    assert runstatus.reason == reden
    assert runstatus.uitgevoerd is False
    assert is_uitgevoerde_run(_resultaat(**invoer)) is False


def test_validated_en_bestaande_unknown_blijven_wat_ze_zijn() -> None:
    gevalideerd = bepaal_runstatus(_volledig_validated())
    assert gevalideerd.status == VALIDATION_STATUS_VALIDATED
    assert gevalideerd.reason is None
    assert gevalideerd.uitgevoerd is True

    onbekend = bepaal_runstatus(_volledig_unknown())
    assert onbekend.status == VALIDATION_STATUS_UNKNOWN
    assert onbekend.reason == UNKNOWN_REASON_RULESET_INCOMPLETE


def test_hoge_score_en_groen_oordeel_omzeilen_de_onbekende_status_niet() -> None:
    """Het probe-geval: score 0.95 en is_acceptable True zonder status."""
    bron = _resultaat()
    uit = met_expliciete_runstatus(bron)

    assert uit["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert uit["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING
    assert uit["is_acceptable"] is False
    # De fail-closed placeholder van het bestaande contract (1.2.0): geen oordeel.
    assert uit["overall_score"] == 0.0
    # Geen readiness verzinnen: er is niets gemeten.
    assert "validation_readiness" not in uit


def test_statusobject_leest_alleen_werkelijke_attributen() -> None:
    """Een Mock verzint elk attribuut; alleen een str telt als status."""
    from unittest.mock import MagicMock

    @dataclass
    class MetStatus:
        validation_status: str = VALIDATION_STATUS_VALIDATED

    assert bepaal_runstatus(MetStatus()).uitgevoerd is True
    assert bepaal_runstatus(MagicMock()).reason == (
        UNKNOWN_REASON_CONTRACT_STATUS_MISSING
    )
    assert bepaal_runstatus(object()).uitgevoerd is False


# ------------------------------------- AC 2: behoud, immutabiliteit, idempotentie


@pytest.mark.parametrize("bron", [_volledig_validated(), _volledig_unknown()])
def test_normalisatie_verliest_geen_uitkomsten_en_raakt_de_bron_niet(
    bron: dict[str, Any],
) -> None:
    kopie = deepcopy(bron)

    uit = met_expliciete_runstatus(bron)

    assert bron == kopie, "de bron is gemuteerd"
    assert uit is not bron
    for veld in DOORGEDRAGEN_VELDEN:
        if veld in bron:
            assert uit[veld] == bron[veld], veld
    assert uit["is_acceptable"] == bron["is_acceptable"]
    assert uit["overall_score"] == bron["overall_score"]


@pytest.mark.parametrize(
    "bron", [_volledig_validated(), _volledig_unknown(), _resultaat()]
)
def test_herhaalde_normalisatie_is_idempotent(bron: dict[str, Any]) -> None:
    eerste = met_expliciete_runstatus(bron)
    tweede = met_expliciete_runstatus(eerste)
    assert tweede == eerste


def test_ensure_schema_compliance_muteert_de_invoer_niet() -> None:
    """Ook het aanvullen van een correlation_id gebeurt op een kopie."""
    bron = _resultaat(system={})
    kopie = deepcopy(bron)

    uit = mappers.ensure_schema_compliance(bron, correlation_id=CORRELATIE)

    assert bron == kopie
    assert uit["system"]["correlation_id"] == CORRELATIE
    assert uit["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert uit["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING


def test_ensure_schema_compliance_draagt_een_validated_resultaat_ongewijzigd_door() -> (
    None
):
    bron = _volledig_validated()
    uit = mappers.ensure_schema_compliance(bron)
    for veld in DOORGEDRAGEN_VELDEN:
        if veld in bron:
            assert uit[veld] == bron[veld], veld
    assert uit["is_acceptable"] is True
    assert uit["overall_score"] == 0.95


# ------------------------------------------- AC 1/3: legacy object en fabrieken


def test_legacy_dataclass_wordt_onbekend_zonder_verzonnen_regels() -> None:
    """De dataclass draagt geen runbewijs; `is_valid=True` maakt dat niet goed."""
    dc = DataclassResult(is_valid=True, definition_text="txt", score=0.8)

    uit = mappers.dataclass_to_schema_dict(dc, correlation_id=CORRELATIE)

    assert uit["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert uit["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING
    assert uit["is_acceptable"] is False
    assert uit["passed_rules"] == [], "conversie verzon geslaagde regels"


def test_legacy_object_met_status_en_uitkomsten_verliest_ze_niet() -> None:
    @dataclass
    class Producent:
        overall_score: float | None = None
        is_acceptable: bool = False
        violations: list = field(default_factory=list)
        passed_rules: list = field(default_factory=lambda: ["CON-01"])
        validation_status: str = VALIDATION_STATUS_VALIDATED
        rule_statuses: dict = field(default_factory=lambda: {"CON-01": "pass"})
        rule_results: dict = field(
            default_factory=lambda: {"CON-01": {"status": "pass", "score": None}}
        )
        review_required: list = field(default_factory=list)
        evaluation_coverage: dict = field(default_factory=lambda: {"total": 1})
        source_assessment: dict = field(default_factory=lambda: {"status": "assessed"})

    uit = mappers.dataclass_to_schema_dict(Producent(), correlation_id=CORRELATIE)

    assert uit["validation_status"] == VALIDATION_STATUS_VALIDATED
    assert uit["overall_score"] is None
    assert uit["rule_statuses"] == {"CON-01": "pass"}
    assert uit["rule_results"]["CON-01"]["status"] == "pass"
    assert uit["evaluation_coverage"] == {"total": 1}
    assert uit["source_assessment"] == {"status": "assessed"}
    assert uit["passed_rules"] == ["CON-01"]


def test_degraded_resultaat_is_expliciet_onbekend() -> None:
    """Een servicefout is geen run; de fabriek zegt dat zelf."""
    for fabriek in (mappers.create_degraded_result, types.create_degraded_result):
        uit = fabriek(error="boom", correlation_id=CORRELATIE)
        assert uit["validation_status"] == VALIDATION_STATUS_UNKNOWN, fabriek
        assert uit["unknown_reason"] == UNKNOWN_REASON_VALIDATION_ERROR, fabriek
        assert uit["is_acceptable"] is False
        assert uit["passed_rules"] == []


def test_fabriek_zonder_status_verzint_geen_run() -> None:
    zonder = types.create_validation_result(overall_score=0.9, is_acceptable=True)
    assert zonder["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert zonder["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING
    assert zonder["is_acceptable"] is False

    met = types.create_validation_result(
        overall_score=0.9,
        is_acceptable=True,
        validation_status=VALIDATION_STATUS_VALIDATED,
    )
    assert met["validation_status"] == VALIDATION_STATUS_VALIDATED
    assert met["is_acceptable"] is True
    assert "unknown_reason" not in met


@pytest.mark.parametrize(
    "legacy",
    [
        pytest.param({"score": 0.9, "is_valid": True}, id="dict"),
        pytest.param(
            DataclassResult(is_valid=True, definition_text="x", score=0.9),
            id="dataclass",
        ),
    ],
)
def test_normalize_to_unified_verzint_geen_run_en_geen_regels(legacy: Any) -> None:
    uit = types.normalize_to_unified(legacy, correlation_id=CORRELATIE)

    assert uit["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert uit["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING
    assert uit["is_acceptable"] is False
    assert uit["passed_rules"] == []
    assert types.is_valid_result(uit)


def test_normalize_to_unified_legacy_met_status_behoudt_die() -> None:
    uit = types.normalize_to_unified(
        {"score": 0.9, "is_valid": True, "validation_status": "validated"},
        correlation_id=CORRELATIE,
    )
    assert uit["validation_status"] == VALIDATION_STATUS_VALIDATED
    assert uit["is_acceptable"] is True
    assert uit["overall_score"] == 0.9


# ------------------------------------------------- AC 4: None blijft None


@pytest.mark.parametrize(
    "conversie",
    [
        pytest.param(
            lambda: types.normalize_to_unified({"score": None}), id="types_dict"
        ),
        pytest.param(
            lambda: types.normalize_to_unified(
                DataclassResult(is_valid=False, definition_text="x", score=None)
            ),
            id="types_dataclass",
        ),
        pytest.param(
            lambda: mappers.dataclass_to_schema_dict(
                DataclassResult(is_valid=False, definition_text="x", score=None)
            ),
            id="mappers_dataclass",
        ),
        pytest.param(
            lambda: mappers.ensure_schema_compliance(
                _resultaat(
                    overall_score=None, validation_status=VALIDATION_STATUS_VALIDATED
                )
            ),
            id="mappers_dict_validated",
        ),
        pytest.param(
            lambda: mappers.ensure_schema_compliance(_resultaat(overall_score=None)),
            id="mappers_dict_zonder_status",
        ),
    ],
)
def test_niet_beschikbare_score_wordt_nooit_nul(conversie: Any) -> None:
    assert conversie()["overall_score"] is None


def test_runstatus_is_onafhankelijk_van_het_kwaliteitsoordeel() -> None:
    """Een fail, een open review of een technische regelfout blijft `validated`."""
    bron = _volledig_validated()
    bron["is_acceptable"] = False
    bron["violations"] = [
        {
            "code": "VAL-STR-001",
            "severity": "error",
            "message": "fout",
            "rule_id": "STR-01",
            "category": "structuur",
        }
    ]
    uit = met_expliciete_runstatus(bron)
    assert uit["validation_status"] == VALIDATION_STATUS_VALIDATED
    assert uit["is_acceptable"] is False
    assert uit["rule_statuses"]["VER-01"] == "error"
    assert "unknown_reason" not in uit


# ------------------------------------- AC 3: type, schema en fabriek sluiten


def test_types_en_interfaces_delen_een_contractversie() -> None:
    assert types.CONTRACT_VERSION == interfaces.CONTRACT_VERSION
    assert types.ValidationResult is interfaces.ValidationResult
    assert (
        types.create_validation_result(
            overall_score=0.5,
            is_acceptable=False,
            validation_status=VALIDATION_STATUS_VALIDATED,
        )["version"]
        == interfaces.CONTRACT_VERSION
    )
    assert mappers.create_degraded_result("x")["version"] == interfaces.CONTRACT_VERSION


def test_schema_declareert_geen_default_en_eist_de_status() -> None:
    schema = _schema()
    assert "default" not in schema["properties"]["validation_status"]
    assert "validation_status" in schema["required"]
    assert interfaces.CONTRACT_VERSION in schema["description"]
    assert set(schema["properties"]["unknown_reason"]["enum"]) == set(
        get_args(UnknownReason)
    )
    assert set(get_args(UnknownReason)) == {
        UNKNOWN_REASON_RULESET_INCOMPLETE,
        UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
        UNKNOWN_REASON_CONTRACT_STATUS_INVALID,
        UNKNOWN_REASON_VALIDATION_ERROR,
    }


def test_schema_weigert_een_resultaat_zonder_status() -> None:
    with pytest.raises(ValidationError, match="validation_status"):
        Draft202012Validator(_schema()).validate(_resultaat())


@pytest.mark.parametrize(
    "bouw",
    [
        pytest.param(_volledig_validated, id="validated"),
        pytest.param(_volledig_unknown, id="unknown_ruleset_incomplete"),
        pytest.param(
            lambda: met_expliciete_runstatus(_resultaat()), id="unknown_status_missing"
        ),
        pytest.param(
            lambda: met_expliciete_runstatus(_resultaat(validation_status="ok")),
            id="unknown_status_invalid",
        ),
        pytest.param(
            lambda: met_expliciete_runstatus(_resultaat(overall_score=None)),
            id="unknown_score_none",
        ),
        pytest.param(
            lambda: mappers.create_degraded_result("boom", correlation_id=CORRELATIE),
            id="degraded",
        ),
        pytest.param(
            lambda: mappers.ensure_schema_compliance(
                mappers.dataclass_to_schema_dict(
                    DataclassResult(is_valid=True, definition_text="x", score=0.8),
                    correlation_id=CORRELATIE,
                )
            ),
            id="legacy_dataclass",
        ),
        pytest.param(
            lambda: types.create_validation_result(
                overall_score=0.7,
                is_acceptable=True,
                validation_status=VALIDATION_STATUS_VALIDATED,
                correlation_id=CORRELATIE,
            ),
            id="fabriek_validated",
        ),
    ],
)
def test_canonieke_gevallen_zijn_schemageldig(bouw: Any) -> None:
    Draft202012Validator(_schema()).validate(bouw())


def test_readiness_is_alleen_verplicht_bij_ruleset_incomplete() -> None:
    schema = Draft202012Validator(_schema())
    zonder_readiness = _resultaat(
        validation_status=VALIDATION_STATUS_UNKNOWN,
        unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
        overall_score=0.0,
        is_acceptable=False,
    )
    with pytest.raises(ValidationError, match="validation_readiness"):
        schema.validate(zonder_readiness)
    # Een ontbrekend contract heeft geen readinessmeting; die wordt niet verzonnen.
    schema.validate(
        _resultaat(
            validation_status=VALIDATION_STATUS_UNKNOWN,
            unknown_reason=UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
            overall_score=0.0,
            is_acceptable=False,
        )
    )


def test_schema_weigert_groen_oordeel_bij_onbekende_status() -> None:
    schema = Draft202012Validator(_schema())
    with pytest.raises(ValidationError):
        schema.validate(
            _resultaat(
                validation_status=VALIDATION_STATUS_UNKNOWN,
                unknown_reason=UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
                overall_score=0.0,
                is_acceptable=True,
            )
        )
    with pytest.raises(ValidationError):
        schema.validate(
            _resultaat(
                validation_status=VALIDATION_STATUS_VALIDATED,
                unknown_reason=UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
            )
        )


def test_typeddict_dekt_alle_schemavelden() -> None:
    schema = _schema()
    assert set(schema["properties"]) <= set(interfaces.ValidationResult.__annotations__)


def test_historisch_schema_1_4_0_blijft_gepind() -> None:
    gepind = SCHEMA_PAD.with_name("validation_result_v1.4.0.schema.json")
    assert gepind.exists(), "het vorige contract hoort gepind te blijven"
    oud = json.loads(gepind.read_text(encoding="utf-8"))
    assert "1.4.0" in oud["description"]
    assert oud["properties"]["validation_status"].get("default") == "validated"
