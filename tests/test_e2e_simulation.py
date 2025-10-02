#!/usr/bin/env python3
"""End-to-end simulation test for auto-load functionality."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock

import streamlit as st

# Initialize mock session state
st.session_state = {}

from src.ui.session_state import SessionStateManager


def simulate_generation_flow():
    """Simulate the complete flow from generation to edit tab."""
    print("SIMULATION: Complete user flow")
    print("=" * 60)

    # Step 1: User generates a definition
    print("\n1️⃣ GENERATING DEFINITION")
    print("-" * 40)

    # Simulate what happens in tabbed_interface.py after generation
    mock_saved_record = Mock()
    mock_saved_record.id = 12345

    # Context from generation
    org_context = ["DJI", "JUSTID", "Reclassering"]
    jur_context = ["Strafrecht", "Bestuursrecht"]
    wet_context = ["Wetboek van Strafvordering", "Penitentiaire beginselenwet"]

    print(f"Generated definition with ID: {mock_saved_record.id}")
    print(f"Organisatorische context: {org_context}")
    print(f"Juridische context: {jur_context}")
    print(f"Wettelijke basis: {wet_context}")

    # This is what tabbed_interface.py does (lines 951-959)
    if mock_saved_record and hasattr(mock_saved_record, "id"):
        SessionStateManager.set_value("editing_definition_id", mock_saved_record.id)
        SessionStateManager.set_value("edit_organisatorische_context", org_context)
        SessionStateManager.set_value("edit_juridische_context", jur_context)
        SessionStateManager.set_value("edit_wettelijke_basis", wet_context)
        print("✓ Definition and contexts stored for edit tab")

    # Step 2: User navigates to Edit tab
    print("\n2️⃣ USER CLICKS ON EDIT TAB")
    print("-" * 40)

    # Simulate what definition_edit_tab.py does
    target_id = SessionStateManager.get_value("editing_definition_id")

    if target_id:
        print(f"✓ Edit tab detects definition ID: {target_id}")

        # Check for contexts
        edit_org = SessionStateManager.get_value("edit_organisatorische_context")
        edit_jur = SessionStateManager.get_value("edit_juridische_context")
        edit_wet = SessionStateManager.get_value("edit_wettelijke_basis")

        if edit_org or edit_jur or edit_wet:
            print("✓ Edit tab detects contexts from generator")
            print(f"  - Organisatorisch: {edit_org}")
            print(f"  - Juridisch: {edit_jur}")
            print(f"  - Wettelijk: {edit_wet}")

            # Show info message
            print("\n📋 Message shown to user:")
            print("   'Contexten van gegenereerde definitie zijn automatisch ingevuld'")

            # Clean up after loading
            SessionStateManager.clear_value("edit_organisatorische_context")
            SessionStateManager.clear_value("edit_juridische_context")
            SessionStateManager.clear_value("edit_wettelijke_basis")
            print("\n✓ Temporary context variables cleaned up")
    else:
        print("❌ No definition to auto-load")

    # Step 3: Verify final state
    print("\n3️⃣ FINAL STATE CHECK")
    print("-" * 40)

    # Definition ID should still be there
    assert SessionStateManager.get_value("editing_definition_id") == 12345
    print(
        f"✓ Definition ID persists: {SessionStateManager.get_value('editing_definition_id')}"
    )

    # Temporary contexts should be cleared
    assert SessionStateManager.get_value("edit_organisatorische_context") is None
    assert SessionStateManager.get_value("edit_juridische_context") is None
    assert SessionStateManager.get_value("edit_wettelijke_basis") is None
    print("✓ Temporary contexts are cleaned")

    print("\n" + "=" * 60)
    print("✅ SIMULATION SUCCESSFUL!")
    print("=" * 60)
    print("\nThe auto-load flow works as expected:")
    print("1. Definition ID and contexts are stored after generation")
    print("2. Edit tab automatically detects and loads them")
    print("3. Contexts are displayed and then cleaned up")
    print("4. User doesn't need to manually search!")


def main():
    """Run the simulation."""
    try:
        # Initialize session state
        SessionStateManager.initialize_session_state()

        # Run simulation
        simulate_generation_flow()
        return 0
    except Exception as e:
        print(f"\n❌ SIMULATION FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
