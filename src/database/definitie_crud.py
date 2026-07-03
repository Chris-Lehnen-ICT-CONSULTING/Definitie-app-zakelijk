"""Core CRUD operaties voor definities."""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from database.audit_helpers import AuditHelpers
from database.db_connection import DatabaseConnection
from database.definitie_duplicates import DefinitieDuplicateRepository
from database.definitie_search import DefinitieSearchRepository
from database.models import DefinitieRecord, DefinitieStatus, normalize_wettelijke_basis

logger = logging.getLogger(__name__)


class DefinitieCrudRepository:
    """Core CRUD repository voor definities."""

    def __init__(
        self,
        db: DatabaseConnection,
        audit: AuditHelpers,
        duplicates: DefinitieDuplicateRepository,
        search: DefinitieSearchRepository,
    ):
        self._db = db
        self._audit = audit
        self._duplicates = duplicates
        self._search = search

    def create_definitie(
        self, record: DefinitieRecord, allow_duplicate: bool = False
    ) -> int:
        """Maak nieuwe definitie aan."""
        # DEF-198: Clean architecture - import from utils/, callback registered by UI
        from utils.progress_callback import operation_progress

        with operation_progress("saving_to_database"):
            # Duplicaat-check buiten de transactie (read-only validatie).
            if not allow_duplicate:
                duplicates = self._duplicates.find_duplicates(
                    record.begrip,
                    record.organisatorische_context,
                    record.juridische_context or "",
                    categorie=record.categorie,
                    wettelijke_basis=(
                        json.loads(record.wettelijke_basis)
                        if record.wettelijke_basis
                        else []
                    ),
                )

                if duplicates and any(
                    d.definitie_record.status != DefinitieStatus.ARCHIVED.value
                    for d in duplicates
                ):
                    msg = f"Definitie voor '{record.begrip}' bestaat al in deze context"
                    raise ValueError(msg)

            now = datetime.now(UTC)
            record.created_at = now
            record.updated_at = now

            wb_value = (
                record.wettelijke_basis if record.wettelijke_basis is not None else "[]"
            )

            # DEF-391: INSERT + audit-log atomair (all-or-nothing).
            with self._db.transaction() as conn:
                include_legacy = AuditHelpers.has_legacy_columns_in_conn(conn)
                columns, values = AuditHelpers.build_insert_columns(
                    record, wb_value, include_legacy
                )
                column_sql = ", ".join(columns)
                placeholders = ", ".join("?" for _ in columns)

                cursor = conn.execute(
                    f"INSERT INTO definities ({column_sql}) VALUES ({placeholders})",
                    tuple(values),
                )

                record_id = cursor.lastrowid

                if record_id is None:
                    raise RuntimeError("Failed to get lastrowid after INSERT")

                self._audit.log_geschiedenis(
                    record_id,
                    "created",
                    record.created_by,
                    f"Nieuwe definitie aangemaakt voor '{record.begrip}'",
                )

            logger.info(f"Created definitie {record_id}")
            return record_id

    def get_definitie(self, definitie_id: int) -> DefinitieRecord | None:
        """Haal definitie op op basis van ID.

        DEF-391: kale connectie (geen committende ``with conn:``) zodat een read
        binnen een lopende transaction() die transactie niet vroegtijdig sluit.
        """
        conn = self._db.get_connection()
        cursor = conn.execute("SELECT * FROM definities WHERE id = ?", (definitie_id,))
        row = cursor.fetchone()

        if row:
            return self._audit.row_to_record(row)
        return None

    def find_definitie(
        self,
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        status: DefinitieStatus | None = None,
        categorie: str | None = None,
        wettelijke_basis: list[str] | None = None,
    ) -> DefinitieRecord | None:
        """Zoek definitie op basis van begrip en context."""
        with self._db.get_connection() as conn:
            query = """
                SELECT * FROM definities
                WHERE begrip = ? AND organisatorische_context = ?
                AND (juridische_context = ? OR (juridische_context IS NULL AND ? = ''))
            """
            params: list[Any] = [
                begrip,
                organisatorische_context,
                juridische_context,
                juridische_context,
            ]

            if categorie is not None:
                query += " AND categorie = ?"
                params.append(categorie)

            if wettelijke_basis is not None:
                wb_json = normalize_wettelijke_basis(wettelijke_basis)
                query += " AND (wettelijke_basis = ? OR (wettelijke_basis IS NULL AND ? = '[]'))"
                params.extend([wb_json, wb_json])

            if status:
                query += " AND status = ?"
                params.append(status.value)

            query += " ORDER BY version_number DESC LIMIT 1"

            cursor = conn.execute(query, params)
            row = cursor.fetchone()

            if row:
                return self._audit.row_to_record(row)

            # Synoniem-fallback
            syn_query = """
                SELECT d.*
                FROM definities d
                JOIN definitie_voorbeelden v ON v.definitie_id = d.id
                WHERE LOWER(v.voorbeeld_tekst) = LOWER(?)
                  AND v.voorbeeld_type = 'synonyms'
                  AND v.actief = TRUE
                  AND d.organisatorische_context = ?
                  AND (d.juridische_context = ? OR (d.juridische_context IS NULL AND ? = ''))
            """
            syn_params: list[Any] = [
                begrip,
                organisatorische_context,
                juridische_context,
                juridische_context,
            ]

            if categorie is not None:
                syn_query += " AND d.categorie = ?"
                syn_params.append(categorie)

            if wettelijke_basis is not None:
                wb_json = normalize_wettelijke_basis(wettelijke_basis)
                syn_query += " AND (d.wettelijke_basis = ? OR (d.wettelijke_basis IS NULL AND ? = '[]'))"
                syn_params.extend([wb_json, wb_json])

            if status:
                syn_query += " AND d.status = ?"
                syn_params.append(status.value)
            else:
                syn_query += " AND d.status != 'archived'"

            syn_query += " ORDER BY d.version_number DESC LIMIT 1"

            cursor = conn.execute(syn_query, syn_params)
            row = cursor.fetchone()
            if row:
                return self._audit.row_to_record(row)

            return None

    def update_definitie(
        self,
        definitie_id: int,
        updates: dict[str, Any],
        updated_by: str | None = None,
        _skip_audit: bool = False,
    ) -> bool:
        """Update bestaande definitie."""
        current = self.get_definitie(definitie_id)
        if not current:
            return False

        allowed_fields = {
            "begrip",
            "definitie",
            "bron",
            "status",
            "categorie",
            "ufo_categorie",
            "ontologie",
            "validated",
            "validation_notes",
            "reviewed_by",
            "review_date",
            "improved_version",
            "context_info",
            "metadata",
            "organisatorische_context",
            "juridische_context",
            "wettelijke_basis",
            "toelichting_proces",
            "ketenpartners",
            "approved_by",
            "approved_at",
            "approval_notes",
        }

        set_clauses = []
        params = []

        for field, value in updates.items():
            if hasattr(current, field) and field in allowed_fields:
                set_clauses.append(f"{field} = ?")
                params.append(value)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = ?")
        params.append(datetime.now(UTC))

        if updated_by:
            set_clauses.append("updated_by = ?")
            params.append(updated_by)

        expected_version = updates.get("version_number")
        set_clauses.append("version_number = version_number + 1")

        where_clause = "id = ?"
        where_params: list[Any] = [definitie_id]
        if expected_version is not None:
            where_clause += " AND version_number = ?"
            where_params.append(expected_version)

        query = (
            "UPDATE definities SET " + ", ".join(set_clauses) + f" WHERE {where_clause}"
        )

        # DEF-391: UPDATE + audit-log atomair (all-or-nothing).
        with self._db.transaction() as conn:
            cursor = conn.execute(query, params + where_params)
            if cursor.rowcount == 0 and expected_version is not None:
                logger.warning(
                    f"Optimistic lock failed for definitie {definitie_id} (expected version {expected_version})"
                )
                return False

            if not _skip_audit:
                self._audit.log_geschiedenis(
                    definitie_id,
                    "updated",
                    updated_by,
                    f"Definitie geupdate: {list(updates.keys())}",
                )

        logger.info(f"Updated definitie {definitie_id}")
        return True

    def change_status(
        self,
        definitie_id: int,
        new_status: DefinitieStatus,
        changed_by: str | None = None,
        notes: str | None = None,
    ) -> bool:
        """Wijzig status van definitie."""
        updates: dict[str, Any] = {"status": new_status.value}

        if new_status == DefinitieStatus.ESTABLISHED and changed_by:
            updates.update(
                {
                    "approved_by": changed_by,
                    "approved_at": datetime.now(UTC),
                    "approval_notes": notes,
                }
            )

        # DEF-391: status-UPDATE + audit-log atomair. update_definitie opent zelf
        # een transaction() die hier aansluit (nesting-guard) i.p.v. apart te
        # committen, zodat de statuswijziging en de audit-trail all-or-nothing zijn.
        with self._db.transaction():
            success = self.update_definitie(
                definitie_id, updates, changed_by, _skip_audit=True
            )

            if success:
                self._audit.log_geschiedenis(
                    definitie_id,
                    "status_changed",
                    changed_by,
                    f"Status gewijzigd naar {new_status.value}",
                )

        return success

    def get_all(self) -> list[DefinitieRecord]:
        """Haal alle definities op zonder limit."""
        return self._search.search_definities(limit=None)

    def get_by_status(self, status: str) -> list[DefinitieRecord]:
        """Haal definities op gefilterd op status."""
        try:
            status_enum = DefinitieStatus(status)
        except ValueError as e:
            valid_statuses = ", ".join([s.value for s in DefinitieStatus])
            raise ValueError(
                f"Ongeldige status '{status}'. Toegestane waarden: {valid_statuses}"
            ) from e

        return self._search.search_definities(status=status_enum, limit=None)
