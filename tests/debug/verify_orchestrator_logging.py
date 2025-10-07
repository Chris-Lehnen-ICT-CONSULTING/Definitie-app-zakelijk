"""
Verify that PromptOrchestrator singleton produces correct logging behavior.

Expected log output:
- ONE "🎯 Creating singleton PromptOrchestrator" message
- ONE "✅ PromptOrchestrator cached: 16 modules registered" message
- Multiple "Adapter using cached orchestrator with 16 modules" messages
"""

import logging
import sys
from io import StringIO
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Capture logs
log_capture = StringIO()
handler = logging.StreamHandler(log_capture)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# Setup logging
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

from services.prompts.modular_prompt_adapter import ModularPromptAdapter

print("\n" + "=" * 80)
print("VERIFICATION: PromptOrchestrator Logging Behavior")
print("=" * 80 + "\n")

print("Creating 3 ModularPromptAdapter instances...\n")

# Create multiple adapters
adapter1 = ModularPromptAdapter()
adapter2 = ModularPromptAdapter()
adapter3 = ModularPromptAdapter()

# Get captured logs
log_output = log_capture.getvalue()

print("=" * 80)
print("CAPTURED LOGS:")
print("=" * 80)
print(log_output)

print("=" * 80)
print("LOG ANALYSIS:")
print("=" * 80)

# Count key log messages
singleton_create_count = log_output.count("🎯 Creating singleton PromptOrchestrator")
cached_msg_count = log_output.count(
    "✅ PromptOrchestrator cached: 16 modules registered"
)
adapter_using_count = log_output.count(
    "Adapter using cached orchestrator with 16 modules"
)
adapter_init_count = log_output.count(
    "ModularPromptAdapter geïnitialiseerd - gebruikt nieuwe modulaire architectuur"
)

print("\n📝 Log Message Counts:")
print(f"   '🎯 Creating singleton':     {singleton_create_count} (expected: 1)")
print(f"   '✅ PromptOrchestrator cached': {cached_msg_count} (expected: 1)")
print(
    f"   'Adapter using cached':      {adapter_using_count} (expected: 3, got debug logs)"
)
print(f"   'ModularPromptAdapter init': {adapter_init_count} (expected: 3)")

print("\n🎯 Verification Results:")

results = []

if singleton_create_count == 1:
    print("   ✅ Singleton created exactly once")
    results.append(True)
else:
    print(f"   ❌ Singleton created {singleton_create_count} times (expected 1)")
    results.append(False)

if cached_msg_count == 1:
    print("   ✅ Cache message logged exactly once")
    results.append(True)
else:
    print(f"   ❌ Cache message logged {cached_msg_count} times (expected 1)")
    results.append(False)

if adapter_init_count == 3:
    print("   ✅ All 3 adapters initialized")
    results.append(True)
else:
    print(f"   ❌ Only {adapter_init_count} adapters initialized (expected 3)")
    results.append(False)

# Check for old misleading log
old_log_count = log_output.count("PromptOrchestrator: 0 modules, 4 workers")
if old_log_count == 0:
    print("   ✅ No misleading '0 modules' log found")
    results.append(True)
else:
    print(f"   ❌ Found {old_log_count} misleading '0 modules' logs (should be 0)")
    results.append(False)

print("\n" + "=" * 80)

if all(results):
    print("🎉 SUCCESS: All logging behavior is correct!")
    sys.exit(0)
else:
    print("❌ FAILURE: Some logging issues detected")
    sys.exit(1)
