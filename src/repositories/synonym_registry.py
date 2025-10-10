"""
SynonymRegistry - Data access layer voor Synonym Orchestrator Architecture v3.1.

Deze repository beheert CRUD operaties op synonym_groups en synonym_group_members
met bidirectionele lookup, cache invalidation callbacks, en statistics.

Architecture Specification: docs/architectuur/synonym-orchestrator-architecture-v3.1.md
Lines 210-323: SynonymRegistry verantwoordelijkheden
"""

import logging
import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from models.synonym_models import SynonymGroup, SynonymGroupMember, WeightedSynonym

logger = logging.getLogger(__name__)


# Valid ORDER BY columns (whitelist for SQL injection prevention)
_VALID_ORDER_BY_COLUMNS = {
    "weight",
    "is_preferred",
    "term",
    "created_at",
    "updated_at",
    "usage_count",
    "status",
}


# ========================================
# PYTHON 3.12+ DATETIME ADAPTER/CONVERTER
# ========================================
# Fix for Python 3.12+ deprecation warning:
# "The default datetime adapter is deprecated as of Python 3.12"


def _adapt_datetime_iso(val: datetime) -> str:
    """
    Adapt datetime to ISO string for SQLite storage (Python 3.12+ compatible).

    Args:
        val: datetime object

    Returns:
        ISO formatted string
    """
    return val.isoformat()


def _convert_datetime(val: bytes) -> datetime:
    """
    Convert ISO string from SQLite to datetime (Python 3.12+ compatible).

    Args:
        val: ISO formatted datetime as bytes or string

    Returns:
        datetime object
    """
    # Handle both bytes and str (SQLite can return either)
    if isinstance(val, bytes):
        val = val.decode()
    return datetime.fromisoformat(val)


# Register custom adapter/converter (Python 3.12+ requirement)
sqlite3.register_adapter(datetime, _adapt_datetime_iso)
sqlite3.register_converter("TIMESTAMP", _convert_datetime)


class SynonymRegistry:
    """
    Data access layer voor synonym groups & members.

    Responsibilities:
    - CRUD operations op synonym_groups & synonym_group_members
    - Bidirectionele lookup (term → groep → alle members)
    - Cache invalidation callbacks
    - Statistics & health checks
    """

    def __init__(self, db_path: str = "data/definities.db"):
        """
        Initialiseer registry met database connectie.

        Args:
            db_path: Pad naar SQLite database bestand
        """
        self.db_path = db_path
        self._invalidation_callbacks: list[Callable[[str], None]] = []
        self._verify_tables_exist()

    def _get_connection(self, timeout: float = 30.0) -> sqlite3.Connection:
        """
        Maak database connectie met proper timeout en settings.

        Python 3.12+ compatibel: gebruikt custom datetime adapters/converters.

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
            detect_types=sqlite3.PARSE_DECLTYPES,  # Enable custom converters
        )
        # Performance pragmas
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _verify_tables_exist(self):
        """Verify synonym tables exist in database."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('synonym_groups', 'synonym_group_members')
                """
            )
            tables = {row["name"] for row in cursor.fetchall()}

            missing = {"synonym_groups", "synonym_group_members"} - tables
            if missing:
                logger.warning(
                    f"Missing synonym tables: {missing}. "
                    "Schema should be initialized via schema.sql"
                )

    # ========================================
    # GROUP OPERATIONS
    # ========================================

    def get_or_create_group(
        self,
        canonical_term: str,
        domain: str | None = None,
        created_by: str = "system",
    ) -> SynonymGroup:
        """
        Haal bestaande groep op of maak nieuwe aan voor canonical term.

        Args:
            canonical_term: De canonieke term voor deze groep
            domain: Optioneel domein (strafrecht, civielrecht, etc.)
            created_by: Wie maakt de groep aan

        Returns:
            SynonymGroup object (bestaand of nieuw)

        Raises:
            ValueError: Als canonical_term leeg is
        """
        if not canonical_term or not canonical_term.strip():
            msg = "canonical_term mag niet leeg zijn"
            raise ValueError(msg)

        canonical_term = canonical_term.strip()

        with self._get_connection() as conn:
            # Check if group exists
            cursor = conn.execute(
                "SELECT * FROM synonym_groups WHERE canonical_term = ?",
                (canonical_term,),
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_group(row)

            # Create new group
            now = datetime.now(UTC)
            cursor = conn.execute(
                """
                INSERT INTO synonym_groups (canonical_term, domain, created_at, updated_at, created_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (canonical_term, domain, now, now, created_by),
            )

            group_id = cursor.lastrowid
            logger.info(
                f"Created new synonym group {group_id} for '{canonical_term}'"
                + (f" (domain: {domain})" if domain else "")
            )

            return SynonymGroup(
                id=group_id,
                canonical_term=canonical_term,
                domain=domain,
                created_at=now,
                updated_at=now,
                created_by=created_by,
            )

    def find_group_by_term(self, term: str) -> SynonymGroup | None:
        """
        Vind groep waar term de canonical_term is OF een member.

        Args:
            term: De term om te zoeken (canonical_term of member term)

        Returns:
            SynonymGroup of None als niet gevonden
        """
        if not term or not term.strip():
            return None

        normalized_term = term.strip()

        with self._get_connection() as conn:
            # First check canonical_term (most common case)
            cursor = conn.execute(
                """
                SELECT * FROM synonym_groups
                WHERE canonical_term = ?
                LIMIT 1
                """,
                (normalized_term,),
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_group(row)

            # If not found, check members
            cursor = conn.execute(
                """
                SELECT g.*
                FROM synonym_groups g
                JOIN synonym_group_members m ON m.group_id = g.id
                WHERE m.term = ?
                LIMIT 1
                """,
                (normalized_term,),
            )
            row = cursor.fetchone()
            return self._row_to_group(row) if row else None

    def get_group(self, group_id: int) -> SynonymGroup | None:
        """
        Haal specifieke groep op op basis van ID.

        Args:
            group_id: Database ID van de groep

        Returns:
            SynonymGroup of None als niet gevonden
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM synonym_groups WHERE id = ?", (group_id,)
            )
            row = cursor.fetchone()
            return self._row_to_group(row) if row else None

    def delete_group(self, group_id: int, cascade: bool = True) -> bool:
        """
        Delete synonym group (optionally cascade delete members).

        Args:
            group_id: ID van group om te verwijderen
            cascade: Als True, delete group + members. Als False, error
                if members exist.

        Returns:
            True als succesvol verwijderd

        Raises:
            ValueError: Als group niet bestaat OF cascade=False en members bestaan
        """
        with self._get_connection() as conn:
            # Check if group exists
            group = self.get_group(group_id)
            if not group:
                msg = f"Group {group_id} bestaat niet"
                raise ValueError(msg)

            canonical_term = group.canonical_term

            # Check for members
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count FROM synonym_group_members
                WHERE group_id = ?
                """,
                (group_id,),
            )
            member_count = cursor.fetchone()["count"]

            if member_count > 0 and not cascade:
                msg = (
                    f"Group {group_id} ('{canonical_term}') heeft "
                    f"{member_count} members. "
                    f"Gebruik cascade=True om group + members te verwijderen."
                )
                raise ValueError(msg)

            # Delete members first if cascade (or if any exist)
            if member_count > 0:
                # Get all member terms for cache invalidation
                cursor = conn.execute(
                    """
                    SELECT DISTINCT term FROM synonym_group_members
                    WHERE group_id = ?
                    """,
                    (group_id,),
                )
                member_terms = [row["term"] for row in cursor.fetchall()]

                # Delete all members
                cursor = conn.execute(
                    "DELETE FROM synonym_group_members WHERE group_id = ?",
                    (group_id,),
                )
                deleted_members = cursor.rowcount

                logger.info(
                    f"Deleted {deleted_members} members from group "
                    f"{group_id} ('{canonical_term}')"
                )

                # Trigger cache invalidation for all deleted members
                for term in member_terms:
                    self._trigger_invalidation(term)

            # Delete the group
            cursor = conn.execute(
                "DELETE FROM synonym_groups WHERE id = ?",
                (group_id,),
            )

            success = cursor.rowcount > 0

            if success:
                mode = f"with {member_count} members" if member_count > 0 else "(empty)"
                logger.info(f"Deleted group {group_id} ('{canonical_term}') {mode}")
                # Trigger cache invalidation for canonical term
                self._trigger_invalidation(canonical_term)

            return success

    # ========================================
    # MEMBER OPERATIONS
    # ========================================

    def add_group_member(
        self,
        group_id: int,
        term: str,
        weight: float = 1.0,
        status: str = "active",
        source: str = "manual",
        definitie_id: int | None = None,
        context_json: str | None = None,
        created_by: str = "system",
    ) -> int:
        """
        Voeg member toe aan groep.

        Args:
            group_id: ID van de groep
            term: De term om toe te voegen
            weight: Gewicht voor ranking (0.0-1.0)
            status: Status (active, ai_pending, rejected_auto, deprecated)
            source: Bron (db_seed, manual, ai_suggested, imported_yaml)
            definitie_id: Optioneel scope naar definitie (NULL = global)
            context_json: Optionele context als JSON string
            created_by: Wie voegt member toe

        Returns:
            ID van nieuw toegevoegde member

        Raises:
            ValueError: Bij ongeldige parameters of duplicate (group_id, term)
        """
        # Validate parameters
        if not term or not term.strip():
            msg = "term mag niet leeg zijn"
            raise ValueError(msg)

        if not (0.0 <= weight <= 1.0):
            msg = f"weight moet tussen 0.0 en 1.0 zijn: {weight}"
            raise ValueError(msg)

        valid_statuses = {"active", "ai_pending", "rejected_auto", "deprecated"}
        if status not in valid_statuses:
            msg = f"status moet een van {valid_statuses} zijn: {status}"
            raise ValueError(msg)

        valid_sources = {"db_seed", "manual", "ai_suggested", "imported_yaml"}
        if source not in valid_sources:
            msg = f"source moet een van {valid_sources} zijn: {source}"
            raise ValueError(msg)

        term = term.strip()

        with self._get_connection() as conn:
            # Check if group exists
            if not self.get_group(group_id):
                msg = f"Group {group_id} bestaat niet"
                raise ValueError(msg)

            # Check for duplicate (group_id, term) constraint
            cursor = conn.execute(
                """
                SELECT id FROM synonym_group_members
                WHERE group_id = ? AND term = ?
                """,
                (group_id, term),
            )
            existing = cursor.fetchone()
            if existing:
                msg = f"Member '{term}' bestaat al in groep {group_id} (ID: {existing[0]})"
                raise ValueError(msg)

            # Insert member
            now = datetime.now(UTC)
            cursor = conn.execute(
                """
                INSERT INTO synonym_group_members (
                    group_id, term, weight, is_preferred, status, source,
                    context_json, definitie_id, usage_count, created_at,
                    updated_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    group_id,
                    term,
                    weight,
                    False,  # is_preferred default
                    status,
                    source,
                    context_json,
                    definitie_id,
                    0,  # usage_count default
                    now,
                    now,
                    created_by,
                ),
            )

            member_id = cursor.lastrowid

            logger.info(
                f"Added member {member_id}: '{term}' to group {group_id} "
                f"(weight: {weight}, status: {status}, source: {source})"
            )

            # Trigger cache invalidation
            self._trigger_invalidation(term)

            return member_id

    def get_group_members(
        self,
        group_id: int,
        statuses: list[str] | None = None,
        min_weight: float = 0.0,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[SynonymGroupMember]:
        """
        Haal members van groep op met optionele filters.

        Args:
            group_id: ID van de groep
            statuses: Filter op statuses (None = alle)
            min_weight: Minimum gewicht threshold
            filters: Extra filters als dict (definitie_id, source, etc.)
            order_by: Sorteer volgorde (moet een van: weight, is_preferred, term,
                created_at, updated_at, usage_count, status zijn)
                Default: is_preferred DESC, weight DESC, usage_count DESC
            limit: Maximum aantal resultaten

        Returns:
            Lijst van SynonymGroupMember objecten

        Raises:
            ValueError: Als order_by niet in whitelist staat
        """
        # Validate order_by parameter (SQL injection prevention)
        # Check for non-None and non-empty string
        if order_by is not None and (
            not order_by or order_by not in _VALID_ORDER_BY_COLUMNS
        ):
            msg = (
                f"Invalid order_by column: '{order_by}'. "
                f"Allowed: {', '.join(sorted(_VALID_ORDER_BY_COLUMNS))}"
            )
            raise ValueError(msg)

        with self._get_connection() as conn:
            query = "SELECT * FROM synonym_group_members WHERE group_id = ?"
            params: list[Any] = [group_id]

            # Status filter
            if statuses:
                placeholders = ", ".join("?" for _ in statuses)
                query += f" AND status IN ({placeholders})"
                params.extend(statuses)

            # Weight filter
            query += " AND weight >= ?"
            params.append(min_weight)

            # Extra filters
            if filters:
                if "definitie_id" in filters:
                    if filters["definitie_id"] is None:
                        query += " AND definitie_id IS NULL"
                    else:
                        query += " AND definitie_id = ?"
                        params.append(filters["definitie_id"])

                if "source" in filters:
                    query += " AND source = ?"
                    params.append(filters["source"])

                if "is_preferred" in filters:
                    query += " AND is_preferred = ?"
                    params.append(filters["is_preferred"])

            # Order by
            if order_by:
                query += f" ORDER BY {order_by}"
            else:
                query += " ORDER BY is_preferred DESC, weight DESC, usage_count DESC"

            # Limit
            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor = conn.execute(query, params)
            return [self._row_to_member(row) for row in cursor.fetchall()]

    def get_member(self, member_id: int) -> SynonymGroupMember | None:
        """
        Haal specifieke member op op basis van ID.

        Args:
            member_id: Database ID van de member

        Returns:
            SynonymGroupMember of None als niet gevonden
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM synonym_group_members WHERE id = ?", (member_id,)
            )
            row = cursor.fetchone()
            return self._row_to_member(row) if row else None

    def update_member_status(
        self,
        member_id: int,
        new_status: str,
        reviewed_by: str,
        reviewed_at: datetime | None = None,
    ) -> bool:
        """
        Update status van een member (governance flow).

        Args:
            member_id: ID van de member
            new_status: Nieuwe status (active, ai_pending, rejected_auto, deprecated)
            reviewed_by: Wie de status update uitvoert
            reviewed_at: Tijdstip van review (default: now)

        Returns:
            True als succesvol geupdate

        Raises:
            ValueError: Bij ongeldige status
        """
        valid_statuses = {"active", "ai_pending", "rejected_auto", "deprecated"}
        if new_status not in valid_statuses:
            msg = f"status moet een van {valid_statuses} zijn: {new_status}"
            raise ValueError(msg)

        with self._get_connection() as conn:
            # Check if member exists
            member = self.get_member(member_id)
            if not member:
                logger.warning(f"Member {member_id} niet gevonden")
                return False

            # Update status
            reviewed_at = reviewed_at or datetime.now(UTC)
            cursor = conn.execute(
                """
                UPDATE synonym_group_members
                SET status = ?,
                    reviewed_by = ?,
                    reviewed_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (new_status, reviewed_by, reviewed_at, datetime.now(UTC), member_id),
            )

            success = cursor.rowcount > 0

            if success:
                logger.info(
                    f"Updated member {member_id} ('{member.term}') status to {new_status}"
                )
                # Trigger cache invalidation
                self._trigger_invalidation(member.term)

            return success

    def get_synonyms(
        self,
        term: str,
        statuses: list[str] | None = None,
        min_weight: float = 0.0,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[WeightedSynonym]:
        """
        Bidirectionele lookup: haal alle synoniemen voor term op.

        Dit is de CORE query van de synonym registry:
        1. Vind groep waar term lid van is
        2. Haal alle andere members van die groep op
        3. Sorteer op is_preferred DESC, weight DESC, usage_count DESC

        Args:
            term: De term om synoniemen voor te vinden
            statuses: Filter op statuses (default: ['active'])
            min_weight: Minimum gewicht threshold
            order_by: Custom sorteer volgorde (moet een van: weight, is_preferred, term,
                created_at, updated_at, usage_count, status zijn)
                Default: is_preferred DESC, weight DESC, usage_count DESC
            limit: Maximum aantal resultaten

        Returns:
            Lijst van WeightedSynonym objecten (lightweight)

        Raises:
            ValueError: Als order_by niet in whitelist staat

        Architecture Reference:
            Lines 188-204: Bidirectional lookup query specification
        """
        if not term or not term.strip():
            return []

        # Validate order_by parameter (SQL injection prevention)
        # Check for non-None and non-empty string
        if order_by is not None and (
            not order_by or order_by not in _VALID_ORDER_BY_COLUMNS
        ):
            msg = (
                f"Invalid order_by column: '{order_by}'. "
                f"Allowed: {', '.join(sorted(_VALID_ORDER_BY_COLUMNS))}"
            )
            raise ValueError(msg)

        statuses = statuses or ["active"]
        term = term.strip()

        with self._get_connection() as conn:
            # First: find group_id where term is canonical_term OR a member
            # Use subquery to get group_id, then get all members
            query = """
                SELECT DISTINCT
                    m.term,
                    m.weight,
                    m.status,
                    m.is_preferred,
                    m.usage_count
                FROM synonym_group_members m
                WHERE m.group_id IN (
                    -- Find group where term is canonical_term
                    SELECT id FROM synonym_groups WHERE canonical_term = ?
                    UNION
                    -- Find group where term is a member
                    SELECT group_id FROM synonym_group_members WHERE term = ?
                )
                AND m.term != ?
                AND m.weight >= ?
            """
            params: list[Any] = [term, term, term, min_weight]

            # Status filter
            if statuses:
                placeholders = ", ".join("?" for _ in statuses)
                query += f" AND m.status IN ({placeholders})"
                params.extend(statuses)

            # Order by
            if order_by:
                # Prefix with m. for column reference
                query += f" ORDER BY m.{order_by}"
            else:
                query += (
                    " ORDER BY m.is_preferred DESC, m.weight DESC, m.usage_count DESC"
                )

            # Limit
            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor = conn.execute(query, params)

            results = []
            for row in cursor.fetchall():
                results.append(
                    WeightedSynonym(
                        term=row["term"],
                        weight=row["weight"],
                        status=row["status"],
                        is_preferred=bool(row["is_preferred"]),
                        usage_count=row["usage_count"],
                    )
                )

            logger.debug(
                f"Found {len(results)} synonyms for '{term}' "
                f"(statuses: {statuses}, min_weight: {min_weight})"
            )

            return results

    # ========================================
    # CACHE INVALIDATION
    # ========================================

    def register_invalidation_callback(self, callback: Callable[[str], None]):
        """
        Registreer callback voor cache updates.

        Callback wordt aangeroepen met term als parameter wanneer
        synonym data voor die term verandert.

        Args:
            callback: Callable die term accepteert als parameter
        """
        self._invalidation_callbacks.append(callback)
        logger.debug(
            f"Registered invalidation callback: {callback.__name__} "
            f"(total: {len(self._invalidation_callbacks)})"
        )

    def _trigger_invalidation(self, term: str):
        """
        Trigger alle cache invalidation callbacks voor term.

        Args:
            term: De term waarvoor cache invalidatie nodig is
        """
        if not self._invalidation_callbacks:
            return

        logger.debug(
            f"Triggering {len(self._invalidation_callbacks)} "
            f"invalidation callbacks for term '{term}'"
        )

        for callback in self._invalidation_callbacks:
            try:
                callback(term)
            except Exception as e:
                logger.error(
                    f"Invalidation callback {callback.__name__} failed for '{term}': {e}"
                )

    # ========================================
    # STATISTICS
    # ========================================

    def get_statistics(self) -> dict[str, Any]:
        """
        Haal statistieken op over synonym registry.

        Returns:
            Dictionary met statistieken:
            - total_groups: Aantal groepen
            - total_members: Aantal members
            - members_by_status: Count per status
            - members_by_source: Count per source
            - avg_group_size: Gemiddeld aantal members per groep
            - top_groups: Grootste groepen (canonical_term + size)
        """
        with self._get_connection() as conn:
            stats = {}

            # Total groups
            cursor = conn.execute("SELECT COUNT(*) as count FROM synonym_groups")
            stats["total_groups"] = cursor.fetchone()["count"]

            # Total members
            cursor = conn.execute("SELECT COUNT(*) as count FROM synonym_group_members")
            stats["total_members"] = cursor.fetchone()["count"]

            # Members by status
            cursor = conn.execute(
                """
                SELECT status, COUNT(*) as count
                FROM synonym_group_members
                GROUP BY status
                """
            )
            stats["members_by_status"] = dict(cursor.fetchall())

            # Members by source
            cursor = conn.execute(
                """
                SELECT source, COUNT(*) as count
                FROM synonym_group_members
                GROUP BY source
                """
            )
            stats["members_by_source"] = dict(cursor.fetchall())

            # Average group size
            if stats["total_groups"] > 0:
                stats["avg_group_size"] = round(
                    stats["total_members"] / stats["total_groups"], 2
                )
            else:
                stats["avg_group_size"] = 0.0

            # Top 10 largest groups
            cursor = conn.execute(
                """
                SELECT
                    g.canonical_term,
                    g.domain,
                    COUNT(m.id) as member_count
                FROM synonym_groups g
                LEFT JOIN synonym_group_members m ON m.group_id = g.id
                GROUP BY g.id
                ORDER BY member_count DESC
                LIMIT 10
                """
            )
            stats["top_groups"] = [
                {
                    "canonical_term": row["canonical_term"],
                    "domain": row["domain"],
                    "member_count": row["member_count"],
                }
                for row in cursor.fetchall()
            ]

            return stats

    def get_top_used_synonyms(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Haal meest gebruikte synoniemen op (voor metrics dashboard).

        Args:
            limit: Maximum aantal resultaten (default: 20)

        Returns:
            Lijst van dictionaries met:
            - term: Synonym term
            - usage_count: Aantal keer gebruikt
            - weight: Gewicht
            - group: Canonical term van groep
            - last_used: Laatste gebruik timestamp (of None)
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    m.term,
                    m.usage_count,
                    m.weight,
                    g.canonical_term as group_term,
                    m.last_used_at
                FROM synonym_group_members m
                JOIN synonym_groups g ON m.group_id = g.id
                WHERE m.status = 'active'
                ORDER BY m.usage_count DESC, m.weight DESC
                LIMIT ?
                """,
                (limit,),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "term": row["term"],
                        "usage_count": row["usage_count"],
                        "weight": row["weight"],
                        "group": row["group_term"],
                        "last_used": row["last_used_at"],
                    }
                )

            return results

    def get_all_members(
        self,
        statuses: list[str] | None = None,
        min_weight: float = 0.0,
        term_search: str | None = None,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[SynonymGroupMember]:
        """
        Haal ALLE members op over ALLE groepen (admin/review use case).

        BELANGRIJK: Deze query haalt potentieel ALLE members op, gebruik met zorg!
        Voor performance: gebruik filters (statuses, min_weight, limit).

        Args:
            statuses: Filter op statuses (None = alle)
            min_weight: Minimum gewicht threshold
            term_search: Filter op term (fuzzy match, case-insensitive)
            order_by: Sorteer volgorde (moet een van: weight, is_preferred, term,
                created_at, updated_at, usage_count, status zijn)
                Default: weight DESC, usage_count DESC
            limit: Maximum aantal resultaten

        Returns:
            Lijst van SynonymGroupMember objecten

        Raises:
            ValueError: Als order_by niet in whitelist staat

        Architecture Reference:
            Gebruikt door synonym_admin.py voor review interface
        """
        # Validate order_by parameter (SQL injection prevention)
        if order_by is not None and (
            not order_by or order_by not in _VALID_ORDER_BY_COLUMNS
        ):
            msg = (
                f"Invalid order_by column: '{order_by}'. "
                f"Allowed: {', '.join(sorted(_VALID_ORDER_BY_COLUMNS))}"
            )
            raise ValueError(msg)

        with self._get_connection() as conn:
            query = "SELECT * FROM synonym_group_members WHERE 1=1"
            params: list[Any] = []

            # Status filter
            if statuses:
                placeholders = ", ".join("?" for _ in statuses)
                query += f" AND status IN ({placeholders})"
                params.extend(statuses)

            # Weight filter
            query += " AND weight >= ?"
            params.append(min_weight)

            # Term search filter (fuzzy match, case-insensitive)
            if term_search and term_search.strip():
                query += " AND term LIKE ?"
                params.append(f"%{term_search.strip().lower()}%")

            # Order by
            if order_by:
                query += f" ORDER BY {order_by}"
            else:
                query += " ORDER BY weight DESC, usage_count DESC"

            # Limit
            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor = conn.execute(query, params)
            members = [self._row_to_member(row) for row in cursor.fetchall()]

            logger.debug(
                f"get_all_members returned {len(members)} members "
                f"(statuses: {statuses}, min_weight: {min_weight}, term_search: '{term_search}')"
            )

            return members

    # ========================================
    # INTERNAL HELPERS
    # ========================================

    def _row_to_group(self, row: sqlite3.Row) -> SynonymGroup:
        """
        Converteer database row naar SynonymGroup.

        Note: With PARSE_DECLTYPES enabled (Python 3.12+ fix), TIMESTAMP columns
        are automatically converted to datetime objects by our custom converter.
        """
        return SynonymGroup(
            id=row["id"],
            canonical_term=row["canonical_term"],
            domain=row["domain"],
            # Datetime fields are auto-converted by PARSE_DECLTYPES + custom converter
            created_at=row["created_at"],  # Already datetime or None
            updated_at=row["updated_at"],  # Already datetime or None
            created_by=row["created_by"],
        )

    def _row_to_member(self, row: sqlite3.Row) -> SynonymGroupMember:
        """
        Converteer database row naar SynonymGroupMember.

        Note: With PARSE_DECLTYPES enabled (Python 3.12+ fix), TIMESTAMP columns
        are automatically converted to datetime objects by our custom converter.
        """
        return SynonymGroupMember(
            id=row["id"],
            group_id=row["group_id"],
            term=row["term"],
            weight=row["weight"],
            is_preferred=bool(row["is_preferred"]),
            status=row["status"],
            source=row["source"],
            context_json=row["context_json"],
            definitie_id=row["definitie_id"],
            usage_count=row["usage_count"],
            # Datetime fields are auto-converted by PARSE_DECLTYPES + custom converter
            last_used_at=row["last_used_at"],  # Already datetime or None
            created_at=row["created_at"],  # Already datetime or None
            updated_at=row["updated_at"],  # Already datetime or None
            created_by=row["created_by"],
            reviewed_by=row["reviewed_by"],
            reviewed_at=row["reviewed_at"],  # Already datetime or None
        )


# Convenience function
def get_synonym_registry(db_path: str | None = None) -> SynonymRegistry:
    """Haal gedeelde registry instance op."""
    if not db_path:
        # Default database in project directory
        project_root = Path(__file__).parent.parent.parent
        db_path = str(project_root / "data" / "definities.db")

    return SynonymRegistry(db_path)
