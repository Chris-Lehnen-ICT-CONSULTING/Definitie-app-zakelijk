"""
Shared pytest fixtures for UI tests.

This module provides reusable fixtures for testing Streamlit UI components,
particularly the SessionStateManager which requires mocking of st.session_state.
"""

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

    with patch.dict("sys.modules", {"streamlit": mock_st}):
        # Import fresh within the patched context
        from ui.session_state import SessionStateManager

        yield MockStreamlitSession(
            manager=SessionStateManager,
            session_state=mock_session_state,
            mock_st=mock_st,
        )


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

    with patch.dict("sys.modules", {"streamlit": mock_st}):
        from ui.session_state import force_cleanup_voorbeelden

        yield force_cleanup_voorbeelden, mock_session_state
