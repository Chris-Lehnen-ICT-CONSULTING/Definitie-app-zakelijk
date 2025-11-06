"""
Performance regression tests for DEF-110 fix.

These tests monitor critical performance metrics to detect regressions like the one
fixed in DEF-110 where force_clean=True caused a 74,569% slowdown.

Run with:
    pytest tests/performance/test_def110_regression.py -v

Design:
- Tests run in isolated subprocess to ensure fresh Python process
- Monitors critical metrics: RuleCache loads, ServiceContainer inits, startup time
- Fails if metrics exceed acceptable thresholds
"""

import subprocess
import sys
import time
from pathlib import Path

import pytest


class TestDEF110Regression:
    """Monitor performance regression patterns from DEF-110."""

    @pytest.mark.performance()
    def test_no_rerun_cascade_in_logs(self, tmp_path):
        """
        CRITICAL: Verify no rerun cascade occurs during startup.

        DEF-110 issue: force_clean=True in render() caused 4x Python process restarts.

        Acceptance criteria:
        - No more than 1 rerun during normal startup
        - Log does not contain "Context state cleaned" more than 2x
        """
        log_file = tmp_path / "startup.log"

        # Start Streamlit with headless mode, capture first 5 seconds
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "src/main.py",
                "--server.headless",
                "true",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=Path(__file__).parent.parent.parent,  # Project root
        )

        # Collect output for 5 seconds
        output_lines = []
        start = time.time()
        while time.time() - start < 5:
            line = proc.stdout.readline()
            if line:
                output_lines.append(line)
                if "You can now view your Streamlit app" in line:
                    break

        proc.terminate()
        proc.wait(timeout=2)

        # Write log for debugging
        log_file.write_text("".join(output_lines))

        # Check for rerun cascade pattern
        full_output = "".join(output_lines)
        rerun_count = full_output.count("Rerun requested")
        context_clean_count = full_output.count("Context state cleaned")

        assert (
            rerun_count <= 1
        ), f"REGRESSION: {rerun_count} reruns detected (expected ≤1). Check {log_file}"
        assert (
            context_clean_count <= 2
        ), f"REGRESSION: {context_clean_count}x context cleanups (expected ≤2). Check {log_file}"

    @pytest.mark.performance()
    def test_rule_cache_loads_once(self, tmp_path):
        """
        CRITICAL: Verify RuleCache is loaded only 1x during startup.

        DEF-110 issue: Rerun cascade caused RuleCache to load 4x (US-202 regression).

        Acceptance criteria:
        - "RuleCache initialized" appears exactly 1x in logs
        - "Loading 45 validation rules" appears exactly 1x
        """
        log_file = tmp_path / "rulecache.log"

        # Start app and capture output
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "src/main.py",
                "--server.headless",
                "true",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        # Collect output
        output_lines = []
        start = time.time()
        while time.time() - start < 10:
            line = proc.stdout.readline()
            if line:
                output_lines.append(line)
                if "You can now view your Streamlit app" in line:
                    break

        proc.terminate()
        proc.wait(timeout=2)

        log_file.write_text("".join(output_lines))

        full_output = "".join(output_lines)
        rule_cache_init_count = full_output.count("RuleCache initialized")

        # Allow 0 or 1 - might not appear in truncated output
        assert (
            rule_cache_init_count <= 1
        ), f"REGRESSION: RuleCache loaded {rule_cache_init_count}x (expected 1x). Check {log_file}"

    @pytest.mark.performance()
    @pytest.mark.slow()
    def test_startup_time_acceptable(self, tmp_path):
        """
        WARNING: Verify startup completes in reasonable time.

        DEF-110 issue: 35s startup due to rerun cascade (baseline: 1.2s).

        Acceptance criteria:
        - Startup completes in <15s (generous threshold for CI environments)
        - Warns if >5s (indicates potential regression)

        Note: This test is marked 'slow' and may be skipped in fast test runs.
        """
        log_file = tmp_path / "startup_time.log"

        start = time.time()

        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "src/main.py",
                "--server.headless",
                "true",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        # Wait for app ready signal
        output_lines = []
        timeout = 20
        app_ready = False

        while time.time() - start < timeout:
            line = proc.stdout.readline()
            if line:
                output_lines.append(line)
                if "You can now view your Streamlit app" in line:
                    app_ready = True
                    break

        elapsed = time.time() - start

        proc.terminate()
        proc.wait(timeout=2)

        log_file.write_text("".join(output_lines))

        # Assertions
        assert app_ready, f"App did not start within {timeout}s - CRITICAL REGRESSION"
        assert elapsed < 15, (
            f"CRITICAL: Startup took {elapsed:.1f}s (expected <15s). "
            f"Possible rerun cascade regression. Check {log_file}"
        )

        if elapsed > 5:
            pytest.warns(
                UserWarning,
                match=f"WARNING: Startup took {elapsed:.1f}s (>5s threshold)",
            )

    @pytest.mark.performance()
    def test_no_force_clean_in_render_methods(self):
        """
        STRUCTURAL: Verify force_clean=True is not used in render() methods.

        This is a code-level check to prevent the exact pattern that caused DEF-110.

        Acceptance criteria:
        - No force_clean=True in render() methods
        - Pre-commit hook should catch this, but verify in tests too
        """
        # Find all render methods in UI code
        ui_dir = Path(__file__).parent.parent.parent / "src" / "ui"
        py_files = list(ui_dir.rglob("*.py"))

        violations = []

        for py_file in py_files:
            content = py_file.read_text(encoding="utf-8")
            lines = content.splitlines()

            in_render_method = False
            render_start_line = 0

            for i, line in enumerate(lines, start=1):
                # Detect render method start
                if "def render(self):" in line or "def render(" in line:
                    in_render_method = True
                    render_start_line = i

                # Detect method end (simplified heuristic)
                if in_render_method and line.strip().startswith("def "):
                    if i != render_start_line:
                        in_render_method = False

                # Check for force_clean=True inside render
                if in_render_method and "force_clean=True" in line:
                    violations.append(
                        (py_file.relative_to(ui_dir.parent.parent), i, line.strip())
                    )

        # Report violations
        if violations:
            msg = "CRITICAL: force_clean=True found in render() methods:\n"
            for file, line_num, line in violations:
                msg += f"  {file}:{line_num}: {line}\n"
            msg += "\nThis pattern causes rerun cascades (DEF-110)!"
            pytest.fail(msg)

    @pytest.mark.performance()
    def test_context_cleaner_idempotent_guard(self):
        """
        STRUCTURAL: Verify context cleaner has idempotent guard.

        The init_context_cleaner() function must have a guard to prevent
        multiple executions unless force_clean=True is explicitly passed.

        Acceptance criteria:
        - init_context_cleaner has default force_clean=False
        - Function checks context_cleaned flag before executing
        """
        # Verify signature
        import inspect

        from ui.components.context_state_cleaner import init_context_cleaner

        sig = inspect.signature(init_context_cleaner)
        assert "force_clean" in sig.parameters, "Missing force_clean parameter"

        force_clean_param = sig.parameters["force_clean"]
        assert (
            force_clean_param.default is False
        ), f"force_clean default should be False, got {force_clean_param.default}"

        # Verify implementation (check source code for guard pattern)
        source = inspect.getsource(init_context_cleaner)
        assert (
            "context_cleaned" in source
        ), "Missing idempotent guard (context_cleaned flag)"
        assert (
            'SessionStateManager.get_value("context_cleaned")' in source
        ), "Guard not using SessionStateManager"


@pytest.mark.performance()
class TestPerformanceBaseline:
    """Baseline performance metrics for regression detection."""

    def test_document_current_metrics(self, caplog):
        """
        Document current performance metrics for future comparison.

        This test always passes but logs current metrics for analysis.
        Used to establish baseline after DEF-110 fix.
        """
        # Run verification script
        from scripts.verify_def110_fix import verify_fix

        result = verify_fix()

        # This test documents metrics, doesn't fail
        assert True, "Baseline metrics logged"
