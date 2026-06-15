"""V6 Database Migration: hybride schema voor rag_chunks (DEF-370).

Voegt bron_type en metadata kolommen toe aan rag_chunks.
Migreert bestaande artikel_lid data naar JSONB metadata.
Creëert indexes voor pre-retrieval filtering.

schema_version = 2.

Deze migratie is volledig idempotent: herhaald uitvoeren is veilig.
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DB_PATH = Path("data/definities.db")
MIGRATION_VERSION = 2
MIGRATION_DESCRIPTION = "Hybrid schema: bron_type + JSONB metadata on rag_chunks"

# Metadata schema conventie per bron_type.
# Basis voor Pydantic validatie in DEF-374.
METADATA_KEYS_PER_BRON_TYPE: dict[str, list[str]] = {
    "wetgeving": ["artikel_nummer", "lid_nummer", "structuur_type"],
    "website": ["url", "scrape_datum", "pagina_titel"],
    "pdf": ["bronbestand", "pagina_nummer", "sectie"],
    "api": ["endpoint", "response_datum"],
}

# Allowed column types for DDL (cannot be parameterized).
_ALLOWED_COL_TYPES = frozenset(
    {
        "VARCHAR(50)",
        "TEXT DEFAULT '{}'",
    }
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _add_column_if_not_exists(
    conn: sqlite3.Connection, table: str, column: str, col_type: str
) -> None:
    """Voeg kolom toe als die nog niet bestaat (idempotent).

    col_type moet in _ALLOWED_COL_TYPES staan (DDL kan niet geparameteriseerd).
    """
    if col_type not in _ALLOWED_COL_TYPES:
        raise ValueError(f"Onbekend kolomtype: {col_type!r}")
    try:
        conn.execute(f"ALTER TABLE [{table}] ADD COLUMN [{column}] {col_type}")
        logger.info("Column '%s' added to table '%s'", column, table)
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            logger.info("Column '%s' already exists in '%s'", column, table)
        else:
            raise


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Check of een kolom bestaat in de tabel."""
    cursor = conn.execute(f"PRAGMA table_info([{table}])")
    return any(row[1] == column for row in cursor.fetchall())


# ---------------------------------------------------------------------------
# Stap 1: Schema versioning
# ---------------------------------------------------------------------------
def apply_schema_version(conn: sqlite3.Connection) -> None:
    """Insert schema version 2 (idempotent)."""
    cursor = conn.execute(
        "SELECT id FROM schema_version WHERE version = ?",
        (MIGRATION_VERSION,),
    )
    if cursor.fetchone() is not None:
        logger.info(
            "Schema version %d already exists — skipping insert",
            MIGRATION_VERSION,
        )
        return

    conn.execute(
        "INSERT INTO schema_version (version, description) VALUES (?, ?)",
        (MIGRATION_VERSION, MIGRATION_DESCRIPTION),
    )
    logger.info(
        "Inserted schema version %d: '%s'",
        MIGRATION_VERSION,
        MIGRATION_DESCRIPTION,
    )


# ---------------------------------------------------------------------------
# Stap 2: Nieuwe kolommen toevoegen
# ---------------------------------------------------------------------------
def add_columns(conn: sqlite3.Connection) -> None:
    """Voeg bron_type en metadata kolommen toe aan rag_chunks."""
    _add_column_if_not_exists(conn, "rag_chunks", "bron_type", "VARCHAR(50)")
    _add_column_if_not_exists(conn, "rag_chunks", "metadata", "TEXT DEFAULT '{}'")


# ---------------------------------------------------------------------------
# Stap 3: Data migratie (artikel_lid → JSONB metadata)
# ---------------------------------------------------------------------------
def migrate_data(conn: sqlite3.Connection) -> dict[str, int]:
    """Migreer bestaande data naar nieuwe kolommen.

    - artikel_lid → metadata.artikel_nummer (als JSONB)
    - rechtsgebied IS NOT NULL → bron_type = 'wetgeving'
    - Lege metadata → jsonb('{}')

    Returns:
        Dict met tellingen: metadata_migrated, bron_type_set, empty_filled
    """
    stats: dict[str, int] = {}

    # Migreer artikel_lid naar metadata JSON (alleen als metadata nog leeg)
    cursor = conn.execute("""
        UPDATE rag_chunks SET metadata = jsonb(json_object(
            'artikel_nummer', artikel_lid,
            'bronbestand', NULL,
            'structuur_type', NULL,
            'lid_nummer', NULL
        )) WHERE artikel_lid IS NOT NULL
          AND (metadata IS NULL OR metadata = '{}')
        """)
    stats["metadata_migrated"] = cursor.rowcount
    logger.info("Metadata gemigreerd voor %d chunks", cursor.rowcount)

    # Vul lege metadata met jsonb('{}')
    cursor = conn.execute(
        "UPDATE rag_chunks SET metadata = jsonb('{}') WHERE metadata IS NULL"
    )
    stats["empty_filled"] = cursor.rowcount
    logger.info("Lege metadata gevuld voor %d chunks", cursor.rowcount)

    # Zet bron_type = 'wetgeving' voor chunks met rechtsgebied
    cursor = conn.execute("""
        UPDATE rag_chunks SET bron_type = 'wetgeving'
        WHERE rechtsgebied IS NOT NULL AND bron_type IS NULL
        """)
    stats["bron_type_set"] = cursor.rowcount
    logger.info("bron_type gezet voor %d chunks", cursor.rowcount)

    return stats


# ---------------------------------------------------------------------------
# Stap 4: Indexes
# ---------------------------------------------------------------------------
def create_indexes(conn: sqlite3.Connection) -> None:
    """Maak indexes voor pre-retrieval filtering."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_chunks_rechtsgebied ON rag_chunks(rechtsgebied)",
        "CREATE INDEX IF NOT EXISTS idx_chunks_wet_regeling ON rag_chunks(wet_regeling)",
        "CREATE INDEX IF NOT EXISTS idx_chunks_bron_type ON rag_chunks(bron_type)",
    ]
    for sql in indexes:
        conn.execute(sql)
    logger.info("Alle filter-indexes aangemaakt/geverifieerd")


# ---------------------------------------------------------------------------
# Stap 5: Verificatie
# ---------------------------------------------------------------------------
def verify_migration(conn: sqlite3.Connection) -> bool:
    """Verifieer dat de migratie succesvol is.

    Checkt:
    1. bron_type en metadata kolommen bestaan
    2. Indexes bestaan
    3. schema_version heeft versie 2
    4. Geen chunks met NULL metadata
    """
    all_ok = True

    # Check kolommen
    for col in ("bron_type", "metadata"):
        if _column_exists(conn, "rag_chunks", col):
            logger.info("  Column '%s' exists (OK)", col)
        else:
            logger.error("  MISSING column: '%s'", col)
            all_ok = False

    # Check indexes
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='rag_chunks'"
    )
    existing_indexes = {row[0] for row in cursor.fetchall()}
    for idx_name in (
        "idx_chunks_rechtsgebied",
        "idx_chunks_wet_regeling",
        "idx_chunks_bron_type",
    ):
        if idx_name in existing_indexes:
            logger.info("  Index '%s' exists (OK)", idx_name)
        else:
            logger.error("  MISSING index: '%s'", idx_name)
            all_ok = False

    # Check schema_version
    cursor = conn.execute(
        "SELECT version FROM schema_version WHERE version = ?",
        (MIGRATION_VERSION,),
    )
    if cursor.fetchone() is not None:
        logger.info("  schema_version %d present (OK)", MIGRATION_VERSION)
    else:
        logger.error("  schema_version %d NOT found", MIGRATION_VERSION)
        all_ok = False

    return all_ok


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------
def run_migration(db_path: Path = DB_PATH) -> bool:
    """Run de V6 migratie.

    Args:
        db_path: Pad naar de SQLite database.

    Returns:
        True als de migratie geslaagd is.
    """
    logger.info("=" * 60)
    logger.info("V6 Migration (DEF-370) — Start")
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
        # Stap 1: Schema versioning
        logger.info("")
        logger.info("STAP 1: Schema versioning")
        logger.info("-" * 40)
        apply_schema_version(conn)

        # Stap 2: Nieuwe kolommen
        logger.info("")
        logger.info("STAP 2: Nieuwe kolommen toevoegen")
        logger.info("-" * 40)
        add_columns(conn)

        # Stap 3: Data migratie
        logger.info("")
        logger.info("STAP 3: Data migratie")
        logger.info("-" * 40)
        stats = migrate_data(conn)

        # Stap 4: Indexes
        logger.info("")
        logger.info("STAP 4: Indexes")
        logger.info("-" * 40)
        create_indexes(conn)

        conn.commit()
        logger.info("Alle wijzigingen gecommit")

        # Stap 5: Verificatie
        logger.info("")
        logger.info("STAP 5: Verificatie")
        logger.info("-" * 40)
        success = verify_migration(conn)

        if success:
            logger.info("")
            logger.info("=" * 60)
            logger.info("V6 Migration COMPLETED SUCCESSFULLY")
            logger.info("  metadata_migrated: %d", stats["metadata_migrated"])
            logger.info("  bron_type_set: %d", stats["bron_type_set"])
            logger.info("=" * 60)
        else:
            logger.error("")
            logger.error("=" * 60)
            logger.error("V6 Migration completed WITH ERRORS")
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
    success = run_migration()
    raise SystemExit(0 if success else 1)
