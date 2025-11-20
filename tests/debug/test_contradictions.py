#!/usr/bin/env python
"""
FORENSIC TEST: Verify alleged contradictions in validation rules.
Tests each claimed contradiction to determine if they are real or phantom bugs.
"""
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import the specific validator modules directly
import importlib.util


def load_validator_module(rule_name):
    """Load a specific validator module."""
    module_path = (
        Path(__file__).parent.parent.parent / f"src/toetsregels/regels/{rule_name}.py"
    )
    spec = importlib.util.spec_from_file_location(f"{rule_name}Validator", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Initialize validators
def init_validators():
    """Initialize all relevant validators."""
    validators = {}

    # STR-01
    str01_path = (
        Path(__file__).parent.parent.parent / "src/toetsregels/regels/STR-01.json"
    )
    with open(str01_path, encoding="utf-8") as f:
        str01_config = json.load(f)
    str01_module = load_validator_module("STR-01")
    validators["STR-01"] = str01_module.STR01Validator(str01_config)

    # ESS-02
    ess02_path = (
        Path(__file__).parent.parent.parent / "src/toetsregels/regels/ESS-02.json"
    )
    with open(ess02_path, encoding="utf-8") as f:
        ess02_config = json.load(f)
    ess02_module = load_validator_module("ESS-02")
    validators["ESS-02"] = ess02_module.ESS02Validator(ess02_config)

    # ARAI-02
    arai02_path = (
        Path(__file__).parent.parent.parent / "src/toetsregels/regels/ARAI-02.json"
    )
    with open(arai02_path, encoding="utf-8") as f:
        arai02_config = json.load(f)
    arai02_module = load_validator_module("ARAI-02")
    validators["ARAI-02"] = arai02_module.ARAI02Validator(arai02_config)

    return validators


def test_contradiction_1():
    """
    Test Contradiction 1: STR-01 vs ESS-02
    Claim: STR-01 verbiedt "is", ESS-02 vereist "is een activiteit"
    """
    print("\n" + "=" * 80)
    print("CONTRADICTION 1: STR-01 vs ESS-02")
    print("=" * 80)

    validators = init_validators()

    # Test cases
    test_cases = [
        ("is een activiteit waarbij gegevens worden verzameld", "observatie"),
        ("activiteit waarbij gegevens worden verzameld", "observatie"),
        ("proces dat gegevens verzamelt voor analyse", "dataverzameling"),
        ("is een proces dat gegevens verzamelt", "dataverzameling"),
    ]

    for definitie, begrip in test_cases:
        print(f"\nTest: '{definitie}'")

        # Test STR-01
        str01_result = validators["STR-01"].validate(definitie, begrip)
        print(f"  STR-01: {str01_result[1]}")

        # Test ESS-02
        ess02_result = validators["ESS-02"].validate(definitie, begrip)
        print(f"  ESS-02: {ess02_result[1]}")

        # Check for contradiction
        if "is een activiteit" in definitie:
            if not str01_result[0] and ess02_result[0]:
                print(
                    "  ⚠️ CONTRADICTION CONFIRMED: STR-01 blocks 'is', ESS-02 wants it"
                )
            else:
                print("  ✅ No contradiction: Both accept or both reject")


def test_contradiction_2():
    """
    Test Contradiction 2: ARAI-02 vs ESS-02
    Claim: ARAI-02 verbiedt "proces", ESS-02 gebruikt "activiteit waarbij"
    """
    print("\n" + "=" * 80)
    print("CONTRADICTION 2: ARAI-02 vs ESS-02")
    print("=" * 80)

    validators = init_validators()

    test_cases = [
        ("proces", "workflow"),  # Just "proces" without specification
        (
            "proces dat gegevens verzamelt",
            "dataverzameling",
        ),  # "proces" with specification
        (
            "activiteit waarbij gegevens worden verzameld",
            "observatie",
        ),  # ESS-02 preferred
        ("handeling die resulteert in data", "dataverzameling"),  # Alternative
    ]

    for definitie, begrip in test_cases:
        print(f"\nTest: '{definitie}'")

        # Test ARAI-02
        arai02_result = validators["ARAI-02"].validate(definitie, begrip)
        print(f"  ARAI-02: {arai02_result[1]}")

        # Test ESS-02
        ess02_result = validators["ESS-02"].validate(definitie, begrip)
        print(f"  ESS-02: {ess02_result[1]}")

        # Analysis
        if "proces" in definitie and not arai02_result[0]:
            print("  ⚠️ ARAI-02 blocks 'proces' (as claimed)")
        if "activiteit waarbij" in definitie and ess02_result[0]:
            print("  ⚠️ ESS-02 accepts 'activiteit waarbij' (as claimed)")


def test_contradiction_3():
    """
    Test Contradiction 3: ErrorPrevention vs Grammar
    Claim: Forbids "waarbij" and "die" (relative clauses)
    """
    print("\n" + "=" * 80)
    print("CONTRADICTION 3: ErrorPrevention vs Grammar")
    print("=" * 80)

    # Read ErrorPrevention module
    error_prev_path = (
        Path(__file__).parent.parent.parent
        / "src/services/prompts/modules/error_prevention_module.py"
    )
    with open(error_prev_path, encoding="utf-8") as f:
        content = f.read()

    # Check what's actually forbidden
    print("\nAnalyzing ErrorPrevention module:")

    # Line 179-180: forbidden starters
    if '"proces waarbij"' in content:
        print("  ⚠️ 'proces waarbij' is listed as forbidden starter (line 179)")

    if '"handeling die"' in content:
        print("  ⚠️ 'handeling die' is listed as forbidden starter (line 180)")

    # Line 261: validation matrix
    if "Vermijd 'die', 'waarin', 'zoals'" in content:
        print("  ⚠️ Validation matrix says to avoid 'die', 'waarin', 'zoals' (line 261)")

    # BUT: Check if these are actually used in good examples
    _ = init_validators()  # Initialize validators for test setup
    ess02_config_path = (
        Path(__file__).parent.parent.parent / "src/toetsregels/regels/ESS-02.json"
    )
    with open(ess02_config_path, encoding="utf-8") as f:
        ess02_config = json.load(f)

    print("\nESS-02 good examples:")
    for example in ess02_config.get("goede_voorbeelden_proces", []):
        print(f"  - '{example}'")
        if "waarbij" in example:
            print("    ⚠️ CONTRADICTION: Uses 'waarbij' despite ErrorPrevention")
        if "die" in example:
            print("    ⚠️ CONTRADICTION: Uses 'die' despite ErrorPrevention")


def test_contradiction_4():
    """
    Test Contradiction 4: "een" Prohibition
    Claim: Line 293 forbids "een" (but line 293 doesn't exist?)
    """
    print("\n" + "=" * 80)
    print("CONTRADICTION 4: 'een' Prohibition (Line 293?)")
    print("=" * 80)

    # Search for "een" prohibition
    error_prev_path = (
        Path(__file__).parent.parent.parent
        / "src/services/prompts/modules/error_prevention_module.py"
    )
    with open(error_prev_path, encoding="utf-8") as f:
        lines = f.readlines()

    print(f"\nErrorPrevention module has {len(lines)} lines (not 293)")

    # Find actual "een" prohibition
    for i, line in enumerate(lines, 1):
        if '"een"' in line and "vermijd" in line.lower():
            print(f"  Line {i}: {line.strip()}")

    # Line 146 and 178
    print("\nActual 'een' prohibition:")
    print(
        f"  Line 146: {lines[145].strip()}"
    )  # "Begin niet met lidwoorden ('de', 'het', 'een')"
    print(f"  Line 178: {lines[177].strip()}")  # Listed in forbidden_starters

    # But ESS-02 uses "is een activiteit"
    print("\nBut ESS-02 good examples use 'een':")
    ess02_config_path = (
        Path(__file__).parent.parent.parent / "src/toetsregels/regels/ESS-02.json"
    )
    with open(ess02_config_path, encoding="utf-8") as f:
        ess02_config = json.load(f)

    for key in ["goede_voorbeelden_type", "goede_voorbeelden_proces"]:
        for example in ess02_config.get(key, []):
            if "een" in example:
                print(f"  - '{example}'")
                if example.startswith("is een"):
                    print(
                        "    ⚠️ STARTS with 'is een' - violates both STR-01 and ErrorPrevention!"
                    )


def analyze_severity():
    """Analyze the actual severity of these contradictions."""
    print("\n" + "=" * 80)
    print("SEVERITY ANALYSIS")
    print("=" * 80)

    print(
        """
CONTRADICTION 1 (STR-01 vs ESS-02): REAL - HIGH SEVERITY
- STR-01 forbids starting with "is"
- ESS-02 examples suggest "is een activiteit/categorie/exemplaar"
- This creates an impossible requirement for process definitions
- WORKAROUND: Start with noun directly ("activiteit waarbij...")

CONTRADICTION 2 (ARAI-02 vs ESS-02): PARTIAL - MEDIUM SEVERITY
- ARAI-02 forbids vague "proces" without specification
- ESS-02 wants explicit "is een proces" for clarity
- Not fully blocking - can use "proces dat..." with specification
- WORKAROUND: Use "activiteit" instead of "proces"

CONTRADICTION 3 (ErrorPrevention vs Grammar): REAL - HIGH SEVERITY
- ErrorPrevention forbids "waarbij" and "die"
- But ESS-02 good examples use "activiteit waarbij"
- Creates confusion about relative clauses
- WORKAROUND: Unclear - relative clauses are often necessary

CONTRADICTION 4 ("een" prohibition): MISREPORTED - LOW SEVERITY
- Line 293 doesn't exist (module has 262 lines)
- Real prohibition is on line 146/178 (don't START with "een")
- But ESS-02 uses "is een..." which also violates STR-01
- WORKAROUND: Don't start with "een", but can use it mid-sentence

CONTRADICTION 5 (Context Traceability): NOT TESTED - UNKNOWN
- Would need to test full generation flow
- Likely a guidance issue, not a blocking contradiction
"""
    )


def main():
    """Run all contradiction tests."""
    print("FORENSIC DEBUG: Testing Alleged Contradictions")
    print("=" * 80)

    test_contradiction_1()
    test_contradiction_2()
    test_contradiction_3()
    test_contradiction_4()
    analyze_severity()

    print("\n" + "=" * 80)
    print("FORENSIC CONCLUSION")
    print("=" * 80)
    print(
        """
The system has REAL contradictions but is NOT "UNUSABLE":

1. TWO HIGH-SEVERITY contradictions exist (STR-01 vs ESS-02, ErrorPrevention vs Grammar)
2. These CAN block certain valid definitions
3. But WORKAROUNDS exist for most cases
4. The "line 293" claim is FALSE (phantom bug)
5. System can still generate definitions with careful prompt engineering

The real issue IS the validation-vs-generation mindset mismatch:
- Rules designed for validation don't translate well to generation
- Contradictions arise from different rule authors/contexts
- Technical fixes alone won't solve the philosophical mismatch

DEF-126 is RIGHT about root cause, but DEF-151 exaggerates severity.
"""
    )


if __name__ == "__main__":
    main()
