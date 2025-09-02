"""
Test dat nieuwe services nu default zijn.
"""
import os
import sys
from pathlib import Path

# Voeg src toe aan path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Zorg dat we GEEN environment variable hebben
if 'USE_NEW_SERVICES' in os.environ:
    del os.environ['USE_NEW_SERVICES']

print("🧪 Testing nieuwe default services...\n")

# Import service factory
from services.service_factory import get_definition_service

# Get service zonder environment variable
service = get_definition_service()

print(f"Service type: {type(service).__name__}")
print(f"Is ServiceAdapter: {type(service).__name__ == 'ServiceAdapter'}")
print(f"Is UnifiedDefinitionService: {type(service).__name__ == 'UnifiedDefinitionService'}")

if type(service).__name__ == 'ServiceAdapter':
    print("\n✅ SUCCES: Nieuwe services zijn nu de default!")

    # Test basic functionality
    print("\nTesting basic operations...")
    stats = service.get_stats()
    print(f"Stats available: {bool(stats)}")
    print(f"Services: {list(stats.keys())}")
else:
    print("\n❌ FOUT: Legacy services zijn nog steeds default")

print("\nTest completed!")
