"""
Test script to verify PromptOrchestrator singleton caching behavior.

This script should show:
- Single "Creating singleton PromptOrchestrator" log
- Single "PromptOrchestrator cached: 16 modules registered" log
- Multiple adapters reusing same instance
"""

import logging
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Setup logging to see our changes
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

from services.prompts.modular_prompt_adapter import (ModularPromptAdapter,
                                                     get_cached_orchestrator)

print("\n" + "=" * 80)
print("TEST: PromptOrchestrator Singleton Caching")
print("=" * 80 + "\n")

print("1️⃣ First adapter creation (should create singleton):")
print("-" * 80)
adapter1 = ModularPromptAdapter()
orchestrator1 = adapter1._orchestrator
print(f"   Orchestrator ID: {id(orchestrator1)}")
print(f"   Modules: {len(orchestrator1.modules)}")

print("\n2️⃣ Second adapter creation (should reuse singleton):")
print("-" * 80)
adapter2 = ModularPromptAdapter()
orchestrator2 = adapter2._orchestrator
print(f"   Orchestrator ID: {id(orchestrator2)}")
print(f"   Modules: {len(orchestrator2.modules)}")

print("\n3️⃣ Direct cached orchestrator access:")
print("-" * 80)
orchestrator3 = get_cached_orchestrator()
print(f"   Orchestrator ID: {id(orchestrator3)}")
print(f"   Modules: {len(orchestrator3.modules)}")

print("\n" + "=" * 80)
print("VERIFICATION:")
print("=" * 80)

same_instance_12 = orchestrator1 is orchestrator2
same_instance_13 = orchestrator1 is orchestrator3
same_instance_23 = orchestrator2 is orchestrator3

print(f"✅ Adapter 1 & 2 share instance: {same_instance_12}")
print(f"✅ Adapter 1 & Direct share instance: {same_instance_13}")
print(f"✅ Adapter 2 & Direct share instance: {same_instance_23}")

if same_instance_12 and same_instance_13 and same_instance_23:
    print("\n🎉 SUCCESS: All instances are the same (singleton works!)")
else:
    print("\n❌ FAILURE: Instances are different (singleton not working)")
    sys.exit(1)

print("\n" + "=" * 80)
print("MODULE REGISTRATION:")
print("=" * 80)

modules = orchestrator1.get_registered_modules()
print(f"Total modules registered: {len(modules)}")
for module in modules:
    print(f"  - {module['module_id']}: {module['module_name']}")

print("\n✅ Test completed successfully!")
