"""DEF-751 B1 — CSV-import zonder/ongeldige categorie: geen default, geen crash.

Op een échte tijdelijke SQLite-database (schema-CHECK actief). Vóór B1 kreeg
een rij zonder categorie stil ``"Type"`` mee, wat op de CHECK strandde met
een cryptische ``CHECK constraint failed``-melding; ``"entiteit"`` idem.
Nu meldt de import precies wat er aan de hand is — een technische
opslagbeperking van het bestaande schema, géén inhoudelijk oordeel over de
definitie — verzint geen type/proces, en bewaart geldige waarden exact.
"""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from database.definitie_repository import DefinitieRepository
from ui.components.tabs.import_export_beheer.csv_importer import CSVImporter

pytestmark = [pytest.mark.unit]

_CSV_MODULE = "ui.components.tabs.import_export_beheer.csv_importer"


@pytest.fixture
def repo(tmp_path) -> DefinitieRepository:
    return DefinitieRepository(str(tmp_path / "import.db"))


def _importeer(
    repo: DefinitieRepository, rijen: list[dict]
) -> tuple[MagicMock, dict[str, str]]:
    """Voer de import uit; geef `st` en de door de import toegevoegde rijen."""
    vooraf = _alle_rijen(repo)  # schema.sql seedt twee voorbeeldrecords
    m = MagicMock()
    with patch(f"{_CSV_MODULE}.st", m):
        CSVImporter(repo)._process_import(
            pd.DataFrame(rijen), skip_duplicates=False, auto_validate=False
        )
    toegevoegd = {k: v for k, v in _alle_rijen(repo).items() if k not in vooraf}
    return m, toegevoegd


def _fouten(m: MagicMock) -> list[str]:
    return [str(c.args[0]) for c in m.error.call_args_list]


def _alle_rijen(repo: DefinitieRepository) -> dict[str, str]:
    with sqlite3.connect(repo.db_path) as conn:
        rijen = conn.execute("SELECT begrip, categorie FROM definities ORDER BY id")
        return dict(rijen.fetchall())


def test_ontbrekende_en_ongeldige_categorie_worden_gemeld_en_geldige_rijen_bewaard(
    repo,
):
    m, toegevoegd = _importeer(
        repo,
        [
            {
                "begrip": "zonder",
                "definitie": "kern zonder categorie",
                "context": "DJI",
            },
            {
                "begrip": "hoofdletter",
                "definitie": "kern met Type",
                "context": "DJI",
                "categorie": "Type",
            },
            {
                "begrip": "synoniem",
                "definitie": "kern met entiteit",
                "context": "DJI",
                "categorie": "entiteit",
            },
            {
                "begrip": "entiteitcode",
                "definitie": "kern met ENT",
                "context": "DJI",
                "categorie": "ENT",
            },
            {
                "begrip": "resultaat",
                "definitie": "kern met resultaat",
                "context": "DJI",
                "categorie": "resultaat",
            },
        ],
    )

    # Geldige waarden exact bewaard; niets verzonnen voor de andere rijen.
    assert toegevoegd == {"entiteitcode": "ENT", "resultaat": "resultaat"}

    fouten = _fouten(m)
    assert len(fouten) == 3
    assert all("CHECK constraint" not in f for f in fouten)
    assert fouten[0].startswith("Rij 1") and "categorie ontbreekt" in fouten[0]
    assert fouten[1].startswith("Rij 2") and "'Type'" in fouten[1]
    assert fouten[2].startswith("Rij 3") and "'entiteit'" in fouten[2]
    for f in fouten:
        # Technische opslagbeperking, geen inhoudelijke afkeur van de kern.
        assert "niet inhoudelijk" in f and "nog niet bewaren" in f
        assert "type, proces, resultaat, exemplaar" in f
    # Telling en fouten zichtbaar: geen verborgen rijverlies.
    assert "2 geïmporteerd" in str(m.success.call_args[0][0])
    assert "3 fouten" in str(m.expander.call_args[0][0])


@pytest.mark.parametrize(
    "categorie",
    [
        "type",
        "proces",
        "resultaat",
        "exemplaar",
        "ENT",
        "ACT",
        "REL",
        "ATT",
        "AUT",
        "STA",
        "OTH",
    ],
)
def test_elke_schemawaarde_wordt_exact_bewaard(repo, categorie):
    m, toegevoegd = _importeer(
        repo,
        [
            {
                "begrip": "b",
                "definitie": "kern",
                "context": "DJI",
                "categorie": categorie,
            }
        ],
    )
    assert _fouten(m) == []
    assert toegevoegd == {"b": categorie}
