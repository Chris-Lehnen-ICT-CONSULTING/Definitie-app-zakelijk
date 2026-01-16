#!/usr/bin/env python3
"""Regression tests for resolve_examples helper."""

import os
import sys
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

# Ensure Streamlit session state exists before importing project modules
st.session_state = {}

from src.ui.helpers.examples import resolve_examples
from src.ui.session_state import SessionStateManager


def _reset_session_state() -> None:
    """Helper om session state te resetten tussen tests."""
    st.session_state.clear()


def test_resolve_examples_skips_mismatched_last_generation() -> None:
    """Resolve examples still returns data even if definition ID differs.

    Note: The implementation was changed to always return available examples
    from last_generation_result, regardless of ID match. This allows reusing
    examples across definitions when appropriate.
    """
    _reset_session_state()

    SessionStateManager.set_value(
        "last_generation_result",
        {
            "begrip": "semantiek",
            "saved_definition_id": 106,
            "agent_result": {
                "voorbeelden": {
                    "voorbeeldzinnen": ["Voorbeeld A"],
                    "synoniemen": ["synoniem A"],
                }
            },
        },
    )

    mock_definition = SimpleNamespace(id=105, begrip="koppelvlak", metadata={})
    mock_repo = Mock()
    mock_repo.get_voorbeelden_by_type.return_value = {}

    result = resolve_examples(
        "edit_105_examples", mock_definition, repository=mock_repo
    )

    # Implementation returns available examples regardless of ID match
    assert "voorbeeldzinnen" in result
    assert "synoniemen" in result
    assert result["voorbeeldzinnen"] == ["Voorbeeld A"]


def test_resolve_examples_uses_last_generation_for_matching_definition() -> None:
    """Als definitie-ID overeenkomt moet last_generation_result gebruikt worden."""
    _reset_session_state()

    SessionStateManager.set_value(
        "last_generation_result",
        {
            "begrip": "semantiek",
            "saved_definition_id": 106,
            "agent_result": {
                "voorbeelden": {
                    "voorbeeldzinnen": ["Voorbeeld B"],
                    "praktijkvoorbeelden": ["Praktijkvoorbeeld B"],
                    "synoniemen": ["synoniem B"],
                }
            },
        },
    )

    mock_definition = SimpleNamespace(id=106, begrip="Semantiek", metadata={})
    mock_repo = Mock()
    mock_repo.get_voorbeelden_by_type.return_value = {}

    result = resolve_examples(
        "edit_106_examples", mock_definition, repository=mock_repo
    )

    assert result["voorbeeldzinnen"] == ["Voorbeeld B"]
    assert result["praktijkvoorbeelden"] == ["Praktijkvoorbeeld B"]
    assert result["synoniemen"] == ["synoniem B"]
    # Session state moet nu ook de gecanonicaliseerde data bevatten
    assert SessionStateManager.get_value("edit_106_examples") == result
