"""DEF-669: het register dekt het contract en violations hebben één vorm.

Twee reviewbevindingen op PR #397:

- bevinding 3: `abbreviation` en `definition_grammar` stonden in
  `EvaluatorType` én in de root-SSOT, maar hadden geen registratie. Een record
  dat er één declareert passeert alle contractvalidatie en klapt pas per
  evaluatie om in `ERROR` — waarna de regel via de dekking uit de noemer valt.
  `registered_types()` bestond al, maar werd nergens gebruikt.
- bevinding 4: vier evaluators bouwden hun violation-dict met de hand en dus
  verschillend. `compound` en `qualification` leverden geen `severity_level`,
  `ontological_category` hardcodeerde `"high"`, `lemma_morphology` leidde hem
  af. Consumers die op `severity_level` filteren kregen voor SAM-02 en SAM-04
  niets.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from services.validation.evaluators import (
    UnknownEvaluatorError,
    build_default_registry,
)
from services.validation.evaluators.base import EvaluationDeps
from services.validation.evaluators.compound import CompoundEvaluator
from services.validation.evaluators.deferred import DEFERRED_EVALUATORS
from services.validation.evaluators.lemma_morphology import LemmaMorphologyEvaluator
from services.validation.evaluators.ontological_category import (
    OntologicalCategoryEvaluator,
)
from services.validation.evaluators.qualification import QualificationEvaluator
from services.validation.modular_validation_service import ModularValidationService
from services.validation.types_internal import EvaluationContext
from toetsregels.manager import get_toetsregel_manager
from toetsregels.runtime_contract import (
    EvaluatorType,
    RequiredInput,
    ResultStatus,
    build_rule_records,
)

pytestmark = [pytest.mark.unit]

REGELS_DIR = Path(__file__).resolve().parents[3] / "src" / "toetsregels" / "regels"
RECORDS = build_rule_records(
    {
        pad.stem: json.loads(pad.read_text(encoding="utf-8"))
        for pad in REGELS_DIR.glob("*.json")
    }
)


class TestRegisterDektHetContract:
    def test_register_dekt_exact_de_toegestane_set(self):
        geregistreerd = build_default_registry().registered_types()
        toegestaan = {soort.value for soort in EvaluatorType}
        assert geregistreerd == toegestaan, (
            f"toegestaan maar ongeregistreerd: "
            f"{sorted(toegestaan - geregistreerd)} · geregistreerd maar niet "
            f"toegestaan: {sorted(geregistreerd - toegestaan)}"
        )

    def test_elk_toegestaan_type_is_oplosbaar(self):
        registry = build_default_registry()
        for soort in EvaluatorType:
            assert registry.resolve(soort) is not None, soort.value

    def test_onbekend_type_blijft_falen(self):
        # De negatieve kant. Zonder deze test zou de guard hierboven ook
        # "gehaald" worden door het register alles te laten accepteren.
        with pytest.raises(UnknownEvaluatorError):
            build_default_registry().resolve("verzonnen_evaluator")

    def test_uitgestelde_strategieen_dragen_een_eigenaar_issue(self):
        # Een uitgestelde evaluator is een dispositie, geen leegte (ALG-375):
        # zonder tracker-ID kan een gat stil blijven staan.
        import re

        zonder = [
            evaluator.evaluator_type.value
            for evaluator in DEFERRED_EVALUATORS
            if not re.fullmatch(r"DEF-\d+", str(evaluator.issue))
        ]
        assert not zonder, f"uitgestelde strategieën zonder DEF-issue: {zonder}"

    def test_uitgestelde_strategie_levert_not_evaluated(self):
        registry = build_default_registry()
        for soort in (EvaluatorType.ABBREVIATION, EvaluatorType.DEFINITION_GRAMMAR):
            uitkomst = registry.resolve(soort).evaluate(
                RECORDS["INT-07"],
                EvaluationContext(raw_text="x", cleaned_text="x", begrip="x"),
                _deps(),
            )
            assert uitkomst.status is ResultStatus.NOT_EVALUATED, soort.value
            assert "DEF-" in (uitkomst.reason or ""), uitkomst


class _StubSupport:
    """Alleen om te bewijzen dat de builder de support-afleiding gebruikt."""

    def severity_for(self, rule: dict[str, Any]) -> str:
        return "stub-severity"

    def severity_level_for(self, rule: dict[str, Any]) -> str:
        return "stub-level"

    def build_suggestion(self, code, rule, text, ctx, *, reason, details=None) -> str:
        return "stub-suggestie"


def _deps(support: Any | None = None) -> EvaluationDeps:
    return EvaluationDeps(
        support=support or _StubSupport(),
        available_inputs=frozenset(RequiredInput),
        pattern_cache={},
    )


def _verwachte_severity(rule: dict[str, Any]) -> tuple[str, str]:
    """De gedocumenteerde afleiding, hier onafhankelijk opgeschreven.

    Zou de verwachting `svc.severity_for` aanroepen, dan vergeleek de test de
    bron met zichzelf en kon de mapping ongemerkt verschuiven.
    """
    aanbeveling = str(rule.get("aanbeveling", "")).lower()
    prioriteit = str(rule.get("prioriteit", "")).lower()
    if aanbeveling == "verplicht" and prioriteit == "hoog":
        niveau = "critical"
    elif aanbeveling == "verplicht":
        niveau = "high"
    elif prioriteit == "hoog":
        niveau = "medium"
    else:
        niveau = "low"
    return ("error" if niveau in ("critical", "high") else "warning", niveau)


# Elk geval drijft precies één evaluator in zijn eigen FAIL-tak.
FAALGEVALLEN = [
    pytest.param(
        "SAM-04",
        CompoundEvaluator(),
        "procesmodel",
        "procesmodel: onbekende zaak zonder het genus vooraan",
        id="compound",
    ),
    pytest.param(
        "SAM-02",
        QualificationEvaluator(),
        "zwaar delict",
        "delict: een gedraging die strafbaar is gesteld",
        id="qualification",
    ),
    pytest.param(
        "ESS-02",
        OntologicalCategoryEvaluator(),
        "besluit",
        "besluit: iets waarvan de aard niet wordt benoemd",
        id="ontological_category",
    ),
    pytest.param(
        "VER-03",
        LemmaMorphologyEvaluator(),
        "beoordeelt",
        "beoordeelt: het vellen van een oordeel over iets",
        id="lemma_morphology",
    ),
]

VERPLICHTE_VIOLATIONVELDEN = frozenset(
    {
        "code",
        "severity",
        "severity_level",
        "message",
        "description",
        "rule_id",
        "category",
        "suggestion",
    }
)


def _violation_van(rule_id: str, evaluator: Any, begrip: str, tekst: str) -> dict:
    ctx = EvaluationContext(raw_text=tekst, cleaned_text=tekst, begrip=begrip)
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    uitkomst = evaluator.evaluate(RECORDS[rule_id], ctx, _deps(support=svc))
    assert uitkomst.status is ResultStatus.FAIL, (
        f"{rule_id}: dit geval raakt de FAIL-tak niet ({uitkomst.status.value}) — "
        f"de vormtest zou dan niets meten"
    )
    assert uitkomst.violation is not None, rule_id
    return uitkomst.violation


class TestViolationVormIsEen:
    """Alle vier evaluators leveren dezelfde violation-vorm."""

    @pytest.mark.parametrize(("rule_id", "evaluator", "begrip", "tekst"), FAALGEVALLEN)
    def test_verplichte_velden_zijn_aanwezig(self, rule_id, evaluator, begrip, tekst):
        violation = _violation_van(rule_id, evaluator, begrip, tekst)
        ontbreekt = sorted(VERPLICHTE_VIOLATIONVELDEN - set(violation))
        assert not ontbreekt, f"{rule_id}: violation mist {ontbreekt}"

    @pytest.mark.parametrize(("rule_id", "evaluator", "begrip", "tekst"), FAALGEVALLEN)
    def test_severity_komt_uit_het_regelrecord(self, rule_id, evaluator, begrip, tekst):
        violation = _violation_van(rule_id, evaluator, begrip, tekst)
        verwacht_severity, verwacht_niveau = _verwachte_severity(
            dict(RECORDS[rule_id].data)
        )
        assert violation["severity"] == verwacht_severity, rule_id
        assert violation["severity_level"] == verwacht_niveau, (
            f"{rule_id}: severity_level {violation['severity_level']!r} volgt niet "
            f"uit aanbeveling/prioriteit (verwacht {verwacht_niveau!r})"
        )

    def test_alle_vier_leveren_dezelfde_veldset(self):
        veldsets = {
            param.id: frozenset(_violation_van(*param.values)) for param in FAALGEVALLEN
        }
        unieke = set(veldsets.values())
        assert len(unieke) == 1, f"uiteenlopende veldsets per evaluator: {veldsets}"

    @pytest.mark.parametrize(("rule_id", "evaluator", "begrip", "tekst"), FAALGEVALLEN)
    def test_builder_gebruikt_de_support_afleiding(
        self, rule_id, evaluator, begrip, tekst
    ):
        # Met een stub-support moeten beide velden uit die stub komen. Zou een
        # evaluator zijn severity nog hardcoderen, dan staat hier de hardcode
        # in plaats van de stubwaarde.
        ctx = EvaluationContext(raw_text=tekst, cleaned_text=tekst, begrip=begrip)
        uitkomst = evaluator.evaluate(RECORDS[rule_id], ctx, _deps())
        assert uitkomst.violation is not None, rule_id
        assert uitkomst.violation["severity"] == "stub-severity", rule_id
        assert uitkomst.violation["severity_level"] == "stub-level", rule_id

    def test_ess02_hardcodeert_geen_niveau_meer(self):
        # Het concrete geval uit de review: ESS-02 is verplicht+hoog en droeg
        # toch het hardgecodeerde "high" in plaats van "critical".
        violation = _violation_van(
            "ESS-02",
            OntologicalCategoryEvaluator(),
            "besluit",
            "besluit: iets waarvan de aard niet wordt benoemd",
        )
        assert violation["severity_level"] == "critical", violation
