#!/usr/bin/env python3
"""
Story 2.4 Test Runner Script

Comprehensive test runner for Story 2.4 interface migration validation.
Runs all test suites in the correct order and provides detailed reporting.

Usage:
    python scripts/run_story_2_4_tests.py [--suite <suite>] [--verbose] [--performance]

Test Suites:
- unit: Unit tests for ValidationOrchestratorV2 components
- integration: Integration tests for full orchestrator flow
- regression: Regression tests for backward compatibility
- performance: Performance tests for overhead validation
- all: Run all test suites (default)
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


class Story24TestRunner:
    """Test runner for Story 2.4 validation."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.test_results: dict[str, Any] = {}

    def run_test_suite(
        self, suite_name: str, test_pattern: str, markers: list[str] = None
    ) -> bool:
        """Run a specific test suite and capture results."""
        print(f"\n{'='*60}")
        print(f"RUNNING {suite_name.upper()} TEST SUITE")
        print(f"{'='*60}")

        # Build pytest command
        cmd = ["python", "-m", "pytest"]

        # Add test pattern
        cmd.append(test_pattern)

        # Add markers if specified
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])

        # Add verbosity
        if self.verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")

        # Add additional flags
        cmd.extend(
            [
                "--tb=short",  # Short traceback format
                "--durations=10",  # Show 10 slowest tests
                "--strict-markers",  # Strict marker validation
                "--disable-warnings",  # Disable warnings for cleaner output
            ]
        )

        print(f"Command: {' '.join(cmd)}")
        print()

        # Run tests
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300, check=False
            )  # 5 min timeout
            execution_time = time.time() - start_time

            # Store results
            self.test_results[suite_name] = {
                "success": result.returncode == 0,
                "duration": execution_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
            }

            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr and self.verbose:
                print("STDERR:")
                print(result.stderr)

            # Print summary
            status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
            print(f"\n{suite_name.upper()} SUITE: {status} ({execution_time:.2f}s)")

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print(f"❌ {suite_name.upper()} SUITE: TIMEOUT (exceeded 5 minutes)")
            self.test_results[suite_name] = {
                "success": False,
                "duration": 300,
                "timeout": True,
            }
            return False
        except Exception as e:
            print(f"❌ {suite_name.upper()} SUITE: ERROR - {e}")
            self.test_results[suite_name] = {"success": False, "error": str(e)}
            return False

    def run_all_suites(self, include_performance: bool = False) -> bool:
        """Run all test suites for Story 2.4."""
        print("🚀 Starting Story 2.4 Test Suite Execution")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        overall_success = True

        # 1. Unit Tests
        success = self.run_test_suite(
            "unit", "tests/unit/test_story_2_4_unit.py", ["unit"]
        )
        overall_success = overall_success and success

        # 2. Integration Tests
        success = self.run_test_suite(
            "integration", "tests/integration/test_story_2_4_interface_migration.py"
        )
        overall_success = overall_success and success

        # 3. Regression Tests
        success = self.run_test_suite(
            "regression",
            "tests/regression/test_story_2_4_regression.py",
            ["regression"],
        )
        overall_success = overall_success and success

        # 4. Performance Tests (optional)
        if include_performance:
            success = self.run_test_suite(
                "performance",
                "tests/performance/test_story_2_4_performance.py",
                ["performance"],
            )
            overall_success = overall_success and success

        # 5. Golden Tests (business logic preservation)
        success = self.run_test_suite(
            "golden",
            "tests/integration/test_story_2_4_interface_migration.py",
            ["golden"],
        )
        overall_success = overall_success and success

        return overall_success

    def print_final_report(self):
        """Print final test execution report."""
        print(f"\n{'='*80}")
        print("STORY 2.4 TEST EXECUTION REPORT")
        print(f"{'='*80}")

        total_duration = sum(
            result.get("duration", 0) for result in self.test_results.values()
        )

        print(f"Total Execution Time: {total_duration:.2f} seconds")
        print()

        # Test suite results
        for suite_name, result in self.test_results.items():
            status_icon = "✅" if result.get("success", False) else "❌"
            duration = result.get("duration", 0)

            print(f"{status_icon} {suite_name.upper():<15} {duration:>8.2f}s")

            if not result.get("success", False):
                if result.get("timeout", False):
                    print("   └─ Timeout exceeded (5 minutes)")
                elif result.get("error"):
                    print(f"   └─ Error: {result['error']}")
                elif result.get("return_code"):
                    print(f"   └─ Exit code: {result['return_code']}")

        print()

        # Overall result
        all_passed = all(
            result.get("success", False) for result in self.test_results.values()
        )
        if all_passed:
            print("🎉 ALL STORY 2.4 TESTS PASSED!")
            print("✅ Interface migration validation successful")
        else:
            print("⚠️  SOME STORY 2.4 TESTS FAILED!")
            failed_suites = [
                name
                for name, result in self.test_results.items()
                if not result.get("success", False)
            ]
            print(f"❌ Failed suites: {', '.join(failed_suites)}")

        print(f"{'='*80}")

        return all_passed

    def run_single_suite(
        self, suite_name: str, include_performance: bool = False
    ) -> bool:
        """Run a single test suite."""
        suite_configs = {
            "unit": ("tests/unit/test_story_2_4_unit.py", ["unit"]),
            "integration": (
                "tests/integration/test_story_2_4_interface_migration.py",
                None,
            ),
            "regression": (
                "tests/regression/test_story_2_4_regression.py",
                ["regression"],
            ),
            "performance": (
                "tests/performance/test_story_2_4_performance.py",
                ["performance"],
            ),
            "golden": (
                "tests/integration/test_story_2_4_interface_migration.py",
                ["golden"],
            ),
        }

        if suite_name not in suite_configs:
            print(f"❌ Unknown test suite: {suite_name}")
            print(f"Available suites: {', '.join(suite_configs.keys())}")
            return False

        test_pattern, markers = suite_configs[suite_name]
        return self.run_test_suite(suite_name, test_pattern, markers)


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Story 2.4 Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_story_2_4_tests.py                    # Run all tests (except performance)
  python scripts/run_story_2_4_tests.py --performance      # Run all tests including performance
  python scripts/run_story_2_4_tests.py --suite unit       # Run only unit tests
  python scripts/run_story_2_4_tests.py --suite regression --verbose  # Run regression tests with verbose output
        """,
    )

    parser.add_argument(
        "--suite",
        choices=["unit", "integration", "regression", "performance", "golden", "all"],
        default="all",
        help="Test suite to run (default: all)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--performance",
        "-p",
        action="store_true",
        help="Include performance tests (slow)",
    )

    args = parser.parse_args()

    # Validate test environment
    test_files = [
        "tests/unit/test_story_2_4_unit.py",
        "tests/integration/test_story_2_4_interface_migration.py",
        "tests/regression/test_story_2_4_regression.py",
        "tests/performance/test_story_2_4_performance.py",
    ]

    missing_files = [f for f in test_files if not Path(f).exists()]
    if missing_files:
        print("❌ Missing test files:")
        for f in missing_files:
            print(f"   - {f}")
        print("\nPlease ensure all Story 2.4 test files are present.")
        return 1

    # Initialize test runner
    runner = Story24TestRunner(verbose=args.verbose)

    # Run tests
    if args.suite == "all":
        success = runner.run_all_suites(include_performance=args.performance)
    else:
        success = runner.run_single_suite(
            args.suite, include_performance=args.performance
        )

    # Print final report
    runner.print_final_report()

    # Return appropriate exit code
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
