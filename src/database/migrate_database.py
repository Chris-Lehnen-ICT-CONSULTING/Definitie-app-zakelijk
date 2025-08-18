"""
Database migratie script voor legacy velden.

Dit script voegt de ontbrekende legacy velden toe aan de database
voor backward compatibility met de UI.
"""

import logging
import sqlite3
from pathlib import Path
from typing import List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """
    Check of een kolom bestaat in een tabel.

    Args:
        conn: Database connectie
        table: Tabelnaam
        column: Kolomnaam

    Returns:
        True als kolom bestaat
    """
    # Whitelist table names for security
    allowed_tables = {"definities", "geschiedenis", "metadata"}
    if table not in allowed_tables:
        raise ValueError(f"Tabel '{table}' niet toegestaan")

    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(definities)")  # Fixed table name for security
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def get_missing_columns(conn: sqlite3.Connection) -> List[Tuple[str, str]]:
    """
    Bepaal welke legacy kolommen ontbreken.

    Returns:
        List van (kolomnaam, sql_type) tuples
    """
    missing = []

    # Check datum_voorstel
    if not check_column_exists(conn, "definities", "datum_voorstel"):
        missing.append(("datum_voorstel", "TIMESTAMP"))

    # Check ketenpartners
    if not check_column_exists(conn, "definities", "ketenpartners"):
        missing.append(("ketenpartners", "TEXT"))

    return missing


def migrate_database(db_path: str = "data/definities.db"):
    """
    Voer database migratie uit.

    Args:
        db_path: Pad naar database bestand
    """
    logger.info(f"Starting database migration for: {db_path}")

    # Check of database bestaat
    if not Path(db_path).exists():
        logger.error(f"Database {db_path} bestaat niet!")
        return False

    try:
        with sqlite3.connect(db_path) as conn:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")

            # Check welke kolommen ontbreken
            missing_columns = get_missing_columns(conn)

            if not missing_columns:
                logger.info("Database is al up-to-date, geen migratie nodig")
                return True

            logger.info(f"Ontbrekende kolommen gevonden: {missing_columns}")

            # Voeg ontbrekende kolommen toe - Use whitelist for security
            allowed_columns = {"datum_voorstel": "TIMESTAMP", "ketenpartners": "TEXT"}

            for column_name, column_type in missing_columns:
                # Security check: only allow predefined columns
                if (
                    column_name in allowed_columns
                    and allowed_columns[column_name] == column_type
                ):
                    try:
                        sql = f"ALTER TABLE definities ADD COLUMN {column_name} {column_type}"
                        conn.execute(sql)
                        logger.info(f"✅ Kolom toegevoegd: {column_name}")

                        # Set default waarde voor datum_voorstel
                        if column_name == "datum_voorstel":
                            conn.execute(
                                """
                                UPDATE definities 
                                SET datum_voorstel = created_at 
                                WHERE datum_voorstel IS NULL
                            """
                            )
                            logger.info("✅ Default waardes gezet voor datum_voorstel")

                    except sqlite3.Error as e:
                        logger.error(f"❌ Fout bij toevoegen kolom {column_name}: {e}")
                        return False
                else:
                    logger.warning(
                        f"⚠️ Kolom '{column_name}' niet toegestaan vanwege security"
                    )

            # Voeg indexes toe
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_definities_datum_voorstel ON definities(datum_voorstel)"
                )
                logger.info("✅ Index toegevoegd voor datum_voorstel")
            except sqlite3.Error as e:
                logger.warning(f"Index kon niet worden toegevoegd: {e}")

            # Commit changes
            conn.commit()

            logger.info("✅ Database migratie succesvol!")
            return True

    except Exception as e:
        logger.error(f"❌ Database migratie mislukt: {e}")
        return False


def verify_migration(db_path: str = "data/definities.db"):
    """
    Verifieer dat de migratie succesvol was.

    Args:
        db_path: Pad naar database
    """
    logger.info("Verifying database schema...")

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check kolommen
            cursor.execute("PRAGMA table_info(definities)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            logger.info("\nHuidige kolommen in definities tabel:")
            for col_name, col_type in columns.items():
                logger.info(f"  - {col_name}: {col_type}")

            # Check specifiek voor legacy velden
            has_datum_voorstel = "datum_voorstel" in columns
            has_ketenpartners = "ketenpartners" in columns

            logger.info(
                f"\n✅ datum_voorstel: {'AANWEZIG' if has_datum_voorstel else 'ONTBREEKT'}"
            )
            logger.info(
                f"✅ ketenpartners: {'AANWEZIG' if has_ketenpartners else 'ONTBREEKT'}"
            )

            # Test query
            cursor.execute(
                "SELECT COUNT(*) FROM definities WHERE datum_voorstel IS NOT NULL"
            )
            count = cursor.fetchone()[0]
            logger.info(f"\nAantal records met datum_voorstel: {count}")

            return has_datum_voorstel and has_ketenpartners

    except Exception as e:
        logger.error(f"Verificatie mislukt: {e}")
        return False


if __name__ == "__main__":
    import sys

    # Bepaal database pad
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = "data/definities.db"

    # Voer migratie uit
    success = migrate_database(db_path)

    if success:
        # Verifieer resultaat
        verified = verify_migration(db_path)
        if verified:
            print("\n🎉 Database is volledig compatibel!")
        else:
            print("\n⚠️  Database migratie incompleet")
    else:
        print("\n❌ Database migratie mislukt!")
        sys.exit(1)
