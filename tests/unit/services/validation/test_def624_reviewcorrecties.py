"""DEF-624 (deellevering 1) — correcties na de onafhankelijke Codex-review.

Vijf bevestigde bevindingen (/tmp/def624-codex-review-result.md), elk met
een gerichte regressietest die vóór de correctie rood was:

1. Een legacy `score=None` werd in de adapter alsnog 0.0 en reisde zo als
   opslaanbare nul door `to_ui_response` en `_opslaanbare_validatiescore`.
2. De fabriek accepteerde `validation_status="validation_unknown"` zonder
   `unknown_reason`: schema-ongeldig terwijl `is_valid_result` True gaf.
3. De canonieke `ValidationResult` (total=False) had geen enkele verplichte
   sleutel; de binding accepteerde wat het schema vereist.
4. Een werkelijk aanwezige ongeldige objectstatus (True/1/[]) werd door het
   str-filter als "ontbrekend" gemeld in plaats van "ongeldig".
5. Een expliciet `source_assessment=None` verdween bij objectconversie en
   legacy-dictnormalisatie door het dict-only-filter.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest
from jsonschema import Draft202012Validator, ValidationError

from integration.definitie_checker import (
    CheckAction,
    DefinitieChecker,
    DefinitieCheckResult,
    _opslaanbare_validatiescore,
)
from services.interfaces import (
    Definition,
    DefinitionResponseV2,
    ValidationResult as DataclassResult,
)
from services.service_factory import ServiceAdapter
from services.validation import interfaces, mappers, types
from services.validation.interfaces import (
    UNKNOWN_REASON_CONTRACT_STATUS_INVALID,
    UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
    UNKNOWN_REASON_RULESET_INCOMPLETE,
    UNKNOWN_REASON_VALIDATION_ERROR,
    VALIDATION_STATUS_UNKNOWN,
    VALIDATION_STATUS_VALIDATED,
    SystemMetadata,
    ValidationResult,
)
from services.validation.result_contract import (
    bepaal_runstatus,
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
READINESS = {
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


@pytest.fixture
def adapter() -> ServiceAdapter:
    container = MagicMock()
    container.orchestrator.return_value = MagicMock()
    return ServiceAdapter(container)


# ------------------------------------- 1. legacy score=None blijft None (keten)


LEGACY_NONE = {
    "score": None,
    "validation_status": VALIDATION_STATUS_VALIDATED,
    "is_acceptable": False,
    "violations": [],
    "passed_rules": ["CON-01"],
}


class _Converter:
    def to_dict(self) -> dict[str, Any]:
        return dict(LEGACY_NONE)


@dataclass
class _ObjectMetNoneScore:
    score: float | None = None
    is_acceptable: bool = False
    violations: list = field(default_factory=list)
    passed_rules: list = field(default_factory=list)
    validation_status: str = VALIDATION_STATUS_VALIDATED


def test_adapter_dictpad_behoudt_legacy_none_score(adapter) -> None:
    uit = adapter.normalize_validation(dict(LEGACY_NONE))
    assert uit["overall_score"] is None
    assert uit["validation_status"] == VALIDATION_STATUS_VALIDATED


def test_adapter_convertertak_behoudt_legacy_none_score(adapter) -> None:
    uit = adapter.normalize_validation(_Converter())
    assert uit["overall_score"] is None


def test_adapter_schemapad_en_attribuutfallback_behouden_none_score(
    adapter, monkeypatch
) -> None:
    assert adapter.normalize_validation(_ObjectMetNoneScore())["overall_score"] is None

    def _valt_om(*a: Any, **kw: Any) -> Any:
        raise ValueError("schemapad geforceerd uitgeschakeld")

    monkeypatch.setattr(mappers, "ensure_schema_compliance", _valt_om)
    uit = adapter.normalize_validation(_ObjectMetNoneScore())
    assert uit["overall_score"] is None
    assert uit["is_acceptable"] is False


def test_legacy_none_score_wordt_op_geen_enkele_route_een_opslaanbare_nul(
    adapter,
) -> None:
    """De volledige keten: adapter -> to_ui_response -> checker (beide routes)."""
    response = DefinitionResponseV2(
        success=True,
        definition=Definition(begrip="besluit", definitie="een beslissing"),
        validation_result=dict(LEGACY_NONE),  # type: ignore[arg-type]
    )
    ui = adapter.to_ui_response(response)

    assert ui["validation_details"]["overall_score"] is None
    assert ui["final_score"] is None
    assert _opslaanbare_validatiescore(ui) is None
    assert _opslaanbare_validatiescore(ui, standaard=0.0) is None

    class _Stub:
        async def generate_definition(self, *a: Any, **kw: Any) -> object:
            return object()

        def to_ui_response(self, response: Any) -> dict[str, Any]:
            return ui

    from domain.ontological_categories import OntologischeCategorie

    repo = MagicMock()
    repo.create_definitie.return_value = 42
    repo.update_definitie.return_value = True
    repo.get_definitie.return_value = MagicMock(
        begrip="besluit",
        categorie=OntologischeCategorie.TYPE.value,
        organisatorische_context="Gemeente",
        juridische_context="",
        version_number=1,
    )
    checker = DefinitieChecker(repository=repo)
    checker._get_integrated_service = lambda: _Stub()  # type: ignore[method-assign]
    checker.check_before_generation = lambda *a, **kw: DefinitieCheckResult(  # type: ignore[method-assign]
        action=CheckAction.PROCEED
    )
    checker.generate_with_check(
        begrip="besluit",
        organisatorische_context="Gemeente",
        categorie=OntologischeCategorie.TYPE,
        force_generate=True,
    )
    assert repo.create_definitie.call_args.args[0].validation_score is None
    checker.update_existing_definition(7, updated_by="tester", regenerate=True)
    assert repo.update_definitie.call_args.args[1]["validation_score"] is None


# ------------------------- 2. fabriek: expliciete unknown met vereiste metadata


def test_fabriek_unknown_met_reden_is_schemageldig_en_valid() -> None:
    uit = types.create_validation_result(
        overall_score=None,
        is_acceptable=False,
        correlation_id=CORRELATIE,
        validation_status=VALIDATION_STATUS_UNKNOWN,
        unknown_reason=UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
    )
    assert uit["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING
    assert "validation_readiness" not in uit, "readiness verzonnen"
    assert _schemageldig(uit)
    assert types.is_valid_result(uit)


def test_fabriek_ruleset_incomplete_met_readiness_is_schemageldig() -> None:
    uit = types.create_validation_result(
        overall_score=0.0,
        is_acceptable=False,
        correlation_id=CORRELATIE,
        validation_status=VALIDATION_STATUS_UNKNOWN,
        unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
        validation_readiness=dict(READINESS),  # type: ignore[arg-type]
    )
    assert uit["validation_readiness"] == READINESS
    assert _schemageldig(uit)
    assert types.is_valid_result(uit)


@pytest.mark.parametrize(
    ("kwargs", "melding"),
    [
        pytest.param(
            {"validation_status": VALIDATION_STATUS_UNKNOWN},
            "unknown_reason",
            id="zonder_reden",
        ),
        pytest.param(
            {
                "validation_status": VALIDATION_STATUS_UNKNOWN,
                "unknown_reason": UNKNOWN_REASON_RULESET_INCOMPLETE,
            },
            "validation_readiness",
            id="ruleset_incomplete_zonder_readiness",
        ),
        pytest.param(
            {
                "validation_status": VALIDATION_STATUS_VALIDATED,
                "unknown_reason": UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
            },
            "geen unknown_reason",
            id="validated_met_reden",
        ),
        pytest.param(
            {
                "validation_status": VALIDATION_STATUS_UNKNOWN,
                "unknown_reason": "verzonnen_reden",
            },
            "verzonnen_reden",
            id="onbekende_reden",
        ),
    ],
)
def test_fabriek_weigert_combinaties_waarvoor_geen_schemageldige_uitvoer_bestaat(
    kwargs: dict[str, Any], melding: str
) -> None:
    with pytest.raises(ValueError, match=melding):
        types.create_validation_result(
            overall_score=0.0, is_acceptable=False, correlation_id=CORRELATIE, **kwargs
        )


def test_fabriek_zonder_status_blijft_veilig_onbekend() -> None:
    uit = types.create_validation_result(overall_score=0.9, is_acceptable=True)
    assert uit["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert uit["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING
    assert _schemageldig(uit) and types.is_valid_result(uit)


def _handgebouwd(**extra: Any) -> dict[str, Any]:
    basis: dict[str, Any] = {
        "version": interfaces.CONTRACT_VERSION,
        "overall_score": 0.0,
        "is_acceptable": False,
        "violations": [],
        "passed_rules": [],
        "detailed_scores": {},
        "system": {"correlation_id": CORRELATIE},
    }
    basis.update(extra)
    return basis


@pytest.mark.parametrize(
    "instantie",
    [
        pytest.param(
            _handgebouwd(validation_status=VALIDATION_STATUS_UNKNOWN),
            id="unknown_zonder_reden",
        ),
        pytest.param(
            _handgebouwd(
                validation_status=VALIDATION_STATUS_UNKNOWN,
                unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
            ),
            id="ruleset_incomplete_zonder_readiness",
        ),
        pytest.param(
            _handgebouwd(
                validation_status=VALIDATION_STATUS_VALIDATED,
                unknown_reason=UNKNOWN_REASON_VALIDATION_ERROR,
            ),
            id="validated_met_reden",
        ),
        pytest.param(
            _handgebouwd(
                validation_status=VALIDATION_STATUS_UNKNOWN,
                unknown_reason=UNKNOWN_REASON_VALIDATION_ERROR,
            ),
            id="unknown_validation_error",
        ),
        pytest.param(
            _handgebouwd(
                validation_status=VALIDATION_STATUS_UNKNOWN,
                unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
                validation_readiness=dict(READINESS),
            ),
            id="ruleset_incomplete_met_readiness",
        ),
        pytest.param(
            _handgebouwd(
                validation_status=VALIDATION_STATUS_VALIDATED, overall_score=0.7
            ),
            id="validated",
        ),
        pytest.param(
            _handgebouwd(
                validation_status=VALIDATION_STATUS_UNKNOWN,
                unknown_reason="verzonnen_reden",
            ),
            id="onbekende_reden",
        ),
    ],
)
def test_is_valid_result_volgt_het_schema_voor_statuscombinaties(
    instantie: dict[str, Any],
) -> None:
    assert types.is_valid_result(instantie) == _schemageldig(instantie), instantie


# ---------------------------------- 3. verplichte sleutels in de typebinding


def test_verplichte_uitvoervelden_zijn_werkelijk_required() -> None:
    schema = _schema()
    assert ValidationResult.__required_keys__ == set(schema["required"])
    assert set(schema["properties"]) - set(schema["required"]) <= (
        ValidationResult.__optional_keys__
    )
    # De invoercontrole (vóór normalisatie) eist alles behalve de status:
    # die wordt aan de invoergrens gezet, niet geweigerd.
    assert (
        ValidationResult.__required_keys__ - {"validation_status"}
    ) == types._VALIDATION_RESULT_REQUIRED_KEYS
    assert SystemMetadata.__required_keys__ == set(
        schema["properties"]["system"]["required"]
    )


def test_fabrieken_leveren_alle_verplichte_sleutels() -> None:
    verplicht = ValidationResult.__required_keys__
    for uit in (
        mappers.create_degraded_result("boom", correlation_id=CORRELATIE),
        types.create_degraded_result("boom", correlation_id=CORRELATIE),
        types.create_validation_result(overall_score=0.5, is_acceptable=False),
        mappers.dataclass_to_schema_dict(
            DataclassResult(is_valid=True, definition_text="x", score=0.8)
        ),
        types.normalize_to_unified({"score": 0.5}),
    ):
        assert verplicht <= set(uit), sorted(verplicht - set(uit))


# ---------------------- 4. aanwezig-maar-ongeldig versus afwezig, over alle grenzen


@dataclass
class _Object:
    validation_status: Any = VALIDATION_STATUS_VALIDATED
    overall_score: float = 0.9
    is_acceptable: bool = True
    violations: list = field(default_factory=list)
    passed_rules: list = field(default_factory=list)


@dataclass
class _ObjectZonderStatus:
    overall_score: float = 0.9
    is_acceptable: bool = True
    violations: list = field(default_factory=list)
    passed_rules: list = field(default_factory=list)


ONGELDIG = [
    pytest.param(True, id="True"),
    pytest.param(1, id="1"),
    pytest.param([], id="lege_lijst"),
    pytest.param("VALIDATED", id="verkeerde_schrijfwijze"),
]


@pytest.mark.parametrize("waarde", ONGELDIG)
def test_ongeldige_status_is_overal_ongeldig_niet_ontbrekend(
    adapter, waarde: Any
) -> None:
    verwacht = UNKNOWN_REASON_CONTRACT_STATUS_INVALID
    assert bepaal_runstatus({"validation_status": waarde}).reason == verwacht
    assert bepaal_runstatus(_Object(validation_status=waarde)).reason == verwacht
    assert (
        met_expliciete_runstatus({"validation_status": waarde})["unknown_reason"]
        == verwacht
    )
    assert (
        mappers.dataclass_to_schema_dict(_Object(validation_status=waarde))[
            "unknown_reason"
        ]
        == verwacht
    )
    assert (
        types.normalize_to_unified(_Object(validation_status=waarde))["unknown_reason"]
        == verwacht
    )
    assert (
        types.normalize_to_unified({"score": 0.9, "validation_status": waarde})[
            "unknown_reason"
        ]
        == verwacht
    )
    assert (
        adapter.normalize_validation(_Object(validation_status=waarde))[
            "unknown_reason"
        ]
        == verwacht
    )


def test_afwezig_null_en_mock_verzinsels_blijven_ontbrekend(adapter) -> None:
    ontbreekt = UNKNOWN_REASON_CONTRACT_STATUS_MISSING
    assert bepaal_runstatus(_ObjectZonderStatus()).reason == ontbreekt
    assert bepaal_runstatus(_Object(validation_status=None)).reason == ontbreekt
    assert bepaal_runstatus({"validation_status": None}).reason == ontbreekt
    # Een Mock verzint elk opgevraagd attribuut: dat is geen aanwezige waarde.
    assert bepaal_runstatus(MagicMock()).reason == ontbreekt
    assert bepaal_runstatus(Mock(spec=[])).reason == ontbreekt
    assert adapter.normalize_validation(MagicMock())["unknown_reason"] == ontbreekt
    # Expliciet op een Mock gezet is wél werkelijk aanwezig.
    gezet = MagicMock()
    gezet.validation_status = True
    assert bepaal_runstatus(gezet).reason == UNKNOWN_REASON_CONTRACT_STATUS_INVALID


def test_ui_meldt_een_ongeldige_objectstatus_als_ongeldig(
    adapter, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ui.components import validation_view

    getoond: list[str] = []
    for api in ("markdown", "info", "warning", "success", "error", "write", "text"):
        monkeypatch.setattr(
            validation_view.st,
            api,
            lambda t, *a, **kw: getoond.append(str(t)),
            raising=False,
        )
    response = DefinitionResponseV2(
        success=True,
        definition=Definition(begrip="besluit", definitie="een beslissing"),
        validation_result=_Object(validation_status=True),  # type: ignore[arg-type]
    )
    details = adapter.to_ui_response(response)["validation_details"]
    validation_view.render_validation_detailed_list(
        details, key_prefix="review4", show_toggle=False
    )
    samen = "\n".join(getoond).lower()
    assert "ongeldig" in samen, getoond
    assert "ontbreekt" not in samen, getoond


# ------------------------ 5. expliciet source_assessment=None blijft behouden


@dataclass
class _MetLegeBeoordeling:
    validation_status: str = VALIDATION_STATUS_VALIDATED
    overall_score: float = 0.9
    is_acceptable: bool = True
    violations: list = field(default_factory=list)
    passed_rules: list = field(default_factory=list)
    source_assessment: dict | None = None


def test_expliciete_lege_bronbeoordeling_overleeft_elke_conversie(adapter) -> None:
    conversies = {
        "mappers_object": mappers.dataclass_to_schema_dict(_MetLegeBeoordeling()),
        "types_object": types.normalize_to_unified(_MetLegeBeoordeling()),
        "types_legacy_dict": types.normalize_to_unified(
            {
                "score": 0.9,
                "validation_status": VALIDATION_STATUS_VALIDATED,
                "source_assessment": None,
            }
        ),
        "adapter_object": adapter.normalize_validation(_MetLegeBeoordeling()),
        "adapter_dict": adapter.normalize_validation(
            {
                "overall_score": 0.9,
                "validation_status": VALIDATION_STATUS_VALIDATED,
                "source_assessment": None,
            }
        ),
    }
    for naam, uit in conversies.items():
        assert "source_assessment" in uit, naam
        assert uit["source_assessment"] is None, naam


def test_ontbrekende_bronbeoordeling_wordt_niet_verzonnen(adapter) -> None:
    for naam, uit in {
        "mappers_object": mappers.dataclass_to_schema_dict(_Object()),
        "types_object": types.normalize_to_unified(_Object()),
        "types_legacy_dict": types.normalize_to_unified({"score": 0.9}),
        "adapter_object": adapter.normalize_validation(_Object()),
        "adapter_dict": adapter.normalize_validation({"overall_score": 0.9}),
    }.items():
        assert "source_assessment" not in uit, naam


def test_lege_bronbeoordeling_idempotent_en_bron_ongewijzigd(adapter) -> None:
    bron = _MetLegeBeoordeling()
    kopie = deepcopy(bron)
    eerste = adapter.normalize_validation(bron)
    tweede = adapter.normalize_validation(eerste)
    assert bron == kopie
    assert tweede == eerste
    assert tweede["source_assessment"] is None
