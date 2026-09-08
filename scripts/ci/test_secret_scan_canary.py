"""Canary: `scan_git()` tegen de échte gepinde Gitleaks-binary (DEF-522).

De unit-suites naast deze module bewijzen het *contract* van `scan_git()` met een
procesdouble: geen repository op schijf, geen tool, geen Git. Deze module doet
het omgekeerde en bewijst het *gedrag* met echte, kleine Git-repositories en de
echte binary:

1. **Schone range → CLEAN.** Twee gewone commits zonder sleutel geven `CLEAN`,
   een positief byteaantal en exitcode 0. Zou dit falen, dan blokkeert de gate
   op elke schone PR.
2. **Historische canary → BLOCKED.** Een sleutelwaarde die in een latere commit
   uit de bestandsinhoud is gehaald, staat niet meer in de werkkopie maar wel in
   de historie, en moet blijven blokkeren. De test stelt eerst vast dat de canary
   überhaupt wordt herkend zolang hij nog in de inhoud staat. Dit is het
   negatieve gedragsbewijs: blijft het tweede deel uit, dan laat de gate een
   verwijderd secret stil door. Let op: daar is `base` nog de eerste commit, dus
   de canary-commit valt binnen `base..head`.
3. **Canary buiten de PR-range → BLOCKED.** Hier is de *verwijderingscommit* de
   `base`, zodat de canary volledig buiten `base..head` én buiten de werkkopie
   valt; alleen de canonieke historie kan hem nog vinden. Dat wordt read-only
   bewezen met `git log -p`. Dit is het punt waarop een range-only scanner
   werkelijk omvalt — test 2 doet dat niet.
4. **Merge-introductie → BLOCKED.** Een canary die pas in de merge-commit zelf
   ontstaat, komt in geen van beide ouders voor en blijft onzichtbaar voor
   `git log -p` zónder `-m`, omdat een merge-commit dan geen diff toont. Dit is
   het gedragsbewijs dat de vaste `-m` in de log-opties werkelijk nodig is.
5. **Alleen via een canonieke ref → BLOCKED.** Een canary op een zijtak die niet
   vanaf de PR-head bereikbaar is, maar wel via een origin-branch of via een
   annotated tag. Dit bewijst dat de canonieke refs werkelijk worden meegescand,
   en in de tag-variant dat een annotated tag naar zijn commit wordt gepeeld in
   plaats van stil overgeslagen — met de échte tag-objecten, niet met een double.

**Buiten `testpaths`.** Dit bestand ligt bewust in `scripts/ci/` en niet onder
`tests/`, zodat de unit-gate niet ongemerkt afhankelijk wordt van een lokaal
geïnstalleerde Gitleaks. De Security-gate roept deze module later expliciet aan.

**Omgevingscontract — geen stille terugval.** `DEF522_GITLEAKS_BINARY` wijst naar
de bestaande, gepinde binary (8.29.1) en `DEF522_FIXTURE_ROOT` naar de vooraf
aangewezen fixture-root; voor de hostrun is dat
`/private/tmp/def522-fixtures-20260907-b36`. Ontbreekt of deugt een van beide
niet, dan **faalt** de test. Nooit een skip, nooit een installatie, nooit
netwerk: een canary die zichzelf overslaat bewijst niets.

**Fixture-isolatie.** Elke test maakt een eigen, nieuwe subdirectory onder de
opgegeven root (`mkdtemp`, dus nooit een bestaande map overschrijven) en laat die
na afloop staan als bewijsmateriaal. De git-child draait zonder de geërfde
`GIT_*`-variabelen van de hostsessie: een actieve `GIT_DIR`, `GIT_WORK_TREE`,
`GIT_INDEX_FILE` of `GIT_CONFIG_*` zou de fixture-commits naar een ándere
repository kunnen verleggen. Alleen een synthetische auteur/committer komt er
weer bij. Direct na `init` wordt read-only geverifieerd dat de werkboom en de
`.git`-map werkelijk de nieuwe fixture zijn; wijkt dat af, dan wordt er niets
gecommit. Buiten die root muteert deze module niets: geen projectremote, geen
globale Git-configuratie, geen `git -C`, geen netwerk. De canonieke origin-ref is
een lokale ref ín de fixture. Hooks worden bewust *niet* uitgezet; erft de host
een globale `core.hooksPath`, dan is een falende `git commit` een zichtbaar
omgevingsfeit en geen weggemoffelde uitkomst.

**Canary-waarde.** Zelf gegenereerd, hoort bij geen enkele account en gaat
nergens heen: alleen het *patroon* (`aws-access-token`) telt. De waarde staat
hier in delen, zodat dit bronbestand zelf geen aaneengesloten sleutelvorm bevat
en de secret-gate van dit project er niet op aanslaat. De waarde verlaat de
fixture niet: uitvoer en faalmeldingen tonen uitsluitend status en tellingen.

**Lezen van een rode uitkomst.** Test 2 scheidt de oorzaken van een uitblijvende
blokkade zelf: eerst wordt gescand terwijl de canary nog in de bestandsinhoud
staat, pas daarna nadat hij eruit is gehaald. Faalt de eerste assertie, dan is er
nog niets over de gate bewezen — de oorzaak ligt dan in de fixture, in de scanner
of in de tool zelf, en die drie zijn op dat punt niet uit elkaar te houden. Faalt
alleen de tweede, dan zit het gat in de dekking van verwijderde inhoud. Test 3
stelt de fixture-voorwaarden read-only vast (canary niet in de range, niet in de
werkkopie, wél in de bereikbare historie) voordat er iets over de gate wordt
beweerd. De booleans worden steeds vóór de assertie berekend, zodat de
canary-waarde nooit in een faalmelding van pytest belandt.
"""

from __future__ import annotations

import os
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

#: Verplichte, expliciete omgeving; geen van beide heeft een default.
_ENV_BINARY = "DEF522_GITLEAKS_BINARY"
_ENV_FIXTURE_ROOT = "DEF522_FIXTURE_ROOT"

#: De fixture wordt direct op deze branch geïnitialiseerd, zodat er geen moment
#: op `main` wordt gewerkt.
_BRANCH = "bugfix/DEF-522-canary"

#: Canonieke origin-ref, lokaal vastgelegd in de fixture zelf. `scan_git()` eist
#: minstens één ref onder `refs/remotes/origin` of `refs/tags`.
_ORIGIN_REF = f"refs/remotes/origin/{_BRANCH}"

#: Tweede canonieke aanwijzing naar een zijtak: een origin-branch respectievelijk
#: een annotated tag. Beide vallen onder de refs die `scan_git()` opsomt.
_ORIGIN_ZIJTAK_REF = "refs/remotes/origin/fixture-side"
_ZIJTAK_TAG = "v0.0.0-canary"

#: Minimale, actieve config: de standaardregelset van Gitleaks zelf.
_CONFIG_TOML = "[extend]\nuseDefault = true\n"
_CONFIG_NAAM = "gitleaks-canary.toml"

#: Ambient Git-configuratie uit de hostsessie mag de fixture niet verleggen.
_GIT_PREFIX = "GIT_"

#: Synthetische identiteit voor de fixture-commits, alleen in de child-omgeving.
_GIT_IDENTITEIT = {
    "GIT_AUTHOR_NAME": "DEF522 Canary",
    "GIT_AUTHOR_EMAIL": "def522-canary@invalid",
    "GIT_COMMITTER_NAME": "DEF522 Canary",
    "GIT_COMMITTER_EMAIL": "def522-canary@invalid",
}

#: Vaste boodschap: de fixture is niet de actieve werkboom, dus er wordt niets
#: gecommit. Zonder deze grens zou een ambient override in een échte repository
#: kunnen schrijven.
_ISOLATIEFOUT = (
    "fixture-isolatie: de nieuwe repository is niet de actieve werkboom of "
    "gebruikt een andere .git-map. Er wordt niets vastgelegd."
)

_GIT_TIMEOUT = 30
_SCAN_TIMEOUT = 20

#: De canary in delen. Aaneengesloten zou dit bronbestand zelf een geldige
#: sleutelvorm bevatten en door de secret-gate van dit project worden gezien;
#: samengevoegd matcht het de standaardregel `aws-access-token`.
#:
#: Het staartdeel volgt een base32-alfabet: de gepinde regel is
#: `(AKIA|...)[A-Z2-7]{16}` met `entropy = 3` (`config/gitleaks.toml:202` in de
#: gepinde pre-commit-bron). De cijfers 0, 1, 8 en 9 vallen daarbuiten — een
#: staart met een 8 erin matcht dus nooit, hoe sleutelvormig hij ook oogt.
_CANARY_DELEN = ("AK", "IA", "3QK7XZ2M", "J5R6W4TB")

#: Neutraal pad in de fixture: geen naam die door een allowlist wordt uitgesloten.
_CANARY_BESTAND = "src/deploy_settings.py"


@dataclass(frozen=True)
class _Omgeving:
    """De twee expliciet aangewezen paden waarop deze canary draait."""

    binary: Path
    fixture_root: Path


def _verplicht_pad(naam: str, *, uitvoerbaar: bool = False) -> Path:
    """Lees een verplichte omgevingsvariabele; ontbreken is een fout, geen skip."""
    waarde = os.environ.get(naam, "").strip()
    if not waarde:
        pytest.fail(
            f"{naam} ontbreekt. Wijs deze expliciet aan; deze canary installeert "
            "niets, zoekt niets op en slaat zichzelf niet over."
        )
    pad = Path(waarde)
    if not pad.is_absolute():
        pytest.fail(f"{naam} moet een absoluut pad zijn.")
    if uitvoerbaar and not (pad.is_file() and os.access(pad, os.X_OK)):
        pytest.fail(f"{naam} wijst niet naar een bestaande, uitvoerbare binary.")
    if not uitvoerbaar and not pad.is_dir():
        pytest.fail(f"{naam} wijst niet naar een bestaande directory.")
    return pad


def _git_omgeving() -> dict[str, str]:
    """Child-omgeving zonder geërfde `GIT_*`, plus de synthetische identiteit.

    `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` en `GIT_CONFIG_*` uit de
    hostsessie zouden een fixture-commit in een andere repository kunnen laten
    landen. Dit filtert alleen de child-omgeving; er wordt niets aan de globale
    configuratie gewijzigd en er worden geen hooks uitgezet.
    """
    schoon = {
        sleutel: waarde
        for sleutel, waarde in os.environ.items()
        if not sleutel.startswith(_GIT_PREFIX)
    }
    return schoon | _GIT_IDENTITEIT


def _git(repo: Path, *args: str) -> str:
    """Vast, begrensd git-commando in de fixture zelf — geen `-C`, geen shell."""
    voltooid = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        check=True,
        shell=False,
        text=True,
        timeout=_GIT_TIMEOUT,
        env=_git_omgeving(),
    )
    return voltooid.stdout.strip()


def _bewijs_isolatie(repo: Path) -> None:
    """Read-only bewijs dat commits in déze fixture landen, en nergens anders."""
    toplevel = Path(_git(repo, "rev-parse", "--show-toplevel")).resolve()
    gitdir = Path(_git(repo, "rev-parse", "--absolute-git-dir")).resolve()
    if toplevel != repo.resolve() or gitdir != (repo / ".git").resolve():
        pytest.fail(_ISOLATIEFOUT)


def _commit(repo: Path, relpad: str, inhoud: str, boodschap: str) -> str:
    """Schrijf één bestand en leg het vast; geeft het volledige commit-ID terug."""
    doel = repo / relpad
    doel.parent.mkdir(parents=True, exist_ok=True)
    doel.write_text(inhoud, encoding="utf-8")
    _git(repo, "add", "--", relpad)
    _git(repo, "commit", "--no-gpg-sign", "-m", boodschap)
    return _git(repo, "rev-parse", "HEAD")


def _nieuwe_fixture(omgeving: _Omgeving, naam: str) -> tuple[Path, Path]:
    """Verse fixture-subdirectory met een lege repo en een actieve config."""
    basis = Path(tempfile.mkdtemp(prefix=f"{naam}-", dir=str(omgeving.fixture_root)))
    config = basis / _CONFIG_NAAM
    config.write_text(_CONFIG_TOML, encoding="utf-8")
    repo = basis / "repo"
    repo.mkdir()
    _git(repo, "init", f"--initial-branch={_BRANCH}")
    _bewijs_isolatie(repo)
    return repo, config


def _scan(omgeving: _Omgeving, repo: Path, config: Path, base: str, head: str):
    return secret_scan.scan_git(
        omgeving.binary, repo, config, base, head, _SCAN_TIMEOUT
    )


def _diagnose(resultaat) -> str:
    """Alleen status en tellingen — nooit rapportinhoud of canary-waarde."""
    return (
        f"status={resultaat.status.value} code={resultaat.code.value} "
        f"findings={resultaat.finding_count} bytes={resultaat.scanned_bytes}"
    )


@pytest.fixture
def omgeving() -> _Omgeving:
    """De expliciet aangewezen binary en fixture-root; beide verplicht."""
    return _Omgeving(
        binary=_verplicht_pad(_ENV_BINARY, uitvoerbaar=True),
        fixture_root=_verplicht_pad(_ENV_FIXTURE_ROOT),
    )


def test_schone_git_range_geeft_clean(omgeving: _Omgeving) -> None:
    """Een echte, schone repo blokkeert niet en toont aantoonbaar scanwerk."""
    repo, config = _nieuwe_fixture(omgeving, "clean")
    base = _commit(
        repo, "README.md", "# Canary\n\nGewone tekst, geen sleutels.\n", "chore: basis"
    )
    head = _commit(
        repo, "src/module.py", 'WAARDE = "gewone tekst"\n', "chore: tweede commit"
    )
    _git(repo, "update-ref", _ORIGIN_REF, head)

    resultaat = _scan(omgeving, repo, config, base, head)

    assert resultaat.status is secret_scan.ScanStatus.CLEAN, _diagnose(resultaat)
    assert resultaat.code is secret_scan.ScanErrorCode.OK, _diagnose(resultaat)
    assert resultaat.finding_count == 0
    # Positief byteaantal: zonder gelezen bytes is "geen findings" geen bewijs.
    assert resultaat.scanned_bytes > 0, _diagnose(resultaat)
    assert resultaat.exit_code == 0


def test_historische_canary_blokkeert(omgeving: _Omgeving) -> None:
    """Een uit de bestandsinhoud gehaalde sleutel blijft in de historie staan."""
    repo, config = _nieuwe_fixture(omgeving, "canary")
    base = _commit(
        repo, "README.md", "# Canary\n\nGewone tekst, geen sleutels.\n", "chore: basis"
    )
    canary = "".join(_CANARY_DELEN)
    toegevoegd = _commit(
        repo,
        _CANARY_BESTAND,
        f'AWS_ACCESS_KEY_ID = "{canary}"\n',
        "chore: instellingen toevoegen",
    )
    _git(repo, "update-ref", _ORIGIN_REF, toegevoegd)

    # Eerst herkenning, dan pas historiedekking: zolang de canary nog gewoon in
    # de bestandsinhoud staat, bewijst een blokkade dat deze Gitleaks-versie het
    # patroon überhaupt ziet. Zonder deze stap is een latere CLEAN niet te
    # onderscheiden van een fixture die nooit kon matchen.
    herkend = _scan(omgeving, repo, config, base, toegevoegd)

    assert herkend.status is secret_scan.ScanStatus.BLOCKED, (
        f"{_diagnose(herkend)} — de canary wordt niet eens herkend terwijl hij "
        "nog in de bestandsinhoud staat. De oorzaak ligt dan in de fixture, in "
        "de scanner of in de tool zelf; die drie zijn hier niet uit elkaar te "
        "houden. Over de historiedekking van de gate is nog niets bewezen."
    )
    assert herkend.finding_count > 0, _diagnose(herkend)

    head = _commit(
        repo,
        _CANARY_BESTAND,
        'AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]\n',
        "chore: waarde uit de code halen",
    )
    _git(repo, "update-ref", _ORIGIN_REF, head)

    # Booleaan vóór de assertie: een directe `in`-assertie zou de canary-waarde
    # in de faalmelding van pytest afdrukken.
    uit_werkkopie = canary not in (repo / _CANARY_BESTAND).read_text(encoding="utf-8")
    assert uit_werkkopie, (
        "fixturefout: de waarde staat nog in de huidige bestandsinhoud, dus deze "
        "test bewijst niets over historiedekking."
    )

    # `base` is nog de eerste commit, dus de canary-commit valt hier bínnen
    # `base..head`. Deze test bewijst daarmee dat uit de inhoud gehaalde waarden
    # binnen de range blijven blokkeren; dat de historie óók buiten de range
    # wordt gedekt, bewijst `test_canary_buiten_de_pr_range_blokkeert`.
    resultaat = _scan(omgeving, repo, config, base, head)

    geblokkeerd = resultaat.status is secret_scan.ScanStatus.BLOCKED
    assert geblokkeerd, (
        f"{_diagnose(resultaat)} — de canary werd hierboven wél herkend en staat "
        "niet meer in de werkkopie, dus een uitblijvende blokkade betekent hier "
        "dat verwijderde inhoud binnen de range niet wordt gedekt."
    )
    assert resultaat.code is secret_scan.ScanErrorCode.FINDINGS_PRESENT
    assert resultaat.finding_count > 0, _diagnose(resultaat)
    assert resultaat.exit_code != 0


def test_canary_buiten_de_pr_range_blokkeert(omgeving: _Omgeving) -> None:
    """Buiten `base..head` en buiten de werkkopie, maar wel in de historie."""
    repo, config = _nieuwe_fixture(omgeving, "buiten-range")
    _commit(
        repo, "README.md", "# Canary\n\nGewone tekst, geen sleutels.\n", "chore: basis"
    )
    canary = "".join(_CANARY_DELEN)
    _commit(
        repo,
        _CANARY_BESTAND,
        f'AWS_ACCESS_KEY_ID = "{canary}"\n',
        "chore: instellingen toevoegen",
    )
    # De verwijderingscommit is de base: alles ervóór ligt buiten de PR-range.
    base = _commit(
        repo,
        _CANARY_BESTAND,
        'AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]\n',
        "chore: waarde uit de code halen",
    )
    head = _commit(
        repo, "src/module.py", 'WAARDE = "gewone tekst"\n', "chore: vervolgwerk"
    )
    _git(repo, "update-ref", _ORIGIN_REF, head)

    # Booleans vóór de asserties: een directe `in`-assertie zou de canary-waarde
    # in de faalmelding van pytest afdrukken.
    in_range = canary in _git(repo, "log", "-p", f"{base}..{head}")
    in_werkkopie = canary in (repo / _CANARY_BESTAND).read_text(encoding="utf-8")
    in_historie = canary in _git(repo, "log", "-p", head)

    assert not in_range, (
        "fixturefout: de canary zit in de PR-range zelf, dus deze test zou ook "
        "slagen met een scanner die uitsluitend de range dekt."
    )
    assert not in_werkkopie, "fixturefout: de waarde staat nog in de werkkopie."
    assert in_historie, (
        "fixturefout: de canary staat niet in de bereikbare historie, dus hier "
        "valt niets over historiedekking te bewijzen."
    )

    resultaat = _scan(omgeving, repo, config, base, head)

    assert resultaat.status is secret_scan.ScanStatus.BLOCKED, (
        f"{_diagnose(resultaat)} — de canary ligt buiten `base..head` én buiten "
        "de werkkopie, maar wel in de canonieke historie. Een uitblijvende "
        "blokkade betekent hier dat de gate alleen de range dekt."
    )
    assert resultaat.code is secret_scan.ScanErrorCode.FINDINGS_PRESENT
    assert resultaat.finding_count > 0, _diagnose(resultaat)
    assert resultaat.exit_code != 0


def test_in_de_merge_geintroduceerde_canary_blokkeert(omgeving: _Omgeving) -> None:
    """Een canary die pas in de merge ontstaat, staat in geen enkele ouder."""
    repo, config = _nieuwe_fixture(omgeving, "merge")
    _commit(
        repo, "README.md", "# Canary\n\nGewone tekst, geen sleutels.\n", "chore: basis"
    )
    zijtak = f"{_BRANCH}-zijtak"
    _git(repo, "checkout", "-b", zijtak)
    _commit(repo, "src/zijtak.py", 'ZIJTAK = "gewone tekst"\n', "chore: zijtak")

    _git(repo, "checkout", _BRANCH)
    base = _commit(
        repo, "src/hoofdtak.py", 'HOOFD = "gewone tekst"\n', "chore: hoofdtak"
    )

    # Reguliere merge die stopt vóór het vastleggen, zodat de canary uitsluitend
    # in de merge-commit zelf ontstaat en in geen van beide ouders voorkomt.
    _git(repo, "merge", "--no-ff", "--no-commit", zijtak)
    canary = "".join(_CANARY_DELEN)
    merge_head = _commit(
        repo,
        _CANARY_BESTAND,
        f'AWS_ACCESS_KEY_ID = "{canary}"\n',
        "chore: zijtak samenvoegen",
    )
    _git(repo, "update-ref", _ORIGIN_REF, merge_head)

    # Booleans vóór de asserties: de canary-waarde mag nooit in een faalmelding
    # van pytest belanden.
    ouders = _git(repo, "rev-list", "--parents", "-n", "1", merge_head).split()[1:]
    in_ouders = any(canary in _git(repo, "log", "-p", ouder) for ouder in ouders)
    zonder_m = canary in _git(repo, "log", "-p", f"{base}..{merge_head}")

    assert len(ouders) == 2, f"fixturefout: merge-commit heeft {len(ouders)} ouders."
    assert not in_ouders, (
        "fixturefout: de canary staat al in de historie van een ouder, dus dit "
        "bewijst niets over introductie in de merge zelf."
    )
    assert not zonder_m, (
        "fixturefout: `git log -p` zonder `-m` toont de canary al, dus deze test "
        "zou ook slagen zonder dat de merge-diff wordt gescand."
    )

    resultaat = _scan(omgeving, repo, config, base, merge_head)

    assert resultaat.status is secret_scan.ScanStatus.BLOCKED, (
        f"{_diagnose(resultaat)} — de canary ontstaat pas in de merge-commit en "
        "komt in geen van beide ouders voor. Een uitblijvende blokkade betekent "
        "hier dat de merge-diff niet wordt meegescand."
    )
    assert resultaat.code is secret_scan.ScanErrorCode.FINDINGS_PRESENT
    assert resultaat.finding_count > 0, _diagnose(resultaat)
    assert resultaat.exit_code != 0


def _markeer_via_origin(repo: Path, commit: str) -> None:
    """Wijs de zijtak aan met een canonieke origin-branch."""
    _git(repo, "update-ref", _ORIGIN_ZIJTAK_REF, commit)


def _markeer_via_tag(repo: Path, commit: str) -> None:
    """Wijs de zijtak aan met een annotated tag — géén origin-ref dus.

    Een annotated tag is een eigen object; `for-each-ref` levert daarvan het
    tag-object-ID, dat naar zijn commit gepeeld moet worden.
    """
    _git(repo, "tag", "-a", _ZIJTAK_TAG, "-m", "chore: zijtak markeren", commit)


@pytest.mark.parametrize(
    "markeer",
    [
        pytest.param(_markeer_via_origin, id="origin-branch"),
        pytest.param(_markeer_via_tag, id="annotated-tag"),
    ],
)
def test_canary_alleen_via_canonieke_ref_blokkeert(
    omgeving: _Omgeving, markeer: Callable[[Path, str], None]
) -> None:
    """Onbereikbaar vanaf de PR-head, maar wel via een canonieke ref."""
    repo, config = _nieuwe_fixture(omgeving, "zijtak")
    base = _commit(
        repo, "README.md", "# Canary\n\nGewone tekst, geen sleutels.\n", "chore: basis"
    )
    head = _commit(
        repo, "src/module.py", 'WAARDE = "gewone tekst"\n', "chore: tweede commit"
    )

    # De zijtak hangt aan `base` en is dus niet bereikbaar vanaf de PR-head.
    _git(repo, "checkout", "-b", f"{_BRANCH}-zijtak", base)
    canary = "".join(_CANARY_DELEN)
    zijtak_commit = _commit(
        repo,
        _CANARY_BESTAND,
        f'AWS_ACCESS_KEY_ID = "{canary}"\n',
        "chore: zijtakwerk",
    )
    markeer(repo, zijtak_commit)
    _git(repo, "checkout", _BRANCH)
    _git(repo, "update-ref", _ORIGIN_REF, head)

    # Booleans vóór de asserties: de canary-waarde mag nooit in een faalmelding
    # van pytest belanden.
    canary_bestand = repo / _CANARY_BESTAND
    werkkopie = (
        canary_bestand.read_text(encoding="utf-8") if canary_bestand.exists() else ""
    )
    in_prhead_historie = canary in _git(repo, "log", "-p", head)
    in_werkkopie = canary in werkkopie
    in_zijtak = canary in _git(repo, "log", "-p", zijtak_commit)

    assert not in_prhead_historie, (
        "fixturefout: de canary is bereikbaar vanaf de PR-head, dus deze test "
        "zou ook slagen met een scanner die alleen die historie dekt."
    )
    assert not in_werkkopie, "fixturefout: de waarde staat nog in de werkkopie."
    assert in_zijtak, (
        "fixturefout: de canary staat niet in de zijtakhistorie, dus hier valt "
        "niets over de dekking van canonieke refs te bewijzen."
    )

    resultaat = _scan(omgeving, repo, config, base, head)

    assert resultaat.status is secret_scan.ScanStatus.BLOCKED, (
        f"{_diagnose(resultaat)} — de canary is alleen via de canonieke ref "
        "bereikbaar, niet vanaf de PR-head. Een uitblijvende blokkade betekent "
        "hier dat die ref niet wordt meegescand."
    )
    assert resultaat.code is secret_scan.ScanErrorCode.FINDINGS_PRESENT
    assert resultaat.finding_count > 0, _diagnose(resultaat)
    assert resultaat.exit_code != 0
