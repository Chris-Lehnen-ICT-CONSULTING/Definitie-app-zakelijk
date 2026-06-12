"""Unit tests for the complexity ratchet (DEF-418).

Fully deterministic: the ruff subprocess is mocked so the unit suite never
depends on the installed ruff version. The real count-vs-baseline check is
enforced by the pinned CI gate (quality-gates.yml) and `make complexity-check`.
Covers baseline I/O, count parsing + error paths, and the grow/equal/shrink/
update decision logic.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

# scripts/ is not on the default pytest path (only src/ is), so add the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts import complexity_ratchet as cr

pytestmark = [pytest.mark.unit]


class TestBaselineIO:
    def test_write_then_read_roundtrip(self, tmp_path):
        path = tmp_path / "baseline.txt"
        cr.write_baseline(195, path)
        assert cr.read_baseline(path) == 195

    def test_read_strips_whitespace(self, tmp_path):
        path = tmp_path / "baseline.txt"
        path.write_text("  201 \n", encoding="utf-8")
        assert cr.read_baseline(path) == 201

    def test_read_missing_file_exits_cleanly(self, tmp_path):
        with pytest.raises(SystemExit):
            cr.read_baseline(tmp_path / "does_not_exist.txt")

    def test_read_corrupt_file_exits_cleanly(self, tmp_path):
        path = tmp_path / "baseline.txt"
        path.write_text("not-a-number", encoding="utf-8")
        with pytest.raises(SystemExit):
            cr.read_baseline(path)


class TestCountViolations:
    """count_violations parses ruff JSON and fails cleanly on ruff errors.

    The ruff subprocess is mocked so these stay deterministic and independent of
    the installed ruff version (the real count is enforced by the pinned CI gate).
    """

    def _mock_run(self, monkeypatch, *, returncode, stdout, stderr=""):
        monkeypatch.setattr(
            cr.subprocess,
            "run",
            lambda *a, **k: SimpleNamespace(
                returncode=returncode, stdout=stdout, stderr=stderr
            ),
        )

    def test_parses_counts_per_code(self, monkeypatch):
        payload = json.dumps([{"code": "C901"}, {"code": "C901"}, {"code": "PLR0912"}])
        self._mock_run(monkeypatch, returncode=1, stdout=payload)
        total, per_code = cr.count_violations()
        assert total == 3
        assert per_code["C901"] == 2
        assert per_code["PLR0912"] == 1

    def test_no_violations_returns_zero(self, monkeypatch):
        self._mock_run(monkeypatch, returncode=0, stdout="[]")
        assert cr.count_violations() == (0, Counter())

    def test_ruff_failure_exits(self, monkeypatch):
        self._mock_run(monkeypatch, returncode=2, stdout="", stderr="bad config")
        with pytest.raises(SystemExit):
            cr.count_violations()

    def test_invalid_json_exits(self, monkeypatch):
        self._mock_run(monkeypatch, returncode=1, stdout="not json at all")
        with pytest.raises(SystemExit):
            cr.count_violations()


class TestRatchetDecision:
    def _stub(self, monkeypatch, current: int, baseline: int):
        monkeypatch.setattr(
            cr, "count_violations", lambda: (current, Counter({"C901": current}))
        )
        monkeypatch.setattr(cr, "read_baseline", lambda: baseline)

    def test_growth_fails(self, monkeypatch):
        self._stub(monkeypatch, current=210, baseline=201)
        assert cr.main([]) == 1

    def test_equal_passes(self, monkeypatch):
        self._stub(monkeypatch, current=201, baseline=201)
        assert cr.main([]) == 0

    def test_shrink_passes_without_update(self, monkeypatch):
        self._stub(monkeypatch, current=190, baseline=201)
        written: list[int] = []
        monkeypatch.setattr(cr, "write_baseline", lambda v: written.append(v))
        assert cr.main([]) == 0
        assert written == []  # baseline not touched without --update

    def test_shrink_with_update_ratchets_down(self, monkeypatch):
        self._stub(monkeypatch, current=190, baseline=201)
        written: list[int] = []
        monkeypatch.setattr(cr, "write_baseline", lambda v: written.append(v))
        assert cr.main(["--update"]) == 0
        assert written == [190]


class TestFormatBreakdown:
    def test_breakdown_lists_all_codes_in_order(self):
        per_code = Counter({"C901": 2, "PLR0912": 1})
        result = cr._format_breakdown(per_code)
        # All four tracked codes appear, zero-filled, in declaration order.
        assert result == "C901=2, PLR0911=0, PLR0912=1, PLR0915=0"
