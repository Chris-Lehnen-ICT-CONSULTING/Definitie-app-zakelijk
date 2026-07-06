"""Regressietests voor twee cosmetische UI-nits (GAT smoke-test 2026-07-02).

DEF-497: het statusbadge rendert een dubbele backslash (``\\\\n``) als
letterlijke tekst "\\n" in plaats van een regeleinde.
DEF-498: de kop "🎯 Context Configuratie" wordt dubbel gerenderd —
GlobalContextRenderer print hem én de EnhancedContextManagerSelector
print hem nogmaals in render(). De selector is de enige eigenaar.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytestmark = [pytest.mark.unit]

KOP = "Context Configuratie"


class TestStatusbadgeDef497:
    def _render_met(self, repository: MagicMock) -> MagicMock:
        from ui.tabbed_interface import TabbedInterface

        st = MagicMock()
        interface = MagicMock(spec=TabbedInterface)
        interface.repository = repository
        with patch("ui.tabbed_interface.st", st):
            TabbedInterface._render_status_indicator(interface)
        return st

    def test_statusbadge_bevat_echt_regeleinde(self):
        repository = MagicMock()
        repository.get_statistics.return_value = {"total_definities": 179}

        st = self._render_met(repository)

        boodschap = str(st.success.call_args.args[0])
        assert (
            "\\n" not in boodschap
        ), f"Letterlijke backslash-n in statusbadge: {boodschap!r}"
        assert "\n" in boodschap, f"Geen regeleinde in statusbadge: {boodschap!r}"
        assert "179 definities beschikbaar" in boodschap

    def test_statusbadge_foutpad_bevat_geen_letterlijke_backslash_n(self):
        repository = MagicMock()
        repository.get_statistics.side_effect = RuntimeError("db weg")

        st = self._render_met(repository)

        boodschap = str(st.error.call_args.args[0])
        assert "\\n" not in boodschap, f"Letterlijke backslash-n: {boodschap!r}"
        assert "\n" in boodschap, f"Geen regeleinde op foutpad: {boodschap!r}"


class TestDubbeleKopDef498:
    def test_global_renderer_print_de_kop_niet_zelf(self):
        """De selector is eigenaar van de kop; de renderer delegeert alleen."""
        from ui.renderers.global_context_renderer import GlobalContextRenderer

        st = MagicMock()
        selector = MagicMock()
        selector.render.return_value = {
            "organisatorische_context": [],
            "juridische_context": [],
            "wettelijke_basis": [],
        }
        renderer = GlobalContextRenderer(selector)

        with (
            patch("ui.renderers.global_context_renderer._default_st", st),
            patch("ui.renderers.global_context_renderer._DefaultSM", MagicMock()),
        ):
            renderer.render_context_selector()

        selector.render.assert_called_once()
        koppen = [
            str(c.args[0])
            for c in st.markdown.call_args_list
            if c.args and KOP in str(c.args[0])
        ]
        assert not koppen, (
            f"GlobalContextRenderer print de kop zelf ({koppen}) — de selector "
            "rendert hem al → dubbele kop op de hoofdpagina (DEF-498)"
        )

    def test_kop_heeft_precies_een_eigenaar_in_de_broncode(self):
        """Bronscan-invariant: de kop staat alleen in de selector-module."""
        src = Path(__file__).resolve().parents[3] / "src"
        renderer_bron = (src / "ui/renderers/global_context_renderer.py").read_text()
        selector_bron = (
            src / "ui/components/enhanced_context_manager_selector.py"
        ).read_text()

        assert (
            KOP not in renderer_bron
        ), "Kop teruggekeerd in global_context_renderer.py — dubbele rendering"
        assert selector_bron.count(KOP) == 1
