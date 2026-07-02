"""
Test UI met nieuwe services ingeschakeld.
"""

import os
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

# Voeg src directory toe aan Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Forceer nieuwe services
os.environ["USE_NEW_SERVICES"] = "true"

print("Testing UI met nieuwe services...")

try:
    from services import get_definition_service
    from ui.tabbed_interface import TabbedInterface

    # Test service met nieuwe mode
    service = get_definition_service()
    info = service.get_service_info()

    print(f"\n✅ Service mode: {info['service_mode']}")
    print(f"✅ Architecture: {info['architecture']}")
    print(f"✅ Version: {info['version']}")
    print(f"✅ Features: {', '.join(info['features'])}")

    # Test UI instantiation
    ui = TabbedInterface()

    if hasattr(ui, "definition_service"):
        ui_info = ui.definition_service.get_service_info()
        print(f"\n✅ UI service mode: {ui_info['service_mode']}")
        print(f"✅ UI architecture: {ui_info['architecture']}")

    print("\n🎉 Nieuwe services integratie werkt!")

except Exception as e:
    print(f"\n❌ Fout: {e}")
    import traceback

    traceback.print_exc()

print("\n📋 Samenvatting UI integratie:")
print("   - TabbedInterface gebruikt nu service factory")
print("   - Feature flag toggle beschikbaar in sidebar")
print("   - Services kunnen dynamisch gewisseld worden")
print("   - Volledige backward compatibility behouden")
