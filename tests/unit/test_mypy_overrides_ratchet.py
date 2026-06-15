"""Unit tests for the mypy per-module override ratchet (DEF-431, Fase 2).

Deterministic: parse-logic tests use inline TOML; the invariant test parses the
real pyproject.toml to assert the committed override count matches the baseline.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts import mypy_overrides_ratchet as mor

pytestmark = [pytest.mark.unit]


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "pyproject.toml"
    p.write_text(body, encoding="utf-8")
    return p


class TestCountOverrides:
    def test_counts_modules_in_disallow_false_block(self, tmp_path):
        p = _write(
            tmp_path,
            "[[tool.mypy.overrides]]\n"
            "disallow_untyped_defs = false\n"
            'module = ["a.b", "c.d", "e.f"]\n',
        )
        assert mor.count_overrides(p) == 3

    def test_ignores_blocks_without_disallow_false(self, tmp_path):
        p = _write(
            tmp_path,
            "[[tool.mypy.overrides]]\n"
            "ignore_missing_imports = true\n"
            'module = ["x.y", "z.w"]\n',
        )
        assert mor.count_overrides(p) == 0

    def test_no_overrides_returns_zero(self, tmp_path):
        p = _write(tmp_path, '[tool.mypy]\npython_version = "3.13"\n')
        assert mor.count_overrides(p) == 0

    def test_sums_multiple_disallow_false_blocks(self, tmp_path):
        p = _write(
            tmp_path,
            "[[tool.mypy.overrides]]\n"
            "disallow_untyped_defs = false\n"
            'module = ["a.b"]\n\n'
            "[[tool.mypy.overrides]]\n"
            "disallow_untyped_defs = false\n"
            'module = ["c.d", "e.f"]\n',
        )
        assert mor.count_overrides(p) == 3

    def test_string_module_counts_one(self, tmp_path):
        # mypy accepts `module` as a bare string, not only a list.
        p = _write(
            tmp_path,
            "[[tool.mypy.overrides]]\n"
            "disallow_untyped_defs = false\n"
            'module = "pkg.mod"\n',
        )
        assert mor.count_overrides(p) == 1

    def test_dedups_modules_across_blocks(self, tmp_path):
        # Same module listed twice must count once (true exemption breadth).
        p = _write(
            tmp_path,
            "[[tool.mypy.overrides]]\n"
            "disallow_untyped_defs = false\n"
            'module = ["a.b", "c.d"]\n\n'
            "[[tool.mypy.overrides]]\n"
            "disallow_untyped_defs = false\n"
            'module = ["a.b"]\n',
        )
        assert mor.count_overrides(p) == 2

    def test_wildcard_module_is_rejected(self, tmp_path):
        # A wildcard would exempt a whole subtree while counting as one entry —
        # dodging both gates. The teller must fail closed (DEF-431 review).
        p = _write(
            tmp_path,
            "[[tool.mypy.overrides]]\n"
            "disallow_untyped_defs = false\n"
            'module = ["src.services.*"]\n',
        )
        with pytest.raises(SystemExit):
            mor.count_overrides(p)


class TestBaselineRoundtrip:
    def test_write_then_read(self, tmp_path):
        path = tmp_path / "baseline.txt"
        mor.write_baseline(42, path)
        assert mor.read_baseline(path) == 42

    def test_missing_baseline_raises(self, tmp_path):
        with pytest.raises(SystemExit):
            mor.read_baseline(tmp_path / "nope.txt")


class TestMainExitCodes:
    def test_grow_fails(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(mor, "count_overrides", lambda *a, **k: 150)
        monkeypatch.setattr(mor, "read_baseline", lambda *a, **k: 145)
        assert mor.main([]) == 1
        assert "grew" in capsys.readouterr().out

    def test_at_baseline_passes(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mor, "count_overrides", lambda *a, **k: 145)
        monkeypatch.setattr(mor, "read_baseline", lambda *a, **k: 145)
        assert mor.main([]) == 0

    def test_shrink_passes_without_update(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(mor, "count_overrides", lambda *a, **k: 140)
        monkeypatch.setattr(mor, "read_baseline", lambda *a, **k: 145)
        written: list[int] = []
        monkeypatch.setattr(mor, "write_baseline", lambda v, *a, **k: written.append(v))
        assert mor.main([]) == 0
        assert "dropped" in capsys.readouterr().out
        assert written == []  # shrink WITHOUT --update must not touch the baseline

    def test_shrink_with_update_writes_lower_baseline(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mor, "count_overrides", lambda *a, **k: 140)
        monkeypatch.setattr(mor, "read_baseline", lambda *a, **k: 145)
        written: list[int] = []
        monkeypatch.setattr(mor, "write_baseline", lambda v, *a, **k: written.append(v))
        assert mor.main(["--update"]) == 0
        assert written == [140]  # --update ratchets the baseline down to the count


class TestRealConfigConsistent:
    """The committed pyproject override count must match the baseline."""

    def test_real_count_matches_baseline(self):
        assert mor.count_overrides() == mor.read_baseline()

    def test_main_passes_on_real_repo(self):
        assert mor.main([]) == 0
