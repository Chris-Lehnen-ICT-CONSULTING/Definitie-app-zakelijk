"""
SynonymRepository - Database laag voor synonym suggestions management.

Biedt CRUD operaties voor GPT-4 synonym suggestions workflow:
- Save suggestions (pending status)
- Get pending/approved/rejected suggestions
- Update suggestion status (approve/reject)
- Query by hoofdterm, confidence, status
"""

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SuggestionStatus(Enum):
    """Status van een synonym suggestion."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class SynonymSuggestionRecord:
    """
    Representatie van een synonym suggestion record.

    Attributes:
        id: Unieke database ID
        hoofdterm: De juridische hoofdterm
        synoniem: De gesuggereerde synoniem
        confidence: AI confidence score (0.0-1.0)
        rationale: Uitleg waarom dit een goed synoniem is
        status: Status (pending/approved/rejected)
        reviewed_by: Wie heeft de suggestie reviewed
        reviewed_at: Wanneer reviewed
        rejection_reason: Reden voor rejection (bij rejected)
        context_data: Extra context als JSON string
        created_at: Aanmaak timestamp
        updated_at: Laatste update timestamp
    """

    hoofdterm: str
    synoniem: str
    confidence: float
    rationale: str
    status: str = SuggestionStatus.PENDING.value
    id: int | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None
    context_data: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Converteer naar dictionary voor JSON serialization."""
        result = asdict(self)
        # Converteer datetime objecten naar ISO strings
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
        return result

    def get_context_dict(self) -> dict[str, Any]:
        """Haal context data op als dictionary."""
        if not self.context_data:
            return {}
        try:
            return json.loads(self.context_data)
        except json.JSONDecodeError:
            return {}

    def set_context(self, context: dict[str, Any]):
        """Stel context data in als JSON string."""
        self.context_data = json.dumps(context, ensure_ascii=False)


class SynonymRepository:
    """
    Repository voor synonym suggestions management.

    Biedt database abstractie laag voor alle synonym suggestion
    operaties, inclusief opslag, zoeken, approve/reject workflow.
    """

    def __init__(self, db_path: str = "data/definities.db"):
        """
        Initialiseer repository met database connectie.

        Args:
            db_path: Pad naar SQLite database bestand
        """
        self.db_path = db_path
        self._verify_table_exists()

    def _get_connection(self, timeout: float = 30.0) -> sqlite3.Connection:
        """
        Maak database connectie met proper timeout en settings.

        Args:
            timeout: Connection timeout in seconden

        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(
            self.db_path,
            timeout=timeout,
            isolation_level=None,  # Autocommit mode
            check_same_thread=False,
        )
        # Performance pragmas
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _verify_table_exists(self):
        """Verify synonym_suggestions table exists."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='synonym_suggestions'
                """
            )
            if not cursor.fetchone():
                logger.warning(
                    "synonym_suggestions table does not exist. "
                    "Run migration: add_synonym_suggestions_table.sql"
                )

    def save_suggestion(
        self,
        hoofdterm: str,
        synoniem: str,
        confidence: float,
        rationale: str,
        context: dict[str, Any] | None = None,
    ) -> int:
        """
        Sla nieuwe synonym suggestion op voor human review.

        Args:
            hoofdterm: De juridische hoofdterm
            synoniem: De gesuggereerde synoniem
            confidence: AI confidence score (0.0-1.0)
            rationale: Uitleg waarom dit een goed synoniem is
            context: Optional extra context (model, definitie, etc.)

        Returns:
            ID van nieuw opgeslagen suggestion

        Raises:
            ValueError: Als suggestion al bestaat (duplicate)
        """
        # Validate confidence range
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"Confidence moet tussen 0.0 en 1.0 zijn: {confidence}")

        with self._get_connection() as conn:
            # Check for duplicates
            cursor = conn.execute(
                """
                SELECT id FROM synonym_suggestions
                WHERE hoofdterm = ? AND synoniem = ?
                """,
                (hoofdterm, synoniem),
            )
            existing = cursor.fetchone()
            if existing:
                raise ValueError(
                    f"Suggestion '{hoofdterm}' → '{synoniem}' bestaat al (ID: {existing[0]})"
                )

            # Convert context to JSON
            context_json = json.dumps(context, ensure_ascii=False) if context else None

            # Insert suggestion
            cursor = conn.execute(
                """
                INSERT INTO synonym_suggestions (
                    hoofdterm, synoniem, confidence, rationale,
                    status, context_data
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    hoofdterm,
                    synoniem,
                    confidence,
                    rationale,
                    SuggestionStatus.PENDING.value,
                    context_json,
                ),
            )

            suggestion_id = cursor.lastrowid
            logger.info(
                f"Saved suggestion {suggestion_id}: '{hoofdterm}' → '{synoniem}' "
                f"(confidence: {confidence:.2f})"
            )
            return suggestion_id

    def get_suggestion(self, suggestion_id: int) -> SynonymSuggestionRecord | None:
        """
        Haal specifieke suggestion op.

        Args:
            suggestion_id: Database ID

        Returns:
            SynonymSuggestionRecord of None als niet gevonden
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM synonym_suggestions WHERE id = ?", (suggestion_id,)
            )
            row = cursor.fetchone()
            return self._row_to_record(row) if row else None

    def get_pending_suggestions(
        self,
        hoofdterm_filter: str | None = None,
        min_confidence: float = 0.0,
        limit: int | None = None,
    ) -> list[SynonymSuggestionRecord]:
        """
        Haal alle pending suggestions op.

        Args:
            hoofdterm_filter: Filter op specifieke hoofdterm (optional)
            min_confidence: Minimum confidence threshold (default: 0.0)
            limit: Maximum aantal resultaten (optional)

        Returns:
            Lijst van SynonymSuggestionRecord objecten
        """
        with self._get_connection() as conn:
            query = """
                SELECT * FROM synonym_suggestions
                WHERE status = ? AND confidence >= ?
            """
            params: list[Any] = [SuggestionStatus.PENDING.value, min_confidence]

            if hoofdterm_filter:
                query += " AND hoofdterm = ?"
                params.append(hoofdterm_filter)

            query += " ORDER BY confidence DESC, created_at DESC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor = conn.execute(query, params)
            return [self._row_to_record(row) for row in cursor.fetchall()]

    def get_suggestions_by_status(
        self, status: SuggestionStatus, limit: int | None = None
    ) -> list[SynonymSuggestionRecord]:
        """
        Haal suggestions op op basis van status.

        Args:
            status: De status om te filteren
            limit: Maximum aantal resultaten (optional)

        Returns:
            Lijst van SynonymSuggestionRecord objecten
        """
        with self._get_connection() as conn:
            query = """
                SELECT * FROM synonym_suggestions
                WHERE status = ?
                ORDER BY created_at DESC
            """
            params: list[Any] = [status.value]

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor = conn.execute(query, params)
            return [self._row_to_record(row) for row in cursor.fetchall()]

    def approve_suggestion(self, suggestion_id: int, reviewed_by: str) -> bool:
        """
        Approve een suggestion.

        Args:
            suggestion_id: ID van de suggestion
            reviewed_by: Wie de approval uitvoert

        Returns:
            True als succesvol approved
        """
        return self._update_status(
            suggestion_id,
            SuggestionStatus.APPROVED,
            reviewed_by,
            rejection_reason=None,
        )

    def reject_suggestion(
        self, suggestion_id: int, reviewed_by: str, rejection_reason: str
    ) -> bool:
        """
        Reject een suggestion.

        Args:
            suggestion_id: ID van de suggestion
            reviewed_by: Wie de rejection uitvoert
            rejection_reason: Reden voor rejection

        Returns:
            True als succesvol rejected
        """
        if not rejection_reason.strip():
            raise ValueError("Rejection reason is verplicht")

        return self._update_status(
            suggestion_id,
            SuggestionStatus.REJECTED,
            reviewed_by,
            rejection_reason=rejection_reason,
        )

    def _update_status(
        self,
        suggestion_id: int,
        new_status: SuggestionStatus,
        reviewed_by: str,
        rejection_reason: str | None = None,
    ) -> bool:
        """
        Update status van een suggestion.

        Args:
            suggestion_id: ID van de suggestion
            new_status: Nieuwe status
            reviewed_by: Wie de update uitvoert
            rejection_reason: Reden voor rejection (bij rejected)

        Returns:
            True als succesvol geupdate
        """
        with self._get_connection() as conn:
            # Check if suggestion exists
            existing = self.get_suggestion(suggestion_id)
            if not existing:
                logger.warning(f"Suggestion {suggestion_id} not found")
                return False

            # Update status
            cursor = conn.execute(
                """
                UPDATE synonym_suggestions
                SET status = ?,
                    reviewed_by = ?,
                    reviewed_at = ?,
                    rejection_reason = ?
                WHERE id = ?
                """,
                (
                    new_status.value,
                    reviewed_by,
                    datetime.now(UTC),
                    rejection_reason,
                    suggestion_id,
                ),
            )

            success = cursor.rowcount > 0

            if success:
                logger.info(
                    f"Updated suggestion {suggestion_id} status to {new_status.value}"
                )

            return success

    def get_statistics(self) -> dict[str, Any]:
        """
        Haal statistieken op over suggestions.

        Returns:
            Dictionary met statistieken
        """
        with self._get_connection() as conn:
            stats = {}

            # Total counts by status
            cursor = conn.execute(
                """
                SELECT status, COUNT(*) as count
                FROM synonym_suggestions
                GROUP BY status
                """
            )
            stats["by_status"] = dict(cursor.fetchall())

            # Total count
            stats["total"] = sum(stats["by_status"].values())

            # Average confidence by status
            cursor = conn.execute(
                """
                SELECT status, AVG(confidence) as avg_confidence
                FROM synonym_suggestions
                GROUP BY status
                """
            )
            stats["avg_confidence_by_status"] = {
                row["status"]: round(row["avg_confidence"], 3)
                for row in cursor.fetchall()
            }

            # Approval rate
            approved = stats["by_status"].get(SuggestionStatus.APPROVED.value, 0)
            rejected = stats["by_status"].get(SuggestionStatus.REJECTED.value, 0)
            total_reviewed = approved + rejected

            if total_reviewed > 0:
                stats["approval_rate"] = approved / total_reviewed
            else:
                stats["approval_rate"] = 0.0

            # Recent activity (last 7 days)
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count
                FROM synonym_suggestions
                WHERE created_at >= datetime('now', '-7 days')
                """
            )
            stats["created_last_7_days"] = cursor.fetchone()["count"]

            return stats

    def get_suggestions_for_hoofdterm(
        self, hoofdterm: str
    ) -> list[SynonymSuggestionRecord]:
        """
        Haal alle suggestions op voor een specifieke hoofdterm.

        Args:
            hoofdterm: De hoofdterm om te filteren

        Returns:
            Lijst van SynonymSuggestionRecord objecten
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM synonym_suggestions
                WHERE hoofdterm = ?
                ORDER BY status, confidence DESC, created_at DESC
                """,
                (hoofdterm,),
            )
            return [self._row_to_record(row) for row in cursor.fetchall()]

    def delete_suggestion(self, suggestion_id: int) -> bool:
        """
        Verwijder een suggestion (alleen voor admin/cleanup).

        Args:
            suggestion_id: ID van de suggestion

        Returns:
            True als succesvol verwijderd
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM synonym_suggestions WHERE id = ?", (suggestion_id,)
            )
            success = cursor.rowcount > 0

            if success:
                logger.info(f"Deleted suggestion {suggestion_id}")

            return success

    def _row_to_record(self, row: sqlite3.Row) -> SynonymSuggestionRecord:
        """Converteer database row naar SynonymSuggestionRecord."""
        return SynonymSuggestionRecord(
            id=row["id"],
            hoofdterm=row["hoofdterm"],
            synoniem=row["synoniem"],
            confidence=row["confidence"],
            rationale=row["rationale"],
            status=row["status"],
            reviewed_by=row["reviewed_by"],
            reviewed_at=(
                datetime.fromisoformat(row["reviewed_at"])
                if row["reviewed_at"]
                else None
            ),
            rejection_reason=row["rejection_reason"],
            context_data=row["context_data"],
            created_at=(
                datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
            ),
            updated_at=(
                datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ),
        )


# Convenience function
def get_synonym_repository(db_path: str | None = None) -> SynonymRepository:
    """Haal gedeelde repository instance op."""
    if not db_path:
        # Default database in project directory
        project_root = Path(__file__).parent.parent.parent
        db_path = str(project_root / "data" / "definities.db")

    return SynonymRepository(db_path)
