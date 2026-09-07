"""Gedragstests voor de pre-commit-entry van de staged scan (DEF-522).

De entry wordt gestart zoals pre-commit dat doet: een echt proces, zonder
argumenten, met de repository-root als werkmap. De entry leidt daaruit zelf haar
scope af, leest `.gitleaks.toml` uit die root en zoekt `gitleaks` op `PATH`. Er
wordt uitsluitend naar de publieke JSON-uitkomst gekeken; procesuitvoer komt nooit
in een faalmelding, en elke run toetst apart dat de canary-waarde niet in stdout of
stderr staat.

Drie gevallen:

1. *Schoon gestaged werk* → `clean`, exitcode 0. Faalt dit, dan blokkeert de hook
   elke gewone commit.
2. *Gestagede canary* → `blocked`, nonzero. Dit is waarvoor de hook bestaat.
3. *Geen vindbare binary* → foutstatus en nonzero. `PATH` is leeg, maar alléén in
   de child van deze test; aan de host verandert niets. Een hook die zonder tool
   stil doorloopt, geeft schijnzekerheid.

De config in de fixture is een eigen, minimale kopie (de standaardregelset van
Gitleaks); de projectconfiguratie wordt niet gelezen. Verder gelden dezelfde
grenzen als in de bestaande suites: verplichte omgeving zonder skip, verse
subdirectories onder de aangewezen fixture-root, geen `git -C`, geen uitgezette
hooks en geen mutatie buiten de fixture.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
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
_repo_met_index = gate._repo_met_index
_diagnose = gate._diagnose
_canary = gate._canary
_canary_regel = gate._canary_regel
_CANARY_BESTAND = canary_fixtures._CANARY_BESTAND
_SCHOON_BESTAND = gate._SCHOON_BESTAND
_SCHONE_INHOUD = gate._SCHONE_INHOUD

#: De entry onder test; als echt proces gestart, nooit in-process geïmporteerd.
_ENTRY = Path(__file__).resolve().parent / "secret_scan_precommit.py"

#: Ruime procesgrens; de entry hanteert zelf een vaste, kortere tooltimeout.
_ENTRY_TIMEOUT = 180

#: De naam die de entry in de repository-root verwacht.
_CONFIG_NAAM = ".gitleaks.toml"

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


def _draai_entry(repo: Path, *, pad: str, verboden: str) -> _Uitkomst:
    """Start de entry vanuit `repo` zonder argumenten, zoals pre-commit dat doet.

    De controle op `verboden` gebeurt hier, zodat die waarde nooit in een
    faalmelding van pytest terechtkomt.
    """
    kindomgeving = _git_omgeving()
    kindomgeving["PATH"] = pad
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
