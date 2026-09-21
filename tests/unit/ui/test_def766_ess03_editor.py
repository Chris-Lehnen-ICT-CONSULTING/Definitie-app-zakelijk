"""DEF-766 — de editor-route van ESS-03 met gemockte `st`.

* De verduidelijking bij deze kandidaat reist van het invoerveld naar de
  toetsing (validatiecontext) en wordt na opslaan uit de opgeslagen
  beoordeling hersteld — zonder de definitietekst te wijzigen.
* Opslaan legt de ESS-03-beoordeling van de laatste toetsing vast (gebonden)
  en meldt dat; een niet-gebonden beoordeling wordt benoemd, nooit stil.
* De ESS-03-sectie toont de opgeslagen uitkomst als replay (vier uitkomsten,
  vraag, fout), herkenbaar als AI-beoordeling, en 'verouderd' na wijziging.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from domain.ess03.contract import Intentie
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import DefinitionEditService
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from tests.fixtures.def766_fakes import BINDING, bouw_ess03_beoordeling
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

BEGRIP = "eiland"
TEKST = (
    "Afzonderlijk aaneengesloten landoppervlak dat op het afgesproken peilmoment "
    "volledig door water is omgeven."
)
TOELICHTING = "Synthetische conventie: elk gescheiden aaneengesloten vlak telt als één."
ORG = ["Synthetisch Waterschap"]
CONTEXT = {
    "organisatorische_context": list(ORG),
    "juridische_context": [],
    "wettelijke_basis": [],
}


@pytest.fixture
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    return st.session_state


@pytest.fixture
def repo(tmp_path) -> DefinitionEditRepository:
    return DefinitionEditRepository(str(tmp_path / "ess03-ui.db"))


def _teksten(m: MagicMock) -> str:
    uit: list[str] = []
    for api in ("markdown", "success", "warning", "error", "info", "caption", "text"):
        uit.extend(str(c.args[0]) for c in getattr(m, api).call_args_list if c.args)
    return "\n".join(uit)


def _mock_st(**antwoorden: Any) -> MagicMock:
    m = MagicMock()

    def _per_key(default: Any):
        def _f(*args: Any, **kw: Any) -> Any:
            sleutel = kw.get("key")
            if sleutel in antwoorden:
                return antwoorden[sleutel]
            return default

        return _f

    m.text_input.side_effect = _per_key("")
    m.text_area.side_effect = _per_key("")
    m.button.side_effect = _per_key(False)
    m.columns.side_effect = lambda spec, **kw: [
        MagicMock() for _ in (spec if isinstance(spec, list | tuple) else range(spec))
    ]
    return m


def _beoordeling(scenario="pass", *, verduidelijking=None, tekst=TEKST) -> dict:
    return bouw_ess03_beoordeling(
        BEGRIP,
        tekst,
        CONTEXT,
        None,
        intentie=Intentie(
            toelichting=TOELICHTING, categorie="type", verduidelijking=verduidelijking
        ),
        scenario=scenario,
    )


def _definition(**meta: Any) -> Definition:
    metadata: dict[str, Any] = {"status": "draft", "created_by": "generator"}
    metadata.update(meta)
    return Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        toelichting=TOELICHTING,
        categorie="type",
        organisatorische_context=list(ORG),
        juridische_context=[],
        wettelijke_basis=[],
        metadata=metadata,
    )


def _tab(repo):
    from ui.components.definition_edit_tab import DefinitionEditTab

    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    tab.repository = repo
    tab.edit_service = DefinitionEditService(repository=repo, validation_service=None)
    # R1: de actuele binding komt in de app uit de gecachte dienst; hier de
    # binding van de fake-dienst (geen container in deze tests).
    tab._ess03_binding = lambda: BINDING  # type: ignore[method-assign]
    return tab


def _vul_editor(did: int, geladen: Definition, **extra: Any) -> None:
    SessionStateManager.set_value("editing_definition_id", did)
    SessionStateManager.set_value("editing_definition", geladen)
    waarden = {
        "begrip": geladen.begrip,
        "definitie": geladen.definitie,
        "organisatorische_context": list(geladen.organisatorische_context or []),
        "juridische_context": [],
        "wettelijke_basis": [],
        "categorie": "type",
        "toelichting": geladen.toelichting or "",
        "status": "draft",
        **extra,
    }
    for veld, waarde in waarden.items():
        SessionStateManager.set_value(f"edit_{did}_{veld}", waarde)


def test_sessiebeoordeling_ess03_komt_uit_de_laatste_toetsing(sessie):
    from ui.components.definition_edit_tab import DefinitionEditTab

    assert DefinitionEditTab._sessiebeoordeling_ess03() is None
    SessionStateManager.set_value(
        "edit_last_validation", {"ess03_assessment": {"a": 1}}
    )
    assert DefinitionEditTab._sessiebeoordeling_ess03() == {"a": 1}
    SessionStateManager.set_value(
        "edit_last_validation", {"raw_v2": {"ess03_assessment": {"b": 2}}}
    )
    assert DefinitionEditTab._sessiebeoordeling_ess03() == {"b": 2}


def test_verduidelijking_reist_naar_de_toetsing_zonder_tekstwijziging(repo, sessie):
    did = repo.save(_definition())
    geladen = DefinitionRepository(repo.db_path).get(did)
    _vul_editor(did, geladen, ess03_verduidelijking="Peil P is het zomerpeil.")
    tab = _tab(repo)
    ontvangen: dict[str, Any] = {}

    def _vang(definition, geladen_meta):
        from services.definition_edit_service import bouw_validatiecontext

        ontvangen["definition"] = definition
        ontvangen["ctx"] = bouw_validatiecontext(definition, geladen_meta)
        return {"valid": False}

    tab.edit_service._validate_definition = _vang  # type: ignore[method-assign]
    m = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m):
        tab._validate_definition()
    assert ontvangen["ctx"]["ess03_verduidelijking"] == "Peil P is het zomerpeil."
    assert ontvangen["ctx"]["toelichting"] == TOELICHTING
    assert ontvangen["ctx"]["categorie"] == "type"
    assert ontvangen["definition"].definitie == TEKST  # tekst ongewijzigd


def test_opslaan_legt_gebonden_ess03_beoordeling_vast_en_meldt_dat(repo, sessie):
    did = repo.save(_definition())
    geladen = DefinitionRepository(repo.db_path).get(did)
    _vul_editor(did, geladen)
    SessionStateManager.set_value("user", "tester")
    SessionStateManager.set_value(
        "edit_last_validation",
        {"ess03_assessment": _beoordeling("fail"), "raw_v2": {}},
    )
    tab = _tab(repo)
    m = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m):
        tab._save_definition()
    vers = DefinitionRepository(repo.db_path).get(did)
    assert vers.metadata["ess03_assessment"] == _beoordeling("fail")
    assert "ESS-03" in _teksten(m) and "opgeslagen" in _teksten(m).lower()


def test_opslaan_benoemt_een_niet_gebonden_ess03_beoordeling(repo, sessie):
    did = repo.save(_definition())
    geladen = DefinitionRepository(repo.db_path).get(did)
    _vul_editor(did, geladen, definitie=TEKST + " Aangepast.")
    SessionStateManager.set_value("user", "tester")
    SessionStateManager.set_value(
        "edit_last_validation", {"ess03_assessment": _beoordeling("pass"), "raw_v2": {}}
    )
    tab = _tab(repo)
    m = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m):
        tab._save_definition()
    vers = DefinitionRepository(repo.db_path).get(did)
    assert vers.metadata.get("ess03_assessment") is None
    tekst = _teksten(m)
    assert "ESS-03" in tekst and "niet opgeslagen" in tekst.lower()
    assert "gewijzigd" in tekst


def test_ess03_sectie_toont_replay_en_verouderd_na_wijziging(repo, sessie):
    did = repo.save(
        _definition(ess03_assessment=_beoordeling("insufficient", verduidelijking=None))
    )
    geladen = DefinitionRepository(repo.db_path).get(did)
    _vul_editor(did, geladen)
    tab = _tab(repo)
    m = _mock_st()
    with (
        patch("ui.components.definition_edit_tab.st", m),
        patch("ui.components.validation_view.st", m),
    ):
        tab._render_ess03_section(geladen)
    tekst = _teksten(m)
    assert "ESS-03" in tekst
    assert "Onvoldoende informatie" in tekst  # R9: eigen label
    assert "Vraag: Binnen welk register en welke populatie geldt het nummer?" in tekst
    assert "AI-beoordeling" in tekst

    # Na een tekstwijziging in de editor is de opgeslagen beoordeling verouderd.
    SessionStateManager.set_value(f"edit_{did}_definitie", TEKST + " Aangepast.")
    m2 = _mock_st()
    with (
        patch("ui.components.definition_edit_tab.st", m2),
        patch("ui.components.validation_view.st", m2),
    ):
        tab._render_ess03_section(geladen)
    tekst2 = _teksten(m2)
    assert "verouderd" in tekst2.lower() or "gewijzigd" in tekst2.lower()
    assert "Vraag: Binnen welk register" not in tekst2


def test_verduidelijking_wordt_uit_de_eigen_recordwaarde_hersteld(repo, sessie):
    # Correctieronde 1 (R5): de recordwaarde telt, niet de beoordeling.
    did = repo.save(
        _definition(
            ess03_verduidelijking="Peil P.",
            ess03_assessment=_beoordeling("pass", verduidelijking="Peil P."),
        )
    )
    geladen = DefinitionRepository(repo.db_path).get(did)
    assert geladen.metadata["ess03_verduidelijking"] == "Peil P."


def test_opslaan_vervoert_de_actuele_verduidelijking_ook_bewust_leeg(repo, sessie):
    # R5: het veld reist expliciet mee bij Opslaan; wissen wordt "" (geen
    # terugval op de eerder opgeslagen tekst), ook zonder nieuwe beoordeling.
    did = repo.save(
        _definition(
            ess03_verduidelijking="Peil P.",
            ess03_assessment=_beoordeling("pass", verduidelijking="Peil P."),
        )
    )
    geladen = DefinitionRepository(repo.db_path).get(did)
    _vul_editor(did, geladen, ess03_verduidelijking="")
    SessionStateManager.set_value("user", "tester")
    tab = _tab(repo)
    m = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m):
        tab._save_definition()
    vers = DefinitionRepository(repo.db_path).get(did)
    assert vers.metadata["ess03_verduidelijking"] == ""
    # De oude beoordeling blijft als historie, maar is niet meer actueel.
    from services.definition_edit_service import ess03_uitkomst_van_definition

    uitkomst = ess03_uitkomst_van_definition(vers, binding=BINDING)
    assert uitkomst["status"] == "review_required"
    assert uitkomst["review"]["assessment"]["historical"] is True
    # Nieuwe verduidelijking zonder beoordeling: bewaard en heropend.
    _vul_editor(did, vers, ess03_verduidelijking="Nieuw antwoord.")
    with patch("ui.components.definition_edit_tab.st", _mock_st()):
        tab._save_definition()
    assert (
        DefinitionRepository(repo.db_path).get(did).metadata["ess03_verduidelijking"]
        == "Nieuw antwoord."
    )
