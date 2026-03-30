"""Audit en history helpers voor de database laag.

Bevat record-conversie, geschiedenis-logging, en import/export-logging.
"""

import logging
import sqlite3
from datetime import UTC, datetime
from typing import Any

from database.db_connection import DatabaseConnection
from database.models import DefinitieRecord

logger = logging.getLogger(__name__)


class AuditHelpers:
    """Audit trail en record-conversie helpers."""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    @staticmethod
    def has_legacy_columns_in_conn(conn: sqlite3.Connection) -> bool:
        """Determine legacy column presence using an existing connection."""
        cursor = conn.execute("PRAGMA table_info(definities)")
        columns = {row[1] for row in cursor.fetchall()}
        return "datum_voorstel" in columns and "ketenpartners" in columns

    @staticmethod
    def build_insert_columns(
        record: DefinitieRecord, wb_value: str, include_legacy: bool
    ) -> tuple[list[str], list[Any]]:
        """Compose insert columns/values for definities table."""
        columns = [
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
            "generation_prompt_data",
        ]

        values: list[Any] = [
            record.begrip,
            record.definitie,
            record.categorie,
            record.organisatorische_context,
            record.juridische_context,
            wb_value,
            record.ufo_categorie,
            record.toelichting_proces,
            record.status,
            record.version_number,
            record.previous_version_id,
            record.validation_score,
            record.validation_date,
            record.validation_issues,
            record.source_type,
            record.source_reference,
            record.imported_from,
            record.created_at,
            record.updated_at,
            record.created_by,
            record.updated_by,
            record.approved_by,
            record.approved_at,
            record.approval_notes,
            record.last_exported_at,
            record.export_destinations,
            record.generation_prompt_data,
        ]

        if include_legacy:
            columns.extend(["datum_voorstel", "ketenpartners"])
            values.extend([record.datum_voorstel, record.ketenpartners])

        return columns, values

    def row_to_record(self, row: sqlite3.Row) -> DefinitieRecord:
        """Converteer database row naar DefinitieRecord."""
        _keys = set(row.keys()) if hasattr(row, "keys") else set()
        return DefinitieRecord(
            id=row["id"],
            begrip=row["begrip"],
            definitie=row["definitie"],
            categorie=row["categorie"],
            organisatorische_context=row["organisatorische_context"],
            juridische_context=row["juridische_context"],
            wettelijke_basis=(
                row.get("wettelijke_basis")
                if isinstance(row, dict)
                else row["wettelijke_basis"]
            ),
            ufo_categorie=(row["ufo_categorie"] if "ufo_categorie" in _keys else None),
            toelichting_proces=(
                row["toelichting_proces"] if "toelichting_proces" in _keys else None
            ),
            status=row["status"],
            version_number=row["version_number"],
            previous_version_id=row["previous_version_id"],
            validation_score=row["validation_score"],
            validation_date=(
                datetime.fromisoformat(row["validation_date"])
                if row["validation_date"]
                else None
            ),
            validation_issues=row["validation_issues"],
            source_type=row["source_type"],
            source_reference=row["source_reference"],
            imported_from=row["imported_from"],
            created_at=(
                datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
            ),
            updated_at=(
                datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ),
            created_by=row["created_by"],
            updated_by=row["updated_by"],
            approved_by=row["approved_by"],
            approved_at=(
                datetime.fromisoformat(row["approved_at"])
                if row["approved_at"]
                else None
            ),
            approval_notes=row["approval_notes"],
            last_exported_at=(
                datetime.fromisoformat(row["last_exported_at"])
                if row["last_exported_at"]
                else None
            ),
            export_destinations=row["export_destinations"],
            generation_prompt_data=(
                row["generation_prompt_data"]
                if "generation_prompt_data" in _keys
                else None
            ),
        )

    def log_geschiedenis(
        self,
        definitie_id: int,
        wijziging_type: str,
        gewijzigd_door: str | None = None,
        reden: str | None = None,
    ):
        """Log wijziging in geschiedenis tabel."""
        with self._db.get_connection() as conn:
            begrip_result = conn.execute(
                "SELECT begrip FROM definities WHERE id = ?", (definitie_id,)
            ).fetchone()
            begrip = begrip_result["begrip"] if begrip_result else "unknown"

            conn.execute(
                """
                INSERT INTO definitie_geschiedenis
                (definitie_id, begrip, wijziging_type, wijziging_reden, gewijzigd_door)
                VALUES (?, ?, ?, ?, ?)
            """,
                (definitie_id, begrip, wijziging_type, reden, gewijzigd_door),
            )

    def log_import_export(
        self,
        operatie_type: str,
        bestand_pad: str,
        verwerkt: int,
        succesvol: int,
        gefaald: int,
    ):
        """Log import/export operatie."""
        with self._db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO import_export_logs
                (operatie_type, bron_bestemming, aantal_verwerkt, aantal_succesvol,
                 aantal_gefaald, bestand_pad, status, voltooid_op)
                VALUES (?, ?, ?, ?, ?, ?, 'completed', ?)
            """,
                (
                    operatie_type,
                    bestand_pad,
                    verwerkt,
                    succesvol,
                    gefaald,
                    bestand_pad,
                    datetime.now(UTC),
                ),
            )
