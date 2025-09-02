"""
Basis test voor nieuwe services.
"""
import os
import sys
from pathlib import Path

# Voeg src toe aan path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing basic service functionality...")

# Test 1: Import interfaces
try:
    from services.interfaces import (
        Definition, GenerationRequest, ValidationResult,
        DefinitionStatus, ValidationSeverity
    )
    print("✅ Interfaces import OK")
except Exception as e:
    print(f"❌ Interfaces import failed: {e}")

# Test 2: Create data objects
try:
    definition = Definition(
        begrip="test",
        definitie="Test definitie",
        context="Test context"
    )
    print("✅ Definition object created")

    request = GenerationRequest(
        begrip="test",
        context="Test context"
    )
    print("✅ GenerationRequest object created")
except Exception as e:
    print(f"❌ Data object creation failed: {e}")

# Test 3: Import services
try:
    from services.definition_generator import DefinitionGenerator
    from services.definition_validator import DefinitionValidator
    from services.definition_repository import DefinitionRepository
    from services.definition_orchestrator import DefinitionOrchestrator
    print("✅ All services imported")
except Exception as e:
    print(f"❌ Service import failed: {e}")

# Test 4: Container
try:
    from services.container import ServiceContainer
    container = ServiceContainer({'db_path': ':memory:'})
    print("✅ ServiceContainer created")

    # Get services
    generator = container.generator()
    print("✅ Generator service retrieved")

    validator = container.validator()
    print("✅ Validator service retrieved")

except Exception as e:
    print(f"❌ Container test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Basic validation
try:
    validator = DefinitionValidator()
    result = validator.validate(definition)
    print(f"✅ Validation completed: score={result.score:.2f}")
except Exception as e:
    print(f"❌ Validation failed: {e}")

print("\n🎉 Basic service tests completed!")
