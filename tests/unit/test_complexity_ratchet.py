"""Unit tests for the complexity ratchet (DEF-418).

Covers the decision logic (grow/equal/shrink/update) with the ruff call mocked,
plus an invariant test that the committed baseline matches the real count so the
two never drift apart silently.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

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


class TestBaselineInvariant:
    """Reality must never exceed the committed baseline (the ratchet contract).

    Uses ``<=`` rather than ``==`` so a benign drop (e.g. a ruff version that
    counts fewer) stays green, while real growth fails — mirroring the CI gate.
    """

    def test_real_count_within_baseline(self):
        current, _ = cr.count_violations()
        baseline = cr.read_baseline()
        assert current <= baseline, (
            f"Complexity count ({current}) exceeds committed baseline ({baseline}). "
            "Refactor the new complexity, or raise the baseline deliberately."
        )
