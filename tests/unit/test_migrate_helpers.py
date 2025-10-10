"""Unit tests for migration helper utilities."""

import sqlite3
from pathlib import Path

from database.migrate_database import (_create_definitie_voorbeelden_table,
                                       _create_definities_table,
                                       _ensure_definitie_voorbeelden_indexes,
                                       _ensure_definities_indexes)


def _get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]


def test_create_definities_table_schema(tmp_path: Path):
    """Helper creates definities table with the canonical column order."""

    db_path = tmp_path / "schema.db"
    with sqlite3.connect(db_path) as conn:
        _create_definities_table(conn)
        columns = _get_columns(conn, "definities")

    expected_columns = [
        "id",
        "begrip",
        "definitie",
        "categorie",
        "organisatorische_context",
        "juridische_context",
        "wettelijke_basis",
        "ufo_categorie",
        "toelichting_proces",
        "status",
        "version_number",
        "previous_version_id",
        "validation_score",
        "validation_date",
        "validation_issues",
        "source_type",
        "source_reference",
        "imported_from",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "approved_by",
        "approved_at",
        "approval_notes",
        "last_exported_at",
        "export_destinations",
        "datum_voorstel",
        "ketenpartners",
        "voorkeursterm",
    ]

    assert columns == expected_columns


def test_create_definitie_voorbeelden_table_schema(tmp_path: Path):
    """Helper creates definitie_voorbeelden table with canonical column order."""

    db_path = tmp_path / "schema_examples.db"
    with sqlite3.connect(db_path) as conn:
        _create_definitie_voorbeelden_table(conn)
        columns = _get_columns(conn, "definitie_voorbeelden")

    expected_columns = [
        "id",
        "definitie_id",
        "voorbeeld_type",
        "voorbeeld_tekst",
        "voorbeeld_volgorde",
        "gegenereerd_door",
        "generation_model",
        "generation_parameters",
        "actief",
        "beoordeeld",
        "beoordeeling",
        "beoordeeling_notities",
        "beoordeeld_door",
        "beoordeeld_op",
        "aangemaakt_op",
        "bijgewerkt_op",
    ]

    assert columns == expected_columns


def test_ensure_indexes_and_triggers(tmp_path: Path):
    """Index helpers add the expected artefacts without errors."""

    db_path = tmp_path / "indexes.db"
    with sqlite3.connect(db_path) as conn:
        _create_definities_table(conn)
        _create_definitie_voorbeelden_table(conn)

        _ensure_definities_indexes(conn)
        _ensure_definitie_voorbeelden_indexes(conn)

        definities_indexes = {
            row[1] for row in conn.execute("PRAGMA index_list(definities)")
        }
        voorbeelden_indexes = {
            row[1] for row in conn.execute("PRAGMA index_list(definitie_voorbeelden)")
        }
        triggers = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger'"
            )
        }

    assert {
        "idx_definities_begrip",
        "idx_definities_context",
        "idx_definities_status",
        "idx_definities_categorie",
        "idx_definities_created_at",
        "idx_definities_datum_voorstel",
    }.issubset(definities_indexes)

    assert {
        "idx_voorbeelden_definitie_id",
        "idx_voorbeelden_type",
        "idx_voorbeelden_actief",
    }.issubset(voorbeelden_indexes)

    assert "update_voorbeelden_timestamp" in triggers
