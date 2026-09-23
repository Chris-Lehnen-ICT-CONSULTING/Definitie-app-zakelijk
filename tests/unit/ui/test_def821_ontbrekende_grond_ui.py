"""DEF-821 — ontbrekende betekenisgrond: transport, UI en de echte keten.

* Adapter: de orchestrator-non-success wordt een UI-dict zonder definitie,
  id of oordeel, met de melding compleet onder één additieve sleutel.
* Sessiehulp: het open verzoek draagt soort, ontbrekende grond en vraag;
  verzenden en toepassen lopen via hetzelfde gebonden antwoordmechanisme
  als het ESS-02-conflict (generation_id + invoervingerafdruk, eenmalig).
* Tab: de melding staat apart van definitie en technische fout; modelvelden
  worden uitsluitend als platte tekst getoond (geen HTML/Markdown-injectie).
* Keten: handler → ServiceAdapter → orchestrator → echte PromptServiceV2 →
  fake model (geen netwerk) → echte DefinitionRepository op een tijdelijke
  SQLite. Bij de melding wordt niets opgeslagen; na het expliciet verzonden
  antwoord staat het als DATA in de nieuwe prompt, wordt de kandidaat
  opgeslagen en is het antwoord op het record terug te lezen. Gewijzigde
  invoer maakt een verzonden antwoord ongeldig.

Het echte-widgetbewijs (AppTest in een subprocess achter de offline-gate)
staat in `test_def821_ontbrekende_grond_apptest.py`. Niets hier claimt
modelkwaliteit.
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
    DefinitionResponseV2,
    OrchestratorConfig,
)
from services.modelantwoord import ONTBREKENDE_GROND_SENTINEL
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.prompts.modules.context_awareness_module import verduidelijking_datalijn
from services.prompts.prompt_service_v2 import PromptServiceV2
from services.service_factory import ServiceAdapter
from tests.unit.ui.handlers.test_def751_betekenisconflict_handler import FakeSM
from toetsregels.rule_cache import get_rule_cache
from ui.handlers.definition_generation_handler import DefinitionGenerationHandler
from ui.helpers.betekenisconflict import (
    KEY_INVOER,
    KEY_OPEN,
    KEY_VERZONDEN,
    SOORT_ONTBREKENDE_GROND,
    open_conflict_uit,
    verduidelijking_uit_keten,
    verzend_verduidelijking,
)

pytestmark = [pytest.mark.unit]

GROND = "de dagconventie: werkdagen of kalenderdagen"
VRAAG = "Tellen de drie dagen als werkdagen of als kalenderdagen?"
ANTWOORD = "Werkdagen; de dag van ontvangst telt niet mee"
DEFINITIE = (
    "Reactie die uiterlijk op de derde werkdag na de dag van ontvangst wordt gegeven"
)
BEGRIP = "tijdige reactie"
CONTEXT = {
    "organisatorische_context": ["Proefdienst"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
#: Correctieronde 1: het toegepaste antwoord reist met de vraag als context.
VERWACHT = verduidelijking_uit_keten([{"vraag": VRAAG, "antwoord": ANTWOORD}])
INJECTIE = '<img src=x onerror="alert(1)"> [klik](javascript:alert(1)) **vet**'


def melding_md(
    generation_id: str = "gen-grond-1", grond: str = GROND, vraag: str = VRAAG
) -> dict[str, Any]:
    return {
        "generation_id": generation_id,
        "error_type": "betekenisgrond_ontbreekt",
        "phases_completed": 4,
        "betekenisgrond_ontbreekt": {
            "ontbrekende_grond": grond,
            "vraag": vraag,
            "gemeld_door": "model",
            "begrip": BEGRIP,
            "ontologische_categorie": None,
            "organisatorische_context": ["Proefdienst"],
            "juridische_context": [],
            "wettelijke_basis": [],
            "generation_id": generation_id,
        },
    }


def melding_ui(**kw) -> dict[str, Any]:
    md = melding_md(**kw)
    return ServiceAdapter.to_ui_response(
        ServiceAdapter.__new__(ServiceAdapter),
        DefinitionResponseV2(
            success=False, error=md["betekenisgrond_ontbreekt"]["vraag"], metadata=md
        ),
    )


# ------------------------------------------------------------------ adapter


def test_adapter_transporteert_de_melding_compleet_zonder_definitie_of_oordeel():
    ui = melding_ui()
    assert ui["success"] is False
    assert ui["error_type"] == "betekenisgrond_ontbreekt"
    assert ui["error_message"] == VRAAG
    melding = ui["betekenisgrond_ontbreekt"]
    assert melding == melding_md()["betekenisgrond_ontbreekt"]
    assert "betekenisconflict" not in ui
    assert ui["definitie_origineel"] == "" and ui["definitie_gecorrigeerd"] == ""
    assert "saved_definition_id" not in ui
    assert ui["validation_details"]["violations"] == []
    assert ui["voorbeelden"] == {}


@pytest.mark.parametrize(
    "kapot",
    [
        {"vraag": VRAAG},  # grond ontbreekt
        {"ontbrekende_grond": GROND},  # vraag ontbreekt
        "geen dict",
    ],
)
def test_adapter_neemt_een_onvolledige_melding_niet_over(kapot):
    md = melding_md()
    md["betekenisgrond_ontbreekt"] = kapot
    ui = ServiceAdapter.to_ui_response(
        ServiceAdapter.__new__(ServiceAdapter),
        DefinitionResponseV2(success=False, error="x", metadata=md),
    )
    assert ui["success"] is False
    assert "betekenisgrond_ontbreekt" not in ui


# ------------------------------------------------------------ sessiehulp


def test_open_verzoek_draagt_soort_grond_en_vraag():
    open_verzoek = open_conflict_uit(melding_ui(), "vf-1")
    assert open_verzoek == {
        "generation_id": "gen-grond-1",
        "vingerafdruk": "vf-1",
        "soort": SOORT_ONTBREKENDE_GROND,
        "vraag": VRAAG,
        "ontbrekende_grond": GROND,
        "lezingen": [],
        "begrip": BEGRIP,
    }


def test_open_verzoek_bij_ess02_conflict_blijft_gelijk_met_soort():
    from tests.unit.ui.handlers.test_def751_betekenisconflict_handler import (
        LEZINGEN,
        conflict_ui,
    )

    open_conflict = open_conflict_uit(conflict_ui(), "vf-2")
    assert open_conflict["soort"] == "betekenisconflict"
    assert open_conflict["lezingen"] == LEZINGEN
    assert "ontbrekende_grond" not in open_conflict


# ------------------------------------------------------------------- tab


def tab_resultaat(generation_id: str = "gen-grond-1", **kw) -> dict[str, Any]:
    return {
        "begrip": BEGRIP,
        "agent_result": melding_ui(generation_id=generation_id, **kw),
        "saved_record": None,
        "saved_definition_id": None,
        "determined_category": None,
    }


def open_verzoek(generation_id: str = "gen-grond-1") -> dict[str, Any]:
    return {
        "generation_id": generation_id,
        "vingerafdruk": "vf-1",
        "soort": SOORT_ONTBREKENDE_GROND,
        "vraag": VRAAG,
        "ontbrekende_grond": GROND,
        "lezingen": [],
        "begrip": BEGRIP,
    }


class TabSM:
    data: dict[str, Any] = {}

    @classmethod
    def get_value(cls, key, default=None):
        return cls.data.get(key, default)

    @classmethod
    def set_value(cls, key, value):
        cls.data[key] = value

    @classmethod
    def clear_value(cls, key):
        cls.data.pop(key, None)


def _tab():
    from ui.components.definition_generator_tab import DefinitionGeneratorTab

    tab = DefinitionGeneratorTab.__new__(DefinitionGeneratorTab)
    for naam in (
        "duplicate_renderer",
        "sources_renderer",
        "validation_renderer",
        "category_renderer",
        "voorbeelden_renderer",
        "workflow_service",
        "category_service",
    ):
        setattr(tab, naam, MagicMock())
    return tab


@pytest.fixture
def render():
    from ui.components import definition_generator_tab as module

    def _render(resultaat: dict[str, Any], sessie: dict[str, Any], knop: bool = False):
        TabSM.data = dict(sessie)
        st = MagicMock()
        st.button.return_value = knop
        tab = _tab()
        with (
            patch.object(module, "st", st),
            patch.object(module, "SessionStateManager", TabSM),
            patch.object(tab, "_render_definition_section") as definitie,
            patch.object(tab, "_render_validation_section") as validatie,
            patch.object(tab, "_render_voorbeelden_section") as voorbeelden,
            patch.object(tab, "_render_generation_status") as status,
        ):
            tab._render_generation_results(resultaat)
        return st, {
            "definitie": definitie,
            "validatie": validatie,
            "voorbeelden": voorbeelden,
            "status": status,
        }

    return _render


_OPGEMAAKT = ("markdown", "warning", "info", "caption", "write", "success", "error")


def _args(mock: MagicMock, namen: tuple[str, ...]) -> list[str]:
    return [
        str(a)
        for naam in namen
        for c in getattr(mock, naam).call_args_list
        for a in (*c.args, *c.kwargs.values())
    ]


def test_tab_toont_grond_en_vraag_als_modelmelding_apart_van_definitie(render):
    st, secties = render(tab_resultaat(), {KEY_OPEN: open_verzoek()})
    platte_tekst = _args(st, ("text",))
    assert any(GROND in t for t in platte_tekst)
    assert any(VRAAG in t for t in platte_tekst)
    opgemaakt = " ".join(_args(st, _OPGEMAAKT))
    assert "melding van het model" in opgemaakt
    assert "geen definitie" in opgemaakt
    assert "betekenisgrond" in opgemaakt.lower()
    # Geen resultaat-, status-, validatie- of voorbeeldensectie; geen succes.
    for naam, sectie in secties.items():
        assert not sectie.called, naam
    assert not st.success.called
    assert not st.error.called
    # Antwoordveld (key-only) en expliciete verzendknop.
    assert st.text_area.call_args.kwargs["key"] == KEY_INVOER
    assert "value" not in st.text_area.call_args.kwargs
    assert st.button.called


def test_tab_modelvelden_nooit_als_markdown_of_html(render):
    st, _ = render(
        tab_resultaat(grond=INJECTIE, vraag=INJECTIE),
        {
            KEY_OPEN: {
                **open_verzoek(),
                "ontbrekende_grond": INJECTIE,
                "vraag": INJECTIE,
            }
        },
    )
    assert any(INJECTIE in t for t in _args(st, ("text",)))
    for tekst in _args(st, _OPGEMAAKT):
        assert "onerror" not in tekst and "javascript:" not in tekst, tekst
    for c in st.markdown.call_args_list:
        assert not c.kwargs.get("unsafe_allow_html"), c


def test_tab_verzenden_bindt_antwoord_aan_open_verzoek(render):
    render(
        tab_resultaat(),
        {KEY_OPEN: open_verzoek(), KEY_INVOER: f"  {ANTWOORD} "},
        knop=True,
    )
    assert TabSM.data[KEY_VERZONDEN] == {
        "generation_id": "gen-grond-1",
        "vingerafdruk": "vf-1",
        "tekst": ANTWOORD,
    }


def test_tab_verzonden_antwoord_ook_als_platte_tekst(render):
    st, _ = render(
        tab_resultaat(),
        {
            KEY_OPEN: open_verzoek(),
            KEY_VERZONDEN: {
                "generation_id": "gen-grond-1",
                "vingerafdruk": "vf-1",
                "tekst": INJECTIE,
            },
        },
    )
    assert any(INJECTIE in t for t in _args(st, ("text",)))
    for tekst in _args(st, _OPGEMAAKT):
        assert "onerror" not in tekst, tekst


def test_tab_zonder_passend_open_verzoek_geen_verzendknop(render):
    for sessie in ({KEY_OPEN: open_verzoek("gen-2")}, {}):
        st, _ = render(tab_resultaat("gen-grond-1"), sessie, knop=True)
        assert not st.button.called and not st.text_area.called
        assert "opnieuw" in " ".join(_args(st, _OPGEMAAKT)).lower()


# ------------------------------------------------------------------ keten


@pytest.fixture
def _verse_regelcache():
    get_rule_cache().clear_cache()


class FakeModel:
    """Meldt ontbrekende grond zolang de prompt het antwoord niet als DATA draagt."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def generate_definition(self, prompt: str, **kwargs) -> AIGenerationResult:
        self.prompts.append(prompt)
        if verduidelijking_datalijn(VERWACHT) in prompt:
            tekst = DEFINITIE
        else:
            tekst = f"{ONTBREKENDE_GROND_SENTINEL} " + json.dumps(
                {"ontbrekende_grond": GROND, "vraag": VRAAG}, ensure_ascii=False
            )
        return AIGenerationResult(
            text=tekst, model="fake", tokens_used=1, generation_time=0.0
        )


def _keten(db_path: str, monkeypatch, model: Any = None):
    from voorbeelden import unified_voorbeelden

    monkeypatch.setattr(
        unified_voorbeelden,
        "genereer_alle_voorbeelden_async",
        AsyncMock(return_value={}),
    )
    model = model or FakeModel()
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
    return handler, model, validation, cleaning


def _genereer(handler, sm, st=None, context=CONTEXT) -> None:
    with patch(
        "ui.helpers.async_bridge.run_async", lambda coro, **kw: asyncio.run(coro)
    ):
        handler.handle_definition_generation(
            BEGRIP, context, _st=st or MagicMock(), _sm=sm
        )


def _aantal(db_path: str) -> int:
    with sqlite3.connect(db_path) as conn:
        (aantal,) = conn.execute(
            "SELECT COUNT(*) FROM definities WHERE begrip = ?", (BEGRIP,)
        ).fetchone()
    return int(aantal)


@pytest.mark.usefixtures("_verse_regelcache")
def test_keten_melding_dan_antwoord_dan_opslag_en_readback(tmp_path, monkeypatch):
    db_path = str(tmp_path / "def821.db")
    handler, model, validation, cleaning = _keten(db_path, monkeypatch)
    sm = FakeSM()
    assert _aantal(db_path) == 0

    # 1. Melding: niets opgeslagen, niet opgeschoond of gevalideerd, geen succes.
    st1 = MagicMock()
    _genereer(handler, sm, st1)
    agent = sm.data["last_generation_result"]["agent_result"]
    assert agent["success"] is False
    assert agent["betekenisgrond_ontbreekt"]["ontbrekende_grond"] == GROND
    assert agent["betekenisgrond_ontbreekt"]["vraag"] == VRAAG
    assert "betekenisconflict" not in agent
    assert sm.data["last_generation_result"]["saved_definition_id"] is None
    assert _aantal(db_path) == 0
    assert not validation.validate_definition.called
    assert not cleaning.clean_text.called
    assert not st1.success.called and not st1.error.called
    waarschuwing = " ".join(str(a) for c in st1.warning.call_args_list for a in c.args)
    assert "betekenisgrond" in waarschuwing.lower() and "geen definitie" in waarschuwing
    assert "betekenisconflict" not in waarschuwing
    open_verzoek = sm.data[KEY_OPEN]
    assert open_verzoek["soort"] == SOORT_ONTBREKENDE_GROND
    assert (
        open_verzoek["generation_id"]
        == agent["betekenisgrond_ontbreekt"]["generation_id"]
    )
    assert "editing_definition_id" not in sm.data

    # 2. Expliciet verzenden (zelfde helper als de tab-knop); leeg telt niet.
    assert verzend_verduidelijking(sm, open_verzoek, "   ") is not None
    assert KEY_VERZONDEN not in sm.data
    assert verzend_verduidelijking(sm, open_verzoek, ANTWOORD) is None

    # 3. Hergenereren met ongewijzigde invoer: het antwoord staat als DATA in
    #    het contextblok van de nieuwe prompt; het model definieert.
    st2 = MagicMock()
    _genereer(handler, sm, st2)
    assert len(model.prompts) == 2
    eerste, tweede = model.prompts
    assert ANTWOORD not in eerste
    blok = tweede.split("<context>", 1)[1].split("</context>", 1)[0]
    assert verduidelijking_datalijn(VERWACHT) in blok
    assert st2.success.called
    assert KEY_OPEN not in sm.data and KEY_VERZONDEN not in sm.data

    # 4. Opslag + readback uit de tijdelijke database.
    did = sm.data["last_generation_result"]["saved_definition_id"]
    assert did and sm.data["editing_definition_id"] == did
    assert _aantal(db_path) == 1
    record = DefinitieRepository(db_path).get_definitie(did)
    assert record.definitie == DEFINITIE
    registratie = record.get_generatieregistratie()
    assert registratie["betekenisverduidelijking"] == VERWACHT
    assert verduidelijking_datalijn(VERWACHT) in registratie["prompt"]


@pytest.mark.usefixtures("_verse_regelcache")
def test_keten_gewijzigde_invoer_maakt_verzonden_antwoord_ongeldig(
    tmp_path, monkeypatch
):
    db_path = str(tmp_path / "def821-wijziging.db")
    handler, model, _, _ = _keten(db_path, monkeypatch)
    sm = FakeSM()
    _genereer(handler, sm)
    open_verzoek = sm.data[KEY_OPEN]
    assert verzend_verduidelijking(sm, open_verzoek, ANTWOORD) is None

    # De context wijzigt: het antwoord hoort niet meer bij deze invoer.
    st = MagicMock()
    _genereer(
        handler,
        sm,
        st,
        context={**CONTEXT, "organisatorische_context": ["Andere dienst"]},
    )
    assert len(model.prompts) == 2
    assert ANTWOORD not in model.prompts[1]
    assert st.info.called and "niet toegepast" in str(st.info.call_args)
    assert KEY_VERZONDEN not in sm.data
    # Opnieuw een melding: nieuw open verzoek, niets opgeslagen.
    assert sm.data[KEY_OPEN]["generation_id"] != open_verzoek["generation_id"]
    assert _aantal(db_path) == 0
