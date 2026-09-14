"""DEF-622 reviewbevinding 2 — de editor vergelijkt met de actuele tekst.

`DefinitionEditTab._render_generation_prompt_section` toont de tekstvergelijking
(kern vóór nabewerking versus eindtekst) alleen zolang de zin nog de
generatie-eindtekst is. De vergelijking hoorde tegen het geladen record te
gaan, maar de expert typt in de editor: zodra de widgetwaarde
(`edit_<id>_definitie`) afwijkt van de eindtekst, is de melding met de oude
eindtekst misleidend (reviewrapport, bevinding 2). De bewijscontrole bindt
daarom aan de actuele, recordgebonden widgetwaarde; zonder widgetwaarde geldt
het record.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from services.interfaces import Definition
from ui.components.definition_edit_tab import DefinitionEditTab
from ui.components.tekstwijziging import MELDING_TEKST_AANGEPAST
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

KERN_RUW = "de controle die op dossiers wordt uitgevoerd"
EIND = "Controle die op dossiers wordt uitgevoerd."
HERSCHREVEN = "Controle die door de expert op dossiers wordt uitgevoerd."


@pytest.fixture
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    return st.session_state


def _definitie(definitie_id: int = 41) -> Definition:
    return Definition(
        id=definitie_id,
        begrip="controle",
        definitie=EIND,
        organisatorische_context=["Team Koper"],
        metadata={
            "generation_prompt_data": {
                "prompt": "Definieer controle",
                "definitie_kern_geextraheerd": KERN_RUW,
                "definitie_eindtekst": EIND,
                "tekst_na_generatie_aangepast": True,
            }
        },
    )


def _mock_st() -> MagicMock:
    m = MagicMock()
    m.expander.return_value.__enter__ = lambda s: s
    m.expander.return_value.__exit__ = lambda s, *a: False
    return m


def _render(definitie: Definition) -> MagicMock:
    m = _mock_st()
    with (
        patch("ui.components.definition_edit_tab.st", m),
        patch("ui.components.tekstwijziging.st", m),
        patch("ui.components.prompt_debug_section.PromptDebugSection.render"),
    ):
        DefinitionEditTab(repository=MagicMock())._render_generation_prompt_section(
            definitie
        )
    return m


def _meldingen(m: MagicMock) -> list[str]:
    return [str(c.args[0]) for c in m.warning.call_args_list if c.args]


def test_ongewijzigde_editor_toont_de_vergelijking(sessie):
    definitie = _definitie()
    SessionStateManager.set_value(f"edit_{definitie.id}_definitie", EIND)

    m = _render(definitie)

    assert MELDING_TEKST_AANGEPAST in _meldingen(m)


def test_zonder_widgetwaarde_geldt_het_record(sessie):
    m = _render(_definitie())

    assert MELDING_TEKST_AANGEPAST in _meldingen(m)


def test_herschreven_tekst_in_de_editor_verbergt_de_oude_vergelijking(sessie):
    definitie = _definitie()
    SessionStateManager.set_value(f"edit_{definitie.id}_definitie", HERSCHREVEN)

    m = _render(definitie)

    assert MELDING_TEKST_AANGEPAST not in _meldingen(m)
    assert m.expander.call_args_list == []


def test_widgetwaarde_van_een_ander_record_telt_niet(sessie):
    definitie = _definitie(41)
    SessionStateManager.set_value("edit_99_definitie", HERSCHREVEN)

    m = _render(definitie)

    assert MELDING_TEKST_AANGEPAST in _meldingen(m)
