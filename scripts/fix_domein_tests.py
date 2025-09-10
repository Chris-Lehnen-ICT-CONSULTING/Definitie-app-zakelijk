#!/usr/bin/env python
"""Fix all test files that use domein parameter (removed per US-043)."""

import re
import os
from pathlib import Path

def fix_domein_in_file(filepath):
    """Remove or comment out domein= parameters in test file."""

    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # Pattern 1: domein="..." as parameter in function calls
    # Replace with comment showing it was removed
    content = re.sub(
        r',?\s*domein\s*=\s*["\'][^"\']*["\']',
        '',  # Remove completely
        content
    )

    # Pattern 2: domein=variable as parameter
    content = re.sub(
        r',?\s*domein\s*=\s*[a-zA-Z_][a-zA-Z0-9_]*(?!["\'])',
        '',  # Remove completely
        content
    )

    # Pattern 3: In Definition() constructor specifically
    content = re.sub(
        r'(\s+)(domein\s*=\s*["\'][^"\']*["\'],?\s*\n)',
        r'\1# \2',  # Comment out the line
        content
    )

    # Pattern 4: In dataclass/dict definitions
    content = re.sub(
        r'(["\']domein["\']\s*:\s*["\'][^"\']*["\'])',
        r'# \1  # removed per US-043',
        content
    )

    # Clean up any double commas that might result
    content = re.sub(r',\s*,', ',', content)

    # Clean up any trailing commas before closing parentheses
    content = re.sub(r',\s*\)', ')', content)

    # If changes were made, write back
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix all test files."""

    test_files = [
        "tests/functionality/test_deep_functionality.py",
        "tests/functionality/test_final_functionality.py",
        "tests/integration/test_business_logic_parity.py",
        "tests/integration/test_new_services_functionality.py",
        "tests/manual_test_prompt_debug.py",
        "tests/regression/test_story_2_4_regression.py",
        "tests/regression/test_v2_orchestrator.py",
        "tests/services/orchestrators/test_definition_orchestrator_v2.py",
        "tests/services/test_step2_components.py",
        "tests/test_container.py",
        "tests/test_modular_prompt_builder.py",
        "tests/test_ontological_category_fix.py",
        "tests/test_ontology_integration.py",
        "tests/test_per007_acceptance.py",
    ]

    fixed_count = 0
    for filepath in test_files:
        if os.path.exists(filepath):
            if fix_domein_in_file(filepath):
                print(f"✅ Fixed: {filepath}")
                fixed_count += 1
            else:
                print(f"⏭️  No changes needed: {filepath}")
        else:
            print(f"❌ Not found: {filepath}")

    print(f"\n{'='*60}")
    print(f"Fixed {fixed_count} files")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
