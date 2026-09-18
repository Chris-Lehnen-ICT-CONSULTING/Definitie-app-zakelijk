"""DEF-751 B1 — de editor toont elke opgeslagen categorie verliesvrij.

Patroon test_def743_editor_ui: echte `DefinitionEditTab._render_editor` en
`_save_definition` met een gemockte `st` op een tijdelijke SQLite-database.

* Een record met een schemawaarde buiten de vier appkeuzes (ACT/ENT) opent
  zonder `ValueError`; de selectbox staat op exact die waarde.
* Openen + opslaan zonder categorieactie schrijft dezelfde waarde terug; een
  nieuwe repository-instantie leest hem ongewijzigd terug (geen stille
  herclassificatie naar type/proces).
* Een lege widgetwaarde (alleen mogelijk bij een record zonder categorie)
  overschrijft de opgeslagen waarde niet.
* De categorie-selector volgt het bestaande alleen-lezenbeleid van de editor
  (vastgesteld/gearchiveerd → disabled), zoals de andere velden.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from database.definitie_repository import DefinitieRepository
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import DefinitionEditService
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from ui.components.definition_edit_tab import DefinitionEditTab
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

ACTOR = "Bewerker Blauw"
ORG = ["DJI"]
JUR = ["Strafrecht"]
WET = ["Penitentiaire beginselenwet"]


@pytest.fixture
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    return st.session_state


@pytest.fixture
def repo(tmp_path) -> DefinitionEditRepository:
    return DefinitionEditRepository(str(tmp_path / "editor.db"))


def _mock_st() -> MagicMock:
    """`st` waarvan de selectbox — zoals het echte widget — `options[index]` geeft."""
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


def _record(
    repo: DefinitionEditRepository, categorie: str, status: str = "draft"
) -> int:
    return repo.save(
        Definition(
            begrip=f"begrip-{categorie.lower()}",
            definitie=f"Een synthetische definitie voor {categorie}.",
            categorie=categorie,
            organisatorische_context=list(ORG),
            juridische_context=list(JUR),
            wettelijke_basis=list(WET),
            metadata={"status": status, "created_by": "seed"},
        )
    )


def _tab(repo: DefinitionEditRepository, did: int) -> DefinitionEditTab:
    geladen = DefinitionRepository(repo.db_path).get(did)
    SessionStateManager.set_value("editing_definition_id", did)
    SessionStateManager.set_value("editing_definition", geladen)
    SessionStateManager.set_value("user", ACTOR)
    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    tab.repository = repo
    tab.edit_service = DefinitionEditService(repository=repo, validation_service=None)
    return tab


def _categorie_widget(m: MagicMock, did: int):
    aanroepen = [
        c
        for c in m.selectbox.call_args_list
        if c.kwargs.get("key") == f"edit_{did}_categorie"
    ]
    assert len(aanroepen) == 1
    return aanroepen[0]


@pytest.mark.parametrize("categorie", ["ACT", "ENT"])
def test_schemawaarde_buiten_de_vier_opent_zonder_valueerror_op_exact_die_waarde(
    repo, sessie, categorie
):
    did = _record(repo, categorie)
    tab = _tab(repo, did)
    m = _mock_st()

    with patch("ui.components.definition_edit_tab.st", m):
        tab._render_editor()  # crashte vóór B1 met ValueError op list.index

    widget = _categorie_widget(m, did)
    opties = widget.kwargs.get("options") or widget.args[1]
    assert opties[widget.kwargs["index"]] == categorie
    assert widget.kwargs.get("disabled") is False
    label = widget.kwargs["format_func"](categorie)
    assert "bestaande waarde" in label and "ongewijzigd" in label
    assert SessionStateManager.get_value(f"edit_{did}_categorie") == categorie


@pytest.mark.parametrize("categorie", ["ACT", "ENT", "resultaat"])
def test_openen_en_opslaan_zonder_categorieactie_herclassificeert_niet(
    repo, sessie, categorie
):
    did = _record(repo, categorie)
    tab = _tab(repo, did)
    m = _mock_st()

    with patch("ui.components.definition_edit_tab.st", m):
        tab._render_editor()
        # Een tekstwijziging, geen categorieactie.
        SessionStateManager.set_value(f"edit_{did}_definitie", "Aangepaste tekst.")
        tab._save_definition()

    assert m.success.called, m.error.call_args_list
    # Readback via een nieuwe repository-instantie én via de DB-laag.
    opnieuw = DefinitionRepository(repo.db_path).get(did)
    assert opnieuw.categorie == categorie
    assert opnieuw.definitie == "Aangepaste tekst."
    assert DefinitieRepository(repo.db_path).get_definitie(did).categorie == categorie


def test_lege_widgetwaarde_overschrijft_de_opgeslagen_categorie_niet(repo, sessie):
    did = _record(repo, "type")
    tab = _tab(repo, did)
    m = _mock_st()

    with patch("ui.components.definition_edit_tab.st", m):
        tab._render_editor()
        SessionStateManager.set_value(f"edit_{did}_categorie", "")
        tab._save_definition()

    assert m.success.called, m.error.call_args_list
    assert DefinitionRepository(repo.db_path).get(did).categorie == "type"


@pytest.mark.parametrize("status", ["established", "archived"])
def test_categorie_selector_volgt_het_alleen_lezenbeleid_van_de_editor(
    repo, sessie, status
):
    did = _record(repo, "type", status=status)
    tab = _tab(repo, did)
    m = _mock_st()

    with patch("ui.components.definition_edit_tab.st", m):
        tab._render_editor()

    assert _categorie_widget(m, did).kwargs.get("disabled") is True
