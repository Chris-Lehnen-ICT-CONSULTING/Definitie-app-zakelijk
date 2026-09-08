"""Gedragstests voor de pre-commit-entry van de staged scan (DEF-522).

De entry wordt gestart zoals pre-commit dat doet: een echt proces, zonder
argumenten, met de repository-root als werkmap. De entry leidt daaruit zelf haar
scope af, leest `.gitleaks.toml` uit die root en zoekt `gitleaks` op `PATH`. Er
wordt uitsluitend naar de publieke JSON-uitkomst gekeken; procesuitvoer komt nooit
in een faalmelding, en elke run toetst apart dat de canary-waarde niet in stdout of
stderr staat.

Drie gevallen zonder refpaar:

1. *Schoon gestaged werk* → `clean`, exitcode 0. Faalt dit, dan blokkeert de hook
   elke gewone commit.
2. *Gestagede canary* → `blocked`, nonzero. Dit is waarvoor de hook bestaat.
3. *Geen vindbare binary* → foutstatus en nonzero. `PATH` is leeg, maar alléén in
   de child van deze test; aan de host verandert niets. Een hook die zonder tool
   stil doorloopt, geeft schijnzekerheid.

**Met refpaar.** In CI draait dezelfde hook niet op een index maar op een schone
checkout met een expliciete commitrange. `pre-commit run --from-ref/--to-ref` zet
dan `PRE_COMMIT_FROM_REF` en `PRE_COMMIT_TO_REF` in de omgeving van de hook. Twee
gevallen draaien daarom door het échte `pre-commit`, met een eigen minimale
local-hookconfig (`language: system`, dus geen installatie en geen netwerk) die de
échte entry start in een origin+clone-fixture:

4. *Schone clone met refpaar* → `clean`, exitcode 0.
5. *Gecommitte canary* → `blocked`, nonzero. Die canary staat in de commit én in
   de werkboom, maar in geen enkele index. Valt de entry stil terug op de
   staged-scan, dan leest die nul bytes en geeft `error` — nooit `blocked`. Dit
   geval scheidt dus de volledige modus van een staged-terugval; welke deelscan
   de canary vindt (de range of de boomscan), staat er niet mee vast.

Drie entrycases dekken het onbruikbare refpaar: alleen `from`, alleen `to`, en een
paar dat geen commit-ID is. Alle drie draaien op een repository met *schoon
gestaged werk*, zodat een stille terugval op de staged-scan `clean` zou geven —
de vereiste nonzero kan dus niet toevallig ontstaan.

De config in de fixture is een eigen, minimale kopie (de standaardregelset van
Gitleaks); de projectconfiguratie wordt niet gelezen. `PRE_COMMIT_HOME` wijst naar
een eigen subdirectory binnen de fixture-root, zodat de cache van de host
ongemoeid blijft. Verder gelden dezelfde grenzen als in de bestaande suites:
verplichte omgeving zonder skip, verse subdirectories onder de aangewezen
fixture-root, geen `git -C`, geen uitgezette hooks en geen mutatie buiten de
fixture.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

pytestmark = [pytest.mark.acceptance]

sys.path.insert(0, str(Path(__file__).resolve().parent))

import secret_scan
import test_secret_scan_canary as canary_fixtures
import test_secret_scan_gate as gate

#: Gedeelde helpers; één canary-vorm, één isolatiebewijs, één child-omgeving.
_Omgeving = canary_fixtures._Omgeving
_Uitkomst = gate._Uitkomst
_verplicht_pad = canary_fixtures._verplicht_pad
_git_omgeving = canary_fixtures._git_omgeving
_git = canary_fixtures._git
_commit = canary_fixtures._commit
_repo_met_index = gate._repo_met_index
_origin_met_clone = gate._origin_met_clone
_diagnose = gate._diagnose
_canary = gate._canary
_canary_regel = gate._canary_regel
_CANARY_BESTAND = canary_fixtures._CANARY_BESTAND
_SCHOON_BESTAND = gate._SCHOON_BESTAND
_SCHONE_INHOUD = gate._SCHONE_INHOUD

#: Herkenbare, niet-sleutelvormige invoerwaarde voor de foutpaden; dezelfde als
#: in de gate-suite, zodat er één marker bestaat.
_MARKER = gate._MARKER

#: De entry onder test; als echt proces gestart, nooit in-process geïmporteerd.
_ENTRY = Path(__file__).resolve().parent / "secret_scan_precommit.py"

#: Ruime procesgrens; de entry hanteert zelf een vaste, kortere tooltimeout.
_ENTRY_TIMEOUT = 180

#: De naam die de entry in de repository-root verwacht.
_CONFIG_NAAM = ".gitleaks.toml"

#: De variabelen die pre-commit zet zodra `--from-ref` en `--to-ref` beide zijn
#: opgegeven. Ze komen nooit uit de hostsessie: elke test bepaalt ze expliciet.
_ENV_FROM_REF = "PRE_COMMIT_FROM_REF"
_ENV_TO_REF = "PRE_COMMIT_TO_REF"

#: Eigen cache binnen de fixture; de cache van de host blijft ongemoeid.
_ENV_PRE_COMMIT_HOME = "PRE_COMMIT_HOME"
_CACHE_NAAM = "pre-commit-home"

#: De hook uit de eigen minimale fixtureconfig, en het bestand waarin die staat.
_HOOK_ID = "def522-secret-scan"
_PRECOMMIT_CONFIG = ".pre-commit-config.yaml"

#: De drie scripts van de entry, op hun normale relatieve paden in de clone.
_ENTRY_SCRIPTS = (
    "scripts/ci/secret_scan_precommit.py",
    "scripts/ci/secret_scan_gate.py",
    "scripts/ci/secret_scan.py",
)

_PROJECT = Path(__file__).resolve().parents[2]

#: Ruime procesgrens: pre-commit start de entry, die zelf fetcht en twee keer
#: scant.
_PRECOMMIT_TIMEOUT = 300

_CLEAN = secret_scan.ScanStatus.CLEAN.value
_BLOCKED = secret_scan.ScanStatus.BLOCKED.value
_ERROR = secret_scan.ScanStatus.ERROR.value


def _pad_met_tool(binary: Path) -> str:
    """PATH waarop `gitleaks` vindbaar is; alleen voor de child, niet voor de host."""
    bestaand = os.environ.get("PATH", "")
    if not bestaand:
        return str(binary.parent)
    return os.pathsep.join([str(binary.parent), bestaand])


def _repo_met_config(omgeving: _Omgeving, naam: str, relpad: str, inhoud: str) -> Path:
    """Repo met één gestaged bestand en een eigen minimale config in de root."""
    repo, _ = _repo_met_index(omgeving, naam, relpad, inhoud)
    doel = repo / _CONFIG_NAAM
    doel.write_text(canary_fixtures._CONFIG_TOML, encoding="utf-8")
    return repo


def _entry_omgeving(pad: str, extra: dict[str, str] | None) -> dict[str, str]:
    """Child-omgeving met een expliciet refpaar; nooit een geërfd refpaar.

    Draait deze suite zelf onder een pre-commit-hook, dan staan
    `PRE_COMMIT_FROM_REF` en `PRE_COMMIT_TO_REF` al in de omgeving. Ze worden
    daarom eerst verwijderd: elke test bepaalt zelf wat de entry te zien krijgt.
    """
    kindomgeving = _git_omgeving()
    kindomgeving["PATH"] = pad
    for naam in (_ENV_FROM_REF, _ENV_TO_REF):
        kindomgeving.pop(naam, None)
    kindomgeving.update(extra or {})
    return kindomgeving


def _draai_entry(
    repo: Path, *, pad: str, verboden: str, extra: dict[str, str] | None = None
) -> _Uitkomst:
    """Start de entry vanuit `repo` zonder argumenten, zoals pre-commit dat doet.

    De controle op `verboden` gebeurt hier, zodat die waarde nooit in een
    faalmelding van pytest terechtkomt.
    """
    kindomgeving = _entry_omgeving(pad, extra)
    voltooid = subprocess.run(
        [sys.executable, str(_ENTRY)],
        cwd=str(repo),
        capture_output=True,
        check=False,
        shell=False,
        text=True,
        timeout=_ENTRY_TIMEOUT,
        env=kindomgeving,
    )
    try:
        gelezen = json.loads(voltooid.stdout)
    except ValueError:
        gelezen = None
    return _Uitkomst(
        exit_code=voltooid.returncode,
        document=gelezen if isinstance(gelezen, dict) else None,
        lekt=verboden in f"{voltooid.stdout}\n{voltooid.stderr}",
    )


@pytest.fixture
def omgeving() -> _Omgeving:
    """De verplicht aangewezen binary en fixture-root; geen default, geen skip."""
    return _Omgeving(
        binary=_verplicht_pad(canary_fixtures._ENV_BINARY, uitvoerbaar=True),
        fixture_root=_verplicht_pad(canary_fixtures._ENV_FIXTURE_ROOT),
    )


def test_schoon_gestaged_werk_geeft_clean(omgeving: _Omgeving) -> None:
    """Een gewone commit met schoon gestaged werk mag niet blokkeren."""
    repo = _repo_met_config(
        omgeving, "precommit-schoon", _SCHOON_BESTAND, _SCHONE_INHOUD
    )
    pad = _pad_met_tool(omgeving.binary)

    uitkomst = _draai_entry(repo, pad=pad, verboden=_canary())

    assert not uitkomst.lekt
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] == _CLEAN, _diagnose(uitkomst)
    assert uitkomst.document["finding_count"] == 0, _diagnose(uitkomst)
    assert uitkomst.exit_code == 0, _diagnose(uitkomst)


def test_gestagede_canary_geeft_blocked(omgeving: _Omgeving) -> None:
    """De canary staat in de index en moet de commit tegenhouden."""
    canary = _canary()
    repo = _repo_met_config(
        omgeving, "precommit-canary", _CANARY_BESTAND, _canary_regel(canary)
    )
    pad = _pad_met_tool(omgeving.binary)

    uitkomst = _draai_entry(repo, pad=pad, verboden=canary)

    assert not uitkomst.lekt, "de canary-waarde staat in de publieke uitvoer."
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] == _BLOCKED, (
        f"{_diagnose(uitkomst)} — de canary staat gestaged in de index. Een "
        "uitblijvende blokkade betekent dat de entry de index niet scant."
    )
    assert uitkomst.document["finding_count"] > 0, _diagnose(uitkomst)
    assert uitkomst.exit_code != 0, _diagnose(uitkomst)


def test_ontbrekende_tool_geeft_nonzero(omgeving: _Omgeving) -> None:
    """Zonder vindbare binary blokkeert de entry; geen stille doorgang."""
    repo = _repo_met_config(
        omgeving, "precommit-geen-tool", _SCHOON_BESTAND, _SCHONE_INHOUD
    )

    uitkomst = _draai_entry(repo, pad="", verboden=_canary())

    assert not uitkomst.lekt
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] == _ERROR, (
        f"{_diagnose(uitkomst)} — er is geen `gitleaks` op PATH, dus er is niets "
        "gescand. Een andere status zou groen geven op nul bewijs."
    )
    assert uitkomst.document["scanned_bytes"] == 0, _diagnose(uitkomst)
    assert uitkomst.exit_code != 0, _diagnose(uitkomst)


def _hook_config(entry: Path) -> str:
    """Minimale local-hookconfig die de échte entry start.

    `language: system` betekent: geen omgeving bouwen, niets downloaden. De hook
    draait altijd en krijgt geen bestandslijst, zodat het refpaar — en niets
    anders — bepaalt wat er gescand wordt.
    """
    aanroep = " ".join(shlex.quote(deel) for deel in (sys.executable, str(entry)))
    return (
        "repos:\n"
        "  - repo: local\n"
        "    hooks:\n"
        f"      - id: {_HOOK_ID}\n"
        "        name: DEF-522 secret scan\n"
        f"        entry: {aanroep}\n"
        "        language: system\n"
        "        always_run: true\n"
        "        pass_filenames: false\n"
    )


def _clone_met_hook(omgeving: _Omgeving, naam: str) -> tuple[gate._Fixture, Path]:
    """Origin met clone, de drie entryscripts, beide configs en een eigen cache.

    De scripts staan op hun normale relatieve paden in de clone, zodat de entry
    daar precies zo ligt als in een echte checkout. De cache ligt náást de clone:
    binnen de fixture-root, maar buiten de scanscope van de boomscan.
    """
    opzet = _origin_met_clone(omgeving, naam)
    for relpad in _ENTRY_SCRIPTS:
        doel = opzet.clone / relpad
        doel.parent.mkdir(parents=True, exist_ok=True)
        doel.write_text(
            (_PROJECT / relpad).read_text(encoding="utf-8"), encoding="utf-8"
        )
    (opzet.clone / _CONFIG_NAAM).write_text(
        canary_fixtures._CONFIG_TOML, encoding="utf-8"
    )
    (opzet.clone / _PRECOMMIT_CONFIG).write_text(
        _hook_config(opzet.clone / _ENTRY_SCRIPTS[0]), encoding="utf-8"
    )
    cache = opzet.clone.parent / _CACHE_NAAM
    cache.mkdir()
    return opzet, cache


def _eis_precommit() -> None:
    """pre-commit moet in deze Python bestaan; geen skip, geen installatie."""
    voltooid = subprocess.run(
        [sys.executable, "-m", "pre_commit", "--version"],
        capture_output=True,
        check=False,
        shell=False,
        text=True,
        timeout=_ENTRY_TIMEOUT,
        env=_git_omgeving(),
    )
    if voltooid.returncode != 0:
        pytest.fail(
            "pre-commit is niet beschikbaar in deze Python. Deze suite start het "
            "echte pre-commit; zij installeert niets en slaat zichzelf niet over."
        )


def _json_regel(stdout: str) -> dict | None:
    """De JSON-regel van de entry; pre-commit zet zijn eigen tekst eromheen."""
    for regel in reversed(stdout.splitlines()):
        try:
            gelezen = json.loads(regel)
        except ValueError:
            continue
        if isinstance(gelezen, dict):
            return gelezen
    return None


def _draai_precommit(
    opzet: gate._Fixture,
    omgeving: _Omgeving,
    cache: Path,
    *,
    van: str,
    naar: str,
    verboden: str,
) -> _Uitkomst:
    """Draai de hook via het échte pre-commit, met een expliciet refpaar.

    `--verbose` is nodig omdat pre-commit de uitvoer van een geslaagde hook
    anders niet toont; zonder die vlag zou het schone geval geen uitkomst hebben
    om op te toetsen. De controle op `verboden` gebeurt hier, zodat die waarde
    nooit in een faalmelding van pytest terechtkomt.
    """
    kindomgeving = _entry_omgeving(
        _pad_met_tool(omgeving.binary), {_ENV_PRE_COMMIT_HOME: str(cache)}
    )
    voltooid = subprocess.run(
        [
            sys.executable,
            "-m",
            "pre_commit",
            "run",
            _HOOK_ID,
            "--verbose",
            "--from-ref",
            van,
            "--to-ref",
            naar,
        ],
        cwd=str(opzet.clone),
        capture_output=True,
        check=False,
        shell=False,
        text=True,
        timeout=_PRECOMMIT_TIMEOUT,
        env=kindomgeving,
    )
    return _Uitkomst(
        exit_code=voltooid.returncode,
        document=_json_regel(voltooid.stdout),
        lekt=verboden in f"{voltooid.stdout}\n{voltooid.stderr}",
    )


def test_refpaar_op_schone_clone_geeft_clean(omgeving: _Omgeving) -> None:
    """Met een refpaar draait dezelfde hook de volledige scan, en die is schoon."""
    _eis_precommit()
    opzet, cache = _clone_met_hook(omgeving, "precommit-refpaar-schoon")

    uitkomst = _draai_precommit(
        opzet, omgeving, cache, van=opzet.base, naar=opzet.head, verboden=_canary()
    )

    assert not uitkomst.lekt
    assert uitkomst.document is not None, (
        f"{_diagnose(uitkomst)} — pre-commit leverde geen uitkomst van de entry. "
        "De hook bereikt de gate niet."
    )
    assert uitkomst.document["status"] == _CLEAN, _diagnose(uitkomst)
    assert uitkomst.document["scanned_bytes"] > 0, (
        f"{_diagnose(uitkomst)} — nul gescande bytes. Bij een expliciet refpaar "
        "hoort de volledige scan te draaien, niet een lege index."
    )
    assert uitkomst.exit_code == 0, _diagnose(uitkomst)


def test_refpaar_blokkeert_gecommitte_canary(omgeving: _Omgeving) -> None:
    """Een gecommitte canary buiten de index moet de gate laten blokkeren."""
    _eis_precommit()
    opzet, cache = _clone_met_hook(omgeving, "precommit-refpaar-canary")
    canary = _canary()
    head = _commit(
        opzet.clone, _CANARY_BESTAND, _canary_regel(canary), "chore: instellingen"
    )

    # Boolean vóór de assertie: de canary-waarde mag nooit in een faalmelding
    # van pytest belanden. De lege index is het discriminerende punt: een
    # staged-terugval leest daar nul bytes en geeft `error`, nooit `blocked`.
    niets_gestaged = _git(opzet.clone, "diff", "--cached", "--name-only") == ""
    assert niets_gestaged, (
        "fixturefout: er staat werk in de index, dus een staged-scan zou deze "
        "canary ook kunnen zien en er valt niets over de volledige modus te "
        "bewijzen."
    )

    uitkomst = _draai_precommit(
        opzet, omgeving, cache, van=opzet.head, naar=head, verboden=canary
    )

    assert not uitkomst.lekt, "de canary-waarde staat in de publieke uitvoer."
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] == _BLOCKED, (
        f"{_diagnose(uitkomst)} — de canary is gecommit en staat in geen enkele "
        "index, dus alleen de volledige modus kan hem zien. Een uitblijvende "
        "blokkade betekent hier dat de entry het refpaar negeert."
    )
    assert uitkomst.document["finding_count"] > 0, _diagnose(uitkomst)
    assert uitkomst.exit_code != 0, _diagnose(uitkomst)


def _alleen_van_ref(repo: Path) -> tuple[dict[str, str], str]:
    """Alleen de ondergrens; pre-commit zet er normaal altijd twee."""
    return {_ENV_FROM_REF: _git(repo, "rev-parse", "HEAD")}, _canary()


def _alleen_naar_ref(repo: Path) -> tuple[dict[str, str], str]:
    """Alleen de bovengrens; de helft van een paar is geen bereik."""
    return {_ENV_TO_REF: _git(repo, "rev-parse", "HEAD")}, _canary()


def _refpaar_zonder_commit_id(repo: Path) -> tuple[dict[str, str], str]:
    """Twee waarden die geen commit-ID zijn; die tekst mag niet terugkomen."""
    return {_ENV_FROM_REF: _MARKER, _ENV_TO_REF: _MARKER}, _MARKER


@pytest.mark.parametrize(
    "bouw",
    [
        pytest.param(_alleen_van_ref, id="alleen-from-ref"),
        pytest.param(_alleen_naar_ref, id="alleen-to-ref"),
        pytest.param(_refpaar_zonder_commit_id, id="refpaar-zonder-commit-id"),
    ],
)
def test_onbruikbaar_refpaar_geeft_nonzero(
    omgeving: _Omgeving, bouw: Callable[[Path], tuple[dict[str, str], str]]
) -> None:
    """Een half of ongeldig refpaar blokkeert; geen stille staged-terugval.

    De repository heeft schoon gestaged werk. Zou de entry bij een onbruikbaar
    refpaar terugvallen op de staged-scan, dan was de uitkomst `clean` met
    exitcode 0; de vereiste nonzero kan hier dus niet toevallig ontstaan.
    """
    repo = _repo_met_config(
        omgeving, "precommit-refpaar-fout", _SCHOON_BESTAND, _SCHONE_INHOUD
    )
    extra, verboden = bouw(repo)

    uitkomst = _draai_entry(
        repo, pad=_pad_met_tool(omgeving.binary), verboden=verboden, extra=extra
    )

    assert not uitkomst.lekt, "de ingevoerde waarde staat in de publieke uitvoer."
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] != _CLEAN, (
        f"{_diagnose(uitkomst)} — het refpaar is onbruikbaar, terwijl er schoon "
        "werk in de index staat. Een schone uitkomst betekent hier dat de entry "
        "stil op de staged-scan is teruggevallen."
    )
    assert uitkomst.exit_code != 0, _diagnose(uitkomst)
