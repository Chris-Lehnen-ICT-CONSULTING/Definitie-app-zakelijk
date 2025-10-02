#!/usr/bin/env python
"""Fix all test files that use GenerationRequest without id parameter."""
import os
import re


def fix_generation_request_in_file(filepath):
    """Add id parameter to GenerationRequest instantiations."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    # Pattern to match GenerationRequest without id
    # This matches GenerationRequest( followed by begrip= but not id=
    pattern = r"GenerationRequest\(\s*\n?\s*begrip="

    if re.search(pattern, content):
        # Add id as first parameter
        content = re.sub(
            pattern,
            r'GenerationRequest(\n        id="test-id",\n        begrip=',
            content,
        )

        # Also handle single-line cases
        pattern2 = r"GenerationRequest\(begrip="
        content = re.sub(pattern2, r'GenerationRequest(id="test-id", begrip=', content)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main():
    test_files = [
        "tests/services/test_step2_components.py",
        "tests/test_per007_acceptance.py",
        "tests/test_ontology_integration.py",
        "tests/test_ontological_category_fix.py",
        "tests/test_container.py",
        "tests/services/orchestrators/test_definition_orchestrator_v2.py",
        "tests/regression/test_v2_orchestrator.py",
        "tests/regression/test_story_2_4_regression.py",
        "tests/manual_test_prompt_debug.py",
        "tests/integration/test_new_services_functionality.py",
        "tests/integration/test_business_logic_parity.py",
        "tests/functionality/test_final_functionality.py",
        "tests/functionality/test_deep_functionality.py",
    ]

    for file in test_files:
        if os.path.exists(file):
            if fix_generation_request_in_file(file):
                print(f"✅ Fixed: {file}")
            else:
                print(f"⏭️  Skipped: {file} (no changes needed)")
        else:
            print(f"❌ Not found: {file}")


if __name__ == "__main__":
    main()
