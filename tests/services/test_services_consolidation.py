#!/usr/bin/env python3
"""
Test script voor services consolidatie.
Test of de unified service correct werkt en backward compatibility behouden blijft.
"""

import sys
import os
import asyncio
from typing import Dict, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_unified_service():
    """Test de nieuwe unified service."""
    print("🧪 Testing UnifiedDefinitionService...")

    try:
        from services.unified_definition_service import (
            UnifiedDefinitionService,
            UnifiedServiceConfig,
            ProcessingMode,
            ArchitectureMode,
            get_definition_service
        )

        # Test data
        begrip = "identiteitsbehandeling"
        context_dict = {
            "organisatorisch": ["Strafrechtketen"],
            "juridisch": ["Strafrecht"],
            "wettelijk": ["Wetboek van Strafrecht"]
        }

        # Test 1: Direct service creation
        print("\n1. Testing direct service creation...")
        service = UnifiedDefinitionService()
        print("✅ UnifiedDefinitionService created successfully")

        # Test 2: Factory function
        print("\n2. Testing factory function...")
        service2 = get_definition_service(mode=ProcessingMode.SYNC)
        print("✅ Factory function works")

        # Test 3: Configuration
        print("\n3. Testing configuration...")
        config = UnifiedServiceConfig(
            processing_mode=ProcessingMode.SYNC,
            architecture_mode=ArchitectureMode.LEGACY,
            enable_caching=True
        )
        service.configure(config)
        print("✅ Configuration works")

        # Test 4: Statistics
        print("\n4. Testing statistics...")
        stats = service.get_statistics()
        print(f"✅ Statistics: {stats}")

        print("\n✅ All UnifiedDefinitionService tests passed!")
        return True

    except Exception as e:
        print(f"❌ UnifiedDefinitionService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backward_compatibility():
    """Test backward compatibility wrappers."""
    print("\n🔄 Testing backward compatibility...")

    try:
        # Test legacy DefinitionService
        print("\n1. Testing legacy DefinitionService...")
        from services.definition_service import DefinitionService

        service = DefinitionService()
        print("✅ Legacy DefinitionService created successfully")

        # Test legacy AsyncDefinitionService
        print("\n2. Testing legacy AsyncDefinitionService...")
        from services.async_definition_service import AsyncDefinitionService

        async_service = AsyncDefinitionService()
        print("✅ Legacy AsyncDefinitionService created successfully")

        # Test legacy IntegratedService
        print("\n3. Testing legacy IntegratedService...")
        from services.integrated_service import IntegratedService

        integrated_service = IntegratedService()
        print("✅ Legacy IntegratedService created successfully")

        print("\n✅ All backward compatibility tests passed!")
        return True

    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Test alle imports werken nog."""
    print("\n📦 Testing imports...")

    try:
        # Test dat alle oude imports nog werken
        imports_to_test = [
            "from services.definition_service import DefinitionService",
            "from services.async_definition_service import AsyncDefinitionService",
            "from services.integrated_service import IntegratedService",
            "from services.unified_definition_service import UnifiedDefinitionService"
        ]

        for import_stmt in imports_to_test:
            try:
                exec(import_stmt)
                print(f"✅ {import_stmt}")
            except Exception as e:
                print(f"❌ {import_stmt}: {e}")
                return False

        print("\n✅ All imports work correctly!")
        return True

    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_file_structure():
    """Test dat alle service files bestaan."""
    print("\n📁 Testing file structure...")

    files_to_check = [
        "src/services/unified_definition_service.py",
        "src/services/definition_service.py",
        "src/services/async_definition_service.py",
        "src/services/integrated_service.py",
        "src/services/definition_service_backup.py",
        "src/services/integrated_service_backup.py",
        "SERVICES_CONSOLIDATION_LOG.md"
    ]

    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing!")
            all_exist = False

    if all_exist:
        print("\n✅ All required files exist!")
    else:
        print("\n❌ Some files are missing!")

    return all_exist

def test_consolidation_log():
    """Test dat consolidation log bestaat en valid is."""
    print("\n📄 Testing consolidation log...")

    try:
        with open("SERVICES_CONSOLIDATION_LOG.md", "r") as f:
            content = f.read()

        required_sections = [
            "Services Consolidation Log",
            "unified_definition_service.py",
            "UnifiedServiceConfig",
            "Backward Compatibility",
            "Migration Strategy"
        ]

        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)

        if missing_sections:
            print(f"❌ Missing sections: {missing_sections}")
            return False

        print("✅ Consolidation log is complete!")
        return True

    except Exception as e:
        print(f"❌ Consolidation log test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Services Consolidation Tests")
    print("=" * 50)

    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Unified Service", test_unified_service),
        ("Backward Compatibility", test_backward_compatibility),
        ("Consolidation Log", test_consolidation_log)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} ERROR: {e}")

    print(f"\n{'='*50}")
    print(f"🎯 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! Services consolidation is successful!")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
