"""Regressietest voor cross-sessie context-isolatie (DEF-484).

De context werd voorheen in de proces-globale ``ContextManager``-singleton
bewaard (``_context``), waardoor Streamlit-sessies elkaars organisatorische/
juridische/wettelijke context zagen. De fix bewaart context per-sessie via
``SessionStateManager`` (= ``st.session_state``, per Streamlit-sessie geïsoleerd).

Deze test simuleert twee sessies door de backing-dict van ``st.session_state``
te wisselen en bewijst dat context van sessie A niet lekt naar sessie B.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.unit]


def test_context_is_session_scoped_not_process_global(mock_streamlit_session):
    """Context van sessie A lekt niet naar een verse sessie B."""
    from ui.helpers.context_adapter import ContextAdapter

    state = mock_streamlit_session.session_state
    adapter = ContextAdapter()

    # Sessie A zet context.
    assert adapter.set_in_session_state(
        {
            "organisatorische_context": ["GEHEIM_ORG_VAN_A"],
            "juridische_context": ["Strafrecht-A"],
            "wettelijke_basis": ["Art. 1 Sr"],
        }
    )
    merged_a = adapter.get_merged_context()
    assert merged_a["organisatorische_context"] == ["GEHEIM_ORG_VAN_A"]
    assert merged_a["juridische_context"] == ["Strafrecht-A"]

    # Sessie B = verse session_state (Streamlit geeft elke sessie een eigen dict).
    state.clear()
    merged_b = adapter.get_merged_context()
    assert merged_b.get("organisatorische_context", []) == []
    assert merged_b.get("juridische_context", []) == []
    assert merged_b.get("wettelijke_basis", []) == []


def test_set_context_validates_and_persists_per_session(mock_streamlit_session):
    """set_in_session_state valideert (via ContextManager) en bewaart in session_state."""
    from ui.helpers.context_adapter import _CONTEXT_STATE_KEY, ContextAdapter

    state = mock_streamlit_session.session_state
    adapter = ContextAdapter()

    # None-waarden en lege strings worden door de validatie genormaliseerd/gefilterd.
    ok = adapter.set_in_session_state(
        {"organisatorische_context": ["Org", "", None], "juridische_context": []}
    )
    assert ok
    stored = state[_CONTEXT_STATE_KEY]
    assert stored["organisatorische_context"] == ["Org"]
    assert stored["juridische_context"] == []
    assert stored["wettelijke_basis"] == []


def test_get_merged_context_falls_back_to_loose_fields(mock_streamlit_session):
    """Zonder opgeslagen context-key valt de adapter terug op losse velden."""
    from ui.helpers.context_adapter import ContextAdapter

    state = mock_streamlit_session.session_state
    state["organisatorische_context"] = ["LosVeld"]

    adapter = ContextAdapter()
    merged = adapter.get_merged_context()
    assert merged["organisatorische_context"] == ["LosVeld"]
