"""DEF-751 stap 2 — de generatietab bij een gemeld betekenisconflict.

Met een gemockt `st` (conftest vervangt streamlit procesbreed): het conflict
wordt getoond als melding van het model (vraag + lezingen + gronden), met een
expliciet antwoordveld en een verzendknop; definitie-, categorie-, validatie-
en voorbeeldensecties worden niet gerenderd, er is geen succesmelding en
geen Toepassen. Een leeg antwoord is geen verduidelijking; verzenden bindt
het antwoord aan het open conflict (generation_id + vingerafdruk). Ook een
gewone mislukte generatie rendert geen resultaatsecties meer.

Het echte-widgetbewijs (AppTest, subprocess achter de offline-gate, zelfde
opzet als `test_def751_categorie_apptest.py`) staat onderaan.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

pytestmark = [pytest.mark.unit]

REPO = Path(__file__).resolve().parents[3]

VRAAG = "Is de handeling of het vastgelegde gegeven bedoeld?"
LEZINGEN = [
    {"lezing": "de handeling", "bron": "bron 1", "grond": "bron 1 zegt activiteit"},
    {
        "lezing": "het gegeven",
        "bron": "context: DJI",
        "grond": "DJI gebruikt resultaat",
    },
]


def conflict_resultaat(generation_id: str = "gen-1") -> dict[str, Any]:
    return {
        "begrip": "registratie",
        "agent_result": {
            "success": False,
            "error_message": VRAAG,
            "definitie_origineel": "",
            "definitie_gecorrigeerd": "",
            "final_score": 0.0,
            "validation_details": {},
            "voorbeelden": {},
            "metadata": {"generation_id": generation_id},
            "sources": [],
            "betekenisconflict": {
                "vraag": VRAAG,
                "lezingen": LEZINGEN,
                "gemeld_door": "model",
                "begrip": "registratie",
                "generation_id": generation_id,
            },
        },
        "saved_record": None,
        "saved_definition_id": None,
        "determined_category": "proces",
    }


def open_conflict(generation_id: str = "gen-1") -> dict[str, Any]:
    return {
        "generation_id": generation_id,
        "vingerafdruk": "vf-1",
        "vraag": VRAAG,
        "lezingen": LEZINGEN,
        "begrip": "registratie",
    }


class FakeSM:
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
        FakeSM.data = dict(sessie)
        st = MagicMock()
        st.button.return_value = knop
        tab = _tab()
        with (
            patch.object(module, "st", st),
            patch.object(module, "SessionStateManager", FakeSM),
            patch.object(tab, "_render_definition_section") as definitie,
            patch.object(tab, "_render_validation_section") as validatie,
            patch.object(tab, "_render_voorbeelden_section") as voorbeelden,
            patch.object(tab, "_cache_definition_id") as cache_id,
        ):
            tab._render_generation_results(resultaat)
        return st, {
            "definitie": definitie,
            "validatie": validatie,
            "voorbeelden": voorbeelden,
            "cache_id": cache_id,
            "categorie": tab.category_renderer,
        }

    return _render


def _tekst(mock: MagicMock) -> str:
    return " ".join(
        str(a)
        for naam in (
            "markdown",
            "warning",
            "info",
            "caption",
            "write",
            "success",
            "error",
        )
        for c in getattr(mock, naam).call_args_list
        for a in c.args
    )


def test_conflict_toont_vraag_lezingen_en_antwoordveld_zonder_resultaatsecties(render):
    from ui.helpers.betekenisconflict import KEY_INVOER, KEY_OPEN

    st, secties = render(conflict_resultaat(), {KEY_OPEN: open_conflict()})
    tekst = _tekst(st)
    assert VRAAG in tekst
    for lezing in LEZINGEN:
        assert (
            lezing["lezing"] in tekst
            and lezing["grond"] in tekst
            and lezing["bron"] in tekst
        )
    assert "melding van het model" in tekst
    assert "geen definitie" in tekst
    assert not st.success.called
    assert st.text_area.called
    assert st.text_area.call_args.kwargs["key"] == KEY_INVOER
    assert "value" not in st.text_area.call_args.kwargs  # key-only widget
    assert st.button.called
    for naam, sectie in secties.items():
        if naam == "categorie":
            assert not sectie.render_ontological_category_section.called
            assert not sectie.render_ufo_category_selector.called
        else:
            assert not sectie.called, naam


def test_leeg_antwoord_is_geen_verduidelijking(render):
    from ui.helpers.betekenisconflict import KEY_INVOER, KEY_OPEN, KEY_VERZONDEN

    st, _ = render(
        conflict_resultaat(), {KEY_OPEN: open_conflict(), KEY_INVOER: "   "}, knop=True
    )
    assert KEY_VERZONDEN not in FakeSM.data
    assert "leeg" in _tekst(st).lower()


def test_verzenden_bindt_antwoord_aan_open_conflict_en_vingerafdruk(render):
    from ui.helpers.betekenisconflict import KEY_INVOER, KEY_OPEN, KEY_VERZONDEN

    st, _ = render(
        conflict_resultaat(),
        {KEY_OPEN: open_conflict(), KEY_INVOER: " Bedoeld is de handeling "},
        knop=True,
    )
    verzonden = FakeSM.data[KEY_VERZONDEN]
    assert verzonden == {
        "generation_id": "gen-1",
        "vingerafdruk": "vf-1",
        "tekst": "Bedoeld is de handeling",
    }
    assert "Genereer" in _tekst(st)
    # Het widget-veld zelf wordt niet aangeraakt (Streamlit-veilig).
    assert FakeSM.data[KEY_INVOER] == " Bedoeld is de handeling "


def test_zonder_passend_open_conflict_geen_verzendknop(render):
    from ui.helpers.betekenisconflict import KEY_OPEN

    # Het getoonde conflict hoort bij gen-1; de sessie kent alleen gen-2 (of niets).
    for sessie in ({KEY_OPEN: open_conflict("gen-2")}, {}):
        st, _ = render(conflict_resultaat("gen-1"), sessie, knop=True)
        assert not st.button.called
        assert not st.text_area.called
        assert "opnieuw" in _tekst(st).lower()


def test_eerder_verzonden_antwoord_wordt_getoond(render):
    from ui.helpers.betekenisconflict import KEY_OPEN, KEY_VERZONDEN

    st, _ = render(
        conflict_resultaat(),
        {
            KEY_OPEN: open_conflict(),
            KEY_VERZONDEN: {
                "generation_id": "gen-1",
                "vingerafdruk": "vf-1",
                "tekst": "de handeling",
            },
        },
    )
    assert "de handeling" in _tekst(st)
    assert "Genereer" in _tekst(st)


def test_gewone_mislukking_rendert_geen_resultaatsecties(render):
    resultaat = conflict_resultaat()
    resultaat["agent_result"].pop("betekenisconflict")
    resultaat["agent_result"][
        "error_message"
    ] = "Generatie mislukt: modelantwoord ongeldig"
    st, secties = render(resultaat, {})
    assert st.warning.called and "ongeldig" in _tekst(st)
    assert not st.success.called
    assert not st.text_area.called
    for naam, sectie in secties.items():
        if naam == "categorie":
            assert not sectie.render_ontological_category_section.called
        else:
            assert not sectie.called, naam


# ------------------------------------------------------------ AppTest-bewijs


def _app() -> None:
    # AppTest voert deze functie geïsoleerd uit: alles expliciet importeren.
    import json
    from unittest.mock import MagicMock

    import streamlit as st

    from tests.unit.ui.test_def751_betekenisconflict_tab import (
        conflict_resultaat,
        open_conflict,
    )
    from ui.components.definition_generator_tab import DefinitionGeneratorTab
    from ui.helpers.betekenisconflict import KEY_OPEN, KEY_VERZONDEN
    from ui.session_state import SessionStateManager

    SessionStateManager.initialize_session_state(
        {"last_generation_result": conflict_resultaat(), KEY_OPEN: open_conflict()}
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
        "markdown": [str(m.value) for m in at.markdown],
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
        # Na elke stap wegschrijven: een crash halverwege laat de eerdere
        # waarnemingen (incl. UI-excepties) zichtbaar voor de pytest-kant.
        Path(uit_pad).write_text(
            json.dumps(w, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    at = AppTest.from_function(_app, default_timeout=120)
    at.run()
    w["stappen"]["getoond"] = _waarneming(at)
    _schrijf()

    # Leeg veld verzenden: geen verduidelijking.
    at.button(key="btn_betekenisverduidelijking").click().run()
    w["stappen"]["leeg_verzonden"] = _waarneming(at)
    _schrijf()

    # Antwoord invullen en expliciet verzenden.
    at.text_area(key=KEY_INVOER).input(
        "Bedoeld is de handeling van het vastleggen"
    ).run()
    w["stappen"]["ingevuld"] = _waarneming(at)
    _schrijf()
    at.button(key="btn_betekenisverduidelijking").click().run()
    w["stappen"]["verzonden"] = _waarneming(at)
    _schrijf()


@pytest.fixture(scope="module")
def w(tmp_path_factory) -> dict:
    uit = tmp_path_factory.mktemp("def751-conflict-apptest") / "waarnemingen.json"
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
def test_apptest_driver_zonder_excepties(w):
    assert w["gate_actief"] is True
    for naam, stap in w["stappen"].items():
        assert stap["exceptions"] == [], (naam, stap["exceptions"])


@pytest.mark.slow
def test_apptest_conflict_toont_vraag_veld_en_knop_zonder_succes(w):
    stap = w["stappen"]["getoond"]
    assert any(VRAAG in m for m in stap["markdown"])
    assert stap["text_areas"] == ["betekenisverduidelijking_invoer"]
    assert stap["buttons"] == ["btn_betekenisverduidelijking"]
    assert stap["successes"] == []
    assert stap["verzonden"] == "null"


@pytest.mark.slow
def test_apptest_leeg_verzenden_legt_niets_vast(w):
    stap = w["stappen"]["leeg_verzonden"]
    assert stap["verzonden"] == "null"
    assert any("leeg" in x.lower() for x in stap["warnings"])


@pytest.mark.slow
def test_apptest_expliciet_verzenden_bindt_antwoord(w):
    assert (
        w["stappen"]["ingevuld"]["verzonden"] == "null"
    ), "invullen alleen is geen verzenden"
    verzonden = json.loads(w["stappen"]["verzonden"]["verzonden"])
    assert verzonden == {
        "generation_id": "gen-1",
        "vingerafdruk": "vf-1",
        "tekst": "Bedoeld is de handeling van het vastleggen",
    }
    assert any("Genereer" in s for s in w["stappen"]["verzonden"]["successes"])


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--driver":
        _driver(sys.argv[2])
