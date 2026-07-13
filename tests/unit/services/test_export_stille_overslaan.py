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
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

pytestmark = pytest.mark.unit

from database.definitie_repository import DefinitieRepository
from database.models import DefinitieRecord
from services.data_aggregation_service import DataAggregationService
from services.export_service import (
    DefinitieExportData,
    ExportFormat,
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


def _drie() -> list[DefinitieRecord]:
    return [_record("eerste"), _record("kapot"), _record("derde")]


# --- Het stille verlies -------------------------------------------------------


def test_prepare_meldt_hoeveel_definities_zijn_overgeslagen(een_van_de_drie_faalt):
    """De aanroeper moet kunnen weten dat er iets ontbreekt."""
    resultaat = een_van_de_drie_faalt._prepare_export_data(_drie(), ExportLevel.BASIS)

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
    """De rijen die het wél halen, moeten er gewoon in staan.

    Via de publieke API, zodat de format-dispatch gratis meegetest wordt.
    """
    pad = een_van_de_drie_faalt.export_multiple_definitions(
        _drie(), ExportFormat.CSV, ExportLevel.BASIS
    )

    with open(pad, encoding="utf-8") as f:
        rijen = list(csv.DictReader(f))
    assert [r["begrip"] for r in rijen] == ["eerste", "derde"]


def test_alles_faalt_geeft_geen_stil_geslaagde_lege_export(export_dir):
    """Een kale Mock liet de export 'slagen' met nul rijen. Dat mag niet stil."""
    aggregation = Mock(spec=DataAggregationService)
    aggregation.aggregate_definitie_for_export.side_effect = RuntimeError("kapot")
    service = _service(export_dir, aggregation)

    _data, _fieldnames, overgeslagen = service._prepare_export_data(
        _drie(), ExportLevel.BASIS
    )
    assert (
        len(overgeslagen) == 3
    ), "alle drie zijn overgeslagen; dat moet zichtbaar zijn"


# --- Wat NIET mag veranderen --------------------------------------------------


def test_een_kapotte_definitie_blaast_de_export_niet_op(een_van_de_drie_faalt):
    """De reden dat `continue` er staat, blijft geldig."""
    pad = een_van_de_drie_faalt._export_multiple_to_csv(_drie(), ExportLevel.BASIS)
    assert pad, "de export moet een bestand opleveren, ook met één kapotte definitie"


def test_volledig_geslaagde_export_meldt_niets_overgeslagen(export_dir):
    aggregation = Mock(spec=DataAggregationService)
    aggregation.aggregate_definitie_for_export.return_value = _export_data()
    service = _service(export_dir, aggregation)

    data, _fieldnames, overgeslagen = service._prepare_export_data(
        _drie(), ExportLevel.BASIS
    )
    assert len(data) == 3
    assert overgeslagen == []


# --- De zichtbaarheidsketen zelf ------------------------------------------------
#
# Sabotage-analyse (review 13 juli): het 3-tuple-contract dwingt sinks tot
# ontvángen, niet tot dóórgeven. Zonder de tests hieronder blijft de suite
# groen als iemand `_log_export_result` uit één sink haalt, WARNING terugdraait
# naar INFO, of het JSON-veld/de TXT-regel schrapt — precies de stilte die
# DEF-597 verbiedt.


_SINKS = [
    "_export_multiple_to_csv",
    "_export_multiple_to_excel",
    "_export_multiple_to_json",
    "_export_multiple_to_txt",
]


@pytest.mark.parametrize("sink", _SINKS)
def test_elke_sink_meldt_de_overgeslagen_begrippen(een_van_de_drie_faalt, sink):
    """Voor CSV en Excel is de melding het énige onvolledigheidssignaal."""
    with patch.object(een_van_de_drie_faalt, "_log_export_result") as spy:
        getattr(een_van_de_drie_faalt, sink)(_drie(), ExportLevel.BASIS)

    spy.assert_called_once()
    assert spy.call_args.args[1] == [
        "kapot"
    ], f"{sink} geeft de overgeslagen begrippen niet door aan de melding"


def test_onvolledige_export_is_een_warning_volledige_een_info(export_dir, caplog):
    """De severity ís de feature: INFO verdwijnt in de ruis."""
    service = _service(export_dir, Mock(spec=DataAggregationService))
    pad = export_dir / "x.csv"

    with caplog.at_level(logging.INFO):
        service._log_export_result([{}], ["kapot"], "CSV", ExportLevel.BASIS, pad)
        service._log_export_result([{}], [], "CSV", ExportLevel.BASIS, pad)

    onvolledig, volledig = caplog.records
    assert onvolledig.levelno == logging.WARNING
    assert "kapot" in onvolledig.getMessage()
    assert volledig.levelno == logging.INFO


def test_json_export_info_benoemt_de_overgeslagen_definities(een_van_de_drie_faalt):
    """Het machine-leesbare contract: de export vertelt zélf wat er mist."""
    pad = een_van_de_drie_faalt._export_multiple_to_json(_drie(), ExportLevel.BASIS)

    with open(pad, encoding="utf-8") as f:
        inhoud = json.load(f)
    assert inhoud["export_info"]["skipped_definitions"] == ["kapot"]
    assert inhoud["export_info"]["total_definitions"] == 2


def test_txt_header_waarschuwt_alleen_bij_overgeslagen_definities(
    een_van_de_drie_faalt, export_dir
):
    pad = een_van_de_drie_faalt._export_multiple_to_txt(_drie(), ExportLevel.BASIS)
    header = Path(pad).read_text(encoding="utf-8").split("-" * 80)[0]
    assert "LET OP" in header and "kapot" in header

    alles_goed = _service(export_dir, Mock(spec=DataAggregationService))
    alles_goed.data_aggregation_service.aggregate_definitie_for_export.return_value = (
        _export_data()
    )
    pad = alles_goed._export_multiple_to_txt(_drie(), ExportLevel.BASIS)
    assert "LET OP" not in Path(pad).read_text(
        encoding="utf-8"
    ), "vals alarm is de spiegelregressie"


# --- Injectie via het begrip (security-review 13 juli) --------------------------


def test_melding_en_txt_header_zijn_immuun_voor_control_chars_in_begrip(
    export_dir, caplog
):
    """Een begrip met newline/ANSI mag geen logregels of TXT-header vervalsen.

    DEF-553 valideert het begrip alleen op het generatiepad; de CLI en de
    edit-tab kunnen control-tekens in de database krijgen. De export mag die
    nooit rauw doorgeven aan het log of de bestandsheader (CWE-117).
    """
    boos = "Zaak\n2026-01-01 - INFO - 100 definities geëxporteerd\x1b[2K"
    aggregation = Mock(spec=DataAggregationService)
    aggregation.aggregate_definitie_for_export.side_effect = ValueError("kapot")
    service = _service(export_dir, aggregation)

    with caplog.at_level(logging.WARNING):
        pad = service._export_multiple_to_txt([_record(boos)], ExportLevel.BASIS)

    for record in caplog.records:
        boodschap = record.getMessage()
        assert (
            "\n" not in boodschap and "\x1b" not in boodschap
        ), f"logregel bevat rauwe control-tekens: {boodschap!r}"

    header = Path(pad).read_text(encoding="utf-8").split("-" * 80)[0]
    regels_met_let_op = [r for r in header.splitlines() if "LET OP" in r]
    assert len(regels_met_let_op) == 1
    assert "\x1b" not in header
    assert (
        "geëxporteerd" in regels_met_let_op[0]
    ), "het hele (gesaneerde) begrip hoort op de LET OP-regel zelf te staan"
