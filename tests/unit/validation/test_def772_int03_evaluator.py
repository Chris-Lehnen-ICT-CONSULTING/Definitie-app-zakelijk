"""DEF-772 WP3: de geregistreerde INT-03-evaluator en de normale validatieroute.

Echte regelrecords, echte `ModularValidationService` (beide laadpaden:
ToetsregelManager en CachedToetsregelManager → RuleCache), geen provider: de
AI-beoordeling is een synthetisch, contractconform en aan de invoer gebonden
document (`tests/fixtures/def772_fakes.py`).

Wat deze tests bewijzen:

- het INT-03-record wijst de eigen evaluator aan: `automated`, `judgment`,
  `excluded_from_score`, alleen `definition_text` vereist (de term is
  ondersteunend), en de evaluator staat in het register én de root-SSOT;
- de uitkomstcategorieën komen zonder cijfer en zonder verlies in het
  resultaat: pass / pass-met-K7-motivering / fail (advisory) / open met
  precies één vraag / error / niet beoordeeld (lege tekst);
- zonder voorbereide beoordeling (directe service-aanroep) is INT-03
  expliciet niet beoordeeld — nooit een stil pass, ook zonder signaalwoord;
- een caller-supplied of verouderde beoordeling (andere tekst, toelichting,
  context, binding, verzonnen citaat) telt niet;
- scorepolicy en advisory-severity lopen werkelijk door de resultaatmappers:
  een negatieve uitkomst is zichtbaar (violation warning/medium) maar
  verandert de categoriecijfers, de acceptatie en de gate niet, en de regel
  krijgt een `rule_results`-blok met score `None`.

Geen aanspraak op modelkwaliteit: de fake bepaalt de uitkomst.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from domain.int03.contract import (
    BEVINDING_GEEN_VERWIJZEND_WOORD,
    BEVINDING_MEERDUIDIG,
    MOTIVERING_GEEN_VERWIJZEND_WOORD,
    ONDERDEEL_VERWIJZING,
    VERWIJZING_DUIDELIJK,
    VERWIJZING_MEERDUIDIG,
)
from services.validation.evaluators.base import EvaluationDeps
from services.validation.evaluators.pronoun_reference_assessment import (
    ADVISORY_SEVERITY,
    ADVISORY_SEVERITY_LEVEL,
    PronounReferenceAssessmentEvaluator,
)
from services.validation.evaluators.registry import get_default_registry
from services.validation.modular_validation_service import ModularValidationService
from services.validation.types_internal import EvaluationContext
from tests.fixtures.def772_fakes import BINDING, MODEL, bouw_int03_beoordeling
from toetsregels.manager import get_toetsregel_manager
from toetsregels.runtime_contract import (
    AutomationStatus,
    EvaluatorType,
    ExamplePairPolicy,
    Executability,
    RequiredInput,
    ResultStatus,
    ScorePolicy,
    build_rule_record,
    load_root_contract_policy,
)

pytestmark = [pytest.mark.unit]

REGELS_DIR = Path(__file__).resolve().parents[3] / "src" / "toetsregels" / "regels"
INT03 = build_rule_record(
    "INT-03", json.loads((REGELS_DIR / "INT-03.json").read_text(encoding="utf-8"))
)

TERM = "proefbegrip"
ASTRA_GOED = (
    "Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die "
    "de basis vormen waardoor die gebeurtenis volledig kan worden begrepen en "
    "geanalyseerd."
)
ASTRA_FOUT = (
    "Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die "
    "de basis vormen waardoor het volledig kan worden begrepen en geanalyseerd."
)
GEEN_WOORD = "veelhoek met precies drie zijden"
HET_VOORTGEZET = "voorziening waardoor het kan worden voortgezet"
CONTEXT = {
    "organisatorische_context": ["Synthetische Organisatie"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
TOELICHTING = "Synthetische toelichting."

#: ASTRA-fout als synthetisch modelantwoord: 'het' met twee plausibele lezingen.
VERWIJZING_HET_ASTRA = [
    {
        "word": "het",
        "passage": "waardoor het volledig kan worden begrepen",
        "status": VERWIJZING_MEERDUIDIG,
        "reading": "twee plausibele lezingen",
        "candidates": [
            {"quote": "Geheel", "reason": "onzijdig onderwerp van de zin"},
            {"quote": "gebeurtenis", "reason": "dichtstbijzijnd naamwoord"},
        ],
    }
]


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


def _metadata(
    assessment, *, tekst=ASTRA_GOED, toelichting=TOELICHTING, binding=True
) -> dict:
    metadata = {
        **CONTEXT,
        "record_text": tekst,
        "definition": {"toelichting": toelichting},
        "int03_assessment": assessment,
    }
    if binding:
        metadata["int03_binding"] = BINDING.als_dict()
    return metadata


def _ctx(metadata: dict, *, tekst=ASTRA_GOED, begrip=TERM) -> EvaluationContext:
    return EvaluationContext(
        raw_text=tekst, cleaned_text=tekst, begrip=begrip, metadata=metadata
    )


def _beoordeling(scenario: str, *, tekst=ASTRA_GOED, **over) -> dict:
    return bouw_int03_beoordeling(
        over.pop("begrip", TERM),
        tekst,
        over.pop("contexten", CONTEXT),
        over.pop("toelichting", TOELICHTING),
        scenario=scenario,
        **over,
    )


def _evalueer(metadata: dict, *, tekst=ASTRA_GOED, begrip=TERM):
    return PronounReferenceAssessmentEvaluator().evaluate(
        INT03, _ctx(metadata, tekst=tekst, begrip=begrip), _deps()
    )


# ---------------------------------------------------------------------------
# Regelcontract en register
# ---------------------------------------------------------------------------


class TestRegelcontract:
    def test_int03_wijst_de_verwijzingsevaluator_aan_zonder_cijfer(self):
        assert INT03.evaluator is EvaluatorType.PRONOUN_REFERENCE_ASSESSMENT
        # De term is ondersteunend, geen vereiste invoer.
        assert INT03.required_inputs == (RequiredInput.DEFINITION_TEXT,)
        assert INT03.executability is Executability.JUDGMENT
        assert INT03.automation_status is AutomationStatus.AUTOMATED
        assert INT03.score_policy is ScorePolicy.EXCLUDED_FROM_SCORE
        assert INT03.counts_toward_score is False
        assert INT03.example_pair_policy is ExamplePairPolicy.REVIEW_POLICY
        assert INT03.example_pair_issue == "DEF-772"

    def test_evaluator_is_geregistreerd_en_in_de_root_ssot(self):
        evaluator = get_default_registry().resolve(
            EvaluatorType.PRONOUN_REFERENCE_ASSESSMENT
        )
        assert isinstance(evaluator, PronounReferenceAssessmentEvaluator)
        assert "pronoun_reference_assessment" in load_root_contract_policy().evaluators

    def test_advisory_ernst_is_gelijk_aan_ess03(self):
        from services.validation.evaluators import countability_assessment as ess03

        assert (ADVISORY_SEVERITY, ADVISORY_SEVERITY_LEVEL) == (
            ess03.ADVISORY_SEVERITY,
            ess03.ADVISORY_SEVERITY_LEVEL,
        )


# ---------------------------------------------------------------------------
# Evaluator: uitkomstcategorieën
# ---------------------------------------------------------------------------


class TestEvaluatorUitkomst:
    def test_zonder_beoordeling_is_de_regel_open_nooit_pass(self):
        uitkomst = _evalueer(_metadata(None))
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert uitkomst.score is None
        assert uitkomst.violation is None
        assert "niet beoordeeld" in (uitkomst.reason or "")
        detail = uitkomst.metadata["rule_result"]
        assert detail["status"] == "review_required"
        assert detail["score"] is None
        assert detail["parts"][0]["id"] == ONDERDEEL_VERWIJZING

    def test_zonder_signaalwoord_en_zonder_beoordeling_geen_pass(self):
        # K7 komt pas ná de LLM-controle, nooit op een lege patroonlijst.
        uitkomst = _evalueer(_metadata(None, tekst=GEEN_WOORD), tekst=GEEN_WOORD)
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert uitkomst.metadata["rule_result"]["signals"] == []

    def test_pass_zonder_cijfer_met_gestructureerd_detail(self):
        uitkomst = _evalueer(_metadata(_beoordeling("pass")))
        assert uitkomst.status is ResultStatus.PASS
        assert uitkomst.score is None
        detail = uitkomst.metadata["rule_result"]
        assert detail["status"] == "pass"
        assert detail["review"]["assessment"]["applied"] is True
        assert detail["review"]["assessment"]["model"] == MODEL
        assert detail["assessment"]["status"] == "assessed"

    def test_geen_verwijzend_woord_is_pass_met_exacte_motivering(self):
        uitkomst = _evalueer(
            _metadata(_beoordeling("no_word", tekst=GEEN_WOORD), tekst=GEEN_WOORD),
            tekst=GEEN_WOORD,
        )
        assert uitkomst.status is ResultStatus.PASS
        detail = uitkomst.metadata["rule_result"]
        assert detail["parts"][0]["reason"] == MOTIVERING_GEEN_VERWIJZEND_WOORD
        assert detail["review"]["assessment"]["finding"] == (
            BEVINDING_GEEN_VERWIJZEND_WOORD
        )

    def test_fail_is_zichtbaar_maar_niet_blokkerend(self):
        uitkomst = _evalueer(
            _metadata(
                _beoordeling(
                    "fail", tekst=ASTRA_FOUT, verwijzingen=VERWIJZING_HET_ASTRA
                ),
                tekst=ASTRA_FOUT,
            ),
            tekst=ASTRA_FOUT,
        )
        assert uitkomst.status is ResultStatus.FAIL
        assert uitkomst.score is None
        violation = uitkomst.violation
        assert violation is not None
        assert violation["code"] == "INT-03"
        assert violation["severity"] == "warning"
        assert violation["severity_level"] == "medium"
        assert violation["metadata"]["advisory"] is True
        assert violation["metadata"]["finding"] == BEVINDING_MEERDUIDIG
        assert "'het'" in violation["message"]
        assert uitkomst.metadata["rule_result"]["status"] == "fail"

    def test_fail_zonder_antecedent(self):
        uitkomst = _evalueer(
            _metadata(
                _beoordeling("no_antecedent", tekst=HET_VOORTGEZET),
                tekst=HET_VOORTGEZET,
            ),
            tekst=HET_VOORTGEZET,
        )
        assert uitkomst.status is ResultStatus.FAIL
        assert "geen antecedent" in (uitkomst.violation or {})["message"].lower()

    def test_onvoldoende_informatie_is_open_met_precies_die_vraag(self):
        uitkomst = _evalueer(
            _metadata(
                _beoordeling(
                    "insufficient", tekst=ASTRA_FOUT, vraag="Waarnaar verwijst 'het'?"
                ),
                tekst=ASTRA_FOUT,
            ),
            tekst=ASTRA_FOUT,
        )
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert "Waarnaar verwijst 'het'?" in (uitkomst.reason or "")
        detail = uitkomst.metadata["rule_result"]
        assert detail["review"]["assessment"]["verdict"] == "insufficient_information"
        assert detail["review"]["assessment"]["question"] == "Waarnaar verwijst 'het'?"

    def test_technische_fout_is_error_zonder_oordeel(self):
        uitkomst = _evalueer(_metadata(_beoordeling("error")))
        assert uitkomst.status is ResultStatus.ERROR
        assert uitkomst.violation is None
        assert uitkomst.metadata["rule_result"]["status"] == "error"

    def test_niet_beschikbaar_is_open_met_reden(self):
        uitkomst = _evalueer(_metadata(_beoordeling("unavailable")))
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert "geen dienst" in (uitkomst.reason or "")

    def test_lege_tekst_is_niet_geevalueerd(self):
        uitkomst = _evalueer(_metadata(None, tekst="   "), tekst="   ")
        assert uitkomst.status is ResultStatus.NOT_EVALUATED
        assert "definition_text" in (uitkomst.reason or "")

    def test_zonder_term_wordt_wel_beoordeeld(self):
        # De term is ondersteunend: zonder term blijft de definitie het toetsobject.
        uitkomst = _evalueer(_metadata(_beoordeling("pass", begrip="")), begrip="")
        assert uitkomst.status is ResultStatus.PASS


class TestBinding:
    def test_stale_beoordeling_geldt_niet_voor_gewijzigde_tekst(self):
        nieuw = ASTRA_GOED + " Aanvulling."
        uitkomst = _evalueer(_metadata(_beoordeling("pass"), tekst=nieuw), tekst=nieuw)
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert "gewijzigd" in (uitkomst.reason or "")

    def test_gewijzigde_toelichting_maakt_beoordeling_stale(self):
        uitkomst = _evalueer(
            _metadata(_beoordeling("pass"), toelichting="Andere bedoeling.")
        )
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED

    def test_gewijzigde_context_maakt_beoordeling_stale(self):
        metadata = _metadata(_beoordeling("pass"))
        metadata["juridische_context"] = ["Strafrecht"]
        uitkomst = _evalueer(metadata)
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED

    def test_zonder_binding_van_de_wrapper_geen_actueel_oordeel(self):
        uitkomst = _evalueer(_metadata(_beoordeling("pass"), binding=False))
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert "binding" in (uitkomst.reason or "")

    def test_caller_supplied_pass_met_verzonnen_citaat_telt_niet(self):
        doc = _beoordeling("pass")
        doc["judgment"]["references"] = [
            {
                "word": "zij",
                "passage": "zij vertrekt",
                "status": VERWIJZING_DUIDELIJK,
                "reading": "verzonnen",
                "candidates": [],
            }
        ]
        uitkomst = _evalueer(_metadata(doc))
        # R4: een niet-verifieerbare beoordeling is een technische fout, geen
        # open reviewpunt; R2: het verzonnen citaat staat niet in de reden.
        assert uitkomst.status is ResultStatus.ERROR
        assert "bruikbaar" in (uitkomst.reason or "")
        assert "zij vertrekt" not in (uitkomst.reason or "")

    def test_ander_model_is_historisch(self):
        uitkomst = _evalueer(_metadata(_beoordeling("pass", model="ander-model")))
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert "historisch" in (uitkomst.reason or "")


class TestSignaalhulp:
    def test_signalen_komen_uit_het_record_en_zijn_geen_oordeel(self):
        # K4: de patronen zijn zoekhulp; zij reizen mee in het detail, maar de
        # status volgt uitsluitend uit de beoordeling.
        uitkomst = _evalueer(_metadata(None, tekst=ASTRA_FOUT), tekst=ASTRA_FOUT)
        signalen = uitkomst.metadata["rule_result"]["signals"]
        assert r"\bhet\b" in signalen
        assert set(signalen) <= set(INT03.get("herkenbaar_patronen"))
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert uitkomst.metadata["signals"] == signalen
        # Met een positieve beoordeling blijft het signaal een signaal.
        goed = _evalueer(_metadata(_beoordeling("pass")))
        assert goed.status is ResultStatus.PASS
        assert r"\bdie\b(?!\s+(begrip|definitie|regel))" in (
            goed.metadata["rule_result"]["signals"]
        )


# ---------------------------------------------------------------------------
# Normale validatieroute — beide laadpaden
# ---------------------------------------------------------------------------


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


def _int03_violations(result: dict) -> list[dict]:
    return [v for v in result.get("violations", []) if v.get("code") == "INT-03"]


class TestServiceRoute:
    async def test_zonder_voorbereide_beoordeling_is_int03_expliciet_open(self, svc):
        result = await svc.validate_definition(begrip=TERM, text=ASTRA_GOED, context={})
        assert result["validation_status"] == "validated"
        assert result["rule_statuses"]["INT-03"] == "review_required"
        assert "INT-03" not in result["passed_rules"]
        assert _int03_violations(result) == []
        detail = result["rule_results"]["INT-03"]
        assert detail["status"] == "review_required"
        assert detail["score"] is None
        assert "niet beoordeeld" in detail["parts"][0]["reason"]
        item = next(r for r in result["review_required"] if r["rule_id"] == "INT-03")
        assert "niet beoordeeld" in item["reason"]

    async def test_pass_via_voorbereide_beoordeling_boekt_geen_cijfer(self, svc):
        result = await svc.validate_definition(
            begrip=TERM, text=ASTRA_GOED, context=_metadata(_beoordeling("pass"))
        )
        assert result["rule_statuses"]["INT-03"] == "pass"
        assert "INT-03" in result["passed_rules"]
        assert result["rule_results"]["INT-03"]["status"] == "pass"
        assert result["rule_results"]["INT-03"]["score"] is None

    async def test_k7_pass_met_exacte_motivering_via_de_keten(self, svc):
        result = await svc.validate_definition(
            begrip=TERM,
            text=GEEN_WOORD,
            context=_metadata(
                _beoordeling("no_word", tekst=GEEN_WOORD), tekst=GEEN_WOORD
            ),
        )
        assert result["rule_statuses"]["INT-03"] == "pass"
        detail = result["rule_results"]["INT-03"]
        assert detail["parts"][0]["reason"] == MOTIVERING_GEEN_VERWIJZEND_WOORD
        assert detail["review"]["assessment"]["finding"] == (
            BEVINDING_GEEN_VERWIJZEND_WOORD
        )

    async def test_fail_is_zichtbaar_maar_verandert_score_en_acceptatie_niet(self, svc):
        basis = await svc.validate_definition(
            begrip=TERM,
            text=ASTRA_FOUT,
            context=_metadata(
                _beoordeling("pass", tekst=ASTRA_FOUT, verwijzingen=[]),
                tekst=ASTRA_FOUT,
            ),
        )
        negatief = await svc.validate_definition(
            begrip=TERM,
            text=ASTRA_FOUT,
            context=_metadata(_beoordeling("fail", tekst=ASTRA_FOUT), tekst=ASTRA_FOUT),
        )
        assert basis["rule_statuses"]["INT-03"] == "pass"
        assert negatief["rule_statuses"]["INT-03"] == "fail"
        [violation] = _int03_violations(negatief)
        assert violation["severity"] == "warning"
        assert violation["severity_level"] == "medium"
        assert violation["metadata"]["advisory"] is True
        assert negatief["rule_results"]["INT-03"]["status"] == "fail"
        # excluded_from_score: geen cijfer voor INT-03, dus dezelfde
        # categoriecijfers, dezelfde acceptatie en dezelfde blokkadegronden.
        assert negatief["detailed_scores"] == basis["detailed_scores"]
        assert negatief["overall_score"] == basis["overall_score"]
        assert negatief["is_acceptable"] == basis["is_acceptable"]
        assert negatief["acceptance_gate"]["gates_failed"] == (
            basis["acceptance_gate"]["gates_failed"]
        )
        assert negatief["acceptance_gate"].get("reasons") == (
            basis["acceptance_gate"].get("reasons")
        )

    async def test_negatieve_uitkomst_bereikt_geen_automatisch_herstel(self, svc):
        from services.orchestrators.definition_orchestrator_v2 import (
            DefinitionOrchestratorV2,
        )

        negatief = await svc.validate_definition(
            begrip=TERM,
            text=ASTRA_FOUT,
            context=_metadata(_beoordeling("fail", tekst=ASTRA_FOUT), tekst=ASTRA_FOUT),
        )
        herstelbaar = DefinitionOrchestratorV2._herstelbare_overtredingen(negatief)
        assert not [v for v in herstelbaar if v.get("code") == "INT-03"]

    async def test_onvoldoende_informatie_is_open_met_vraag_in_de_keten(self, svc):
        result = await svc.validate_definition(
            begrip=TERM,
            text=ASTRA_FOUT,
            context=_metadata(
                _beoordeling("insufficient", tekst=ASTRA_FOUT, vraag="Wat is 'het'?"),
                tekst=ASTRA_FOUT,
            ),
        )
        assert result["rule_statuses"]["INT-03"] == "review_required"
        item = next(r for r in result["review_required"] if r["rule_id"] == "INT-03")
        assert "Wat is 'het'?" in item["reason"]

    async def test_technische_fout_is_error(self, svc):
        result = await svc.validate_definition(
            begrip=TERM, text=ASTRA_GOED, context=_metadata(_beoordeling("error"))
        )
        assert result["rule_statuses"]["INT-03"] == "error"
        assert _int03_violations(result) == []
        assert result["rule_results"]["INT-03"]["status"] == "error"
        assert result["evaluation_coverage"]["error"] >= 1

    async def test_ongeldige_beoordeling_is_error_in_de_keten(self, svc):
        # R4: structureel ongeldig ≠ ontbrekend: geen open reviewpunt zonder vraag.
        doc = _beoordeling("pass")
        doc["judgment"]["verdict"] = "ONGELDIG"
        result = await svc.validate_definition(
            begrip=TERM, text=ASTRA_GOED, context=_metadata(doc)
        )
        assert result["rule_statuses"]["INT-03"] == "error"
        assert _int03_violations(result) == []
        assert "INT-03" not in [r["rule_id"] for r in result["review_required"]]
        assert "ONGELDIG" not in result["rule_results"]["INT-03"]["parts"][0]["reason"]

    @pytest.mark.parametrize(
        "corrupt",
        [[], {"status": "ONGELDIG"}],
        ids=["geen-object", "onbekende-status"],
    )
    async def test_corrupt_beoordelingsdocument_is_error_in_de_keten(
        self, svc, corrupt
    ):
        # R4 (v2): documentcorruptie is geen ontbrekende beoordeling.
        result = await svc.validate_definition(
            begrip=TERM, text=ASTRA_GOED, context=_metadata(corrupt)
        )
        assert result["rule_statuses"]["INT-03"] == "error"
        assert "INT-03" not in [r["rule_id"] for r in result["review_required"]]
        assert "ONGELDIG" not in result["rule_results"]["INT-03"]["parts"][0]["reason"]

    async def test_lege_tekst_is_niet_geevalueerd(self, svc):
        result = await svc.validate_definition(begrip=TERM, text="", context={})
        assert result["rule_statuses"]["INT-03"] == "not_evaluated"
        assert result["rule_statuses"]["VAL-EMP-001"] == "fail"

    async def test_zonder_term_wordt_de_definitie_toch_beoordeeld(self, svc):
        result = await svc.validate_definition(
            begrip="",
            text=ASTRA_GOED,
            context=_metadata(_beoordeling("pass", begrip="")),
        )
        assert result["rule_statuses"]["INT-03"] == "pass"
