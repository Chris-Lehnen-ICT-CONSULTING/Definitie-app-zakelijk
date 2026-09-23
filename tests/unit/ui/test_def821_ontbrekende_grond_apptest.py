"""DEF-821 — echte-widgetbewijs voor de melding 'ontbrekende betekenisgrond'.

Streamlit AppTest in een subprocess achter de offline-gate (zelfde opzet als
`test_def751_betekenisconflict_tab.py`). De tab rendert een melding waarvan
de modelvelden HTML- en Markdown-injectie bevatten: die verschijnen alleen
als `st.text`-element, in geen enkel Markdown-, waarschuwings-, succes- of
foutelement. Daarna wordt een antwoord ingevuld en expliciet verzonden.

Topniveau bewust zonder projectimports: de driver draait dit bestand als
script en zet `sys.path` pas in `_driver`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

REPO = Path(__file__).resolve().parents[3]
ANTWOORD = "Werkdagen; de dag van ontvangst telt niet mee"


def _app() -> None:
    # AppTest voert deze functie geïsoleerd uit: alles expliciet importeren.
    import json
    from unittest.mock import MagicMock

    import streamlit as st

    from tests.unit.ui.test_def821_ontbrekende_grond_ui import (
        INJECTIE,
        open_verzoek,
        tab_resultaat,
    )
    from ui.components.definition_generator_tab import DefinitionGeneratorTab
    from ui.helpers.betekenisconflict import KEY_OPEN, KEY_VERZONDEN
    from ui.session_state import SessionStateManager

    SessionStateManager.initialize_session_state(
        {
            "last_generation_result": tab_resultaat(grond=INJECTIE),
            KEY_OPEN: {**open_verzoek(), "ontbrekende_grond": INJECTIE},
        }
    )
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
    tab._render_generation_results(
        SessionStateManager.get_value("last_generation_result")
    )
    st.caption("verzonden=" + json.dumps(SessionStateManager.get_value(KEY_VERZONDEN)))


def _waarneming(at) -> dict:
    captions = [str(c.value) for c in at.caption]
    return {
        "exceptions": [str(e.value) for e in at.exception],
        "warnings": [str(w.value) for w in at.warning],
        "successes": [str(s.value) for s in at.success],
        "errors": [str(e.value) for e in at.error],
        "infos": [str(i.value) for i in at.info],
        "markdown": [str(m.value) for m in at.markdown],
        "captions": captions,
        "text": [str(t.value) for t in at.text],
        "text_areas": [t.key for t in at.text_area],
        "buttons": [b.key for b in at.button],
        "verzonden": next(
            (c.split("=", 1)[1] for c in captions if c.startswith("verzonden=")),
            "<geen caption>",
        ),
    }


def _driver(uit_pad: str) -> None:
    for pad in (str(REPO), str(REPO / "src")):
        if pad not in sys.path:
            sys.path.insert(0, pad)
    from tests import offline_bootstrap

    offline_bootstrap.install()
    from streamlit.testing.v1 import AppTest

    from ui.helpers.betekenisconflict import KEY_INVOER

    w: dict = {"gate_actief": offline_bootstrap.gate_is_actief(), "stappen": {}}

    def _schrijf() -> None:
        Path(uit_pad).write_text(
            json.dumps(w, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    at = AppTest.from_function(_app, default_timeout=120)
    at.run()
    w["stappen"]["getoond"] = _waarneming(at)
    _schrijf()
    at.text_area(key=KEY_INVOER).input(ANTWOORD).run()
    at.button(key="btn_betekenisverduidelijking").click().run()
    w["stappen"]["verzonden"] = _waarneming(at)
    _schrijf()


@pytest.fixture(scope="module")
def w(tmp_path_factory) -> dict:
    uit = tmp_path_factory.mktemp("def821-apptest") / "waarnemingen.json"
    proces = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--driver", str(uit)],
        cwd=str(REPO),
        env=dict(os.environ),
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    deel = uit.read_text(encoding="utf-8") if uit.exists() else "<geen waarnemingen>"
    assert proces.returncode == 0, proces.stderr[-8000:] + "\n" + deel[-8000:]
    return json.loads(uit.read_text(encoding="utf-8"))


@pytest.mark.slow
def test_apptest_melding_als_platte_tekst_zonder_excepties(w):
    from tests.unit.ui.test_def821_ontbrekende_grond_ui import INJECTIE, VRAAG

    assert w["gate_actief"] is True
    for naam, stap in w["stappen"].items():
        assert stap["exceptions"] == [], (naam, stap["exceptions"])
    stap = w["stappen"]["getoond"]
    assert INJECTIE in stap["text"]
    assert VRAAG in stap["text"]
    for veld in ("markdown", "warnings", "successes", "errors", "infos", "captions"):
        assert not any("onerror" in m for m in stap[veld]), (veld, stap[veld])
    assert any("betekenisgrond" in x for x in stap["warnings"])
    assert stap["successes"] == [] and stap["errors"] == []
    assert stap["text_areas"] == ["betekenisverduidelijking_invoer"]
    assert stap["buttons"] == ["btn_betekenisverduidelijking"]
    assert stap["verzonden"] == "null"


@pytest.mark.slow
def test_apptest_expliciet_verzenden_bindt_antwoord(w):
    verzonden = json.loads(w["stappen"]["verzonden"]["verzonden"])
    assert verzonden == {
        "generation_id": "gen-grond-1",
        "vingerafdruk": "vf-1",
        "tekst": ANTWOORD,
    }
    assert any("Genereer" in s for s in w["stappen"]["verzonden"]["successes"])


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--driver":
        _driver(sys.argv[2])
