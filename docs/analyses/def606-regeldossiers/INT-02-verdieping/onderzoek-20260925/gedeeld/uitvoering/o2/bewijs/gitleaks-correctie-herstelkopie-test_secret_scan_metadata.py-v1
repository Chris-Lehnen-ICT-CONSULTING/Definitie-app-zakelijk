"""Canary: de uitzondering voor vier metadataregels in `.gitleaksignore`.

Naast de synthetische AWS-fixture kent de projectconfiguratie één andere
uitzondering (DEF-522). Vier regels in `.gitleaksignore` staan in de
legacy-notatie `pad:regel-ID:commit-ID`; de drie 40-hex staarten zijn
geverifieerde Git-commitobjecten, geen sleutels. Dat is niet het
fingerprintformaat dat de gepinde Gitleaks nu schrijft, en over die
formaatgeldigheid of over intrekking van sleutels doet deze module geen uitspraak.

De uitzondering hangt aan één regel-ID (`generic-api-key`), één exact pad en vier
volledige, verankerde regels. Alles daarbuiten moet blijven blokkeren: dezelfde
regel op een ander pad, een gewijzigde commit-staart, extra tekst achter de
regel, en een echte sleutelvorm in hetzelfde bestand. De historische gevallen
tellen het zwaarst, want daar staan de werkelijke bevindingen.

Twee dingen liggen vast omdat ze uit de gepinde bron volgen:

* `regexTarget = "line"` krijgt bij elke regel ná de eerste het voorafgaande
  regeleinde mee (`detect/location.go:45` en `:54` zetten `startLineIndex` op de
  vorige newline zonder er 1 bij op te tellen; `detect/detect.go:496` snijdt
  daarmee `finding.Line` en `:520-521` geeft die snede door als `currentLine`).
  De regexes verdragen daarom precies één optionele leidende LF, meer niet.
* `.gitleaksignore` in de werkboom wordt altijd ingelezen (`cmd/root.go:317-320`)
  en een onbruikbare regel daarin geeft een waarschuwing (`detect.go:188`), wat
  voor deze fail-closed scanner een onvolledige scan is. De Git-fixture schrijft
  daarom geldig commentaar op dat pad.

Waarden worden tijdens de run samengesteld, de sleutelcanary is synthetisch, en
faalmeldingen tonen uitsluitend status, code en tellingen.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.acceptance]

sys.path.insert(0, str(Path(__file__).resolve().parent))

import secret_scan
from test_secret_scan_canary import (
    _ENV_BINARY,
    _ENV_FIXTURE_ROOT,
    _ORIGIN_REF,
    _commit,
    _diagnose,
    _git,
    _nieuwe_fixture,
    _Omgeving,
    _scan as _git_scan,
    _verplicht_pad,
)
from test_secret_scan_exceptions import _scanmap

#: De actuele projectconfiguratie — bewust niet een kopie of subset.
_PROJECT_CONFIG = Path(__file__).resolve().parents[2] / ".gitleaks.toml"

_SCAN_TIMEOUT = 20

#: Het exacte pad waarop de uitzondering geldt, een pad dat er alleen op lijkt,
#: en het pad van de configuratie zelf.
_IGNORE_PAD = ".gitleaksignore"
_ANDER_PAD = "docs/technisch/def522_ignore_kopie.txt"
_CONFIG_NAAM = ".gitleaks.toml"

#: Losse onderdelen; de metadataregels worden tijdens de run samengesteld.
_REGEL_GENERIC = "generic-api-key"
_REGEL_OPENAI = "openai-api-key-new-format"
_SLEUTELNAAM_YAML = "openai" + "_api_key"

_COMMIT_A = "0b706cc1e0a4be76782d0f0c505f99bb74072368"
_COMMIT_B = "5a61be55d691c1e35a6a95c89f56f82f10feb83a"
_COMMIT_C = "5f02ab5a2c28c2df8ac9fd9c85a48e6eb78a517a"

_PAD_YAML = "config/config_development.yaml"
_PAD_MASTERPLAN = "docs/portal/rendered/analyses/CONFIG_ENVIRONMENT_MASTERPLAN.html"
_PAD_VERIFICATIE = (
    "docs/portal/rendered/analyses/CONFIG_ENVIRONMENT_VERIFICATION_REPORT.html"
)
_PAD_LOGGING = "docs/portal/rendered/architectuur/structured-logging-architecture.html"

#: Nieuw gegenereerde synthetische waarde; hoort bij geen enkele account en gaat
#: nergens heen. In delen geschreven, zodat dit bestand zelf geen aaneengesloten
#: sleutelvorm bevat.
_SYNTHETISCHE_SLEUTEL = "Xq7" + "Lm2Rt9Vb4Nz6Pw1Kd8Hs3Jf5Gy0Cx" + "Ae7Uo4Ir"

#: Inhoud voor de Git-fixture. De vervanging is een commentaarregel: kale tekst
#: op dit pad levert een waarschuwing op en dus een onvolledige scan.
_BASIS_TEKST = "Gewone tekst zonder sleutels of verwijzingen.\n"
_ONSCHULDIG_COMMENTAAR = f"# {_BASIS_TEKST}"


def _metaregel(pad: str, sleutel: str, commit: str) -> str:
    """Eén regel in de legacy-notatie: pad, regel-ID en commit-ID."""
    return f"{pad}:{sleutel}:{commit}"


def _mutatie(commit: str) -> str:
    """Eén ander teken in de staart; blijft hexadecimaal en even lang."""
    return commit[:-1] + ("0" if commit[-1] != "0" else "1")


#: (naam, regel) — de vier regels die onder de uitzondering vallen.
_METAGEVALLEN = [
    ("yaml", _metaregel(_PAD_YAML, _SLEUTELNAAM_YAML, _COMMIT_A)),
    ("masterplan", _metaregel(_PAD_MASTERPLAN, _REGEL_OPENAI, _COMMIT_B)),
    ("verificatie", _metaregel(_PAD_VERIFICATIE, _REGEL_GENERIC, _COMMIT_B)),
    ("logging", _metaregel(_PAD_LOGGING, _REGEL_GENERIC, _COMMIT_C)),
]
_METAREGELS = [regel for _, regel in _METAGEVALLEN]

#: (naam, regel) — dezelfde paden met één ander teken in de commit-staart.
_GEWIJZIGDE_GEVALLEN = [
    ("commit-a", _metaregel(_PAD_YAML, _SLEUTELNAAM_YAML, _mutatie(_COMMIT_A))),
    ("commit-b", _metaregel(_PAD_VERIFICATIE, _REGEL_GENERIC, _mutatie(_COMMIT_B))),
    ("commit-c", _metaregel(_PAD_LOGGING, _REGEL_GENERIC, _mutatie(_COMMIT_C))),
]
_GEWIJZIGDE_REGELS = [regel for _, regel in _GEWIJZIGDE_GEVALLEN]


def _inhoud(regels: list[str]) -> str:
    return "".join(f"{regel}\n" for regel in regels)


def _scan(omgeving: _Omgeving, directory: Path):
    return secret_scan.scan_directory(
        omgeving.binary, directory, _PROJECT_CONFIG, _SCAN_TIMEOUT
    )


def _historie(omgeving: _Omgeving, naam: str, regels: list[str]):
    """Verse repo: basis, de regels vastleggen, daarna vervangen door commentaar.

    Het bestand blijft bestaan; alleen de inhoud verandert. De regels staan
    daarna nog in de historie en niet meer in de werkkopie — precies het beeld
    waar de uitzondering voor bedoeld is.
    """
    repo, _ = _nieuwe_fixture(omgeving, naam)
    base = _commit(repo, "README.md", _BASIS_TEKST, "chore: basis")
    _commit(repo, _IGNORE_PAD, _inhoud(regels), "chore: regels vastleggen")
    head = _commit(repo, _IGNORE_PAD, _ONSCHULDIG_COMMENTAAR, "chore: vervangen")
    _git(repo, "update-ref", _ORIGIN_REF, head)
    return repo, base, head


def _eis_schoon(resultaat, toelichting: str) -> None:
    """Schoon telt alleen met gelezen bytes; anders bewijst het niets."""
    assert (
        resultaat.status is secret_scan.ScanStatus.CLEAN
    ), f"{_diagnose(resultaat)} — {toelichting}"
    assert resultaat.code is secret_scan.ScanErrorCode.OK, _diagnose(resultaat)
    assert resultaat.finding_count == 0
    assert resultaat.scanned_bytes > 0, _diagnose(resultaat)
    assert resultaat.exit_code == 0


def _eis_geblokkeerd(resultaat, toelichting: str) -> None:
    assert (
        resultaat.status is secret_scan.ScanStatus.BLOCKED
    ), f"{_diagnose(resultaat)} — {toelichting}"
    assert resultaat.code is secret_scan.ScanErrorCode.FINDINGS_PRESENT
    assert resultaat.finding_count > 0, _diagnose(resultaat)
    assert resultaat.scanned_bytes > 0, _diagnose(resultaat)
    assert resultaat.exit_code != 0


@pytest.fixture
def omgeving() -> _Omgeving:
    """De expliciet aangewezen binary en fixture-root; beide verplicht."""
    return _Omgeving(
        binary=_verplicht_pad(_ENV_BINARY, uitvoerbaar=True),
        fixture_root=_verplicht_pad(_ENV_FIXTURE_ROOT),
    )


def test_vier_metaregels_op_exact_pad_passeren(omgeving: _Omgeving) -> None:
    """Waar de uitzondering voor is: deze vier regels, op dit ene pad."""
    directory = _scanmap(omgeving, "meta-exact", _IGNORE_PAD, _inhoud(_METAREGELS))

    _eis_schoon(
        _scan(omgeving, directory),
        "de vier metadataregels worden op hun eigen pad niet doorgelaten.",
    )


@pytest.mark.parametrize(
    ("naam", "regel"), _METAGEVALLEN, ids=[naam for naam, _ in _METAGEVALLEN]
)
def test_metaregel_op_ander_pad_blokkeert(
    omgeving: _Omgeving, naam: str, regel: str
) -> None:
    """Een uitzondering die naar een ander pad verhuist, is geen uitzondering."""
    directory = _scanmap(
        omgeving, f"meta-anderpad-{naam}", _ANDER_PAD, _inhoud([regel])
    )

    _eis_geblokkeerd(
        _scan(omgeving, directory),
        "dezelfde regel buiten .gitleaksignore wordt doorgelaten; de "
        "uitzondering hangt dan niet aan dat ene pad.",
    )


@pytest.mark.parametrize(
    ("naam", "regel"),
    _GEWIJZIGDE_GEVALLEN,
    ids=[naam for naam, _ in _GEWIJZIGDE_GEVALLEN],
)
def test_gewijzigde_commitstaart_blokkeert(
    omgeving: _Omgeving, naam: str, regel: str
) -> None:
    """Eén teken verschil is een andere regel, ook op het juiste pad."""
    directory = _scanmap(
        omgeving, f"meta-mutatie-{naam}", _IGNORE_PAD, _inhoud([regel])
    )

    _eis_geblokkeerd(
        _scan(omgeving, directory),
        "een gewijzigde commit-staart wordt doorgelaten; de uitzondering "
        "toetst dan niet de volledige regel.",
    )


def test_metaregel_met_extra_tekst_blokkeert(omgeving: _Omgeving) -> None:
    """De uitzondering geldt voor de hele regel, niet voor een beginstuk ervan."""
    regel = f"{_METAREGELS[0]} extra tekst"
    directory = _scanmap(omgeving, "meta-staart", _IGNORE_PAD, _inhoud([regel]))

    _eis_geblokkeerd(
        _scan(omgeving, directory),
        "een regel met extra tekst erachter wordt doorgelaten; de uitzondering "
        "is dan een prefix-uitzondering.",
    )


def test_synthetische_sleutel_naast_metaregels_blokkeert(omgeving: _Omgeving) -> None:
    """Het pad zelf mag geen vrijbrief worden voor een echte sleutelvorm."""
    inhoud = _inhoud(_METAREGELS) + f'api_key = "{_SYNTHETISCHE_SLEUTEL}"\n'
    directory = _scanmap(omgeving, "meta-canary", _IGNORE_PAD, inhoud)

    _eis_geblokkeerd(
        _scan(omgeving, directory),
        "een synthetische sleutel in hetzelfde bestand wordt doorgelaten; het "
        "pad is dan een vrijbrief in plaats van vier exacte regels.",
    )


def test_projectconfig_blokkeert_zichzelf_niet(omgeving: _Omgeving) -> None:
    """De uitzondering bevat de regels die ze doorlaat, dus ook hun staarten.

    Staat zo'n staart aaneengesloten in de configuratie, dan blokkeert de gate
    haar eigen configbestand. Het eerste hexteken staat daarom als tekenklasse
    geschreven, net als bij de bestaande AWS-fixture.
    """
    directory = _scanmap(
        omgeving,
        "meta-eigenconfig",
        _CONFIG_NAAM,
        _PROJECT_CONFIG.read_text(encoding="utf-8"),
    )

    _eis_schoon(
        _scan(omgeving, directory),
        "de configuratie blokkeert haar eigen tekst.",
    )


def test_historische_metaregels_passeren(omgeving: _Omgeving) -> None:
    """Het bereik dat er werkelijk toe doet: de historie, niet de werkkopie."""
    repo, base, head = _historie(omgeving, "meta-historie", _METAREGELS)

    huidige = (repo / _IGNORE_PAD).read_text(encoding="utf-8")
    uit_werkkopie = all(regel not in huidige for regel in _METAREGELS)
    assert uit_werkkopie, (
        "fixturefout: de regels staan nog in de werkkopie, dus deze test bewijst "
        "niets over historisch bereik."
    )

    _eis_schoon(
        _git_scan(omgeving, repo, _PROJECT_CONFIG, base, head),
        "de vier regels worden in de historie niet doorgelaten, terwijl daar de "
        "werkelijke bevindingen staan.",
    )


def test_historische_gewijzigde_staart_blokkeert(omgeving: _Omgeving) -> None:
    """Dezelfde historie met een gewijzigde staart moet wél blijven blokkeren."""
    repo, base, head = _historie(omgeving, "meta-historie-mutatie", _GEWIJZIGDE_REGELS)

    _eis_geblokkeerd(
        _git_scan(omgeving, repo, _PROJECT_CONFIG, base, head),
        "een gewijzigde commit-staart passeert in de historie; de uitzondering "
        "dekt daar dan meer dan de vier vastgelegde regels.",
    )
