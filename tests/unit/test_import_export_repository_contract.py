"""Repository-contract tests voor de Import/Export-beheer UI (DEF-439).

Deze tests borgen dat CSVImporter en BulkOperations de ECHTE methodes van de
DB-laag `DefinitieRepository` aanroepen. Vóór DEF-439 riepen ze niet-bestaande
methodes aan (`find_by_begrip`, `save`, `update`) die door brede per-rij
`except`-handlers werden opgeslokt → CSV-import en bulk-statuswijziging deden
stil niets. Een `Mock(spec=DefinitieRepository)` dwingt het echte contract af:
een verkeerde methodenaam geeft `AttributeError`, waardoor de juiste methode
nooit wordt aangeroepen (RED), en na de fix wél (GREEN).
"""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from database.definitie_repository import DefinitieRecord, DefinitieRepository

pytestmark = [pytest.mark.unit]

_CSV_MODULE = "ui.components.tabs.import_export_beheer.csv_importer"
_BULK_MODULE = "ui.components.tabs.import_export_beheer.bulk_operations"


def test_csv_import_uses_db_repository_contract():
    """CSV-import gebruikt find_definitie + create_definitie (niet find_by_begrip/save)."""
    from ui.components.tabs.import_export_beheer.csv_importer import CSVImporter

    repo = Mock(spec=DefinitieRepository)
    repo.find_definitie.return_value = None  # geen duplicaat
    repo.create_definitie.return_value = 1

    importer = CSVImporter(repo)
    df = pd.DataFrame(
        [
            {
                "begrip": "Testbegrip",
                "definitie": "Een testdefinitie",
                "context": "Algemeen",
            }
        ]
    )

    with patch(f"{_CSV_MODULE}.st"):
        importer._process_import(df, skip_duplicates=True, auto_validate=False)

    repo.find_definitie.assert_called_once()
    repo.create_definitie.assert_called_once()


def test_bulk_status_change_uses_update_definitie():
    """Bulk-statuswijziging gebruikt update_definitie(id, updates) (niet update(record))."""
    from ui.components.tabs.import_export_beheer.bulk_operations import BulkOperations

    record = DefinitieRecord(begrip="X", definitie="Y")
    record.id = 5
    record.status = "concept"

    repo = Mock(spec=DefinitieRepository)
    repo.get_by_status.return_value = [record]
    repo.update_definitie.return_value = True

    bulk = BulkOperations(repo)

    with patch(f"{_BULK_MODULE}.st"):
        bulk._execute_bulk_status_change("concept", "goedgekeurd")

    repo.update_definitie.assert_called_once()
    # eerste positionele arg = definitie-id
    assert repo.update_definitie.call_args.args[0] == 5
