"""DEF-846: de keuzelijst "wettelijke basis" komt uit het regelingenregister.

Eén lijst (besluit Chris 10-10-2026): contextkiezer, bewerk-tab en de
bronbibliotheek gebruiken dezelfde regelingen uit ``config/bronnenlijst.yaml``.
Er mag nergens in ``src`` of ``scripts`` nog een eigen, hardgecodeerde
wettenlijst staan.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from domain.sources.regelingen import register

pytestmark = [pytest.mark.unit]

SRC = Path(__file__).resolve().parents[3] / "src"


def test_contextkiezer_rendert_de_registerlabels(monkeypatch):
    """De echte render() geeft de registerlabels als opties aan de wet-kiezer."""
    from unittest.mock import MagicMock

    import ui.components.enhanced_context_manager_selector as mod

    kiezer = mod.EnhancedContextManagerSelector.__new__(
        mod.EnhancedContextManagerSelector
    )
    kiezer.context_adapter = MagicMock()
    kiezer.context_adapter.get_from_session_state.return_value = {
        "wettelijke_basis": ["Wet op de politiegegevens", "Burgerlijk Wetboek"]
    }
    nep_st = MagicMock()
    nep_st.columns.return_value = (MagicMock(), MagicMock(), MagicMock())
    monkeypatch.setattr(mod, "st", nep_st)
    aanroepen: dict[str, dict] = {}

    def opnemen(self, **kwargs):
        aanroepen[kwargs["multiselect_key"]] = kwargs
        return kwargs["current_values"]

    monkeypatch.setattr(
        mod.EnhancedContextManagerSelector, "_render_context_selector", opnemen
    )
    monkeypatch.setattr(
        mod.EnhancedContextManagerSelector, "_render_context_summary", lambda *a: None
    )

    uit = kiezer.render()

    wet = aanroepen["wet_multiselect"]
    assert wet["base_options"] == register().labels()
    # opgeslagen waarden gaan ongewijzigd door (geen stille hernoeming)
    assert wet["current_values"] == ["Wet op de politiegegevens", "Burgerlijk Wetboek"]
    assert uit["wettelijke_basis"] == [
        "Wet op de politiegegevens",
        "Burgerlijk Wetboek",
    ]


def test_geen_eigen_wettenlijst_meer_in_src():
    """Regressieguard: de oude lijsten (WET_OPTIONS, common_laws, ...) zijn weg.

    Doorzocht: src/ en scripts/ (*.py). Niet: src/config/context_wet_mapping.json
    (wordt nergens gelezen; opruimen buiten DEF-846).
    """
    verboden = re.compile(
        r"WET_OPTIONS|common_laws|\"Wetboek van Strafvordering \(huidig\)\""
    )
    treffers = [
        f"{pad.relative_to(SRC.parent)}:{nr}"
        for pad in [*SRC.rglob("*.py"), *(SRC.parent / "scripts").rglob("*.py")]
        for nr, regel in enumerate(pad.read_text(encoding="utf-8").splitlines(), 1)
        if verboden.search(regel)
    ]
    assert treffers == []
