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
from datetime import datetime
from pathlib import Path

from database.schema_contract import (  # DEF-664
    SchemaContractError,
    create_migration_backup,
    lost_objects,
    migration_transaction,
    require_migration_preconditions,
    schema_objects,
    schema_version,
    verify_target_contract,
)

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
    """Controleer of een kolom bestaat in een tabel.

    DEF-664: een ontbrekende tabel geeft een lege ``table_info`` en las dus
    als "kolom al verwijderd" — v7 meldde daardoor succes zonder
    ``rag_collections``. Een ontbrekende tabel is nu een harde fout.
    """
    rows = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
    if not rows:
        raise sqlite3.OperationalError(f"no such table: {table}")
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
STALE_VIEWS: tuple[str, ...] = ("failed_generations", "definities_with_generation")
STALE_VIEW_REFERENCE = "generation_logs_old"
_ONTBREKENDE_STALE_TABEL = {
    f"no such table: {STALE_VIEW_REFERENCE}",
    f"no such table: main.{STALE_VIEW_REFERENCE}",
}


def stale_views_present(conn: sqlite3.Connection) -> list[str]:
    """De historische views die daadwerkelijk stuk zijn op ``generation_logs_old``.

    DEF-664 (Codex-interimreview P1): noch de naam, noch een substring in de
    SQL is bewijs — een literal, alias of commentaar met dezelfde tekst hoort
    bij een geldige gebruikersview. Bewijs is de uitvoering: alleen een view
    die bij ``SELECT`` faalt met precies "no such table: generation_logs_old"
    is de bekende historische onbruikbare vorm. Een bruikbare view blijft
    staan; een view die om een ándere reden onbruikbaar is, is een
    twijfelgeval en laat de migratie fail-closed stoppen.
    """
    verouderd: list[str] = []
    for view in STALE_VIEWS:
        bestaat = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='view' AND name=?", (view,)
        ).fetchone()
        if not bestaat:
            continue
        try:
            conn.execute(f"SELECT * FROM [{view}] LIMIT 0")
        except sqlite3.OperationalError as exc:
            if str(exc).strip().lower() in _ONTBREKENDE_STALE_TABEL:
                verouderd.append(view)
                continue
            raise SchemaContractError(
                "stale_view_unresolvable", (f"view {view}: {type(exc).__name__}",)
            ) from exc
    return verouderd


def drop_stale_views(conn: sqlite3.Connection) -> None:
    """Verwijder uitsluitend de historische views die aantoonbaar stuk zijn op
    ``generation_logs_old`` (idempotent).

    SQLite valideert alle views bij ALTER TABLE DDL, waardoor DROP COLUMN
    anders faalt. Views met een bekende naam maar een bruikbare body worden
    niet aangeraakt.
    """
    verouderd = stale_views_present(conn)
    for view in STALE_VIEWS:
        if view in verouderd:
            conn.execute(f"DROP VIEW IF EXISTS [{view}]")
            logger.info(
                "Stale view '%s' (-> %s) verwijderd", view, STALE_VIEW_REFERENCE
            )
        else:
            logger.info("View '%s' is niet de verouderde definitie — behouden", view)


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
        # Autocommit: de transactiegrens is expliciet (DEF-664).
        conn = sqlite3.connect(str(db_path), isolation_level=None)
    except sqlite3.Error as exc:
        logger.error("Kan niet verbinden met database: %s", exc)
        return False

    try:
        # PRAGMA's binnen de try: een fout hier sluit de verbinding ook.
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")

        # Stap 0: precondities en geverifieerde backup, vóór enige schrijfactie
        require_migration_preconditions(
            conn,
            previous_version=MIGRATION_VERSION - 1,
            tables=("rag_collections",),
        )
        backup_path = create_migration_backup(
            db_path, "pre_v7_migration", datetime.now()
        )
        logger.info("Backup geverifieerd: %s", backup_path)
        # Idempotent op een al hogere database: doelcontract = hoogste versie.
        doelversie = max(MIGRATION_VERSION, schema_version(conn) or 0)
        # Bronbehoud: alles wat er nu is moet er straks nog zijn, behalve de
        # aantoonbaar verouderde views.
        bronobjecten = schema_objects(conn)
        bewust_weg = {("view", naam) for naam in stale_views_present(conn)}

        # Stap 1 t/m 4 in één transactie: verificatie vóór commit
        with migration_transaction(conn):
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

            logger.info("")
            logger.info("STAP 4: Verificatie")
            logger.info("-" * 40)
            if not verify_migration(conn):
                raise SchemaContractError("migration_verification_failed")
            # DEF-664: bronbehoud (afzonderlijk) + volledig doelcontract
            # (= startupcontract) + integrity/FK, nog binnen de transactie.
            problemen = lost_objects(bronobjecten, schema_objects(conn), bewust_weg)
            problemen += verify_target_contract(conn, doelversie)
            if problemen:
                for probleem in problemen:
                    logger.error("Doelcontract: %s", probleem)
                raise SchemaContractError("migration_target_contract_failed", problemen)
        logger.info("Alle wijzigingen gecommit")

        logger.info("")
        logger.info("=" * 60)
        logger.info("V7 Migration COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        return True

    except (SchemaContractError, sqlite3.Error, OSError) as exc:
        # De transactiehelper heeft al teruggerold; niets is gecommit.
        logger.error("V7 Migration FAILED: %s", exc)
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
