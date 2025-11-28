"""
Extended DefinitionRepository for edit interface functionality.

This module provides additional repository methods needed for the
definition edit interface, including version history and optimistic locking.
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Any, cast

from services.definition_repository import DefinitionRepository
from services.interfaces import Definition

logger = logging.getLogger(__name__)


class DefinitionEditRepository(DefinitionRepository):
    """
    Extended repository with edit interface specific functionality.

    Adds support for:
    - Version history management
    - Optimistic locking
    - Auto-save functionality
    - Bulk operations
    """

    def __init__(self, db_path: str = "data/definities.db"):
        """Initialize the extended repository."""
        super().__init__(db_path)
        logger.info("DefinitionEditRepository initialized with extended features")

    def get_version_history(
        self, definitie_id: int, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Haal versie geschiedenis op voor een definitie.

        Filtert auto_save entries uit - deze zitten nu in definitie_drafts tabel.

        Args:
            definitie_id: ID van de definitie
            limit: Maximum aantal versies om op te halen

        Returns:
            Lijst met versie geschiedenis entries (exclusief auto-saves)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT
                        id,
                        begrip,
                        definitie_oude_waarde,
                        definitie_nieuwe_waarde,
                        wijziging_type,
                        wijziging_reden,
                        gewijzigd_door,
                        gewijzigd_op,
                        context_snapshot
                    FROM definitie_geschiedenis
                    WHERE definitie_id = ? AND wijziging_type != 'auto_save'
                    ORDER BY gewijzigd_op DESC
                    LIMIT ?
                """,
                    (definitie_id, limit),
                )

                history = []
                for row in cursor.fetchall():
                    entry = self._row_to_dict(row, cursor.description)

                    # Parse JSON context snapshot
                    if entry.get("context_snapshot"):
                        try:
                            entry["context_snapshot"] = json.loads(
                                entry["context_snapshot"]
                            )
                        except json.JSONDecodeError as e:
                            logger.warning(f"Could not parse context_snapshot: {e}")

                    history.append(entry)

                return history

        except Exception as e:
            logger.error(
                f"Error fetching version history for definitie {definitie_id}: {e}"
            )
            return []

    def save_with_history(
        self,
        definition: Definition,
        wijziging_reden: str | None = None,
        gewijzigd_door: str = "system",
    ) -> int:
        """
        Sla definitie op met automatische history logging.

        Args:
            definition: De op te slaan definitie
            wijziging_reden: Optionele reden voor wijziging
            gewijzigd_door: Gebruiker die wijziging maakt

        Returns:
            ID van de opgeslagen definitie
        """
        try:
            # Get current version if updating
            old_definition = None
            if definition.id:
                old_definition = self.get(definition.id)

            # Set updated_by in metadata
            if not definition.metadata:
                definition.metadata = {}
            definition.metadata["updated_by"] = gewijzigd_door

            # Save using parent method
            definition_id = self.save(definition)

            # Manual history entry if needed (trigger handles most cases)
            if wijziging_reden and definition_id:
                self._add_history_entry(
                    definitie_id=definition_id,
                    begrip=definition.begrip,
                    oude_waarde=old_definition.definitie if old_definition else "",
                    nieuwe_waarde=definition.definitie,
                    wijziging_type="updated" if old_definition else "created",
                    wijziging_reden=wijziging_reden,
                    gewijzigd_door=gewijzigd_door,
                )

            return cast(int, definition_id)

        except Exception as e:
            logger.error(f"Error saving definition with history: {e}")
            raise

    def check_version_conflict(self, definitie_id: int, version_number: int) -> bool:
        """
        Check voor version conflicts (optimistic locking).

        Args:
            definitie_id: ID van de definitie
            version_number: Verwachte versie nummer

        Returns:
            True als er een conflict is, False anders
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT version_number 
                    FROM definities 
                    WHERE id = ?
                """,
                    (definitie_id,),
                )

                row = cursor.fetchone()
                if row:
                    current_version: int = row[0]
                    return cast(bool, current_version != version_number)

                return False

        except Exception as e:
            logger.error(f"Error checking version conflict: {e}")
            return True  # Assume conflict on error

    def auto_save_draft(self, definitie_id: int, draft_content: dict[str, Any]) -> bool:
        """
        Auto-save draft versie van definitie.

        Gebruikt INSERT OR REPLACE om max 1 draft per definitie te behouden.
        Dit voorkomt clutter in de versiegeschiedenis UI.

        Args:
            definitie_id: ID van de definitie
            draft_content: Draft content om op te slaan

        Returns:
            True als succesvol, False anders
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Store draft in dedicated drafts table (replaces previous draft)
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO definitie_drafts (
                        definitie_id,
                        draft_content,
                        saved_at,
                        saved_by
                    ) VALUES (?, ?, CURRENT_TIMESTAMP, 'system')
                """,
                    (
                        definitie_id,
                        json.dumps(draft_content),
                    ),
                )

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Error auto-saving draft: {e}")
            return False

    def get_latest_auto_save(self, definitie_id: int) -> dict[str, Any] | None:
        """
        Haal laatste auto-save op voor een definitie.

        Args:
            definitie_id: ID van de definitie

        Returns:
            Auto-save content indien beschikbaar
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT draft_content, saved_at
                    FROM definitie_drafts
                    WHERE definitie_id = ?
                """,
                    (definitie_id,),
                )

                row = cursor.fetchone()
                if row:
                    try:
                        draft: dict[str, Any] = json.loads(row[0])
                        draft["auto_save_timestamp"] = row[1]
                        return draft
                    except json.JSONDecodeError:
                        pass

                return None

        except Exception as e:
            logger.error(f"Error fetching auto-save: {e}")
            return None

    def bulk_update_status(
        self, definitie_ids: list[int], new_status: str, gewijzigd_door: str = "system"
    ) -> int:
        """
        Update status voor meerdere definities tegelijk.

        Args:
            definitie_ids: Lijst van definitie IDs
            new_status: Nieuwe status
            gewijzigd_door: Gebruiker die wijziging maakt

        Returns:
            Aantal succesvol geüpdatete definities
        """
        if not definitie_ids:
            return 0

        updated_count = 0
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                for def_id in definitie_ids:
                    cursor.execute(
                        """
                        UPDATE definities 
                        SET status = ?, updated_by = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """,
                        (new_status, gewijzigd_door, def_id),
                    )

                    if cursor.rowcount > 0:
                        updated_count += 1

                conn.commit()
                logger.info(
                    f"Bulk updated {updated_count} definitions to status {new_status}"
                )

        except Exception as e:
            logger.error(f"Error in bulk status update: {e}")

        return updated_count

    def search_with_filters(
        self,
        search_term: str | None = None,
        categorie: str | None = None,
        status: str | None = None,
        context_filter: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        source_type: str | None = None,
        limit: int = 50,
    ) -> list[Definition]:
        """
        Geavanceerd zoeken met meerdere filters.

        Args:
            search_term: Optionele zoekterm
            categorie: Filter op categorie
            status: Filter op status
            context_filter: Filter op organisatorische context
            date_from: Filter vanaf datum
            date_to: Filter tot datum
            source_type: Filter op herkomst (generated/imported/manual)
            limit: Maximum aantal resultaten

        Returns:
            Lijst van gevonden definities
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Build dynamic query
                # Note: Geen hardcoded archived filter meer - status filter is nu expliciet
                query = "SELECT * FROM definities WHERE 1=1"
                params: list[Any] = []

                if search_term:
                    query += " AND (begrip LIKE ? OR definitie LIKE ?)"
                    search_pattern = f"%{search_term}%"
                    params.extend([search_pattern, search_pattern])

                if categorie:
                    query += " AND categorie = ?"
                    params.append(categorie)

                if status:
                    query += " AND status = ?"
                    params.append(status)

                if source_type:
                    query += " AND source_type = ?"
                    params.append(source_type)

                if context_filter:
                    query += " AND organisatorische_context LIKE ?"
                    params.append(f"%{context_filter}%")

                if date_from:
                    query += " AND created_at >= ?"
                    params.append(date_from.isoformat())

                if date_to:
                    query += " AND created_at <= ?"
                    params.append(date_to.isoformat())

                query += " ORDER BY updated_at DESC LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)

                definitions = []
                for row in cursor.fetchall():
                    record = self._row_to_record(row, cursor.description)
                    definition = self._record_to_definition(record)
                    if definition:
                        definitions.append(definition)

                return definitions

        except Exception as e:
            logger.error(f"Error in advanced search: {e}")
            return []

    def get_statistics(self) -> dict[str, Any]:
        """
        Haal uitgebreide statistieken op.

        Returns:
            Dictionary met statistieken
        """
        stats = super().get_stats()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Recent changes
                cursor.execute(
                    """
                    SELECT COUNT(*) 
                    FROM definities 
                    WHERE updated_at > datetime('now', '-7 days')
                """
                )
                stats["recent_changes"] = cursor.fetchone()[0]

                # Most active users
                cursor.execute(
                    """
                    SELECT updated_by, COUNT(*) as count
                    FROM definities
                    WHERE updated_by IS NOT NULL
                    GROUP BY updated_by
                    ORDER BY count DESC
                    LIMIT 5
                """
                )
                stats["most_active_users"] = [
                    {"user": row[0], "count": row[1]} for row in cursor.fetchall()
                ]

                # Categories distribution
                cursor.execute(
                    """
                    SELECT categorie, COUNT(*) as count
                    FROM definities
                    WHERE status != 'archived'
                    GROUP BY categorie
                """
                )
                stats["by_category"] = dict(cursor.fetchall())

        except Exception as e:
            logger.error(f"Error fetching statistics: {e}")

        return cast(dict[str, Any], stats)

    def _add_history_entry(
        self,
        definitie_id: int,
        begrip: str,
        oude_waarde: str,
        nieuwe_waarde: str,
        wijziging_type: str,
        wijziging_reden: str,
        gewijzigd_door: str,
    ) -> None:
        """Add manual history entry."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO definitie_geschiedenis (
                        definitie_id, begrip, definitie_oude_waarde,
                        definitie_nieuwe_waarde, wijziging_type,
                        wijziging_reden, gewijzigd_door
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        definitie_id,
                        begrip,
                        oude_waarde,
                        nieuwe_waarde,
                        wijziging_type,
                        wijziging_reden,
                        gewijzigd_door,
                    ),
                )
                conn.commit()

        except Exception as e:
            logger.error(f"Error adding history entry: {e}")

    def _row_to_dict(self, row: sqlite3.Row, description) -> dict[str, Any]:
        """Convert database row to dictionary."""
        result = {}
        for idx, col in enumerate(description):
            col_name = col[0]
            value = row[idx]

            # Convert datetime strings
            if col_name.endswith(("_op", "_at")):
                if value and isinstance(value, str):
                    try:
                        value = datetime.fromisoformat(value)
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Could not parse datetime for {col_name}: {e}")

            result[col_name] = value

        return result
