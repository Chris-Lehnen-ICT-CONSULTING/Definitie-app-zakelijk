"""Gedragstests voor de gedeelde fail-closed secret-gate-CLI (DEF-522).

Deze module toetst `secret_scan_gate.py` als échte CLI: elk geval start een apart
proces met `sys.executable`, tegen zelfgemaakte Git-repositories en de echte
gepinde Gitleaks-binary. Er wordt uitsluitend naar de publieke JSON-uitkomst
gekeken — status, statische code en tellingen. Procesuitvoer komt nooit in een
faalmelding terecht, en elke run toetst apart dat de gevoelige invoerwaarde niet
in stdout of stderr staat.

**Historie-modi (`full` en `new-branch`).** De fixture is een lokale
origin-repository met daaruit een gewone clone; er komt geen netwerk aan te pas.
Drie gevallen, die in beide modi hetzelfde moeten uitpakken en daarom over beide
zijn geparametriseerd — alleen de `--base` verschilt:

1. *Schoon* → `clean`, exitcode 0. Zou dit falen, dan blokkeert de gate elke
   schone PR.
2. *Alleen niet-gecommitte werkkopie-inhoud* → `blocked`. Deze canary staat in
   geen enkele commit; alleen de scan van de actuele boom kan hem zien. Ontbreekt
   die deelscan, dan blijft de uitkomst `clean`.
3. *Alleen op een origin-zijtak die ná de clone is ontstaan* → `blocked`. Dat
   object zit vóór de fetch nergens in de clone: niet in de werkkopie, niet onder
   `refs/remotes/origin/*`, niet in de bereikbare historie. Alleen een werkelijk
   uitgevoerde, volledige fetch haalt het binnen. Zonder die stap blijft de
   uitkomst `clean`; dit is dus het discriminerende bewijs voor de fetch.

**Staged-modus.** Aanvullende lokale feedback op de index, zonder historieclaim.
Schoon staged werk geeft `clean`, een staged canary `blocked`, en een lege index
is géén succes: nul gescande bytes bewijst niets en moet nonzero geven.

**Foutpaden.** Onbekende modus, ontbrekende `--base`, onbestaande binary,
niet-gehele timeout en een `--head` die niet de uitgecheckte HEAD is, geven alle
nonzero. Drie daarvan (modus, binarypad, timeout) krijgen een herkenbare marker
als invoerwaarde mee; die marker mag in geen enkele publieke uitvoerregel
terugkomen — ook niet in een argparse-foutmelding, die van nature juist de
ingevoerde waarde citeert. De twee andere gevallen draaien bewust op verder
geldige invoer, zodat alleen de ontbrekende grens respectievelijk de HEAD-eis de
uitkomst kan bepalen: bij `--head` ≠ HEAD bestaan beide commits en is de range
niet leeg.

**Omgevingscontract.** `DEF522_GITLEAKS_BINARY` en `DEF522_FIXTURE_ROOT` zijn
verplicht; ontbreken is een fout, geen skip, geen installatie, geen netwerk. De
helpers voor repository-opbouw, fixture-isolatie, child-omgeving en de
canary-waarde komen uit `test_secret_scan_canary`, zodat er één canary-vorm en
één isolatiebewijs bestaat. Elke test maakt een eigen verse subdirectory onder de
aangewezen root (`mkdtemp`, dus nooit een bestaande map overschrijven) en laat
die staan als bewijsmateriaal. Buiten die root muteert deze module niets: geen
`git -C`, geen globale configuratie, geen uitgezette hooks.

**Lezen van een rode uitkomst.** De fixturevoorwaarden worden per test eerst
read-only vastgesteld (staat de canary werkelijk alleen daar waar de test
beweert?) voordat er iets over de gate wordt beweerd. Faalt zo'n voorwaarde, dan
ligt de oorzaak in de fixture en is er over de gate nog niets bewezen. Alle
vergelijkingen met de canary-waarde worden vóór de assertie tot een boolean
gereduceerd, zodat die waarde nooit in een faalmelding van pytest belandt.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

pytestmark = [pytest.mark.acceptance]

sys.path.insert(0, str(Path(__file__).resolve().parent))

import secret_scan
import test_secret_scan_canary as canary_fixtures

#: Gedeelde helpers: één canary-vorm, één isolatiebewijs, één child-omgeving.
_git = canary_fixtures._git
_commit = canary_fixtures._commit
_bewijs_isolatie = canary_fixtures._bewijs_isolatie
_git_omgeving = canary_fixtures._git_omgeving
_verplicht_pad = canary_fixtures._verplicht_pad
_Omgeving = canary_fixtures._Omgeving

#: De CLI onder test; als echt proces gestart, nooit in-process geïmporteerd.
_CLI = Path(__file__).resolve().parent / "secret_scan_gate.py"

#: Ruime procesgrens: de CLI voert zelf een fetch en meerdere scans uit.
_CLI_TIMEOUT = 240

#: De `--timeout` die de CLI aan de tool doorgeeft; hele seconden.
_TOOL_TIMEOUT = "60"

#: Vaste publieke statuswaarden — dezelfde woordenlijst als `secret_scan`.
_CLEAN = secret_scan.ScanStatus.CLEAN.value
_BLOCKED = secret_scan.ScanStatus.BLOCKED.value

#: De publieke velden die een faalmelding mag tonen; verder niets.
_PUBLIEKE_VELDEN = ("status", "code", "finding_count", "scanned_bytes")

#: Herkenbare invoerwaarde voor de foutpaden. Geen sleutelvorm: het gaat hier om
#: het lekken van ingevoerde waarden, niet om detectie.
_MARKER = "def522-verboden-invoerwaarde"

#: Neutrale paden in de fixture; geen naam die door een allowlist wordt gedekt.
_CANARY_BESTAND = canary_fixtures._CANARY_BESTAND
_SCHOON_BESTAND = "src/module.py"
_SCHONE_INHOUD = 'WAARDE = "gewone tekst"\n'
_README = "# Gate\n\nGewone tekst, geen sleutels.\n"

#: De twee historie-modi (DEF-741). `full` houdt de expliciete `base..head`-range;
#: `new-branch` is de aparte modus voor een net aangemaakte branch, waar de push
#: géén bruikbare voorganger meldt en de volledige historie van head telt.
_FULL = "full"
_NEW_BRANCH = "new-branch"

#: De nulbase die GitHub bij een branchcreatie in `github.event.before` zet. In
#: `new-branch` is dit de enige toegestane `--base`; in `full` blijft het een
#: onbestaande commit en dus een weigering.
_NULBASE = "0" * 40

#: Statische code voor een leeg bereik; een rootcommit mag die nooit opleveren.
_EMPTY_RANGE = secret_scan.ScanErrorCode.EMPTY_RANGE.value

#: Beide modi voor de gedeelde gedragstests; dezelfde asserties, andere grenzen.
_HISTORIEMODI = (
    pytest.param(_FULL, id="full"),
    pytest.param(_NEW_BRANCH, id="new-branch"),
)


@dataclass(frozen=True)
class _Fixture:
    """Een lokale origin met een clone daarvan; alles onder de fixture-root."""

    origin: Path
    clone: Path
    config: Path
    base: str
    midden: str
    head: str


@dataclass(frozen=True)
class _Aanroep:
    """De drie expliciete, absolute paden waarmee de CLI wordt aangeroepen."""

    binary: Path
    source: Path
    config: Path


@dataclass(frozen=True)
class _Uitkomst:
    """Publieke uitkomst van één CLI-run; nooit de procesuitvoer zelf."""

    exit_code: int
    document: dict | None
    lekt: bool


def _canary() -> str:
    """De synthetische AWS-canary, samengesteld uit de gedeelde delen."""
    return "".join(canary_fixtures._CANARY_DELEN)


def _canary_regel(canary: str) -> str:
    """Bestandsinhoud met de canary op een gewone toewijzing."""
    return f'AWS_ACCESS_KEY_ID = "{canary}"\n'


def _diagnose(uitkomst: _Uitkomst) -> str:
    """Alleen exitcode en de vaste publieke velden — nooit stdout of stderr."""
    if uitkomst.document is None:
        return f"exit={uitkomst.exit_code} json=onbruikbaar"
    velden = " ".join(
        f"{naam}={uitkomst.document.get(naam)}" for naam in _PUBLIEKE_VELDEN
    )
    return f"exit={uitkomst.exit_code} {velden}"


def _draai(argumenten: list[str], *, verboden: str) -> _Uitkomst:
    """Start de CLI als echt proces en lees uitsluitend de publieke JSON.

    De controle op `verboden` gebeurt hier, zodat die waarde zelf nooit in een
    faalmelding van pytest terechtkomt: de aanroeper krijgt alleen een boolean.
    """
    voltooid = subprocess.run(
        [sys.executable, str(_CLI), *argumenten],
        capture_output=True,
        check=False,
        shell=False,
        text=True,
        timeout=_CLI_TIMEOUT,
        env=_git_omgeving(),
    )
    try:
        gelezen = json.loads(voltooid.stdout)
    except ValueError:
        gelezen = None
    document = gelezen if isinstance(gelezen, dict) else None
    return _Uitkomst(
        exit_code=voltooid.returncode,
        document=document,
        lekt=verboden in f"{voltooid.stdout}\n{voltooid.stderr}",
    )


def _basis_argumenten(
    aanroep: _Aanroep, mode: str, timeout: str = _TOOL_TIMEOUT
) -> list[str]:
    """De vaste vlaggenset van de CLI; uitsluitend expliciete absolute paden."""
    return [
        "--mode",
        mode,
        "--source",
        str(aanroep.source),
        "--config",
        str(aanroep.config),
        "--binary",
        str(aanroep.binary),
        "--timeout",
        timeout,
    ]


def _full_argumenten(
    aanroep: _Aanroep, base: str, head: str, timeout: str = _TOOL_TIMEOUT
) -> list[str]:
    """Full vereist expliciete, volledige commit-ID's als grenzen."""
    return [
        *_basis_argumenten(aanroep, "full", timeout),
        "--base",
        base,
        "--head",
        head,
    ]


def _historie_argumenten(aanroep: _Aanroep, opzet: _Fixture, modus: str) -> list[str]:
    """De grenzen per historie-modus; alleen de `--base` verschilt.

    `full` krijgt de expliciete voorganger uit de fixture, `new-branch` de
    nulbase van een branchcreatie. `--head` is in beide gevallen de werkelijk
    uitgecheckte commit, zodat de HEAD-eis in beide modi geldt.
    """
    base = opzet.base if modus == _FULL else _NULBASE
    return [*_basis_argumenten(aanroep, modus), "--base", base, "--head", opzet.head]


def _staged_argumenten(aanroep: _Aanroep) -> list[str]:
    """Staged kent geen grenzen: de index is het hele bereik."""
    return _basis_argumenten(aanroep, "staged")


def _nieuwe_basis(omgeving: _Omgeving, naam: str) -> tuple[Path, Path]:
    """Verse werkruimte onder de aangewezen root, met een actieve config."""
    basis = Path(tempfile.mkdtemp(prefix=f"{naam}-", dir=str(omgeving.fixture_root)))
    config = basis / canary_fixtures._CONFIG_NAAM
    config.write_text(canary_fixtures._CONFIG_TOML, encoding="utf-8")
    return basis, config


def _nieuwe_repo(basis: Path, naam: str) -> Path:
    """Lege repository in de werkruimte, direct op de fixture-branch."""
    repo = basis / naam
    repo.mkdir()
    _git(repo, "init", f"--initial-branch={canary_fixtures._BRANCH}")
    _bewijs_isolatie(repo)
    return repo


def _origin_met_clone(omgeving: _Omgeving, naam: str) -> _Fixture:
    """Lokale origin met drie schone commits, plus een verse clone daarvan.

    Drie commits, zodat een foutpad een `--head` kan aanwijzen die wél bestaat en
    wél een niet-lege range oplevert, maar niet de uitgecheckte HEAD is. Bewust
    `--no-hardlinks`: de clone krijgt dan een eigen objectdatabase, zodat een
    commit die ná de clone in de origin ontstaat er aantoonbaar niet in zit.
    """
    basis, config = _nieuwe_basis(omgeving, naam)
    origin = _nieuwe_repo(basis, "origin")
    base = _commit(origin, "README.md", _README, "chore: basis")
    midden = _commit(origin, _SCHOON_BESTAND, _SCHONE_INHOUD, "chore: module")
    head = _commit(origin, "NOTITIES.md", "# Notities\n", "chore: notities")

    _git(basis, "clone", "--no-hardlinks", "--", str(origin), "clone")
    clone = basis / "clone"
    _bewijs_isolatie(clone)
    return _Fixture(
        origin=origin,
        clone=clone,
        config=config,
        base=base,
        midden=midden,
        head=head,
    )


@pytest.fixture
def omgeving() -> _Omgeving:
    """De verplicht aangewezen binary en fixture-root; geen default, geen skip."""
    return _Omgeving(
        binary=_verplicht_pad(canary_fixtures._ENV_BINARY, uitvoerbaar=True),
        fixture_root=_verplicht_pad(canary_fixtures._ENV_FIXTURE_ROOT),
    )


@pytest.mark.parametrize("modus", _HISTORIEMODI)
def test_historiemodus_op_schone_clone_geeft_clean(
    omgeving: _Omgeving, modus: str
) -> None:
    """Een schone origin met clone blokkeert niet en toont aantoonbaar scanwerk."""
    opzet = _origin_met_clone(omgeving, f"schoon-{modus}")
    aanroep = _Aanroep(omgeving.binary, opzet.clone, opzet.config)
    argumenten = _historie_argumenten(aanroep, opzet, modus)

    uitkomst = _draai(argumenten, verboden=_canary())

    assert not uitkomst.lekt
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] == _CLEAN, _diagnose(uitkomst)
    assert uitkomst.document["finding_count"] == 0, _diagnose(uitkomst)
    # Positief byteaantal: zonder gelezen bytes is "geen findings" geen bewijs.
    assert uitkomst.document["scanned_bytes"] > 0, _diagnose(uitkomst)
    assert uitkomst.exit_code == 0, _diagnose(uitkomst)


@pytest.mark.parametrize("modus", _HISTORIEMODI)
def test_historiemodus_ziet_werkkopie_canary(omgeving: _Omgeving, modus: str) -> None:
    """Een canary die in geen enkele commit staat, komt alleen uit de boomscan."""
    opzet = _origin_met_clone(omgeving, f"werkkopie-{modus}")
    canary = _canary()
    doel = opzet.clone / _CANARY_BESTAND
    doel.parent.mkdir(parents=True, exist_ok=True)
    doel.write_text(_canary_regel(canary), encoding="utf-8")

    # Boolean vóór de assertie: een directe `in`-assertie zou de canary-waarde
    # in de faalmelding van pytest afdrukken.
    in_historie = canary in _git(opzet.clone, "log", "-p", "--all")
    assert not in_historie, (
        "fixturefout: de canary staat al in de historie van de clone, dus deze "
        "test zou ook slagen zonder een scan van de actuele werkboom."
    )

    aanroep = _Aanroep(omgeving.binary, opzet.clone, opzet.config)
    argumenten = _historie_argumenten(aanroep, opzet, modus)

    uitkomst = _draai(argumenten, verboden=canary)

    assert not uitkomst.lekt, "de canary-waarde staat in de publieke uitvoer."
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] == _BLOCKED, (
        f"{_diagnose(uitkomst)} — de canary staat in geen enkele commit, alleen "
        "in de actuele werkboom. Een uitblijvende blokkade betekent hier dat de "
        "boomscan niet meedoet in deze modus."
    )
    assert uitkomst.document["finding_count"] > 0, _diagnose(uitkomst)
    assert uitkomst.exit_code != 0, _diagnose(uitkomst)


@pytest.mark.parametrize("modus", _HISTORIEMODI)
def test_historiemodus_ziet_zijtak_canary_van_na_de_clone(
    omgeving: _Omgeving, modus: str
) -> None:
    """Alleen een werkelijk uitgevoerde volledige fetch haalt deze zijtak binnen."""
    opzet = _origin_met_clone(omgeving, f"zijtak-{modus}")
    canary = _canary()
    zijtak = f"{canary_fixtures._BRANCH}-zijtak"
    _git(opzet.origin, "checkout", "-b", zijtak, opzet.base)
    _commit(opzet.origin, _CANARY_BESTAND, _canary_regel(canary), "chore: zijtak")
    _git(opzet.origin, "checkout", canary_fixtures._BRANCH)

    # Booleans vóór de asserties: de canary-waarde mag nooit in een faalmelding
    # van pytest belanden.
    in_clone = canary in _git(opzet.clone, "log", "-p", "--all")
    in_werkkopie = (opzet.clone / _CANARY_BESTAND).exists()
    assert not in_clone, (
        "fixturefout: de zijtak is al in de clone bereikbaar, dus deze test "
        "bewijst niets over de fetchstap."
    )
    assert not in_werkkopie, (
        "fixturefout: de canary staat in de werkkopie van de clone, dus de "
        "boomscan zou hem sowieso vinden."
    )

    aanroep = _Aanroep(omgeving.binary, opzet.clone, opzet.config)
    argumenten = _historie_argumenten(aanroep, opzet, modus)

    uitkomst = _draai(argumenten, verboden=canary)

    assert not uitkomst.lekt, "de canary-waarde staat in de publieke uitvoer."
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] == _BLOCKED, (
        f"{_diagnose(uitkomst)} — de canary bestaat vóór de fetch nergens in de "
        "clone. Een uitblijvende blokkade betekent hier dat de volledige fetch "
        "van de canonieke origin-refs niet werkelijk wordt uitgevoerd."
    )
    assert uitkomst.document["finding_count"] > 0, _diagnose(uitkomst)
    assert uitkomst.exit_code != 0, _diagnose(uitkomst)


def _clone_op_nieuwe_tak(omgeving: _Omgeving, naam: str, canary: str) -> _Fixture:
    """Origin waarin een canary later uit de inhoud is gehaald, plus een tak die
    daarna op de al bestaande commit is aangemaakt; de clone staat op die tak.

    Dit is precies het geval dat DEF-741 raakt: bij het pushen van deze tak meldt
    GitHub geen voorganger, terwijl de canary in de historie vóór het aftakpunt
    zit — niet in de werkboom en niet in de commits van de tak zelf.
    """
    basis, config = _nieuwe_basis(omgeving, naam)
    origin = _nieuwe_repo(basis, "origin")
    base = _commit(origin, "README.md", _README, "chore: basis")
    _commit(origin, _CANARY_BESTAND, _canary_regel(canary), "chore: sleutel")
    midden = _commit(origin, _CANARY_BESTAND, _SCHONE_INHOUD, "chore: sleutel eruit")

    tak = f"{canary_fixtures._BRANCH}-nieuw"
    _git(origin, "checkout", "-b", tak, midden)
    head = _commit(origin, "NOTITIES.md", "# Notities\n", "chore: notities")
    _git(origin, "checkout", canary_fixtures._BRANCH)

    _git(basis, "clone", "--no-hardlinks", "--branch", tak, "--", str(origin), "clone")
    clone = basis / "clone"
    _bewijs_isolatie(clone)
    return _Fixture(
        origin=origin,
        clone=clone,
        config=config,
        base=base,
        midden=midden,
        head=head,
    )


def _clone_met_alleen_rootcommit(omgeving: _Omgeving, naam: str) -> _Fixture:
    """Origin met precies één commit; die rootcommit heeft geen ouder."""
    basis, config = _nieuwe_basis(omgeving, naam)
    origin = _nieuwe_repo(basis, "origin")
    root = _commit(origin, "README.md", _README, "chore: basis")

    _git(basis, "clone", "--no-hardlinks", "--", str(origin), "clone")
    clone = basis / "clone"
    _bewijs_isolatie(clone)
    return _Fixture(
        origin=origin,
        clone=clone,
        config=config,
        base=root,
        midden=root,
        head=root,
    )


def test_new_branch_ziet_canary_voor_het_aftakpunt(omgeving: _Omgeving) -> None:
    """De volledige historie van head telt, ook wat vóór het aftakpunt ligt."""
    canary = _canary()
    opzet = _clone_op_nieuwe_tak(omgeving, "nb-aftakpunt", canary)

    # Booleans vóór de asserties: de canary-waarde mag nooit in een faalmelding
    # van pytest belanden.
    # Het bestand bestáát nog in de werkboom; de verwijderingscommit heeft er
    # schone inhoud in gezet. De canary-waarde zelf moet eruit zijn.
    in_werkkopie = canary in (opzet.clone / _CANARY_BESTAND).read_text(encoding="utf-8")
    in_takcommits = canary in _git(opzet.clone, "log", "-p", f"{opzet.midden}..HEAD")
    in_historie = canary in _git(opzet.clone, "log", "-p", "HEAD")
    assert not in_werkkopie, (
        "fixturefout: de canary staat nog in de inhoud van de werkkopie, dus de "
        "boomscan zou hem sowieso vinden."
    )
    assert not in_takcommits, (
        "fixturefout: de canary zit in de commits van de tak zelf, dus deze test "
        "zegt niets over de historie vóór het aftakpunt."
    )
    assert in_historie, (
        "fixturefout: de canary is niet bereikbaar vanaf head, dus er valt hier "
        "niets te vinden."
    )

    aanroep = _Aanroep(omgeving.binary, opzet.clone, opzet.config)
    argumenten = _historie_argumenten(aanroep, opzet, _NEW_BRANCH)

    uitkomst = _draai(argumenten, verboden=canary)

    assert not uitkomst.lekt, "de canary-waarde staat in de publieke uitvoer."
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] == _BLOCKED, (
        f"{_diagnose(uitkomst)} — de canary ligt in de historie vóór het "
        "aftakpunt van deze tak. Een uitblijvende blokkade betekent dat deze "
        "modus niet de volledige historie van head scant."
    )
    assert uitkomst.document["finding_count"] > 0, _diagnose(uitkomst)
    assert uitkomst.exit_code != 0, _diagnose(uitkomst)


def test_new_branch_op_rootcommit_scant_schoon(omgeving: _Omgeving) -> None:
    """Een head zonder ouder is een geldige scope, geen leeg bereik."""
    opzet = _clone_met_alleen_rootcommit(omgeving, "nb-rootcommit")
    aanroep = _Aanroep(omgeving.binary, opzet.clone, opzet.config)
    argumenten = _historie_argumenten(aanroep, opzet, _NEW_BRANCH)

    uitkomst = _draai(argumenten, verboden=_canary())

    assert not uitkomst.lekt
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["code"] != _EMPTY_RANGE, (
        f"{_diagnose(uitkomst)} — een rootcommit heeft geen ouder, maar wel "
        "inhoud. Die als leeg bereik afwijzen zou elke eerste push blokkeren."
    )
    assert uitkomst.document["status"] == _CLEAN, _diagnose(uitkomst)
    assert uitkomst.document["scanned_bytes"] > 0, _diagnose(uitkomst)
    assert uitkomst.exit_code == 0, _diagnose(uitkomst)


def _nb_zonder_base(aanroep: _Aanroep, opzet: _Fixture) -> list[str]:
    """Ook deze modus eist een expliciete grens; impliciet is geen invoer."""
    return [*_basis_argumenten(aanroep, _NEW_BRANCH), "--head", opzet.head]


def _nb_met_echte_base(aanroep: _Aanroep, opzet: _Fixture) -> list[str]:
    """Een bestaande commit als base hoort bij `full`, niet bij deze modus."""
    return [
        *_basis_argumenten(aanroep, _NEW_BRANCH),
        "--base",
        opzet.base,
        "--head",
        opzet.head,
    ]


def _nb_head_is_niet_de_werkboom(aanroep: _Aanroep, opzet: _Fixture) -> list[str]:
    """De HEAD-eis blijft gelden; `midden` bestaat wel, maar staat niet uitgecheckt."""
    return [
        *_basis_argumenten(aanroep, _NEW_BRANCH),
        "--base",
        _NULBASE,
        "--head",
        opzet.midden,
    ]


def _nb_lege_scope(aanroep: _Aanroep, opzet: _Fixture) -> list[str]:
    """Een map die geen werkboomroot is, levert geen scope op."""
    leeg = opzet.clone.parent / "leeg"
    leeg.mkdir(exist_ok=True)
    vervangen = _Aanroep(binary=aanroep.binary, source=leeg, config=aanroep.config)
    return [
        *_basis_argumenten(vervangen, _NEW_BRANCH),
        "--base",
        _NULBASE,
        "--head",
        opzet.head,
    ]


def _nb_fetchfout(aanroep: _Aanroep, opzet: _Fixture) -> list[str]:
    """Een onbereikbare origin mag geen stil versmald bereik opleveren."""
    _git(opzet.clone, "remote", "set-url", "origin", str(opzet.clone.parent / "weg"))
    return [
        *_basis_argumenten(aanroep, _NEW_BRANCH),
        "--base",
        _NULBASE,
        "--head",
        opzet.head,
    ]


@pytest.mark.parametrize(
    "bouw",
    [
        pytest.param(_nb_zonder_base, id="zonder-base"),
        pytest.param(_nb_met_echte_base, id="niet-nul-base"),
        pytest.param(_nb_head_is_niet_de_werkboom, id="head-is-niet-de-werkboom"),
        pytest.param(_nb_lege_scope, id="lege-scope"),
        pytest.param(_nb_fetchfout, id="fetchfout"),
    ],
)
def test_new_branch_foutpad_geeft_nonzero(
    omgeving: _Omgeving, bouw: Callable[[_Aanroep, _Fixture], list[str]]
) -> None:
    """De nieuwe modus verzwakt geen enkele bestaande grens."""
    opzet = _origin_met_clone(omgeving, "nb-foutpad")
    aanroep = _Aanroep(omgeving.binary, opzet.clone, opzet.config)

    uitkomst = _draai(bouw(aanroep, opzet), verboden=_canary())

    assert not uitkomst.lekt
    assert uitkomst.exit_code != 0, _diagnose(uitkomst)
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] != _CLEAN, _diagnose(uitkomst)


def test_full_weigert_de_nulbase(omgeving: _Omgeving) -> None:
    """`full` blijft een onbestaande voorganger afwijzen; de nieuwe modus is apart."""
    opzet = _origin_met_clone(omgeving, "full-nulbase")
    aanroep = _Aanroep(omgeving.binary, opzet.clone, opzet.config)

    uitkomst = _draai(
        _full_argumenten(aanroep, _NULBASE, opzet.head), verboden=_canary()
    )

    assert not uitkomst.lekt
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] != _CLEAN, (
        f"{_diagnose(uitkomst)} — de nulbase wijst geen commit aan. Groen worden "
        "op dat bereik zou een push met een onbewezen grens doorlaten."
    )
    assert uitkomst.exit_code != 0, _diagnose(uitkomst)


def _repo_met_index(
    omgeving: _Omgeving, naam: str, relpad: str, inhoud: str
) -> tuple[Path, Path]:
    """Repo met één commit en daarna precies één gestaged, niet-gecommit bestand."""
    basis, config = _nieuwe_basis(omgeving, naam)
    repo = _nieuwe_repo(basis, "repo")
    _commit(repo, "README.md", _README, "chore: basis")
    doel = repo / relpad
    doel.parent.mkdir(parents=True, exist_ok=True)
    doel.write_text(inhoud, encoding="utf-8")
    _git(repo, "add", "--", relpad)
    return repo, config


def test_staged_op_schone_index_geeft_clean(omgeving: _Omgeving) -> None:
    """Schoon gestaged werk blokkeert niet en toont aantoonbaar scanwerk."""
    repo, config = _repo_met_index(
        omgeving, "staged-schoon", _SCHOON_BESTAND, _SCHONE_INHOUD
    )
    aanroep = _Aanroep(omgeving.binary, repo, config)

    uitkomst = _draai(_staged_argumenten(aanroep), verboden=_canary())

    assert not uitkomst.lekt
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] == _CLEAN, _diagnose(uitkomst)
    assert uitkomst.document["finding_count"] == 0, _diagnose(uitkomst)
    assert uitkomst.document["scanned_bytes"] > 0, _diagnose(uitkomst)
    assert uitkomst.exit_code == 0, _diagnose(uitkomst)


def test_staged_canary_blokkeert(omgeving: _Omgeving) -> None:
    """Een gestagede canary blokkeert, zonder dat de waarde publiek wordt."""
    canary = _canary()
    repo, config = _repo_met_index(
        omgeving, "staged-canary", _CANARY_BESTAND, _canary_regel(canary)
    )

    # Boolean vóór de assertie: de canary-waarde mag nooit in een faalmelding
    # van pytest belanden.
    in_historie = canary in _git(repo, "log", "-p", "--all")
    assert not in_historie, (
        "fixturefout: de canary is al gecommit, dus deze test zegt niets over "
        "de scan van de index."
    )

    aanroep = _Aanroep(omgeving.binary, repo, config)
    uitkomst = _draai(_staged_argumenten(aanroep), verboden=canary)

    assert not uitkomst.lekt, "de canary-waarde staat in de publieke uitvoer."
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] == _BLOCKED, (
        f"{_diagnose(uitkomst)} — de canary staat gestaged in de index. Een "
        "uitblijvende blokkade betekent hier dat de staged-modus de index niet "
        "werkelijk scant."
    )
    assert uitkomst.document["finding_count"] > 0, _diagnose(uitkomst)
    assert uitkomst.exit_code != 0, _diagnose(uitkomst)


def test_staged_zonder_gestaged_werk_is_geen_succes(omgeving: _Omgeving) -> None:
    """Een lege index levert nul gescande bytes op; dat bewijst niets."""
    basis, config = _nieuwe_basis(omgeving, "staged-leeg")
    repo = _nieuwe_repo(basis, "repo")
    _commit(repo, "README.md", _README, "chore: basis")
    aanroep = _Aanroep(omgeving.binary, repo, config)

    uitkomst = _draai(_staged_argumenten(aanroep), verboden=_canary())

    assert not uitkomst.lekt
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] != _CLEAN, (
        f"{_diagnose(uitkomst)} — er is niets gestaged, dus er is niets "
        "gescand. Een schone uitkomst zou hier groen geven op nul bewijs."
    )
    assert uitkomst.exit_code != 0, _diagnose(uitkomst)


def _onbekende_modus(aanroep: _Aanroep, opzet: _Fixture) -> list[str]:
    """Een modus die niet bestaat; argparse zou de waarde willen citeren."""
    return _basis_argumenten(aanroep, _MARKER)


def _zonder_base(aanroep: _Aanroep, opzet: _Fixture) -> list[str]:
    """Full zonder expliciete `--base`; een impliciete grens is geen invoer.

    Verder volledig geldige invoer: alleen de ontbrekende grens kan deze
    aanroep afkeuren.
    """
    return [*_basis_argumenten(aanroep, "full"), "--head", opzet.head]


def _onbestaande_binary(aanroep: _Aanroep, opzet: _Fixture) -> list[str]:
    """Een binary-pad dat niet bestaat; dat pad mag niet worden geciteerd."""
    vervangen = _Aanroep(
        binary=aanroep.source.parent / _MARKER,
        source=aanroep.source,
        config=aanroep.config,
    )
    return _full_argumenten(vervangen, opzet.base, opzet.head)


def _niet_gehele_timeout(aanroep: _Aanroep, opzet: _Fixture) -> list[str]:
    """Een timeout die geen geheel getal is; de tekst mag niet terugkomen."""
    return _full_argumenten(aanroep, opzet.base, opzet.head, timeout=_MARKER)


def _head_is_niet_de_werkboom(aanroep: _Aanroep, opzet: _Fixture) -> list[str]:
    """Een bestaande commit met niet-lege range, maar niet de uitgecheckte HEAD.

    Zonder de HEAD-eis zou dit een gewone, geslaagde scan zijn: `base..midden`
    is niet leeg en beide commits bestaan. Alleen de eis dat de bron werkelijk op
    `--head` staat, kan deze aanroep afkeuren.
    """
    return _full_argumenten(aanroep, opzet.base, opzet.midden)


@pytest.mark.parametrize(
    "bouw",
    [
        pytest.param(_onbekende_modus, id="onbekende-modus"),
        pytest.param(_zonder_base, id="zonder-base"),
        pytest.param(_onbestaande_binary, id="onbestaande-binary"),
        pytest.param(_niet_gehele_timeout, id="niet-gehele-timeout"),
        pytest.param(_head_is_niet_de_werkboom, id="head-is-niet-de-werkboom"),
    ],
)
def test_foutpad_geeft_nonzero_zonder_de_invoerwaarde(
    omgeving: _Omgeving, bouw: Callable[[_Aanroep, _Fixture], list[str]]
) -> None:
    """Elk foutpad blokkeert, en citeert de ingevoerde waarde nergens."""
    opzet = _origin_met_clone(omgeving, "foutpad")
    aanroep = _Aanroep(omgeving.binary, opzet.clone, opzet.config)

    uitkomst = _draai(bouw(aanroep, opzet), verboden=_MARKER)

    assert not uitkomst.lekt, (
        "de ingevoerde waarde staat in de publieke uitvoer; ook een "
        "argparse-foutmelding mag invoer niet citeren."
    )
    assert uitkomst.exit_code != 0, _diagnose(uitkomst)
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] != _CLEAN, _diagnose(uitkomst)
