"""DEF-846: de keuzelijst "wettelijke basis" komt uit het regelingenregister.

Eén lijst (besluit Chris 10-10-2026): contextkiezer, bewerk-tab en de
bronbibliotheek gebruiken dezelfde regelingen uit ``config/bronnenlijst.yaml``.
Er mag nergens in ``src`` nog een eigen, hardgecodeerde wettenlijst staan.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from domain.sources.regelingen import register

pytestmark = [pytest.mark.unit]

SRC = Path(__file__).resolve().parents[3] / "src"


def test_contextkiezer_toont_de_labels_uit_het_register():
    from ui.components.enhanced_context_manager_selector import (
        wettelijke_basis_opties,
    )

    assert wettelijke_basis_opties() == register().labels()


def test_geen_eigen_wettenlijst_meer_in_src():
    """Regressieguard: de oude lijsten (WET_OPTIONS, common_laws, ...) zijn weg."""
    verboden = re.compile(
        r"WET_OPTIONS|common_laws|\"Wetboek van Strafvordering \(huidig\)\""
    )
    treffers = [
        f"{pad.relative_to(SRC)}:{nr}"
        for pad in SRC.rglob("*.py")
        for nr, regel in enumerate(pad.read_text(encoding="utf-8").splitlines(), 1)
        if verboden.search(regel)
    ]
    assert treffers == []
