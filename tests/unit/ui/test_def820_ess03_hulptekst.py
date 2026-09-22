"""DEF-820 (K2): uitleg dat de ontbrekende conventie aanleveren de weg is.

Sinds DEF-766 vraagt de ESS-03-beoordeling bij een verwijzende formulering
(register, code, conventie) zonder aangeleverde afspraak vrijwel altijd naar
die conventie. Wat deze tests vastleggen: die uitleg verschijnt precies bij
een actuele uitkomst 'onvoldoende informatie' — niet bij de drie andere
uitkomsten, niet bij een technische fout, een niet-beschikbare dienst of een
historische beoordeling — en staat in de help van het
ESS-03-verduidelijkingsveld, zonder de bestaande vervolgstaptekst te
herhalen. Streamlit-aanroepen worden opgevangen (geen browser, geen model).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from domain.ess03.contract import Intentie, beoordeel_telbaarheid
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from tests.fixtures.def766_fakes import BINDING, bouw_ess03_beoordeling
from ui.components import validation_view
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

BEGRIP = "registernummer"
TEKST = "Nummer waarmee een object in het register wordt aangeduid."
TOELICHTING = "Synthetische conventie: het nummer volgt de registerafspraak."
ORG = ["Synthetisch Register"]
CONTEXT = {
    "organisatorische_context": list(ORG),
    "juridische_context": [],
    "wettelijke_basis": [],
}
INTENTIE = Intentie(toelichting=TOELICHTING, categorie="type")

#: Kernwoorden van de nieuwe uitleg: de ontbrekende conventie aanleveren, niet
#: de definitie herschrijven om de vraag te ontlopen.
KERNWOORDEN = ("register", "conventie", "aangeleverd", "ontlopen")


def _uitkomst(scenario: str, *, kandidaattekst: str = TEKST) -> dict[str, Any]:
    """De ESS-03-regeluitkomst van een replay op `kandidaattekst`.

    De beoordeling is aan TEKST gebonden; een afwijkende kandidaattekst maakt
    haar historisch (niet toegepast), zonder AI-aanroep.
    """
    beoordeling = bouw_ess03_beoordeling(
        BEGRIP, TEKST, CONTEXT, None, intentie=INTENTIE, scenario=scenario
    )
    return beoordeel_telbaarheid(
        BEGRIP,
        kandidaattekst,
        CONTEXT,
        None,
        intentie=INTENTIE,
        assessment=beoordeling,
        binding=BINDING,
    ).als_dict()


@pytest.fixture
def getoond(monkeypatch):
    opgevangen: dict[str, list[str]] = {
        api: []
        for api in (
            "markdown",
            "info",
            "warning",
            "success",
            "error",
            "write",
            "text",
            "caption",
        )
    }
    for api in opgevangen:
        monkeypatch.setattr(
            validation_view.st,
            api,
            lambda t, *a, _api=api, **kw: opgevangen[_api].append(str(t)),
            raising=False,
        )
    monkeypatch.setattr(validation_view.st, "button", lambda *a, **kw: False)
    return opgevangen


@pytest.fixture
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    return st.session_state


@pytest.fixture
def repo(tmp_path) -> DefinitionEditRepository:
    return DefinitionEditRepository(str(tmp_path / "def820-ui.db"))


def _mock_st() -> MagicMock:
    m = MagicMock()
    m.text_input.side_effect = lambda *a, **kw: ""
    m.text_area.side_effect = lambda *a, **kw: ""
    m.button.side_effect = lambda *a, **kw: False
    m.columns.side_effect = lambda spec, **kw: [
        MagicMock() for _ in (spec if isinstance(spec, list | tuple) else range(spec))
    ]
    return m


def _help_van(m: MagicMock, sleutel: str) -> str:
    """De help-tekst van het `st.text_area` met deze widgetsleutel."""
    for aanroep in m.text_area.call_args_list:
        if aanroep.kwargs.get("key") == sleutel:
            return str(aanroep.kwargs.get("help") or "")
    raise AssertionError(f"geen text_area met sleutel {sleutel} gerenderd")


def _definition() -> Definition:
    return Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        toelichting=TOELICHTING,
        categorie="type",
        organisatorische_context=list(ORG),
        juridische_context=[],
        wettelijke_basis=[],
        metadata={"status": "draft", "created_by": "generator"},
    )


class TestWeergave:
    def test_uitleg_bij_een_actuele_onvoldoende_informatie(self, getoond):
        validation_view.render_rule_results({"ESS-03": _uitkomst("insufficient")})
        [uitleg] = getoond["caption"]
        for woord in KERNWOORDEN:
            assert woord in uitleg.lower()
        # De vraag en de vervolgstap blijven staan; de uitleg herhaalt ze niet.
        [deel] = getoond["warning"]
        assert "Vraag: Binnen welk register" in deel
        assert "Beantwoord de vraag" in deel
        assert "Beantwoord de vraag" not in uitleg

    @pytest.mark.parametrize(
        "scenario", ["pass", "fail", "not_applicable", "error", "unavailable"]
    )
    def test_geen_uitleg_bij_de_overige_uitkomsten(self, getoond, scenario):
        validation_view.render_rule_results({"ESS-03": _uitkomst(scenario)})
        assert getoond["caption"] == []

    def test_geen_uitleg_bij_een_historische_beoordeling(self, getoond):
        detail = _uitkomst("insufficient", kandidaattekst=TEKST + " Aangepast.")
        assert detail["review"]["assessment"]["historical"] is True
        validation_view.render_rule_results({"ESS-03": detail})
        assert getoond["caption"] == []


def test_help_van_het_verduidelijkingsveld_legt_de_conventie_uit(repo, sessie):
    from ui.components.definition_edit_tab import DefinitionEditTab

    did = repo.save(_definition())
    geladen = DefinitionRepository(repo.db_path).get(did)
    SessionStateManager.set_value("editing_definition_id", did)
    SessionStateManager.set_value("editing_definition", geladen)
    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    m = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m):
        tab._render_editor()
    hulp = _help_van(m, f"edit_{did}_ess03_verduidelijking").lower()
    for woord in KERNWOORDEN:
        assert woord in hulp
