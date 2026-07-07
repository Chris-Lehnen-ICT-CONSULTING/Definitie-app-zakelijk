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

    def test_decoy_in_diagnostic_does_not_match(self, monkeypatch):
        """A diagnostic line mentioning 'Found N errors' must not be counted."""
        self._mock_run(
            monkeypatch,
            returncode=1,
            stdout=(
                'src/x.py:1: error: Bad string "Found 5 errors" here\n'
                "Found 92 errors in 29 files (checked 371 source files)\n"
            ),
        )
        assert mr.count_errors() == 92

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
    def _stub(self, monkeypatch, current, baseline, services=0):
        # count_errors dispatches on its args: the global src/ scope returns
        # `current`, the src/services subtree returns `services` (default clean).
        def fake_count(args=mr.MYPY_ARGS):
            return services if tuple(args) == mr.SERVICES_ARGS else current

        monkeypatch.setattr(mr, "count_errors", fake_count)
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


class TestServicesSubtreeGuard:
    """DEF-569: while the global baseline is > 0, the KRITIEK src/services
    subtree must still be proven mypy-clean (the aggregate count does not
    partition per subtree). When baseline == 0 the guard is skipped."""

    def _stub(self, monkeypatch, current, baseline, services):
        def fake_count(args=mr.MYPY_ARGS):
            return services if tuple(args) == mr.SERVICES_ARGS else current

        monkeypatch.setattr(mr, "count_errors", fake_count)
        monkeypatch.setattr(mr, "read_baseline", lambda: baseline)

    def test_baseline_zero_skips_services_check(self, monkeypatch):
        # Guard must NOT invoke the services scope when baseline == 0 — that
        # would re-add the ~42s cost DEF-568 removed. Track the scopes queried.
        queried: list[tuple] = []

        def fake_count(args=mr.MYPY_ARGS):
            queried.append(tuple(args))
            return 0

        monkeypatch.setattr(mr, "count_errors", fake_count)
        monkeypatch.setattr(mr, "read_baseline", lambda: 0)
        assert mr.main([]) == 0
        assert mr.SERVICES_ARGS not in queried

    def test_baseline_positive_services_dirty_fails(self, monkeypatch):
        # Global count is AT baseline (main ratchet would pass), but the
        # services subtree has an error → the guard must fail the gate.
        self._stub(monkeypatch, current=5, baseline=5, services=1)
        assert mr.main([]) == 1

    def test_baseline_positive_services_clean_passes(self, monkeypatch):
        self._stub(monkeypatch, current=5, baseline=5, services=0)
        assert mr.main([]) == 0

    def test_baseline_positive_services_dirty_fails_even_on_shrink(self, monkeypatch):
        # Even when the global count shrank (would normally pass/ratchet), a
        # dirty services subtree still fails.
        self._stub(monkeypatch, current=3, baseline=5, services=2)
        assert mr.main([]) == 1

    def test_update_with_dirty_services_does_not_ratchet(self, monkeypatch):
        # The most dangerous combination: --update + global shrink + dirty
        # services. The guard must fire BEFORE the ratchet writes, so a broken
        # services subtree is never cemented into a lower baseline.
        self._stub(monkeypatch, current=3, baseline=5, services=1)
        written: list[int] = []
        monkeypatch.setattr(mr, "write_baseline", lambda v: written.append(v))
        assert mr.main(["--update"]) == 1
        assert written == []  # baseline NOT lowered while services is dirty

    def test_update_with_clean_services_still_ratchets(self, monkeypatch):
        # Mirror: clean services + shrink + --update must still ratchet down.
        self._stub(monkeypatch, current=3, baseline=5, services=0)
        written: list[int] = []
        monkeypatch.setattr(mr, "write_baseline", lambda v: written.append(v))
        assert mr.main(["--update"]) == 0
        assert written == [3]

    def test_guard_active_at_lower_bound_baseline_one(self, monkeypatch):
        # Boundary: the guard must be active for the smallest positive baseline
        # (catches an off-by-one like `baseline >= 2`).
        self._stub(monkeypatch, current=1, baseline=1, services=1)
        assert mr.main([]) == 1
