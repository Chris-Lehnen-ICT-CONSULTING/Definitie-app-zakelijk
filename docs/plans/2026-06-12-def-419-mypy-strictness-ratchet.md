# DEF-419 — Mypy strictness ratchet (Fase 1) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: gebruik `executing-plans` (of `subagent-driven-development`) om dit plan taak-voor-taak uit te voeren.

**Goal:** Maak de verborgen mypy type-debt zichtbaar en *bevries de groei* met een count-baseline ratchet (Fase 1) — zonder de bestaande `src/services`-gate te breken en zonder 92 errors nu te hoeven fixen.

**Architecture:** Een sibling van de zojuist gemergede DEF-418 complexity-ratchet. Een klein script (`scripts/mypy_ratchet.py`) draait `mypy src/ --check-untyped-defs`, parseert het aantal errors uit de samenvattingsregel, en vergelijkt met een gecommit baseline-getal (`scripts/mypy_baseline.txt` = 92). Faalt bij groei; `--update` ratcheted omlaag. Een nieuwe CI-job in `quality-gates.yml` met **exact gepinde mypy** draait de gate. De pyproject-config (`check_untyped_defs`) blijft bewust ONgewijzigd zodat de bestaande `mypy src/services`-gate groen blijft.

**Tech Stack:** Python 3.13, mypy 1.18.2 (exact te pinnen in de gate), pytest, GitHub Actions.

---

## Achtergrond & geverifieerde feiten (2026-06-12)

| Meting | Resultaat |
|--------|-----------|
| `mypy src/` (default config) | 69 errors in 17 files |
| `mypy src/ --check-untyped-defs` | **92 errors in 29 files** (33% undercount) |
| `mypy src/services --ignore-missing-imports` (huidige CI-gate) | 0 errors (groen) |
| `mypy src/services --check-untyped-defs` | **6 errors in 4 files** ⚠️ |
| Functies zonder return-type | 521 · zonder arg-annotatie: 226 |
| mypy-pin | `mypy>=1.8.0` (floor, niet-deterministisch); lokaal 1.18.2 |

**Kernconstraint:** `check_untyped_defs = true` in `pyproject.toml` zetten (zoals de issue-tekst letterlijk vraagt) breekt de bestaande `mypy src/services`-gate (6 nieuwe errors). Daarom doet dit Fase 1-plan dat **niet** globaal; de ratchet-gate geeft de vlag expliciet mee aan zijn eigen mypy-aanroep (net zoals de complexity-ratchet `--select` expliciet meegeeft).

## Aanpak-keuze

### ✅ Gekozen: Option A — count-baseline ratchet (consistent met DEF-418)
- Klein script + baseline-getal (92). Faalt alleen bij groei → "bevries de groei" (Fase 1).
- Mini-diff, laag risico, hergebruikt het net-gemergede DEF-418-patroon.
- pyproject-config blijft ongemoeid → bestaande gates onaangetast.

### ⏸️ Uitgesteld: Option B — mypy-native per-module overrides (Fase 2)
- `disallow_untyped_defs = true` globaal + `[[tool.mypy.overrides]]` met `disallow_untyped_defs = false` per legacy-module.
- Sterker (dwingt nieuwe/schone modules volledig getypeerd), maar met **521 functies zonder return-type** beslaat de override-lijst vrijwel de hele codebase — grote, onderhoudsintensieve config. Hoort bij een gerichte typ-verbeter-epic, niet bij "bevries de groei".
- Vereist eerst het fixen van de 6 `src/services`-errors (zie boven).

### Determinisme
Net als bij DEF-418/DEF-430: de error-count is mypy-versie-gebonden. De gate pint mypy **exact** (1.18.2). Bij een mypy-bump: hertel de baseline in dezelfde wijziging. Borg met een comment in de workflow.

---

## Task 1: Baseline-meting bevriezen + branch

**Files:**
- (geen wijziging; alleen meten en vastleggen in commit-message van Task 3)

**Step 1:** Bevestig de baseline op de huidige `main`-staat:
Run: `.venv/bin/mypy src/ --check-untyped-defs 2>/dev/null | tail -1`
Expected: `Found 92 errors in 29 files (checked 371 source files)`

**Step 2:** Leg het getal vast als de te-committen baseline: **92**.

---

## Task 2: `scripts/mypy_ratchet.py` (TDD)

**Files:**
- Create: `scripts/mypy_ratchet.py`
- Create: `scripts/mypy_baseline.txt`
- Test: `tests/unit/test_mypy_ratchet.py`

**Step 1: Schrijf de falende tests** (`tests/unit/test_mypy_ratchet.py`), gemockt subprocess zodat ze deterministisch zijn (les uit DEF-418-review: geen echte mypy in de unit-suite):

```python
"""Unit tests for the mypy ratchet (DEF-419)."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts import mypy_ratchet as mr

pytestmark = [pytest.mark.unit]


class TestParseErrorCount:
    def _mock_run(self, monkeypatch, *, returncode, stdout):
        monkeypatch.setattr(
            mr.subprocess, "run",
            lambda *a, **k: SimpleNamespace(returncode=returncode, stdout=stdout, stderr=""),
        )

    def test_parses_found_n_errors(self, monkeypatch):
        self._mock_run(monkeypatch, returncode=1,
                       stdout="src/x.py:1: error: foo\nFound 92 errors in 29 files (checked 371 source files)\n")
        assert mr.count_errors() == 92

    def test_success_line_is_zero(self, monkeypatch):
        self._mock_run(monkeypatch, returncode=0, stdout="Success: no issues found in 371 source files\n")
        assert mr.count_errors() == 0

    def test_unparseable_output_exits(self, monkeypatch):
        self._mock_run(monkeypatch, returncode=2, stdout="internal error\n")
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

    def test_shrink_with_update(self, monkeypatch):
        self._stub(monkeypatch, 88, 92)
        written: list[int] = []
        monkeypatch.setattr(mr, "write_baseline", lambda v: written.append(v))
        assert mr.main(["--update"]) == 0
        assert written == [88]
```

**Step 2: Run om te bevestigen dat ze falen**
Run: `.venv/bin/python -m pytest tests/unit/test_mypy_ratchet.py -q`
Expected: collection error / ImportError (`scripts.mypy_ratchet` bestaat nog niet)

**Step 3: Schrijf `scripts/mypy_ratchet.py`** — mirror van `complexity_ratchet.py`, maar parseert de mypy-samenvattingsregel i.p.v. JSON:

```python
#!/usr/bin/env python3
"""Mypy error-count ratchet for DefinitieAgent (DEF-419).

Runs `mypy src/ --check-untyped-defs` and compares the error count against a
committed baseline. Fails on growth ("freeze the growth", Fase 1); --update
ratchets the baseline down. The flag is passed explicitly so the project-wide
pyproject config (and the existing src/services gate) stays untouched.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

MYPY_ARGS = ("src/", "--check-untyped-defs")
BASELINE_PATH = Path(__file__).with_name("mypy_baseline.txt")
_FOUND_RE = re.compile(r"Found (\d+) errors?")
_SUCCESS_RE = re.compile(r"Success: no issues found")


def count_errors() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "mypy", *MYPY_ARGS],
        capture_output=True, text=True, check=False,
    )
    out = result.stdout
    if _SUCCESS_RE.search(out):
        return 0
    match = _FOUND_RE.search(out)
    if not match:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(
            f"mypy_ratchet: could not parse mypy output (exit {result.returncode})"
        )
    return int(match.group(1))


def read_baseline(path: Path = BASELINE_PATH) -> int:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(
            f"mypy_ratchet: cannot read baseline at {path} ({exc}). "
            "Restore scripts/mypy_baseline.txt to a single integer."
        ) from exc


def write_baseline(value: int, path: Path = BASELINE_PATH) -> None:
    path.write_text(f"{value}\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    parser.add_argument("--update", action="store_true",
                        help="Lower the baseline to the current count (ratchet down).")
    args = parser.parse_args(argv)

    current = count_errors()
    baseline = read_baseline()

    if current > baseline:
        print(f"FAIL: mypy errors grew {baseline} -> {current} (+{current - baseline}). "
              "Add type annotations to the code you touched, or raise the baseline "
              "deliberately with a justification.")
        return 1
    if current < baseline:
        msg = f"mypy errors dropped {baseline} -> {current} (-{baseline - current})."
        if args.update:
            write_baseline(current)
            print(f"{msg}\nBaseline ratcheted down to {current}.")
        else:
            print(f"{msg}\nRun 'python scripts/mypy_ratchet.py --update' to lock it in.")
        return 0
    print(f"OK: mypy at baseline ({current}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4:** Maak het baseline-bestand:
Run: `printf '92\n' > scripts/mypy_baseline.txt`

**Step 5: Run de tests tot ze slagen**
Run: `.venv/bin/python -m pytest tests/unit/test_mypy_ratchet.py -q`
Expected: PASS (alle tests)

**Step 6: Verifieer de echte gate lokaal**
Run: `.venv/bin/python scripts/mypy_ratchet.py`
Expected: `OK: mypy at baseline (92).`

**Step 7: Lint**
Run: `.venv/bin/ruff check scripts/mypy_ratchet.py tests/unit/test_mypy_ratchet.py && .venv/bin/black --check scripts/mypy_ratchet.py tests/unit/test_mypy_ratchet.py`
Expected: All checks passed / unchanged

**Step 8: Commit**
```bash
git add scripts/mypy_ratchet.py scripts/mypy_baseline.txt tests/unit/test_mypy_ratchet.py
SKIP=validate-juridische-synoniemen git commit -m "feat(DEF-419): mypy error-count ratchet (baseline 92)"
```

---

## Task 3: Makefile-target

**Files:**
- Modify: `Makefile` (`.PHONY`-regel + nieuw target naast `complexity-check`)

**Step 1:** Voeg toe aan `.PHONY`: `mypy-check`. Voeg target toe:
```makefile
mypy-check:
	@echo "[mypy] Ratchet on src/ (DEF-419) — fails if type-errors grow above baseline"
	@$(PY) scripts/mypy_ratchet.py
```

**Step 2:** Run: `PY=.venv/bin/python make mypy-check` → Expected: `OK: mypy at baseline (92).`

**Step 3: Commit**
```bash
git add Makefile
SKIP=validate-juridische-synoniemen git commit -m "build(DEF-419): make mypy-check target"
```

---

## Task 4: CI-job in `quality-gates.yml`

**Files:**
- Modify: `.github/workflows/quality-gates.yml` (nieuwe job + wire in `quality-summary`)

**Step 1:** Voeg een job toe (naar analogie van `complexity-ratchet`), met **exact gepinde mypy**:
```yaml
  mypy-ratchet:
    name: Mypy Ratchet (DEF-419)
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v6
      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: '3.11'
      - name: Install dependencies (mypy pinned for a deterministic count)
        # Exact pin: the error count is tied to the mypy version. When mypy is
        # bumped, re-measure and update scripts/mypy_baseline.txt in the same
        # change. Install the project deps so imports resolve for type-checking.
        run: |
          pip install -r requirements.txt
          pip install mypy==1.18.2
      - name: Check mypy errors have not grown
        run: python scripts/mypy_ratchet.py
```

**Step 2:** Voeg `mypy-ratchet` toe aan `quality-summary.needs` en aan de fail-check (zoals `complexity-ratchet` daar al staat) + een echo-regel.

**Step 3:** YAML-syntax check:
Run: `.venv/bin/python -c "import yaml; yaml.safe_load(open('.github/workflows/quality-gates.yml')); print('YAML OK')"`
Expected: `YAML OK`

**Step 4: Commit**
```bash
git add .github/workflows/quality-gates.yml
SKIP=validate-juridische-synoniemen git commit -m "ci(DEF-419): mypy-ratchet gate in quality-gates"
```

> ⚠️ **Open punt voor CI-verificatie:** `count_errors()` resolvet imports; in CI moet `pip install -r requirements.txt` de import-resolutie dekken zodat het aantal (92) reproduceert. Mocht CI een ander aantal geven (ontbrekende dev-deps / `ignore_missing_imports` interactie), dan: ofwel ook `requirements-dev.txt` installeren, ofwel de baseline op het CI-gemeten getal zetten en lokaal met dezelfde set meten. Dit valideren in de PR-checks vóór merge.

---

## Task 5: Volledige verificatie + PR

**Step 1:** Volledige unit-gate ongebroken:
Run: `.venv/bin/python -m pytest -m unit -q -p no:cacheprovider` → Expected: exit 0, 0 failures

**Step 2:** `make lint` groen:
Run: `.venv/bin/ruff check src config && .venv/bin/black --check src config` → Expected: clean

**Step 3:** Push + PR + `/review-pr` + Linear → In Progress (conform het vaste protocol van deze sessie).

---

## Risico's & mitigaties

| Risico | Mitigatie |
|--------|-----------|
| CI mypy-count ≠ 92 (import-resolutie/versie) | mypy exact gepind; deps geïnstalleerd; baseline desnoods op CI-gemeten getal (valideren vóór merge) |
| Mypy-bump verschuift de count stil | Comment in workflow koppelt pin ↔ baseline; bij bump samen muteren |
| Verwarring met de bestaande `src/services`-gate | Bewust ongewijzigd; ratchet draait op heel `src/` met expliciete `--check-untyped-defs`-vlag, los van pyproject-config |
| Indruk dat 92 errors "opgelost" zijn | Het is *bevries de groei* (Fase 1); een prominente FAIL-melding + Linear-comment maken expliciet dat fixen Fase 2 is |

## Out of scope (Fase 2, apart issue/epic)
- `disallow_untyped_defs = true` globaal + per-module overrides (Option B).
- De 6 `src/services --check-untyped-defs`-errors fixen + `check_untyped_defs=true` globaal in pyproject.
- De 521 ontbrekende return-types daadwerkelijk annoteren.
