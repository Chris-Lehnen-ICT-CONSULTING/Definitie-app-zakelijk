"""ESS-05 (DEF-768): regelrecord, geregistreerde evaluator en uitkomstvertaling.

Echte regelrecords, geen provider: de AI-beoordeling is een synthetisch,
contractconform en aan de invoer gebonden document
(`tests/fixtures/def768_fakes.py`). Bewijst: geen woordindicator meer, geen
cijfer, een negatieve uitkomst is zichtbaar maar niet blokkerend, zonder
beoordeling nooit pass, technische fout apart.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from domain.ess05.contract import ONDERDEEL_ONDERSCHEID
from services.validation.evaluators.base import EvaluationDeps
from services.validation.evaluators.distinction_assessment import (
    DistinctionAssessmentEvaluator,
)
from services.validation.evaluators.positive_indicator import _INDICATOREN
from services.validation.evaluators.registry import get_default_registry
from services.validation.types_internal import EvaluationContext
from tests.fixtures.def768_fakes import BINDING, bouw_ess05_beoordeling
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
RUW = json.loads((REGELS_DIR / "ESS-05.json").read_text(encoding="utf-8"))
ESS05 = build_rule_record("ESS-05", RUW)

BEGRIP = "lener"
TEKST = "Persoon met een actuele lening bij de instelling."
CONTEXT = {
    "organisatorische_context": ["Synthetische Uitleendienst"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
BUREN = [
    {
        "term": "werknemer",
        "definitie": "Persoon met een arbeidsovereenkomst met de instelling.",
        "herkomst": "gebruiker",
        "bevestigd": True,
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


def _metadata(assessment, *, buren=BUREN, **extra) -> dict:
    return {
        **CONTEXT,
        "record_text": TEKST,
        "ess05_actieve_buren": buren,
        "ess05_assessment": assessment,
        "ess05_binding": BINDING.als_dict(),
        **extra,
    }


def _ctx(metadata: dict, *, tekst=TEKST) -> EvaluationContext:
    return EvaluationContext(
        raw_text=tekst, cleaned_text=tekst, begrip=BEGRIP, metadata=metadata
    )


def _evalueer(metadata, **kw):
    return DistinctionAssessmentEvaluator().evaluate(
        ESS05, _ctx(metadata, **kw), _deps()
    )


def _beoordeling(scenario, buren=BUREN):
    return bouw_ess05_beoordeling(
        BEGRIP, TEKST, CONTEXT, None, buren=buren, scenario=scenario
    )


class TestRegelrecord:
    def test_directe_ai_beoordeling_zonder_cijfer_met_verplichte_context(self):
        assert ESS05.evaluator is EvaluatorType.DISTINCTION_ASSESSMENT
        assert ESS05.required_inputs == (
            RequiredInput.DEFINITION_TEXT,
            RequiredInput.TERM,
            RequiredInput.CONTEXT_LISTS,
        )
        assert ESS05.executability is Executability.JUDGMENT
        assert ESS05.automation_status is AutomationStatus.AUTOMATED
        assert ESS05.score_policy is ScorePolicy.NO_SCORE
        assert ESS05.example_pair_policy is ExamplePairPolicy.REVIEW_POLICY
        assert RUW["runtime_contract"]["example_pair_issue"] == "DEF-768"

    def test_astra_voorbeeldpaar_prioriteit_midden_en_ess03_relatie(self):
        assert RUW["goede_voorbeelden"] == [
            (
                "Incident waarbij een jeugdige zonder toestemming één van de volgende "
                "justitiële voorzieningen verlaat: de open justitiële jeugdinrichting "
                "of het terrein dat tot de gesloten justitiële jeugdinrichting behoort."
            )
        ]
        assert RUW["foute_voorbeelden"] == [
            (
                "Incident waarbij een jeugdige zonder toestemming de justitiële "
                "jeugdinrichting verlaat."
            )
        ]
        assert RUW["prioriteit"] == "midden"
        assert "Instanties uniek onderscheidbaar" in {
            r["fulltext"] for r in RUW["relatie"]
        }
        assert RUW["thema"] == "onderscheid van verwante begrippen"

    def test_norm_is_een_kenmerkvraag_geen_extensietoets(self):
        """K-3b / E05: overlap van gevallen is geen gebrek."""
        assert "overlap" in RUW["toelichting"].lower()
        assert "beide rollen" in RUW["toelichting"]
        assert "kenmerk" in RUW["toetsvraag"]

    def test_evaluator_is_geregistreerd_en_in_het_rootcontract(self):
        evaluator = get_default_registry().resolve(EvaluatorType.DISTINCTION_ASSESSMENT)
        assert isinstance(evaluator, DistinctionAssessmentEvaluator)
        assert "distinction_assessment" in load_root_contract_policy().evaluators

    def test_de_woordindicator_voor_ess05_bestaat_niet_meer(self):
        assert "ESS-05" not in _INDICATOREN


class TestEvaluatorUitkomst:
    def test_lege_tekst_is_niet_beoordeeld(self):
        uitkomst = _evalueer({**_metadata(None), "record_text": ""}, tekst="")
        assert uitkomst.status is ResultStatus.NOT_EVALUATED

    def test_zonder_beoordeling_open_nooit_pass(self):
        uitkomst = _evalueer(_metadata(None))
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert uitkomst.score is None
        detail = uitkomst.metadata["rule_result"]
        assert detail["parts"][0]["id"] == ONDERDEEL_ONDERSCHEID
        assert detail["score"] is None

    def test_pass_zonder_cijfer(self):
        uitkomst = _evalueer(_metadata(_beoordeling("pass")))
        assert uitkomst.status is ResultStatus.PASS
        assert uitkomst.score is None
        assert uitkomst.metadata["rule_result"]["review"]["assessment"]["applied"]

    def test_fail_is_zichtbaar_maar_niet_blokkerend(self):
        uitkomst = _evalueer(_metadata(_beoordeling("fail")))
        assert uitkomst.status is ResultStatus.FAIL
        violation = uitkomst.violation
        assert violation["code"] == "ESS-05"
        assert violation["severity"] == "warning"
        assert violation["severity_level"] == "medium"
        assert violation["metadata"]["advisory"] is True
        assert "werknemer" in violation["message"]

    def test_k8_eigen_ess05_reden_zonder_buren(self):
        uitkomst = _evalueer(_metadata(_beoordeling("lacks", []), buren=[]))
        assert uitkomst.status is ResultStatus.FAIL
        assert "geen enkel verwant begrip" in uitkomst.violation["message"]

    def test_technische_fout_is_error(self):
        uitkomst = _evalueer(_metadata(_beoordeling("error")))
        assert uitkomst.status is ResultStatus.ERROR

    def test_modelvoorstel_maakt_open_met_een_vraag(self):
        uitkomst = _evalueer(_metadata(_beoordeling("voorstel")))
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert "synthetisch voorstel" in uitkomst.reason
        review = uitkomst.metadata["rule_result"]["review"]
        assert review["proposals"][0]["bevestigd"] is False

    def test_ongeldige_burenlijst_is_error(self):
        uitkomst = _evalueer(_metadata(None, buren="kapot"))
        assert uitkomst.status is ResultStatus.ERROR

    def test_zonder_binding_telt_een_beoordeling_niet(self):
        metadata = _metadata(_beoordeling("pass"))
        metadata.pop("ess05_binding")
        assert _evalueer(metadata).status is ResultStatus.REVIEW_REQUIRED

    @pytest.mark.parametrize(
        "veld",
        [
            "verification_model",
            "verification_provider",
            "verification_prompt_version",
            "schema_version",
            "verification_schema_version",
            "renderer_version",
        ],
    )
    def test_ess05_eigen_bindingsveld_dat_afwijkt_maakt_historisch(self, veld):
        """ADR-003: de evaluator bindt alle ESS-05-bindingsvelden, niet alleen
        de vier ESS-03-velden (anders valt de verificatiebinding stil weg)."""
        binding = {**BINDING.als_dict(), veld: "ander"}
        metadata = _metadata(_beoordeling("pass"), ess05_binding=binding)
        uitkomst = _evalueer(metadata)
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assessment = uitkomst.metadata["rule_result"]["review"]["assessment"]
        assert assessment["historical"] is True
        assert veld in assessment["reason"]

    def test_onvolledige_binding_telt_als_geen_binding(self):
        binding = BINDING.als_dict()
        binding.pop("verification_model")
        metadata = _metadata(_beoordeling("pass"), ess05_binding=binding)
        assert _evalueer(metadata).status is ResultStatus.REVIEW_REQUIRED


class TestZonderContextMetReden:
    """UI-bewijs DEF-768: zonder context is ESS-05 'niet beoordeeld' mét de
    contractreden in de gestructureerde uitkomst (alle weergavepaden), terwijl
    de contextplicht (`required_inputs`) blijft en er nooit een oordeel valt."""

    @staticmethod
    def _valideer(context: dict) -> dict:
        import asyncio

        from services.validation.modular_validation_service import (
            ModularValidationService,
        )
        from toetsregels.manager import get_toetsregel_manager

        service = ModularValidationService(get_toetsregel_manager(), None, None)
        return asyncio.run(
            service.validate_definition(begrip=BEGRIP, text=TEKST, context=context)
        )

    def test_contextplicht_blijft_gedeclareerd(self):
        assert RequiredInput.CONTEXT_LISTS in ESS05.required_inputs

    def test_niet_beoordeeld_met_contractreden_in_rule_results(self):
        resultaat = self._valideer({})
        assert resultaat["rule_statuses"]["ESS-05"] == "not_evaluated"
        detail = resultaat["rule_results"]["ESS-05"]
        assert detail["status"] == "not_evaluated"
        assert "zonder context is niet te bepalen" in json.dumps(
            detail, ensure_ascii=False
        )

    def test_met_context_ongewijzigd_niet_beoordeeld_zonder_dienst(self):
        resultaat = self._valideer(dict(CONTEXT))
        assert resultaat["rule_statuses"]["ESS-05"] == "review_required"

    def test_vangnet_nooit_een_oordeel_bij_ontbrekende_invoer(self, monkeypatch):
        from services.validation.evaluators.base import EvaluationOutcome

        monkeypatch.setattr(
            DistinctionAssessmentEvaluator,
            "evaluate",
            lambda self, record, ctx, deps: EvaluationOutcome.passed(),
        )
        resultaat = self._valideer({})
        assert resultaat["rule_statuses"]["ESS-05"] == "not_evaluated"
        assert "ESS-05" not in (resultaat.get("rule_results") or {})
