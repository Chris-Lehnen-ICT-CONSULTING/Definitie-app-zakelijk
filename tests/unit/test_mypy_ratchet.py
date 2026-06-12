"""Unit tests for the mypy ratchet (DEF-419).

Fully deterministic: the mypy subprocess is mocked so the unit suite never
depends on the installed mypy version. The real count-vs-baseline check is
enforced by the pinned CI gate (quality-gates.yml) and `make mypy-check`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

# scripts/ is not on the default pytest path (only src/ is), so add the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts import mypy_ratchet as mr

pytestmark = [pytest.mark.unit]


class TestCountErrors:
    """count_errors parses the mypy summary line and fails cleanly otherwise."""

    def _mock_run(self, monkeypatch, *, returncode, stdout, stderr=""):
        monkeypatch.setattr(
            mr.subprocess,
            "run",
            lambda *a, **k: SimpleNamespace(
                returncode=returncode, stdout=stdout, stderr=stderr
            ),
        )

    def test_parses_found_n_errors(self, monkeypatch):
        self._mock_run(
            monkeypatch,
            returncode=1,
            stdout=(
                "src/x.py:1: error: foo\n"
                "Found 92 errors in 29 files (checked 371 source files)\n"
            ),
        )
        assert mr.count_errors() == 92

    def test_singular_error_line(self, monkeypatch):
        self._mock_run(
            monkeypatch,
            returncode=1,
            stdout="Found 1 error in 1 file (checked 371 source files)\n",
        )
        assert mr.count_errors() == 1

    def test_success_line_is_zero(self, monkeypatch):
        self._mock_run(
            monkeypatch,
            returncode=0,
            stdout="Success: no issues found in 371 source files\n",
        )
        assert mr.count_errors() == 0

    def test_unparseable_output_exits(self, monkeypatch):
        self._mock_run(
            monkeypatch, returncode=2, stdout="internal error", stderr="traceback"
        )
        with pytest.raises(SystemExit):
            mr.count_errors()


class TestBaselineIO:
    def test_roundtrip(self, tmp_path):
        p = tmp_path / "b.txt"
        mr.write_baseline(80, p)
        assert mr.read_baseline(p) == 80

    def test_missing_exits(self, tmp_path):
        with pytest.raises(SystemExit):
            mr.read_baseline(tmp_path / "nope.txt")

    def test_corrupt_exits(self, tmp_path):
        p = tmp_path / "b.txt"
        p.write_text("not-a-number", encoding="utf-8")
        with pytest.raises(SystemExit):
            mr.read_baseline(p)


class TestDecision:
    def _stub(self, monkeypatch, current, baseline):
        monkeypatch.setattr(mr, "count_errors", lambda: current)
        monkeypatch.setattr(mr, "read_baseline", lambda: baseline)

    def test_growth_fails(self, monkeypatch):
        self._stub(monkeypatch, 95, 92)
        assert mr.main([]) == 1

    def test_equal_passes(self, monkeypatch):
        self._stub(monkeypatch, 92, 92)
        assert mr.main([]) == 0

    def test_shrink_passes_without_update(self, monkeypatch):
        self._stub(monkeypatch, 88, 92)
        written: list[int] = []
        monkeypatch.setattr(mr, "write_baseline", lambda v: written.append(v))
        assert mr.main([]) == 0
        assert written == []

    def test_shrink_with_update(self, monkeypatch):
        self._stub(monkeypatch, 88, 92)
        written: list[int] = []
        monkeypatch.setattr(mr, "write_baseline", lambda v: written.append(v))
        assert mr.main(["--update"]) == 0
        assert written == [88]
