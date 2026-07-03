"""Regressietests DEF-500: sleutel-mismatch begrip_input vs begrip.

Het invoerveld schrijft naar widget-key ``begrip_input``, maar de
categorie-preview (en 4 andere lezers) lezen key ``begrip``. Zonder
synchronisatie draait de ontologische classificatie nooit en blokkeert
definitie-generatie permanent (catch-22).

Deze tests bewijzen de echte wiring: alleen de widget-waarde is gezet
(zoals in de echte app) — géén voorgevulde ``begrip``-key zoals in
test_classification_single_path.py, waardoor de bug daar onzichtbaar was.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domain.ontological_categories import OntologischeCategorie
from ui.renderers.global_context_renderer import GlobalContextRenderer

pytestmark = [pytest.mark.unit]


class FakeSessionStateManager:
    """Dict-backed vervanger voor SessionStateManager (echte read/write-semantiek)."""

    def __init__(self) -> None:
        self.store: dict = {}

    def get_value(self, key, default=None):
        return self.store.get(key, default)

    def set_value(self, key, value):
        self.store[key] = value

    def initialize_session_state(self, defaults):
        for key, value in defaults.items():
            self.store.setdefault(key, value)


def _make_streamlit_mock() -> MagicMock:
    """Streamlit-mock die unpacking en falsy selectbox correct simuleert."""
    st = MagicMock()
    st.columns.return_value = (MagicMock(), MagicMock())
    st.selectbox.return_value = ""  # geen handmatige override
    return st


@pytest.fixture
def renderer() -> GlobalContextRenderer:
    return GlobalContextRenderer(context_selector=MagicMock())


class TestBegripKeySync:
    """render_begrip_input moet de widget-waarde naar key 'begrip' spiegelen."""

    def test_render_begrip_input_mirrors_value_to_begrip_key(self, renderer):
        fake_sm = FakeSessionStateManager()
        fake_st = _make_streamlit_mock()
        fake_st.text_input.return_value = "authenticatie"

        with (
            patch("ui.renderers.global_context_renderer._default_st", fake_st),
            patch("ui.renderers.global_context_renderer._DefaultSM", fake_sm),
        ):
            returned = renderer.render_begrip_input()

        assert returned == "authenticatie"
        assert fake_sm.get_value("begrip") == "authenticatie", (
            "Widget-waarde is niet gespiegeld naar session-key 'begrip' — "
            "categorie-preview en generatie blijven geblokkeerd (DEF-500)"
        )

    def test_clearing_input_clears_begrip_key(self, renderer):
        """Leegmaken van het veld moet ook de gespiegelde key legen."""
        fake_sm = FakeSessionStateManager()
        fake_sm.set_value("begrip", "oude-term")
        fake_st = _make_streamlit_mock()
        fake_st.text_input.return_value = ""

        with (
            patch("ui.renderers.global_context_renderer._default_st", fake_st),
            patch("ui.renderers.global_context_renderer._DefaultSM", fake_sm),
        ):
            renderer.render_begrip_input()

        assert fake_sm.get_value("begrip") == ""


class TestCatch22Regression:
    """End-to-end op renderer-niveau: invoer → preview → classificatie."""

    def test_preview_classifies_after_input_with_context(self, renderer):
        """Na render_begrip_input (alleen widget gezet) moet de preview classificeren."""
        fake_sm = FakeSessionStateManager()
        fake_sm.set_value(
            "global_context",
            {
                "organisatorische_context": ["Justitie"],
                "juridische_context": ["Strafrecht"],
                "wettelijke_basis": [],
            },
        )
        fake_st = _make_streamlit_mock()
        fake_st.text_input.return_value = "authenticatie"

        classify = AsyncMock(
            return_value=(
                OntologischeCategorie.PROCES,
                "Gedetecteerd als proces",
                {"proces": 2, "type": 0, "resultaat": 0, "exemplaar": 0},
            )
        )

        with (
            patch("ui.renderers.global_context_renderer._default_st", fake_st),
            patch("ui.renderers.global_context_renderer._DefaultSM", fake_sm),
        ):
            renderer.render_begrip_input()

        renderer.render_category_preview(
            _st=fake_st,
            _sm=fake_sm,
            _asyncio_run=asyncio.run,
            _determine_fn=classify,
        )

        classify.assert_called_once_with("authenticatie", "Justitie", "Strafrecht")
        assert fake_sm.get_value("determined_category") == (
            OntologischeCategorie.PROCES.value
        ), "Catch-22 DEF-500: classificatie draaide niet na term + context"

    def test_preview_skips_classification_without_input(self, renderer):
        """Zonder ingevoerde term mag de classifier niet draaien."""
        fake_sm = FakeSessionStateManager()
        fake_sm.set_value(
            "global_context",
            {"organisatorische_context": ["Justitie"], "juridische_context": []},
        )
        fake_st = _make_streamlit_mock()
        classify = AsyncMock()

        renderer.render_category_preview(
            _st=fake_st,
            _sm=fake_sm,
            _asyncio_run=asyncio.run,
            _determine_fn=classify,
        )

        classify.assert_not_called()
        assert fake_sm.get_value("determined_category") is None
