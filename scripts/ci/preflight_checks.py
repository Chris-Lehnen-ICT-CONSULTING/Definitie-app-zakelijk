#!/usr/bin/env python3
"""preflight_checks.py — repositorygebonden preflight (DEF-737).

Vervangt de inline shell-preflight in `quality-gates.yml`, die alleen draaide
als er toevallig een persoonlijk script in de homedir stond en anders terugviel
op drie losse `rg -q`-regels. Deze CLI staat volledig in de repository: dezelfde
controles, maar met een expliciete scope, een expliciet oordeel en een exitcode
die het verschil maakt tussen "schoon", "blokkerend" en "niet gemeten".

    python scripts/ci/preflight_checks.py [projectpad]      # standaard: cwd

Alleen lezen. Geen app-imports, geen providers, geen database, geen externe
configuratie of hooks, geen dependencies buiten de standaardbibliotheek; `rg` en
`git` zijn de enige externe tools.

Secrets vallen buiten deze gate: die worden beoordeeld door de verplichte
gitleaks-gate in `.github/workflows/security.yml` (DEF-522), die werkboom én
historie scant. Hier staat daarom geen eigen geheimscan meer.

Exit-codes:
    0  geldige scan, geaccepteerd (waarschuwingen mogen)
    1  geldige scan, blokkerende bevinding
    2  ongeldige scan (scope, tool, git of I/O) — nooit stil groen

De uitvoer draagt uitsluitend metadata: categorie, pad en telling. Broncode van
een treffer en rauwe tool-stderr komen er nooit in; deze log is publiek in CI.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PREFIX = "preflight:"
TIMEOUT = 120

#: De variabelen die de tools mogen zien. Alles daarbuiten blijft weg, zodat
#: externe configuratie het oordeel niet kan sturen: `RIPGREP_CONFIG_PATH` kan
#: paden uitsluiten en een lege scan als schoon laten doorgaan, en de
#: git-variabelen kunnen een driver of monitor aanwijzen. HOME staat er bewust
#: niet in en wordt ook niet gezet: de gate hoort niets uit een homedir te halen.
_DOOR_TE_GEVEN = ("PATH", "LANG", "LC_ALL", "TMPDIR")

#: `rg` leest van stdin zodra er geen pad meegegeven is. In een CI-stap is dat
#: een gesloten of lege stream, en dan meldt een scan nul treffers zonder ooit
#: een bestand te hebben gezien — een gate die groen is omdat hij niets deed.
#: Elke aanroep krijgt daarom een expliciet pad, en stdin gaat naar /dev/null.
#: Om dezelfde reden geen `-q`: die stopt bij de eerste treffer en verbergt een
#: leesfout verderop in de scope. `-l` leest de scope wel af en levert alleen
#: bestandsnamen, dus ook geen broncode op stdout.
_RG_BASIS = ("--files-with-matches", "--null")

#: Git zonder pager, externe diffdriver, textconv of filesystemmonitor: die
#: zouden een programma uit repo-eigen configuratie starten, en de meting hangt
#: niet van hun uitvoer af. Per commando meegegeven, niet uit globale config.
_GIT_DIFF = (
    "-c",
    "core.fsmonitor=false",
    "--no-pager",
    "diff",
    "--no-ext-diff",
    "--no-textconv",
)

# De patronen staan hier letterlijk zoals de oorspronkelijke gate ze had, met
# één ingreep: waar een patroon zichzelf in deze bron zou vinden, staat één
# teken tussen blokhaken — `voor[b]eeld` matcht dezelfde tekst als de vorm
# zonder haken, maar komt zelf niet als treffer terug. Zonder die ingreep zou de
# gate op zijn eigen definities aanslaan.
#
# Dat geldt ook voor deze toelichting: een patroon hier voluit spellen maakt de
# gate tot zijn eigen bevinding, die vervolgens in elke echte scan meetelt.
#
# Deze gate blokkeert alleen nog op laagoverschrijdende imports. De twee brede
# geheimpatronen zijn hier vervallen; secrets worden beoordeeld door de
# verplichte gitleaks-gate in `.github/workflows/security.yml` (DEF-522), die
# werkboom én historie scant. Dat is een taakverdeling, geen claim dat beide
# hetzelfde vinden.
BLOKKEREND = (
    ("services-streamlit", r"import streamlit", "src/services", False),
    ("services-ui-import", r"from ui\.", "src/services", False),
    ("services-asyncio-run", r"asyncio\.run\(", "src/services", False),
    ("ui-repository-import", r"from src\.repositories\.", "src/ui", False),
)

WAARSCHUWEND = (
    ("organizational-context", r"organi[z]ational_context|org[_]context"),
    ("legal-context", r"legal[_]context"),
    (
        "validation-orchestrator-v1",
        r"Validation[O]rchestratorV1|Validation[O]rchestrator[^V]",
    ),
    ("todo-marker", r"TO[D]O|FIX[M]E|XX[X]|HA[C]K"),
)

#: Scopes die moeten bestaan en niet leeg mogen zijn. Een gate die groen is
#: omdat de map waarin hij zoekt verdwenen is, meet niets.
SCOPES = ("src/services", "src/ui")

#: Duplicaatdrempel voor importregels in de kop van een module.
KOPREGELS = 20
DUPLICAATGRENS = 5

#: Drempels voor de omvangswaarschuwing. Deze meting adviseert alleen; ze
#: blokkeert niet en vraagt nooit om toestemming.
DIFF_BESTANDEN = 5
DIFF_REGELS = 100


class _OngeldigError(Exception):
    """Een scan die geen oordeel kan dragen; alleen de code wordt publiek."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _meld(regel: str) -> None:
    # Geen print(): één helper houdt het uitvoercontract op één plek.
    sys.stdout.write(f"{PREFIX} {regel}\n")


def _omgeving() -> dict[str, str]:
    """Kleine, voorspelbare omgeving voor de tools.

    Alleen wat ze nodig hebben om te draaien, plus de twee git-variabelen die de
    globale en systeemconfiguratie uitschakelen. HOME wordt niet doorgegeven en
    niet gezet.
    """
    omgeving = {
        sleutel: os.environ[sleutel]
        for sleutel in _DOOR_TE_GEVEN
        if sleutel in os.environ
    }
    omgeving.setdefault("PATH", os.defpath)
    omgeving["GIT_CONFIG_GLOBAL"] = os.devnull
    omgeving["GIT_CONFIG_SYSTEM"] = os.devnull
    return omgeving


def _voer_uit(programma: str, argumenten: list[str], root: Path, code: str):
    """Roep een tool read-only aan; elke opstartfout wordt een vaste code."""
    try:
        return subprocess.run(
            [programma, *argumenten],
            cwd=str(root),
            env=_omgeving(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as fout:
        raise _OngeldigError(code) from fout


def _rg(root: Path, argumenten: list[str]) -> list[str]:
    """Paden uit een rg-aanroep; 0 = treffers, 1 = geen, alles daarboven fout.

    Ook een waarschuwing-only patroon volgt deze regel: status 2 betekent dat de
    scope niet volledig gelezen is, en dan is er geen uitspraak te doen — ook
    geen geruststellende.
    """
    # `--no-config` hoort bij élke aanroep: een ripgreprc uit de omgeving kan
    # globs toevoegen die bestanden uitsluiten, en dan is een lege uitkomst geen
    # bewijs dat er niets te vinden was.
    voltooid = _voer_uit("rg", ["--no-config", *argumenten], root, "tool")
    if voltooid.returncode == 1:
        return []
    if voltooid.returncode != 0:
        raise _OngeldigError("tool")
    return [pad.strip("\n") for pad in voltooid.stdout.split("\0") if pad.strip("\n")]


def _zoek(root: Path, patroon: str, doel: str, alleen_python: bool) -> list[str]:
    argumenten = list(_RG_BASIS)
    if alleen_python:
        argumenten += ["--type", "py"]
    # `-e` voor het patroon en `--` voor het pad: zo kan geen van beide alsnog
    # als vlag gelezen worden.
    argumenten += ["-e", patroon, "--", doel]
    return _rg(root, argumenten)


def _bestanden(root: Path, doel: str, alleen_python: bool) -> list[str]:
    argumenten = ["--files"]
    if alleen_python:
        argumenten += ["--type", "py"]
    argumenten += ["--null", "--", doel]
    return _rg(root, argumenten)


def _eis_scope(root: Path, doel: str, alleen_python: bool = False) -> None:
    if not (root / doel).is_dir():
        raise _OngeldigError("scope-missing")
    if not _bestanden(root, doel, alleen_python):
        raise _OngeldigError("scope-empty")


def _dubbele_imports(root: Path) -> int:
    """Tel importregels die in meer dan vijf modulekoppen identiek terugkomen."""
    tellingen: dict[str, int] = {}
    for pad in sorted(root.glob("src/**/*.py")):
        try:
            tekst = pad.read_text(encoding="utf-8", errors="replace")
        except OSError as fout:
            raise _OngeldigError("scan-io") from fout
        for regel in tekst.splitlines()[:KOPREGELS]:
            # `^from`/`^import` zonder spatie, en de regel exact zoals hij staat:
            # dat is de grens die de bestaande controle had. Een smallere prefix
            # of een rstrip() zou andere regels tellen dan voorheen.
            if regel.startswith(("from", "import")):
                tellingen[regel] = tellingen.get(regel, 0) + 1
    return sum(1 for aantal in tellingen.values() if aantal > DUPLICAATGRENS)


def _git_uit(root: Path, argumenten: list[str]) -> str:
    voltooid = _voer_uit("git", argumenten, root, "git")
    if voltooid.returncode != 0:
        raise _OngeldigError("git")
    return voltooid.stdout


def _diff(root: Path) -> tuple[list[str], int, int]:
    """Gewijzigde bestanden, gewijzigde regels en nieuwe bestanden.

    De werkboom tegen de index, begrensd tot het projectpad — geen `HEAD`, net
    als de bestaande controle. Wat al gestaged is, staat dus niet meer in deze
    diff en verschuift het advies niet.

    Een lege uitvoer is een geldige meting van nul wijzigingen, geen scanfout;
    een onleesbaar record is dat wél, want dan klopt de telling niet.
    """
    bestanden: list[str] = []
    regels = 0
    for record in _git_uit(root, [*_GIT_DIFF, "--numstat", "--", "."]).splitlines():
        velden = record.split("\t")
        if len(velden) < 3:
            raise _OngeldigError("git")
        for waarde in velden[:2]:
            if waarde.isdigit():
                regels += int(waarde)
            elif waarde != "-":
                # `-` is de vaste notatie voor binaire bestanden; al het andere
                # betekent dat dit geen numstat-record is.
                raise _OngeldigError("git")
        bestanden.append(velden[2])

    nieuw = [
        pad
        for pad in _git_uit(
            root, [*_GIT_DIFF, "--name-only", "--diff-filter=A", "--", "."]
        ).splitlines()
        if pad
    ]
    return bestanden, regels, len(nieuw)


def _advies(bestanden: list[str], regels: int, nieuw: int) -> str:
    """Het werkwijze-advies; volgorde is load-bearing."""
    if len(bestanden) == 1 and bestanden[0].endswith(".md"):
        return "DOCUMENT"
    if regels < 50 and nieuw == 0:
        return "HOTFIX"
    if nieuw > 0 or len(bestanden) > 3:
        return "FULL_TDD"
    return "ANALYSIS"


def _preflight(root: Path) -> int:
    if not root.is_dir():
        raise _OngeldigError("scope-missing")
    _meld(f"root={root}")

    for doel in SCOPES:
        _eis_scope(root, doel)
    _eis_scope(root, ".", alleen_python=True)

    # Alle categorieën worden gemeten, ook nadat er één is aangeslagen. De
    # inline-fallback stopte bij zijn eerste treffer met `exit 1` en telde
    # niets; het globale script telde wel, maar brak onder `set -e` af op de
    # eerste `((counter++))` vanaf nul.
    blokkerend = 0
    for naam, patroon, doel, alleen_python in BLOKKEREND:
        treffers = _zoek(root, patroon, doel, alleen_python)
        if treffers:
            blokkerend += 1
            _meld(f"BLOCK {naam} files={len(treffers)}")
            for pad in treffers:
                _meld(f"  file={pad}")

    for naam, patroon in WAARSCHUWEND:
        treffers = _zoek(root, patroon, ".", True)
        if treffers:
            _meld(f"WARN {naam} files={len(treffers)}")

    dubbel = _dubbele_imports(root)
    if dubbel:
        _meld(f"WARN duplicate-import lines={dubbel}")

    bestanden, regels, nieuw = _diff(root)
    _meld(f"diff files={len(bestanden)} lines={regels} added={nieuw}")
    if len(bestanden) > DIFF_BESTANDEN or regels > DIFF_REGELS:
        _meld(f"WARN diff-size files={len(bestanden)} lines={regels}")
    _meld(f"workflow={_advies(bestanden, regels, nieuw)}")

    _meld(f"blocking={blokkerend}")
    return 1 if blokkerend else 0


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        sys.stderr.write(f"{PREFIX} error=arguments\n")
        return 2
    doel = Path(argv[0]) if argv else Path.cwd()
    try:
        return _preflight(doel.resolve())
    except _OngeldigError as fout:
        # Alleen de code: tool- en git-stderr kunnen paden en inhoud dragen die
        # niet in een publiek joblog thuishoren.
        sys.stderr.write(f"{PREFIX} error={fout.code}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
