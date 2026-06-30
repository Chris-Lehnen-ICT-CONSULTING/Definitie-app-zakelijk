"""Hardening-tests voor de CSV-import (DEF-470).

Borgt dat de CSV-import:
- encoding-fallback toepast (utf-8 → cp1252/latin-1) i.p.v. te crashen;
- lege en te grote bestanden met een nette `ValueError` weigert;
- lege verplichte waarden (begrip/definitie) NIET stil als leeg record opslaat;
- per-rij-fouten verzamelt én logt (geen stille maskering);
- stringvelden in de service-laag begrenst op een maximale lengte.
"""

from __future__ import annotations

import io
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from database.definitie_repository import DefinitieRepository

pytestmark = [pytest.mark.unit]

_CSV_MODULE = "ui.components.tabs.import_export_beheer.csv_importer"


class _FakeUpload:
    """Minimale stand-in voor een Streamlit UploadedFile (seek/read/.size)."""

    def __init__(self, data: bytes):
        self._buf = io.BytesIO(data)
        self.size = len(data)

    def seek(self, pos: int, whence: int = 0) -> int:
        return self._buf.seek(pos, whence)

    def read(self, *args: int) -> bytes:
        return self._buf.read(*args)


def _make_importer() -> tuple[object, Mock]:
    from ui.components.tabs.import_export_beheer.csv_importer import CSVImporter

    repo = Mock(spec=DefinitieRepository)
    repo.find_definitie.return_value = None
    repo.create_definitie.return_value = 1
    return CSVImporter(repo), repo


# --------------------------------------------------------------------------- #
# Encoding-fallback + grootte-/leegcheck (_read_csv_safe)
# --------------------------------------------------------------------------- #
def test_read_csv_safe_falls_back_on_non_utf8_encoding():
    """Een latin-1/cp1252-bestand (ongeldig utf-8) moet alsnog ingelezen worden."""
    importer, _ = _make_importer()
    # "café" in latin-1 = b"caf\xe9" -> ongeldig als utf-8
    data = "begrip,definitie\ncafé,een definitie\n".encode("latin-1")
    upload = _FakeUpload(data)

    df = importer._read_csv_safe(upload)

    assert list(df.columns) == ["begrip", "definitie"]
    assert df.iloc[0]["begrip"] == "café"


def test_read_csv_safe_rejects_empty_file():
    importer, _ = _make_importer()
    with pytest.raises(ValueError, match="leeg"):
        importer._read_csv_safe(_FakeUpload(b""))


def test_read_csv_safe_rejects_oversized_file():
    importer, _ = _make_importer()
    upload = _FakeUpload(b"begrip,definitie\n")
    # forceer een grootte boven de limiet
    upload.size = 999 * 1024 * 1024
    with pytest.raises(ValueError, match="te groot"):
        importer._read_csv_safe(upload)


# --------------------------------------------------------------------------- #
# Lege verplichte waarden mogen geen leeg record worden
# --------------------------------------------------------------------------- #
def test_process_import_skips_rows_with_empty_required_values():
    """Rij met lege begrip/definitie -> geen create_definitie, wel als fout geteld."""
    importer, repo = _make_importer()
    df = pd.DataFrame(
        [
            {"begrip": "", "definitie": "Heeft definitie", "context": "Algemeen"},
            {
                "begrip": "Geldig",
                "definitie": "Geldige definitie",
                "context": "Algemeen",
            },
            {"begrip": "Mist definitie", "definitie": "", "context": "Algemeen"},
        ]
    )

    with patch(f"{_CSV_MODULE}.st"):
        importer._process_import(df, skip_duplicates=False, auto_validate=False)

    # Alleen de geldige rij wordt aangemaakt
    assert repo.create_definitie.call_count == 1


def test_process_import_handles_nan_required_values():
    """Een NaN-cel (lege CSV-waarde) telt als leeg en wordt niet opgeslagen."""
    importer, repo = _make_importer()
    df = pd.DataFrame(
        [
            {"begrip": None, "definitie": "x", "context": "Algemeen"},
            {"begrip": "Geldig", "definitie": "y", "context": "Algemeen"},
        ]
    )

    with patch(f"{_CSV_MODULE}.st"):
        importer._process_import(df, skip_duplicates=False, auto_validate=False)

    assert repo.create_definitie.call_count == 1


def test_process_import_continues_after_row_error():
    """Een fout op één rij stopt de import niet en wordt gelogd (niet stil gemaskeerd)."""
    importer, repo = _make_importer()
    repo.create_definitie.side_effect = [RuntimeError("db kapot"), 2]
    df = pd.DataFrame(
        [
            {"begrip": "Rij1", "definitie": "def1", "context": "Algemeen"},
            {"begrip": "Rij2", "definitie": "def2", "context": "Algemeen"},
        ]
    )

    with patch(f"{_CSV_MODULE}.st"), patch(f"{_CSV_MODULE}.logger") as mock_logger:
        importer._process_import(df, skip_duplicates=False, auto_validate=False)

    assert repo.create_definitie.call_count == 2
    assert mock_logger.exception.called


# --------------------------------------------------------------------------- #
# Service-laag: lengtelimiet op stringvelden
# --------------------------------------------------------------------------- #
def test_payload_to_definition_caps_both_fields():
    """Zowel begrip als definitie worden afgekapt op _MAX_FIELD_LENGTH."""
    from services.definition_import_service import (
        _MAX_FIELD_LENGTH,
        DefinitionImportService,
    )

    svc = DefinitionImportService(repository=Mock(), validation_orchestrator=Mock())
    payload = {
        "begrip": "x" * (_MAX_FIELD_LENGTH + 5000),
        "definitie": "y" * (_MAX_FIELD_LENGTH + 5000),
    }

    definition = svc._payload_to_definition(payload)

    assert len(definition.begrip) == _MAX_FIELD_LENGTH
    assert len(definition.definitie) == _MAX_FIELD_LENGTH


def test_payload_to_definition_warns_on_truncation():
    """Truncatie wordt niet stil gedaan maar gelogd als waarschuwing."""
    from services import definition_import_service as svc_mod
    from services.definition_import_service import (
        _MAX_FIELD_LENGTH,
        DefinitionImportService,
    )

    svc = DefinitionImportService(repository=Mock(), validation_orchestrator=Mock())
    payload = {"begrip": "x" * (_MAX_FIELD_LENGTH + 1), "definitie": "y"}

    with patch.object(svc_mod.logger, "warning") as mock_warning:
        svc._payload_to_definition(payload)

    assert mock_warning.called


# --------------------------------------------------------------------------- #
# CSV-bulkpad: lengtelimiet op het record dat naar de DB gaat
# --------------------------------------------------------------------------- #
def test_process_import_caps_field_length():
    """Het CSV-bulkpad kapt begrip/definitie af vóór create_definitie."""
    from ui.components.tabs.import_export_beheer.csv_importer import _MAX_FIELD_LENGTH

    importer, repo = _make_importer()
    df = pd.DataFrame(
        [
            {
                "begrip": "b" * (_MAX_FIELD_LENGTH + 100),
                "definitie": "d" * (_MAX_FIELD_LENGTH + 100),
                "context": "Algemeen",
            }
        ]
    )

    with patch(f"{_CSV_MODULE}.st"):
        importer._process_import(df, skip_duplicates=False, auto_validate=False)

    record = repo.create_definitie.call_args.args[0]
    assert len(record.begrip) == _MAX_FIELD_LENGTH
    assert len(record.definitie) == _MAX_FIELD_LENGTH


# --------------------------------------------------------------------------- #
# _cell_str helper
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, ""),
        (float("nan"), ""),
        ("  spaties  ", "spaties"),
        (123, "123"),
    ],
)
def test_cell_str_normalises(value, expected):
    from ui.components.tabs.import_export_beheer.csv_importer import _cell_str

    assert _cell_str(value) == expected
