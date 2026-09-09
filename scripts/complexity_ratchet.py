#!/usr/bin/env python3
"""Complexity ratchet for DefinitieAgent (DEF-418, hardened in DEF-665).

`ruff check src/` passes because PLR0911/0912/0915 sit in the global ignore and
C901 is not selected — so CI is blind to complexity debt. Rather than masking it
with ~200 inline ``# noqa`` comments, this script counts the complexity
violations and compares the total against a committed baseline.

- Fails (exit 1) when the count GROWS above the baseline -> "freeze the growth".
- Passes when the count stays equal.
- When the count SHRINKS, it prints how far it dropped and (with ``--update``)
  rewrites the baseline so the ceiling can only ratchet downwards.

The codes counted bypass the project's global ``ignore`` (via an explicit CLI
``--select``) so the real debt is visible here even though ``make lint`` stays
green.

DEF-665 closes the blind spots that made a non-scan look clean: the root comes
from this file instead of the working directory, the same resolved root and the
same option set drive ``--version``, ``--show-files`` and the real check, the
selection must be a non-empty list of existing in-root ``src`` Python files, and
only raw Ruff statuses 0 and 1 are accepted — with the status and the reported
findings having to agree. Anything else (tool, config, I/O, decode, JSON or
schema failure, or a killed process) is a public exit 2, never a silent pass.
The log carries metadata only: the Ruff version, the root and the counts.

Usage:
    python scripts/complexity_ratchet.py            # check (CI gate)
    python scripts/complexity_ratchet.py --update   # ratchet the baseline down
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import NoReturn

# Complexity rules deliberately tracked here (globally ignored in pyproject).
COMPLEXITY_CODES = ("C901", "PLR0911", "PLR0912", "PLR0915")
TARGET = "src/"

#: De root komt uit dit bestand, niet uit de werkmap.
ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = Path(__file__).with_name("complexity_baseline.txt")

EXIT_OK = 0
EXIT_BLOCK = 1
EXIT_INVALID = 2

#: Elke fase draait met dezelfde geïsoleerde prefix. `-I` negeert PYTHONPATH en
#: houdt zowel de werkmap als de scriptmap uit `sys.path`, zodat een `ruff`-
#: pakket naast de code de echte tool niet kan overschaduwen; `-B` laat geen
#: bytecode achter. Zonder deze isolatie zou `-m ruff` een nagemaakte module
#: kunnen laden en een lege, groene meting opleveren.
_RUFF_PREFIX = (sys.executable, "-I", "-B", "-m", "ruff")

_VERSIE_PATROON = re.compile(r"^ruff (\d+\.\d+(?:\.\d+)?)")
_GEHEEL_GETAL = re.compile(r"\A\d+\Z")
_TIMEOUT = 300


def _log(bericht: str) -> None:
    print(f"complexity-gate: {bericht}", flush=True)


def _ongeldig(reden: str) -> NoReturn:
    """Publieke, veilige uitkomst: een vaste reden en exit 2, nooit een payload."""
    _log(f"invalid reason={reden}")
    raise SystemExit(EXIT_INVALID)


def _run(argv: list[str], reden: str) -> subprocess.CompletedProcess:
    """Vaste, begrensde aanroep vanuit de root; uitvoer blijft bytes."""
    try:
        return subprocess.run(
            argv,
            cwd=str(ROOT),
            capture_output=True,
            timeout=_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        _ongeldig(reden)


def _decode(rauw: bytes, reden: str) -> str:
    try:
        return rauw.decode("utf-8")
    except UnicodeDecodeError:
        _ongeldig(reden)


def _ruff_argv(*extra: str) -> list[str]:
    """Dezelfde scope en dezelfde regelset voor elke fase van de meting."""
    return [
        *_RUFF_PREFIX,
        "check",
        TARGET,
        "--select",
        ",".join(COMPLEXITY_CODES),
        *extra,
    ]


def _ruff_versie() -> str:
    """Alleen een echte Ruff-versieregel telt als bewijs van de tool."""
    klaar = _run([*_RUFF_PREFIX, "--version"], "ruff_version_failed")
    if klaar.returncode != 0:
        _ongeldig("ruff_version_failed")
    regels = _decode(klaar.stdout, "ruff_version_decode").splitlines()
    treffer = _VERSIE_PATROON.match(regels[0].strip()) if regels else None
    if treffer is None:
        _ongeldig("ruff_version_invalid")
    return treffer.group(1)


def _binnen_root(pad: str) -> str:
    """Normaliseer naar een root-relatief pad; leeg als het er niet in ligt."""
    kandidaat = Path(pad)
    if not kandidaat.is_absolute():
        kandidaat = ROOT / kandidaat
    try:
        echt = kandidaat.resolve(strict=True)
        return echt.relative_to(ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        return ""


def _geselecteerde_bestanden() -> list[str]:
    """Bewijs de scope: een werkelijke, niet-lege selectie binnen `src/`."""
    klaar = _run(_ruff_argv("--show-files"), "ruff_files_failed")
    if klaar.returncode not in (0, 1):
        _ongeldig("ruff_files_status")

    regels = [
        regel.strip()
        for regel in _decode(klaar.stdout, "ruff_files_decode").splitlines()
        if regel.strip()
    ]
    if not regels:
        _ongeldig("empty_selection")

    paden: list[str] = []
    for regel in regels:
        relatief = _binnen_root(regel)
        if not relatief:
            _ongeldig("selection_escape")
        if not relatief.startswith("src/") or not relatief.endswith(".py"):
            _ongeldig("selection_path")
        if not (ROOT / relatief).is_file():
            _ongeldig("selection_missing")
        paden.append(relatief)

    if len(set(paden)) != len(paden):
        _ongeldig("selection_duplicate")
    return sorted(paden)


def count_violations() -> tuple[int, Counter[str]]:
    """Run ruff and return (total, per-code counts) for the complexity codes."""
    if not (ROOT / "src").is_dir():
        _ongeldig("layout")

    _log(f"ruff={_ruff_versie()}")
    bestanden = _geselecteerde_bestanden()
    _log(f"selected files={len(bestanden)}")

    klaar = _run(_ruff_argv("--output-format=json"), "ruff_check_failed")
    # ruff exit codes: 0 = no violations, 1 = violations found (expected here),
    # anything else — including a negative status from a signal — means ruff
    # itself failed and the measurement is worthless.
    if klaar.returncode not in (0, 1):
        _ongeldig("ruff_check_status")

    try:
        rapport = json.loads(_decode(klaar.stdout, "ruff_check_decode"))
    except ValueError:
        _ongeldig("ruff_json_invalid")
    if not isinstance(rapport, list):
        _ongeldig("ruff_json_schema")

    toegestaan = set(bestanden)
    per_code: Counter[str] = Counter()
    for post in rapport:
        if not isinstance(post, dict):
            _ongeldig("ruff_json_schema")
        code = post.get("code")
        bestand = post.get("filename")
        if code not in COMPLEXITY_CODES or not isinstance(bestand, str):
            _ongeldig("ruff_json_schema")
        if _binnen_root(bestand) not in toegestaan:
            _ongeldig("ruff_json_path")
        per_code[code] += 1

    if (klaar.returncode == 0) != (len(rapport) == 0):
        _ongeldig("ruff_status_mismatch")
    return len(rapport), per_code


def read_baseline(path: Path = BASELINE_PATH) -> int:
    """Read the committed baseline count."""
    try:
        rauw = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        _ongeldig("baseline_unreadable")
    if not _GEHEEL_GETAL.match(rauw):
        _ongeldig("baseline_invalid")
    return int(rauw)


def write_baseline(value: int, path: Path = BASELINE_PATH) -> None:
    """Persist a new baseline count."""
    try:
        path.write_text(f"{value}\n", encoding="utf-8")
    except OSError:
        _ongeldig("baseline_unwritable")


def _format_breakdown(per_code: Counter[str]) -> str:
    return ", ".join(f"{code}={per_code.get(code, 0)}" for code in COMPLEXITY_CODES)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip().splitlines()[0]
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Lower the baseline to the current count (ratchet down).",
    )
    args = parser.parse_args(argv)

    _log(f"root={ROOT}")
    current, per_code = count_violations()
    baseline = read_baseline()
    _log(f"findings={current}")
    _log(f"baseline={baseline}")
    breakdown = _format_breakdown(per_code)

    if current > baseline:
        print(
            f"FAIL: complexity violations grew {baseline} -> {current} "
            f"(+{current - baseline}). [{breakdown}]\n"
            "New complex code was added. Refactor it, or — only if truly "
            "unavoidable — raise the baseline deliberately in "
            f"{BASELINE_PATH.name} with a justification."
        )
        return EXIT_BLOCK

    if current < baseline:
        message = (
            f"Complexity dropped {baseline} -> {current} (-{baseline - current}). "
            f"[{breakdown}]"
        )
        if args.update:
            write_baseline(current)
            print(f"{message}\nBaseline ratcheted down to {current}.")
        else:
            print(
                f"{message}\nRun 'python scripts/complexity_ratchet.py --update' "
                "to lock in the improvement."
            )
        return EXIT_OK

    print(f"OK: complexity at baseline ({current}). [{breakdown}]")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
