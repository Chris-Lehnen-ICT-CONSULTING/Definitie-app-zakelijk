"""DEF-594: path traversal via het `begrip` in de exportbestandsnaam.

`_export_to_csv` en `_export_to_json` bouwen de bestandsnaam uit het begrip:

    begrip_clean = export_data.begrip.replace(" ", "_").lower()
    bestandsnaam = f"definitie_{begrip_clean}_{tijdstempel}.csv"
    pad = self.export_dir / bestandsnaam

`Path("/exports") / "definitie_../../../tmp/pwned_...csv"` resolvet naar
`/tmp/pwned_...csv` — buiten de exportmap. Een begrip is vrije invoer, dus dit
is arbitrary file write (begrensd tot de extensie en het tijdstempel-achtervoegsel).

Gevonden terwijl DEF-593 (formula injection) getest werd: een testpayload met een
`/` erin liet de export met een FileNotFoundError klappen, omdat hij naar een
niet-bestaande submap schreef.
"""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

pytestmark = pytest.mark.unit

from database.definitie_repository import DefinitieRepository
from services.data_aggregation_service import DataAggregationService
from services.export_service import DefinitieExportData, ExportService

_TRAVERSAL = "../../../tmp/pwned"


@pytest.fixture
def export_dir(tmp_path):
    d = tmp_path / "exports"
    d.mkdir()
    return d


@pytest.fixture
def service(export_dir):
    return ExportService(
        repository=Mock(spec=DefinitieRepository),
        data_aggregation_service=Mock(spec=DataAggregationService),
        export_dir=str(export_dir),
    )


def _export_data(begrip: str) -> DefinitieExportData:
    return DefinitieExportData(
        begrip=begrip,
        definitie_origineel="origineel",
        definitie_gecorrigeerd="gecorrigeerd",
        definitie_aangepast="aangepast",
        metadata={"status": "DRAFT", "categorie": "proces"},
        context_dict={"organisatorisch": ["OM"]},
        toetsresultaten={"score": 0.85},
        voorbeeld_zinnen=["voorbeeld"],
        toelichting="toelichting",
        synoniemen="syn",
        voorkeursterm=begrip,
        expert_review="Goedgekeurd",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.mark.parametrize("exporteer", ["_export_to_csv", "_export_to_json"])
def test_traversal_in_begrip_schrijft_niet_buiten_de_exportmap(
    service, export_dir, exporteer
):
    """De kern: het geschreven bestand moet binnen `export_dir` blijven."""
    pad = Path(getattr(service, exporteer)(_export_data(_TRAVERSAL))).resolve()

    assert pad.is_file(), f"geen bestand geschreven: {pad}"
    assert (
        pad.parent == export_dir.resolve()
    ), f"export ontsnapte uit de exportmap: {pad} ligt niet in {export_dir}"


@pytest.mark.parametrize("exporteer", ["_export_to_csv", "_export_to_json"])
def test_slash_in_begrip_maakt_geen_submap(service, export_dir, exporteer):
    pad = Path(getattr(service, exporteer)(_export_data("a/b/c"))).resolve()
    assert pad.parent == export_dir.resolve()
    assert "/" not in pad.name.replace(str(export_dir), "")


def test_bestandsnaam_bevat_geen_gevaarlijke_tekens(service):
    pad = Path(service._export_to_csv(_export_data('=HYPERLINK("http://x")')))
    naam = pad.name
    for teken in ("/", "\\", "..", '"', "="):
        assert teken not in naam, f"{teken!r} zit nog in de bestandsnaam: {naam}"


@pytest.mark.parametrize("begrip", ["///", "", "   ", "___"])
def test_begrip_dat_wegvalt_geeft_nog_steeds_een_geldige_naam(
    service, export_dir, begrip
):
    """Een begrip dat volledig wegvalt mag geen bestand zonder naam opleveren."""
    pad = Path(service._export_to_csv(_export_data(begrip)))
    assert pad.is_file()
    assert pad.parent.resolve() == export_dir.resolve()
    assert pad.name.startswith("definitie_")


def test_normaal_begrip_blijft_leesbaar_in_de_bestandsnaam(service):
    """De naam moet bruikbaar blijven — hardening mag niet alles wegvagen."""
    pad = Path(service._export_to_csv(_export_data("toezichthouder bestuursrecht")))
    assert "toezichthouder_bestuursrecht" in pad.name


@pytest.mark.parametrize(
    ("begrip", "verwacht"),
    [
        ("privé", "prive"),
        ("coöperatie", "cooperatie"),
        ("reëel", "reeel"),
        ("naïef", "naief"),
    ],
)
def test_nederlandse_accenten_worden_getranslitereerd(service, begrip, verwacht):
    """Dit is een Nederlandstalige juridische app.

    Een whitelist op `[a-z0-9_-]` alléén zou `privé` tot `priv` reduceren en
    `coöperatie` tot `co_peratie`. NFKD splitst het accent van de basisletter,
    zodat de bestandsnaam herkenbaar blijft.
    """
    pad = Path(service._export_to_csv(_export_data(begrip)))
    assert verwacht in pad.name, f"{begrip!r} werd {pad.name!r}"


def test_slug_eindigt_nooit_op_een_underscore(service):
    """Afkappen vóór strippen; anders levert de lengtecap een trailing `_`."""
    lang = "a" * 58 + " " + "b" * 20
    pad = Path(service._export_to_csv(_export_data(lang)))
    kern = pad.name.split("definitie_", 1)[1].rsplit("_", 1)[0]
    assert not kern.endswith("_"), f"slug eindigt op underscore: {kern!r}"
