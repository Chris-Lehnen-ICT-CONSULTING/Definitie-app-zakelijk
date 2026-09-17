"""DEF-751 stap 2 — de echte keten: conflict → expliciete verduidelijking → nieuwe
prompt → opslag → readback (tijdelijke SQLite).

Handler → ServiceAdapter → DefinitionOrchestratorV2 → echte PromptServiceV2 →
fake model (geen netwerk) → echte DefinitionRepository. Het fake model meldt
een conflict zolang de prompt geen verduidelijking draagt en levert daarna
een definitie. Bewezen wordt: bij het conflict wordt niets opgeslagen en
niets bevestigd; na het expliciet verzonden antwoord staat de verduidelijking
als DATA in de nieuwe prompt, wordt het concept opgeslagen en is de
verduidelijking op het record herleidbaar als gebruikersbedoeling — de
categorieherkomst is identiek aan die van een gewone generatie (B2).
Gewijzigde invoer (bronwissel) laat een verzonden antwoord vervallen.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from database.definitie_repository import DefinitieRepository
from integration.definitie_checker import CheckAction
from services.definition_repository import DefinitionRepository
from services.interfaces import (
    AIGenerationResult,
    CleaningResult,
    OrchestratorConfig,
)
from services.modelantwoord import CONFLICT_SENTINEL
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.prompts.modules.context_awareness_module import VERDUIDELIJKING_KOP
from services.prompts.prompt_service_v2 import PromptServiceV2
from services.service_factory import ServiceAdapter
from tests.unit.ui.handlers.test_def751_betekenisconflict_handler import FakeSM
from toetsregels.rule_cache import get_rule_cache
from ui.handlers.definition_generation_handler import DefinitionGenerationHandler
from ui.helpers.betekenisconflict import (
    KEY_OPEN,
    KEY_VERZONDEN,
    verzend_verduidelijking,
)

pytestmark = [pytest.mark.unit]

CONTEXT = {
    "organisatorische_context": ["DJI"],
    "juridische_context": ["Strafrecht"],
    "wettelijke_basis": [],
}
DEFINITIE = "Een registratie is de handeling waarbij meetwaarden in een register worden vastgelegd"
VERDUIDELIJKING = "Bedoeld is de handeling van het vastleggen"
MELDING = f"{CONFLICT_SENTINEL} " + json.dumps(
    {
        "vraag": "Is de handeling of het vastgelegde gegeven bedoeld?",
        "lezingen": [
            {
                "lezing": "de handeling",
                "bron": "context: DJI",
                "grond": "DJI-context: activiteit",
            },
            {
                "lezing": "het gegeven",
                "bron": "context: Strafrecht",
                "grond": "strafrechtelijk: het resultaat",
            },
        ],
    },
    ensure_ascii=False,
)


@pytest.fixture(autouse=True)
def _verse_regelcache():
    get_rule_cache().clear_cache()


class FakeModel:
    """Meldt een conflict zolang de prompt geen verduidelijking draagt."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def generate_definition(self, prompt: str, **kwargs) -> AIGenerationResult:
        self.prompts.append(prompt)
        # De instructie noemt het kopje zelf; alleen de DATA-regel (kopje +
        # dubbele punt + antwoord) telt als aanwezige verduidelijking.
        tekst = (
            DEFINITIE
            if f"{VERDUIDELIJKING_KOP}: {VERDUIDELIJKING}" in prompt
            else MELDING
        )
        return AIGenerationResult(
            text=tekst, model="fake", tokens_used=1, generation_time=0.0
        )


def _keten(db_path: str, monkeypatch) -> tuple[DefinitionGenerationHandler, FakeModel]:
    from voorbeelden import unified_voorbeelden

    monkeypatch.setattr(
        unified_voorbeelden,
        "genereer_alle_voorbeelden_async",
        AsyncMock(return_value={}),
    )
    model = FakeModel()
    cleaning = AsyncMock()

    async def _clean(text: str, term: str) -> CleaningResult:
        return CleaningResult(original_text=text, cleaned_text=text, was_cleaned=False)

    cleaning.clean_text.side_effect = _clean
    validation = AsyncMock()
    validation.validate_definition.return_value = {
        "version": "1.0.0",
        "overall_score": 0.8,
        "is_acceptable": True,
        "violations": [],
        "passed_rules": [],
        "detailed_scores": {},
        "system": {},
    }
    orch = DefinitionOrchestratorV2(
        prompt_service=PromptServiceV2(),
        ai_service=model,
        validation_service=validation,
        cleaning_service=cleaning,
        repository=DefinitionRepository(db_path),
        config=OrchestratorConfig(enable_feedback_loop=False, enable_enhancement=False),
    )
    adapter = ServiceAdapter.__new__(ServiceAdapter)
    adapter.orchestrator = orch
    checker = MagicMock()
    checker.check_before_generation.return_value = MagicMock(action=CheckAction.PROCEED)
    handler = DefinitionGenerationHandler(
        checker, adapter, DefinitieRepository(db_path)
    )
    return handler, model


def _genereer(handler, sm, st=None, context=CONTEXT) -> None:
    with patch(
        "ui.helpers.async_bridge.run_async", lambda coro, **kw: asyncio.run(coro)
    ):
        handler.handle_definition_generation(
            "registratie", context, _st=st or MagicMock(), _sm=sm
        )


def _aantal_records(db_path: str) -> int:
    """Alle 'registratie'-records. Let op: het schema seedt zelf al één
    'registratie'-voorbeeldrecord; de tests meten daarom het verschil met de
    stand vóór de eerste generatie."""
    with sqlite3.connect(db_path) as conn:
        (aantal,) = conn.execute(
            "SELECT COUNT(*) FROM definities WHERE begrip = ?", ("registratie",)
        ).fetchone()
    return int(aantal)


def test_conflict_dan_verduidelijking_dan_opslag_en_readback(tmp_path, monkeypatch):
    db_path = str(tmp_path / "keten.db")
    handler, model = _keten(db_path, monkeypatch)
    sm = FakeSM(determined_category="proces", category_reasoning="r")
    basis = _aantal_records(db_path)  # seed-record(s) van het schema

    # 1. Conflict: niets opgeslagen, niets bevestigd, open conflict in de sessie.
    st1 = MagicMock()
    _genereer(handler, sm, st1)
    resultaat = sm.data["last_generation_result"]
    assert resultaat["agent_result"].get("betekenisconflict"), resultaat["agent_result"]
    assert resultaat["agent_result"]["betekenisconflict"]["gemeld_door"] == "model"
    assert resultaat["saved_definition_id"] is None
    assert _aantal_records(db_path) == basis
    assert not st1.success.called and st1.warning.called
    open_conflict = sm.data[KEY_OPEN]
    assert (
        open_conflict["generation_id"]
        == resultaat["agent_result"]["betekenisconflict"]["generation_id"]
    )
    assert "editing_definition_id" not in sm.data

    # 2. Expliciet verzonden antwoord (zelfde helper als de tab-knop).
    assert (
        verzend_verduidelijking(sm, open_conflict, "  ") is not None
    )  # leeg = geen antwoord
    assert KEY_VERZONDEN not in sm.data
    assert verzend_verduidelijking(sm, open_conflict, VERDUIDELIJKING) is None
    assert sm.data[KEY_VERZONDEN]["generation_id"] == open_conflict["generation_id"]

    # 3. Opnieuw genereren met dezelfde invoer: nieuwe prompt draagt de
    #    verduidelijking als DATA in het contextblok; het model definieert.
    st2 = MagicMock()
    _genereer(handler, sm, st2)
    assert len(model.prompts) == 2
    eerste, tweede = model.prompts
    assert f"{VERDUIDELIJKING_KOP}:" not in eerste and VERDUIDELIJKING not in eerste
    assert VERDUIDELIJKING in tweede
    blok = tweede.split("<context>", 1)[1].split("</context>", 1)[0]
    assert VERDUIDELIJKING in blok and "DJI" in blok
    assert tweede.count(VERDUIDELIJKING) == 1
    assert st2.success.called and not st2.info.called
    assert KEY_VERZONDEN not in sm.data and KEY_OPEN not in sm.data

    # 4. Opslag + readback: definitie, verduidelijking als gebruikersbedoeling,
    #    categorieherkomst identiek aan een gewone generatie (modelvoorstel).
    did = sm.data["last_generation_result"]["saved_definition_id"]
    assert did and sm.data["editing_definition_id"] == did
    record = DefinitieRepository(db_path).get_definitie(did)
    assert record.definitie == DEFINITIE
    registratie = record.get_generatieregistratie()
    assert registratie["betekenisverduidelijking"] == VERDUIDELIJKING
    assert VERDUIDELIJKING in registratie["prompt"]
    assert record.categorie == "proces"
    assert record.get_category_choice()["origin"] == "model"
    assert record.get_category_choice_status()["status"] == "model_suggestion"
    # Geen ESS-02-oordeel of bronfeit uit de verduidelijking afgeleid.
    assert "source_review" not in json.dumps(
        registratie.get("betekenisverduidelijking")
    )
    assert _aantal_records(db_path) == basis + 1


def test_bronwissel_na_verzenden_laat_antwoord_vervallen_en_meldt_dat(
    tmp_path, monkeypatch
):
    db_path = str(tmp_path / "keten2.db")
    handler, model = _keten(db_path, monkeypatch)
    sm = FakeSM(determined_category="proces", category_reasoning="r")
    basis = _aantal_records(db_path)
    _genereer(handler, sm)
    open_conflict = sm.data[KEY_OPEN]
    assert verzend_verduidelijking(sm, open_conflict, VERDUIDELIJKING) is None

    # Documentselectie wijzigt (andere bronnen): het antwoord hoort niet meer
    # bij de actuele invoer.
    sm.data["selected_documents"] = ["doc-nieuw"]
    st = MagicMock()
    with (
        patch.object(handler, "_get_document_context", return_value=None),
        patch.object(handler, "_build_document_snippets", return_value=[]),
    ):
        _genereer(handler, sm, st)
    assert len(model.prompts) == 2
    assert VERDUIDELIJKING not in model.prompts[1]
    assert st.info.called and "niet toegepast" in str(st.info.call_args)
    assert KEY_VERZONDEN not in sm.data
    # Zonder verduidelijking meldt het model opnieuw een conflict: weer open,
    # met een nieuwe generation_id, en nog steeds niets opgeslagen.
    assert sm.data[KEY_OPEN]["generation_id"] != open_conflict["generation_id"]
    assert _aantal_records(db_path) == basis


def _render_rag_selector(sm, collecties: list[dict], keuze: list[int]) -> None:
    """De echte RAG-collectieselector van de tab (`_render_rag_collection_selector`)
    met een gemockte `st`: de multiselect levert `keuze`; `collecties` is wat
    `_load_rag_collections()` op dit moment ziet."""
    import types

    from ui import tabbed_interface

    st = MagicMock()
    st.expander.return_value.__enter__ = lambda *a: None
    st.expander.return_value.__exit__ = lambda *a: None
    st.multiselect.return_value = keuze
    tab = types.SimpleNamespace(_load_rag_collections=lambda: collecties)
    with (
        patch.object(tabbed_interface, "st", st),
        patch.object(tabbed_interface, "SessionStateManager", sm),
    ):
        tabbed_interface.TabbedInterface._render_rag_collection_selector(tab)


def _collectie(cid: int) -> dict:
    return {"id": cid, "type_icon": "📁", "name": f"c{cid}", "chunk_count": 0}


def test_pure_rerun_na_antwoord_past_verduidelijking_toe_ook_als_rag_selector_verschijnt(
    tmp_path, monkeypatch
):
    """Browserbevinding 17-09-2026 (echte UI, port 8512): pure rerun na het
    antwoord gaf 'Verduidelijking niet toegepast: … RAG-selectie is
    gewijzigd'. Oorzaak: de eerste generatie maakt via de orchestrator de
    RAG-collectie `user_documents` aan; bij de volgende rerun verschijnt
    daardoor de RAG-selector, die zijn standaard (alle collecties) als
    selectie in de sessie schrijft (None → [1]). De gebruiker koos niets;
    de standaard is geen wijziging van de RAG-selectie."""
    db_path = str(tmp_path / "keten3.db")
    handler, model = _keten(db_path, monkeypatch)
    sm = FakeSM(determined_category="proces", category_reasoning="r")
    basis = _aantal_records(db_path)

    # 1. Eerste generatie: nog geen collecties, dus geen selector gerenderd.
    _render_rag_selector(sm, [], [])
    assert "rag_selected_collection_ids" not in sm.data
    _genereer(handler, sm)
    open_conflict = sm.data[KEY_OPEN]
    assert verzend_verduidelijking(sm, open_conflict, VERDUIDELIJKING) is None

    # 2. Rerun: de collectie bestaat nu; de selector rendert met zijn
    #    standaard (alle collecties) — geen gebruikershandeling.
    _render_rag_selector(sm, [_collectie(1)], [1])
    assert sm.data["rag_selected_collection_ids"] == [1]

    # 3. Opnieuw genereren met ongewijzigde invoer: het antwoord hoort erbij.
    st = MagicMock()
    _genereer(handler, sm, st)
    assert len(model.prompts) == 2
    assert VERDUIDELIJKING in model.prompts[1]
    assert not st.info.called, str(st.info.call_args)
    assert st.success.called
    assert _aantal_records(db_path) == basis + 1


def test_werkelijke_rag_deselectie_laat_antwoord_wel_vervallen(tmp_path, monkeypatch):
    """Tegenproef: kiest de gebruiker wél een andere RAG-selectie dan de
    standaard, dan hoort het antwoord niet meer bij de invoer."""
    db_path = str(tmp_path / "keten4.db")
    handler, model = _keten(db_path, monkeypatch)
    sm = FakeSM(determined_category="proces", category_reasoning="r")
    twee = [_collectie(1), _collectie(2)]
    _render_rag_selector(sm, twee, [1, 2])  # standaard: alle
    _genereer(handler, sm)
    assert verzend_verduidelijking(sm, sm.data[KEY_OPEN], VERDUIDELIJKING) is None

    _render_rag_selector(sm, twee, [1])  # gebruiker deselecteert collectie 2
    st = MagicMock()
    _genereer(handler, sm, st)
    assert len(model.prompts) == 2
    assert VERDUIDELIJKING not in model.prompts[1]
    assert st.info.called and "RAG-selectie" in str(st.info.call_args)
    assert KEY_VERZONDEN not in sm.data
