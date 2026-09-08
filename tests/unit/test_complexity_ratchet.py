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

    @pytest.mark.parametrize("inhoud", ["-3", "", "1.5"])
    def test_read_rejects_non_natural_numbers(self, tmp_path, inhoud):
        path = tmp_path / "baseline.txt"
        path.write_text(inhoud, encoding="utf-8")
        with pytest.raises(SystemExit):
            cr.read_baseline(path)


#: Bestaat in deze repo en ligt binnen de gemeten scope; de gate valideert de
#: gerapporteerde bestandsnamen tegen de werkelijke selectie.
_GESELECTEERD = "src/main.py"


def _bevinding(code: str, bestand: str = _GESELECTEERD) -> dict:
    return {"code": code, "filename": bestand}


class TestCountViolations:
    """count_violations parses ruff JSON and fails cleanly on ruff errors.

    De ruff-subprocessen zijn nagemaakt zodat deze tests deterministisch blijven
    en niet afhangen van de geïnstalleerde ruff-versie (de echte telling wordt
    afgedwongen door de gepinde CI-gate). De mock onderscheidt bewust de drie
    fasen — versie, selectie en de eigenlijke controle — omdat de gate die alle
    drie met dezelfde root en optieset uitvoert.
    """

    def _mock_run(
        self,
        monkeypatch,
        *,
        returncode,
        stdout,
        selectie=(_GESELECTEERD,),
        versie=b"ruff 0.15.17\n",
    ):
        aanroepen: list[list[str]] = []

        def run(cmd, *args, **kwargs):
            argv = list(cmd)
            aanroepen.append(argv)
            if "--version" in argv:
                return SimpleNamespace(returncode=0, stdout=versie, stderr=b"")
            if "--show-files" in argv:
                opsomming = "".join(f"{pad}\n" for pad in selectie).encode()
                return SimpleNamespace(returncode=0, stdout=opsomming, stderr=b"")
            return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=b"")

        monkeypatch.setattr(cr.subprocess, "run", run)
        return aanroepen

    def test_every_phase_runs_isolated(self, monkeypatch):
        # `-I` houdt PYTHONPATH en de werkmap uit sys.path van de child, zodat
        # een `ruff`-pakket naast de code de echte tool niet kan overschaduwen.
        aanroepen = self._mock_run(monkeypatch, returncode=0, stdout=b"[]")
        cr.count_violations()

        assert aanroepen, "er moet werkelijk een tool zijn aangeroepen"
        for argv in aanroepen:
            assert argv[:5] == [sys.executable, "-I", "-B", "-m", "ruff"], argv
        assert any("--version" in argv for argv in aanroepen), aanroepen
        assert any("--show-files" in argv for argv in aanroepen), aanroepen

    def test_parses_counts_per_code(self, monkeypatch):
        payload = json.dumps(
            [_bevinding("C901"), _bevinding("C901"), _bevinding("PLR0912")]
        ).encode()
        self._mock_run(monkeypatch, returncode=1, stdout=payload)
        total, per_code = cr.count_violations()
        assert total == 3
        assert per_code["C901"] == 2
        assert per_code["PLR0912"] == 1

    def test_no_violations_returns_zero(self, monkeypatch):
        self._mock_run(monkeypatch, returncode=0, stdout=b"[]")
        assert cr.count_violations() == (0, Counter())

    def test_ruff_failure_exits(self, monkeypatch):
        self._mock_run(monkeypatch, returncode=2, stdout=b"")
        with pytest.raises(SystemExit):
            cr.count_violations()

    def test_signal_death_exits(self, monkeypatch):
        # Een door een signaal afgebroken ruff meldt een negatieve status; die
        # mag nooit als "nul bevindingen" doorgaan.
        self._mock_run(monkeypatch, returncode=-9, stdout=b"[]")
        with pytest.raises(SystemExit):
            cr.count_violations()

    def test_invalid_json_exits(self, monkeypatch):
        self._mock_run(monkeypatch, returncode=1, stdout=b"not json at all")
        with pytest.raises(SystemExit):
            cr.count_violations()

    def test_empty_selection_exits(self, monkeypatch):
        self._mock_run(monkeypatch, returncode=0, stdout=b"[]", selectie=())
        with pytest.raises(SystemExit):
            cr.count_violations()

    def test_invalid_version_line_exits(self, monkeypatch):
        self._mock_run(monkeypatch, returncode=0, stdout=b"[]", versie=b"niet-ruff\n")
        with pytest.raises(SystemExit):
            cr.count_violations()

    @pytest.mark.parametrize(
        ("returncode", "stdout"),
        [
            (0, json.dumps([_bevinding("C901")]).encode()),
            (1, b"[]"),
        ],
    )
    def test_status_and_results_must_agree(self, monkeypatch, returncode, stdout):
        self._mock_run(monkeypatch, returncode=returncode, stdout=stdout)
        with pytest.raises(SystemExit):
            cr.count_violations()

    @pytest.mark.parametrize(
        "record",
        [
            {"filename": _GESELECTEERD},
            {"code": "E501", "filename": _GESELECTEERD},
            {"code": "C901"},
            {"code": "C901", "filename": "src/bestaat_niet.py"},
            "geen dict",
        ],
    )
    def test_invalid_result_records_exit(self, monkeypatch, record):
        self._mock_run(monkeypatch, returncode=1, stdout=json.dumps([record]).encode())
        with pytest.raises(SystemExit):
            cr.count_violations()

    def test_non_list_report_exits(self, monkeypatch):
        self._mock_run(monkeypatch, returncode=1, stdout=b'{"results": []}')
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
