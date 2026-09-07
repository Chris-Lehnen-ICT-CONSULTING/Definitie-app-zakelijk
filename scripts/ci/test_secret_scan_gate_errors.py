"""Foutcriteria van de gedeelde secret-gate-CLI (DEF-522).

Aanvulling op `test_secret_scan_gate.py`: dezelfde echte CLI, dezelfde helpers en
dezelfde fixture-root, maar hier uitsluitend de gevallen waarin de gate moet
weigeren. Elk geval eist naast een nonzero exitcode ook dat de tellingen op nul
blijven — een foutuitkomst mag nooit suggereren dat er iets gescand is.

De invoervalidatie is gedeeld tussen beide modi, dus de config- en scope-gevallen
draaien in de compacte staged-modus; de fetch-gevallen draaien in full, want daar
hoort de fetch. Gedekt:

1. *Ontbrekende config* → `config_missing`.
2. *Onleesbare TOML* → `config_invalid`.
3. *Geldige TOML met een onbruikbaar regexpatroon* → de tool faalt werkelijk, en
   dat wordt een foutstatus in plaats van een stille schone scan. De exacte code
   ligt hier bewust niet vast: Gitleaks kan zo'n configfout vóór of ná het
   openen van zijn rapport afbreken, wat twee verschillende, even correcte codes
   oplevert.
4. *Lege expliciete scope* → `scope_missing`. Een lege directory is geen
   werkboomroot en wordt afgekeurd vóór er iets wordt gestart.
5. *Onbereikbare origin* → `fetch_failed`, zonder terugval op een smallere scan.
   De remote wijst naar een niet-bestaand pad binnen de eigen fixture; er komt
   geen netwerk aan te pas.
6. *Conflicterende tag* → `fetch_failed`, en de lokale tag wijst na afloop nog
   naar hetzelfde commit als ervoor. Dit is het gedragsbewijs bij de refspec
   zonder `+`: een afwijkende canonieke tag mag een bestaande lokale tag niet
   overschrijven. De tag wordt alleen aangemaakt, nooit geforceerd of verwijderd.

De configpaden dragen een herkenbare marker in hun naam; die mag in geen enkele
publieke uitvoerregel terugkomen, ook niet in een diagnose over een kapot
configbestand. Verder gelden dezelfde grenzen als in de bestaande suite:
verplichte omgeving zonder skip, alleen verse subdirectories onder de aangewezen
root, geen `git -C`, geen uitgezette hooks, en geen procesuitvoer in een
faalmelding.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.acceptance]

sys.path.insert(0, str(Path(__file__).resolve().parent))

import secret_scan
import test_secret_scan_canary as canary_fixtures
import test_secret_scan_gate as gate

#: Gedeelde helpers; één canary-vorm, één CLI-runner, één isolatiebewijs.
_git = canary_fixtures._git
_verplicht_pad = canary_fixtures._verplicht_pad
_Omgeving = canary_fixtures._Omgeving
_Aanroep = gate._Aanroep
_Uitkomst = gate._Uitkomst
_draai = gate._draai
_diagnose = gate._diagnose
_canary = gate._canary
_full_argumenten = gate._full_argumenten
_staged_argumenten = gate._staged_argumenten
_nieuwe_basis = gate._nieuwe_basis
_repo_met_index = gate._repo_met_index
_origin_met_clone = gate._origin_met_clone
_SCHOON_BESTAND = gate._SCHOON_BESTAND
_SCHONE_INHOUD = gate._SCHONE_INHOUD

_ERROR = secret_scan.ScanStatus.ERROR.value

#: Herkenbare naam voor de configpaden; mag nooit in publieke uitvoer staan.
_CONFIG_MARKER = "def522-verboden-confignaam"
_CONFIG_NAAM = f"{_CONFIG_MARKER}.toml"

#: Naam binnen de fixture die met opzet nergens bestaat.
_AFWEZIG = "afwezig-in-fixture"

#: Tagnaam voor het conflictgeval; alleen aanmaken, nooit forceren of wissen.
_TAG = "v0.0.0-def522-fixture"

#: `[extend` sluit niet af, dus dit is geen leesbare TOML.
_KAPOTTE_TOML = "[extend\nuseDefault = true\n"

#: Leesbare TOML met een actieve regel, maar met een patroon dat niet compileert:
#: de haakjesgroep sluit niet. De configvalidatie laat dit door; de tool niet.
_ONBRUIKBARE_REGEX_TOML = (
    "[[rules]]\n"
    'id = "def522-fixture-onbruikbaar"\n'
    'description = "Synthetische regel met een patroon dat niet compileert."\n'
    'regex = "(?P<onafgesloten"\n'
)


def _config(basis: Path, inhoud: str) -> Path:
    """Schrijf een eigen configbestand met de gemarkeerde naam."""
    pad = basis / _CONFIG_NAAM
    pad.write_text(inhoud, encoding="utf-8")
    return pad


def _assert_fout(uitkomst: _Uitkomst, code: secret_scan.ScanErrorCode) -> None:
    """Geen clean, nonzero, precies deze vaste code, en geen tellingen."""
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] == _ERROR, _diagnose(uitkomst)
    assert uitkomst.document["code"] == code.value, _diagnose(uitkomst)
    assert uitkomst.document["finding_count"] == 0, _diagnose(uitkomst)
    assert uitkomst.document["scanned_bytes"] == 0, _diagnose(uitkomst)
    assert uitkomst.exit_code != 0, _diagnose(uitkomst)


@pytest.fixture
def omgeving() -> _Omgeving:
    """De verplicht aangewezen binary en fixture-root; geen default, geen skip."""
    return _Omgeving(
        binary=_verplicht_pad(canary_fixtures._ENV_BINARY, uitvoerbaar=True),
        fixture_root=_verplicht_pad(canary_fixtures._ENV_FIXTURE_ROOT),
    )


def test_ontbrekende_config_wordt_afgekeurd(omgeving: _Omgeving) -> None:
    """Een configpad dat niet bestaat, komt niet verder dan de validatie."""
    repo, standaard = _repo_met_index(
        omgeving, "config-weg", _SCHOON_BESTAND, _SCHONE_INHOUD
    )
    aanroep = _Aanroep(omgeving.binary, repo, standaard.parent / _CONFIG_NAAM)

    uitkomst = _draai(_staged_argumenten(aanroep), verboden=_CONFIG_MARKER)

    assert not uitkomst.lekt, "het opgegeven configpad staat in de uitvoer."
    _assert_fout(uitkomst, secret_scan.ScanErrorCode.CONFIG_MISSING)


def test_onleesbare_config_wordt_afgekeurd(omgeving: _Omgeving) -> None:
    """Een config die geen geldige TOML is, geeft config_invalid."""
    repo, standaard = _repo_met_index(
        omgeving, "config-kapot", _SCHOON_BESTAND, _SCHONE_INHOUD
    )
    config = _config(standaard.parent, _KAPOTTE_TOML)
    aanroep = _Aanroep(omgeving.binary, repo, config)

    uitkomst = _draai(_staged_argumenten(aanroep), verboden=_CONFIG_MARKER)

    assert not uitkomst.lekt, "het opgegeven configpad staat in de uitvoer."
    _assert_fout(uitkomst, secret_scan.ScanErrorCode.CONFIG_INVALID)


def test_onbruikbaar_regexpatroon_geeft_geen_schone_scan(omgeving: _Omgeving) -> None:
    """De tool faalt werkelijk op de regelset; dat wordt geen stille clean."""
    repo, standaard = _repo_met_index(
        omgeving, "regex-kapot", _SCHOON_BESTAND, _SCHONE_INHOUD
    )
    config = _config(standaard.parent, _ONBRUIKBARE_REGEX_TOML)
    aanroep = _Aanroep(omgeving.binary, repo, config)

    uitkomst = _draai(_staged_argumenten(aanroep), verboden=_CONFIG_MARKER)

    assert not uitkomst.lekt, "het opgegeven configpad staat in de uitvoer."
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] == _ERROR, (
        f"{_diagnose(uitkomst)} — de regelset compileert niet, dus er is niets "
        "gescand. Een andere status zou hier groen of rood geven op een scan "
        "die nooit heeft plaatsgevonden."
    )
    assert uitkomst.document["scanned_bytes"] == 0, _diagnose(uitkomst)
    assert uitkomst.exit_code != 0, _diagnose(uitkomst)


def test_lege_scope_wordt_afgekeurd(omgeving: _Omgeving) -> None:
    """Een lege directory is geen werkboomroot en wordt vóór elke scan geweigerd."""
    basis, standaard = _nieuwe_basis(omgeving, "scope-leeg")
    leeg = basis / "leeg"
    leeg.mkdir()
    aanroep = _Aanroep(omgeving.binary, leeg, standaard)

    uitkomst = _draai(_staged_argumenten(aanroep), verboden=_canary())

    assert not uitkomst.lekt
    _assert_fout(uitkomst, secret_scan.ScanErrorCode.SCOPE_MISSING)


def test_onbereikbare_origin_geeft_fetch_failed(omgeving: _Omgeving) -> None:
    """Zonder geslaagde fetch volgt er geen scan; er is geen smallere terugval."""
    opzet = _origin_met_clone(omgeving, "fetch-weg")
    afwezig = opzet.origin.parent / _AFWEZIG
    _git(opzet.clone, "remote", "set-url", "origin", str(afwezig))
    aanroep = _Aanroep(omgeving.binary, opzet.clone, opzet.config)
    argumenten = _full_argumenten(aanroep, opzet.base, opzet.head)

    uitkomst = _draai(argumenten, verboden=_canary())

    assert not uitkomst.lekt
    _assert_fout(uitkomst, secret_scan.ScanErrorCode.FETCH_FAILED)


def test_conflicterende_tag_blijft_staan(omgeving: _Omgeving) -> None:
    """Een afwijkende canonieke tag overschrijft de lokale tag niet."""
    opzet = _origin_met_clone(omgeving, "tag-conflict")
    # De clone dateert van vóór beide tags, dus dezelfde naam wijst lokaal en in
    # de origin naar een ander commit. Alleen aanmaken; niet forceren, niet wissen.
    _git(opzet.clone, "tag", _TAG, opzet.head)
    _git(opzet.origin, "tag", _TAG, opzet.base)
    voor = _git(opzet.clone, "rev-parse", f"{_TAG}^{{commit}}")

    aanroep = _Aanroep(omgeving.binary, opzet.clone, opzet.config)
    argumenten = _full_argumenten(aanroep, opzet.base, opzet.head)

    uitkomst = _draai(argumenten, verboden=_canary())

    na = _git(opzet.clone, "rev-parse", f"{_TAG}^{{commit}}")
    assert voor == opzet.head, "fixturefout: de lokale tag wees niet naar de head."
    assert na == voor, (
        "de lokale tag is verplaatst: de fetch overschrijft een bestaande tag "
        "met de canonieke variant."
    )
    assert not uitkomst.lekt
    _assert_fout(uitkomst, secret_scan.ScanErrorCode.FETCH_FAILED)
