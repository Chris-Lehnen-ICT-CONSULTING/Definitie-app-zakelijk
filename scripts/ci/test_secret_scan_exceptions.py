"""Canary: één uitzondering geldt alleen op exact pad én exacte inhoud (DEF-522).

De spec laat brede uitzonderingen vervallen: alleen een aantoonbaar synthetische
fixture krijgt een uitzondering, en dan met een exact pad *en* een specifiek
inhoudelijk criterium. Deze module toetst dat met de échte gepinde binary tegen
de **actuele** project-`.gitleaks.toml` — niet tegen een uitgeklede kopie, want
juist die config is wat de gate straks draait.

Drie directoryscans, elk op een eigen verse map met twee bestanden: het te
toetsen fixture-bestand, plus één onschuldig controlebestand buiten elke brede
uitzondering. Dat tweede bestand levert het scanwerk: zou de map alleen de
overgeslagen fixture bevatten, dan leest Gitleaks nul bytes en is de uitkomst
geen bewijs — de bytecontrole van de scanner wijst zo'n scan terecht af.

1. **Exact pad, bekende inhoud → CLEAN.** De aangewezen fixture mag passeren.
2. **Zelfde inhoud, ander pad → BLOCKED.** Een uitzondering die naar het pad
   verhuist, is geen uitzondering meer maar een gat.
3. **Exact pad, andere geldige sleutelstaart → BLOCKED.** Eén teken verschil,
   nog steeds binnen het base32-alfabet en de entropiedrempel. Zonder inhouds-
   criterium wordt het pad zelf een vrijbrief.

**Waarom geval 3 het scherpst is.** Een globale allowlist met `paths` wordt in
de gepinde bron toegepast als pad-skip (`sources/common.go:37-52`,
`shouldSkipPath` → `PathAllowed`): het pad gaat overboord vóórdat de inhoud
wordt bekeken, en `condition` weegt daar niet mee. Alleen met `targetRules`
hangt de uitzondering aan de regel zelf (`config/config.go:233-240`), waar
`detect.go` de AND-conditie wél eerbiedigt. Zonder die koppeling levert geval 3
stil `CLEAN` op — het pad is dan een vrijbrief voor elke waarde.

**Fixture-waarde.** Dezelfde zelf gegenereerde canary als de git-canary, hier
opnieuw in delen samengesteld zodat dit bronbestand zelf geen aaneengesloten
sleutelvorm bevat. De waarde blijft in locals: faalmeldingen tonen uitsluitend
status, code en tellingen. Er wordt niets uit `.env`, de projectdatabase of
historische blobs gelezen.

**Omgevingscontract.** Gelijk aan de git-canary: `DEF522_GITLEAKS_BINARY` en
`DEF522_FIXTURE_ROOT` zijn verplicht, ontbreken is een fout en nooit een skip.
Elke test maakt een eigen `mkdtemp`-map onder de aangewezen root en laat die
staan als bewijsmateriaal. Het echte fixture-bestand staat in de repository op
`tests/fixtures/def522_synthetic_aws.txt`; hier wordt dat pad binnen de tempmap
nagebouwd, zodat de scan hetzelfde repo-relatieve pad ziet zonder dat de
repository zelf wordt gescand.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

pytestmark = [pytest.mark.acceptance]

sys.path.insert(0, str(Path(__file__).resolve().parent))

import secret_scan
from test_secret_scan_canary import (
    _CANARY_DELEN,
    _ENV_BINARY,
    _ENV_FIXTURE_ROOT,
    _diagnose,
    _Omgeving,
    _verplicht_pad,
)

#: De actuele projectconfiguratie — bewust niet een kopie of subset.
_PROJECT_CONFIG = Path(__file__).resolve().parents[2] / ".gitleaks.toml"

#: Het pad waarop de synthetische fixture in de repository staat, en een pad dat
#: er alleen op lijkt maar buiten de uitzondering valt.
_EXACT_PAD = "tests/fixtures/def522_synthetic_aws.txt"
_AFWIJKEND_PAD = "tests/fixtures/def522_other_aws.txt"

#: De bekende staart, en een variant met één ander teken. Beide blijven binnen
#: het base32-alfabet (`A-Z2-7`) van de gepinde `aws-access-token`-regel en ver
#: boven de entropiedrempel: zestien onderling verschillende tekens.
_BEKENDE_STAART = _CANARY_DELEN[3]
_ANDERE_STAART = f"{_CANARY_DELEN[3][:-1]}C"

#: Onschuldig controlebestand in de scanroot, buiten elke brede uitzondering:
#: gewone tekst zonder sleutelwoord of toegewezen waarde.
_CONTROLE_PAD = "non_secret_scope.txt"
_CONTROLE_INHOUD = (
    "Gewone tekst voor de omvang van de scan.\n"
    "Dit bestand valt buiten elke brede uitzondering en bevat niets gevoeligs.\n"
)

_SCAN_TIMEOUT = 20


def _inhoud(staart: str) -> str:
    """Eén regel met de sleutelvorm, hier nooit aaneengesloten in de bron."""
    return f'AWS_ACCESS_KEY_ID = "{"".join(_CANARY_DELEN[:3])}{staart}"\n'


def _scanmap(omgeving: _Omgeving, naam: str, relpad: str, inhoud: str) -> Path:
    """Verse map met het toetsbestand plus het onschuldige controlebestand.

    Zonder dat tweede bestand zou een overgeslagen fixture nul gelezen bytes
    opleveren en zegt de uitkomst niets over de uitzondering zelf.
    """
    basis = Path(
        tempfile.mkdtemp(prefix=f"exception-{naam}-", dir=str(omgeving.fixture_root))
    )
    (basis / _CONTROLE_PAD).write_text(_CONTROLE_INHOUD, encoding="utf-8")
    doel = basis / relpad
    doel.parent.mkdir(parents=True, exist_ok=True)
    doel.write_text(inhoud, encoding="utf-8")
    return basis


def _scan(omgeving: _Omgeving, directory: Path, config: Path):
    return secret_scan.scan_directory(omgeving.binary, directory, config, _SCAN_TIMEOUT)


@pytest.fixture
def omgeving() -> _Omgeving:
    """De expliciet aangewezen binary en fixture-root; beide verplicht."""
    return _Omgeving(
        binary=_verplicht_pad(_ENV_BINARY, uitvoerbaar=True),
        fixture_root=_verplicht_pad(_ENV_FIXTURE_ROOT),
    )


@pytest.fixture
def projectconfig() -> Path:
    """De actuele `.gitleaks.toml` van dit project; ontbreken is een fout."""
    if not _PROJECT_CONFIG.is_file():
        pytest.fail(f"projectconfiguratie ontbreekt: {_PROJECT_CONFIG}")
    return _PROJECT_CONFIG


def test_bekende_fixture_op_exact_pad_passeert(
    omgeving: _Omgeving, projectconfig: Path
) -> None:
    """De aangewezen synthetische fixture mag als enige passeren."""
    directory = _scanmap(omgeving, "exact", _EXACT_PAD, _inhoud(_BEKENDE_STAART))

    resultaat = _scan(omgeving, directory, projectconfig)

    assert resultaat.status is secret_scan.ScanStatus.CLEAN, _diagnose(resultaat)
    assert resultaat.code is secret_scan.ScanErrorCode.OK, _diagnose(resultaat)
    assert resultaat.finding_count == 0
    # Zonder gelezen bytes is "geen findings" geen bewijs.
    assert resultaat.scanned_bytes > 0, _diagnose(resultaat)
    assert resultaat.exit_code == 0


def test_zelfde_inhoud_op_afwijkend_pad_blokkeert(
    omgeving: _Omgeving, projectconfig: Path
) -> None:
    """Dezelfde waarde op een ander pad valt buiten de uitzondering."""
    directory = _scanmap(
        omgeving, "ander-pad", _AFWIJKEND_PAD, _inhoud(_BEKENDE_STAART)
    )

    resultaat = _scan(omgeving, directory, projectconfig)

    assert resultaat.status is secret_scan.ScanStatus.BLOCKED, (
        f"{_diagnose(resultaat)} — de uitzondering geldt hier voor het hele "
        "pad-patroon in plaats van voor één exact pad, dus elk bestand op die "
        "plek mag een sleutel bevatten."
    )
    assert resultaat.code is secret_scan.ScanErrorCode.FINDINGS_PRESENT
    assert resultaat.finding_count > 0, _diagnose(resultaat)
    assert resultaat.scanned_bytes > 0, _diagnose(resultaat)
    assert resultaat.exit_code != 0


def test_afwijkende_inhoud_op_exact_pad_blokkeert(
    omgeving: _Omgeving, projectconfig: Path
) -> None:
    """Eén teken verschil is een andere waarde, ook op het juiste pad."""
    directory = _scanmap(omgeving, "andere-inhoud", _EXACT_PAD, _inhoud(_ANDERE_STAART))

    resultaat = _scan(omgeving, directory, projectconfig)

    assert resultaat.status is secret_scan.ScanStatus.BLOCKED, (
        f"{_diagnose(resultaat)} — de uitzondering toetst hier alleen het pad en "
        "niet de inhoud, dus het pad zelf is een vrijbrief voor elke sleutel."
    )
    assert resultaat.code is secret_scan.ScanErrorCode.FINDINGS_PRESENT
    assert resultaat.finding_count > 0, _diagnose(resultaat)
    assert resultaat.scanned_bytes > 0, _diagnose(resultaat)
    assert resultaat.exit_code != 0


# --- Regressie: `database-connection-string` leest niet over een regeleinde ---
#
# De regel gebruikt genegeerde tekenklassen voor gebruikersnaam en wachtwoord. In
# de regexp-engine van Go matcht zo'n klasse ook een regeleinde, en Gitleaks past
# een regel toe op de hele bestandsinhoud. Een credentialvrije URI werd daardoor
# samen met een dubbele punt en een apenstaartje op latere regels gelezen als
# "gebruiker:wachtwoord@host".
#
# De grens ligt bij het regeleinde — LF én CR — en niet bij de URI-authority.
# Binnen één regel blijft de regel bewust permissief: spatie, schuine streep,
# vraagteken, hekje, dubbele punt en apostrof komen alle voor in wachtwoorden die
# echte bibliotheken renderen of teruglezen.

#: Bouwstenen. De verbindingsreeksen worden pas tijdens de run samengesteld,
#: zodat dit bronbestand zelf geen aaneengesloten credential bevat.
_DUBBELE_PUNT = ":"
_APENSTAARTJE = "@"
_SCHUINE_STREEP = "/"

_DB_SCHEMAS = ("postgres", "mysql", "mongodb", "redis")
_DB_HOST = "db.intern.invalid"
_DB_BESTAND = "src/config/database_settings.py"
_DB_GEBRUIKER = "def522_gebruiker"
_DB_WACHTWOORD = "Zelfverzonnen1234"

#: Vormen die binnen één regel toegestaan moeten blijven.
_GEBRUIKER_PERCENT = "def522%40organisatie"
_GEBRUIKER_SPATIE = "def522 gebruiker"
_GEHEIM_PERCENT = "%2FZelfverzonnen9"
_GEHEIM_DUBBELE_PUNT = f"Zelf{_DUBBELE_PUNT}verzonnen7"
_GEHEIM_APOSTROF = "Zelf'verzonnen8"
_GEHEIM_SPATIE = "Zelf verzonnen1"
_GEHEIM_STREEP = f"Zelf{_SCHUINE_STREEP}verzonnen2"
_GEHEIM_VRAAGTEKEN = "Zelf?verzonnen3"
_GEHEIM_HEKJE = "Zelf#verzonnen4"

#: Dezelfde host met en zonder poort; de poort brengt een extra dubbele punt mee.
_DB_HOST_MET_POORT = f"{_DB_HOST}{_DUBBELE_PUNT}5432{_SCHUINE_STREEP}definities"
_DB_HOST_ZONDER_POORT = f"{_DB_HOST}{_SCHUINE_STREEP}definities"

#: (naam, host, regelscheiding) — LF en CR apart, want beide sluiten de match af.
_VERSTROOIDE_GEVALLEN = [
    ("met-poort-lf", _DB_HOST_MET_POORT, "\n"),
    ("met-poort-cr", _DB_HOST_MET_POORT, "\r"),
    ("zonder-poort-lf", _DB_HOST_ZONDER_POORT, "\n"),
    ("zonder-poort-cr", _DB_HOST_ZONDER_POORT, "\r"),
]

#: (naam, schema, gebruiker, geheim) — twaalf vormen die moeten blijven blokkeren.
_CREDENTIALVORMEN = [
    *[(schema, schema, _DB_GEBRUIKER, _DB_WACHTWOORD) for schema in _DB_SCHEMAS],
    ("percent-userinfo", "postgres", _GEBRUIKER_PERCENT, _GEHEIM_PERCENT),
    ("dubbelepunt-wachtwoord", "postgres", _DB_GEBRUIKER, _GEHEIM_DUBBELE_PUNT),
    ("apostrof-wachtwoord", "postgres", _DB_GEBRUIKER, _GEHEIM_APOSTROF),
    ("spatie-gebruikersnaam", "postgres", _GEBRUIKER_SPATIE, _DB_WACHTWOORD),
    ("spatie-wachtwoord", "postgres", _DB_GEBRUIKER, _GEHEIM_SPATIE),
    ("streep-wachtwoord", "postgres", _DB_GEBRUIKER, _GEHEIM_STREEP),
    ("vraagteken-wachtwoord", "postgres", _DB_GEBRUIKER, _GEHEIM_VRAAGTEKEN),
    ("hekje-wachtwoord", "postgres", _DB_GEBRUIKER, _GEHEIM_HEKJE),
]


def _db_uri(schema: str, gebruiker: str, geheim: str, host: str) -> str:
    """Stel een verbindingsreeks samen; lege `gebruiker` geeft een schone URI."""
    userinfo = ""
    if gebruiker:
        userinfo = f"{gebruiker}{_DUBBELE_PUNT}{geheim}{_APENSTAARTJE}"
    scheider = f"{_DUBBELE_PUNT}{_SCHUINE_STREEP}{_SCHUINE_STREEP}"
    return f"{schema}{scheider}{userinfo}{host}"


def _verstrooide_inhoud(host: str, scheiding: str) -> str:
    """Credentialvrije URI, met losse tekst op volgende regels."""
    uri = _db_uri("postgres", "", "", host)
    return scheiding.join(
        [
            f'DATABASE_URL = "{uri}"',
            "OPENINGSTIJDEN = {",
            '    "start": "08:00",',
            "}",
            f'CONTACT = "beheer{_APENSTAARTJE}voorbeeld.invalid"',
            "",
        ]
    )


def _credential_inhoud(schema: str, gebruiker: str, geheim: str) -> str:
    """Eén regel met een volledige, synthetische verbindingsreeks."""
    return f'DATABASE_URL = "{_db_uri(schema, gebruiker, geheim, _DB_HOST)}"\n'


@pytest.mark.parametrize(
    ("naam", "host", "scheiding"),
    _VERSTROOIDE_GEVALLEN,
    ids=[geval[0] for geval in _VERSTROOIDE_GEVALLEN],
)
def test_credentialvrije_uri_met_latere_tekst_passeert(
    omgeving: _Omgeving, projectconfig: Path, naam: str, host: str, scheiding: str
) -> None:
    """Binnen deze regel staat geen credential; latere regels horen er niet bij."""
    directory = _scanmap(
        omgeving, f"dburi-{naam}", _DB_BESTAND, _verstrooide_inhoud(host, scheiding)
    )

    resultaat = _scan(omgeving, directory, projectconfig)

    assert resultaat.status is secret_scan.ScanStatus.CLEAN, (
        f"{_diagnose(resultaat)} — deze verbindingsreeks bevat geen inloggegevens "
        "en het apenstaartje staat op een latere regel. Een blokkade betekent dat "
        "er over het regeleinde heen wordt doorgelezen."
    )
    assert resultaat.code is secret_scan.ScanErrorCode.OK, _diagnose(resultaat)
    assert resultaat.finding_count == 0
    assert resultaat.scanned_bytes > 0, _diagnose(resultaat)
    assert resultaat.exit_code == 0


@pytest.mark.parametrize(
    ("naam", "schema", "gebruiker", "geheim"),
    _CREDENTIALVORMEN,
    ids=[vorm[0] for vorm in _CREDENTIALVORMEN],
)
def test_credentialvorm_blijft_blokkeren(
    omgeving: _Omgeving,
    projectconfig: Path,
    naam: str,
    schema: str,
    gebruiker: str,
    geheim: str,
) -> None:
    """Elke vorm binnen één regel moet geblokkeerd blijven."""
    directory = _scanmap(
        omgeving,
        f"dbcred-{naam}",
        _DB_BESTAND,
        _credential_inhoud(schema, gebruiker, geheim),
    )

    resultaat = _scan(omgeving, directory, projectconfig)

    assert resultaat.status is secret_scan.ScanStatus.BLOCKED, (
        f"{_diagnose(resultaat)} — deze credential-vorm wordt niet geblokkeerd. "
        "Binnen één regel hoort de regel permissief te blijven; dit is een "
        "dekkingsgat."
    )
    assert resultaat.code is secret_scan.ScanErrorCode.FINDINGS_PRESENT
    assert resultaat.finding_count > 0, _diagnose(resultaat)
    assert resultaat.scanned_bytes > 0, _diagnose(resultaat)
    assert resultaat.exit_code != 0
