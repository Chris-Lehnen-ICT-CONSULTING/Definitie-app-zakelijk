"""
Quick UI smoke test voor beide modes.
"""

import os
import sys
from pathlib import Path

# Voeg src toe aan path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("🔍 UI Smoke Test\n")


def test_ui_mode(use_new_services):
    """Test UI in een specifieke mode."""
    os.environ["USE_NEW_SERVICES"] = str(use_new_services).lower()
    mode = "NEW" if use_new_services else "LEGACY"

    print(f"\n{'='*40}")
    print(f"Testing {mode} mode")
    print("=" * 40)

    try:
        # Import UI components
        from ui.tabbed_interface import TabbedInterface

        print("✅ TabbedInterface imported")

        # Check service factory
        from services.service_factory import get_definition_service

        service = get_definition_service()
        print(f"✅ Service created: {type(service).__name__}")

        # Test basic operations
        if hasattr(service, "generate_definition"):
            print("✅ Has generate_definition method")
        elif hasattr(service, "genereer_definitie"):
            print("✅ Has genereer_definitie method")
        else:
            print("❌ No generation method found")

        # Check UI initialization
        interface = TabbedInterface()
        print("✅ TabbedInterface created")

        # Check available tabs
        if hasattr(interface, "tabs"):
            print(f"✅ Tabs available: {len(interface.tabs)}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


# Test both modes
print("Testing UI in both modes...")

# Legacy mode
test_ui_mode(False)

# New services mode
test_ui_mode(True)

print("\n✅ UI smoke test completed!")
