"""DEF-620: de RAG-collectieselector overleeft een verwijderde collectie."""

from __future__ import annotations

import pytest

from tests.unit.ui.test_def751_verduidelijking_keten import (
    FakeSM,
    _collectie,
    _render_rag_selector,
)

pytestmark = [pytest.mark.unit]


def test_bewaarde_selectie_met_verwijderde_collectie(monkeypatch):
    from unittest.mock import MagicMock, patch

    from ui import tabbed_interface

    sm = FakeSM()
    sm.data["rag_selected_collection_ids"] = [9, 10]  # 9 is inmiddels verwijderd
    st = MagicMock()
    st.expander.return_value.__enter__ = lambda *a: None
    st.expander.return_value.__exit__ = lambda *a: None
    st.multiselect.return_value = [10]
    import types

    tab = types.SimpleNamespace(
        _load_rag_collections=lambda: [_collectie(10), _collectie(11)]
    )
    with (
        patch.object(tabbed_interface, "st", st),
        patch.object(tabbed_interface, "SessionStateManager", sm),
    ):
        tabbed_interface.TabbedInterface._render_rag_collection_selector(tab)
    assert st.multiselect.call_args.kwargs["default"] == [10]


def test_alleen_verwijderde_collecties_valt_terug_op_alle(monkeypatch):
    from unittest.mock import MagicMock, patch

    from ui import tabbed_interface

    sm = FakeSM()
    sm.data["rag_selected_collection_ids"] = [9]
    st = MagicMock()
    st.expander.return_value.__enter__ = lambda *a: None
    st.expander.return_value.__exit__ = lambda *a: None
    st.multiselect.return_value = [10, 11]
    import types

    tab = types.SimpleNamespace(
        _load_rag_collections=lambda: [_collectie(10), _collectie(11)]
    )
    with (
        patch.object(tabbed_interface, "st", st),
        patch.object(tabbed_interface, "SessionStateManager", sm),
    ):
        tabbed_interface.TabbedInterface._render_rag_collection_selector(tab)
    assert st.multiselect.call_args.kwargs["default"] == [10, 11]
    assert _render_rag_selector  # helper uit DEF-751 blijft bruikbaar
