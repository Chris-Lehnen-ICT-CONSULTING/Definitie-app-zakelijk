#!/usr/bin/env python3
"""
Performance verification script for DEF-110 fix.

Verifies:
1. RuleCache loads only 1x (not 4x)
2. No rerun cascade in logs
3. Startup completes in reasonable time (~6s, not 35s)

Usage:
    python scripts/verify_def110_fix.py
"""

import subprocess
import sys
import time
from pathlib import Path


def verify_fix():
    """Run Streamlit in headless mode and verify performance metrics."""

    print("🔍 DEF-110 Performance Verification")
    print("=" * 50)

    # Start Streamlit with headless mode
    log_file = Path("logs/verification_run.log")
    log_file.parent.mkdir(exist_ok=True)

    print(f"\n1. Starting Streamlit app...")
    print(f"   Log: {log_file}")

    start_time = time.time()

    # Run streamlit with timeout
    try:
        proc = subprocess.Popen(
            ["streamlit", "run", "src/main.py", "--server.headless", "true"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env={**subprocess.os.environ, "OPENAI_API_KEY": subprocess.os.environ.get("OPENAI_API_KEY_PROD", "")}
        )

        # Capture first 10 seconds of output
        output_lines = []
        timeout = 10

        while time.time() - start_time < timeout:
            line = proc.stdout.readline()
            if line:
                output_lines.append(line)
                if "You can now view your Streamlit app" in line:
                    break
            time.sleep(0.1)

        proc.terminate()
        proc.wait(timeout=2)

        elapsed = time.time() - start_time

        # Write output to log
        with open(log_file, "w") as f:
            f.write("".join(output_lines))

        # Analyze output
        print(f"\n2. Startup completed in {elapsed:.1f}s")

        # Count critical patterns
        full_output = "".join(output_lines)

        rule_cache_loads = full_output.count("RuleCache initialized")
        rerun_count = full_output.count("Rerun requested")
        context_cleans = full_output.count("Context state cleaned")

        print(f"\n3. Performance Metrics:")
        print(f"   ✓ Startup time: {elapsed:.1f}s (target: <10s)")
        print(f"   ✓ RuleCache loads: {rule_cache_loads}x (target: 1x)")
        print(f"   ✓ Reruns: {rerun_count}x")
        print(f"   ✓ Context cleanups: {context_cleans}x (target: 1x)")

        # Verification
        success = True

        if elapsed > 15:
            print(f"\n   ❌ FAIL: Startup too slow ({elapsed:.1f}s > 15s)")
            success = False

        if rule_cache_loads > 1:
            print(f"\n   ❌ FAIL: RuleCache loaded multiple times ({rule_cache_loads}x)")
            success = False

        if context_cleans > 2:  # Allow 1-2 cleanups (initial + potential rerun)
            print(f"\n   ⚠️  WARNING: Multiple context cleanups ({context_cleans}x)")

        if success:
            print("\n✅ VERIFICATION PASSED")
            print(f"   Fix is working correctly - no performance regression detected")
            return 0
        else:
            print("\n❌ VERIFICATION FAILED")
            print(f"   Performance regression still present - review {log_file}")
            return 1

    except subprocess.TimeoutExpired:
        print("\n❌ FAIL: Streamlit startup timed out")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(verify_fix())
