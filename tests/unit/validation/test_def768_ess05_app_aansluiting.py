"""DEF-768 stap 2 — de app gebruikt de bewijsregelroute voor ESS-05.

Plan: docs/plans/2026-09-29-DEF-768-ess05-app-aansluiting-plan-v1.md, besluit
Chris in -aanvulling-v1.md (A–D). Keten: container → ValidationOrchestratorV2
→ `Ess05BewijsregelService.assess` (één interpretatie + lokale controles) →
document `ess05/3` → `DistinctionAssessmentEvaluator` → contract-replay met het
app-bevestigingsbeleid (B) → resultaat → `validation_view`. Het model is een
spy op `generate_definition`: dit bewijst de keten en het beleid, niet de
modelkwaliteit. Geen echt model, geen netwerk.
"""

from __future__ import annotations

import asyncio
import copy
import json
from types import SimpleNamespace

import pytest

from domain.ess05 import app_bewijsregels as app, bewijsregels as br, contract as ec
from domain.sources.normalisatie import canoniseer_bronnen
from services.interfaces import Definition
from services.null_repository import NullDefinitionRepository
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation import ess05_bewijsregel_service as bs
from services.validation.ess05_assessment_service import Ess05AssessmentService
from services.validation.ess05_local_verification_service import (
    Ess05LocalVerificationService,
)
from services.validation.interfaces import ValidationContext
from services.validation.modular_validation_service import ModularValidationService
from tests.unit.domain.test_def768_bewijsregels import (
    BRON,
    BRON_A,
    BRON_C,
    BUUR,
    BUUR_A,
    BUUR_C,
    DEFINITIE,
    _a,
    _interpretatie_a,
    _interpretatie_c,
    _ruw,
    naar_eenheden,
)
from tests.unit.validation.test_def768_bewijsregel_service import _SpyAI
from toetsregels.manager import get_toetsregel_manager
from ui.components.validation_view import _ess05_regels

pytestmark = [pytest.mark.unit]

BEGRIP = "uitleen"
CONTEXT = {
    "organisatorische_context": ["Servicedesk ICT-middelen"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
BRONID = BRON.removeprefix("source:")

#: Tegengeval (K2-fixture van de domeintests): verhuur is tijdelijk maar niet
#: kosteloos, terwijl de kern kosteloosheid niet uitdrukt → niet onderscheiden.
DEF_T = "tijdelijk ter beschikking stellen van apparatuur"
BRON_T = (
    "Uitleen: apparatuur tijdelijk en kosteloos ter beschikking. Verhuur: "
    "apparatuur tijdelijk en tegen betaling ter beschikking."
)
BUUR_T = "ter beschikking stellen van apparatuur"
_UITLEEN_T = "Uitleen: apparatuur tijdelijk en kosteloos"
_VERHUUR_T = "Verhuur: apparatuur tijdelijk en tegen betaling"


def _interpretatie_t():
    return _ruw(
        {"bovenbegrip": "ter beschikking stellen van apparatuur",
         "kenmerken": [{"id": "K1", "kenmerk": "duur", "waarde": "tijdelijk",
                        "citaat": "tijdelijk"}]},
        [
            _a("K1", "doel", "bevestigd", [(BRON, _UITLEEN_T)]),
            _a("M1", "doel", "bevestigd", [(BRON, _UITLEEN_T)]),
            _a("K1", BUUR, "bevestigd", [(BRON, _VERHUUR_T)]),
            _a("M1", BUUR, "ontkend", [(BRON, _VERHUUR_T)]),
        ],
        buiten_kern=[{"id": "M1", "kenmerk": "kosten", "waarde": "kosteloos"}],
    )  # fmt: skip


def _interpretatie_zonder_kenmerk():
    return _ruw({"bovenbegrip": "ter beschikking stellen van apparatuur",
                 "kenmerken": []}, [])  # fmt: skip


#: scenario → (definitie, bronpassage, buurdefinitie, interpretatie)
SCENARIO = {
    "pass": (DEFINITIE, BRON_C, BUUR_C, _interpretatie_c),
    "open": (DEFINITIE, BRON_A, BUUR_A, _interpretatie_a),
    "tegengeval": (DEF_T, BRON_T, BUUR_T, _interpretatie_t),
    "zonder_kenmerk": (BUUR_T, BRON_A, BUUR_A, _interpretatie_zonder_kenmerk),
}


def _bronnen(passage: str) -> list[dict]:
    return [{"source_id": BRONID, "snippet": passage}]


def _buur(definitie: str, *, bevestigd: bool = True) -> dict:
    """Een bevestigde (gebruiker) of onbevestigde (bron) buur met vast id."""
    return {
        "id": BUUR,
        "term": "verhuur",
        "definitie": definitie,
        "herkomst": "gebruiker" if bevestigd else "bron",
        "bevestigd": bevestigd,
    }


def _invoer(tekst: str, passage: str, buren: list[dict]) -> br.Vergelijkingsinvoer:
    """Het materiaal dat de app bindt (onafhankelijk van de adapter opgebouwd)."""
    actief = ec.normaliseer_buren(buren)
    materiaal = ec.beoordelingsmateriaal(
        BEGRIP, tekst, canoniseer_bronnen(_bronnen(passage)), actief, contexten=CONTEXT
    )
    return br.Vergelijkingsinvoer(
        BEGRIP, materiaal, tuple((b.id, b.term) for b in actief)
    )


def _spy(scenario: str, buren: list[dict], **kwargs) -> _SpyAI:
    """Spy met de interpretatie van dit scenario; zonder buren wordt niets gevraagd."""
    tekst, passage, _, ruw = SCENARIO[scenario]
    if not buren:
        return _SpyAI({}, **kwargs)
    return _SpyAI(naar_eenheden(ruw(), _invoer(tekst, passage, buren)), **kwargs)


def _dienst(ai) -> bs.Ess05BewijsregelService:
    return bs.Ess05BewijsregelService.voor_app(ai)


def _assess(dienst, scenario: str, buren: list[dict], **kwargs) -> dict:
    tekst, passage, _, _ = SCENARIO[scenario]
    return asyncio.run(
        dienst.assess(
            BEGRIP,
            tekst,
            CONTEXT,
            kwargs.pop("bronnen", _bronnen(passage)),
            buren=ec.normaliseer_buren(buren),
            intentie=None,
            uitgesloten_termen=(),
            correlation_id="test",
        )
    )


def _replay(dienst, scenario: str, buren: list[dict], document, **kwargs):
    tekst, passage, _, _ = SCENARIO[scenario]
    return ec.beoordeel_onderscheid(
        BEGRIP,
        tekst,
        CONTEXT,
        _bronnen(passage),
        buren=buren,
        assessment=document,
        binding=ec.binding_uit_dict(dienst.binding().als_dict()),
        **kwargs,
    )


def _oordeel(scenario: str, *, bevestigd: bool = True):
    buren = [_buur(SCENARIO[scenario][2], bevestigd=bevestigd)]
    dienst = _dienst(_spy(scenario, buren))
    return _replay(dienst, scenario, buren, _assess(dienst, scenario, buren))


def _oude_route_verboden(monkeypatch):
    def _verboden(*_a, **_k):
        raise AssertionError("de app-keten mag ess05-assess/19 niet meer aanroepen")

    monkeypatch.setattr(Ess05AssessmentService, "__init__", _verboden)
    monkeypatch.setattr(Ess05AssessmentService, "assess", _verboden)


# --- aansluiting: container en generatie-orchestrator -----------------------------------


class TestAansluiting:
    def test_container_levert_de_bewijsregelservice(self, monkeypatch):
        from services.container import ServiceContainer

        _oude_route_verboden(monkeypatch)
        container = ServiceContainer.__new__(ServiceContainer)
        container._instances = {}
        ai = _SpyAI({})
        monkeypatch.setattr(container, "ai_service", lambda: ai, raising=False)
        monkeypatch.setattr(container, "model_router", lambda: None, raising=False)
        dienst = container.ess05_assessment_service()
        assert isinstance(dienst, bs.Ess05BewijsregelService)
        assert isinstance(dienst.controle, Ess05LocalVerificationService)
        assert container.ess05_assessment_service() is dienst
        assert dienst.binding().prompt_version == "ess05-interpretatie-prompt/5"

    def test_generatie_orchestrator_bouwt_standaard_de_bewijsregelservice(
        self, monkeypatch
    ):
        from services.orchestrators import definition_orchestrator_v2 as module

        _oude_route_verboden(monkeypatch)

        class FakeRouter:
            @classmethod
            def from_config(cls):
                return cls()

            def get_model(self, task_type):
                return "fake", f"fake-{task_type}"

        monkeypatch.setattr("services.ai.model_router.ModelRouter", FakeRouter)
        orch = module.DefinitionOrchestratorV2(
            ai_service=_SpyAI({}), cleaning_service=object(), repository=object()
        )
        dienst = orch.ess05_assessment_service
        assert isinstance(dienst, bs.Ess05BewijsregelService)
        assert orch.ess05_assessment_service is dienst
        binding = dienst.binding()
        assert (binding.model, binding.verification_model) == (
            "fake-validation",
            "fake-ess05_verification",
        )


# --- adapter: document ess05/3 --------------------------------------------------------


class TestAdapter:
    def test_document_na_een_interpretatie_en_controles(self):
        buren = [_buur(BUUR_C)]
        ai = _spy("pass", buren)
        dienst = _dienst(ai)
        document = _assess(dienst, "pass", buren)
        assert app.DOCUMENTVERSIE == "ess05/3"
        assert document["contract_version"] == app.DOCUMENTVERSIE
        assert document["status"] == "assessed"
        assert document["fingerprint"] == ec.bereken_ess05_vingerafdruk(
            BEGRIP,
            DEFINITIE,
            CONTEXT,
            _bronnen(BRON_C),
            buren=ec.normaliseer_buren(buren),
        )
        assert document["binding"] == dienst.binding().als_dict()
        assert [a["task_type"] for a in ai.aanroepen] == [
            "validation",
            "ess05_verification",
            "ess05_verification",
            "ess05_verification",
        ]
        assert [c["name"] for c in document["controls"]] == [
            "kern",
            "doel",
            f"buur:{BUUR}",
        ]
        assert ai.aanroepen[0]["system_prompt"] == bs.interpretatiesysteemprompt()
        # Nergens de oude route: geen assess/19-prompt, geen modelvoorstellen.
        assert "ess05-assess" not in json.dumps(document)
        assert "Definitiekern (te toetsen" not in json.dumps(
            [a["prompt"] for a in ai.aanroepen]
        )

    def test_zonder_actieve_buren_geen_aanroep(self):
        ai = _spy("pass", [])
        document = _assess(_dienst(ai), "pass", [])
        assert ai.aanroepen == []
        assert (document["contract_version"], document["status"]) == (
            "ess05/3",
            "assessed",
        )
        assert document["interpretation"] is None and document["controls"] == []

    def test_te_lange_passage_is_technische_fout_zonder_aanroep(self):
        buren = [_buur(BUUR_C)]
        ai = _spy("pass", buren)
        document = _assess(_dienst(ai), "pass", buren, bronnen=_bronnen("x" * 8001))
        assert ai.aanroepen == []
        assert document["status"] == "error"
        assert document["error"]["type"] == "input_truncated"

    def test_onleesbare_interpretatie_is_technische_fout(self):
        buren = [_buur(BUUR_C)]
        ai = _SpyAI("geen json")
        document = _assess(_dienst(ai), "pass", buren)
        assert len(ai.aanroepen) == 1
        assert (document["status"], document["error"]["type"]) == (
            "error",
            "malformed_response",
        )


# --- replay en app-bevestigingsbeleid (besluit B) -------------------------------------


class TestBeleidB:
    def test_onderscheiden_van_bevestigde_buur_voldoet(self):
        uitkomst = _oordeel("pass")
        assert uitkomst.status == ec.STATUS_PASS
        assert uitkomst.review["proposals"] == []
        assert uitkomst.review["question"] is None
        assert [p.status for p in uitkomst.parts] == ["pass", "pass"]

    def test_niet_onderscheiden_van_bevestigde_buur_is_fail(self):
        uitkomst = _oordeel("tegengeval")
        assert uitkomst.status == ec.STATUS_FAIL
        assert "verhuur" in uitkomst.parts[0].reason
        assert uitkomst.parts[1].status == ec.STATUS_FAIL

    def test_niet_onderscheiden_van_onbevestigde_buur_is_open_met_vraag(self):
        uitkomst = _oordeel("tegengeval", bevestigd=False)
        assert uitkomst.status == ec.STATUS_OPEN
        assert "verhuur" in uitkomst.review["question"]
        assert uitkomst.review["proposals"] == []
        assert uitkomst.parts[1].status == ec.STATUS_OPEN

    def test_open_oordeel_bij_bevestigde_buur_blijft_open(self):
        uitkomst = _oordeel("open")
        assert uitkomst.status == ec.STATUS_OPEN
        assert uitkomst.review["question"].startswith("Wat onderscheidt")

    def test_onderscheiden_zonder_bevestigde_buur_is_open(self):
        uitkomst = _oordeel("pass", bevestigd=False)
        assert uitkomst.status == ec.STATUS_OPEN
        assert uitkomst.review["question"]

    def test_kern_zonder_kenmerk_blijft_fail_ook_zonder_bevestiging(self):
        uitkomst = _oordeel("zonder_kenmerk", bevestigd=False)
        assert uitkomst.status == ec.STATUS_FAIL
        assert "kenmerk" in uitkomst.parts[0].reason

    def test_zonder_buren_open_met_vraag_verwante_begrippen(self):
        dienst = _dienst(_spy("pass", []))
        uitkomst = _replay(dienst, "pass", [], _assess(dienst, "pass", []))
        assert uitkomst.status == ec.STATUS_OPEN
        assert "verwante begrippen" in uitkomst.review["question"]
        assert "voeg verwante begrippen toe" in uitkomst.parts[0].action

    def test_lege_ruimte_blijft_pass_zonder_beoordeling(self):
        dienst = _dienst(_spy("pass", []))
        vingerafdruk = ec.bereken_ess05_vingerafdruk(
            BEGRIP, DEFINITIE, CONTEXT, _bronnen(BRON_C)
        )
        lege = {
            "contract_version": ec.CONTRACTVERSIE,
            "fingerprint": vingerafdruk,
            "grond": "geen verwante begrippen in deze context",
            "actor": "deskundige",
        }
        uitkomst = _replay(dienst, "pass", [], None, lege_ruimte=lege)
        assert uitkomst.status == ec.STATUS_PASS


class TestReplayFailClosed:
    def _document(self):
        buren = [_buur(BUUR_C)]
        dienst = _dienst(_spy("pass", buren))
        return dienst, buren, _assess(dienst, "pass", buren)

    def test_ess05_2_document_is_verouderd(self):
        dienst, buren, document = self._document()
        document["contract_version"] = "ess05/2"
        uitkomst = _replay(dienst, "pass", buren, document)
        assert uitkomst.status == ec.STATUS_OPEN
        assert "verouderd — toets opnieuw" in uitkomst.parts[0].reason

    def test_gewijzigde_controle_telt_niet(self):
        dienst, buren, document = self._document()
        vervalst = copy.deepcopy(document)
        vervalst["controls"][1]["raw"]["checks"][0]["outcome"] = "unsupported"
        assert _replay(dienst, "pass", buren, vervalst).status == ec.STATUS_OPEN

    def test_gewijzigde_interpretatie_telt_niet(self):
        dienst, buren, document = self._document()
        vervalst = copy.deepcopy(document)
        vervalst["interpretation"]["raw_response"] += " "
        assert _replay(dienst, "pass", buren, vervalst).status == ec.STATUS_OPEN

    def test_andere_binding_is_historisch(self):
        dienst, buren, document = self._document()
        document["binding"] = {**document["binding"], "model": "ander-model"}
        uitkomst = _replay(dienst, "pass", buren, document)
        assert uitkomst.status == ec.STATUS_OPEN
        assert uitkomst.review["assessment"]["historical"] is True

    def test_onvervalst_document_wordt_toegepast(self):
        dienst, buren, document = self._document()
        uitkomst = _replay(dienst, "pass", buren, document)
        assert uitkomst.status == ec.STATUS_PASS
        assert uitkomst.review["assessment"]["applied"] is True


# --- de hele app-keten: orchestrator → evaluator → resultaat → weergave -----------------


def _valideer(monkeypatch, scenario: str, buren: list[dict], ai=None):
    _oude_route_verboden(monkeypatch)
    tekst, passage, _, _ = SCENARIO[scenario]
    ai = ai or _spy(scenario, buren)
    orch = ValidationOrchestratorV2(
        ModularValidationService(
            get_toetsregel_manager(), repository=NullDefinitionRepository()
        ),
        ess05_assessment_service=_dienst(ai),
    )
    metadata = {
        **CONTEXT,
        "ess05_buren": buren,
        "provenance_sources": _bronnen(passage),
    }
    resultaat = asyncio.run(
        orch.validate_text(BEGRIP, tekst, context=ValidationContext(metadata=metadata))
    )
    return SimpleNamespace(resultaat=resultaat, ai=ai)


class TestKetenDoorDeApp:
    def test_fail_via_orchestrator_evaluator_en_resultaat(self, monkeypatch):
        run = _valideer(monkeypatch, "tegengeval", [_buur(BUUR_T)])
        resultaat = run.resultaat
        assert resultaat["ess05_assessment"]["contract_version"] == "ess05/3"
        assert resultaat["rule_statuses"]["ESS-05"] == "fail"
        [schending] = [v for v in resultaat["violations"] if v.get("code") == "ESS-05"]
        assert schending["severity"] == "warning"  # adviserend, geen blokkade
        assert resultaat["rule_results"]["ESS-05"]["review"]["proposals"] == []
        assert run.ai.aanroepen[0]["task_type"] == "validation"
        assert {a["task_type"] for a in run.ai.aanroepen[1:]} == {"ess05_verification"}

    def test_onbevestigde_buur_open_met_vraag_op_het_scherm(self, monkeypatch):
        run = _valideer(monkeypatch, "tegengeval", [_buur(BUUR_T, bevestigd=False)])
        assert run.resultaat["rule_statuses"]["ESS-05"] == "review_required"
        regels = _ess05_regels(run.resultaat["rule_results"]["ESS-05"]["review"])
        assert any(r.startswith("❓ Vraag:") and "verhuur" in r for r in regels)
        assert any("verhuur (bron, onbevestigd)" in r for r in regels)
        assert not any(r.startswith("Voorstel:") for r in regels)

    def test_zonder_buren_geen_modelaanroep(self, monkeypatch):
        run = _valideer(monkeypatch, "pass", [])
        assert run.ai.aanroepen == []
        assert run.resultaat["rule_statuses"]["ESS-05"] == "review_required"
        assert run.resultaat["rule_results"]["ESS-05"]["review"]["question"]

    def test_technische_fout_reist_mee_als_error(self, monkeypatch):
        # Robuustheid P1 (punt 4): alleen een echte storing is `error`; onleesbare
        # modeluitvoer ("geen json") is sindsdien review_required
        # (test_def768_robuustheid_melding.py).
        ai = _SpyAI({}, fout=RuntimeError("storing"))
        run = _valideer(monkeypatch, "pass", [_buur(BUUR_C)], ai=ai)
        assert run.resultaat["rule_statuses"]["ESS-05"] == "error"
        assert run.resultaat["ess05_assessment"]["status"] == "error"


# --- editor: opslaan en herbinden met de nieuwe binding --------------------------------


def test_editor_neemt_een_geldige_ess05_3_beoordeling_op():
    from services.definition_edit_service import (
        _neem_ess05_beoordeling_op,
        ess03_intentie_van_definition,
    )

    buren = [_buur(BUUR_C)]
    definitie = Definition(
        begrip=BEGRIP,
        definitie=DEFINITIE,
        organisatorische_context=list(CONTEXT["organisatorische_context"]),
        metadata={"ess05_buren": buren, "provenance_sources": _bronnen(BRON_C)},
    )
    dienst = _dienst(_spy("pass", buren))
    document = asyncio.run(
        dienst.assess(
            BEGRIP,
            DEFINITIE,
            CONTEXT,
            _bronnen(BRON_C),
            buren=ec.normaliseer_buren(buren),
            intentie=ess03_intentie_van_definition(definitie),
        )
    )
    opgenomen, reden = _neem_ess05_beoordeling_op(
        document, definitie, buren, dienst.binding()
    )
    assert (opgenomen, reden) == (True, None)
    assert definitie.metadata["ess05_assessment"]["contract_version"] == "ess05/3"
