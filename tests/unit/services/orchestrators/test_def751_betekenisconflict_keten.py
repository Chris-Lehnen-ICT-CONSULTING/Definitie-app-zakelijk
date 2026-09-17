"""DEF-751 stap 2 — de aftakking in de echte orchestrator, direct na het AI-antwoord.

Een door het model gemeld betekenisconflict (of een ongeldige melding) mag
niet als definitie verder de keten in: geen voorbeelden, geen opschoning,
geen validatie, geen opslag, geen mislukte-poging-registratie, geen
categoriebevestiging. Het resultaat is een specifieke non-success met de
conflictgegevens in de metadata; de monitoring wordt netjes afgerond. Een
gewoon definitieantwoord loopt exact zoals vóór deze wijziging.

Alle services zijn offline doubles (zelfde opzet als de DEF-743-transport-
tests); niets hier claimt modelkwaliteit.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.interfaces import (
    AIGenerationResult,
    CleaningResult,
    GenerationRequest,
    OrchestratorConfig,
    PromptResult,
)
from services.modelantwoord import CONFLICT_SENTINEL
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.prompts.modules.context_awareness_module import verduidelijking_datalijn

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

DEFINITIE = "Een registratie is een vastlegging van meetwaarden in een register"
LEZINGEN = [
    {
        "lezing": "de handeling van het vastleggen",
        "bron": "bron 1",
        "grond": "bron 1 beschrijft registratie als activiteit",
    },
    {
        "lezing": "het vastgelegde gegeven",
        "bron": "context: DJI",
        "grond": "de DJI-context gebruikt registratie voor het resultaat",
    },
]
VRAAG = "Is de handeling of het vastgelegde gegeven bedoeld?"


def conflictmelding(lezingen=LEZINGEN, vraag=VRAAG) -> str:
    return f"{CONFLICT_SENTINEL} " + json.dumps(
        {"vraag": vraag, "lezingen": lezingen}, ensure_ascii=False
    )


def _request(**extra) -> GenerationRequest:
    return GenerationRequest(
        id="11111111-2222-3333-4444-555555555555",
        begrip="registratie",
        ontologische_categorie="proces",
        organisatorische_context=["DJI"],
        juridische_context=["Strafrecht"],
        actor="test",
        options={"category_choice": {"origin": "model", "reasoning": "r"}},
        **extra,
    )


class Keten:
    """Eén echte `create_definition`-run met zichtbare doubles."""

    def __init__(self, monkeypatch, modeltekst: str, bron_nrs=(1, 2)):
        from voorbeelden import unified_voorbeelden

        self.voorbeelden = AsyncMock(return_value={})
        monkeypatch.setattr(
            unified_voorbeelden, "genereer_alle_voorbeelden_async", self.voorbeelden
        )
        self.prompt = AsyncMock()

        async def _bouw(request, **kwargs) -> PromptResult:
            # Zoals de echte promptservice: een verduidelijking staat als
            # volledige datalijn in de prompt (postconditie, reviewcorrectie 1).
            tekst = "Offline prompt"
            if request.betekenisverduidelijking:
                tekst += "\n" + verduidelijking_datalijn(
                    request.betekenisverduidelijking
                )
            return PromptResult(
                text=tekst,
                token_count=1,
                components_used=(),
                feedback_integrated=False,
                optimization_applied=False,
                metadata={
                    "source_receipt": {
                        "status": "used" if bron_nrs else "none",
                        "sources": [
                            {"nr": nr, "source_type": "document"} for nr in bron_nrs
                        ],
                        "omitted": [],
                        "errors": [],
                        "channels": {},
                    }
                },
            )

        self.prompt.build_generation_prompt.side_effect = _bouw
        self.ai = AsyncMock()
        self.ai.generate_definition.return_value = AIGenerationResult(
            text=modeltekst, model="offline", tokens_used=7, generation_time=0.0
        )
        self.cleaning = AsyncMock()
        self.cleaning.clean_text.return_value = CleaningResult(
            original_text=DEFINITIE, cleaned_text=DEFINITIE, was_cleaned=False
        )
        self.validation = AsyncMock()
        self.validation.validate_definition.return_value = {
            "version": "1.0.0",
            "overall_score": 0.85,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": [],
            "detailed_scores": {},
            "system": {},
        }
        self.repo = MagicMock()
        self.repo.save.return_value = 42
        self.repo.save_failed_attempt = AsyncMock()
        self.monitoring = AsyncMock()
        self.feedback = AsyncMock()
        self.orch = DefinitionOrchestratorV2(
            prompt_service=self.prompt,
            ai_service=self.ai,
            validation_service=self.validation,
            cleaning_service=self.cleaning,
            repository=self.repo,
            monitoring=self.monitoring,
            feedback_engine=self.feedback,
            config=OrchestratorConfig(
                enable_feedback_loop=True, enable_enhancement=False
            ),
        )

    async def run(self, request: GenerationRequest | None = None):
        return await self.orch.create_definition(request or _request())

    def geen_downstream(self) -> None:
        assert not self.voorbeelden.called, "voorbeelden gedraaid op een conflict"
        assert not self.cleaning.clean_text.called, "opschoning gedraaid"
        assert not self.validation.validate_definition.called, "validatie gedraaid"
        assert not self.repo.save.called, "opgeslagen"
        assert not self.repo.save_failed_attempt.called, "mislukte poging geboekt"
        assert not self.feedback.process_validation_feedback.called


async def test_gemeld_conflict_is_specifieke_non_success_zonder_definitie(monkeypatch):
    keten = Keten(monkeypatch, conflictmelding())
    response = await keten.run()

    assert response.success is False
    assert response.definition is None
    assert response.validation_result is None
    md = response.metadata
    assert md["error_type"] == "betekenisconflict"
    assert md["phases_completed"] == 4
    conflict = md["betekenisconflict"]
    assert conflict["vraag"] == VRAAG
    assert conflict["lezingen"] == LEZINGEN
    assert conflict["gemeld_door"] == "model"
    assert conflict["begrip"] == "registratie"
    assert conflict["ontologische_categorie"] == "proces"
    assert conflict["organisatorische_context"] == ["DJI"]
    assert conflict["generation_id"] == "11111111-2222-3333-4444-555555555555"
    # Geen cijfer, geen oordeel, geen categoriebevestiging in het resultaat.
    assert "category_choice" not in json.dumps(md)
    assert VRAAG in (response.error or "")
    keten.geen_downstream()
    # Monitoring is afgerond, niet als error maar als niet-geslaagde generatie.
    keten.monitoring.complete_generation.assert_awaited_once()
    assert keten.monitoring.complete_generation.await_args.kwargs["success"] is False
    assert not keten.monitoring.track_error.called


@pytest.mark.parametrize(
    ("modeltekst", "reden_bevat"),
    [
        (DEFINITIE + "\n" + conflictmelding(), "eerste regel"),
        (conflictmelding() + "\n" + DEFINITIE, "na de"),
        (f"{CONFLICT_SENTINEL} de bronnen spreken elkaar tegen", "JSON"),
        (conflictmelding(lezingen=LEZINGEN[:1]), "minstens twee"),
        (conflictmelding() + "\n" + conflictmelding(), "dubbel"),
    ],
)
async def test_ongeldige_of_vermengde_melding_faalt_veilig(
    monkeypatch, modeltekst, reden_bevat, caplog
):
    keten = Keten(monkeypatch, modeltekst)
    with caplog.at_level("INFO"):
        response = await keten.run()

    assert response.success is False and response.definition is None
    assert response.metadata["error_type"] == "modelantwoord_ongeldig"
    assert reden_bevat.lower() in response.metadata["reden"].lower()
    assert "betekenisconflict" not in response.metadata
    # De ruwe modeltekst is geen kandidaat en staat nergens in de response of het log.
    assert DEFINITIE not in json.dumps(response.metadata)
    assert DEFINITIE not in (response.error or "")
    assert VRAAG not in caplog.text and DEFINITIE not in caplog.text
    keten.geen_downstream()
    keten.monitoring.complete_generation.assert_awaited_once()


async def test_grond_zonder_aangeleverde_bron_of_context_is_ongeldig(monkeypatch):
    # Bron 3 is niet in de prompt opgenomen (kwitantie kent 1 en 2); OM is
    # geen opgegeven contextwaarde. Verzonnen bewijs → geen conflict, geen kandidaat.
    lezingen = [
        {**LEZINGEN[0], "bron": "bron 3"},
        {**LEZINGEN[1], "bron": "context: OM"},
    ]
    keten = Keten(monkeypatch, conflictmelding(lezingen=lezingen))
    response = await keten.run()
    assert response.success is False
    assert response.metadata["error_type"] == "modelantwoord_ongeldig"
    assert "aangeleverd" in response.metadata["reden"]
    keten.geen_downstream()


async def test_conflict_zonder_bronnen_mag_alleen_op_contextwaarden_steunen(
    monkeypatch,
):
    lezingen = [
        {**LEZINGEN[0], "bron": "context: DJI"},
        {**LEZINGEN[1], "bron": "context: Strafrecht"},
    ]
    keten = Keten(monkeypatch, conflictmelding(lezingen=lezingen), bron_nrs=())
    response = await keten.run()
    assert response.metadata["error_type"] == "betekenisconflict"
    keten.geen_downstream()


async def test_gewoon_definitieantwoord_loopt_ongewijzigd_door(monkeypatch):
    keten = Keten(monkeypatch, "Ontologische categorie: proces\n" + DEFINITIE)
    response = await keten.run()

    assert response.success is True
    assert response.definition is not None and response.definition.id == 42
    # De ruwe modeltekst bereikt de opschoning byte-identiek.
    keten.cleaning.clean_text.assert_awaited_once()
    assert (
        keten.cleaning.clean_text.await_args.args[0]
        == "Ontologische categorie: proces\n" + DEFINITIE
    )
    assert keten.validation.validate_definition.called
    assert keten.repo.save.called
    assert "betekenisconflict" not in response.metadata
    assert response.metadata.get("betekenisverduidelijking_gebruikt") is False


async def test_verduidelijking_reist_naar_de_prompt_en_wordt_geregistreerd(monkeypatch):
    keten = Keten(monkeypatch, DEFINITIE)
    request = _request(
        betekenisverduidelijking="Bedoeld is de handeling van het vastleggen"
    )
    response = await keten.run(request)

    assert response.success is True
    doorgegeven = keten.prompt.build_generation_prompt.await_args.args[0]
    assert (
        doorgegeven.betekenisverduidelijking
        == "Bedoeld is de handeling van het vastleggen"
    )
    assert response.metadata["betekenisverduidelijking_gebruikt"] is True
    # Herleidbaar op het record: als gebruikersbedoeling, niet als bronfeit of oordeel.
    md = response.definition.metadata
    assert (
        md["betekenisverduidelijking"] == "Bedoeld is de handeling van het vastleggen"
    )
    assert md.get("source_review") is None
