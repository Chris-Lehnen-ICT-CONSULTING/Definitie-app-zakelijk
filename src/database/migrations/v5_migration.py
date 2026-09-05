#!/usr/bin/env python3
"""V5 Database Migration for Definitie-app (DEF-303).

Creates 8 new tables for RAG, Ontology, and Projects functionality,
plus a schema_version table for future migration tracking.

This migration is fully idempotent: running it multiple times is safe.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import cast  # DEF-439

from database.sqlite_backup import (  # DEF-663
    BackupError,
    create_verified_backup,
    open_readonly_snapshot,
    read_manifest,
    verify_backup_file,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DB_PATH = Path("data/definities.db")
MIGRATION_VERSION = 1
MIGRATION_DESCRIPTION = "Initial v5 migration"

# Expected tables BEFORE migration (for verification).
# sqlite_sequence is auto-managed by SQLite and excluded.
EXPECTED_EXISTING_TABLES: set[str] = {
    "definitie_drafts",
    "definitie_geschiedenis",
    "definitie_tags",
    "definitie_voorbeelden",
    "definities",
    "generation_logs",
    "import_export_logs",
    "performance_baselines",
    "performance_metrics",
    "synonym_group_members",
    "synonym_groups",
    "synonym_suggestions",
}

# Tables created by this migration
NEW_TABLES: list[str] = [
    "schema_version",
    "rag_collections",
    "rag_documents",
    "rag_chunks",
    "ontological_models",
    "ontology_terms",
    "ontology_relationships",
    "projects",
]

# ---------------------------------------------------------------------------
# SQL Statements
# ---------------------------------------------------------------------------
SQL_SCHEMA_VERSION = """
CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version INTEGER NOT NULL,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_RAG_COLLECTIONS = """
CREATE TABLE IF NOT EXISTS rag_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_name VARCHAR(255) NOT NULL UNIQUE,
    document_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT
);
"""

SQL_RAG_DOCUMENTS = """
CREATE TABLE IF NOT EXISTS rag_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER REFERENCES rag_collections(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    file_type VARCHAR(50),
    chunk_count INTEGER,
    rechtsgebied VARCHAR(100),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_RAG_CHUNKS = """
CREATE TABLE IF NOT EXISTS rag_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER REFERENCES rag_collections(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES rag_documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding BLOB,
    chunk_index INTEGER,
    rechtsgebied VARCHAR(100),
    wet_regeling VARCHAR(255),
    artikel_lid VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_RAG_CHUNKS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_chunks_collection ON rag_chunks(collection_id);",
    "CREATE INDEX IF NOT EXISTS idx_chunks_document ON rag_chunks(document_id);",
]

SQL_ONTOLOGICAL_MODELS = """
CREATE TABLE IF NOT EXISTS ontological_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name VARCHAR(255) NOT NULL,
    version_number INTEGER DEFAULT 1,
    parent_version_id INTEGER REFERENCES ontological_models(id),
    rag_collection_id INTEGER REFERENCES rag_collections(id),
    validation_status VARCHAR(50) DEFAULT 'draft',
    validation_score DECIMAL(3,2),
    snapshot_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
"""

SQL_ONTOLOGY_TERMS = """
CREATE TABLE IF NOT EXISTS ontology_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER REFERENCES ontological_models(id) ON DELETE CASCADE,
    term_text VARCHAR(255) NOT NULL,
    categorie_6 VARCHAR(50),
    ufo_categorie VARCHAR(50),
    classification_confidence DECIMAL(3,2),
    wettelijke_basis VARCHAR(255),
    rechtsgebied VARCHAR(100),
    rag_context_summary TEXT
);
"""

SQL_ONTOLOGY_RELATIONSHIPS = """
CREATE TABLE IF NOT EXISTS ontology_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER REFERENCES ontological_models(id) ON DELETE CASCADE,
    source_term_id INTEGER REFERENCES ontology_terms(id) ON DELETE CASCADE,
    target_term_id INTEGER REFERENCES ontology_terms(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50),
    confidence_score DECIMAL(3,2),
    inferred_by VARCHAR(50) DEFAULT 'manual'
);
"""

SQL_ONTOLOGY_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_ont_terms_model ON ontology_terms(model_id);",
    "CREATE INDEX IF NOT EXISTS idx_ont_rels_model ON ontology_relationships(model_id);",
]

SQL_PROJECTS = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name VARCHAR(255) NOT NULL,
    description TEXT,
    rag_collection_id INTEGER REFERENCES rag_collections(id),
    ontology_model_id INTEGER REFERENCES ontological_models(id),
    phase_rag_status VARCHAR(50) DEFAULT 'not_started',
    phase_ontology_status VARCHAR(50) DEFAULT 'not_started',
    phase_definition_status VARCHAR(50) DEFAULT 'not_started',
    phase_validation_status VARCHAR(50) DEFAULT 'not_started',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
"""


# ---------------------------------------------------------------------------
# Helper: get all user tables (excluding sqlite internal tables)
# ---------------------------------------------------------------------------
def _get_table_names(conn: sqlite3.Connection) -> list[str]:
    """Return sorted list of user table names (excludes sqlite_sequence)."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name != 'sqlite_sequence' "
        "ORDER BY name"
    )
    return [row[0] for row in cursor.fetchall()]


def _get_row_count(conn: sqlite3.Connection, table: str) -> int:
    """Return the row count for a given table."""
    cursor = conn.execute(f"SELECT COUNT(*) FROM [{table}]")
    return cast(int, cursor.fetchone()[0])  # DEF-439: pattern 3


# ---------------------------------------------------------------------------
# Stap 0: Backup
# ---------------------------------------------------------------------------
def create_backup(db_path: Path) -> Path:
    """Create a timestamped, WAL-safe and verified backup of the database.

    Delegates to ``database.sqlite_backup`` (DEF-663): the backup is taken via
    the SQLite Online Backup API from a read-only snapshot, verified
    (integrity_check + schema manifest) and only then published. The
    timestamp carries microseconds so consecutive runs never collide with an
    existing backup, which the helper refuses to overwrite.

    Returns the path to the backup file.
    Raises FileNotFoundError if the database is missing and RuntimeError if
    the backup is refused or fails verification (no file is left behind).
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_path = backup_dir / f"pre_v5_migration_{timestamp}.db"

    logger.info("Creating backup: %s -> %s", db_path, backup_path)
    try:
        create_verified_backup(db_path, backup_path)
    except BackupError as exc:
        raise RuntimeError(
            f"Backup failed ({exc.reason}) — migration aborted"
        ) from None

    logger.info("Backup verified successfully: %s", backup_path)
    return backup_path


def verify_backup(backup_path: Path, original_path: Path) -> bool:
    """Verify that the backup is a faithful copy of the original.

    Checks (DEF-663, shared verifier ``database.sqlite_backup.verify_backup_file``):
    1. ``PRAGMA integrity_check`` on the backup is exactly ``ok``
    2. The application core schema (definities, geschiedenis, voorbeelden,
       synoniemen, ...) is present in the backup
    3. The full schema manifest (objects, columns, row counts, schema_version)
       of the backup equals that of the original

    Note: this reads a fresh snapshot of the original; a commit on the original
    after the backup legitimately makes this return False.
    """
    try:
        original_conn = open_readonly_snapshot(original_path)
        try:
            expected = read_manifest(original_conn)
        finally:
            original_conn.close()
        verify_backup_file(backup_path, expected)
    except BackupError as exc:
        logger.error("Backup verification failed: %s", exc.reason)
        return False
    except sqlite3.Error:
        logger.error("Backup verification failed: original_unreadable")
        return False

    logger.info("Backup verified: integrity ok, core schema present, manifest matches")
    return True


# ---------------------------------------------------------------------------
# Stap 1: Schema versioning
# ---------------------------------------------------------------------------
def apply_schema_version(conn: sqlite3.Connection) -> None:
    """Create schema_version table and insert version 1 (idempotent)."""
    conn.execute(SQL_SCHEMA_VERSION)

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
# Stap 2: Create new tables
# ---------------------------------------------------------------------------
def create_new_tables(conn: sqlite3.Connection) -> None:
    """Create all 8 new tables and indexes (idempotent via IF NOT EXISTS)."""
    table_sql_pairs: list[tuple[str, str]] = [
        ("rag_collections", SQL_RAG_COLLECTIONS),
        ("rag_documents", SQL_RAG_DOCUMENTS),
        ("rag_chunks", SQL_RAG_CHUNKS),
        ("ontological_models", SQL_ONTOLOGICAL_MODELS),
        ("ontology_terms", SQL_ONTOLOGY_TERMS),
        ("ontology_relationships", SQL_ONTOLOGY_RELATIONSHIPS),
        ("projects", SQL_PROJECTS),
    ]

    for table_name, sql in table_sql_pairs:
        conn.execute(sql)
        logger.info("Ensured table exists: %s", table_name)

    # Create indexes
    for idx_sql in SQL_RAG_CHUNKS_INDEXES + SQL_ONTOLOGY_INDEXES:
        conn.execute(idx_sql)

    logger.info("All indexes created/verified")

    # DEF-356: file_path kolom voor upload-opslag
    _add_column_if_not_exists(conn, "rag_documents", "file_path", "VARCHAR(500)")


_ALLOWED_COL_TYPES = frozenset(
    {
        "TEXT",
        "INTEGER",
        "REAL",
        "BLOB",
        "BOOLEAN",
        "VARCHAR(100)",
        "VARCHAR(255)",
        "VARCHAR(500)",
        "TIMESTAMP",
        "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    }
)


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


# ---------------------------------------------------------------------------
# Stap 3: Verification
# ---------------------------------------------------------------------------
def verify_migration(conn: sqlite3.Connection) -> bool:
    """Verify the migration completed successfully.

    Checks:
    1. All 12 original tables still exist
    2. All 8 new tables exist
    3. schema_version has version 1
    """
    all_ok = True
    tables_in_db = set(_get_table_names(conn))

    # --- Check original tables ---
    logger.info("--- Verifying original tables ---")
    for table_name in sorted(EXPECTED_EXISTING_TABLES):
        if table_name not in tables_in_db:
            logger.error("MISSING original table: %s", table_name)
            all_ok = False
        else:
            count = _get_row_count(conn, table_name)
            logger.info("  %s: %d rows (OK)", table_name, count)

    # --- Check new tables ---
    logger.info("--- Verifying new tables ---")
    for table_name in NEW_TABLES:
        if table_name not in tables_in_db:
            logger.error("MISSING new table: %s", table_name)
            all_ok = False
        else:
            count = _get_row_count(conn, table_name)
            logger.info("  %s: %d rows (OK)", table_name, count)

    # --- Check schema_version entry ---
    logger.info("--- Verifying schema_version ---")
    try:
        cursor = conn.execute(
            "SELECT version, description, applied_at "
            "FROM schema_version WHERE version = ?",
            (MIGRATION_VERSION,),
        )
        row = cursor.fetchone()
        if row is None:
            logger.error(
                "schema_version does not contain version %d",
                MIGRATION_VERSION,
            )
            all_ok = False
        else:
            logger.info(
                "  schema_version: version=%d, description='%s', applied_at=%s (OK)",
                row[0],
                row[1],
                row[2],
            )
    except sqlite3.OperationalError:
        logger.error("schema_version table does not exist")
        all_ok = False

    return all_ok


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------
def run_migration(db_path: Path = DB_PATH) -> bool:
    """Run the complete V5 migration.

    Args:
        db_path: Path to the SQLite database (default: data/definities.db).

    Returns:
        True if migration succeeded, False otherwise.
    """
    logger.info("=" * 60)
    logger.info("V5 Migration (DEF-303) — Start")
    logger.info("=" * 60)
    logger.info("Database: %s", db_path.resolve())

    # --- Stap 0: Backup ---
    logger.info("")
    logger.info("STAP 0: Creating backup")
    logger.info("-" * 40)
    try:
        backup_path = create_backup(db_path)
    except (FileNotFoundError, RuntimeError) as exc:
        logger.error("Backup failed: %s", exc)
        logger.error("Migration ABORTED — no changes were made")
        return False

    # --- Connect ---
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
    except sqlite3.Error as exc:
        logger.error("Failed to connect to database: %s", exc)
        return False

    try:
        # --- Stap 1: Schema versioning ---
        logger.info("")
        logger.info("STAP 1: Schema versioning")
        logger.info("-" * 40)
        apply_schema_version(conn)

        # --- Stap 2: Create new tables ---
        logger.info("")
        logger.info("STAP 2: Creating new tables")
        logger.info("-" * 40)
        create_new_tables(conn)

        # Commit all DDL changes
        conn.commit()
        logger.info("All changes committed")

        # --- Stap 3: Verification ---
        logger.info("")
        logger.info("STAP 3: Verification")
        logger.info("-" * 40)
        success = verify_migration(conn)

        if success:
            logger.info("")
            logger.info("=" * 60)
            logger.info("V5 Migration COMPLETED SUCCESSFULLY")
            logger.info("  Backup: %s", backup_path)
            logger.info("  New tables: %d", len(NEW_TABLES))
            logger.info("=" * 60)
        else:
            logger.error("")
            logger.error("=" * 60)
            logger.error("V5 Migration completed WITH WARNINGS/ERRORS")
            logger.error("  Review the log output above for details")
            logger.error("  Backup available at: %s", backup_path)
            logger.error("=" * 60)

        return success

    except sqlite3.Error as exc:
        logger.error("Database error during migration: %s", exc)
        logger.error("Rolling back transaction")
        conn.rollback()
        logger.error("Backup available at: %s", backup_path)
        return False
    except Exception as exc:
        logger.error("Unexpected error during migration: %s", exc)
        conn.rollback()
        logger.error("Backup available at: %s", backup_path)
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
