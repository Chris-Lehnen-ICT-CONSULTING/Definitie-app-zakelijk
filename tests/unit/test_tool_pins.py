"""Unit tests for the tool-pin consistency guard (DEF-430).

Deterministic: parse-logic tests use inline text; the invariant test parses the
real config files (static, no tools installed) to assert ruff/mypy are pinned to
one version across every source.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts import check_tool_pins as ctp

pytestmark = [pytest.mark.unit]


class TestExtract:
    def test_strips_leading_v(self):
        assert ctp._extract(r"rev:\s*(\S+)", "rev: v0.15.16", "x") == "0.15.16"

    def test_plain_version(self):
        assert ctp._extract(r"ruff==(\S+)", "ruff==0.15.16", "x") == "0.15.16"

    def test_missing_raises(self):
        with pytest.raises(SystemExit):
            ctp._extract(r"ruff==(\S+)", "nothing here", "ruff")


class TestInconsistency:
    def test_all_equal_returns_none(self):
        assert ctp.inconsistency("ruff", {"a": "0.15.16", "b": "0.15.16"}) is None

    def test_mismatch_returns_message(self):
        msg = ctp.inconsistency("ruff", {"a": "0.15.16", "b": "0.14.5"})
        assert msg is not None
        assert "mismatch" in msg
        assert "0.14.5" in msg


class TestRealConfigConsistent:
    """The committed config files must pin ruff/mypy to one version each."""

    def test_ruff_consistent(self):
        versions = ctp.ruff_versions()
        assert len(set(versions.values())) == 1, versions

    def test_mypy_consistent(self):
        versions = ctp.mypy_versions()
        assert len(set(versions.values())) == 1, versions

    def test_main_passes_on_real_repo(self):
        assert ctp.main() == 0
