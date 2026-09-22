"""ESS-03 (DEF-766): de geregistreerde evaluator en de normale validatieroute.

Echte regelrecords, echte `ModularValidationService` (beide regel-laadpaden),
geen provider: de AI-beoordeling is een synthetisch, contractconform en aan
de invoer gebonden document (`tests/fixtures/def766_fakes.py`). Wat deze
tests bewijzen: de vier inhoudelijke uitkomsten en de technische statussen
komen zonder cijfer en zonder verlies in het resultaat; zonder voorbereide
beoordeling is ESS-03 expliciet niet beoordeeld (nooit pass); een negatieve
uitkomst blokkeert de acceptatie niet en wijzigt niets aan de tekst.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from domain.ess03.contract import ONDERDEEL_TELBAARHEID, Intentie
from services.validation.evaluators.base import EvaluationDeps
from services.validation.evaluators.countability_assessment import (
    CountabilityAssessmentEvaluator,
)
from services.validation.evaluators.registry import get_default_registry
from services.validation.modular_validation_service import ModularValidationService
from services.validation.types_internal import EvaluationContext
from tests.fixtures.def766_fakes import BINDING, bouw_ess03_beoordeling
from toetsregels.manager import get_toetsregel_manager
from toetsregels.runtime_contract import (
    AutomationStatus,
    EvaluatorType,
    RequiredInput,
    ResultStatus,
    ScorePolicy,
    build_rule_record,
    load_root_contract_policy,
)

pytestmark = [pytest.mark.unit]

REGELS_DIR = Path(__file__).resolve().parents[3] / "src" / "toetsregels" / "regels"
ESS03 = build_rule_record(
    "ESS-03", json.loads((REGELS_DIR / "ESS-03.json").read_text(encoding="utf-8"))
)

BEGRIP = "eiland"
TEKST = (
    "Afzonderlijk aaneengesloten landoppervlak dat op het afgesproken peilmoment "
    "volledig door water is omgeven."
)
CONTEXT = {
    "organisatorische_context": ["Synthetisch Waterschap"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
TOELICHTING = "Synthetische conventie: elk gescheiden aaneengesloten vlak telt als één."


class _StubSupport:
    def severity_for(self, rule):
        return "error"

    def severity_level_for(self, rule):
        return "critical"

    def build_suggestion(self, code, rule, text, ctx, *, reason, details=None):
        return "stub"


def _deps() -> EvaluationDeps:
    return EvaluationDeps(
        support=_StubSupport(),
        available_inputs=frozenset(RequiredInput),
        pattern_cache={},
    )


def _metadata(assessment, *, tekst=TEKST, toelichting=TOELICHTING) -> dict:
    return {
        **CONTEXT,
        "record_text": tekst,
        "definition": {"toelichting": toelichting},
        "ess03_assessment": assessment,
        # R1: de wrapper geeft de actuele binding van de dienst mee.
        "ess03_binding": BINDING.als_dict(),
    }


def _ctx(metadata: dict, *, tekst=TEKST, begrip=BEGRIP) -> EvaluationContext:
    return EvaluationContext(
        raw_text=tekst, cleaned_text=tekst, begrip=begrip, metadata=metadata
    )


def _beoordeling(scenario: str, **over) -> dict:
    args = {
        "begrip": BEGRIP,
        "tekst": TEKST,
        "contexten": CONTEXT,
        "bronnen_ruw": None,
        "intentie": Intentie(toelichting=TOELICHTING),
    }
    args.update(over)
    return bouw_ess03_beoordeling(
        args["begrip"],
        args["tekst"],
        args["contexten"],
        args["bronnen_ruw"],
        intentie=args["intentie"],
        scenario=scenario,
    )


class TestRegelcontract:
    def test_ess03_wijst_de_telbaarheidsevaluator_aan_zonder_cijfer(self):
        assert ESS03.evaluator is EvaluatorType.COUNTABILITY_ASSESSMENT
        assert ESS03.required_inputs == (
            RequiredInput.DEFINITION_TEXT,
            RequiredInput.TERM,
        )
        assert ESS03.automation_status is AutomationStatus.AUTOMATED
        assert ESS03.score_policy is ScorePolicy.NO_SCORE
        assert ESS03.counts_toward_score is False

    def test_evaluator_is_geregistreerd(self):
        evaluator = get_default_registry().resolve(
            EvaluatorType.COUNTABILITY_ASSESSMENT
        )
        assert isinstance(evaluator, CountabilityAssessmentEvaluator)

    def test_niet_van_toepassing_is_een_contractstatus(self):
        assert ResultStatus.NOT_APPLICABLE.value == "not_applicable"
        assert ResultStatus.NOT_APPLICABLE.telt_mee_in_score is False
        policy = load_root_contract_policy()
        assert "not_applicable" in policy.result_status
        assert "countability_assessment" in policy.evaluators


class TestEvaluatorUitkomst:
    def test_zonder_beoordeling_is_de_regel_open_nooit_pass(self):
        uitkomst = CountabilityAssessmentEvaluator().evaluate(
            ESS03, _ctx(_metadata(None)), _deps()
        )
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert uitkomst.score is None
        assert uitkomst.violation is None
        assert "niet uitgevoerd" in (uitkomst.reason or "").lower()
        detail = uitkomst.metadata["rule_result"]
        assert detail["status"] == "review_required"
        assert detail["parts"][0]["id"] == ONDERDEEL_TELBAARHEID

    def test_pass_zonder_cijfer_met_gestructureerd_detail(self):
        uitkomst = CountabilityAssessmentEvaluator().evaluate(
            ESS03, _ctx(_metadata(_beoordeling("pass"))), _deps()
        )
        assert uitkomst.status is ResultStatus.PASS
        assert uitkomst.score is None
        detail = uitkomst.metadata["rule_result"]
        assert detail["status"] == "pass"
        assert detail["score"] is None
        assert detail["review"]["assessment"]["applied"] is True
        assert detail["review"]["assessment"]["model"] == "fake-ess03-model"

    def test_fail_is_zichtbaar_maar_niet_blokkerend(self):
        uitkomst = CountabilityAssessmentEvaluator().evaluate(
            ESS03, _ctx(_metadata(_beoordeling("fail"))), _deps()
        )
        assert uitkomst.status is ResultStatus.FAIL
        assert uitkomst.score is None
        violation = uitkomst.violation
        assert violation is not None
        assert violation["code"] == "ESS-03"
        # Besluit 21-09-2026: een negatieve ESS-03-uitkomst is geen blokkade.
        # De ernst wordt expliciet overschreven, ongeacht wat het record zegt.
        assert violation["severity"] == "warning"
        assert violation["severity_level"] == "medium"
        assert violation["metadata"]["advisory"] is True
        assert "AI-beoordeling" in violation["message"]
        assert uitkomst.metadata["rule_result"]["status"] == "fail"

    def test_niet_van_toepassing_is_eigen_status_geen_pass_geen_violation(self):
        uitkomst = CountabilityAssessmentEvaluator().evaluate(
            ESS03, _ctx(_metadata(_beoordeling("not_applicable"))), _deps()
        )
        assert uitkomst.status is ResultStatus.NOT_APPLICABLE
        assert uitkomst.score is None
        assert uitkomst.violation is None
        assert uitkomst.metadata["rule_result"]["status"] == "not_applicable"
        assert "geen afzonderlijke identificatie" in (
            uitkomst.metadata["rule_result"]["parts"][0]["reason"].lower()
        )

    def test_onvoldoende_informatie_is_open_met_precies_die_vraag(self):
        uitkomst = CountabilityAssessmentEvaluator().evaluate(
            ESS03, _ctx(_metadata(_beoordeling("insufficient"))), _deps()
        )
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert "Binnen welk register en welke populatie geldt het nummer?" in (
            uitkomst.reason or ""
        )
        detail = uitkomst.metadata["rule_result"]
        assert detail["review"]["assessment"]["verdict"] == "insufficient_information"
        assert detail["review"]["assessment"]["question"]

    def test_technische_fout_is_error_zonder_oordeel(self):
        uitkomst = CountabilityAssessmentEvaluator().evaluate(
            ESS03, _ctx(_metadata(_beoordeling("error"))), _deps()
        )
        assert uitkomst.status is ResultStatus.ERROR
        assert uitkomst.violation is None
        assert uitkomst.metadata["rule_result"]["status"] == "error"

    def test_niet_beschikbaar_is_open_met_reden(self):
        uitkomst = CountabilityAssessmentEvaluator().evaluate(
            ESS03, _ctx(_metadata(_beoordeling("unavailable"))), _deps()
        )
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert "geen dienst" in (uitkomst.reason or "")

    def test_lege_tekst_is_niet_geevalueerd(self):
        uitkomst = CountabilityAssessmentEvaluator().evaluate(
            ESS03, _ctx(_metadata(None, tekst="   "), tekst="   "), _deps()
        )
        assert uitkomst.status is ResultStatus.NOT_EVALUATED
        assert "definition_text" in (uitkomst.reason or "")

    def test_stale_beoordeling_geldt_niet_voor_gewijzigde_tekst(self):
        oud = _beoordeling("pass")
        nieuw_tekst = TEKST + " Aanvulling."
        uitkomst = CountabilityAssessmentEvaluator().evaluate(
            ESS03,
            _ctx(_metadata(oud, tekst=nieuw_tekst), tekst=nieuw_tekst),
            _deps(),
        )
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert "gewijzigd" in (uitkomst.reason or "")

    def test_gewijzigde_toelichting_maakt_beoordeling_stale(self):
        oud = _beoordeling("pass")
        uitkomst = CountabilityAssessmentEvaluator().evaluate(
            ESS03, _ctx(_metadata(oud, toelichting="Andere bedoeling.")), _deps()
        )
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED

    def test_verduidelijking_hoort_bij_de_binding(self):
        met = _beoordeling(
            "pass",
            intentie=Intentie(toelichting=TOELICHTING, verduidelijking="Peil P."),
        )
        metadata = {**_metadata(met), "ess03_verduidelijking": "Peil P."}
        uitkomst = CountabilityAssessmentEvaluator().evaluate(
            ESS03, _ctx(metadata), _deps()
        )
        assert uitkomst.status is ResultStatus.PASS
        # Zonder de verduidelijking hoort de beoordeling niet meer bij de invoer.
        uitkomst2 = CountabilityAssessmentEvaluator().evaluate(
            ESS03, _ctx(_metadata(met)), _deps()
        )
        assert uitkomst2.status is ResultStatus.REVIEW_REQUIRED

    def test_caller_supplied_pass_zonder_bewijs_telt_niet(self):
        doc = _beoordeling("pass")
        doc["judgment"]["evidence"] = []
        uitkomst = CountabilityAssessmentEvaluator().evaluate(
            ESS03, _ctx(_metadata(doc)), _deps()
        )
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        # Correctieronde 1 (R2/R3): een afgerond oordeel zonder bewijs is een
        # structuurfout van het document — het telt niet, met die reden.
        assert "zonder bewijs" in (uitkomst.reason or "")

    def test_bronnen_tellen_mee_in_de_binding(self):
        bron = {
            "provider": "documents",
            "doc_id": "conv-1",
            "snippet": "Elk gescheiden vlak telt als één.",
        }
        met_bron = _beoordeling("pass", bronnen_ruw=[bron])
        metadata = {**_metadata(met_bron), "provenance_sources": [bron]}
        uitkomst = CountabilityAssessmentEvaluator().evaluate(
            ESS03, _ctx(metadata), _deps()
        )
        assert uitkomst.status is ResultStatus.PASS
        zonder = CountabilityAssessmentEvaluator().evaluate(
            ESS03, _ctx(_metadata(met_bron)), _deps()
        )
        assert zonder.status is ResultStatus.REVIEW_REQUIRED


@pytest.fixture(
    scope="module", params=["toetsregel_manager", "cached_manager (productiepad)"]
)
def svc(request) -> ModularValidationService:
    if request.param.startswith("cached_manager"):
        from toetsregels.cached_manager import get_cached_toetsregel_manager
        from toetsregels.rule_cache import get_rule_cache

        get_rule_cache().clear_cache()
        manager = get_cached_toetsregel_manager()
    else:
        manager = get_toetsregel_manager()
    return ModularValidationService(manager, None, None)


def _ess03_violations(result: dict) -> list[dict]:
    return [v for v in result.get("violations", []) if v.get("code") == "ESS-03"]


class TestServiceRoute:
    async def test_zonder_voorbereide_beoordeling_is_ess03_expliciet_open(self, svc):
        result = await svc.validate_definition(begrip=BEGRIP, text=TEKST, context={})
        assert result["validation_status"] == "validated"
        assert result["rule_statuses"]["ESS-03"] == "review_required"
        assert "ESS-03" not in result["passed_rules"]
        assert _ess03_violations(result) == []
        detail = result["rule_results"]["ESS-03"]
        assert detail["status"] == "review_required"
        assert "niet uitgevoerd" in detail["parts"][0]["reason"].lower()
        assert result["overall_score"] is None

    async def test_pass_via_voorbereide_beoordeling_boekt_geen_cijfer(self, svc):
        result = await svc.validate_definition(
            begrip=BEGRIP, text=TEKST, context=_metadata(_beoordeling("pass"))
        )
        assert result["rule_statuses"]["ESS-03"] == "pass"
        assert "ESS-03" in result["passed_rules"]
        assert result["rule_results"]["ESS-03"]["status"] == "pass"
        assert result["overall_score"] is None
        assert result["detailed_scores"]["juridisch"] is None

    async def test_niet_van_toepassing_telt_apart_in_de_dekking(self, svc):
        result = await svc.validate_definition(
            begrip=BEGRIP,
            text=TEKST,
            context=_metadata(_beoordeling("not_applicable")),
        )
        assert result["rule_statuses"]["ESS-03"] == "not_applicable"
        assert "ESS-03" not in result["passed_rules"]
        assert _ess03_violations(result) == []
        assert not any(r["rule_id"] == "ESS-03" for r in result["review_required"])
        dekking = result["evaluation_coverage"]
        assert dekking["not_applicable"] == 1
        assert (
            dekking["passed"]
            + dekking["failed"]
            + dekking["review_required"]
            + dekking["not_evaluated"]
            + dekking["error"]
            + dekking["not_applicable"]
            == dekking["total"]
        )
        assert result["rule_results"]["ESS-03"]["status"] == "not_applicable"

    async def test_fail_is_zichtbaar_maar_verandert_de_acceptatie_niet(self, svc):
        basis = await svc.validate_definition(
            begrip=BEGRIP, text=TEKST, context=_metadata(_beoordeling("pass"))
        )
        negatief = await svc.validate_definition(
            begrip=BEGRIP, text=TEKST, context=_metadata(_beoordeling("fail"))
        )
        assert negatief["rule_statuses"]["ESS-03"] == "fail"
        [violation] = _ess03_violations(negatief)
        assert violation["severity"] == "warning"
        assert violation["severity_level"] == "medium"
        assert negatief["rule_results"]["ESS-03"]["status"] == "fail"
        # Zelfde acceptatie en dezelfde blokkadegronden als bij pass.
        assert negatief["is_acceptable"] == basis["is_acceptable"]
        assert negatief["acceptance_gate"]["gates_failed"] == (
            basis["acceptance_gate"]["gates_failed"]
        )
        assert negatief["acceptance_gate"].get("reasons") == (
            basis["acceptance_gate"].get("reasons")
        )
        # Geen cijfer geboekt: geen categoriecijfer voor 'juridisch'.
        assert negatief["detailed_scores"]["juridisch"] is None

    async def test_technische_fout_is_error_en_blokkeert_zoals_elke_error(self, svc):
        result = await svc.validate_definition(
            begrip=BEGRIP, text=TEKST, context=_metadata(_beoordeling("error"))
        )
        assert result["rule_statuses"]["ESS-03"] == "error"
        assert _ess03_violations(result) == []
        assert result["rule_results"]["ESS-03"]["status"] == "error"
        assert result["evaluation_coverage"]["error"] >= 1

    async def test_zonder_term_is_ess03_niet_geevalueerd_nooit_pass(self, svc):
        result = await svc.validate_definition(
            begrip="", text=TEKST, context=_metadata(_beoordeling("pass", begrip=""))
        )
        assert result["rule_statuses"]["ESS-03"] == "not_evaluated"
        assert "ESS-03" not in result["passed_rules"]

    async def test_lege_tekst_met_term_is_niet_geevalueerd(self, svc):
        result = await svc.validate_definition(begrip=BEGRIP, text="", context={})
        assert result["rule_statuses"]["ESS-03"] == "not_evaluated"
        assert result["rule_statuses"]["VAL-EMP-001"] == "fail"
