#!/usr/bin/env python3
"""
Test script voor metadata velden implementatie.
Verifieert dat datum_voorstel, voorgesteld_door en ketenpartners correct werken.
"""

import sys
sys.path.append('src')

from datetime import datetime
from ui.session_state import SessionStateManager
from export.export_txt import exporteer_naar_txt

def test_metadata_fields():
    print("🧪 Testing metadata fields implementation...")

    # Test 1: Session State Manager
    print("\n1️⃣ Testing SessionStateManager...")
    SessionStateManager.initialize_session_state()

    # Check default values
    assert SessionStateManager.get_value("datum_voorstel") is None
    assert SessionStateManager.get_value("voorgesteld_door") == ""
    assert SessionStateManager.get_value("ketenpartners") == []
    print("✅ Default values correct")

    # Set values
    test_date = datetime.today()
    SessionStateManager.set_value("datum_voorstel", test_date)
    SessionStateManager.set_value("voorgesteld_door", "Test User")
    SessionStateManager.set_value("ketenpartners", ["ZM", "DJI", "KMAR"])

    # Verify values
    assert SessionStateManager.get_value("datum_voorstel") == test_date
    assert SessionStateManager.get_value("voorgesteld_door") == "Test User"
    assert SessionStateManager.get_value("ketenpartners") == ["ZM", "DJI", "KMAR"]
    print("✅ Values correctly stored and retrieved")

    # Test 2: Export functionality
    print("\n2️⃣ Testing export functionality...")
    export_data = SessionStateManager.get_export_data()

    # Check metadata in export
    assert "metadata" in export_data
    assert export_data["metadata"]["datum_voorstel"] == test_date
    assert export_data["metadata"]["voorgesteld_door"] == "Test User"
    assert export_data["metadata"]["ketenpartners"] == ["ZM", "DJI", "KMAR"]
    print("✅ Metadata included in export data")

    # Test 3: TXT Export
    print("\n3️⃣ Testing TXT export...")
    test_data = {
        "begrip": "test_begrip",
        "definitie_gecorrigeerd": "Test definitie",
        "definitie_origineel": "Test definitie origineel",
        "metadata": {
            "marker": "type",
            "datum_voorstel": test_date,
            "voorgesteld_door": "Test User",
            "ketenpartners": ["ZM", "DJI", "KMAR"]
        },
        "context_dict": {},
        "toetsresultaten": [],
        "bronnen": []
    }

    try:
        export_path = exporteer_naar_txt(test_data)
        print(f"✅ Export successful: {export_path}")

        # Read and verify content
        with open(export_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "datum_voorstel:" in content
            assert "voorgesteld_door: Test User" in content
            assert "ketenpartners: ZM, DJI, KMAR" in content
        print("✅ Metadata correctly formatted in export")
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False

    # Test 4: Database fields
    print("\n4️⃣ Testing database record...")
    from database.definitie_repository import DefinitieRecord

    record = DefinitieRecord()
    record.datum_voorstel = test_date
    record.set_ketenpartners(["ZM", "DJI", "KMAR"])

    # Verify JSON handling
    partners_list = record.get_ketenpartners_list()
    assert partners_list == ["ZM", "DJI", "KMAR"]
    print("✅ Database record handles metadata correctly")

    print("\n✅ All tests passed! Metadata fields implementation successful.")
    return True

if __name__ == "__main__":
    success = test_metadata_fields()
    sys.exit(0 if success else 1)
