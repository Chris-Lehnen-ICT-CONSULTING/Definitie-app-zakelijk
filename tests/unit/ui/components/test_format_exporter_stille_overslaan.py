"""DEF-597, de UI-keten: een onvolledige export krijgt geen groene success.

De service meldde sinds de kernfix wél wat er overgeslagen was, maar
`FormatExporter._execute_export` toonde nog `st.success` met het *gevraagde*
aantal — exporteer 100 definities waarvan er 30 falen en het scherm zei
"✅ Export gegenereerd: 100 definitie(s)". Review 13 juli, High.
"""

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit

from services.export_service import BulkExportResult
from ui.components.tabs.import_export_beheer.format_exporter import FormatExporter


def _exporter(resultaat: BulkExportResult) -> FormatExporter:
    """FormatExporter zonder echte services; de export levert `resultaat`."""
    exporter = FormatExporter.__new__(FormatExporter)
    exporter.repository = MagicMock()
    exporter.export_service = MagicMock()
    exporter.export_service.export_multiple_definitions.return_value = resultaat
    return exporter


def _drie_definities() -> list[MagicMock]:
    return [MagicMock(), MagicMock(), MagicMock()]


def _run(exporter: FormatExporter) -> MagicMock:
    """Draai _execute_export met gemockte streamlit; geef de st-mock terug."""
    with patch("ui.components.tabs.import_export_beheer.format_exporter.st") as mock_st:
        exporter._execute_export(_drie_definities(), "CSV", "Basis", "bulk")
    return mock_st


def _meldingen(mock_calls) -> str:
    return " | ".join(str(call.args[0]) for call in mock_calls)


def test_onvolledige_export_toont_warning_met_de_echte_aantallen(tmp_path):
    bestand = tmp_path / "export.csv"
    bestand.write_text("begrip\neerste\nderde\n", encoding="utf-8")

    mock_st = _run(
        _exporter(BulkExportResult(path=str(bestand), skipped=["kapot"], exported=2))
    )

    assert (
        not mock_st.success.called
    ), "een onvolledige export mag geen groene success-melding krijgen"
    assert mock_st.warning.called
    waarschuwing = _meldingen(mock_st.warning.call_args_list)
    assert (
        "2" in waarschuwing and "3" in waarschuwing
    ), f"de warning moet 'geëxporteerd X van Y' vertellen, kreeg: {waarschuwing}"
    assert "kapot" in waarschuwing, "de gebruiker moet kunnen zien wélke ontbreken"


def test_volledige_export_toont_success_met_het_geleverde_aantal(tmp_path):
    bestand = tmp_path / "export.csv"
    bestand.write_text("begrip\na\nb\nc\n", encoding="utf-8")

    mock_st = _run(
        _exporter(BulkExportResult(path=str(bestand), skipped=[], exported=3))
    )

    assert mock_st.success.called
    assert "3" in _meldingen(mock_st.success.call_args_list)
    assert not mock_st.warning.called


def test_download_knop_meldt_het_geleverde_aantal_niet_het_gevraagde(tmp_path):
    bestand = tmp_path / "export.csv"
    bestand.write_text("begrip\neerste\nderde\n", encoding="utf-8")

    mock_st = _run(
        _exporter(BulkExportResult(path=str(bestand), skipped=["kapot"], exported=2))
    )

    label = mock_st.download_button.call_args.kwargs["label"]
    assert (
        "2" in label and "3" not in label
    ), f"download-label belooft meer dan het bestand bevat: {label!r}"
