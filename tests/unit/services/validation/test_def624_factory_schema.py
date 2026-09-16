"""DEF-624 (deellevering 1) — correctieronde 2: factory/schema-consistentie.

Twee bevestigde restbevindingen uit de Codex-deltareview
(/tmp/def624-codex-deltareview-result.md):

A. `is_valid_result` keurde een unknown-resultaat met een groen oordeel
   (`is_acceptable=True`) of een niet-placeholderscore (0.95) goed, en de
   fabriek accepteerde bij `ruleset_incomplete` een lege
   `validation_readiness={}` — terwijl het schema vijf readinessvelden eist.
B. De fabriek wierp sinds correctieronde 1 een `ValueError` voor een
   ongeldige `validation_status` ("ok", True, 1, []); AC 1 eist aan de
   factorygrens juist een expliciete `validation_unknown` met
   `contract_status_invalid` via de centrale statusbepaling.

De grensmatrix hieronder vergelijkt `is_valid_result` met het ECHTE
JSON-schema voor status-, unknown- en readinessuitkomsten; de functie die
geldig claimt mag geen schema-ongeldig geval goedkeuren.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from services.validation import interfaces, types
from services.validation.interfaces import (
    UNKNOWN_REASON_CONTRACT_STATUS_INVALID,
    UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
    UNKNOWN_REASON_RULESET_INCOMPLETE,
    UNKNOWN_REASON_VALIDATION_ERROR,
    VALIDATION_STATUS_UNKNOWN,
    VALIDATION_STATUS_VALIDATED,
)
from services.validation.result_contract import met_expliciete_runstatus

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
READINESS: dict[str, Any] = {
    "ready": False,
    "expected_total": 53,
    "loaded_total": 7,
    "missing_rule_ids": ["CON-01"],
    "unexpected_rule_ids": [],
}


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PAD.read_text(encoding="utf-8"))


def _schemageldig(instantie: dict[str, Any]) -> bool:
    try:
        Draft202012Validator(_schema()).validate(instantie)
    except ValidationError:
        return False
    return True


def _resultaat(**extra: Any) -> dict[str, Any]:
    basis: dict[str, Any] = {
        "version": interfaces.CONTRACT_VERSION,
        "overall_score": 0.0,
        "is_acceptable": False,
        "violations": [],
        "passed_rules": [],
        "detailed_scores": {},
        "system": {"correlation_id": CORRELATIE},
        "validation_status": VALIDATION_STATUS_UNKNOWN,
        "unknown_reason": UNKNOWN_REASON_VALIDATION_ERROR,
    }
    basis.update(extra)
    return basis


def _zonder(resultaat: dict[str, Any], *sleutels: str) -> dict[str, Any]:
    for sleutel in sleutels:
        resultaat.pop(sleutel, None)
    return resultaat


def _readiness(**over: Any) -> dict[str, Any]:
    return {**deepcopy(READINESS), **over}


# --------------------------------------------- A. de twee reviewprobes exact


def test_probe_a1_unknown_met_groen_oordeel_en_echte_score_is_niet_geldig() -> None:
    probe = _resultaat(overall_score=0.95, is_acceptable=True)
    assert _schemageldig(probe) is False, "opzetfout: schema keurt de probe goed"
    assert types.is_valid_result(probe) is False


def test_probe_a2_lege_readiness_bij_ruleset_incomplete_wordt_geweigerd() -> None:
    with pytest.raises(ValueError, match="validation_readiness"):
        types.create_validation_result(
            overall_score=0.0,
            is_acceptable=False,
            correlation_id=CORRELATIE,
            validation_status=VALIDATION_STATUS_UNKNOWN,
            unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
            validation_readiness={},  # type: ignore[typeddict-item]
        )
    handgebouwd = _resultaat(
        unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE, validation_readiness={}
    )
    assert _schemageldig(handgebouwd) is False
    assert types.is_valid_result(handgebouwd) is False


# --------------------------------------------- B. ongeldige fabriekstatus


@pytest.mark.parametrize(
    "status",
    [
        pytest.param("ok", id="ok"),
        pytest.param(True, id="True"),
        pytest.param(1, id="1"),
        pytest.param([], id="lege_lijst"),
    ],
)
def test_probe_b_ongeldige_fabriekstatus_wordt_expliciet_onbekend(status: Any) -> None:
    uit = types.create_validation_result(
        overall_score=0.95,
        is_acceptable=True,
        correlation_id=CORRELATIE,
        validation_status=status,
    )
    assert uit["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert uit["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_INVALID
    assert uit["is_acceptable"] is False
    assert uit["overall_score"] == 0.0
    assert "validation_readiness" not in uit
    assert _schemageldig(uit) and types.is_valid_result(uit)


def test_fabriek_none_status_blijft_ontbrekend_en_none_score_blijft_none() -> None:
    uit = types.create_validation_result(
        overall_score=None, is_acceptable=True, correlation_id=CORRELATIE
    )
    assert uit["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING
    assert uit["overall_score"] is None
    assert uit["is_acceptable"] is False
    assert _schemageldig(uit) and types.is_valid_result(uit)


# ------------------------------- grensmatrix: is_valid_result == echt schema


MATRIX = [
    pytest.param(
        _zonder(
            _resultaat(
                validation_status=VALIDATION_STATUS_VALIDATED,
                overall_score=0.95,
                is_acceptable=True,
            ),
            "unknown_reason",
        ),
        True,
        id="validated_groen",
    ),
    pytest.param(
        _resultaat(validation_status=VALIDATION_STATUS_VALIDATED),
        False,
        id="validated_met_reden",
    ),
    pytest.param(_resultaat(), True, id="unknown_validation_error_placeholders"),
    pytest.param(_resultaat(is_acceptable=True), False, id="unknown_groen_oordeel"),
    pytest.param(_resultaat(overall_score=0.95), False, id="unknown_echte_score"),
    pytest.param(_resultaat(overall_score=None), True, id="unknown_score_none"),
    pytest.param(_resultaat(overall_score=False), False, id="unknown_score_bool"),
    pytest.param(
        _resultaat(unknown_reason=UNKNOWN_REASON_CONTRACT_STATUS_MISSING),
        True,
        id="unknown_status_missing",
    ),
    pytest.param(
        _resultaat(unknown_reason=UNKNOWN_REASON_CONTRACT_STATUS_INVALID),
        True,
        id="unknown_status_invalid",
    ),
    pytest.param(
        _resultaat(unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE),
        False,
        id="ruleset_incomplete_zonder_readiness",
    ),
    pytest.param(
        _resultaat(
            unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE, validation_readiness={}
        ),
        False,
        id="ruleset_incomplete_lege_readiness",
    ),
    pytest.param(
        _resultaat(
            unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
            validation_readiness=_zonder(_readiness(), "missing_rule_ids"),
        ),
        False,
        id="ruleset_incomplete_onvolledige_readiness",
    ),
    pytest.param(
        _resultaat(
            unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
            validation_readiness=_readiness(),
        ),
        True,
        id="ruleset_incomplete_geldige_readiness",
    ),
    pytest.param(
        _resultaat(
            unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
            validation_readiness=_readiness(extra="x"),
        ),
        False,
        id="readiness_extra_veld",
    ),
    pytest.param(
        _resultaat(
            unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
            validation_readiness=_readiness(ready="ja"),
        ),
        False,
        id="readiness_ready_geen_bool",
    ),
    pytest.param(
        _resultaat(
            unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
            validation_readiness=_readiness(expected_total="53"),
        ),
        False,
        id="readiness_totaal_string",
    ),
    pytest.param(
        _resultaat(
            unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
            validation_readiness=_readiness(loaded_total=-1),
        ),
        False,
        id="readiness_negatief_aantal",
    ),
    pytest.param(
        _resultaat(
            unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
            validation_readiness=_readiness(loaded_total=True),
        ),
        False,
        id="readiness_aantal_bool",
    ),
    pytest.param(
        _resultaat(
            unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
            validation_readiness=_readiness(missing_rule_ids="CON-01"),
        ),
        False,
        id="readiness_ids_geen_lijst",
    ),
    pytest.param(
        _resultaat(
            unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
            validation_readiness=_readiness(unexpected_rule_ids=[1]),
        ),
        False,
        id="readiness_ids_geen_strings",
    ),
    pytest.param(
        _zonder(
            _resultaat(
                validation_status=VALIDATION_STATUS_VALIDATED,
                validation_readiness=_readiness(ready=True, loaded_total=53),
            ),
            "unknown_reason",
        ),
        True,
        id="validated_met_geldige_readiness",
    ),
    pytest.param(
        _zonder(
            _resultaat(
                validation_status=VALIDATION_STATUS_VALIDATED, validation_readiness={}
            ),
            "unknown_reason",
        ),
        False,
        id="validated_met_lege_readiness",
    ),
    pytest.param(
        _zonder(_resultaat(), "unknown_reason"), False, id="unknown_zonder_reden"
    ),
    pytest.param(
        _resultaat(unknown_reason="verzonnen_reden"),
        False,
        id="unknown_onbekende_reden",
    ),
    pytest.param(
        _zonder(_resultaat(), "validation_status", "unknown_reason"),
        False,
        id="status_ontbreekt",
    ),
    pytest.param(
        _zonder(_resultaat(validation_status="ok"), "unknown_reason"),
        False,
        id="status_ongeldig",
    ),
]


@pytest.mark.parametrize(("instantie", "verwacht"), MATRIX)
def test_grensmatrix_is_valid_result_volgt_het_echte_schema(
    instantie: dict[str, Any], verwacht: bool
) -> None:
    assert (
        _schemageldig(instantie) is verwacht
    ), "opzetfout: schemaverwachting klopt niet"
    assert types.is_valid_result(instantie) is verwacht


# ------------------------------ fabriekmatrix: weigeren of schemageldig leveren


@pytest.mark.parametrize(
    "readiness",
    [
        pytest.param({}, id="leeg"),
        pytest.param(_zonder(_readiness(), "ready"), id="onvolledig"),
        pytest.param(_readiness(extra="x"), id="extra_veld"),
        pytest.param(_readiness(ready="ja"), id="ready_geen_bool"),
        pytest.param(_readiness(expected_total="53"), id="totaal_string"),
        pytest.param(_readiness(loaded_total=-1), id="negatief_aantal"),
        pytest.param(_readiness(missing_rule_ids="CON-01"), id="ids_geen_lijst"),
        pytest.param("kapot", id="geen_mapping"),
    ],
)
def test_fabriek_weigert_ongeldige_readiness(readiness: Any) -> None:
    with pytest.raises(ValueError, match="validation_readiness"):
        types.create_validation_result(
            overall_score=0.0,
            is_acceptable=False,
            correlation_id=CORRELATIE,
            validation_status=VALIDATION_STATUS_UNKNOWN,
            unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
            validation_readiness=readiness,
        )
    # Ook een expliciet validated resultaat draagt geen kapotte readiness.
    with pytest.raises(ValueError, match="validation_readiness"):
        types.create_validation_result(
            overall_score=0.9,
            is_acceptable=True,
            correlation_id=CORRELATIE,
            validation_status=VALIDATION_STATUS_VALIDATED,
            validation_readiness=readiness,
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param(
            {"validation_status": VALIDATION_STATUS_UNKNOWN}, id="unknown_zonder_reden"
        ),
        pytest.param(
            {
                "validation_status": VALIDATION_STATUS_UNKNOWN,
                "unknown_reason": UNKNOWN_REASON_RULESET_INCOMPLETE,
            },
            id="ruleset_incomplete_zonder_readiness",
        ),
        pytest.param(
            {
                "validation_status": VALIDATION_STATUS_VALIDATED,
                "unknown_reason": UNKNOWN_REASON_VALIDATION_ERROR,
            },
            id="validated_met_reden",
        ),
        pytest.param(
            {"validation_status": VALIDATION_STATUS_UNKNOWN, "unknown_reason": "x"},
            id="onbekende_reden",
        ),
        pytest.param(
            {
                "validation_status": "ok",
                "unknown_reason": UNKNOWN_REASON_VALIDATION_ERROR,
            },
            id="ongeldige_status_met_tegenstrijdige_reden",
        ),
        pytest.param(
            {"unknown_reason": UNKNOWN_REASON_VALIDATION_ERROR},
            id="geen_status_met_tegenstrijdige_reden",
        ),
    ],
)
def test_fabriek_weigert_tegenstrijdige_expliciete_metadata(
    kwargs: dict[str, Any],
) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - de combinatie is de boodschap
        types.create_validation_result(
            overall_score=0.0, is_acceptable=False, correlation_id=CORRELATIE, **kwargs
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param(
            {
                "validation_status": VALIDATION_STATUS_UNKNOWN,
                "unknown_reason": UNKNOWN_REASON_RULESET_INCOMPLETE,
                "validation_readiness": _readiness(),
            },
            id="ruleset_incomplete_geldig",
        ),
        pytest.param(
            {
                "validation_status": VALIDATION_STATUS_UNKNOWN,
                "unknown_reason": UNKNOWN_REASON_VALIDATION_ERROR,
            },
            id="validation_error",
        ),
        pytest.param(
            {
                "validation_status": VALIDATION_STATUS_UNKNOWN,
                "unknown_reason": UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
            },
            id="contract_status_missing",
        ),
        pytest.param(
            {
                "validation_status": VALIDATION_STATUS_UNKNOWN,
                "unknown_reason": UNKNOWN_REASON_CONTRACT_STATUS_INVALID,
            },
            id="contract_status_invalid",
        ),
        pytest.param(
            {
                "validation_status": "ok",
                "unknown_reason": UNKNOWN_REASON_CONTRACT_STATUS_INVALID,
            },
            id="ongeldige_status_met_passende_reden",
        ),
        pytest.param(
            {
                "validation_status": VALIDATION_STATUS_VALIDATED,
                "validation_readiness": _readiness(ready=True, loaded_total=53),
            },
            id="validated_met_geldige_readiness",
        ),
    ],
)
def test_fabriek_levert_voor_geldige_combinaties_schemageldige_uitvoer(
    kwargs: dict[str, Any],
) -> None:
    bewaard = deepcopy(kwargs)
    uit = types.create_validation_result(
        overall_score=0.95, is_acceptable=True, correlation_id=CORRELATIE, **kwargs
    )
    assert kwargs == bewaard, "de fabriek muteerde haar invoer"
    assert _schemageldig(uit), uit
    assert types.is_valid_result(uit)
    assert met_expliciete_runstatus(uit) == uit, "fabriekuitvoer is niet idempotent"
    if uit["validation_status"] == VALIDATION_STATUS_UNKNOWN:
        assert uit["is_acceptable"] is False and uit["overall_score"] == 0.0
    else:
        assert uit["is_acceptable"] is True and uit["overall_score"] == 0.95
