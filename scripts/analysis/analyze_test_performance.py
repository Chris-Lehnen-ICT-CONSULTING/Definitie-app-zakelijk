#!/usr/bin/env python3
"""Analyze test performance and identify slow tests."""

import re
import subprocess
from pathlib import Path


def analyze_test_performance():
    """Run tests with timing information and identify slow tests."""

    print("=" * 80)
    print("TEST PERFORMANCE ANALYSIS")
    print("=" * 80)

    # Run pytest with durations
    print("\nRunning tests to collect timing data...")

    cmd = [
        "python",
        "-m",
        "pytest",
        "--durations=50",
        "--tb=no",
        "-q",
        "--ignore=tests/performance/test_ufo_performance.py",
        "--ignore=tests/services/test_ufo_classifier_comprehensive.py",
        "--ignore=tests/services/test_ufo_classifier_service.py",
        "--ignore=tests/services/test_ufo_classifier_service_correctness.py",
        "-m",
        "not slow",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/Users/chrislehnen/Projecten/Definitie-app",
            check=False,
        )

        output = result.stdout + result.stderr

        # Parse slow tests from output
        slow_tests = []
        parsing = False

        for line in output.split("\n"):
            if "slowest durations" in line:
                parsing = True
                continue
            if parsing and line.strip():
                # Parse lines like "1.23s call     tests/test_example.py::test_function"
                match = re.match(r"(\d+\.\d+)s\s+\w+\s+(.+)", line)
                if match:
                    duration = float(match.group(1))
                    test_path = match.group(2)
                    slow_tests.append((duration, test_path))
                elif "passed" in line or "failed" in line or "error" in line:
                    break

        # Categorize tests by speed
        very_slow = [(d, t) for d, t in slow_tests if d > 1.0]
        slow = [(d, t) for d, t in slow_tests if 0.5 <= d < 1.0]
        moderate = [(d, t) for d, t in slow_tests if 0.2 <= d < 0.5]

        print("\n🐌 VERY SLOW TESTS (>1 second):")
        for duration, test in very_slow[:20]:
            print(f"  {duration:6.2f}s - {test}")

        print(f"\n⚠️ SLOW TESTS (0.5-1 second): {len(slow)} tests")
        for duration, test in slow[:10]:
            print(f"  {duration:6.2f}s - {test}")

        print(f"\n⏱️ MODERATE TESTS (0.2-0.5 second): {len(moderate)} tests")

        # Check for tests with sleep
        print("\n\n🔍 TESTS WITH SLEEP CALLS:")
        sleep_tests = []
        for test_file in Path("tests").rglob("test_*.py"):
            if "__pycache__" in str(test_file):
                continue
            try:
                with open(test_file) as f:
                    content = f.read()
                    if "time.sleep" in content or "sleep(" in content:
                        # Count occurrences
                        count = content.count("sleep(")
                        sleep_tests.append(
                            (test_file.relative_to(Path("tests")), count)
                        )
            except:
                pass

        for test_file, count in sorted(sleep_tests, key=lambda x: x[1], reverse=True)[
            :15
        ]:
            print(f"  {test_file}: {count} sleep() calls")

        # Check for database tests
        print("\n\n💾 DATABASE TESTS WITHOUT TRANSACTIONS:")
        db_tests = []
        for test_file in Path("tests").rglob("test_*.py"):
            if "__pycache__" in str(test_file):
                continue
            try:
                with open(test_file) as f:
                    content = f.read()
                    if any(
                        x in content
                        for x in [
                            "sqlite",
                            "database",
                            "cursor",
                            "CREATE TABLE",
                            "INSERT INTO",
                        ]
                    ):
                        if (
                            "transaction" not in content.lower()
                            and "rollback" not in content
                        ):
                            db_tests.append(test_file.relative_to(Path("tests")))
            except:
                pass

        for test_file in db_tests[:15]:
            print(f"  {test_file}")

        # Check for I/O heavy tests
        print("\n\n📁 I/O HEAVY TESTS:")
        io_tests = []
        for test_file in Path("tests").rglob("test_*.py"):
            if "__pycache__" in str(test_file):
                continue
            try:
                with open(test_file) as f:
                    content = f.read()
                    io_score = 0
                    io_score += content.count("open(") * 2
                    io_score += content.count("Path(").count(".write") * 3
                    io_score += content.count(".read(") * 2
                    io_score += content.count("json.dump") * 2
                    io_score += content.count("json.load") * 2

                    if io_score > 10:
                        io_tests.append(
                            (test_file.relative_to(Path("tests")), io_score)
                        )
            except:
                pass

        for test_file, score in sorted(io_tests, key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {test_file}: I/O score {score}")

        # Summary
        print("\n\n📊 PERFORMANCE SUMMARY:")
        print(f"  Very slow tests (>1s): {len(very_slow)}")
        print(f"  Slow tests (0.5-1s): {len(slow)}")
        print(f"  Tests with sleep(): {len(sleep_tests)}")
        print(f"  DB tests without transactions: {len(db_tests)}")
        print(f"  I/O heavy tests: {len(io_tests)}")

        print("\n\n💡 RECOMMENDATIONS:")
        print("  1. Add @pytest.mark.slow to tests >0.5s and skip in CI")
        print("  2. Replace sleep() with proper wait conditions or mocks")
        print("  3. Use database transactions for test isolation")
        print("  4. Mock file I/O operations where possible")
        print("  5. Use pytest-xdist for parallel execution")

    except subprocess.TimeoutExpired:
        print("❌ Test run timed out after 30 seconds")
        print("   This indicates very slow tests or infinite loops")
    except Exception as e:
        print(f"❌ Error running tests: {e}")


if __name__ == "__main__":
    analyze_test_performance()
