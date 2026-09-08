"""Contract- en gedragstests voor de Git-scan van de secret-gate (DEF-522).

Deze suite legt het gewenste contract vast van een nog te schrijven publieke
ingang `scan_git(binary, source, config, base, head, timeout)` in
`scripts/ci/secret_scan.py`. Zij hoort bij de RED-stap: zolang die functie en
haar diagnosecodes ontbreken, falen deze tests op een **API-contractassertie**
(`_scan_git` / `_code` hieronder). Dat is uitdrukkelijk géén uitspraak over
waargenomen gedrag — gedrags-RED kan pas worden vastgesteld nadat een minimale
fail-closed ingang bestaat.

Wat het contract moet borgen:

1. **Dezelfde resultaatgrens als `scan_directory`.** Altijd een `ScanResult` met
   vaste status, vaste diagnosecode en tellingen; nooit een exceptie en nooit
   Git- of Gitleaks-tekst naar buiten.
2. **Expliciete, geverifieerde commits.** `base` en `head` zijn volledige
   hexadecimale commit-ID's — geen ref-namen, geen vlaggen, geen afkortingen —
   en de bijbehorende objecten moeten werkelijk aanwezig zijn.
3. **Aantoonbaar scanbereik.** Een niet-repository, een shallow checkout en een
   partial clone leveren geen bewijsbare historie op en worden geweigerd —
   partial/promisor-metadata van élke remote plus `extensions.partialclone`,
   niet alleen die van `origin`. Ook een bereik waarin objecten ontbreken, een
   lege PR-range en een ontbrekende canonieke historie worden geweigerd, en de
   child-omgeving zet lazy fetch en replacement-objecten expliciet uit.
4. **Range én historie.** De expliciete `base..head`-range wordt gescand, én de
   bereikbare historie van de canonieke origin-branches/tags plus de PR-head.
   Een secret dat alleen nog in de historie zit, moet blijven blokkeren.
5. **Vaste log-opties.** `--full-history -m` met geverifieerde hex-ID's; geen
   `--all` en geen vrije logopties uit de omgeving of van de aanroeper.

**Geen repository op schijf.** De fixture maakt uitsluitend een gewone
`tmp_path`-map met één niet-leeg tekstbestand. Er wordt geen `.git`-map,
geen shallow-bestand, geen ref en geen pseudo-object aangelegd, en er start geen
Git-, subprocess- of netwerkaanroep. Álle Git-metadata — repository-identiteit,
shallow, partial, refs, objectbestaan, commit-opsommingen — komt uit
geprogrammeerde waarden van de procesdouble (`_Git`). De productcode mag die
feiten gerust via een Git-hulpcommando ophalen; de double bepaalt het antwoord.

**Gesloten doublegrens.** `_ProcesRouter` ondersteunt een vaste, read-only
verzameling Git-hulpcommando's. Een niet-ondersteund proces of commando levert
geen neutraal succes maar `_OnverwachtProces`, zodat een stil afwijkend
commando-oppervlak zichtbaar wordt in plaats van te slagen. Die klasse erft
bewust van `BaseException`: een `AssertionError` zou door de fail-closed
`contextlib.suppress(Exception)` van de productcode gemaskeerd worden, en dan
zou de grens juist onzichtbaar zijn. (`pytest.fail` heeft dat bezwaar niet —
`Failed` erft via `OutcomeException` óók van `BaseException` — maar een eigen
klasse is hier gerichter aan te spreken met `pytest.raises`.) `TestDoubleGrens`
bewijst die eigenschap. Uitbreiden van het commando-oppervlak vraagt dus om een
bewuste wijziging van deze tabel.

**Tellingen zijn waarnemingen.** `finding_count` telt de waarnemingen over de
deelscans heen. Range en historie overlappen: hetzelfde secret kan in beide
worden gezien. Het getal is dus géén unieke-incidenttelling en mag ook niet zo
worden gelezen; het bewijst alleen dat beide deelscans meetellen.

**Openstaand caller-contract (eerlijk gemeld, niet weggetest).** Lokale
`refs/remotes/origin/*` bewijzen niet dat de checkout de canonieke refs
*volledig* heeft opgehaald: een begrensde fetch levert eveneens refs. Shallow en
partial zijn wél vast te stellen en worden hier getest; volledige remote-dekking
is dat niet. Het huidige signatuur biedt geen kanaal voor zulk fetch-bewijs, dus
die garantie moet van de caller komen (expliciete volledige fetch plus
doorgegeven bewijs) — er wordt hier geen bypass van die eindgate geïmproviseerd.
Deze suite legt alleen de ondergrens vast: zonder canonieke refs volgt een fout,
geen stille terugval op alleen de range.

Alle waarden zijn zelf gegenereerd en synthetisch: de commit-ID's horen bij geen
enkel bestaand object, de markers zijn bewust niet sleutelvormig, en er wordt
geen projectdatabase, `.env` of historische waarde aangeraakt. Bewijs met de
échte gepinde binary is een aparte canary.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "ci"))

import secret_scan

# Synthetische commit-ID's: geldige 40-hex vorm, herkenbaar zelfverzonnen.
_BASE = "1111111111111111111111111111111111111111"
_HEAD = "2222222222222222222222222222222222222222"
_ORIGIN_MAIN = "3333333333333333333333333333333333333333"
_ORIGIN_TAG = "4444444444444444444444444444444444444444"
_TUSSEN = "5555555555555555555555555555555555555555"
# Het tag-object van een annotated tag: zelf geen commit, peelt naar er een.
_TAG_OBJECT = "6666666666666666666666666666666666666666"
# Een blob uit het objectrapport van `rev-list --objects`.
_BLOB_OBJECT = "7777777777777777777777777777777777777777"

_ALLE_OBJECTEN = frozenset({_BASE, _HEAD, _ORIGIN_MAIN, _ORIGIN_TAG, _TUSSEN})

#: `git rev-parse <id>^{commit}` peelt een ref naar zijn commit.
_PEEL_ACHTERVOEGSEL = "^{commit}"

# Synthetische markers voor onbetrouwbare tool-inhoud (secret, match, logregel,
# Git-fouttekst). Geen ervan mag in publieke uitvoer of logging opduiken.
_MARKER_SECRET = "SYNTHETISCHE-GITMARKER-ALFA-GEEN-ECHTE-WAARDE"
_MARKER_MATCH = "SYNTHETISCHE-GITMARKER-BRAVO-GEEN-ECHTE-WAARDE"
_MARKER_LOG = "SYNTHETISCHE-GITMARKER-CHARLIE-GEEN-ECHTE-WAARDE"
_MARKER_GIT = "SYNTHETISCHE-GITMARKER-DELTA-GEEN-ECHTE-WAARDE"
_MARKERS = (_MARKER_SECRET, _MARKER_MATCH, _MARKER_LOG, _MARKER_GIT)

_ACTIEVE_CONFIG = "[extend]\nuseDefault = true\n"

# Twee deelscans met verschillende byteaantallen, zodat zichtbaar is dat beide
# meetellen in het samengestelde resultaat.
_BYTES_RANGE = 128
_BYTES_HISTORIE = 256

# `-m` als los token: voorafgegaan door spatie of `=`, niet door een woordteken.
_LOSSE_M = re.compile(r"(?<![\w-])-m(?![\w-])")

# Vrije of verbredende logopties horen niet in een expliciet bereik.
_VERBODEN_LOGOPTIES = (
    "--all",
    "--branches",
    "--remotes",
    "--tags",
    "--glob",
    "--since",
    "--until",
    "--not",
    "--max-count",
)


class _OnverwachtProces(BaseException):
    """Doublegrens: er is een niet-ondersteund proces of commando aangeroepen.

    Erft van `BaseException` zodat de fail-closed buitengrens van de productcode
    (`contextlib.suppress(Exception)`) deze grens niet kan maskeren, zoals bij
    een `AssertionError` wél zou gebeuren.
    """


@dataclass(frozen=True)
class _Respons:
    """Vaste procesrespons uit de tabel — geen echte tool, geen echte repo."""

    returncode: int = 0
    stdout: bytes = b""
    stderr: bytes = b""
    raises: BaseException | None = None


@dataclass(frozen=True)
class _Git:
    """Geprogrammeerde antwoorden van de read-only Git-hulpcommando's.

    Dit is de enige bron van Git-waarheid in deze suite; op schijf staat niets
    dat op een repository lijkt.
    """

    is_repository: bool = True
    is_shallow: bool = False
    is_partial: bool = False
    #: Regels zoals `git config --get-regexp` ze levert: "<sleutel> <waarde>".
    config_regels: tuple[str, ...] = ()
    #: Objectrapport van `rev-list --objects`: één object-ID per regel.
    objectrapport: tuple[str, ...] = (_HEAD, _TUSSEN, _BLOB_OBJECT)
    objecten: frozenset[str] = _ALLE_OBJECTEN
    refs: tuple[str, ...] = (_ORIGIN_MAIN, _ORIGIN_TAG)
    range_commits: tuple[str, ...] = (_HEAD, _TUSSEN)
    historie_commits: tuple[str, ...] = (
        _HEAD,
        _TUSSEN,
        _ORIGIN_MAIN,
        _ORIGIN_TAG,
        _BASE,
    )
    faalt_op: str | None = None
    #: Respons voor `faalt_op`; None betekent de standaard Git-fout.
    faalt_met: _Respons | None = None
    #: Tag-object-ID → commit-ID. Ontbreekt een ID, dan peelt het naar zichzelf.
    peel: dict[str, str] = field(default_factory=dict)


_GIT_STANDAARD = _Git()


def _schone_stderr(bytes_aantal: int) -> bytes:
    return (
        f"11:20AM INF scanned ~{bytes_aantal} bytes (0.13 KB) in 11ms\n"
        "11:20AM INF no leaks found\n"
    ).encode()


def _findings_stderr(bytes_aantal: int, aantal: int) -> bytes:
    return (
        f"11:20AM INF scanned ~{bytes_aantal} bytes (0.13 KB) in 11ms\n"
        f"11:20AM WRN leaks found: {aantal}\n"
    ).encode()


def _findings_json(aantal: int) -> bytes:
    """Rapport met `aantal` findings; elk veld draagt een synthetische marker."""
    return json.dumps(
        [
            {
                "RuleID": "synthetische-canaryregel",
                "File": f"pakket/module_{volgnummer}.py",
                "StartLine": 3,
                "Commit": _TUSSEN,
                "Secret": _MARKER_SECRET,
                "Match": _MARKER_MATCH,
                "Line": _MARKER_LOG,
                "CommitMessage": _MARKER_LOG,
            }
            for volgnummer in range(aantal)
        ]
    ).encode()


def _findings_respons(bytes_aantal: int, aantal: int) -> _Respons:
    return _Respons(
        returncode=1,
        stdout=_findings_json(aantal),
        stderr=_findings_stderr(bytes_aantal, aantal),
    )


_SCHOON_RANGE = _Respons(stdout=b"[]", stderr=_schone_stderr(_BYTES_RANGE))
_SCHOON_HISTORIE = _Respons(stdout=b"[]", stderr=_schone_stderr(_BYTES_HISTORIE))
_GIT_FOUT = _Respons(returncode=128, stderr=_MARKER_GIT.encode())


def _is_hex40(waarde: str) -> bool:
    return len(waarde) == 40 and all(teken in "0123456789abcdef" for teken in waarde)


def _is_range(argv: list[str]) -> bool:
    """Herkent de deelscan van de expliciete PR-range aan de `base..head`-vorm."""
    return any(f"{_BASE}..{_HEAD}" in argument for argument in argv)


def _regels(waarden: tuple[str, ...]) -> bytes:
    return "".join(f"{waarde}\n" for waarde in waarden).encode()


class _ProcesRouter:
    """Beantwoordt elke subprocess-aanroep uit een vaste, gesloten tabel.

    Het onderscheid tussen de gepinde Gitleaks-binary en een Git-hulpcommando
    loopt over `argv[0]`. Welke van de twee Gitleaks-deelscans antwoord krijgt,
    hangt af van de *inhoud* van de log-opts (bevat die `base..head`?), niet van
    de aanroepvolgorde.

    Ondersteund zijn uitsluitend deze read-only Git-hulpcommando's:
    `rev-parse --is-inside-work-tree`, `rev-parse --is-shallow-repository`,
    `rev-parse <id>^{commit}` (een ref naar zijn commit peelen), `config`
    (`--get <sleutel>` of `--get-regexp <patroon>` over de partial/promisor-
    metadata), `cat-file` (objectbestaan), `for-each-ref` (één commit-ID per
    regel) en `rev-list` (range- of historie-opsomming, of met `--objects` het
    objectrapport). Alles daarbuiten is een fout in plaats van een neutraal
    succes.
    """

    def __init__(
        self,
        binary: Path,
        *,
        git: _Git | None = None,
        range_respons: _Respons | None = None,
        historie_respons: _Respons | None = None,
    ) -> None:
        self.binary = str(Path(binary).resolve())
        self.git = git or _GIT_STANDAARD
        self.range_respons = range_respons or _SCHOON_RANGE
        self.historie_respons = historie_respons or _SCHOON_HISTORIE
        self.calls: list[tuple[list[str], dict]] = []

    def __call__(self, argv, **kwargs):
        argumenten = [str(deel) for deel in argv]
        self.calls.append((argumenten, dict(kwargs)))
        respons = self._respons(argumenten)
        if respons.raises is not None:
            raise respons.raises
        return subprocess.CompletedProcess(
            argumenten, respons.returncode, respons.stdout, respons.stderr
        )

    @property
    def gitleaks_calls(self) -> list[tuple[list[str], dict]]:
        return [aanroep for aanroep in self.calls if self._is_gitleaks(aanroep[0])]

    @property
    def gitleaks_argvs(self) -> list[list[str]]:
        return [argv for argv, _ in self.gitleaks_calls]

    def _is_gitleaks(self, argv: list[str]) -> bool:
        return bool(argv) and argv[0] == self.binary

    def _respons(self, argv: list[str]) -> _Respons:
        if self._is_gitleaks(argv):
            return self.range_respons if _is_range(argv) else self.historie_respons
        return self._git_respons(argv)

    def _config_regels(self) -> tuple[str, ...]:
        """Alle partial/promisor-metadata die deze checkout zou melden."""
        git = self.git
        origin = (
            ("remote.origin.partialclonefilter blob:none",) if git.is_partial else ()
        )
        return origin + git.config_regels

    def _git_respons(self, argv: list[str]) -> _Respons:
        git = self.git
        if git.faalt_op is not None and git.faalt_op in argv:
            return git.faalt_met or _GIT_FOUT
        if "--is-inside-work-tree" in argv:
            return _Respons(stdout=b"true\n") if git.is_repository else _GIT_FOUT
        if "--is-shallow-repository" in argv:
            return _Respons(stdout=b"true\n" if git.is_shallow else b"false\n")
        if "rev-parse" in argv:
            # Alleen het peelen van een ref naar zijn commit is ondersteund;
            # elke andere `rev-parse`-vorm valt buiten de tabel.
            doelen = [
                deel.removesuffix(_PEEL_ACHTERVOEGSEL)
                for deel in argv
                if deel.endswith(_PEEL_ACHTERVOEGSEL)
            ]
            if not doelen:
                raise _OnverwachtProces(
                    f"doublegrens: niet-ondersteunde rev-parse-vorm {argv[:4]!r}"
                )
            commits = [git.peel.get(doel, doel) for doel in doelen]
            if any(commit not in git.objecten for commit in commits):
                return _GIT_FOUT
            return _Respons(stdout=_regels(tuple(commits)))
        if "config" in argv:
            # Exit 1 = niets gevonden, dus geen partial-clone-metadata.
            regels = self._config_regels()
            if "--get-regexp" not in argv and "--get" in argv:
                sleutel = argv[argv.index("--get") + 1]
                regels = tuple(r for r in regels if r.startswith(f"{sleutel} "))
            if not regels:
                return _Respons(returncode=1)
            return _Respons(stdout=_regels(regels))
        if "cat-file" in argv:
            gevraagd = [deel for deel in argv if _is_hex40(deel)]
            if not gevraagd or any(deel not in git.objecten for deel in gevraagd):
                return _GIT_FOUT
            return _Respons(stdout=b"commit\n")
        if "for-each-ref" in argv:
            return _Respons(stdout=_regels(git.refs))
        if "rev-list" in argv:
            if "--objects" in argv:
                return _Respons(stdout=_regels(git.objectrapport))
            bron = git.range_commits if _is_range(argv) else git.historie_commits
            return _Respons(stdout=_regels(bron))
        raise _OnverwachtProces(
            "doublegrens: niet-ondersteund proces of Git-commando "
            f"{argv[:4]!r}; brei de tabel bewust uit in plaats van te slagen"
        )


@pytest.fixture
def binary(tmp_path: Path) -> Path:
    """Uitvoerbaar bestand op de plek van de gepinde tool (proces is gedoubled)."""
    pad = tmp_path / "gitleaks"
    pad.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    pad.chmod(0o755)
    return pad


@pytest.fixture
def config(tmp_path: Path) -> Path:
    """Expliciete TOML-config met actieve regels."""
    pad = tmp_path / "gitleaks.toml"
    pad.write_text(_ACTIEVE_CONFIG, encoding="utf-8")
    return pad


@pytest.fixture
def source(tmp_path: Path) -> Path:
    """Gewone, niet-lege werkmap — geen repository-artefacten op schijf."""
    pad = tmp_path / "checkout"
    pad.mkdir()
    (pad / "module.py").write_text("waarde = 1\n", encoding="utf-8")
    return pad


@pytest.fixture
def router(binary: Path, monkeypatch: pytest.MonkeyPatch) -> _ProcesRouter:
    """Standaardtabel: geldige scope, schone range en schone historie."""
    return _installeer(monkeypatch, _ProcesRouter(binary))


def _installeer(monkeypatch, double: _ProcesRouter) -> _ProcesRouter:
    monkeypatch.setattr(secret_scan.subprocess, "run", double)
    return double


def _scan_git(binary, source, config, base=_BASE, head=_HEAD, timeout=30):
    """Roep de publieke Git-ingang aan.

    Zolang `scan_git` ontbreekt, is dit een **API-contractassertie**: de test
    faalt op het ontbrekende contract en doet geen uitspraak over gedrag.
    """
    functie = getattr(secret_scan, "scan_git", None)
    assert callable(functie), (
        "ontbrekend API-contract: publieke scan_git(binary, source, config, "
        "base, head, timeout) ontbreekt in scripts/ci/secret_scan.py"
    )
    return functie(binary, source, config, base, head, timeout)


def _code(naam: str):
    """Vaste diagnosecode uit het contract; ontbreken is een contractfout."""
    code = getattr(secret_scan.ScanErrorCode, naam, None)
    assert code is not None, f"ontbrekend API-contract: ScanErrorCode.{naam}"
    return code


def _scope_gedekt(argv: list[str], kwargs: dict, source: Path) -> bool:
    """De scan draait op de opgegeven checkout, positioneel of als cwd."""
    pad = str(Path(source).resolve())
    return pad in argv or str(kwargs.get("cwd", "")) == pad


def _oppervlak(resultaat, capsys, caplog) -> str:
    """Alle publieke tekst rond een resultaat: resultaat, uitvoer én logging."""
    gerapporteerd = capsys.readouterr()
    return "\n".join(
        [
            repr(resultaat),
            str(resultaat),
            str(resultaat.status),
            str(resultaat.code),
            gerapporteerd.out,
            gerapporteerd.err,
            caplog.text,
            *(record.getMessage() for record in caplog.records),
        ]
    )


class TestDoubleGrens:
    """De procesdouble slaagt nergens stil; onbekend is een harde fout."""

    def test_niet_ondersteund_commando_wordt_geweigerd(self, binary):
        router = _ProcesRouter(binary)

        with pytest.raises(_OnverwachtProces):
            router(["git", "gc", "--prune=now"])

        # Zou de grens van `Exception` erven (zoals een `AssertionError`), dan
        # slikte de fail-closed buitengrens van de productcode haar en bleef de
        # afwijking onzichtbaar.
        assert not issubclass(_OnverwachtProces, Exception)
        assert router.gitleaks_argvs == []


class TestPubliekContract:
    """Vaste resultaatgrens, gelijk aan die van `scan_directory`."""

    def test_scan_git_levert_een_scanresult(self, binary, source, config, router):
        resultaat = _scan_git(binary, source, config)

        assert isinstance(resultaat, secret_scan.ScanResult)
        assert isinstance(resultaat.status, secret_scan.ScanStatus)
        assert isinstance(resultaat.code, secret_scan.ScanErrorCode)
        assert isinstance(resultaat.finding_count, int)
        assert isinstance(resultaat.scanned_bytes, int)

    def test_schone_range_en_historie_geven_clean(self, binary, source, config, router):
        resultaat = _scan_git(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.CLEAN
        assert resultaat.code is secret_scan.ScanErrorCode.OK
        assert resultaat.finding_count == 0
        # Beide deelscans tellen mee; alleen de range zou 128 opleveren.
        assert resultaat.scanned_bytes == _BYTES_RANGE + _BYTES_HISTORIE
        assert resultaat.ok is True
        assert resultaat.exit_code == 0


class TestBereikRangeEnHistorie:
    """De bedoelde range én de canonieke historie worden werkelijk gescand."""

    def test_range_wordt_met_geverifieerde_hex_gescand(
        self, binary, source, config, router
    ):
        _scan_git(binary, source, config)

        range_scans = [
            (argv, kwargs) for argv, kwargs in router.gitleaks_calls if _is_range(argv)
        ]
        assert len(range_scans) == 1
        argv, kwargs = range_scans[0]
        assert argv[1] == "git"
        assert _scope_gedekt(argv, kwargs, source)

    def test_historie_dekt_canonieke_refs_en_prhead(
        self, binary, source, config, router
    ):
        _scan_git(binary, source, config)

        historie = [argv for argv in router.gitleaks_argvs if not _is_range(argv)]
        assert len(historie) == 1
        tekst = " ".join(historie[0])
        for commit in (_ORIGIN_MAIN, _ORIGIN_TAG, _HEAD):
            assert commit in tekst

    def test_annotated_tag_wordt_naar_commit_gepeeld(
        self, binary, source, config, monkeypatch
    ):
        # Een annotated tag wijst naar een tag-object; alleen het gepeelde
        # commit-ID is een bruikbaar anker. De tag stil overslaan zou de
        # historiedekking ongemerkt verkleinen.
        router = _installeer(
            monkeypatch,
            _ProcesRouter(
                binary,
                git=_Git(
                    refs=(_ORIGIN_MAIN, _TAG_OBJECT),
                    peel={_TAG_OBJECT: _ORIGIN_TAG},
                ),
            ),
        )

        resultaat = _scan_git(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.CLEAN
        historie = [argv for argv in router.gitleaks_argvs if not _is_range(argv)]
        assert len(historie) == 1
        tekst = " ".join(historie[0])
        assert _ORIGIN_TAG in tekst
        assert _TAG_OBJECT not in tekst

    def test_logopties_liggen_vast_zonder_vrije_opties(
        self, binary, source, config, router
    ):
        _scan_git(binary, source, config)

        assert len(router.gitleaks_argvs) == 2
        for argv in router.gitleaks_argvs:
            tekst = " ".join(argv)
            assert "--full-history" in tekst
            assert _LOSSE_M.search(tekst)
            for optie in _VERBODEN_LOGOPTIES:
                assert optie not in tekst


class TestFindingsBlokkeren:
    """Een finding in de range of in de historie blokkeert de gate."""

    def test_finding_in_range_blokkeert(self, binary, source, config, monkeypatch):
        _installeer(
            monkeypatch,
            _ProcesRouter(binary, range_respons=_findings_respons(_BYTES_RANGE, 1)),
        )

        resultaat = _scan_git(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.BLOCKED
        assert resultaat.code is secret_scan.ScanErrorCode.FINDINGS_PRESENT
        assert resultaat.finding_count == 1
        assert resultaat.exit_code != 0

    def test_alleen_in_historie_gevonden_secret_blokkeert(
        self, binary, source, config, monkeypatch
    ):
        # Een later verwijderd secret staat niet meer in de range, maar wel in
        # de bereikbare historie. Alleen-range scannen zou dit stil doorlaten.
        _installeer(
            monkeypatch,
            _ProcesRouter(
                binary, historie_respons=_findings_respons(_BYTES_HISTORIE, 2)
            ),
        )

        resultaat = _scan_git(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.BLOCKED
        assert resultaat.code is secret_scan.ScanErrorCode.FINDINGS_PRESENT
        assert resultaat.finding_count == 2

    def test_waarnemingen_uit_beide_scans_worden_geteld(
        self, binary, source, config, monkeypatch
    ):
        """1 + 2 = 3 waarnemingen, geen unieke-incidenttelling.

        Range en historie overlappen; hetzelfde secret kan in beide deelscans
        worden gezien. Deze assertie bewijst alleen dat beide meetellen.
        Contractaanname: één range-scan en één historie-scan.
        """
        _installeer(
            monkeypatch,
            _ProcesRouter(
                binary,
                range_respons=_findings_respons(_BYTES_RANGE, 1),
                historie_respons=_findings_respons(_BYTES_HISTORIE, 2),
            ),
        )

        resultaat = _scan_git(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.BLOCKED
        assert resultaat.finding_count == 3


class TestCommitIdentificatie:
    """Alleen expliciete, bestaande commitobjecten zijn geldige grenzen."""

    @pytest.mark.parametrize("positie", ["base", "head"])
    @pytest.mark.parametrize(
        "waarde",
        [
            pytest.param("main", id="branchnaam"),
            pytest.param("origin/main", id="remote-ref"),
            pytest.param("HEAD~1", id="revisie-expressie"),
            pytest.param("--all", id="vlag"),
            pytest.param("1a2b3c4", id="afkorting"),
            pytest.param(f"{_BASE}..{_HEAD}", id="range-injectie"),
            pytest.param("", id="leeg"),
        ],
    )
    def test_niet_hexadecimale_revisie_wordt_geweigerd(
        self, binary, source, config, router, positie, waarde
    ):
        grenzen = {"base": _BASE, "head": _HEAD} | {positie: waarde}

        resultaat = _scan_git(binary, source, config, **grenzen)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is _code("INVALID_COMMIT_ID")
        assert resultaat.exit_code != 0
        assert router.gitleaks_argvs == []

    @pytest.mark.parametrize("ontbrekend", [_BASE, _HEAD], ids=["base", "head"])
    def test_onbekend_commitobject_wordt_geweigerd(
        self, binary, source, config, monkeypatch, ontbrekend
    ):
        router = _installeer(
            monkeypatch,
            _ProcesRouter(binary, git=_Git(objecten=_ALLE_OBJECTEN - {ontbrekend})),
        )

        resultaat = _scan_git(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is _code("COMMIT_MISSING")
        assert router.gitleaks_argvs == []


class TestScopeBewijs:
    """Zonder aantoonbaar volledige checkout is er geen historiedekking."""

    def test_map_zonder_repository_wordt_geweigerd(
        self, binary, source, config, monkeypatch
    ):
        router = _installeer(
            monkeypatch, _ProcesRouter(binary, git=_Git(is_repository=False))
        )

        resultaat = _scan_git(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.SCOPE_MISSING
        assert router.gitleaks_argvs == []

    @pytest.mark.parametrize(
        "git",
        [
            pytest.param(_Git(is_shallow=True), id="shallow"),
            pytest.param(_Git(is_partial=True), id="partial-clone"),
        ],
    )
    def test_onvolledige_checkout_wordt_geweigerd(
        self, binary, source, config, monkeypatch, git
    ):
        router = _installeer(monkeypatch, _ProcesRouter(binary, git=git))

        resultaat = _scan_git(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is _code("SCOPE_INCOMPLETE")
        assert router.gitleaks_argvs == []


class TestOnvolledigeGitInvoer:
    """Partial-metadata en ontbrekende objecten blokkeren vóór de scan."""

    @pytest.mark.parametrize(
        "regel",
        [
            pytest.param("remote.upstream.promisor true", id="andere-remote-promisor"),
            pytest.param(
                "remote.fork.partialclonefilter blob:none", id="andere-remote-filter"
            ),
            pytest.param("extensions.partialclone origin", id="extensions"),
        ],
    )
    def test_partialmetadata_buiten_origin_wordt_geweigerd(
        self, binary, source, config, monkeypatch, regel
    ):
        # Alleen `remote.origin.partialclonefilter` toetsen laat elke andere
        # remote en de repository-extensie ongemoeid.
        router = _installeer(
            monkeypatch, _ProcesRouter(binary, git=_Git(config_regels=(regel,)))
        )

        resultaat = _scan_git(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is _code("SCOPE_INCOMPLETE")
        assert router.gitleaks_argvs == []

    @pytest.mark.parametrize(
        "git",
        [
            pytest.param(_Git(faalt_op="--objects"), id="ontbrekend-object"),
            pytest.param(_Git(objectrapport=()), id="leeg-objectrapport"),
        ],
    )
    def test_onvolledig_objectbereik_wordt_geweigerd(
        self, binary, source, config, monkeypatch, git
    ):
        # `rev-list --objects --missing=error` faalt zodra een bereikbaar
        # object ontbreekt; een leeg rapport bewijst evenmin volledigheid.
        router = _installeer(monkeypatch, _ProcesRouter(binary, git=git))

        resultaat = _scan_git(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is _code("SCOPE_INCOMPLETE")
        assert router.gitleaks_argvs == []

    def test_onbruikbaar_objectrapport_geeft_vaste_foutcode(
        self, binary, source, config, monkeypatch
    ):
        router = _installeer(
            monkeypatch,
            _ProcesRouter(binary, git=_Git(objectrapport=(_MARKER_GIT,))),
        )

        resultaat = _scan_git(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is _code("GIT_FAILED")
        assert router.gitleaks_argvs == []

    def test_timeout_tijdens_objectcontrole_is_fail_closed(
        self, binary, source, config, monkeypatch
    ):
        router = _installeer(
            monkeypatch,
            _ProcesRouter(
                binary,
                git=_Git(
                    faalt_op="--objects",
                    faalt_met=_Respons(
                        raises=subprocess.TimeoutExpired(cmd=["git"], timeout=1)
                    ),
                ),
            ),
        )

        resultaat = _scan_git(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.TIMEOUT
        assert router.gitleaks_argvs == []

    def test_lazy_fetch_en_replace_zijn_uit_in_elke_child(
        self, binary, source, config, router, monkeypatch
    ):
        # Het ambient-filter alleen is niet genoeg: zonder expliciete waarden
        # kan de child alsnog objecten nafetchen of replacement-refs volgen.
        monkeypatch.setenv("GIT_NO_LAZY_FETCH", "0")
        monkeypatch.setenv("GIT_DIR", "/elders/.git")
        monkeypatch.setenv("GIT_REPLACE_REF_BASE", "refs/replace-elders")

        _scan_git(binary, source, config)

        assert router.calls
        for argv, kwargs in router.calls:
            env = kwargs["env"]
            assert env.get("GIT_NO_LAZY_FETCH") == "1", argv[:3]
            assert env.get("GIT_NO_REPLACE_OBJECTS") == "1", argv[:3]
            assert "GIT_DIR" not in env, argv[:3]
            assert "GIT_REPLACE_REF_BASE" not in env, argv[:3]


class TestBereikInhoud:
    """Een leeg bereik en een ontbrekende historie zijn fouten, geen succes."""

    def test_lege_pr_range_wordt_geweigerd(self, binary, source, config, monkeypatch):
        router = _installeer(
            monkeypatch, _ProcesRouter(binary, git=_Git(range_commits=()))
        )

        resultaat = _scan_git(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is _code("EMPTY_RANGE")
        assert router.gitleaks_argvs == []

    def test_ontbrekende_canonieke_historie_wordt_geweigerd(
        self, binary, source, config, monkeypatch
    ):
        # Zonder canonieke origin-refs is er geen historie om op te steunen.
        # Stil terugvallen op alleen de range zou de gate uithollen.
        router = _installeer(
            monkeypatch,
            _ProcesRouter(binary, git=_Git(refs=(), historie_commits=())),
        )

        resultaat = _scan_git(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is _code("HISTORY_MISSING")
        assert router.gitleaks_argvs == []


class TestGitHulptool:
    """Elke storing in de voorbereiding is fail-closed, niet 'geen findings'."""

    @pytest.mark.parametrize(
        "commando", ["rev-list", "for-each-ref", "cat-file", "config"]
    )
    def test_falend_hulpcommando_start_geen_scan(
        self, binary, source, config, monkeypatch, commando
    ):
        # De exacte code mag per commando verschillen (een falende `cat-file`
        # kan terecht als ontbrekend object gelden); fail-closed is de eis.
        router = _installeer(
            monkeypatch, _ProcesRouter(binary, git=_Git(faalt_op=commando))
        )

        resultaat = _scan_git(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.ok is False
        assert resultaat.exit_code != 0
        assert router.gitleaks_argvs == []

    def test_falende_partialcheck_geeft_vaste_foutcode(
        self, binary, source, config, monkeypatch
    ):
        # Alleen exit 1 betekent "instelling niet gezet". Exit 128 is een
        # toolfout — de partial-clone-vraag is dan onbeantwoord, en dat als
        # "geen partial clone" lezen zou een onvolledige checkout doorlaten.
        _installeer(monkeypatch, _ProcesRouter(binary, git=_Git(faalt_op="config")))

        resultaat = _scan_git(binary, source, config)

        assert resultaat.code is _code("GIT_FAILED")

    def test_falende_refopsomming_geeft_vaste_foutcode(
        self, binary, source, config, monkeypatch
    ):
        _installeer(
            monkeypatch, _ProcesRouter(binary, git=_Git(faalt_op="for-each-ref"))
        )

        resultaat = _scan_git(binary, source, config)

        assert resultaat.code is _code("GIT_FAILED")

    def test_timeout_van_een_deelscan_is_fail_closed(
        self, binary, source, config, monkeypatch
    ):
        _installeer(
            monkeypatch,
            _ProcesRouter(
                binary,
                historie_respons=_Respons(
                    raises=subprocess.TimeoutExpired(
                        cmd=["gitleaks"],
                        timeout=1,
                        output=_MARKER_SECRET.encode(),
                        stderr=_MARKER_LOG.encode(),
                    )
                ),
            ),
        )

        resultaat = _scan_git(binary, source, config, timeout=1)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.TIMEOUT
        assert resultaat.ok is False


class TestUitvoergrens:
    """Git- en Gitleaks-tekst verlaat de functie niet, ook niet bij fouten."""

    @pytest.fixture(
        params=["blocked", "kapot-rapport", "lekkende-stderr", "git-fout", "exceptie"]
    )
    def scenario(self, request, binary) -> _ProcesRouter:
        lekkend = (
            f"11:20AM WRN skipping file error={_MARKER_LOG} path={_MARKER_MATCH}\n"
            f"11:20AM INF scanned ~{_BYTES_HISTORIE} bytes (0.26 KB) in 14ms\n"
            "11:20AM INF no leaks found\n"
        ).encode()
        doubles = {
            "blocked": _ProcesRouter(
                binary, range_respons=_findings_respons(_BYTES_RANGE, 2)
            ),
            "kapot-rapport": _ProcesRouter(
                binary,
                historie_respons=_Respons(
                    stdout=b"{niet-json" + _MARKER_SECRET.encode(), stderr=lekkend
                ),
            ),
            "lekkende-stderr": _ProcesRouter(
                binary, historie_respons=_Respons(stdout=b"[]", stderr=lekkend)
            ),
            "git-fout": _ProcesRouter(binary, git=_Git(faalt_op="for-each-ref")),
            "exceptie": _ProcesRouter(
                binary, historie_respons=_Respons(raises=RuntimeError(_MARKER_LOG))
            ),
        }
        return doubles[request.param]

    def test_geen_synthetische_marker_in_publieke_uitvoer(
        self, binary, source, config, monkeypatch, capsys, caplog, scenario
    ):
        _installeer(monkeypatch, scenario)

        with caplog.at_level(logging.DEBUG):
            resultaat = _scan_git(binary, source, config)

        oppervlak = _oppervlak(resultaat, capsys, caplog)
        for marker in _MARKERS:
            assert marker not in oppervlak

    def test_fouttoestand_gebruikt_uitsluitend_vaste_codes(
        self, binary, source, config, monkeypatch, scenario
    ):
        _installeer(monkeypatch, scenario)

        resultaat = _scan_git(binary, source, config)

        assert isinstance(resultaat.code, secret_scan.ScanErrorCode)
        assert isinstance(resultaat.status, secret_scan.ScanStatus)
        assert resultaat.ok is False
        assert resultaat.exit_code != 0
        assert isinstance(resultaat.finding_count, int)
        assert isinstance(resultaat.scanned_bytes, int)
