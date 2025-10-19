"""
Database migratie script voor legacy velden.

Dit script voegt de ontbrekende legacy velden toe aan de database
voor backward compatibility met de UI.
"""

import json
import logging
import sqlite3
from pathlib import Path

DEFINITIE_VOORBEELDEN_TABLE_SQL = """
CREATE TABLE {table_name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL REFERENCES definities(id) ON DELETE CASCADE,
    voorbeeld_type VARCHAR(50) NOT NULL CHECK (
        voorbeeld_type IN ('sentence', 'practical', 'counter', 'synonyms', 'antonyms', 'explanation')
    ),
    voorbeeld_tekst TEXT NOT NULL,
    voorbeeld_volgorde INTEGER DEFAULT 1,
    gegenereerd_door VARCHAR(50) DEFAULT 'system',
    generation_model VARCHAR(50),
    generation_parameters TEXT,
    actief BOOLEAN NOT NULL DEFAULT TRUE,
    beoordeeld BOOLEAN NOT NULL DEFAULT FALSE,
    beoordeeling VARCHAR(50),
    beoordeeling_notities TEXT,
    beoordeeld_door VARCHAR(255),
    beoordeeld_op TIMESTAMP,
    aangemaakt_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    bijgewerkt_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(definitie_id, voorbeeld_type, voorbeeld_volgorde)
);
"""


DEFINITIES_TABLE_SQL = """
CREATE TABLE {table_name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    begrip VARCHAR(255) NOT NULL,
    definitie TEXT NOT NULL,
    categorie VARCHAR(50) NOT NULL CHECK (
        categorie IN ('type','proces','resultaat','exemplaar','ENT','ACT','REL','ATT','AUT','STA','OTH')
    ),
    organisatorische_context TEXT NOT NULL DEFAULT '[]',
    juridische_context TEXT NOT NULL DEFAULT '[]',
    wettelijke_basis TEXT NOT NULL DEFAULT '[]',
    ufo_categorie TEXT CHECK (
        ufo_categorie IN (
            'Kind','Event','Role','Phase','Relator','Mode','Quantity','Quality','Subkind',
            'Category','Mixin','RoleMixin','PhaseMixin','Abstract','Relatie','Event Composition'
        )
    ),
    toelichting_proces TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (
        status IN ('imported','draft','review','established','archived')
    ),
    version_number INTEGER NOT NULL DEFAULT 1,
    previous_version_id INTEGER REFERENCES definities(id),
    validation_score DECIMAL(3,2),
    validation_date TIMESTAMP,
    validation_issues TEXT,
    source_type VARCHAR(50) DEFAULT 'generated' CHECK (
        source_type IN ('generated','imported','manual')
    ),
    source_reference VARCHAR(500),
    imported_from VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    approval_notes TEXT,
    last_exported_at TIMESTAMP,
    export_destinations TEXT,
    datum_voorstel DATE,
    ketenpartners TEXT,
    voorkeursterm TEXT
);
"""


def _create_definitie_voorbeelden_table(
    conn: sqlite3.Connection, table_name: str = "definitie_voorbeelden"
) -> None:
    """(Re)create the definitie_voorbeelden table with the canonical schema."""

    conn.executescript(DEFINITIE_VOORBEELDEN_TABLE_SQL.format(table_name=table_name))


def _ensure_definitie_voorbeelden_indexes(conn: sqlite3.Connection) -> None:
    """Ensure indexes and triggers exist for definitie_voorbeelden."""

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_voorbeelden_definitie_id ON definitie_voorbeelden(definitie_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_voorbeelden_type ON definitie_voorbeelden(voorbeeld_type)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_voorbeelden_actief ON definitie_voorbeelden(actief)"
    )
    conn.executescript(
        """
        CREATE TRIGGER IF NOT EXISTS update_voorbeelden_timestamp
            AFTER UPDATE ON definitie_voorbeelden
            FOR EACH ROW
            WHEN NEW.bijgewerkt_op = OLD.bijgewerkt_op
        BEGIN
            UPDATE definitie_voorbeelden
            SET bijgewerkt_op = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END;
        """
    )


def _create_definities_table(
    conn: sqlite3.Connection, table_name: str = "definities"
) -> None:
    """(Re)create the definities table with the canonical schema."""

    conn.executescript(DEFINITIES_TABLE_SQL.format(table_name=table_name))


def _ensure_definities_indexes(conn: sqlite3.Connection) -> None:
    """Ensure indexes exist for the definities table."""

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_definities_begrip ON definities(begrip)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_definities_context ON definities(organisatorische_context, juridische_context)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_definities_status ON definities(status)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_definities_categorie ON definities(categorie)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_definities_created_at ON definities(created_at)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_definities_datum_voorstel ON definities(datum_voorstel)"
    )


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
        msg = f"Tabel '{table}' niet toegestaan"
        raise ValueError(msg)

    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(definities)")  # Fixed table name for security
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def get_missing_columns(conn: sqlite3.Connection) -> list[tuple[str, str]]:
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

    # Check wettelijke_basis (JSON stored as TEXT)
    if not check_column_exists(conn, "definities", "wettelijke_basis"):
        missing.append(("wettelijke_basis", "TEXT"))

    # Check UFO-categorie (OntoUML/UFO metamodel)
    if not check_column_exists(conn, "definities", "ufo_categorie"):
        missing.append(("ufo_categorie", "TEXT"))

    return missing


def _normalize_list_json(raw: str | None) -> str:
    """Normalize a TEXT column that stores a JSON list: unique + sorted.

    - Accepts None, empty, JSON strings, or plain strings.
    - Returns a JSON array string with unique, sorted, stripped elements.
    """
    if not raw:
        return json.dumps([], ensure_ascii=False)
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            items = {str(x).strip() for x in data}
            return json.dumps(sorted(items), ensure_ascii=False)
        # Non-list JSON → wrap as single element
        return json.dumps([str(data).strip()], ensure_ascii=False)
    except Exception:
        # Not JSON → wrap raw as single element
        return json.dumps([str(raw).strip()], ensure_ascii=False)


def _normalize_wettelijke_basis(conn: sqlite3.Connection) -> int:
    """Normalize all bestaande wettelijke_basis waarden (TEXT JSON) in definities.

    Returns aantal gewijzigde rijen.
    """
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, wettelijke_basis FROM definities")
        rows = cur.fetchall()
        changed = 0
        for row in rows:
            _id, raw = row[0], row[1]
            new_val = _normalize_list_json(raw)
            # Update only when changed to reduce write load
            if new_val != (raw or json.dumps([], ensure_ascii=False)):
                cur.execute(
                    "UPDATE definities SET wettelijke_basis = ? WHERE id = ?",
                    (new_val, _id),
                )
                changed += 1
        conn.commit()
        if changed:
            logger.info(f"✅ Genormaliseerd: {changed} rijen voor wettelijke_basis")
        else:
            logger.info("ℹ️  Geen normalisaties nodig voor wettelijke_basis")
        return changed
    except Exception as e:
        logger.warning(f"Normalisatie wettelijk mislukt: {e}")
        return 0


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

            # Altijd normalisatie uitvoeren; ook als er geen kolommen ontbreken
            if not missing_columns:
                logger.info("Database schema OK; voer normalisatie uit…")
            else:
                logger.info(f"Ontbrekende kolommen gevonden: {missing_columns}")

            # Voeg ontbrekende kolommen toe - Use whitelist for security
            allowed_columns = {
                "datum_voorstel": "TIMESTAMP",
                "ketenpartners": "TEXT",
                "wettelijke_basis": "TEXT",
                "ufo_categorie": "TEXT",
            }

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

            # Zorg dat kolom 'is_voorkeursterm' bestaat op tabel 'definitie_voorbeelden'
            try:
                cur = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='definitie_voorbeelden'"
                )
                if cur.fetchone():
                    cur = conn.execute("PRAGMA table_info(definitie_voorbeelden)")
                    voorbeelden_columns = {row[1] for row in cur.fetchall()}
                    if "is_voorkeursterm" not in voorbeelden_columns:
                        conn.execute(
                            "ALTER TABLE definitie_voorbeelden ADD COLUMN is_voorkeursterm BOOLEAN NOT NULL DEFAULT FALSE"
                        )
                        logger.info(
                            "✅ Kolom 'is_voorkeursterm' toegevoegd aan 'definitie_voorbeelden'"
                        )
            except sqlite3.Error as e:
                logger.warning(
                    f"Kon kolom 'is_voorkeursterm' niet toevoegen aan 'definitie_voorbeelden': {e}"
                )

            # Zorg dat kolom 'voorkeursterm' bestaat op tabel 'definities'
            try:
                cur = conn.execute("PRAGMA table_info(definities)")
                definities_columns = {row[1] for row in cur.fetchall()}
                if "voorkeursterm" not in definities_columns:
                    conn.execute("ALTER TABLE definities ADD COLUMN voorkeursterm TEXT")
                    logger.info("✅ Kolom 'voorkeursterm' toegevoegd aan 'definities'")
                    # Backfill vanuit gemarkeerde synoniemen → definities.voorkeursterm = voorbeeld_tekst
                    try:
                        conn.execute(
                            """
                            UPDATE definities
                            SET voorkeursterm = (
                                SELECT v.voorbeeld_tekst FROM definitie_voorbeelden v
                                WHERE v.definitie_id = definities.id
                                  AND v.voorbeeld_type = 'synonyms'
                                  AND v.actief = TRUE
                                  AND v.is_voorkeursterm = TRUE
                                LIMIT 1
                            )
                            WHERE voorkeursterm IS NULL
                            """
                        )
                        # Backfill vanuit boolean vlag → begrip als voorkeursterm
                        conn.execute(
                            """
                            UPDATE definities
                            SET voorkeursterm = begrip
                            WHERE voorkeursterm IS NULL AND voorkeursterm_is_begrip = TRUE
                            """
                        )
                        logger.info("✅ Backfill voor 'voorkeursterm' uitgevoerd")
                    except sqlite3.Error as e:
                        logger.warning(f"Backfill voorkeursterm mislukt: {e}")
                if "voorkeursterm_is_begrip" not in definities_columns:
                    conn.execute(
                        "ALTER TABLE definities ADD COLUMN voorkeursterm_is_begrip BOOLEAN NOT NULL DEFAULT FALSE"
                    )
                    logger.info(
                        "✅ Kolom 'voorkeursterm_is_begrip' toegevoegd aan 'definities'"
                    )
            except sqlite3.Error as e:
                logger.warning(
                    f"Kon kolom 'voorkeursterm_is_begrip' niet toevoegen aan 'definities': {e}"
                )

            # Voeg indexes toe
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_definities_datum_voorstel ON definities(datum_voorstel)"
                )
                logger.info("✅ Index toegevoegd voor datum_voorstel")
                # Case-insensitive synoniem lookup index (SQLite supports expression indexes)
                try:
                    conn.execute(
                        "CREATE INDEX IF NOT EXISTS idx_synonyms_text_ci ON definitie_voorbeelden(voorbeeld_type, actief, voorbeeld_tekst COLLATE NOCASE)"
                    )
                    logger.info("✅ Index toegevoegd voor synoniemen (CI)")
                except sqlite3.Error as e:
                    logger.warning(f"Synoniemen-index kon niet worden toegevoegd: {e}")
            except sqlite3.Error as e:
                logger.warning(f"Index kon niet worden toegevoegd: {e}")

            # Commit changes so far
            conn.commit()

            # Drop deprecated preference columns by rebuilding tables (SQLite limitation)
            try:
                # Helper to check column existence
                def _col_exists(table: str, col: str) -> bool:
                    c = conn.execute(f"PRAGMA table_info({table})")
                    return any(r[1] == col for r in c.fetchall())

                # 1) definitie_voorbeelden: drop is_voorkeursterm if present
                if _col_exists("definitie_voorbeelden", "is_voorkeursterm"):
                    logger.info(
                        "🔧 Rebuild 'definitie_voorbeelden' zonder kolom 'is_voorkeursterm'"
                    )
                    conn.execute("PRAGMA foreign_keys=OFF")
                    conn.execute(
                        "ALTER TABLE definitie_voorbeelden RENAME TO definitie_voorbeelden_old"
                    )
                    _create_definitie_voorbeelden_table(conn)
                    conn.execute(
                        """
                        INSERT INTO definitie_voorbeelden (
                            id, definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
                            gegenereerd_door, generation_model, generation_parameters, actief,
                            beoordeeld, beoordeeling, beoordeeling_notities, beoordeeld_door, beoordeeld_op,
                            aangemaakt_op, bijgewerkt_op
                        )
                        SELECT
                            id, definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
                            gegenereerd_door, generation_model, generation_parameters, actief,
                            beoordeeld, beoordeeling, beoordeeling_notities, beoordeeld_door, beoordeeld_op,
                            aangemaakt_op, bijgewerkt_op
                        FROM definitie_voorbeelden_old
                        """
                    )
                    # Indexes en trigger
                    try:
                        _ensure_definitie_voorbeelden_indexes(conn)
                    except sqlite3.Error as e:
                        logger.warning(
                            f"Indexes/triggers hercreatie mislukt voor definitie_voorbeelden: {e}"
                        )
                    conn.execute("DROP TABLE definitie_voorbeelden_old")
                    conn.execute("PRAGMA foreign_keys=ON")
                    logger.info("✅ Kolom 'is_voorkeursterm' verwijderd")

                # 2) definities: drop voorkeursterm_is_begrip if present
                if _col_exists("definities", "voorkeursterm_is_begrip"):
                    logger.info(
                        "🔧 Rebuild 'definities' zonder kolom 'voorkeursterm_is_begrip'"
                    )
                    conn.execute("PRAGMA foreign_keys=OFF")
                    conn.execute("ALTER TABLE definities RENAME TO definities_old")
                    _create_definities_table(conn)
                    conn.execute(
                        """
                        INSERT INTO definities (
                            id, begrip, definitie, categorie, organisatorische_context, juridische_context,
                            wettelijke_basis, ufo_categorie, toelichting_proces, status, version_number, previous_version_id,
                            validation_score, validation_date, validation_issues, source_type, source_reference, imported_from,
                            created_at, updated_at, created_by, updated_by, approved_by, approved_at, approval_notes,
                            last_exported_at, export_destinations, datum_voorstel, ketenpartners, voorkeursterm
                        )
                        SELECT
                            id, begrip, definitie, categorie, organisatorische_context, juridische_context,
                            wettelijke_basis, ufo_categorie, toelichting_proces, status, version_number, previous_version_id,
                            validation_score, validation_date, validation_issues, source_type, source_reference, imported_from,
                            created_at, updated_at, created_by, updated_by, approved_by, approved_at, approval_notes,
                            last_exported_at, export_destinations, datum_voorstel, ketenpartners, voorkeursterm
                        FROM definities_old
                        """
                    )
                    # Recreate indexes
                    try:
                        _ensure_definities_indexes(conn)
                    except sqlite3.Error as e:
                        logger.warning(f"Definities-indexen hercreatie mislukt: {e}")
                    conn.execute("DROP TABLE definities_old")
                    conn.execute("PRAGMA foreign_keys=ON")
                    logger.info("✅ Kolom 'voorkeursterm_is_begrip' verwijderd")
            except Exception as e:
                logger.warning(f"Kolom‑opruiming overgeslagen/mislukt: {e}")

            # Correcteer eventueel FK die nog naar 'definities_old' wijst
            try:
                cur = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name='definitie_voorbeelden'"
                )
                row = cur.fetchone()
                table_sql = row[0] if row else ""
                if "definities_old" in (table_sql or ""):
                    logger.info(
                        "🔧 Corrigeer FK: rebuild 'definitie_voorbeelden' met FK naar 'definities'"
                    )
                    conn.execute("PRAGMA foreign_keys=OFF")
                    conn.execute(
                        "ALTER TABLE definitie_voorbeelden RENAME TO definitie_voorbeelden_old2"
                    )
                    _create_definitie_voorbeelden_table(conn)
                    # Copy data
                    conn.execute(
                        """
                        INSERT INTO definitie_voorbeelden (
                            id, definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
                            gegenereerd_door, generation_model, generation_parameters, actief,
                            beoordeeld, beoordeeling, beoordeeling_notities, beoordeeld_door, beoordeeld_op,
                            aangemaakt_op, bijgewerkt_op
                        )
                        SELECT
                            id, definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
                            gegenereerd_door, generation_model, generation_parameters, actief,
                            beoordeeld, beoordeeling, beoordeeling_notities, beoordeeld_door, beoordeeld_op,
                            aangemaakt_op, bijgewerkt_op
                        FROM definitie_voorbeelden_old2
                        """
                    )
                    # Recreate indexes + trigger
                    try:
                        _ensure_definitie_voorbeelden_indexes(conn)
                    except sqlite3.Error as e:
                        logger.warning(
                            f"Indexes/triggers hercreatie mislukt (FK fix): {e}"
                        )
                    conn.execute("DROP TABLE definitie_voorbeelden_old2")
                    conn.execute("PRAGMA foreign_keys=ON")
                    logger.info(
                        "✅ FK naar 'definities' hersteld op 'definitie_voorbeelden'"
                    )
            except Exception as e:
                logger.warning(f"FK correctie check overslagen/mislukt: {e}")

            # Normaliseer wettelijke_basis voor betrouwbare duplicate‑check op DB‑laag
            _normalize_wettelijke_basis(conn)

            logger.info("✅ Database migratie + normalisatie succesvol!")
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
            has_voorkeursterm_is_begrip = "voorkeursterm_is_begrip" in columns
            has_voorkeursterm_text = "voorkeursterm" in columns

            logger.info(
                f"\n✅ datum_voorstel: {'AANWEZIG' if has_datum_voorstel else 'ONTBREEKT'}"
            )
            logger.info(
                f"✅ ketenpartners: {'AANWEZIG' if has_ketenpartners else 'ONTBREEKT'}"
            )
            logger.info(
                f"ℹ️  voorkeursterm_is_begrip: {'AANWEZIG (deprecated)' if has_voorkeursterm_is_begrip else 'ONTBREEKT (ok)'}"
            )
            logger.info(
                f"✅ voorkeursterm (TEXT): {'AANWEZIG' if has_voorkeursterm_text else 'ONTBREEKT'}"
            )

            # Test query
            cursor.execute(
                "SELECT COUNT(*) FROM definities WHERE datum_voorstel IS NOT NULL"
            )
            count = cursor.fetchone()[0]
            logger.info(f"\nAantal records met datum_voorstel: {count}")

            return has_datum_voorstel and has_ketenpartners and has_voorkeursterm_text

    except Exception as e:
        logger.error(f"Verificatie mislukt: {e}")
        return False


if __name__ == "__main__":
    import sys

    # Bepaal database pad
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/definities.db"

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
