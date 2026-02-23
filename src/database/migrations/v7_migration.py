"""V7 Database Migration: verwijder dode teller-kolommen uit rag_collections (DEF-381).

document_count en chunk_count in rag_collections worden nooit bijgewerkt
en nooit uitgelezen — list_collections() en get_collection_stats() gebruiken
live COUNT(*) queries (zie DEF-363). De kolommen zijn dode technische schuld.

schema_version = 3.

Deze migratie is volledig idempotent: herhaald uitvoeren is veilig.
Vereist SQLite >= 3.35.0 (DROP COLUMN ondersteuning).
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DB_PATH = Path("data/definities.db")
MIGRATION_VERSION = 3
MIGRATION_DESCRIPTION = "Drop stale document_count/chunk_count from rag_collections"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Controleer of een kolom bestaat in een tabel."""
    rows = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
    return any(row[1] == column for row in rows)


# ---------------------------------------------------------------------------
# Stap 1: Schema versioning
# ---------------------------------------------------------------------------
def apply_schema_version(conn: sqlite3.Connection) -> None:
    """Insert schema version 3 (idempotent)."""
    existing = conn.execute(
        "SELECT id FROM schema_version WHERE version = ?",
        (MIGRATION_VERSION,),
    ).fetchone()
    if existing:
        logger.info(
            "Schema version %d already exists — skipping insert", MIGRATION_VERSION
        )
        return
    conn.execute(
        "INSERT INTO schema_version (version, description) VALUES (?, ?)",
        (MIGRATION_VERSION, MIGRATION_DESCRIPTION),
    )
    logger.info(
        "Inserted schema version %d: '%s'", MIGRATION_VERSION, MIGRATION_DESCRIPTION
    )


# ---------------------------------------------------------------------------
# Stap 2: Drop stale views
# ---------------------------------------------------------------------------
def drop_stale_views(conn: sqlite3.Connection) -> None:
    """Verwijder views die verwijzen naar niet-bestaande tabellen (idempotent).

    definities_with_generation en failed_generations refereren aan
    generation_logs_old die niet meer bestaat. SQLite valideert alle views
    bij ALTER TABLE DDL, waardoor DROP COLUMN anders faalt.
    Geen van deze views wordt gebruikt in de codebase.
    """
    for view in ("failed_generations", "definities_with_generation"):
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view' AND name=?", (view,)
        ).fetchone()
        if exists:
            conn.execute(f"DROP VIEW IF EXISTS [{view}]")
            logger.info("Stale view '%s' verwijderd", view)
        else:
            logger.info("View '%s' bestaat al niet — skip", view)


# ---------------------------------------------------------------------------
# Stap 3: Drop stale kolommen
# ---------------------------------------------------------------------------
def drop_stale_columns(conn: sqlite3.Connection) -> None:
    """Verwijder document_count en chunk_count uit rag_collections (idempotent)."""
    for column in ("document_count", "chunk_count"):
        if _column_exists(conn, "rag_collections", column):
            conn.execute(f"ALTER TABLE rag_collections DROP COLUMN [{column}]")
            logger.info("Kolom '%s' verwijderd uit rag_collections", column)
        else:
            logger.info("Kolom '%s' bestaat al niet — skip", column)


# ---------------------------------------------------------------------------
# Stap 3: Verificatie
# ---------------------------------------------------------------------------
def verify_migration(conn: sqlite3.Connection) -> bool:
    """Controleer dat de kolommen weg zijn en schema_version 3 aanwezig is."""
    all_ok = True

    for column in ("document_count", "chunk_count"):
        if _column_exists(conn, "rag_collections", column):
            logger.error("Kolom '%s' nog aanwezig in rag_collections — FAILED", column)
            all_ok = False
        else:
            logger.info("  rag_collections.%s afwezig (OK)", column)

    row = conn.execute(
        "SELECT version FROM schema_version WHERE version = ?",
        (MIGRATION_VERSION,),
    ).fetchone()
    if row:
        logger.info("  schema_version %d aanwezig (OK)", MIGRATION_VERSION)
    else:
        logger.error("  schema_version %d NIET gevonden", MIGRATION_VERSION)
        all_ok = False

    return all_ok


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------
def run_migration(db_path: Path = DB_PATH) -> bool:
    """Run de V7 migratie.

    Args:
        db_path: Pad naar de SQLite database.

    Returns:
        True als de migratie geslaagd is.
    """
    logger.info("=" * 60)
    logger.info("V7 Migration (DEF-381) — Start")
    logger.info("=" * 60)
    logger.info("Database: %s", db_path.resolve())

    if not db_path.exists():
        logger.error("Database niet gevonden: %s", db_path)
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
    except sqlite3.Error as exc:
        logger.error("Kan niet verbinden met database: %s", exc)
        return False

    try:
        logger.info("")
        logger.info("STAP 1: Schema versioning")
        logger.info("-" * 40)
        apply_schema_version(conn)

        logger.info("")
        logger.info("STAP 2: Drop stale views")
        logger.info("-" * 40)
        drop_stale_views(conn)

        logger.info("")
        logger.info("STAP 3: Drop stale kolommen")
        logger.info("-" * 40)
        drop_stale_columns(conn)

        conn.commit()
        logger.info("Alle wijzigingen gecommit")

        logger.info("")
        logger.info("STAP 4: Verificatie")
        logger.info("-" * 40)
        success = verify_migration(conn)

        if success:
            logger.info("")
            logger.info("=" * 60)
            logger.info("V7 Migration COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
        else:
            logger.error("")
            logger.error("=" * 60)
            logger.error("V7 Migration completed WITH ERRORS")
            logger.error("=" * 60)

        return success

    except sqlite3.Error as exc:
        logger.error("Database error tijdens migratie: %s", exc)
        conn.rollback()
        return False
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    import sys

    success = run_migration()
    sys.exit(0 if success else 1)
