"""DEF-751 B2 — echte Streamlit-controls voor voorstel/override (AppTest).

Reproductie van reviewbevinding 4: de selectbox `manual_category_override`
behield haar waarde over reruns, waardoor de oude handmatige override na een
term- of contextwissel direct werd teruggezet. Zelfde opzet als
``test_def743_editor_apptest.py``: de pytest-conftest vervangt ``streamlit``
procesbreed door een mock, dus dit bestand start zichzelf als subprocess-
driver achter ``tests.offline_bootstrap`` en leest de waarnemingen terug.

Bewezen met échte widgets (classificatie via een geïnjecteerde fake, geen
model): kies `TYPE` bij *keurmerk* → termwissel naar *vergunning* → widget én
effectieve override zijn leeg; kies opnieuw `TYPE` → contextwissel DJI→OM →
opnieuw leeg; kies `TYPE` en zet "Aanpassen?" terug op leeg → override
ingetrokken, voorstel blijft.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.slow]

REPO = Path(__file__).resolve().parents[3]


def _app() -> None:
    import streamlit as st

    from domain.ontological_categories import OntologischeCategorie
    from ui.renderers.global_context_renderer import GlobalContextRenderer
    from ui.session_state import SessionStateManager

    async def _fake_classify(begrip: str, org: str, jur: str):
        return OntologischeCategorie.PROCES, f"fake voor {begrip}", {"proces": 0.9}

    # De context komt uit een niet-widget-sleutel die de driver zet.
    SessionStateManager.initialize_session_state(
        {"global_context": {"organisatorische_context": ["DJI"]}}
    )
    renderer = GlobalContextRenderer(context_selector=None)
    renderer.render_begrip_input()
    renderer.render_category_preview(_determine_fn=_fake_classify)
    st.caption(
        "effectieve_override="
        + str(SessionStateManager.get_value("manual_ontological_category"))
    )
    st.caption("voorstel=" + str(SessionStateManager.get_value("determined_category")))


def _waarneming(at) -> dict:
    captions = [str(c.value) for c in at.caption]
    widget = [s for s in at.selectbox if s.key == "manual_category_override"]
    return {
        "exceptions": [str(e.value) for e in at.exception],
        "widget": widget[0].value if widget else "<geen widget>",
        "captions": captions,
        "override": next(
            (
                c.split("=", 1)[1]
                for c in captions
                if c.startswith("effectieve_override=")
            ),
            "<geen caption>",
        ),
        "voorstel": next(
            (c.split("=", 1)[1] for c in captions if c.startswith("voorstel=")),
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

    w: dict = {"gate_actief": offline_bootstrap.gate_is_actief(), "stappen": {}}
    at = AppTest.from_function(_app, default_timeout=120)
    at.run()

    # Stap 1: term invoeren → voorstel (fake: proces), override kiezen: TYPE.
    at.text_input(key="begrip_input").input("keurmerk").run()
    at.selectbox(key="manual_category_override").select("TYPE").run()
    w["stappen"]["override_gekozen"] = _waarneming(at)

    # Stap 2: termwissel → voorstel én override (widget + effectief) leeg.
    at.text_input(key="begrip_input").input("vergunning").run()
    w["stappen"]["na_termwissel"] = _waarneming(at)

    # Stap 3: opnieuw TYPE kiezen, dan contextwissel DJI→OM.
    at.selectbox(key="manual_category_override").select("TYPE").run()
    w["stappen"]["opnieuw_gekozen"] = _waarneming(at)
    at.session_state["global_context"] = {"organisatorische_context": ["OM"]}
    at.run()
    w["stappen"]["na_contextwissel"] = _waarneming(at)

    # Stap 4: TYPE kiezen en "Aanpassen?" terug op leeg → override ingetrokken.
    at.selectbox(key="manual_category_override").select("TYPE").run()
    at.selectbox(key="manual_category_override").select("").run()
    w["stappen"]["terug_naar_voorstel"] = _waarneming(at)

    Path(uit_pad).write_text(
        json.dumps(w, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ------------------------------------------------------------------ pytest


@pytest.fixture(scope="module")
def w(tmp_path_factory) -> dict:
    uit = tmp_path_factory.mktemp("def751-categorie-apptest") / "waarnemingen.json"
    proces = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--driver", str(uit)],
        cwd=str(REPO),
        env=dict(os.environ),
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert proces.returncode == 0, proces.stderr[-8000:]
    return json.loads(uit.read_text(encoding="utf-8"))


def test_driver_draait_achter_de_gate_zonder_ui_excepties(w):
    assert w["gate_actief"] is True
    for naam, stap in w["stappen"].items():
        assert stap["exceptions"] == [], (naam, stap["exceptions"])


def test_override_wordt_gekozen_en_effectief(w):
    stap = w["stappen"]["override_gekozen"]
    assert stap["widget"] == "TYPE" and stap["override"] == "TYPE"
    assert stap["voorstel"] == "proces"


def test_termwissel_wist_widget_en_effectieve_override(w):
    stap = w["stappen"]["na_termwissel"]
    assert stap["widget"] == "", stap
    assert stap["override"] == "None", stap
    assert stap["voorstel"] == "proces"  # opnieuw geclassificeerd voor de nieuwe term


def test_contextwissel_wist_widget_en_effectieve_override(w):
    assert w["stappen"]["opnieuw_gekozen"]["override"] == "TYPE"
    stap = w["stappen"]["na_contextwissel"]
    assert stap["widget"] == "", stap
    assert stap["override"] == "None", stap


def test_terug_naar_voorstel_trekt_override_in(w):
    stap = w["stappen"]["terug_naar_voorstel"]
    assert stap["widget"] == "" and stap["override"] == "None"
    assert stap["voorstel"] == "proces"


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--driver":
        _driver(sys.argv[2])
