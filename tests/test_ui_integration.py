"""
Test UI integratie met nieuwe services.
"""
import os
import sys
from pathlib import Path

# Voeg src directory toe aan Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Test imports
print("Testing imports...")

try:
    from ui.tabbed_interface import TabbedInterface
    print("✅ TabbedInterface import OK")
except Exception as e:
    print(f"❌ TabbedInterface import fout: {e}")

try:
    from services import get_definition_service, render_feature_flag_toggle
    print("✅ Service factory imports OK")
except Exception as e:
    print(f"❌ Service factory import fout: {e}")

# Test service instantiation
print("\nTesting service instantiation...")

try:
    service = get_definition_service()
    print("✅ Definition service created")

    info = service.get_service_info()
    print(f"   Service mode: {info['service_mode']}")
    print(f"   Architecture: {info['architecture']}")
except Exception as e:
    print(f"❌ Service instantiation fout: {e}")
    import traceback
    traceback.print_exc()

# Test UI instantiation
print("\nTesting UI instantiation...")

try:
    ui = TabbedInterface()
    print("✅ TabbedInterface created")

    if hasattr(ui, 'definition_service'):
        print("✅ Definition service attached to UI")
    else:
        print("❌ Definition service not found in UI")
except Exception as e:
    print(f"❌ UI instantiation fout: {e}")
    import traceback
    traceback.print_exc()

print("\n🎉 UI integratie test compleet!")
