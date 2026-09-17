"""DEF-751 B2 — reproducties van de Codex-herreview op commit 570efa223.

A. Generieke `GenerationRequest.options → orchestrator → save` mag geen
   handmatig keuze-event maken: een aangeleverde `manual`-claim blijft
   onbevestigde aanvraaginformatie (`category_choice_claim`, status
   `unconfirmed_claim`); het echte handmatige event ontstaat uitsluitend via
   de expliciete generatieactie in de handler (commando na opslag), zoals
   het editorcommando. Beide routes: echte save → sluiten → nieuwe repository.
B. Een ruwe `generation_prompt_data`-update met None/'not-json'/'null'/'[]'
   mag beheerde keuzegegevens (event, staat, historie, claim) en de overige
   beheerde JSON-sleutels (CON-02-historie, bronbewijs, prompt) niet wissen:
   geweigerd vóór de transactie, niets geschreven.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from database.models import (
    CATEGORY_CHOICE_CLAIM_KEY,
    CATEGORY_CHOICE_HISTORY_KEY,
    CATEGORY_CHOICE_KEY,
    CATEGORY_CHOICE_STATE_KEY,
    SOURCE_REVIEW_HISTORY_KEY,
)
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition, GenerationRequest
from services.orchestrators.definition_orchestrator_v2 import (
    DefinitionOrchestratorV2,
)
from ui.handlers.definition_generation_handler import DefinitionGenerationHandler
from ui.helpers.categorie_weergave import beschrijf_keuzestatus

pytestmark = [pytest.mark.unit]

ORG = ["DJI"]
JUR = ["Strafrecht"]
WET = ["Pbw"]
CONTEXT = {
    "organisatorische_context": ORG,
    "juridische_context": JUR,
    "wettelijke_basis": WET,
}


@pytest.fixture
def db_path(tmp_path) -> str:
    return str(tmp_path / "review2.db")


# ---------------------------------------------------------------- A: generiek


def test_generieke_options_manual_claim_maakt_geen_handmatig_event(db_path):
    orch = DefinitionOrchestratorV2.__new__(DefinitionOrchestratorV2)
    request = GenerationRequest(
        id="r1",
        begrip="keurmerk",
        ontologische_categorie="type",
        organisatorische_context=list(ORG),
        juridische_context=list(JUR),
        wettelijke_basis=list(WET),
        options={"category_choice": {"origin": "manual", "actor": "Henk"}},
    )
    definition = orch._create_definition_object(
        request=request,
        text="Een keurmerk is …",
        validation_result={},
        generation_metadata={"generation_id": "gen-1", "status": "draft"},
    )
    did = DefinitionRepository(db_path).save(definition)

    record = DefinitieRepository(db_path).get_definitie(did)
    assert record.categorie == "type"
    assert record.get_category_choice() is None, "generieke claim werd een event"
    status = record.get_category_choice_status()
    assert status["status"] == "unconfirmed_claim"
    claim = record.get_generatieregistratie()[CATEGORY_CHOICE_CLAIM_KEY]
    assert claim["origin"] == "manual" and "actor" not in claim
    caption = beschrijf_keuzestatus(status, None)
    assert "niet bevestigd" in caption and "Henk" not in caption
    # Servicelaag-readback via nieuwe repository.
    opnieuw = DefinitionRepository(db_path).get(did)
    assert opnieuw.metadata["category_choice"] is None
    assert opnieuw.metadata["category_choice_status"]["status"] == "unconfirmed_claim"


def test_generieke_options_model_blijft_een_modelvoorstel(db_path):
    orch = DefinitionOrchestratorV2.__new__(DefinitionOrchestratorV2)
    request = GenerationRequest(
        id="r1",
        begrip="keurmerk",
        ontologische_categorie="proces",
        organisatorische_context=list(ORG),
        options={"category_choice": {"origin": "model", "reasoning": "r"}},
    )
    definition = orch._create_definition_object(
        request=request, text="x", validation_result={}, generation_metadata={}
    )
    did = DefinitionRepository(db_path).save(definition)
    record = DefinitieRepository(db_path).get_definitie(did)
    assert record.get_category_choice()["origin"] == "model"
    assert record.get_category_choice_status()["status"] == "model_suggestion"


# ---------------------------------------------------------- A: echte handler


class _OpslaandeService:
    """Fake definitieservice die — zoals de echte — het concept opslaat."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.laatste_kwargs: dict[str, Any] = {}

    async def generate_definition(self, begrip: str, context_dict: dict, **kwargs):
        self.laatste_kwargs = kwargs
        categorie = kwargs.get("categorie")
        did = DefinitionRepository(self.db_path).save(
            Definition(
                begrip=begrip,
                definitie="Een gegenereerde definitie.",
                categorie=categorie.value if categorie else None,
                organisatorische_context=list(context_dict.get("organisatorisch", [])),
                juridische_context=list(context_dict.get("juridisch", [])),
                wettelijke_basis=list(context_dict.get("wettelijk", [])),
                metadata={
                    "status": "draft",
                    "category_choice_input": kwargs.get("options", {}).get(
                        "category_choice"
                    ),
                },
            )
        )
        return {"saved_definition_id": did}

    def to_ui_response(self, response):
        return {"success": True, "saved_definition_id": response["saved_definition_id"]}


def _handler(db_path: str) -> tuple[DefinitionGenerationHandler, _OpslaandeService]:
    service = _OpslaandeService(db_path)
    from integration.definitie_checker import CheckAction

    checker = MagicMock()
    checker.check_before_generation.return_value = MagicMock(action=CheckAction.PROCEED)
    return (
        DefinitionGenerationHandler(
            checker=checker,
            definition_service=service,
            repository=DefinitieRepository(db_path),
        ),
        service,
    )


def _sm(**waarden):
    sessie = {"generation_options": {"model": "x"}, **waarden}
    sm = MagicMock()
    sm.get_value = Mock(side_effect=lambda k, d=None: sessie.get(k, d))
    return sm


def generatieresultaat(sm: MagicMock) -> dict[str, Any]:
    """Het `last_generation_result` dat de handler in de sessie zette."""
    for aanroep in sm.set_value.call_args_list:
        if aanroep.args and aanroep.args[0] == "last_generation_result":
            return aanroep.args[1]
    raise AssertionError("geen last_generation_result gezet")


def test_echte_handleroverride_maakt_via_het_commando_een_handmatig_event(db_path):
    handler, service = _handler(db_path)
    sm = _sm(manual_ontological_category="TYPE", determined_category="proces")
    with patch(
        "ui.helpers.async_bridge.run_async",
        lambda coro, **kw: __import__("asyncio").run(coro),
    ):
        handler.handle_definition_generation(
            "keurmerk", CONTEXT, _st=MagicMock(), _sm=sm
        )

    # Generieke options dragen geen manual-claim meer; de keuze volgt als commando.
    assert "category_choice" not in service.laatste_kwargs.get("options", {})
    resultaat = generatieresultaat(sm)
    assert resultaat["saved_definition_id"]
    did = resultaat["saved_definition_id"]
    record = DefinitieRepository(db_path).get_definitie(did)
    assert record.categorie == "type" and record.version_number == 2
    keuze = record.get_category_choice()
    assert keuze["origin"] == "manual" and keuze["actor"] is None
    assert record.get_category_choice_status()["status"] == "manual_unattributed"
    # Het getoonde opgeslagen record (voor Toepassen) draagt id én versie.
    assert resultaat["saved_record"].id == did
    assert resultaat["saved_record"].version_number == 2


def test_echte_handler_modelvoorstel_maakt_modelevent_en_toont_record(db_path):
    handler, service = _handler(db_path)
    sm = _sm(determined_category="proces", category_reasoning="r")
    with patch(
        "ui.helpers.async_bridge.run_async",
        lambda coro, **kw: __import__("asyncio").run(coro),
    ):
        handler.handle_definition_generation(
            "keurmerk", CONTEXT, _st=MagicMock(), _sm=sm
        )
    resultaat = generatieresultaat(sm)
    record = DefinitieRepository(db_path).get_definitie(
        resultaat["saved_definition_id"]
    )
    assert record.get_category_choice()["origin"] == "model"
    assert record.version_number == 1
    assert resultaat["saved_record"].version_number == 1


# ------------------------------------------------- B: ruwe registratiewrites


def _record_met_keuze_en_historie(db_path: str) -> int:
    repo = DefinitieRepository(db_path)
    did = repo.create_definitie(
        DefinitieRecord(
            begrip="keurmerk",
            definitie="kern",
            categorie="type",
            organisatorische_context=json.dumps(ORG),
            generation_prompt_data=json.dumps(
                {"prompt": "p", SOURCE_REVIEW_HISTORY_KEY: [{"x": 1}], "vreemd": True}
            ),
        )
    )
    for waarde in ("proces", "resultaat"):
        versie = repo.get_definitie(did).version_number
        assert repo.record_category_choice(
            did,
            {},
            waarde=waarde,
            herkomst="editor",
            actor="A",
            actor_source="typed_name",
            updated_by="A",
            expected_version=versie,
        )
    record = repo.get_definitie(did)
    assert len(record.get_category_choice_history()) == 1
    return did


@pytest.mark.parametrize("ruw", [None, "not-json", "null", "[]"])
def test_ruwe_niet_object_registratie_wist_geen_beheerde_gegevens(db_path, ruw):
    did = _record_met_keuze_en_historie(db_path)
    voor = DefinitieRepository(db_path).get_definitie(did)
    registratie_voor = voor.get_generatieregistratie()

    with pytest.raises(ValueError, match="beheerde"):
        DefinitieRepository(db_path).update_definitie(
            did, {"generation_prompt_data": ruw, "toelichting_proces": "n"}, "A"
        )

    na = DefinitieRepository(db_path).get_definitie(did)
    assert na.version_number == voor.version_number
    assert na.toelichting_proces is None  # niets geschreven, ook geen ander veld
    registratie = na.get_generatieregistratie()
    assert registratie == registratie_voor
    assert registratie[CATEGORY_CHOICE_KEY]["value"] == "resultaat"
    assert registratie[CATEGORY_CHOICE_STATE_KEY]["current"] is True
    assert len(registratie[CATEGORY_CHOICE_HISTORY_KEY]) == 1
    assert registratie[SOURCE_REVIEW_HISTORY_KEY] == [{"x": 1}]
    assert registratie["prompt"] == "p" and registratie["vreemd"] is True
    assert na.get_category_choice_status()["status"] == "manual_confirmed"


def test_ruwe_niet_object_registratie_zonder_beheerde_gegevens_blijft_mogelijk(db_path):
    repo = DefinitieRepository(db_path)
    did = repo.create_definitie(
        DefinitieRecord(begrip="k", definitie="kern", categorie="type")
    )
    assert repo.update_definitie(did, {"generation_prompt_data": None}, None)
    assert repo.get_definitie(did).generation_prompt_data is None
