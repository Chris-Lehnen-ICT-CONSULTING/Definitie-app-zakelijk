"""
Shared pytest fixtures for UI tests.

This module provides reusable fixtures for testing Streamlit UI components,
particularly the SessionStateManager which requires mocking of st.session_state.
"""

import sys
from typing import NamedTuple
from unittest.mock import MagicMock, patch

import pytest


class MockStreamlitSession(NamedTuple):
    """Container for mock Streamlit session components.

    Attributes:
        manager: The SessionStateManager class (not instance - it uses class methods)
        session_state: The underlying dict that mocks st.session_state
        mock_st: The mock streamlit module (for advanced test scenarios)
    """

    manager: type  # SessionStateManager class
    session_state: dict
    mock_st: MagicMock


@pytest.fixture
def mock_streamlit_session():
    """Provide a mock Streamlit environment for SessionStateManager testing.

    This fixture creates a complete mock of the streamlit module with a dict-backed
    session_state, then imports SessionStateManager within that patched context.

    Yields:
        MockStreamlitSession: A named tuple containing:
            - manager: The SessionStateManager class
            - session_state: The mock dict backing st.session_state
            - mock_st: The mock streamlit module

    Example:
        def test_example(mock_streamlit_session):
            manager = mock_streamlit_session.manager
            state = mock_streamlit_session.session_state

            # Pre-populate state
            state["my_key"] = "value"

            # Use manager methods
            result = manager.get_value("my_key")
            assert result == "value"

    Note:
        Uses function scope because SessionStateManager imports streamlit at module
        level, requiring a fresh import per test to ensure isolation. Session scope
        would cause state leakage between tests.
    """
    mock_session_state: dict = {}

    mock_st = MagicMock()
    mock_st.session_state = mock_session_state

    # Remove cached session_state module to force fresh import with mock.
    # Without this, Streamlit imports from other tests pollute the module cache,
    # causing SessionStateManager to reference the real st.session_state.
    saved_module = sys.modules.pop("ui.session_state", None)

    try:
        with patch.dict("sys.modules", {"streamlit": mock_st}):
            from ui.session_state import SessionStateManager

            yield MockStreamlitSession(
                manager=SessionStateManager,
                session_state=mock_session_state,
                mock_st=mock_st,
            )
    finally:
        if saved_module is not None:
            sys.modules["ui.session_state"] = saved_module


@pytest.fixture
def mock_streamlit_cleanup():
    """Provide mock for force_cleanup_voorbeelden function testing.

    Similar to mock_streamlit_session but yields the cleanup function instead.

    Yields:
        tuple: (force_cleanup_voorbeelden function, mock_session_state dict)
    """
    mock_session_state: dict = {}

    mock_st = MagicMock()
    mock_st.session_state = mock_session_state

    saved_module = sys.modules.pop("ui.session_state", None)

    try:
        with patch.dict("sys.modules", {"streamlit": mock_st}):
            from ui.session_state import force_cleanup_voorbeelden

            yield force_cleanup_voorbeelden, mock_session_state
    finally:
        if saved_module is not None:
            sys.modules["ui.session_state"] = saved_module
