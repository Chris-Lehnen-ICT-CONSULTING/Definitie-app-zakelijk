"""DEF-597: een onvolledige export mag niet als geslaagd overkomen.

`_prepare_export_data` vangt élke exception per definitie en doet `continue`.
De aanroeper krijgt alleen een bestandspad terug. De logregel meldt `len(data)`
— het aantal *geslaagde* rijen, niet het aantal gevraagde. Exporteer honderd
definities waarvan er dertig falen, en het log zegt tevreden "70 definities
geëxporteerd". Het bestand mist dertig rijen en niemand weet het.

Gevonden doordat een testfixture met een kale `Mock` een geldig CSV-bestand met
nul rijen opleverde, en de export toch "slaagde".

Het doel van `continue` is goed: één corrupte definitie mag de hele export niet
opblazen. Maar stilte is de verkeerde prijs. De aanroeper moet weten wat er
ontbreekt.
"""

import csv
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

pytestmark = pytest.mark.unit

from database.definitie_repository import DefinitieRepository
from database.models import DefinitieRecord
from services.data_aggregation_service import DataAggregationService
from services.export_service import (
    DefinitieExportData,
    ExportLevel,
    ExportService,
)


def _export_data() -> DefinitieExportData:
    return DefinitieExportData(
        begrip="toezichthouder",
        definitie_origineel="origineel",
        definitie_gecorrigeerd="gecorrigeerd",
        definitie_aangepast="aangepast",
        metadata={"status": "DRAFT", "categorie": "proces"},
        context_dict={"organisatorisch": ["OM"]},
        toetsresultaten={"score": 0.85},
        voorbeeld_zinnen=["voorbeeld"],
        toelichting="toelichting",
        synoniemen="syn",
        voorkeursterm="toezichthouder",
        expert_review="Goedgekeurd",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _record(begrip: str) -> DefinitieRecord:
    return DefinitieRecord(
        begrip=begrip,
        definitie=f"definitie van {begrip}",
        categorie="proces",
        status="DRAFT",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def export_dir(tmp_path):
    d = tmp_path / "exports"
    d.mkdir()
    return d


def _service(export_dir, aggregation) -> ExportService:
    return ExportService(
        repository=Mock(spec=DefinitieRepository),
        data_aggregation_service=aggregation,
        export_dir=str(export_dir),
    )


@pytest.fixture
def een_van_de_drie_faalt(export_dir):
    """Aggregation-service die op de tweede definitie struikelt."""
    aggregation = Mock(spec=DataAggregationService)

    def zijdelings(definitie_record):
        if definitie_record.begrip == "kapot":
            raise ValueError("corrupte JSON-kolom")
        return _export_data()

    aggregation.aggregate_definitie_for_export.side_effect = zijdelings
    return _service(export_dir, aggregation)


_DRIE = [_record("eerste"), _record("kapot"), _record("derde")]


# --- Het stille verlies -------------------------------------------------------


def test_prepare_meldt_hoeveel_definities_zijn_overgeslagen(een_van_de_drie_faalt):
    """De aanroeper moet kunnen weten dat er iets ontbreekt."""
    resultaat = een_van_de_drie_faalt._prepare_export_data(_DRIE, ExportLevel.BASIS)

    assert len(resultaat) == 3, (
        "_prepare_export_data geeft nog steeds (data, fieldnames) terug; "
        "de overgeslagen definities zijn onzichtbaar voor de aanroeper"
    )
    data, _fieldnames, overgeslagen = resultaat
    assert len(data) == 2
    assert overgeslagen == [
        "kapot"
    ], f"verwachtte 'kapot' overgeslagen, kreeg {overgeslagen}"


def test_csv_export_bevat_alleen_de_geslaagde_rijen(een_van_de_drie_faalt):
    """De rijen die het wél halen, moeten er gewoon in staan."""
    pad = een_van_de_drie_faalt._export_multiple_to_csv(_DRIE, ExportLevel.BASIS)

    with open(pad, encoding="utf-8") as f:
        rijen = list(csv.DictReader(f))
    assert [r["begrip"] for r in rijen] == ["eerste", "derde"]


def test_alles_faalt_geeft_geen_stil_geslaagde_lege_export(export_dir):
    """Een kale Mock liet de export 'slagen' met nul rijen. Dat mag niet stil."""
    aggregation = Mock(spec=DataAggregationService)
    aggregation.aggregate_definitie_for_export.side_effect = RuntimeError("kapot")
    service = _service(export_dir, aggregation)

    _data, _fieldnames, overgeslagen = service._prepare_export_data(
        _DRIE, ExportLevel.BASIS
    )
    assert (
        len(overgeslagen) == 3
    ), "alle drie zijn overgeslagen; dat moet zichtbaar zijn"


# --- Wat NIET mag veranderen --------------------------------------------------


def test_een_kapotte_definitie_blaast_de_export_niet_op(een_van_de_drie_faalt):
    """De reden dat `continue` er staat, blijft geldig."""
    pad = een_van_de_drie_faalt._export_multiple_to_csv(_DRIE, ExportLevel.BASIS)
    assert pad, "de export moet een bestand opleveren, ook met één kapotte definitie"


def test_volledig_geslaagde_export_meldt_niets_overgeslagen(export_dir):
    aggregation = Mock(spec=DataAggregationService)
    aggregation.aggregate_definitie_for_export.return_value = _export_data()
    service = _service(export_dir, aggregation)

    data, _fieldnames, overgeslagen = service._prepare_export_data(
        _DRIE, ExportLevel.BASIS
    )
    assert len(data) == 3
    assert overgeslagen == []
