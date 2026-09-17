"""V8 Database Migration: `definities.categorie` optioneel (DEF-751 B2).

Een definitie zonder categorielabel wordt als NULL opgeslagen — nooit meer
een verzonnen "proces". De waardenlijst van de CHECK blijft ongewijzigd
(NULL passeert een CHECK in SQLite); alleen `NOT NULL` vervalt. SQLite kan
een NOT NULL niet in-place versoepelen, dus de tabel wordt herbouwd met de
bestaande, geverifieerde rebuildhelper (`migrate_database._rebuild_tabel_
atomair`): ids, rijen, alle elf categoriewaarden, extra kolommen, unieke
sleutels, CHECKs, foreign keys, indexen, triggers, views en de
autoincrement-teller blijven behouden; de versoepeling van precies deze ene
kolom wordt expliciet opgegeven (`versoepeld`), elk ander verlies van
semantiek blijft een harde fout.

schema_version = 4.

Idempotent: herhaald uitvoeren is veilig (kolom al optioneel → geen rebuild).
Fail-closed en transactioneel (DEF-664): backup vóór de eerste schrijfactie,
verificatie (bronbehoud, volledig doelcontract, integrity/foreign_key_check)
vóór de commit; bij elke fout blijft de database exact zoals ervoor.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from database.migrate_database import (
    DEFINITIES_KOLOMMEN,
    _create_definities_table,
    _ensure_definities_indexes,
    _migratiemodus,
    _rebuild_tabel_atomair,
)
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
MIGRATION_VERSION = 4
MIGRATION_DESCRIPTION = "definities.categorie optioneel: NULL = geen label (DEF-751)"
TABEL = "definities"
KOLOM = "categorie"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def categorie_is_verplicht(conn: sqlite3.Connection) -> bool:
    """True zolang `definities.categorie` nog NOT NULL is (v3-vorm).

    Een ontbrekende tabel of kolom is een harde fout, geen "al gedaan".
    """
    rows = conn.execute(f"PRAGMA table_info([{TABEL}])").fetchall()
    if not rows:
        raise sqlite3.OperationalError(f"no such table: {TABEL}")
    for _cid, naam, _type, notnull, _dflt, _pk in rows:
        if naam == KOLOM:
            return bool(notnull)
    raise sqlite3.OperationalError(f"no such column: {TABEL}.{KOLOM}")


def _rijtelling(conn: sqlite3.Connection) -> tuple[int, list[tuple]]:
    """(aantal rijen, [(id, categorie), …]) — het bronbehoud dat v8 zelf toetst."""
    aantal = conn.execute(f"SELECT COUNT(*) FROM {TABEL}").fetchone()[0]
    rijen = conn.execute(f"SELECT id, {KOLOM} FROM {TABEL} ORDER BY id").fetchall()
    return int(aantal), rijen


# ---------------------------------------------------------------------------
# Stap 1: Schema versioning
# ---------------------------------------------------------------------------
def apply_schema_version(conn: sqlite3.Connection) -> None:
    """Insert schema version 4 (idempotent)."""
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
# Stap 2: categorie optioneel maken (tabelrebuild)
# ---------------------------------------------------------------------------
def maak_categorie_optioneel(conn: sqlite3.Connection) -> bool:
    """Herbouw `definities` zonder `NOT NULL` op `categorie` (idempotent).

    Geeft True als er herbouwd is. De rebuildhelper draait als SAVEPOINT
    binnen de buitenste transactie en verifieert zelf kolomsemantiek,
    constraints, indexen/triggers en de autoincrement-teller; de
    versoepeling van `categorie` is de enige toegestane afwijking. De
    tabelmaker kiest de DDL op de schemaversie: de versiemarker 4 staat er
    (stap 1) vóór deze rebuild, dus de v4-DDL.
    """
    if not categorie_is_verplicht(conn):
        logger.info("Kolom '%s.%s' is al optioneel — skip", TABEL, KOLOM)
        return False
    if (schema_version(conn) or 0) < MIGRATION_VERSION:
        raise SchemaContractError(
            "migration_precondition_failed",
            (f"schema_version {MIGRATION_VERSION} moet vóór de rebuild zijn gezet",),
        )
    logger.info("🔧 Rebuild '%s' met optionele kolom '%s'", TABEL, KOLOM)
    _rebuild_tabel_atomair(
        conn,
        tabel=TABEL,
        tijdelijke_naam=f"{TABEL}_old",
        maak_tabel=_create_definities_table,
        kolommen=DEFINITIES_KOLOMMEN,
        zorg_voor_indexen=_ensure_definities_indexes,
        versoepeld=frozenset({KOLOM}),
    )
    return True


# ---------------------------------------------------------------------------
# Stap 3: Verificatie
# ---------------------------------------------------------------------------
def verify_migration(
    conn: sqlite3.Connection, bron: tuple[int, list[tuple]]
) -> list[str]:
    """Eigen v8-controles: kolom optioneel, versie 4 aanwezig, rijen exact behouden."""
    problemen: list[str] = []
    if categorie_is_verplicht(conn):
        problemen.append(f"{TABEL}.{KOLOM} is nog NOT NULL")
    row = conn.execute(
        "SELECT version FROM schema_version WHERE version = ?",
        (MIGRATION_VERSION,),
    ).fetchone()
    if not row:
        problemen.append(f"schema_version {MIGRATION_VERSION} niet gevonden")
    if _rijtelling(conn) != bron:
        problemen.append(f"rijen of categoriewaarden van {TABEL} zijn gewijzigd")
    return problemen


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------
def run_migration(db_path: Path = DB_PATH) -> bool:
    """Run de V8 migratie.

    Args:
        db_path: Pad naar de SQLite database.

    Returns:
        True als de migratie geslaagd is.
    """
    logger.info("=" * 60)
    logger.info("V8 Migration (DEF-751) — Start")
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
            tables=(TABEL,),
        )
        backup_path = create_migration_backup(
            db_path, "pre_v8_migration", datetime.now()
        )
        logger.info("Backup geverifieerd: %s", backup_path)
        # Idempotent op een al hogere database: doelcontract = hoogste versie.
        doelversie = max(MIGRATION_VERSION, schema_version(conn) or 0)
        # Bronbehoud: alles wat er nu is moet er straks nog zijn; de rijen en
        # categoriewaarden van `definities` exact.
        bronobjecten = schema_objects(conn)
        bron = _rijtelling(conn)

        # De rebuild-PRAGMA's (foreign_keys uit, legacy_alter_table aan) staan
        # bewust búiten de transactie: binnen een transactie is
        # `foreign_keys` een no-op. Ze worden altijd hersteld.
        with _migratiemodus(conn), migration_transaction(conn):
            logger.info("")
            logger.info("STAP 1: Schema versioning")
            logger.info("-" * 40)
            apply_schema_version(conn)

            logger.info("")
            logger.info("STAP 2: categorie optioneel")
            logger.info("-" * 40)
            maak_categorie_optioneel(conn)

            logger.info("")
            logger.info("STAP 3: Verificatie")
            logger.info("-" * 40)
            problemen = verify_migration(conn, bron)
            # DEF-664: bronbehoud (afzonderlijk) + volledig doelcontract
            # (= startupcontract) + integrity/FK, nog binnen de transactie.
            problemen += lost_objects(bronobjecten, schema_objects(conn), set())
            problemen += verify_target_contract(conn, doelversie)
            if problemen:
                for probleem in problemen:
                    logger.error("Doelcontract: %s", probleem)
                raise SchemaContractError("migration_target_contract_failed", problemen)
        logger.info("Alle wijzigingen gecommit")

        logger.info("")
        logger.info("=" * 60)
        logger.info("V8 Migration COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        return True

    except (SchemaContractError, sqlite3.Error, OSError) as exc:
        # De transactiehelper heeft al teruggerold; niets is gecommit.
        logger.error("V8 Migration FAILED: %s", exc)
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
