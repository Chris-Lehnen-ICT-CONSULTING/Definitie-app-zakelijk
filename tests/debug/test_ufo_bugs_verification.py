#!/usr/bin/env python3
"""
UFO Classifier Bug Verification Script
=====================================
Direct testing of claimed bugs to determine if they are real or false positives.
"""

import gc
import os
import sys
import threading
import time
import traceback
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.ufo_classifier_service import (
    UFOCategory,
    UFOClassifierService,
    get_ufo_classifier,
)


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print("=" * 60)


def test_bug_1_empty_none_input():
    """BUG CLAIM 1: Empty string/None input crashes → silently returns UNKNOWN"""
    print_section("BUG 1: Empty/None Input Handling")

    classifier = UFOClassifierService()
    results = []

    test_cases = [
        ("", "valid definition", "empty term"),
        ("valid term", "", "empty definition"),
        ("", "", "both empty"),
        (None, "valid definition", "None term"),
        ("valid term", None, "None definition"),
        (None, None, "both None"),
        ("   ", "valid definition", "whitespace term"),
        ("valid term", "   ", "whitespace definition"),
    ]

    for term, definition, description in test_cases:
        try:
            print(f"\nTesting {description}:")
            print(f"  Input: term={term!r}, def={definition!r}")

            result = classifier.classify(term, definition)

            print(f"  Result: {result.primary_category.value}")
            print(f"  Confidence: {result.confidence}")
            print(f"  Explanation: {result.explanation}")

            # Check if it silently returns UNKNOWN
            if result.primary_category == UFOCategory.UNKNOWN:
                print("  ✓ Returns UNKNOWN (as claimed)")
            else:
                print(f"  ✗ Returns {result.primary_category.value} (not UNKNOWN)")

            results.append((description, "NO_CRASH", result.primary_category))

        except Exception as e:
            print(f"  ✗ EXCEPTION: {type(e).__name__}: {e}")
            results.append((description, "EXCEPTION", str(e)))

    # Summary
    print("\n" + "-" * 40)
    print("SUMMARY:")
    crashes = [r for r in results if r[1] == "EXCEPTION"]
    unknowns = [
        r for r in results if r[1] == "NO_CRASH" and r[2] == UFOCategory.UNKNOWN
    ]

    print(f"  Crashes: {len(crashes)}/{len(test_cases)}")
    print(f"  Silent UNKNOWN returns: {len(unknowns)}/{len(test_cases)}")

    if crashes:
        print("  BUG CLAIM: FALSE - Does crash (not silent)")
    elif unknowns == results:
        print("  BUG CLAIM: TRUE - Silently returns UNKNOWN")
    else:
        print("  BUG CLAIM: PARTIAL - Mixed behavior")

    return len(crashes) == 0 and len(unknowns) == len(test_cases)


def test_bug_2_config_loading():
    """BUG CLAIM 2: Config file nooit geladen ondanks parameter"""
    print_section("BUG 2: Config File Loading")

    # Test 1: Check if config_path is stored
    config_path = Path("/fake/config.yaml")
    classifier = UFOClassifierService(config_path=config_path)

    print(f"Config path provided: {config_path}")
    print(f"Classifier config_path attribute: {classifier.config_path}")

    if classifier.config_path == config_path:
        print("✓ Config path is stored")
    else:
        print("✗ Config path NOT stored")

    # Test 2: Check if config is actually used
    print("\nChecking for config usage in code...")

    # Check if config_path is ever read/used after __init__
    has_config_usage = False

    # Inspect the class methods
    import inspect

    source = inspect.getsource(UFOClassifierService)

    # Count references to config_path outside __init__
    lines = source.split("\n")
    config_refs = []
    in_init = False

    for i, line in enumerate(lines):
        if "def __init__" in line:
            in_init = True
        elif in_init and line.strip() and not line.startswith(" "):
            in_init = False

        if not in_init and "config_path" in line.lower():
            config_refs.append((i, line.strip()))

    if config_refs:
        print(f"Found {len(config_refs)} references to config_path outside __init__:")
        for line_no, line in config_refs[:3]:
            print(f"  Line {line_no}: {line[:60]}...")
        has_config_usage = True
    else:
        print("✗ No references to config_path found outside __init__")
        print("  Config is stored but NEVER USED!")
        has_config_usage = False

    print("\n" + "-" * 40)
    print("SUMMARY:")
    if not has_config_usage:
        print("  BUG CLAIM: TRUE - Config parameter accepted but never used")
        return True
    print("  BUG CLAIM: FALSE - Config is used")
    return False


def test_bug_3_singleton_race_condition():
    """BUG CLAIM 3: Race conditions in singleton pattern"""
    print_section("BUG 3: Singleton Thread Safety")

    instances = []
    errors = []

    def get_instance_thread(thread_id):
        try:
            instance = get_ufo_classifier()
            instances.append((thread_id, id(instance)))
        except Exception as e:
            errors.append((thread_id, str(e)))

    # Create many threads simultaneously
    threads = []
    num_threads = 50

    print(f"Creating {num_threads} threads to get singleton...")

    for i in range(num_threads):
        t = threading.Thread(target=get_instance_thread, args=(i,))
        threads.append(t)

    # Start all threads at once
    start_time = time.time()
    for t in threads:
        t.start()

    # Wait for completion
    for t in threads:
        t.join(timeout=5)

    elapsed = time.time() - start_time

    print(f"Completed in {elapsed:.3f} seconds")
    print(f"Instances created: {len(instances)}")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nErrors encountered:")
        for thread_id, error in errors[:5]:
            print(f"  Thread {thread_id}: {error}")

    # Check if all instances are the same
    unique_ids = {inst_id for _, inst_id in instances}
    print(f"Unique instance IDs: {len(unique_ids)}")

    if len(unique_ids) > 1:
        print("✗ RACE CONDITION DETECTED: Multiple instances created!")
        print(f"  Instance IDs: {list(unique_ids)[:5]}...")
    else:
        print("✓ All threads got the same instance")

    # Test with rapid sequential calls
    print("\nTesting rapid sequential calls...")
    sequential_ids = []
    for i in range(100):
        inst = get_ufo_classifier()
        sequential_ids.append(id(inst))

    unique_sequential = len(set(sequential_ids))
    print(f"Unique instances in sequential calls: {unique_sequential}")

    print("\n" + "-" * 40)
    print("SUMMARY:")

    has_race_condition = len(unique_ids) > 1 or unique_sequential > 1

    if has_race_condition:
        print("  BUG CLAIM: TRUE - Race condition exists")
        return True
    print("  BUG CLAIM: FALSE - Singleton is thread-safe")
    return False


def test_bug_4_memory_leak():
    """BUG CLAIM 5: Memory leaks via pattern compilation per instance"""
    print_section("BUG 4: Memory Leak in Pattern Compilation")

    # Test 1: Check if patterns are compiled per instance
    print("Test 1: Pattern compilation per instance check")

    instance1 = UFOClassifierService()
    instance2 = UFOClassifierService()

    patterns1_id = id(instance1.compiled_patterns)
    patterns2_id = id(instance2.compiled_patterns)

    print(f"Instance 1 patterns ID: {patterns1_id}")
    print(f"Instance 2 patterns ID: {patterns2_id}")

    if patterns1_id == patterns2_id:
        print("✓ Patterns are shared (same object)")
        patterns_per_instance = False
    else:
        print("✗ Patterns compiled per instance (different objects)")
        patterns_per_instance = True

    # Test 2: Memory growth test
    print("\nTest 2: Memory growth during repeated instantiation")

    gc.collect()
    initial_objects = len(gc.get_objects())
    print(f"Initial objects: {initial_objects}")

    instances = []
    for i in range(100):
        inst = UFOClassifierService()
        instances.append(inst)  # Keep reference to prevent GC

        if i % 20 == 0:
            gc.collect()

    gc.collect()
    final_objects = len(gc.get_objects())
    growth = final_objects - initial_objects

    print(f"Final objects: {final_objects}")
    print(f"Growth: {growth} objects")
    print(f"Growth per instance: {growth/100:.1f} objects")

    # Test 3: Pattern compilation inspection
    print("\nTest 3: Pattern compilation method analysis")

    import re

    # Check how many regex patterns are compiled
    num_categories = len(UFOClassifierService.PATTERNS)
    total_patterns = sum(
        len(patterns) for patterns in UFOClassifierService.PATTERNS.values()
    )

    print(f"Categories: {num_categories}")
    print(f"Total patterns: {total_patterns}")

    # Check if compiled patterns are cached
    inst = UFOClassifierService()
    compiled_count = sum(len(patterns) for patterns in inst.compiled_patterns.values())
    print(f"Compiled patterns per instance: {compiled_count}")

    print("\n" + "-" * 40)
    print("SUMMARY:")

    has_memory_leak = patterns_per_instance and growth > 5000

    if has_memory_leak:
        print("  BUG CLAIM: TRUE - Memory leak via per-instance compilation")
        return True
    if patterns_per_instance:
        print("  BUG CLAIM: PARTIAL - Patterns per instance, but limited growth")
        return False
    print("  BUG CLAIM: FALSE - No memory leak detected")
    return False


def test_bug_5_edge_case_failures():
    """BUG CLAIM 4: 15/34 edge tests fail (44% failure)"""
    print_section("BUG 5: Edge Case Test Failures")

    import re
    import subprocess

    print("Running edge case test suite...")

    # Run pytest and capture output
    result = subprocess.run(
        [
            "python",
            "-m",
            "pytest",
            "tests/services/test_ufo_classifier_edge_cases.py",
            "-v",
            "--tb=no",
        ],
        capture_output=True,
        text=True,
        cwd="/Users/chrislehnen/Projecten/Definitie-app",
        check=False,
    )

    output = result.stdout + result.stderr

    # Parse test results
    passed = re.findall(r"(\d+) passed", output)
    failed = re.findall(r"(\d+) failed", output)

    num_passed = int(passed[0]) if passed else 0
    num_failed = int(failed[0]) if failed else 0
    total_tests = num_passed + num_failed

    print("\nTest Results:")
    print(f"  Passed: {num_passed}")
    print(f"  Failed: {num_failed}")
    print(f"  Total: {total_tests}")

    if total_tests > 0:
        failure_rate = (num_failed / total_tests) * 100
        print(f"  Failure rate: {failure_rate:.1f}%")
    else:
        failure_rate = 0
        print("  No tests found")

    # Extract failed test names
    failed_tests = re.findall(r"FAILED (.*?) -", output)
    if failed_tests:
        print(f"\nFailed tests ({len(failed_tests)}):")
        for test in failed_tests[:10]:  # Show first 10
            test_name = test.split("::")[-1] if "::" in test else test
            print(f"  - {test_name}")
        if len(failed_tests) > 10:
            print(f"  ... and {len(failed_tests)-10} more")

    print("\n" + "-" * 40)
    print("SUMMARY:")

    claimed_failures = 15
    claimed_total = 34

    print(f"  Claimed: {claimed_failures}/{claimed_total} failures (44%)")
    print(f"  Actual: {num_failed}/{total_tests} failures ({failure_rate:.1f}%)")

    if abs(num_failed - claimed_failures) <= 2:  # Allow small variance
        print("  BUG CLAIM: TRUE - Significant test failures")
        return True
    if num_failed > 5:
        print("  BUG CLAIM: PARTIAL - Some failures, but not as many as claimed")
        return True
    print("  BUG CLAIM: FALSE - Most tests pass")
    return False


def main():
    """Run all bug verification tests."""
    print("=" * 60)
    print("  UFO CLASSIFIER v5.0.0 BUG VERIFICATION")
    print("  Analyzing claimed critical issues")
    print("=" * 60)

    results = {}

    # Test each bug claim
    try:
        results["bug1_empty_input"] = test_bug_1_empty_none_input()
    except Exception as e:
        print(f"\nBUG 1 TEST CRASHED: {e}")
        results["bug1_empty_input"] = None

    try:
        results["bug2_config"] = test_bug_2_config_loading()
    except Exception as e:
        print(f"\nBUG 2 TEST CRASHED: {e}")
        results["bug2_config"] = None

    try:
        results["bug3_singleton"] = test_bug_3_singleton_race_condition()
    except Exception as e:
        print(f"\nBUG 3 TEST CRASHED: {e}")
        results["bug3_singleton"] = None

    try:
        results["bug4_memory"] = test_bug_4_memory_leak()
    except Exception as e:
        print(f"\nBUG 4 TEST CRASHED: {e}")
        results["bug4_memory"] = None

    try:
        results["bug5_edge_cases"] = test_bug_5_edge_case_failures()
    except Exception as e:
        print(f"\nBUG 5 TEST CRASHED: {e}")
        results["bug5_edge_cases"] = None

    # Final report
    print("\n" + "=" * 60)
    print("  FINAL BUG VERIFICATION REPORT")
    print("=" * 60)

    confirmed_bugs = []
    false_positives = []

    bug_names = {
        "bug1_empty_input": "Empty/None input handling",
        "bug2_config": "Config file loading",
        "bug3_singleton": "Singleton race conditions",
        "bug4_memory": "Memory leaks",
        "bug5_edge_cases": "Edge case test failures",
    }

    for bug_id, is_real in results.items():
        name = bug_names[bug_id]
        if is_real is None:
            print(f"  ⚠️  {name}: COULD NOT VERIFY")
        elif is_real:
            confirmed_bugs.append(name)
            print(f"  ✗  {name}: CONFIRMED BUG")
        else:
            false_positives.append(name)
            print(f"  ✓  {name}: FALSE POSITIVE")

    print("\n" + "-" * 40)
    print(f"Confirmed bugs: {len(confirmed_bugs)}/{len(results)}")
    print(f"False positives: {len(false_positives)}/{len(results)}")

    # Severity assessment
    print("\n" + "=" * 60)
    print("  PRODUCTION READINESS ASSESSMENT")
    print("=" * 60)

    if len(confirmed_bugs) >= 3:
        print("Status: NOT PRODUCTION READY")
        print("Reason: Multiple critical bugs confirmed")
    elif len(confirmed_bugs) >= 1:
        print("Status: NEEDS FIXES")
        print("Reason: Some bugs require attention")
    else:
        print("Status: PRODUCTION READY")
        print("Reason: No critical bugs, only minor issues")

    print("\nCritical issues to fix:")
    for bug in confirmed_bugs:
        print(f"  - {bug}")

    return len(confirmed_bugs) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
