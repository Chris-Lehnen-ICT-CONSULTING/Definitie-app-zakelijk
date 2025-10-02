#!/usr/bin/env python3
"""Identify missing test scenarios and edge cases."""

from collections import defaultdict
from pathlib import Path


def analyze_test_scenarios():
    """Analyze missing test scenarios."""

    print("=" * 80)
    print("MISSING TEST SCENARIOS AND EDGE CASES ANALYSIS")
    print("=" * 80)

    # Analyze key service modules for test coverage
    critical_modules = {
        "src/services/ai_service_v2.py": {
            "scenarios": [
                "rate limiting behavior",
                "API key validation",
                "timeout handling",
                "retry logic",
                "error responses",
                "temperature variations",
                "max token limits",
                "empty/null inputs",
                "concurrent requests",
            ]
        },
        "src/services/definition_repository.py": {
            "scenarios": [
                "database connection failures",
                "concurrent writes",
                "transaction rollback",
                "SQL injection prevention",
                "UTF-8 character handling",
                "large dataset pagination",
                "duplicate key handling",
                "null/empty field handling",
                "cascade deletes",
            ]
        },
        "src/services/validation/modular_validation_service.py": {
            "scenarios": [
                "all 45 validation rules",
                "rule priority ordering",
                "partial validation",
                "validation caching",
                "error accumulation",
                "performance with large inputs",
                "rule dependency chains",
                "custom rule injection",
                "validation state persistence",
            ]
        },
        "src/services/orchestrators/validation_orchestrator_v2.py": {
            "scenarios": [
                "orchestration flow interruption",
                "service failure handling",
                "partial results aggregation",
                "async operation handling",
                "timeout management",
                "retry strategies",
                "circuit breaker patterns",
                "state machine transitions",
                "rollback scenarios",
            ]
        },
        "src/services/export_service.py": {
            "scenarios": [
                "file system full",
                "permission denied",
                "concurrent exports",
                "large dataset exports",
                "format conversion errors",
                "character encoding issues",
                "template rendering failures",
                "partial export recovery",
                "export cancellation",
            ]
        },
    }

    # Check what's actually tested
    print("\n1. CRITICAL MODULE TEST COVERAGE GAPS")
    print("-" * 50)

    for module_path, expected in critical_modules.items():
        print(f"\n📁 {module_path}")

        # Find test files for this module
        module_name = Path(module_path).stem
        test_pattern = f"test_{module_name}"
        tested_scenarios = set()

        for test_file in Path("tests").rglob(f"*{test_pattern}*.py"):
            if "__pycache__" in str(test_file):
                continue
            try:
                with open(test_file) as f:
                    content = f.read()

                    # Look for scenario keywords in test names and comments
                    for scenario in expected["scenarios"]:
                        keywords = scenario.split()
                        if any(
                            keyword.lower() in content.lower() for keyword in keywords
                        ):
                            tested_scenarios.add(scenario)
            except:
                pass

        missing = set(expected["scenarios"]) - tested_scenarios
        coverage_pct = (
            (len(tested_scenarios) / len(expected["scenarios"])) * 100
            if expected["scenarios"]
            else 0
        )

        print(
            f"  Coverage: {len(tested_scenarios)}/{len(expected['scenarios'])} scenarios ({coverage_pct:.0f}%)"
        )

        if missing:
            print("  ❌ MISSING SCENARIOS:")
            for scenario in sorted(missing):
                print(f"    - {scenario}")
        else:
            print("  ✅ All expected scenarios covered")

    # Analyze edge cases
    print("\n\n2. EDGE CASE COVERAGE ANALYSIS")
    print("-" * 50)

    edge_cases = {
        "Input Validation": [
            "empty strings",
            "None values",
            "extremely long inputs (>10000 chars)",
            "special characters (emoji, RTL text)",
            "SQL injection attempts",
            "XSS payloads",
            "binary data",
            "malformed JSON",
            "circular references",
        ],
        "Boundary Conditions": [
            "zero values",
            "negative numbers",
            "maximum integer values",
            "floating point precision",
            "date/time edge cases",
            "array/list boundaries",
            "pagination limits",
            "rate limit boundaries",
        ],
        "Error Handling": [
            "network timeouts",
            "connection refused",
            "permission denied",
            "disk full",
            "memory exhaustion",
            "stack overflow",
            "deadlocks",
            "race conditions",
        ],
        "Concurrency": [
            "parallel writes",
            "read-write conflicts",
            "cache invalidation",
            "session conflicts",
            "resource locking",
            "async cancellation",
            "event ordering",
        ],
    }

    # Search for edge case testing
    edge_case_coverage = defaultdict(set)

    for test_file in Path("tests").rglob("test_*.py"):
        if "__pycache__" in str(test_file):
            continue
        try:
            with open(test_file) as f:
                content = f.read()

                for category, cases in edge_cases.items():
                    for case in cases:
                        # Look for keywords indicating this edge case is tested
                        keywords = case.replace("(", "").replace(")", "").split()
                        if any(
                            keyword.lower() in content.lower() for keyword in keywords
                        ):
                            edge_case_coverage[category].add(case)
        except:
            pass

    print("\n📊 EDGE CASE TEST COVERAGE:")
    for category, cases in edge_cases.items():
        tested = edge_case_coverage.get(category, set())
        coverage_pct = (len(tested) / len(cases)) * 100 if cases else 0
        status = "🟢" if coverage_pct > 60 else "🟡" if coverage_pct > 30 else "🔴"

        print(
            f"\n{status} {category}: {len(tested)}/{len(cases)} cases tested ({coverage_pct:.0f}%)"
        )

        missing = set(cases) - tested
        if missing and coverage_pct < 50:
            print("  Missing:")
            for case in sorted(missing)[:5]:
                print(f"    - {case}")

    # Check for state transition testing
    print("\n\n3. STATE TRANSITION TESTING")
    print("-" * 50)

    state_files = [
        "src/services/orchestrators/validation_orchestrator_v2.py",
        "src/services/workflow_service.py",
        "src/services/category_state_manager.py",
    ]

    for file_path in state_files:
        if Path(file_path).exists():
            module_name = Path(file_path).stem
            has_state_tests = False

            for test_file in Path("tests").rglob(f"*{module_name}*.py"):
                try:
                    with open(test_file) as f:
                        content = f.read()
                        if any(
                            x in content
                            for x in ["state", "transition", "workflow", "status"]
                        ):
                            has_state_tests = True
                            break
                except:
                    pass

            status = "✅" if has_state_tests else "❌"
            print(
                f"  {status} {file_path}: {'Has state tests' if has_state_tests else 'NO STATE TESTS'}"
            )

    # Integration test coverage
    print("\n\n4. INTEGRATION TEST COVERAGE")
    print("-" * 50)

    integration_scenarios = [
        "End-to-end definition generation",
        "Full validation pipeline",
        "Export with all formats",
        "Import and validation",
        "Web lookup integration",
        "Database transaction flows",
        "Multi-service orchestration",
        "Error propagation across services",
        "Performance under load",
    ]

    found_integration_tests = set()
    for test_file in Path("tests/integration").rglob("test_*.py"):
        try:
            with open(test_file) as f:
                content = f.read()
                for scenario in integration_scenarios:
                    if any(
                        word.lower() in content.lower() for word in scenario.split()[:2]
                    ):
                        found_integration_tests.add(scenario)
        except:
            pass

    print(
        f"\n📊 Integration Scenarios: {len(found_integration_tests)}/{len(integration_scenarios)} covered"
    )
    missing_integration = set(integration_scenarios) - found_integration_tests
    if missing_integration:
        print("\n❌ Missing Integration Tests:")
        for scenario in missing_integration:
            print(f"  - {scenario}")

    # Summary and recommendations
    print("\n\n5. CRITICAL GAPS SUMMARY")
    print("-" * 50)

    print("\n🚨 HIGHEST PRIORITY MISSING TESTS:\n")
    print("1. AI Service V2:")
    print("   - Rate limiting and retry logic")
    print("   - Error response handling")
    print("   - Concurrent request management\n")

    print("2. Database Operations:")
    print("   - Transaction rollback scenarios")
    print("   - Concurrent write conflicts")
    print("   - Connection failure recovery\n")

    print("3. Validation Service:")
    print("   - Complete coverage of all 45 rules")
    print("   - Rule interaction and dependencies")
    print("   - Performance with large inputs\n")

    print("4. Edge Cases:")
    print("   - Input validation for special characters")
    print("   - Boundary condition testing")
    print("   - Error propagation paths\n")

    print("5. Integration:")
    print("   - End-to-end workflow testing")
    print("   - Multi-service failure scenarios")
    print("   - Performance under concurrent load")


if __name__ == "__main__":
    analyze_test_scenarios()
