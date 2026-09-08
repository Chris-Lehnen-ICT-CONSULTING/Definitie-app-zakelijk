#!/usr/bin/env python3
"""Fail-closed Semgrep-gate (DEF-665).

De inline stappen in `security.yml` lazen ontbrekende velden als leeg
(`data.get("results", [])`), controleerden `paths.scanned` niet en behandelden
niet-fatale scanfouten als ruis. Een rapport zonder `results`, zonder gescande
paden of met dertien parse-fouten kwam daardoor als schone scan door.

Deze gate is één gedeeld entrypoint voor Make en CI, met hetzelfde bereik en
dezelfde configuraties als voorheen: de hele repository, `p/owasp-top-ten` en
`p/python`. Wat verandert is de bewijslast:

1. de root komt uit dit bestand en moet werkelijke, niet-lege Python-bestanden
   onder `src/` bevatten voordat er iets draait;
2. het rapport komt uit stdout, in het geheugen — een achtergebleven
   `semgrep-results.json` telt nooit als vers bewijs;
3. alleen status 0 is geldig (er wordt bewust geen `--error` gebruikt, de gate
   beslist zelf), en de gemelde versie moet overeenkomen met `--version`;
4. `version`, `results`, `errors` en `paths.scanned` moeten aanwezig én van het
   juiste type zijn, met minstens één bestaand Python-bestand onder `src/`;
5. elke scanfout en elke overgeslagen regel maakt de meting ongeldig — ook een
   waarschuwing zoals PartialParsing.

Bevindingenbeleid blijft ongewijzigd: ERROR in `src/` blokkeert, ERROR daarbuiten
en WARNING/INFO/MEDIUM zijn adviserend. Een onbekende severity is geen stille
advisory maar een ongeldige meting.

Publiek contract:
    exit 0 = geldige scan, geaccepteerd
    exit 1 = geldige scan, ERROR-bevinding in src/
    exit 2 = ongeldige scan — nooit stil groen

De log draagt uitsluitend metadata: versie, root, tellingen en genormaliseerde
paden/regelnummers. Nooit meldingen, snippets, broncode, rauwe stderr of een
traceback. Alle dynamische waarden gaan door `json.dumps`, zodat een
bestandsnaam met stuurtekens geen logregels kan vervalsen.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parents[2]

EXIT_OK = 0
EXIT_BLOCK = 1
EXIT_INVALID = 2

CONFIGS = ("p/owasp-top-ten", "p/python")
DOEL = "."

#: ERROR in src/ blokkeert; de rest is adviserend. Een severity buiten deze set
#: is onbekend en maakt de meting ongeldig in plaats van stil advisory.
BLOKKEREND = "ERROR"
BEKENDE_SEVERITY = frozenset({"ERROR", "WARNING", "INFO", "MEDIUM"})

_VERSIE_PATROON = re.compile(r"^v?(\d+\.\d+(?:\.\d+)?)")
#: Foutmetadata mag alleen begrensde tokens dragen; vrije tekst uit de tool kan
#: van alles bevatten en hoort nooit in de log.
_TOKEN_PATROON = re.compile(r"\A[A-Za-z_][A-Za-z0-9_]{0,63}\Z")
_VERSIE_TIMEOUT = 60
_SCAN_TIMEOUT = 1800


class GateError(Exception):
    """Ongeldige scan; draagt uitsluitend een vaste, veilige reden."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _log(bericht: str) -> None:
    print(f"semgrep-gate: {bericht}", flush=True)


def _ongeldig(reden: str) -> NoReturn:
    raise GateError(reden)


def _child_env() -> dict[str, str]:
    """Geen geinjecteerde Python-omgeving die het entrypoint kan overschaduwen."""
    env = {
        sleutel: waarde
        for sleutel, waarde in os.environ.items()
        if sleutel not in ("PYTHONPATH", "PYTHONHOME")
    }
    env["LC_ALL"] = "C"
    return env


def _run(argv: list[str], timeout: int, reden: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            argv,
            cwd=str(ROOT),
            env=_child_env(),
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        _ongeldig(reden)


def _decode(rauw: bytes, reden: str) -> str:
    try:
        return rauw.decode("utf-8")
    except UnicodeDecodeError:
        _ongeldig(reden)


def _relatief(pad: str) -> str:
    """Lexicale normalisatie; leeg als het pad niet root-relatief kan zijn.

    Een pad met een NUL-byte of een andere onbruikbare vorm levert hier een lege
    string op in plaats van een exceptie.
    """
    try:
        schoon = pad.strip()
        while schoon.startswith("./"):
            schoon = schoon[2:]
        if not schoon or schoon.startswith(("/", "~")) or "\x00" in schoon:
            return ""
        delen = Path(schoon).parts
        if not delen or ".." in delen:
            return ""
        return Path(schoon).as_posix()
    except (OSError, ValueError):
        return ""


def _bestaat_in_root(relatief: str) -> bool:
    try:
        echt = (ROOT / relatief).resolve(strict=True)
        return echt.is_file() and ROOT.resolve() in echt.parents
    except (OSError, ValueError, RuntimeError):
        # Ontbrekend pad, symlinklus of een onbruikbare padvorm.
        return False


def _token(waarde: object) -> str | None:
    """Alleen een begrensd, alfanumeriek token; al het andere vervalt."""
    if isinstance(waarde, str) and _TOKEN_PATROON.match(waarde):
        return waarde
    return None


def _src_scope() -> int:
    """Een niet-lege lijst Python-bestanden onder src/, vóór elke uitvoering.

    Het gaat om de omvang van de bestandslijst, niet om de inhoud: een leeg
    `__init__.py` is een volwaardig bronbestand.
    """
    bronmap = ROOT / "src"
    if bronmap.is_symlink() or not bronmap.is_dir():
        _ongeldig("layout")
    aantal = 0
    try:
        for pad in sorted(bronmap.rglob("*.py")):
            if pad.is_file() and not pad.is_symlink():
                aantal += 1
    except (OSError, ValueError, RuntimeError):
        _ongeldig("scope_unreadable")
    if aantal == 0:
        _ongeldig("empty_scope")
    return aantal


def _semgrep_pad() -> str:
    pad = shutil.which("semgrep")
    if not pad:
        _ongeldig("semgrep_missing")
    return pad


def _semgrep_versie(semgrep: str) -> str:
    klaar = _run([semgrep, "--version"], _VERSIE_TIMEOUT, "version_failed")
    if klaar.returncode != 0:
        _ongeldig("version_failed")
    regels = [
        regel.strip()
        for regel in _decode(klaar.stdout, "version_decode").splitlines()
        if regel.strip()
    ]
    treffer = _VERSIE_PATROON.match(regels[0]) if regels else None
    if treffer is None:
        _ongeldig("version_invalid")
    return treffer.group(1)


def _scan(semgrep: str) -> dict:
    """Vaste argv; het rapport komt uit stdout, nooit uit een bestand."""
    argv = [semgrep, "scan"]
    for config in CONFIGS:
        argv += ["--config", config]
    argv += [
        "--metrics=off",
        "--json",
        "--strict",
        "--oss-only",
        "--disable-version-check",
        DOEL,
    ]

    klaar = _run(argv, _SCAN_TIMEOUT, "scan_failed")
    rapport = _lees_rapport(klaar.stdout)

    # Zonder `--error` is uitsluitend 0 een geldige afronding; elke andere
    # status, inclusief een negatieve van een signaal, maakt de meting waardeloos.
    # `--strict` laat de tool ook bij waarschuwingen nonzero eindigen, en juist
    # dan staan de locaties in het rapport: eerst veilig diagnosticeren, dan
    # blokkeren. Nonzero blijft altijd ongeldig.
    if klaar.returncode != 0:
        _diagnose(rapport)
        _ongeldig("scan_status")
    if rapport is None:
        _ongeldig("report_invalid")
    return rapport


def _lees_rapport(rauw: bytes) -> dict | None:
    """Parseer het JSON-rapport; None zodra het onbruikbaar is."""
    try:
        data = json.loads(rauw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _diagnose(rapport: dict | None) -> None:
    """Veilige, gestructureerde diagnose bij een gefaalde scan."""
    fouten = rapport.get("errors") if isinstance(rapport, dict) else None
    if not isinstance(fouten, list):
        _log("scan errors=unknown")
        return
    _log(f"scan errors={len(fouten)}")
    for post in fouten:
        _log(f"scan error {_veilige_fout(post)}")


def _valideer_vorm(rapport: dict) -> None:
    if not isinstance(rapport.get("version"), str):
        _ongeldig("report_schema")
    for sleutel in ("results", "errors"):
        if not isinstance(rapport.get(sleutel), list):
            _ongeldig("report_schema")
    paden = rapport.get("paths")
    if not isinstance(paden, dict) or not isinstance(paden.get("scanned"), list):
        _ongeldig("report_schema")
    # Aanwezig-maar-null is misvormd; alleen een volledig afwezig veld telt als
    # "niet geleverd".
    if "skipped_rules" in rapport:
        overgeslagen = rapport["skipped_rules"]
        if not isinstance(overgeslagen, list):
            _ongeldig("report_schema")
        if overgeslagen:
            _log(f"skipped rules={len(overgeslagen)}")
            _ongeldig("skipped_rules")


def _gescande_paden(rapport: dict) -> set[str]:
    rauw = rapport["paths"]["scanned"]
    gezien: set[str] = set()
    for post in rauw:
        if not isinstance(post, str):
            _ongeldig("scanned_schema")
        relatief = _relatief(post)
        if not relatief:
            _ongeldig("scanned_escape")
        if relatief in gezien:
            _ongeldig("scanned_duplicate")
        if not _bestaat_in_root(relatief):
            _ongeldig("scanned_missing")
        gezien.add(relatief)

    if not gezien:
        _ongeldig("scanned_empty")
    if not any(pad.startswith("src/") and pad.endswith(".py") for pad in gezien):
        _ongeldig("scanned_no_src")
    return gezien


def _veilige_fout(post: object) -> str:
    """Uitsluitend gestructureerde velden; nooit `message` of een snippet."""
    code = level = soort = None
    pad = ""
    regel = None
    if isinstance(post, dict):
        if isinstance(post.get("code"), int) and not isinstance(post["code"], bool):
            code = post["code"]
        level = _token(post.get("level"))
        rauw_soort = post.get("type")
        if isinstance(rauw_soort, list):
            rauw_soort = rauw_soort[0] if rauw_soort else None
        soort = _token(rauw_soort)
        if isinstance(post.get("path"), str):
            pad = _relatief(post["path"])
        start = post.get("start")
        if isinstance(start, dict) and isinstance(start.get("line"), int):
            if not isinstance(start["line"], bool) and start["line"] > 0:
                regel = start["line"]
    return (
        f"code={json.dumps(code)} level={json.dumps(level)} "
        f"type={json.dumps(soort)} path={json.dumps(pad or None)} "
        f"line={json.dumps(regel)}"
    )


def _lees_bevinding(post: object, gescand: set[str]) -> tuple[str, str, int, str]:
    if not isinstance(post, dict):
        _ongeldig("finding_schema")
    check_id = post.get("check_id")
    pad = post.get("path")
    start = post.get("start")
    extra = post.get("extra")
    if not isinstance(check_id, str) or not check_id:
        _ongeldig("finding_schema")
    if not isinstance(pad, str) or not isinstance(start, dict):
        _ongeldig("finding_schema")
    if not isinstance(extra, dict):
        _ongeldig("finding_schema")

    regel = start.get("line")
    if not isinstance(regel, int) or isinstance(regel, bool) or regel < 1:
        _ongeldig("finding_schema")

    relatief = _relatief(pad)
    if not relatief or relatief not in gescand:
        _ongeldig("finding_path")

    severity = extra.get("severity")
    if not isinstance(severity, str) or severity not in BEKENDE_SEVERITY:
        _ongeldig("finding_severity")
    return relatief, severity, regel, check_id


def _beoordeel(rapport: dict, gescand: set[str]) -> int:
    fouten = rapport["errors"]
    if fouten:
        _log(f"scan errors={len(fouten)}")
        for post in fouten:
            _log(f"scan error {_veilige_fout(post)}")
        _ongeldig("scan_errors")

    per_severity: dict[str, int] = {}
    blokkerend: list[tuple[str, int, str]] = []
    for post in rapport["results"]:
        pad, severity, regel, check_id = _lees_bevinding(post, gescand)
        per_severity[severity] = per_severity.get(severity, 0) + 1
        if severity == BLOKKEREND and pad.startswith("src/"):
            blokkerend.append((pad, regel, check_id))

    for severity in sorted(per_severity):
        _log(f"findings severity={severity} count={per_severity[severity]}")
    _log(f"blocking findings={len(blokkerend)}")
    for pad, regel, check_id in sorted(blokkerend):
        _log(
            f"blocking path={json.dumps(pad)} line={json.dumps(regel)} "
            f"rule={json.dumps(check_id)}"
        )
    return EXIT_BLOCK if blokkerend else EXIT_OK


def _draai() -> int:
    bronbestanden = _src_scope()
    _log(f"root={json.dumps(str(ROOT))}")
    _log(f"src files={bronbestanden}")

    semgrep = _semgrep_pad()
    versie = _semgrep_versie(semgrep)
    _log(f"semgrep={versie}")

    rapport = _scan(semgrep)
    _valideer_vorm(rapport)
    if rapport["version"] != versie:
        _ongeldig("version_mismatch")

    gescand = _gescande_paden(rapport)
    src_gescand = sum(
        1 for pad in gescand if pad.startswith("src/") and pad.endswith(".py")
    )
    _log(f"scanned total={len(gescand)} src={src_gescand}")
    return _beoordeel(rapport, gescand)


def main() -> int:
    try:
        return _draai()
    except GateError as fout:
        _log(f"invalid reason={fout.reason}")
        return EXIT_INVALID
    except Exception:
        # Buitengrens: wat hier ontsnapt kan tool- of broninhoud dragen, dus
        # alleen de vaste code naar buiten — nooit een traceback.
        _log("invalid reason=unexpected_failure")
        return EXIT_INVALID


if __name__ == "__main__":
    sys.exit(main())
