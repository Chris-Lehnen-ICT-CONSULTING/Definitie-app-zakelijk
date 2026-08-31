"""Contracttests voor de Python-runtime van Make-targets."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MAKEFILE = _REPO_ROOT / "Makefile"
_TEST_TARGETS = (
    "test",
    "test-all",
    "test-unit",
    "test-integration",
    "test-acceptance",
    "test-performance",
    "test-smoke",
    "test-parallel",
    "test-cov",
    "test-cov-ci",
    "test-durations",
    "smoke-web-lookup",
    "test-markers-check",
)


def _makefile_text() -> str:
    return _MAKEFILE.read_text(encoding="utf-8")


def _run_make(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["make", "-s", *arguments],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_makefile_defines_pytest_runner_from_selected_python():
    assert re.search(
        r"^PYTEST\s*:?=\s*\$\(PY\) -m pytest$",
        _makefile_text(),
        flags=re.MULTILINE,
    )


def test_makefile_has_no_bare_pytest_commands():
    bare_pytest = re.compile(r"^\t@?(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*pytest(?:\s|$)")
    offenders = [
        f"{line_number}: {line.strip()}"
        for line_number, line in enumerate(_makefile_text().splitlines(), start=1)
        if bare_pytest.match(line)
    ]

    assert offenders == []


def test_python_version_guard_accepts_required_runtime():
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}"

    result = _run_make(
        "check-python",
        f"PY={sys.executable}",
        f"REQUIRED_PYTHON_VERSION={current_version}",
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_python_version_guard_rejects_different_runtime():
    result = _run_make(
        "check-python",
        f"PY={sys.executable}",
        "REQUIRED_PYTHON_VERSION=0.0",
    )

    assert result.returncode != 0
    assert "Python 0.0 vereist" in result.stdout + result.stderr


def test_all_test_targets_require_python_version_guard():
    makefile = _makefile_text()
    missing_guard = []
    for target in _TEST_TARGETS:
        target_rule = re.search(
            rf"^{re.escape(target)}:(?P<dependencies>[^\n]*)$",
            makefile,
            flags=re.MULTILINE,
        )
        if (
            target_rule is None
            or "check-python" not in target_rule.group("dependencies").split()
        ):
            missing_guard.append(target)

    assert missing_guard == []
