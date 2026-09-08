"""secret_scan_gate.py — gedeelde fail-closed CLI voor de secret-gate (DEF-522).

Eén ingang voor beide callers: de verplichte CI-gate (`--mode full`) en de
aanvullende lokale precommit-feedback (`--mode staged`). Publiek levert deze CLI
uitsluitend één JSON-regel met een vaste status, een statische diagnosecode en
tellingen. Gitleaks-stdout, -stderr, rapportinhoud, Git-uitvoer, exceptietekst en
argparse-meldingen met ingevoerde waarden verlaten deze module nooit.

`--mode full` valideert eerst alle invoer (binary, config, source, timeout, base,
head), stelt daarna vast dat `source` de root van een werkboom is die werkelijk
op `--head` staat, haalt vervolgens de canonieke origin-refs volledig op met een
vaste refspec — zonder prune, delete of terugval — en scant ten slotte zowel de
`base..head`-range met de canonieke historie (`scan_git()`) als de actuele boom
(`scan_directory()`). Beide deelscans zijn vereist; elke fout geeft nonzero.

`--mode staged` is aanvullende lokale feedback op de index: dezelfde validatie en
dezelfde controle dat `source` een werkboomroot is, maar geen fetch, geen
`base`/`head` en geen enkele uitspraak over de historie. Nul gescande bytes blijft
ook daar nonzero.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

sys.path.insert(0, str(Path(__file__).resolve().parent))

import secret_scan

#: De publieke velden; hier komt geen tool- of Git-tekst bij.
_STATUS = "status"
_CODE = "code"
_FINDINGS = "finding_count"
_BYTES = "scanned_bytes"

_MODE_FULL = "full"
_MODE_STAGED = "staged"

#: De canonieke remote en de volledige refspec ernaartoe. Geen `--prune`, geen
#: `--prune-tags`, geen smaller bereik als terugval. De tag-refspec staat bewust
#: zónder `+`: tags zijn gedeelde, lokale refs, dus een afwijkende canonieke tag
#: moet de fetch laten falen in plaats van de bestaande stil te overschrijven.
#: Remote-tracking refs zijn wél van de remote afgeleid en mogen bijwerken.
_REMOTE = "origin"
_FETCH_REFSPECS = (
    "+refs/heads/*:refs/remotes/origin/*",
    "refs/tags/*:refs/tags/*",
)

#: `--no-tags` schakelt alleen het automatisch volgen van tags uit, óók wanneer
#: `remote.origin.tagOpt` iets anders zegt; de refspec hierboven haalt ze op.
_FETCH_VLAGGEN = ("--no-tags", "--no-recurse-submodules")

#: Hele seconden, zonder teken, spatie of scheidingsteken.
_GEHEEL_PATROON = re.compile(r"\A[0-9]+\Z")


class _InvoerError(Exception):
    """Interne signalering van afgekeurde invoer; alleen de code wordt publiek."""

    def __init__(self, code: secret_scan.ScanErrorCode) -> None:
        super().__init__(code.value)
        self.code = code


class _StilleParser(argparse.ArgumentParser):
    """Argparse die nooit publiceert: elke fout wordt dezelfde vaste code.

    De standaardmeldingen citeren de ingevoerde waarde en schrijven naar stderr;
    beide overrides sluiten dat af, inclusief het pad via `exit()`.
    """

    def error(self, message: str) -> NoReturn:
        raise _InvoerError(secret_scan.ScanErrorCode.INVALID_ARGUMENTS)

    def exit(self, status: int = 0, message: str | None = None) -> NoReturn:
        raise _InvoerError(secret_scan.ScanErrorCode.INVALID_ARGUMENTS)


@dataclass(frozen=True)
class _Invoer:
    """De gevalideerde invoer die beide modi delen."""

    binary: Path
    config: Path
    source: Path
    seconden: int


def _antwoord(resultaat: secret_scan.ScanResult) -> str:
    """Serialiseer de uitkomst tot de vaste, publieke JSON-regel."""
    return json.dumps(
        {
            _STATUS: resultaat.status.value,
            _CODE: resultaat.code.value,
            _FINDINGS: resultaat.finding_count,
            _BYTES: resultaat.scanned_bytes,
        },
        sort_keys=True,
    )


def _fout_resultaat(code: secret_scan.ScanErrorCode) -> secret_scan.ScanResult:
    """Zichtbaar foutresultaat met uitsluitend een statische code."""
    return secret_scan.ScanResult(status=secret_scan.ScanStatus.ERROR, code=code)


def _parser() -> argparse.ArgumentParser:
    """De vaste vlaggenset; geen hulptekst, geen defaults uit de omgeving."""
    parser = _StilleParser(prog="secret-scan-gate", add_help=False)
    parser.add_argument("--mode", required=True, choices=(_MODE_FULL, _MODE_STAGED))
    parser.add_argument("--source", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--binary", required=True)
    parser.add_argument("--timeout", required=True)
    parser.add_argument("--base")
    parser.add_argument("--head")
    return parser


def _absoluut_pad(waarde: str, code: secret_scan.ScanErrorCode) -> Path:
    """Een expliciet, absoluut pad; relatieve invoer wordt afgekeurd."""
    if not Path(waarde).is_absolute():
        raise _InvoerError(secret_scan.ScanErrorCode.INVALID_ARGUMENTS)
    pad = secret_scan._veilig_pad(waarde)
    if pad is None:
        raise _InvoerError(code)
    return pad


def _seconden(waarde: str) -> int:
    """Hele seconden; alles anders is een ongeldige timeout."""
    if _GEHEEL_PATROON.match(waarde) is None:
        raise _InvoerError(secret_scan.ScanErrorCode.INVALID_TIMEOUT)
    seconden = int(waarde)
    if not secret_scan._geldige_timeout(seconden):
        raise _InvoerError(secret_scan.ScanErrorCode.INVALID_TIMEOUT)
    return seconden


def _commit_id(waarde: str | None) -> str:
    """Een volledig commit-ID; een ref of vlag is geen geldige grens."""
    if not secret_scan._is_commit_id(waarde):
        raise _InvoerError(secret_scan.ScanErrorCode.INVALID_COMMIT_ID)
    return str(waarde)


def _invoer(argumenten: argparse.Namespace) -> _Invoer:
    """Valideer de gedeelde invoer, vóór er iets wordt gemuteerd."""
    seconden = _seconden(argumenten.timeout)

    binary = _absoluut_pad(argumenten.binary, secret_scan.ScanErrorCode.TOOL_MISSING)
    probleem = secret_scan._tool_probleem(binary)
    if probleem is not None:
        raise _InvoerError(probleem)

    config = _absoluut_pad(argumenten.config, secret_scan.ScanErrorCode.CONFIG_MISSING)
    probleem = secret_scan._config_probleem(config)
    if probleem is not None:
        raise _InvoerError(probleem)

    source = _absoluut_pad(argumenten.source, secret_scan.ScanErrorCode.SCOPE_MISSING)
    if not source.is_dir():
        raise _InvoerError(secret_scan.ScanErrorCode.SCOPE_MISSING)

    return _Invoer(binary=binary, config=config, source=source, seconden=seconden)


def _git_tekst(args: list[str], invoer: _Invoer) -> str | None:
    """Read-only git-uitvoer; None bij nonzero exit, een toolfout wordt een code."""
    try:
        return secret_scan._git_uit(args, invoer.source, invoer.seconden)
    except (OSError, subprocess.TimeoutExpired) as fout:
        raise _InvoerError(secret_scan.ScanErrorCode.GIT_FAILED) from fout


def _controleer_werkboom(invoer: _Invoer) -> None:
    """De bron moet de root van een echte werkboom zijn; beide modi eisen dat."""
    toplevel = _git_tekst(["rev-parse", "--show-toplevel"], invoer)
    gevonden = None if toplevel is None else secret_scan._veilig_pad(toplevel)
    if gevonden is None or gevonden != invoer.source:
        raise _InvoerError(secret_scan.ScanErrorCode.SCOPE_MISSING)


def _controleer_head(invoer: _Invoer, head: str) -> None:
    """De werkboom moet werkelijk op de opgegeven head staan."""
    if _git_tekst(["rev-parse", "HEAD"], invoer) != head:
        raise _InvoerError(secret_scan.ScanErrorCode.HEAD_MISMATCH)


def _fetch(invoer: _Invoer) -> None:
    """Haal de canonieke origin-refs volledig op; begrensd en opgevangen."""
    argumenten = ["fetch", *_FETCH_VLAGGEN, _REMOTE, *_FETCH_REFSPECS]
    try:
        voltooid = secret_scan._git_run(argumenten, invoer.source, invoer.seconden)
    except (OSError, subprocess.TimeoutExpired) as fout:
        raise _InvoerError(secret_scan.ScanErrorCode.FETCH_FAILED) from fout
    if voltooid.returncode != 0:
        raise _InvoerError(secret_scan.ScanErrorCode.FETCH_FAILED)


def _scan(invoer: _Invoer, base: str, head: str) -> secret_scan.ScanResult:
    """Beide deelscans zijn vereist: de expliciete historie én de actuele boom."""
    deelscans = [
        secret_scan.scan_git(
            invoer.binary,
            invoer.source,
            invoer.config,
            base,
            head,
            invoer.seconden,
        ),
        secret_scan.scan_directory(
            invoer.binary, invoer.source, invoer.config, invoer.seconden
        ),
    ]
    for deel in deelscans:
        if deel.status is secret_scan.ScanStatus.ERROR:
            return deel
    return secret_scan._samengevoegd(deelscans)


def _full(invoer: _Invoer, argumenten: argparse.Namespace) -> secret_scan.ScanResult:
    """De verplichte gate: expliciete grenzen, volledige fetch, beide deelscans."""
    base = _commit_id(argumenten.base)
    head = _commit_id(argumenten.head)
    _controleer_head(invoer, head)
    _fetch(invoer)
    return _scan(invoer, base, head)


def _staged_argv(invoer: _Invoer) -> list[str]:
    """Scan uitsluitend de index; `--staged` kiest de diff van de staged wijzigingen.

    Geen `--log-opts` en dus geen historie: deze modus doet daar geen uitspraak
    over. `--platform=none` houdt de aanroep vrij van platformmetadata.
    """
    return [
        str(invoer.binary),
        "git",
        str(invoer.source),
        "--staged",
        "--platform=none",
        *secret_scan._vaste_vlaggen(invoer.config, invoer.seconden),
    ]


def _staged(invoer: _Invoer) -> secret_scan.ScanResult:
    """Aanvullende lokale feedback op de index; nul gescande bytes is geen succes."""
    return secret_scan._voer_tool_uit(_staged_argv(invoer), invoer.seconden)


def _gate(argv: list[str]) -> secret_scan.ScanResult:
    """Voer de gevraagde modus uit; elke afgekeurde stap wordt een vaste code."""
    argumenten = _parser().parse_args(argv)
    invoer = _invoer(argumenten)
    _controleer_werkboom(invoer)
    if argumenten.mode == _MODE_STAGED:
        return _staged(invoer)
    return _full(invoer, argumenten)


def main(argv: list[str]) -> int:
    """Publiceer precies één vaste JSON-regel en geef de bijbehorende exitcode."""
    try:
        resultaat = _gate(argv)
    except _InvoerError as fout:
        resultaat = _fout_resultaat(fout.code)
    except (SystemExit, Exception):
        # Fail-closed buitengrens: exceptietekst kan onbetrouwbare tool- of
        # Git-inhoud dragen en mag deze CLI niet verlaten. `SystemExit` hoort
        # erbij, anders zou een ontsnapte argparse-afbreking het proces zonder
        # JSON-regel beëindigen.
        resultaat = _fout_resultaat(secret_scan.ScanErrorCode.UNEXPECTED_FAILURE)
    # Geen `print()`: de JSON-regel is de enige publieke uitvoer van deze CLI.
    sys.stdout.write(f"{_antwoord(resultaat)}\n")
    return resultaat.exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
