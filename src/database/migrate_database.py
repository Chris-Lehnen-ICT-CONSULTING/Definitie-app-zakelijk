"""
Database migratie script voor legacy velden.

Dit script voegt de ontbrekende legacy velden toe aan de database
voor backward compatibility met de UI.
"""

import json
import logging
import re
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from database.definitie_duplicates import KANDIDATEN_INDEX, KANDIDATEN_INDEX_DDL

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
    voorkeursterm TEXT,
    -- DEF-672: stond wél in schema.sql maar niet hier, en werd door de rebuild
    -- hieronder dus stil weggegooid — kolom én inhoud. Toegevoegd via DEF-151
    -- als ALTER TABLE, waardoor deze definitie er nooit op is bijgewerkt.
    generation_prompt_data TEXT
);
"""

# De kolommen die de rebuild van `definities` overzet. Afgeleid uit
# DEFINITIES_TABLE_SQL zodat de INSERT- en SELECT-lijst niet apart kunnen
# achterlopen op de tabeldefinitie — precies wat bij generation_prompt_data
# gebeurde (DEF-672).
DEFINITIES_KOLOMMEN: tuple[str, ...] = tuple(
    re.findall(r"^\s{4}(\w+)\s", DEFINITIES_TABLE_SQL, flags=re.MULTILINE)
)


DEFINITIE_VOORBEELDEN_KOLOMMEN: tuple[str, ...] = tuple(
    re.findall(r"^\s{4}(\w+)\s", DEFINITIE_VOORBEELDEN_TABLE_SQL, flags=re.MULTILINE)
)


def _create_definitie_voorbeelden_table(
    conn: sqlite3.Connection, table_name: str = "definitie_voorbeelden"
) -> None:
    """(Re)create the definitie_voorbeelden table with the canonical schema.

    DEF-672: `execute` en niet `executescript`. Die laatste commit een lopende
    transactie impliciet, waardoor de voorafgaande RENAME vastgezet werd en een
    fout daarna niet meer terug te draaien was.
    """
    conn.execute(DEFINITIE_VOORBEELDEN_TABLE_SQL.format(table_name=table_name))


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
    conn.executescript("""
        CREATE TRIGGER IF NOT EXISTS update_voorbeelden_timestamp
            AFTER UPDATE ON definitie_voorbeelden
            FOR EACH ROW
            WHEN NEW.bijgewerkt_op = OLD.bijgewerkt_op
        BEGIN
            UPDATE definitie_voorbeelden
            SET bijgewerkt_op = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END;
        """)


def _create_definities_table(
    conn: sqlite3.Connection, table_name: str = "definities"
) -> None:
    """(Re)create the definities table with the canonical schema."""

    # DEF-672: `execute`, niet `executescript` — zie
    # `_create_definitie_voorbeelden_table` voor de reden.
    conn.execute(DEFINITIES_TABLE_SQL.format(table_name=table_name))


def _bewaar_afhankelijke_objecten(conn: sqlite3.Connection, tabel: str) -> list[str]:
    """Leg de DDL van indexen en triggers op deze tabel vast (DEF-672).

    Moet vóór de `ALTER TABLE … RENAME` gebeuren: daarna dragen ze de
    tijdelijke tabelnaam. Zij verhuizen namelijk mee én houden hun naam,
    waardoor een `CREATE … IF NOT EXISTS` erna een no-op is en `DROP TABLE`
    ze alsnog allemaal meeneemt.
    """
    return [
        rij[0]
        for rij in conn.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE tbl_name = ? AND type IN ('index', 'trigger') AND sql IS NOT NULL",
            (tabel,),
        )
    ]


def _herstel_afhankelijke_objecten(conn: sqlite3.Connection, ddls: list[str]) -> None:
    """Zet bewaarde indexen en triggers terug op de herbouwde tabel.

    Bewust zonder foutafhandeling (DEF-672): een index of trigger die niet
    terugkomt is een halve migratie. De fout loopt door naar de rollbackgrens
    in `_rebuild_tabel_atomair`, zodat de oorspronkelijke tabel intact blijft
    in plaats van kaal achter te blijven met een warning in het log.
    """
    for ddl in ddls:
        conn.execute(ddl)


def _schemaobjecten(conn: sqlite3.Connection) -> set[tuple[str, str]]:
    """Alle door ons beheerde schemaobjecten, als (type, naam)."""
    return {
        (rij[0], rij[1])
        for rij in conn.execute(
            "SELECT type, name FROM sqlite_master "
            "WHERE type IN ('table', 'index', 'trigger', 'view') "
            "AND name NOT LIKE 'sqlite_%'"
        )
    }


def _verifieer_migratie(
    conn: sqlite3.Connection, verwacht: set[tuple[str, str]]
) -> list[str]:
    """Controleer of de migratie werkelijk is afgerond (DEF-672).

    Levert een lijst problemen; leeg betekent geslaagd. `migrate_database()`
    mag alleen True melden als deze lijst leeg is — succes moet gemeten zijn,
    niet aangenomen.
    """
    problemen: list[str] = []

    aanwezig = _schemaobjecten(conn)
    verdwenen = sorted(f"{soort} {naam}" for soort, naam in verwacht - aanwezig)
    if verdwenen:
        problemen.append(f"schemaobjecten verdwenen: {verdwenen}")

    resten = sorted(
        naam
        for soort, naam in aanwezig
        if soort == "table" and naam.endswith(("_old", "_old2"))
    )
    if resten:
        problemen.append(f"tijdelijke rebuild-tabellen blijven staan: {resten}")

    if not any(naam == KANDIDATEN_INDEX for _, naam in aanwezig):
        problemen.append(f"index {KANDIDATEN_INDEX} ontbreekt")

    try:
        schendingen = conn.execute("PRAGMA foreign_key_check").fetchall()
    except sqlite3.Error as exc:
        problemen.append(f"foreign_key_check kon niet draaien: {exc}")
    else:
        if schendingen:
            problemen.append(
                f"foreign_key_check meldt {len(schendingen)} schending(en)"
            )

    try:
        integriteit = conn.execute("PRAGMA integrity_check").fetchone()[0]
    except sqlite3.Error as exc:
        problemen.append(f"integrity_check kon niet draaien: {exc}")
    else:
        if str(integriteit).lower() != "ok":
            problemen.append(f"integrity_check: {integriteit}")

    return problemen


@contextmanager
def _migratiemodus(conn: sqlite3.Connection) -> Iterator[None]:
    """Zet de PRAGMA's voor een tabelrebuild en herstel ze altijd (DEF-672).

    `foreign_keys` moet uit vóór de transactie: binnen een transactie is die
    PRAGMA een no-op. `legacy_alter_table` zorgt dat `ALTER TABLE … RENAME`
    verwijzingen in views en FK-clausules niet herschrijft — de door SQLite
    gedocumenteerde route voor het rename-recreate-drop-patroon.

    Beide worden hersteld op hun oorspronkelijke waarde, niet op een aanname.
    """
    oude_fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    oude_legacy = conn.execute("PRAGMA legacy_alter_table").fetchone()[0]
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("PRAGMA legacy_alter_table=ON")
    try:
        yield
    finally:
        conn.execute(f"PRAGMA legacy_alter_table={int(oude_legacy)}")
        conn.execute(f"PRAGMA foreign_keys={int(oude_fk)}")


def _rebuild_tabel_atomair(
    conn: sqlite3.Connection,
    *,
    tabel: str,
    tijdelijke_naam: str,
    maak_tabel: Callable[[sqlite3.Connection], None],
    kolommen: tuple[str, ...],
    zorg_voor_indexen: Callable[[sqlite3.Connection], None],
) -> None:
    """Bouw één tabel opnieuw op in één transactie (DEF-672).

    Alles of niets. Faalt een stap — het aanmaken van de nieuwe tabel, de
    datakopie, de `DROP`, of het herstel van indexen en triggers — dan gaat de
    hele rebuild terug en staat de oorspronkelijke tabel er onaangeroerd. De
    uitzondering loopt door naar de aanroeper, die de migratie als mislukt
    rapporteert.

    Vóór deze wijziging vingen die stappen hun eigen fouten af met een warning
    en liep de migratie door. Met een fout in het aanmaken van de nieuwe tabel
    bleef alleen `<tabel>_old` over en meldde `migrate_database()` tóch succes:
    destructief én fail-open.
    """
    bewaard = _bewaar_afhankelijke_objecten(conn, tabel)
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(f"ALTER TABLE {tabel} RENAME TO {tijdelijke_naam}")
        maak_tabel(conn)

        # Kolommen die de oude tabel nog niet heeft (bv. na een ALTER-migratie
        # die nooit draaide) worden overgeslagen in plaats van de hele rebuild
        # te laten falen.
        aanwezig = {
            rij[1] for rij in conn.execute(f"PRAGMA table_info({tijdelijke_naam})")
        }
        over_te_zetten = [kolom for kolom in kolommen if kolom in aanwezig]
        kolomlijst = ", ".join(over_te_zetten)
        conn.execute(
            f"INSERT INTO {tabel} ({kolomlijst}) "
            f"SELECT {kolomlijst} FROM {tijdelijke_naam}"
        )

        conn.execute(f"DROP TABLE {tijdelijke_naam}")
        # Pas ná de DROP: de oude indexen en triggers verhuisden bij de RENAME
        # mee en hielden hun naam, dus een CREATE … IF NOT EXISTS ervóór is een
        # no-op en de nieuwe tabel bleef kaal achter.
        _herstel_afhankelijke_objecten(conn, bewaard)
        zorg_voor_indexen(conn)
    except Exception:
        conn.rollback()
        raise
    conn.commit()


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
    # DEF-672: bedient de CON-01-kandidatenquery, die op
    # `begrip = ? COLLATE NOCASE AND status != 'archived'` zoekt. Zonder deze
    # partiele index valt die query terug op een volledige tabelscan. Index-only
    # en idempotent; bestaande databases krijgen hem via deze migratie.
    conn.execute(KANDIDATEN_INDEX_DDL)


from utils.logging_bootstrap import ensure_logging_configured

# DEF-571: eigen entrypoint — main.py draait hier niet.
ensure_logging_configured()

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
            logger.info("i  Geen normalisaties nodig voor wettelijke_basis")
        return changed
    except Exception as e:
        logger.warning(f"Normalisatie wettelijk mislukt: {e}")
        return 0


def migrate_database(db_path: str = "data/definities.db") -> bool:
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
            # DEF-672: autocommit, zodat `_rebuild_tabel_atomair` zijn eigen
            # BEGIN/COMMIT/ROLLBACK kan voeren. Met de impliciete transactie van
            # de sqlite3-module zou een expliciete BEGIN botsen.
            conn.isolation_level = None

            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")

            # Momentopname vóór de migratie: elk schemaobject dat er nu is moet
            # er ná de migratie nog zijn (DEF-672).
            verwachte_objecten = _schemaobjecten(conn)

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
                            conn.execute("""
                                UPDATE definities
                                SET datum_voorstel = created_at
                                WHERE datum_voorstel IS NULL
                            """)
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
                        conn.execute("""
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
                            """)
                        # Backfill vanuit boolean vlag → begrip als voorkeursterm
                        conn.execute("""
                            UPDATE definities
                            SET voorkeursterm = begrip
                            WHERE voorkeursterm IS NULL AND voorkeursterm_is_begrip = TRUE
                            """)
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

            # DEF-672: de rebuilds hieronder zijn atomair. Elke stap die faalt
            # rolt de héle rebuild terug; de uitzondering loopt door naar de
            # buitenste handler, die de migratie als mislukt rapporteert. Geen
            # warning-plus-doorgaan meer voor verplichte migratiestappen.
            def _col_exists(table: str, col: str) -> bool:
                c = conn.execute(f"PRAGMA table_info({table})")
                return any(r[1] == col for r in c.fetchall())

            with _migratiemodus(conn):
                # 1) definitie_voorbeelden: drop is_voorkeursterm if present
                if _col_exists("definitie_voorbeelden", "is_voorkeursterm"):
                    logger.info(
                        "🔧 Rebuild 'definitie_voorbeelden' zonder kolom 'is_voorkeursterm'"
                    )
                    _rebuild_tabel_atomair(
                        conn,
                        tabel="definitie_voorbeelden",
                        tijdelijke_naam="definitie_voorbeelden_old",
                        maak_tabel=_create_definitie_voorbeelden_table,
                        kolommen=DEFINITIE_VOORBEELDEN_KOLOMMEN,
                        zorg_voor_indexen=_ensure_definitie_voorbeelden_indexes,
                    )
                    logger.info("✅ Kolom 'is_voorkeursterm' verwijderd")

                # 2) definities: drop voorkeursterm_is_begrip if present
                if _col_exists("definities", "voorkeursterm_is_begrip"):
                    logger.info(
                        "🔧 Rebuild 'definities' zonder kolom 'voorkeursterm_is_begrip'"
                    )
                    _rebuild_tabel_atomair(
                        conn,
                        tabel="definities",
                        tijdelijke_naam="definities_old",
                        maak_tabel=_create_definities_table,
                        kolommen=DEFINITIES_KOLOMMEN,
                        zorg_voor_indexen=_ensure_definities_indexes,
                    )
                    logger.info("✅ Kolom 'voorkeursterm_is_begrip' verwijderd")

                # 3) Corrigeer een FK die nog naar 'definities_old' wijst. Dat
                #    kan alleen in een database die vóór DEF-672 is gemigreerd;
                #    sinds `legacy_alter_table` worden verwijzingen niet meer
                #    herschreven.
                rij = conn.execute(
                    "SELECT sql FROM sqlite_master "
                    "WHERE type='table' AND name='definitie_voorbeelden'"
                ).fetchone()
                if "definities_old" in ((rij[0] if rij else "") or ""):
                    logger.info(
                        "🔧 Corrigeer FK: rebuild 'definitie_voorbeelden' met FK naar 'definities'"
                    )
                    _rebuild_tabel_atomair(
                        conn,
                        tabel="definitie_voorbeelden",
                        tijdelijke_naam="definitie_voorbeelden_old2",
                        maak_tabel=_create_definitie_voorbeelden_table,
                        kolommen=DEFINITIE_VOORBEELDEN_KOLOMMEN,
                        zorg_voor_indexen=_ensure_definitie_voorbeelden_indexes,
                    )
                    logger.info(
                        "✅ FK naar 'definities' hersteld op 'definitie_voorbeelden'"
                    )

            # Normaliseer wettelijke_basis voor betrouwbare duplicate-check op DB-laag
            _normalize_wettelijke_basis(conn)

            # DEF-672: succes is een uitkomst, geen aanname. Zonder deze
            # controle meldde de migratie True terwijl `definities` niet meer
            # bestond en alleen `definities_old` restte.
            problemen = _verifieer_migratie(conn, verwachte_objecten)
            if problemen:
                for probleem in problemen:
                    logger.error(f"❌ Migratieverificatie: {probleem}")
                return False

            logger.info("✅ Database migratie + normalisatie succesvol!")
            return True

    except Exception as e:
        logger.error(f"❌ Database migratie mislukt: {e}")
        return False


def verify_migration(db_path: str = "data/definities.db") -> bool:
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
                f"i  voorkeursterm_is_begrip: {'AANWEZIG (deprecated)' if has_voorkeursterm_is_begrip else 'ONTBREEKT (ok)'}"
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
            logger.info("Database is volledig compatibel!")
        else:
            logger.warning("Database migratie incompleet")
    else:
        logger.error("Database migratie mislukt!")
        sys.exit(1)
