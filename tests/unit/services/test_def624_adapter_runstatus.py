"""DEF-624: de adapter maakt een ontbrekende runstatus expliciet onbekend.

`ServiceAdapter.normalize_validation` is de enige weg van orchestrator naar de
Generator-tab. Het probe-bewijs bij de start van deze deellevering
(/tmp/def624-status-loss-probe.log): een resultaat zonder `validation_status`
kwam er als `overall_score 0.95 / is_acceptable True` doorheen — een groen
oordeel zonder enig runbewijs. DEF-621 koos destijds bewust om legacy niets
"op te dringen"; deze deellevering keert dat om: afwezig, null of ongeldig
wordt `validation_unknown` met een concrete contractreden.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest

from services.interfaces import (
    Definition,
    DefinitionResponseV2,
    ValidationResult as DataclassResult,
)
from services.service_factory import ServiceAdapter
from services.validation.interfaces import (
    UNKNOWN_REASON_CONTRACT_STATUS_INVALID,
    UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
    UNKNOWN_REASON_RULESET_INCOMPLETE,
    VALIDATION_STATUS_UNKNOWN,
    VALIDATION_STATUS_VALIDATED,
)

pytestmark = [pytest.mark.unit]


@pytest.fixture
def adapter() -> ServiceAdapter:
    container = MagicMock()
    container.orchestrator.return_value = MagicMock()
    return ServiceAdapter(container)


PROBE = {
    "overall_score": 0.95,
    "is_acceptable": True,
    "violations": [],
    "passed_rules": ["EXAMPLE"],
}


def test_probe_zonder_status_wordt_onbekend_en_niet_acceptabel(adapter) -> None:
    uit = adapter.normalize_validation(dict(PROBE))

    assert uit["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert uit["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING
    assert uit["is_acceptable"] is False
    assert uit["overall_score"] == 0.0
    # Wat de bron wél droeg blijft beschikbaar voor uitleg.
    assert uit["passed_rules"] == ["EXAMPLE"]
    assert "validation_readiness" not in uit


@pytest.mark.parametrize(
    ("status", "reden"),
    [
        (None, UNKNOWN_REASON_CONTRACT_STATUS_MISSING),
        ("VALIDATED", UNKNOWN_REASON_CONTRACT_STATUS_INVALID),
        (1, UNKNOWN_REASON_CONTRACT_STATUS_INVALID),
    ],
)
def test_null_en_ongeldige_status_krijgen_een_concrete_reden(
    adapter, status: Any, reden: str
) -> None:
    uit = adapter.normalize_validation({**PROBE, "validation_status": status})
    assert uit["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert uit["unknown_reason"] == reden
    assert uit["is_acceptable"] is False


def test_geen_resultaat_is_geen_run(adapter) -> None:
    uit = adapter.normalize_validation(None)
    assert uit["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert uit["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING
    assert uit["is_acceptable"] is False
    assert uit["violations"] == [] and uit["passed_rules"] == []


def test_validated_resultaat_blijft_validated_en_acceptabel(adapter) -> None:
    bron = {
        **PROBE,
        "validation_status": VALIDATION_STATUS_VALIDATED,
        "rule_statuses": {"CON-01": "pass"},
        "source_assessment": {"status": "assessed", "fingerprint": "abc"},
    }
    kopie = deepcopy(bron)

    uit = adapter.normalize_validation(bron)

    assert bron == kopie, "de adapter muteerde het bronresultaat"
    assert uit["validation_status"] == VALIDATION_STATUS_VALIDATED
    assert "unknown_reason" not in uit
    assert uit["is_acceptable"] is True
    assert uit["overall_score"] == 0.95
    assert uit["rule_statuses"] == {"CON-01": "pass"}
    assert uit["source_assessment"] == {"status": "assessed", "fingerprint": "abc"}


def test_bestaande_unknown_behoudt_reden_en_readiness(adapter) -> None:
    readiness = {
        "ready": False,
        "expected_total": 53,
        "loaded_total": 7,
        "missing_rule_ids": ["CON-01"],
        "unexpected_rule_ids": [],
    }
    uit = adapter.normalize_validation(
        {
            "validation_status": VALIDATION_STATUS_UNKNOWN,
            "unknown_reason": UNKNOWN_REASON_RULESET_INCOMPLETE,
            "validation_readiness": readiness,
            "overall_score": 0.0,
            "is_acceptable": False,
            "violations": [],
            "passed_rules": [],
        }
    )
    assert uit["unknown_reason"] == UNKNOWN_REASON_RULESET_INCOMPLETE
    assert uit["validation_readiness"] == readiness


def test_normalisatie_is_idempotent(adapter) -> None:
    eerste = adapter.normalize_validation(dict(PROBE))
    tweede = adapter.normalize_validation(eerste)
    assert tweede == eerste


def test_niet_beschikbare_score_blijft_none_ook_zonder_status(adapter) -> None:
    uit = adapter.normalize_validation({**PROBE, "overall_score": None})
    assert uit["overall_score"] is None
    assert uit["validation_status"] == VALIDATION_STATUS_UNKNOWN


@dataclass
class _LegacyObject:
    overall_score: float = 0.82
    is_acceptable: bool = True
    violations: list = field(default_factory=list)
    passed_rules: list = field(default_factory=list)


class _Converter:
    def to_dict(self) -> dict[str, Any]:
        return {"overall_score": 0.9, "is_acceptable": True, "violations": []}


@pytest.mark.parametrize(
    "bron",
    [
        pytest.param(_LegacyObject(), id="schemapad"),
        pytest.param(_Converter(), id="convertertak"),
        pytest.param(
            DataclassResult(is_valid=True, definition_text="x", score=0.9),
            id="legacy_dataclass",
        ),
        pytest.param(Mock(spec=[]), id="leeg_mock"),
        pytest.param(MagicMock(), id="magicmock"),
    ],
)
def test_legacy_objecten_zonder_status_zijn_onbekend(adapter, bron: Any) -> None:
    uit = adapter.normalize_validation(bron)
    assert uit["validation_status"] == VALIDATION_STATUS_UNKNOWN, bron
    assert uit["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING, bron
    assert uit["is_acceptable"] is False, bron


def test_attribuutfallback_maakt_de_status_ook_expliciet(adapter, monkeypatch) -> None:
    from services.validation import mappers

    def _valt_om(*a: Any, **kw: Any) -> Any:
        raise ValueError("schemapad geforceerd uitgeschakeld")

    monkeypatch.setattr(mappers, "ensure_schema_compliance", _valt_om)

    uit = adapter.normalize_validation(_LegacyObject())
    assert uit["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert uit["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING
    assert uit["is_acceptable"] is False


def test_ui_response_draagt_de_onbekende_status_naar_de_generator_tab(
    adapter,
) -> None:
    """Het pad dat de Generator-tab werkelijk rendert: `validation_details`."""
    response = DefinitionResponseV2(
        success=True,
        definition=Definition(begrip="besluit", definitie="een beslissing"),
        validation_result=dict(PROBE),  # type: ignore[arg-type]
    )

    ui = adapter.to_ui_response(response)

    details = ui["validation_details"]
    assert details["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert details["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING
    assert details["is_acceptable"] is False
    assert ui["final_score"] == 0.0

    from ui.components.definition_generator_tab import _validatie_is_onbepaald

    assert _validatie_is_onbepaald(ui) is True
