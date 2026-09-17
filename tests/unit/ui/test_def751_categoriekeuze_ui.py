"""DEF-751 B2 — de UI brengt de categoriekeuze over; alleen echte acties tellen.

* Generatiehandler: alleen een modelvoorstel reist als
  `options["category_choice"] = {"origin": "model", …}` naar de service;
  een handmatige override is een keuzeactie en wordt ná de opslag via het
  expliciete commando vastgelegd (herreview 2) — nooit als aanvraagclaim en
  nooit met actor (de generator-tab kent geen identiteit).
* Editor-opslaan met gewijzigde categorie: `category_choice_input` met
  herkomst `editor` en de bestaande lokale actorbron (`_handelende_gebruiker`);
  readback via nieuwe repository na sluiten; zonder categoriewijziging geen
  event; heropenen + opslaan maakt geen tweede event.
* Toepassen-actie (post-generatie): `CategoryService.update_category_v2`
  legt een `manual`-event vast zonder gefabriceerde `web_user`.
* Voorstel/override-state: term- of contextwissel wist het modelvoorstel én
  de handmatige override; "Aanpassen?" terug op leeg trekt de override in.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
import streamlit as st

from database.definitie_repository import DefinitieRepository
from services.category_service import CategoryService
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import DefinitionEditService
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from ui.components.definition_edit_tab import DefinitionEditTab
from ui.handlers.definition_generation_handler import DefinitionGenerationHandler
from ui.renderers.global_context_renderer import GlobalContextRenderer
from ui.session_state import SessionStateManager

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
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    return st.session_state


# ------------------------------------------------------------ handler


def _handler() -> DefinitionGenerationHandler:
    return DefinitionGenerationHandler(
        checker=MagicMock(), definition_service=MagicMock(), repository=MagicMock()
    )


def _sm(**waarden):
    sessie = {"generation_options": {"force_generate": True}, **waarden}
    sm = MagicMock()
    sm.get_value = Mock(side_effect=lambda k, d=None: sessie.get(k, d))
    return sm


def _generatie_options(handler: DefinitionGenerationHandler) -> dict[str, Any]:
    aanroep = handler.definition_service.generate_definition.call_args
    assert aanroep is not None, "geen modelaanroep"
    return aanroep.kwargs["options"]


def test_handler_geeft_alleen_het_modelvoorstel_als_herkomst_door():
    handler = _handler()
    handler.definition_service.to_ui_response.return_value = {"success": False}
    with patch("ui.helpers.async_bridge.run_async", lambda coro, **kw: coro):
        handler.handle_definition_generation(
            "keurmerk",
            CONTEXT,
            _st=MagicMock(),
            _sm=_sm(
                determined_category="proces",
                category_reasoning="werkwoordvorm",
                category_scores={"proces": 0.7},
            ),
        )
    options = _generatie_options(handler)
    assert options["category_choice"] == {
        "origin": "model",
        "reasoning": "werkwoordvorm",
        "scores": {"proces": 0.7},
    }
    assert "actor" not in options["category_choice"]
    assert options["force_generate"] is True


def test_handler_stuurt_een_override_niet_als_aanvraagclaim_mee():
    """Herreview 2: de handmatige override is een keuzeactie en wordt ná de
    opslag via het commando vastgelegd (zie test_def751_review2_reproducties),
    niet als generieke `manual`-claim in de aanvraagopties."""
    handler = _handler()
    handler.definition_service.to_ui_response.return_value = {"success": False}
    with patch("ui.helpers.async_bridge.run_async", lambda coro, **kw: coro):
        handler.handle_definition_generation(
            "keurmerk",
            CONTEXT,
            _st=MagicMock(),
            _sm=_sm(manual_ontological_category="TYPE", determined_category="proces"),
        )
    options = _generatie_options(handler)
    assert "category_choice" not in options
    assert (
        handler.definition_service.generate_definition.call_args.kwargs[
            "categorie"
        ].value
        == "type"
    )
    # Zonder opgeslagen concept (success False) geen commando en geen claim.
    handler.repository.record_category_choice.assert_not_called()


# ------------------------------------------------------------ editor


@pytest.fixture
def repo(tmp_path) -> DefinitionEditRepository:
    return DefinitionEditRepository(str(tmp_path / "editor.db"))


def _mock_st() -> MagicMock:
    m = MagicMock()

    def _selectbox(*args: Any, **kw: Any) -> Any:
        opties = kw.get("options") or (args[1] if len(args) > 1 else [])
        if kw.get("key") is not None:
            SessionStateManager.set_value(kw["key"], opties[kw.get("index", 0)])
        return opties[kw.get("index", 0)]

    m.selectbox.side_effect = _selectbox
    m.multiselect.side_effect = lambda *a, **kw: list(kw.get("default") or [])
    m.text_input.side_effect = lambda *a, **kw: kw.get("value", "")
    m.text_area.side_effect = lambda *a, **kw: ""
    m.button.side_effect = lambda *a, **kw: False
    m.columns.side_effect = lambda spec, **kw: [
        MagicMock() for _ in (spec if isinstance(spec, list | tuple) else range(spec))
    ]
    return m


def _record(repo: DefinitionEditRepository, categorie: str = "type") -> int:
    return repo.save(
        Definition(
            begrip="keurmerk",
            definitie="Een synthetische definitie.",
            categorie=categorie,
            organisatorische_context=list(ORG),
            juridische_context=list(JUR),
            wettelijke_basis=list(WET),
            metadata={"status": "draft", "created_by": "seed"},
        )
    )


def _tab(
    repo: DefinitionEditRepository, did: int, actor: str | None
) -> DefinitionEditTab:
    geladen = DefinitionRepository(repo.db_path).get(did)
    SessionStateManager.set_value("editing_definition_id", did)
    SessionStateManager.set_value("editing_definition", geladen)
    if actor is not None:
        SessionStateManager.set_value("edit_reviewer_name_input", actor)
    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    tab.repository = repo
    tab.edit_service = DefinitionEditService(repository=repo, validation_service=None)
    return tab


def _teksten(m: MagicMock) -> str:
    uit: list[str] = []
    for api in ("markdown", "caption", "info", "warning", "success", "error", "write"):
        uit.extend(str(c.args[0]) for c in getattr(m, api).call_args_list if c.args)
    return "\n".join(uit)


@pytest.mark.parametrize(
    ("actor", "status"),
    [("Reviewer Rood", "manual_confirmed"), (None, "manual_unattributed")],
)
def test_editor_opslaan_met_gewijzigde_categorie_legt_editorkeuze_vast(
    repo, sessie, actor, status
):
    did = _record(repo)
    tab = _tab(repo, did, actor)
    m = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m):
        tab._render_editor()
        SessionStateManager.set_value(f"edit_{did}_categorie", "proces")
        tab._save_definition()
    assert m.success.called, m.error.call_args_list

    record = DefinitieRepository(repo.db_path).get_definitie(did)
    assert record.categorie == "proces"
    keuze = record.get_category_choice()
    assert keuze["origin"] == "editor" and keuze["actor"] == actor
    assert keuze["actor_source"] == ("typed_name" if actor else None)
    assert record.get_category_choice_status()["status"] == status

    # Heropenen + opslaan zonder categorieactie: geen tweede event, status blijft.
    tab2 = _tab(repo, did, actor)
    m2 = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m2):
        tab2._render_editor()
        SessionStateManager.set_value(f"edit_{did}_definitie", "Andere tekst.")
        tab2._save_definition()
    assert m2.success.called, m2.error.call_args_list
    record2 = DefinitieRepository(repo.db_path).get_definitie(did)
    assert record2.get_category_choice_history() == []
    assert record2.get_category_choice_status()["status"] == status
    assert record2.get_definitie_tekst() == "Andere tekst."


def test_editor_toont_herkomststatus_en_maakt_geen_event_zonder_categoriewijziging(
    repo, sessie
):
    did = _record(repo, "ENT")
    tab = _tab(repo, did, "Reviewer Rood")
    m = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m):
        tab._render_editor()
        tab._save_definition()
    assert "herkomst onbekend" in _teksten(m).lower()
    record = DefinitieRepository(repo.db_path).get_definitie(did)
    assert record.get_category_choice() is None
    assert record.get_category_choice_status()["status"] == "unknown_origin"


# ------------------------------------------------------------ toepassen


def test_toepassen_actie_legt_manual_event_vast_zonder_web_user(tmp_path):
    db = DefinitieRepository(str(tmp_path / "apply.db"))
    did = DefinitionRepository(db.db_path).save(
        Definition(
            begrip="keurmerk",
            definitie="x",
            categorie="type",
            organisatorische_context=list(ORG),
            metadata={"status": "draft"},
        )
    )
    resultaat = CategoryService(db).update_category_v2(
        did, "proces", user=None, expected_version=1
    )
    assert resultaat.success, resultaat.message
    record = DefinitieRepository(db.db_path).get_definitie(did)
    assert record.categorie == "proces" and record.version_number == 2
    keuze = record.get_category_choice()
    assert keuze["origin"] == "manual" and keuze["actor"] is None
    assert record.updated_by != "web_user"
    assert record.get_category_choice_status()["status"] == "manual_unattributed"
    # Een verouderde kandidaatversie is een conflict, geen stille keuze.
    verouderd = CategoryService(db).update_category_v2(
        did, "type", user=None, expected_version=1
    )
    assert verouderd.success is False and "versieconflict" in verouderd.message
    assert DefinitieRepository(db.db_path).get_definitie(did).categorie == "proces"


# ------------------------------------------------------------ override-state


def _renderer_met_term(sessie, oude_term: str, nieuwe_term: str) -> None:
    renderer = GlobalContextRenderer.__new__(GlobalContextRenderer)
    SessionStateManager.set_value("begrip", oude_term)
    SessionStateManager.set_value("determined_category", "proces")
    SessionStateManager.set_value("manual_ontological_category", "TYPE")
    m = MagicMock()
    m.text_input = Mock(return_value=nieuwe_term)
    with patch("ui.renderers.global_context_renderer._default_st", m):
        renderer.render_begrip_input()


def test_termwissel_wist_voorstel_en_override(sessie):
    _renderer_met_term(sessie, "keurmerk", "vergunning")
    assert SessionStateManager.get_value("determined_category") is None
    assert SessionStateManager.get_value("manual_ontological_category") is None


def test_ongewijzigde_term_behoudt_voorstel_en_override(sessie):
    _renderer_met_term(sessie, "keurmerk", "keurmerk")
    assert SessionStateManager.get_value("determined_category") == "proces"
    assert SessionStateManager.get_value("manual_ontological_category") == "TYPE"


def test_contextwissel_wist_voorstel_en_override(sessie):
    renderer = GlobalContextRenderer.__new__(GlobalContextRenderer)
    SessionStateManager.set_value("begrip", "keurmerk")
    SessionStateManager.set_value("determined_category", "proces")
    SessionStateManager.set_value("manual_ontological_category", "TYPE")
    SessionStateManager.set_value(
        "classification_basis", "keurmerk|" + repr({"organisatorische_context": ["OM"]})
    )
    SessionStateManager.set_value(
        "global_context", {"organisatorische_context": ["DJI"]}
    )
    m = MagicMock()
    m.selectbox = Mock(return_value="")
    m.columns.side_effect = lambda spec, **kw: [MagicMock(), MagicMock()]
    renderer.render_category_preview(_st=m, _sm=SessionStateManager)
    assert SessionStateManager.get_value("manual_ontological_category") is None


def test_terug_naar_voorstel_trekt_override_in(sessie):
    renderer = GlobalContextRenderer.__new__(GlobalContextRenderer)
    SessionStateManager.set_value("begrip", "keurmerk")
    SessionStateManager.set_value("determined_category", "proces")
    SessionStateManager.set_value("manual_ontological_category", "TYPE")
    SessionStateManager.set_value(
        "global_context", {"organisatorische_context": ["DJI"]}
    )
    m = MagicMock()
    m.selectbox = Mock(return_value="")  # "Aanpassen?" terug op leeg
    m.columns.side_effect = lambda spec, **kw: [MagicMock(), MagicMock()]
    renderer.render_category_preview(_st=m, _sm=SessionStateManager)
    assert SessionStateManager.get_value("manual_ontological_category") is None
    assert SessionStateManager.get_value("determined_category") == "proces"
