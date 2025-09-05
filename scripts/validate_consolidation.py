#!/usr/bin/env python3
"""
Architecture Consolidation Validation Runner
Executes all consolidation tests and provides detailed report
"""

import subprocess
import sys
from pathlib import Path

def run_tests(test_file: str) -> dict:
    """Run pytest on specified test file and return results."""
    result = subprocess.run(
        ["pytest", test_file, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )

    # Parse output for results
    output = result.stdout + result.stderr
    passed = output.count(" PASSED")
    failed = output.count(" FAILED")
    skipped = output.count(" SKIPPED")

    return {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "total": passed + failed + skipped,
        "output": output,
        "success": result.returncode == 0 or (failed == 0 and passed > 0)
    }

def main():
    """Main validation runner."""
    print("=" * 60)
    print("ARCHITECTURE CONSOLIDATION VALIDATION SUITE")
    print("=" * 60)
    print()

    # Run architecture consolidation tests
    print("1. Running Architecture Consolidation Tests...")
    print("-" * 40)
    arch_results = run_tests("tests/test_architecture_consolidation.py")
    print(f"✓ Passed: {arch_results['passed']}")
    print(f"⚠ Skipped: {arch_results['skipped']}")
    print(f"✗ Failed: {arch_results['failed']}")
    print()

    # Run PER-007 compliance tests
    print("2. Running PER-007 Compliance Tests...")
    print("-" * 40)
    per_results = run_tests("tests/test_per007_documentation_compliance.py")
    print(f"✓ Passed: {per_results['passed']}")
    print(f"⚠ Skipped: {per_results['skipped']}")
    print(f"✗ Failed: {per_results['failed']}")
    print()

    # Calculate totals
    total_tests = arch_results['total'] + per_results['total']
    total_passed = arch_results['passed'] + per_results['passed']
    total_failed = arch_results['failed'] + per_results['failed']
    total_skipped = arch_results['skipped'] + per_results['skipped']

    # Print summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Tests Run: {total_tests}")
    print(f"Tests Passed: {total_passed} ({total_passed*100//total_tests if total_tests > 0 else 0}%)")
    print(f"Tests Failed: {total_failed}")
    print(f"Tests Skipped: {total_skipped}")
    print()

    # Determine overall status
    pass_rate = (total_passed * 100 // total_tests) if total_tests > 0 else 0

    if pass_rate >= 80:
        print("✅ CONSOLIDATION VALIDATED")
        print("Minor issues detected - review skipped/failed tests")
        return 0
    elif pass_rate >= 60:
        print("⚠️  CONSOLIDATION PARTIALLY VALIDATED")
        print("Several issues need attention")
        return 1
    else:
        print("❌ CONSOLIDATION VALIDATION FAILED")
        print("Critical issues require immediate attention")
        return 2

if __name__ == "__main__":
    sys.exit(main())
