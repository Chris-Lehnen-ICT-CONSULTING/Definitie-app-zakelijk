"""secret_scan.py — begrensde directoryscan voor de fail-closed secret-gate (DEF-522).

`scan_directory()` start de gepinde Gitleaks-binary op één expliciete directory
onder één expliciete TOML-config, en levert een compact resultaat: een vaste
status, een vaste diagnosecode en tellingen. Verder niets: Gitleaks-stdout,
-stderr, rapportinhoud en exceptietekst zijn onbetrouwbare invoer en blijven
binnen deze module.

Fail-closed betekent hier dat exit 0 nog géén succes is. Een schone scan vereist
ook een geldig, leeg JSON-rapport, een positief gescand byteaantal en de
volledige eindmelding "no leaks found" — zonder waarschuwing, skip-melding,
leesfout of partiële scan. Elk ander beeld (ontbrekende tool, onbruikbare scope,
inactieve config, timeout, onverwachte exitcode, onbruikbaar of tegenstrijdig
rapport) geeft een foutstatus met exitcode-equivalent 1. Ook een niet-decodeerbare
respons en een configroute waarvan de effectieve regelset niet te toetsen is
(`extend.disabledRules`, `extend.path`/`extend.url`) worden conservatief
geweigerd, en de publieke ingang is gesloten voor onverwachte excepties.

De vlaggenset en de eindmeldingen volgen de gepinde bron van Gitleaks 8.29.1
(broncommit fb5d707e08fe0d2578b155458fdd53b6782dcab2): `cmd/root.go` voor de
vlaggen en `findingSummaryAndExit`, `detect/files.go` voor de skip-meldingen.

`scan_git()` breidt dat uit naar een expliciete `base..head`-range plus de
bereikbare historie van de canonieke origin-branches/tags en de PR-head. Het
bereik wordt eerst bewezen met vaste, read-only en begrensde git-commando's
(repository, shallow, partial/promisor van elke remote, objecttype, aanwezigheid
van alle bereikbare objecten, niet-lege range en historie) voordat er iets wordt
gescand; beide deelscans tellen mee in één resultaat. Dat lokale refs de
*volledigheid* van de fetch niet bewijzen, blijft een caller-contract.

Deze module is geen CLI en geen generieke commandrunner: de vlaggenset ligt
vast, er komt geen vlag uit de omgeving of van de aanroeper bij, en ambient
`GITLEAKS_*`- en `GIT_*`-variabelen worden uit de child-omgeving verwijderd. De
gedeelde caller volgt apart binnen DEF-522.
"""

from __future__ import annotations

import contextlib
import json
import math
import os
import re
import subprocess
import tomllib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

#: Exitcode die onder `--exit-code=1` staat voor "leaks gevonden".
_EXIT_FINDINGS = 1

#: Ondergrens voor de wachttijd; `--timeout` van Gitleaks telt hele seconden.
_MIN_TIMEOUT_SECONDS = 1

#: Extra wachttijd bovenop de tooltimeout, zodat Gitleaks zijn eigen timeout kan
#: afronden voordat het proces hard wordt afgebroken.
_GRACE_SECONDS = 5.0

#: Ambient configuratie en overrides horen niet in de child-omgeving. Naast
#: `GITLEAKS_*` geldt dat voor `GIT_*` (`GIT_DIR`, `GIT_WORK_TREE`,
#: `GIT_CONFIG_*`, ...): die kunnen de scope of de config van de child verleggen.
_AMBIENT_PREFIXEN = ("GITLEAKS_", "GIT_")

#: Read-only git-hulptool voor scope-, object- en bereikbewijs.
_GIT = "git"

#: Volledig, ondubbelzinnig commit-ID; `\A..\Z` sluit een newline-staart uit.
_COMMIT_ID_PATROON = re.compile(r"\A[0-9a-f]{40}\Z")

#: Canonieke CI-invoer: origin-branches en tags. Lokale of stash-refs niet.
_CANONIEKE_REFS = ("refs/remotes/origin", "refs/tags")

#: Een annotated tag wijst naar een tag-object; alleen het gepeelde commit-ID
#: is een bruikbaar historie-anker.
_PEEL_ACHTERVOEGSEL = "^{commit}"

#: Partial/promisor-metadata van élke remote, plus de repository-extensie zelf.
#: Alleen `remote.origin.*` toetsen laat een tweede remote ongemoeid.
_PARTIAL_PATROON = (
    r"^(remote\..+\.(promisor|partialclonefilter)|extensions\.partialclone)$"
)

#: Vertrouwde waarden voor elke child (git.1): geen lazy fetch van ontbrekende
#: objecten, en geen replacement-refs die een object stil kunnen vervangen.
_VERTROUWDE_GIT_ENV = {
    "GIT_NO_LAZY_FETCH": "1",
    "GIT_NO_REPLACE_OBJECTS": "1",
}

#: Vaste log-opties voor beide deelscans; hier komt geen vrije optie bij.
_LOGOPTS = "--full-history -m"

#: Externe extend-routes (`extend.path`/`extend.url`, config.go:103-106) laden
#: een tweede configbestand dat deze validator niet volgt.
_EXTERNE_EXTEND_VELDEN = ("path", "url")

#: "scanned ~<N> bytes (...)" — het bewijs dat er werkelijk gelezen is.
_BYTES_PATROON = re.compile(r"scanned ~(\d+) bytes")

#: De volledige eindmelding; "no leaks found in partial scan" matcht bewust niet.
_EINDMELDING_PATROON = re.compile(r"\bno leaks found\s*$", re.MULTILINE)

#: Elk niet-informatief logniveau duidt op een onvolledige of gestoorde scan.
_WAARSCHUWING_PATROON = re.compile(r"\b(WRN|ERR|FTL)\b")


class ScanStatus(StrEnum):
    """Vaste uitkomststatus van een scan."""

    CLEAN = "clean"
    BLOCKED = "blocked"
    ERROR = "error"


class ScanErrorCode(StrEnum):
    """Vaste, statische diagnosecodes; nooit onbetrouwbare tooltekst.

    Een paar codes ontstaan bij de gedeelde caller in plaats van bij een scan
    (`invalid_arguments`, `head_mismatch`, `fetch_failed`); ze staan hier zodat
    de publieke uitvoer één woordenlijst houdt.
    """

    OK = "ok"
    FINDINGS_PRESENT = "findings_present"
    INVALID_ARGUMENTS = "invalid_arguments"
    TOOL_MISSING = "tool_missing"
    TOOL_FAILED = "tool_failed"
    TIMEOUT = "timeout"
    INVALID_TIMEOUT = "invalid_timeout"
    CONFIG_MISSING = "config_missing"
    CONFIG_INVALID = "config_invalid"
    CONFIG_INACTIVE = "config_inactive"
    SCOPE_MISSING = "scope_missing"
    SCOPE_EMPTY = "scope_empty"
    SCOPE_INCOMPLETE = "scope_incomplete"
    INVALID_COMMIT_ID = "invalid_commit_id"
    COMMIT_MISSING = "commit_missing"
    HEAD_MISMATCH = "head_mismatch"
    EMPTY_RANGE = "empty_range"
    HISTORY_MISSING = "history_missing"
    GIT_FAILED = "git_failed"
    FETCH_FAILED = "fetch_failed"
    UNEXPECTED_EXIT = "unexpected_exit"
    REPORT_INVALID = "report_invalid"
    REPORT_INCONSISTENT = "report_inconsistent"
    NO_SCAN_EVIDENCE = "no_scan_evidence"
    ZERO_BYTES = "zero_bytes"
    SCAN_INCOMPLETE = "scan_incomplete"
    RESPONSE_UNREADABLE = "response_unreadable"
    UNEXPECTED_FAILURE = "unexpected_failure"


@dataclass(frozen=True)
class ScanResult:
    """Compact resultaat: vaste status/code plus aantallen, geen tooltekst."""

    status: ScanStatus
    code: ScanErrorCode
    finding_count: int = 0
    scanned_bytes: int = 0

    @property
    def ok(self) -> bool:
        return self.status is ScanStatus.CLEAN

    @property
    def exit_code(self) -> int:
        return 0 if self.ok else 1


def _fout(code: ScanErrorCode) -> ScanResult:
    """Zichtbaar, veilig foutresultaat met uitsluitend een statische code."""
    return ScanResult(status=ScanStatus.ERROR, code=code)


def _als_tekst(waarde: bytes | str | None) -> str | None:
    """Decodeer procesuitvoer strikt; None betekent: onbruikbare response.

    Bewust geen `errors="replace"`: vervangingstekens zouden een verminkte
    respons kunnen laten doorgaan voor volledig bewijs. De inhoud zelf verlaat
    deze module niet.
    """
    if waarde is None:
        return ""
    if isinstance(waarde, bytes):
        try:
            return waarde.decode("utf-8")
        except UnicodeDecodeError:
            return None
    return str(waarde)


def _veilig_pad(waarde: Path | str) -> Path | None:
    """Resolveer een pad; None betekent: onbruikbaar pad, geen scanbereik.

    De aanroeper vertaalt None meteen in een zichtbare, specifieke foutcode —
    er wordt hier niets stil doorgeslikt.
    """
    try:
        return Path(waarde).resolve()
    except (OSError, TypeError, ValueError):
        return None


def _niet_lege_tekst(waarde: object) -> bool:
    return isinstance(waarde, str) and bool(waarde.strip())


def _geldige_timeout(timeout: float) -> bool:
    if isinstance(timeout, bool) or not isinstance(timeout, int | float):
        return False
    return math.isfinite(timeout) and timeout >= _MIN_TIMEOUT_SECONDS


def _tool_probleem(binary: Path) -> ScanErrorCode | None:
    if not binary.is_file() or not os.access(binary, os.X_OK):
        return ScanErrorCode.TOOL_MISSING
    return None


def _scope_probleem(source: Path) -> ScanErrorCode | None:
    """Alleen een bestaande, leesbare, niet-lege directory is scanbereik."""
    if not source.is_dir() or not os.access(source, os.R_OK | os.X_OK):
        return ScanErrorCode.SCOPE_MISSING
    try:
        leeg = next(source.iterdir(), None) is None
    except OSError:
        return ScanErrorCode.SCOPE_MISSING
    return ScanErrorCode.SCOPE_EMPTY if leeg else None


def _extend_velden(extend: object) -> dict[str, object]:
    """Gitleaks leest configsleutels hoofdletterongevoelig; wij dus ook."""
    if not isinstance(extend, dict):
        return {}
    return {str(sleutel).lower(): waarde for sleutel, waarde in extend.items()}


def _regels_probleem(document: dict) -> ScanErrorCode | None:
    """Toets dat de config werkelijk actieve regels aanzet."""
    velden = _extend_velden(document.get("extend"))
    if any(velden.get(veld) for veld in _EXTERNE_EXTEND_VELDEN):
        return ScanErrorCode.CONFIG_INVALID
    if velden.get("disabledrules"):
        return ScanErrorCode.CONFIG_INACTIVE
    gebruikt_default = velden.get("usedefault") is True

    regels = document.get("rules", [])
    if not isinstance(regels, list):
        return ScanErrorCode.CONFIG_INVALID
    for regel in regels:
        if not isinstance(regel, dict) or not _niet_lege_tekst(regel.get("id")):
            return ScanErrorCode.CONFIG_INVALID
        criteria = (regel.get("regex"), regel.get("path"))
        if not any(_niet_lege_tekst(waarde) for waarde in criteria):
            return ScanErrorCode.CONFIG_INVALID

    if not gebruikt_default and not regels:
        return ScanErrorCode.CONFIG_INACTIVE
    return None


def _config_probleem(config: Path) -> ScanErrorCode | None:
    """Expliciete, bestaande, leesbare TOML-config met actieve regels."""
    if not config.is_file():
        return ScanErrorCode.CONFIG_MISSING
    try:
        with config.open("rb") as bestand:
            document = tomllib.load(bestand)
    except OSError:
        return ScanErrorCode.CONFIG_MISSING
    except (tomllib.TOMLDecodeError, UnicodeDecodeError):
        return ScanErrorCode.CONFIG_INVALID
    return _regels_probleem(document)


def _vaste_vlaggen(config: Path, seconden: int) -> list[str]:
    """De vaste, geverifieerde vlaggenset — hier komt niets bij."""
    return [
        "--config",
        str(config),
        "--gitleaks-ignore-path",
        "/dev/null",
        "--ignore-gitleaks-allow",
        "--redact=100",
        "--no-banner",
        "--no-color",
        "--report-format=json",
        "--report-path=-",
        "--log-level=info",
        f"--timeout={seconden}",
        f"--exit-code={_EXIT_FINDINGS}",
    ]


def _argv(binary: Path, config: Path, seconden: int) -> list[str]:
    """Directoryscan op de werkdirectory; de scope is de expliciete cwd.

    Bewust `dir "."` en geen absoluut pad: Gitleaks rapporteert `File` relatief
    aan het meegegeven scanpad, dus met een absoluut pad worden dat absolute
    paden. De allowlists in de config zijn op repo-relatieve paden verankerd en
    matchen dan niet meer. De aanroeper bindt de gevalideerde scope als cwd.
    """
    return [str(binary), "dir", ".", *_vaste_vlaggen(config, seconden)]


def _git_argv(
    binary: Path, scope: Path, config: Path, logopts: str, seconden: int
) -> list[str]:
    """Git-scan op één expliciet bereik; geen platformmetadata, geen netwerk."""
    return [
        str(binary),
        "git",
        str(scope),
        f"--log-opts={logopts}",
        "--platform=none",
        *_vaste_vlaggen(config, seconden),
    ]


def _child_omgeving() -> dict[str, str]:
    """Ambient overrides eruit, daarna de vertrouwde waarden erin.

    Het filter alleen is niet genoeg: zonder expliciete `GIT_NO_*` kan de child
    alsnog ontbrekende objecten nafetchen of replacement-refs volgen. Geldt voor
    zowel de git-hulpcommando's als Gitleaks zelf.
    """
    schoon = {
        sleutel: waarde
        for sleutel, waarde in os.environ.items()
        if not sleutel.startswith(_AMBIENT_PREFIXEN)
    }
    return schoon | _VERTROUWDE_GIT_ENV


def _findings_aantal(stdout: str) -> int | None:
    """Aantal findings, of None als het rapport onbruikbaar is."""
    try:
        rapport = json.loads(stdout)
    except ValueError:
        return None
    if not isinstance(rapport, list):
        return None
    return len(rapport)


def _gescande_bytes(stderr: str) -> int | None:
    """Het gerapporteerde byteaantal, of None als dat bewijs ontbreekt."""
    treffers = _BYTES_PATROON.findall(stderr)
    if not treffers:
        return None
    return int(treffers[-1])


def _beoordeel_schone_scan(stdout: str, stderr: str) -> ScanResult:
    """Exit 0 telt pas als succes bij volledig en consistent bewijs."""
    aantal = _findings_aantal(stdout)
    if aantal is None:
        return _fout(ScanErrorCode.REPORT_INVALID)
    if aantal:
        return _fout(ScanErrorCode.REPORT_INCONSISTENT)
    if _WAARSCHUWING_PATROON.search(stderr):
        return _fout(ScanErrorCode.SCAN_INCOMPLETE)

    gescand = _gescande_bytes(stderr)
    if gescand is None:
        return _fout(ScanErrorCode.NO_SCAN_EVIDENCE)
    if gescand == 0:
        return _fout(ScanErrorCode.ZERO_BYTES)
    if not _EINDMELDING_PATROON.search(stderr):
        return _fout(ScanErrorCode.NO_SCAN_EVIDENCE)

    return ScanResult(
        status=ScanStatus.CLEAN,
        code=ScanErrorCode.OK,
        finding_count=0,
        scanned_bytes=gescand,
    )


def _beoordeel_findings(stdout: str, stderr: str) -> ScanResult:
    """Exit 1 blokkeert alleen met een rapport dat de findings ook toont."""
    aantal = _findings_aantal(stdout)
    if aantal is None:
        return _fout(ScanErrorCode.REPORT_INVALID)
    if aantal == 0:
        return _fout(ScanErrorCode.REPORT_INCONSISTENT)

    return ScanResult(
        status=ScanStatus.BLOCKED,
        code=ScanErrorCode.FINDINGS_PRESENT,
        finding_count=aantal,
        scanned_bytes=_gescande_bytes(stderr) or 0,
    )


def _voer_tool_uit(
    argv: list[str], seconden: int, cwd: Path | None = None
) -> ScanResult:
    """Start de gepinde tool en beoordeel de respons op volledig bewijs.

    `cwd` bindt de scanscope voor de directorymodus. De git-modus geeft haar
    bereik positioneel mee en laat `cwd` bewust ongezet.
    """
    try:
        voltooid = subprocess.run(
            argv,
            capture_output=True,
            check=False,
            shell=False,
            cwd=None if cwd is None else str(cwd),
            timeout=seconden + _GRACE_SECONDS,
            env=_child_omgeving(),
        )
    except subprocess.TimeoutExpired:
        return _fout(ScanErrorCode.TIMEOUT)
    except OSError:
        return _fout(ScanErrorCode.TOOL_FAILED)

    stdout = _als_tekst(voltooid.stdout)
    stderr = _als_tekst(voltooid.stderr)
    if stdout is None or stderr is None:
        return _fout(ScanErrorCode.RESPONSE_UNREADABLE)

    if voltooid.returncode == _EXIT_FINDINGS:
        return _beoordeel_findings(stdout, stderr)
    if voltooid.returncode != 0:
        return _fout(ScanErrorCode.UNEXPECTED_EXIT)

    return _beoordeel_schone_scan(stdout, stderr)


def _voer_scan_uit(
    binary: Path | str,
    source: Path | str,
    config: Path | str,
    timeout: float,
) -> ScanResult:
    """De eigenlijke scan: elke bekende faalmodus krijgt hier haar eigen code."""
    if not _geldige_timeout(timeout):
        return _fout(ScanErrorCode.INVALID_TIMEOUT)

    tool = _veilig_pad(binary)
    if tool is None:
        return _fout(ScanErrorCode.TOOL_MISSING)
    probleem = _tool_probleem(tool)
    if probleem is not None:
        return _fout(probleem)

    configpad = _veilig_pad(config)
    if configpad is None:
        return _fout(ScanErrorCode.CONFIG_MISSING)
    probleem = _config_probleem(configpad)
    if probleem is not None:
        return _fout(probleem)

    scope = _veilig_pad(source)
    if scope is None:
        return _fout(ScanErrorCode.SCOPE_MISSING)
    probleem = _scope_probleem(scope)
    if probleem is not None:
        return _fout(probleem)

    seconden = int(timeout)
    return _voer_tool_uit(_argv(tool, configpad, seconden), seconden, cwd=scope)


def scan_directory(
    binary: Path | str,
    source: Path | str,
    config: Path | str,
    timeout: float,
) -> ScanResult:
    """Scan `source` met de gepinde `binary` onder de expliciete `config`.

    Geeft altijd een `ScanResult` terug en werpt geen exceptie: alleen
    `ScanStatus.CLEAN` is succes, elke andere uitkomst is nonzero-equivalent.
    """
    # Fail-closed buitengrens. `_voer_scan_uit` dekt elke bekende faalmodus met
    # een eigen code; wat daarbuiten valt (een onverwachte fout in padresolutie,
    # procesopstart of parser) mag deze functie niet verlaten, want zulke
    # exceptietekst kan onbetrouwbare toolinhoud dragen. Het resultaat staat
    # daarom vooraf op de vaste, nonzero foutstatus en blijft dat als er iets
    # ontsnapt. Bewust een gedocumenteerde `contextlib.suppress` en geen stille
    # handler: de uitkomst is altijd een zichtbaar resultaat met statische code.
    resultaat = _fout(ScanErrorCode.UNEXPECTED_FAILURE)
    with contextlib.suppress(Exception):
        resultaat = _voer_scan_uit(binary, source, config, timeout)
    return resultaat


def _is_commit_id(waarde: object) -> bool:
    """Alleen een volledig hexadecimaal commit-ID is een geldige grens."""
    return isinstance(waarde, str) and _COMMIT_ID_PATROON.match(waarde) is not None


@dataclass(frozen=True)
class _GitBereik:
    """De twee expliciete deelbereiken: de PR-range en de canonieke historie."""

    range_opts: str
    historie_opts: str


def _git_run(args: list[str], scope: Path, seconden: int):
    """Vast, read-only en begrensd git-commando in de expliciete werkboom."""
    return subprocess.run(
        [_GIT, "--no-optional-locks", *args],
        capture_output=True,
        check=False,
        shell=False,
        cwd=str(scope),
        timeout=seconden + _GRACE_SECONDS,
        env=_child_omgeving(),
    )


def _git_uit(args: list[str], scope: Path, seconden: int) -> str | None:
    """Uitvoer van git; None bij nonzero exit of onbruikbare respons."""
    voltooid = _git_run(args, scope, seconden)
    if voltooid.returncode != 0:
        return None
    tekst = _als_tekst(voltooid.stdout)
    return None if tekst is None else tekst.strip()


def _git_regels(args: list[str], scope: Path, seconden: int) -> list[str] | None:
    tekst = _git_uit(args, scope, seconden)
    if tekst is None:
        return None
    return [regel.strip() for regel in tekst.splitlines() if regel.strip()]


def _historie_ankers(scope: Path, seconden: int) -> list[str] | ScanErrorCode:
    """Commit-ID's van de canonieke origin-branches en tags.

    Een annotated tag wijst naar een tag-object; die wordt naar zijn commit
    gepeeld in plaats van stil overgeslagen, want anders krimpt de dekking
    ongemerkt. Peelt een ref niet naar een commit, dan is dat een fout.
    """
    refs = _git_regels(
        ["for-each-ref", "--format=%(objectname)", *_CANONIEKE_REFS], scope, seconden
    )
    if refs is None:
        return ScanErrorCode.GIT_FAILED
    if not refs:
        return ScanErrorCode.HISTORY_MISSING

    ankers: list[str] = []
    for ref in refs:
        if not _is_commit_id(ref):
            return ScanErrorCode.GIT_FAILED
        gepeeld = _git_uit(
            ["rev-parse", "--verify", f"{ref}{_PEEL_ACHTERVOEGSEL}"], scope, seconden
        )
        if not _is_commit_id(gepeeld):
            return ScanErrorCode.GIT_FAILED
        ankers.append(str(gepeeld))
    return ankers


def _objecten_probleem(
    scope: Path, ankers: list[str], seconden: int
) -> ScanErrorCode | None:
    """Toets dat elk bereikbaar object er werkelijk is.

    `--missing=error` (git-rev-list.1) laat rev-list falen zodra een commit,
    tree of blob ontbreekt. Een leeg rapport bewijst evenmin volledigheid. De
    object-ID's hebben dezelfde 40-hex vorm als commit-ID's.
    """
    rapport = _git_regels(
        ["rev-list", "--objects", "--no-object-names", "--missing=error", *ankers],
        scope,
        seconden,
    )
    if not rapport:
        return ScanErrorCode.SCOPE_INCOMPLETE
    if not all(_is_commit_id(regel) for regel in rapport):
        return ScanErrorCode.GIT_FAILED
    return None


def _bepaal_bereik(
    scope: Path, base: str, head: str, seconden: int
) -> _GitBereik | ScanErrorCode:
    """Bewijs scope, commitobjecten en niet-leeg bereik vóór er iets scant.

    Shallow en partial worden vóór de objectinspectie afgevangen: in zo'n
    checkout zegt een aanwezig object niets over de bereikbare historie.
    """
    if _git_uit(["rev-parse", "--is-inside-work-tree"], scope, seconden) != "true":
        return ScanErrorCode.SCOPE_MISSING
    if _git_uit(["rev-parse", "--is-shallow-repository"], scope, seconden) != "false":
        return ScanErrorCode.SCOPE_INCOMPLETE
    # `git config --get-regexp` meldt uitsluitend met exit 1 dat er niets
    # gevonden is; elke andere nonzero exit is een toolfout en laat de
    # partial-clone-vraag onbeantwoord. Die als "geen partial clone" lezen zou
    # een onvolledige checkout doorlaten.
    partial = _git_run(["config", "--get-regexp", _PARTIAL_PATROON], scope, seconden)
    if partial.returncode == 0:
        return ScanErrorCode.SCOPE_INCOMPLETE
    if partial.returncode != 1:
        return ScanErrorCode.GIT_FAILED

    for commit in (base, head):
        if _git_uit(["cat-file", "-t", commit], scope, seconden) != "commit":
            return ScanErrorCode.COMMIT_MISSING

    ankers = _historie_ankers(scope, seconden)
    if isinstance(ankers, ScanErrorCode):
        return ankers

    bereik = f"{base}..{head}"
    commits = _git_regels(["rev-list", "--full-history", bereik], scope, seconden)
    if commits is None:
        return ScanErrorCode.GIT_FAILED
    if not commits:
        return ScanErrorCode.EMPTY_RANGE

    historie = list(dict.fromkeys([*ankers, head]))
    probleem = _objecten_probleem(scope, [*historie, base], seconden)
    if probleem is not None:
        return probleem

    return _GitBereik(f"{_LOGOPTS} {bereik}", f"{_LOGOPTS} {' '.join(historie)}")


def _samengevoegd(deelscans: list[ScanResult]) -> ScanResult:
    """Beide deelscans tellen mee; `finding_count` telt waarnemingen.

    Range en historie overlappen, dus hetzelfde secret kan tweemaal worden
    gezien. Het getal is geen unieke-incidenttelling.
    """
    findings = sum(deel.finding_count for deel in deelscans)
    gescand = sum(deel.scanned_bytes for deel in deelscans)
    geblokkeerd = any(deel.status is ScanStatus.BLOCKED for deel in deelscans)
    return ScanResult(
        status=ScanStatus.BLOCKED if geblokkeerd else ScanStatus.CLEAN,
        code=ScanErrorCode.FINDINGS_PRESENT if geblokkeerd else ScanErrorCode.OK,
        finding_count=findings,
        scanned_bytes=gescand,
    )


def _voer_git_scan_uit(
    binary: Path | str,
    source: Path | str,
    config: Path | str,
    base: str,
    head: str,
    timeout: float,
) -> ScanResult:
    """Elke bekende faalmodus krijgt hier haar eigen statische code."""
    if not _geldige_timeout(timeout):
        return _fout(ScanErrorCode.INVALID_TIMEOUT)

    tool = _veilig_pad(binary)
    if tool is None:
        return _fout(ScanErrorCode.TOOL_MISSING)
    probleem = _tool_probleem(tool)
    if probleem is not None:
        return _fout(probleem)

    configpad = _veilig_pad(config)
    if configpad is None:
        return _fout(ScanErrorCode.CONFIG_MISSING)
    probleem = _config_probleem(configpad)
    if probleem is not None:
        return _fout(probleem)

    if not _is_commit_id(base) or not _is_commit_id(head):
        return _fout(ScanErrorCode.INVALID_COMMIT_ID)

    scope = _veilig_pad(source)
    if scope is None or not scope.is_dir():
        return _fout(ScanErrorCode.SCOPE_MISSING)

    seconden = int(timeout)
    try:
        bereik = _bepaal_bereik(scope, base, head, seconden)
    except subprocess.TimeoutExpired:
        return _fout(ScanErrorCode.TIMEOUT)
    except OSError:
        return _fout(ScanErrorCode.GIT_FAILED)
    if isinstance(bereik, ScanErrorCode):
        return _fout(bereik)

    deelscans: list[ScanResult] = []
    for logopts in (bereik.range_opts, bereik.historie_opts):
        uitkomst = _voer_tool_uit(
            _git_argv(tool, scope, configpad, logopts, seconden), seconden
        )
        if uitkomst.status is ScanStatus.ERROR:
            return uitkomst
        deelscans.append(uitkomst)
    return _samengevoegd(deelscans)


def scan_git(
    binary: Path | str,
    source: Path | str,
    config: Path | str,
    base: str,
    head: str,
    timeout: float = 30,
) -> ScanResult:
    """Scan de expliciete `base..head`-range én de canonieke historie.

    `base` en `head` zijn volledige commit-ID's — geen refs, geen vlaggen. De
    historie loopt over de origin-branches en tags plus de PR-head, met vaste
    log-opties (`--full-history -m`) en geverifieerde hex-ID's.

    Geeft altijd een `ScanResult` en werpt geen exceptie; alleen
    `ScanStatus.CLEAN` is succes. Wat de aanroeper hier *niet* van krijgt, is
    het bewijs dat de canonieke refs volledig zijn opgehaald: lokale refs tonen
    dat niet. Die garantie hoort bij de caller (expliciete volledige fetch).
    """
    # Zelfde fail-closed buitengrens als `scan_directory`: wat buiten de
    # bekende faalmodi valt, mag deze functie niet verlaten, want zulke
    # exceptietekst kan onbetrouwbare tool- of Git-inhoud dragen.
    resultaat = _fout(ScanErrorCode.UNEXPECTED_FAILURE)
    with contextlib.suppress(Exception):
        resultaat = _voer_git_scan_uit(binary, source, config, base, head, timeout)
    return resultaat
