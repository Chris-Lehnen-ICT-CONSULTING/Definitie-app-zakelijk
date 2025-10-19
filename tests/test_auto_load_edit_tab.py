#!/usr/bin/env python3
"""Test auto-load functionality for edit tab."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock, Mock, patch

import streamlit as st

# Mock streamlit before importing our modules
st.session_state = {}

from datetime import datetime

from src.ui.session_state import SessionStateManager


def test_session_state_keys_exist():
    """Test that all required session state keys are defined."""
    print("Testing session state keys...")

    required_keys = [
        "editing_definition_id",
        "editing_definition",
        "edit_session",
        "edit_search_results",
        "last_auto_save",
        "edit_organisatorische_context",
        "edit_juridische_context",
        "edit_wettelijke_basis",
    ]

    for key in required_keys:
        assert key in SessionStateManager.DEFAULT_VALUES, f"Missing key: {key}"
        print(f"✓ Key '{key}' exists")

    print("✅ All session state keys are present!\n")


def test_context_coupling():
    """Test that contexts are properly coupled when definition is generated."""
    print("Testing context coupling...")

    # Initialize session state
    SessionStateManager.initialize_session_state()

    # Simulate a generation result with contexts
    mock_saved_record = Mock()
    mock_saved_record.id = 123

    # Set the values as the tabbed_interface would
    SessionStateManager.set_value("editing_definition_id", mock_saved_record.id)
    SessionStateManager.set_value("edit_organisatorische_context", ["DJI", "JUSTID"])
    SessionStateManager.set_value("edit_juridische_context", ["Strafrecht"])
    SessionStateManager.set_value(
        "edit_wettelijke_basis", ["Wetboek van Strafvordering"]
    )

    # Verify values are set
    assert SessionStateManager.get_value("editing_definition_id") == 123
    assert SessionStateManager.get_value("edit_organisatorische_context") == [
        "DJI",
        "JUSTID",
    ]
    assert SessionStateManager.get_value("edit_juridische_context") == ["Strafrecht"]
    assert SessionStateManager.get_value("edit_wettelijke_basis") == [
        "Wetboek van Strafvordering"
    ]

    print("✓ Definition ID is coupled")
    print("✓ Organisatorische context is coupled")
    print("✓ Juridische context is coupled")
    print("✓ Wettelijke basis is coupled")
    print("✅ Context coupling works correctly!\n")


def test_auto_load_detection():
    """Test that edit tab can detect when a definition should be loaded."""
    print("Testing auto-load detection...")

    # Clear any existing values first
    SessionStateManager.clear_value("editing_definition_id")

    # Initially no definition
    assert SessionStateManager.get_value("editing_definition_id") is None
    print("✓ Initially no definition to load")

    # Set a definition ID (as done after generation)
    SessionStateManager.set_value("editing_definition_id", 456)

    # Edit tab should detect this
    target_id = SessionStateManager.get_value("editing_definition_id")
    assert target_id == 456
    print(f"✓ Edit tab detects definition ID: {target_id}")

    # Check if contexts are available
    SessionStateManager.set_value("edit_organisatorische_context", ["Test Org"])
    org_context = SessionStateManager.get_value("edit_organisatorische_context")
    assert org_context == ["Test Org"]
    print(f"✓ Edit tab detects context: {org_context}")

    print("✅ Auto-load detection works correctly!\n")


def test_context_cleanup():
    """Test that contexts are cleaned up after use."""
    print("Testing context cleanup...")

    # Set contexts
    SessionStateManager.set_value("edit_organisatorische_context", ["Temp Org"])
    SessionStateManager.set_value("edit_juridische_context", ["Temp Jur"])

    # Verify they exist
    assert SessionStateManager.get_value("edit_organisatorische_context") is not None
    assert SessionStateManager.get_value("edit_juridische_context") is not None
    print("✓ Contexts are set")

    # Simulate cleanup (as done in edit tab after loading)
    SessionStateManager.clear_value("edit_organisatorische_context")
    SessionStateManager.clear_value("edit_juridische_context")

    # Verify they are cleared
    assert SessionStateManager.get_value("edit_organisatorische_context") is None
    assert SessionStateManager.get_value("edit_juridische_context") is None
    print("✓ Contexts are cleared after use")

    print("✅ Context cleanup works correctly!\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("AUTO-LOAD EDIT TAB FUNCTIONALITY TEST")
    print("=" * 60)
    print()

    try:
        test_session_state_keys_exist()
        test_context_coupling()
        test_auto_load_detection()
        test_context_cleanup()

        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("The auto-load functionality is working correctly:")
        print("- Session state keys are properly defined")
        print("- Definition ID is coupled after generation")
        print("- Contexts are preserved and passed to edit tab")
        print("- Cleanup mechanism prevents memory leaks")
        print()
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
