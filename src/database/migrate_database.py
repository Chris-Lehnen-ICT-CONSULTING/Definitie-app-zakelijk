"""
Database migratie script voor legacy velden.

Dit script voegt de ontbrekende legacy velden toe aan de database
voor backward compatibility met de UI.
"""

import json
import logging
import re
import sqlite3
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from database.definitie_duplicates import KANDIDATEN_INDEX, KANDIDATEN_INDEX_DDL
from database.schema_contract import (
    SUPPORTED_VERSIONS,
    SchemaContractError,
    create_migration_backup,
    fold_identifier,
    folded_columns,
    migration_transaction,
    schema_version,
    verify_target_contract,
)

# DEF-664: als modulevariabelen zodat een falend pad functioneel te injecteren
# is; vóór deze reparatie liepen deze stappen door met alleen een warning.
DATUM_VOORSTEL_INDEX_DDL = (
    "CREATE INDEX IF NOT EXISTS idx_definities_datum_voorstel "
    "ON definities(datum_voorstel)"
)
SYNONIEMEN_INDEX_DDL = (
    "CREATE INDEX IF NOT EXISTS idx_synonyms_text_ci ON definitie_voorbeelden("
    "voorbeeld_type, actief, voorbeeld_tekst COLLATE NOCASE)"
)
VOORKEURSTERM_BACKFILL_UIT_SYNONIEMEN_SQL = """
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
VOORKEURSTERM_BACKFILL_UIT_VLAG_SQL = """
    UPDATE definities
    SET voorkeursterm = begrip
    WHERE voorkeursterm IS NULL AND voorkeursterm_is_begrip = TRUE
"""

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
    # DEF-664: `execute`, niet `executescript` — die laatste commit een lopende
    # transactie impliciet en zou de atomaire migratie in tweeën knippen.
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS update_voorbeelden_timestamp
            AFTER UPDATE ON definitie_voorbeelden
            FOR EACH ROW
            WHEN NEW.bijgewerkt_op = OLD.bijgewerkt_op
        BEGIN
            UPDATE definitie_voorbeelden
            SET bijgewerkt_op = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END
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
        naam for soort, naam in aanwezig if soort == "table" and naam.endswith("_old")
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
    oude_fk = int(conn.execute("PRAGMA foreign_keys").fetchone()[0])
    oude_legacy = int(conn.execute("PRAGMA legacy_alter_table").fetchone()[0])
    # DEF-664 (Codex-herreview): ook een gedeeltelijk mislukte setup wordt
    # hersteld, op déze verbinding, en een falende herstelstap laat de andere
    # PRAGMA niet achterwege.
    try:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("PRAGMA legacy_alter_table=ON")
        yield
    finally:
        herstelfout: sqlite3.Error | None = None
        for pragma, waarde in (
            ("legacy_alter_table", oude_legacy),
            ("foreign_keys", oude_fk),
        ):
            try:
                conn.execute(f"PRAGMA {pragma}={waarde}")
            except sqlite3.Error as exc:
                herstelfout = herstelfout or exc
        if herstelfout is not None:
            raise herstelfout


def _rebuild_tabel_atomair(
    conn: sqlite3.Connection,
    *,
    tabel: str,
    tijdelijke_naam: str,
    maak_tabel: Callable[[sqlite3.Connection], None],
    kolommen: tuple[str, ...],
    zorg_voor_indexen: Callable[[sqlite3.Connection], None],
    verwijderd: frozenset[str] = frozenset(),
) -> None:
    """Bouw één tabel opnieuw op in één transactie (DEF-672).

    ``verwijderd`` zijn de kolommen die de rebuild bewust laat vervallen;
    alle andere niet-canonieke kolommen worden behouden (DEF-664).

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
    extra = _extra_kolommen(conn, tabel, kolommen, verwijderd)
    # DEF-664 (Codex-herreview P1): de werkelijke bronconstraints uit de
    # SQLite-metagegevens, vóór de rebuild; na afloop afzonderlijk vergeleken.
    constraints_voor = _tabelconstraints(conn, tabel)
    seq_voor = _autoincrement_teller(conn, tabel)
    # DEF-664: binnen een al open transactie wordt dit een SAVEPOINT, zodat de
    # hele legacy-migratie één transactie kan zijn; standalone blijft het een
    # eigen BEGIN IMMEDIATE/COMMIT/ROLLBACK.
    with migration_transaction(conn, savepoint=f"rebuild_{tabel}"):
        conn.execute(f"ALTER TABLE {tabel} RENAME TO {tijdelijke_naam}")
        maak_tabel(conn)
        # Codex-review 3 (P1): bronkolomeigenschappen óók op canonieke
        # kolommen vergelijken; sterkere NOT NULL/DEFAULT-semantiek van de
        # bron mag niet stil door de zwakkere canonieke DDL worden vervangen.
        _controleer_kolomsemantiek(conn, tabel, tijdelijke_naam, kolommen, verwijderd)
        for kolom, declaratie in extra:
            conn.execute(f"ALTER TABLE {tabel} ADD COLUMN {kolom} {declaratie}")
            logger.info(f"✅ Extra kolom '{tabel}.{kolom}' behouden ({declaratie})")

        # Kolommen die de oude tabel nog niet heeft (bv. na een ALTER-migratie
        # die nooit draaide) worden overgeslagen in plaats van de hele rebuild
        # te laten falen. Namen hoofdletterongevoelig, bronnaam letterlijk.
        aanwezig = folded_columns(conn, tijdelijke_naam)
        canoniek = [kolom for kolom in kolommen if fold_identifier(kolom) in aanwezig]
        doelkolommen = canoniek + [kolom for kolom, _ in extra]
        bronkolommen = [aanwezig[fold_identifier(kolom)] for kolom in canoniek] + [
            kolom for kolom, _ in extra
        ]
        conn.execute(
            f"INSERT INTO {tabel} ({', '.join(_q(k) for k in doelkolommen)}) "
            f"SELECT {', '.join(_q(k) for k in bronkolommen)} FROM {tijdelijke_naam}"
        )

        conn.execute(f"DROP TABLE {tijdelijke_naam}")
        # Pas ná de DROP: de oude indexen en triggers verhuisden bij de RENAME
        # mee en hielden hun naam, dus een CREATE … IF NOT EXISTS ervóór is een
        # no-op en de nieuwe tabel bleef kaal achter.
        _herstel_afhankelijke_objecten(conn, bewaard)
        zorg_voor_indexen(conn)
        # Rootprobe (probe-autoincrement-preservation): de teller ging met de
        # DROP verloren en eerder uitgegeven ids konden opnieuw verschijnen.
        _herstel_autoincrement_teller(conn, tabel, seq_voor)
        _herstel_unique_constraints(conn, tabel, constraints_voor, verwijderd)
        _controleer_constraintbehoud(conn, tabel, constraints_voor, verwijderd)


def _q(naam: str) -> str:
    """Quote een identifier voor DDL/DML; een dubbele quote wordt verdubbeld."""
    return '"' + naam.replace('"', '""') + '"'


UniqueSleutel = tuple[tuple[str, str], ...]
"""((kolom, collatie), ...) van een UNIQUE-constraint of unique index."""


def _tabelconstraints(
    conn: sqlite3.Connection, tabel: str
) -> tuple[set[UniqueSleutel], frozenset, frozenset[str]]:
    """(unieke sleutels, foreign keys, CHECK-expressies) uit de metagegevens.

    Unieke sleutels: UNIQUE-constraints (autoindexen) én unique indexen, als
    ((kolom, collatie), ...). Bron: ``schema_contract.read_contract`` —
    dezelfde SQLite-PRAGMA's als het startupcontract, geen substringgevallen.
    """
    from database.schema_contract import read_contract

    contract = read_contract(conn)
    uniek: set[UniqueSleutel] = set(contract.unique_constraints.get(tabel, ()))
    for eigenaar, is_uniek, partieel, sleutel, _sql in contract.indexes.values():
        # Rootprobe (probe-partial-unique-equivalence): alleen een volledige,
        # niet-partiële unieke index op echte kolommen dwingt dezelfde
        # uniciteit af als een UNIQUE-constraint. Partiële en expressie-
        # indexen tellen hier niet mee; die blijven via hun eigen volledige
        # DDL behouden (`_bewaar_afhankelijke_objecten`) en worden nooit
        # verstrakt tot een volledige constraint.
        if (
            eigenaar == tabel
            and is_uniek
            and not partieel
            and all(kolom is not None for kolom, _desc, _coll in sleutel)
        ):
            # `or ""` alleen voor de typering: de guard hierboven sluit None uit.
            uniek.add(tuple((kolom or "", coll) for kolom, _desc, coll in sleutel))
    return (
        uniek,
        contract.foreign_keys.get(tabel, frozenset()),
        contract.checks.get(tabel, frozenset()),
    )


def _raakt_verwijderde_kolom(
    kolommen: Iterable[str], verwijderd: frozenset[str]
) -> bool:
    return any(kolom in verwijderd for kolom in kolommen)


def _verwijst_naar(expressie: str, kolom: str) -> bool:
    """True als ``expressie`` (genormaliseerd) de kolom als identifier noemt.

    Codex-review 3 (P1): ``'voorkeursterm_is_begrip'`` als string-literal is
    géén verwijzing; ``"voorkeursterm_is_begrip"`` als gequote identifier wel.
    """
    from database.schema_contract import fold_identifier, identifier_text

    return (
        re.search(
            rf"(?<!\w){re.escape(fold_identifier(kolom))}(?!\w)",
            fold_identifier(identifier_text(expressie)),
        )
        is not None
    )


def _controleer_kolomsemantiek(
    conn: sqlite3.Connection,
    tabel: str,
    oude_tabel: str,
    kolommen: tuple[str, ...],
    verwijderd: frozenset[str],
) -> None:
    """Weiger als een canonieke kolom in de bron sterkere of andere
    NOT NULL-/DEFAULT-semantiek of een andere affiniteit heeft dan de nieuwe
    canonieke definitie.

    Rootprobe (probe-canonical-column-affinity): een BLOB-bronkolom bewaart
    ``7`` als integer; de ``INSERT … SELECT`` naar een TEXT-kolom maakt daar
    stil ``'7'`` (text) van. Affiniteit bepaalt de opgeslagen waarde en het
    type, dus een verschil is dataverandering en wordt intact geweigerd.
    """
    from database.schema_contract import (
        column_affinity,
        fold_identifier,
        folded_columns,
        key_semantics,
        normalize_sql,
    )

    def _eigenschappen(naam: str) -> dict[str, tuple[str, int, str, tuple[int, int]]]:
        folded_columns(conn, naam)  # fail-closed bij een botsende fold
        sleutels = key_semantics(conn, naam)
        return {
            fold_identifier(rij[1]): (
                column_affinity(rij[2]),
                int(rij[3]),
                normalize_sql(rij[4]),
                sleutels.get(fold_identifier(rij[1]), (0, 0)),
            )
            for rij in conn.execute(f"PRAGMA table_info({naam})")
        }

    oud = _eigenschappen(oude_tabel)
    nieuw = _eigenschappen(tabel)
    weg = {fold_identifier(k) for k in verwijderd}
    verloren: list[str] = []
    for kolom in (fold_identifier(k) for k in kolommen):
        if kolom in weg or kolom not in oud or kolom not in nieuw:
            continue
        oud_aff, oud_notnull, oud_default, oud_sleutel = oud[kolom]
        nieuw_aff, nieuw_notnull, nieuw_default, nieuw_sleutel = nieuw[kolom]
        if oud_aff != nieuw_aff:
            verloren.append(f"{tabel}.{kolom}: affiniteit {oud_aff} -> {nieuw_aff}")
        if oud_sleutel != nieuw_sleutel:
            # Rootprobe rebuild-primary-key-values-v2: INT en INTEGER delen
            # affiniteit, maar alleen INTEGER PRIMARY KEY is een rowid-alias;
            # een NULL-id in de bron zou stil een nieuw id krijgen.
            verloren.append(
                f"{tabel}.{kolom}: sleutelsemantiek (rowid-alias, autoincrement) "
                f"{oud_sleutel} -> {nieuw_sleutel}"
            )
        if oud_notnull and not nieuw_notnull:
            verloren.append(f"{tabel}.{kolom}: NOT NULL")
        if oud_default and oud_default != nieuw_default:
            verloren.append(f"{tabel}.{kolom}: DEFAULT {oud_default}")
    if verloren:
        raise SchemaContractError("rebuild_column_semantics_lost", verloren)


def _herstel_unique_constraints(
    conn: sqlite3.Connection,
    tabel: str,
    voor: tuple[set[UniqueSleutel], frozenset, frozenset[str]],
    verwijderd: frozenset[str],
) -> None:
    """Zet elke verloren UNIQUE-semantiek terug als unique index (DEF-664).

    Benoemde, gequote, composite of op-canonieke-kolom UNIQUE-constraints
    overleven de tabel-DDL van de rebuild niet; een unique index dwingt exact
    dezelfde uniciteit af. Constraints op een bewust verwijderde kolom
    vervallen mee.
    """
    na, _fks, _checks = _tabelconstraints(conn, tabel)
    for sleutel in sorted(voor[0] - na):
        kolommen = [kolom for kolom, _coll in sleutel]
        if _raakt_verwijderde_kolom(kolommen, verwijderd):
            continue
        naam = f"uq_{tabel}_" + "_".join(kolommen)
        teller = 1
        while conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name = ?", (naam,)
        ).fetchone():
            teller += 1
            naam = f"uq_{tabel}_" + "_".join(kolommen) + f"_{teller}"
        definitie = ", ".join(
            f'"{kolom}" COLLATE {coll}' if coll != "BINARY" else f'"{kolom}"'
            for kolom, coll in sleutel
        )
        conn.execute(f'CREATE UNIQUE INDEX "{naam}" ON "{tabel}"({definitie})')
        logger.info(
            f"✅ UNIQUE-semantiek '{tabel}{kolommen}' behouden als index {naam}"
        )


def _controleer_constraintbehoud(
    conn: sqlite3.Connection,
    tabel: str,
    voor: tuple[set[UniqueSleutel], frozenset, frozenset[str]],
    verwijderd: frozenset[str],
) -> None:
    """Afzonderlijke vóór/na-controle van ALLE bronconstraints (DEF-664).

    Elke unieke sleutel, foreign key of CHECK die vóór de rebuild bestond
    moet er ná nog zijn, behalve wat een bewust verwijderde kolom raakt.
    Anders: ``rebuild_constraint_lost`` → de hele migratie rolt terug.
    """
    na = _tabelconstraints(conn, tabel)
    verloren: list[str] = []
    for sleutel in sorted(voor[0] - na[0]):
        if not _raakt_verwijderde_kolom([k for k, _ in sleutel], verwijderd):
            verloren.append(f"unique {tabel}{sleutel}")
    # DEF-688: een FK naar `definities_old` wordt door de rebuild bewust
    # hersteld naar `definities`; vergelijk op het herstelde doel.
    voor_fks = {
        ("definities" if doel == "definities_old" else doel, kol, upd, dele)
        for doel, kol, upd, dele in voor[1]
    }
    for fk in sorted(voor_fks - na[1]):
        if not _raakt_verwijderde_kolom([van for van, _naar in fk[1]], verwijderd):
            verloren.append(f"foreign key {tabel}{fk[1]} -> {fk[0]}")
    for check in sorted(voor[2] - na[2]):
        # Alleen een CHECK die de verwijderde kolom als identifier noemt mag
        # meevervallen; een string-literal met die naam telt niet.
        if not any(_verwijst_naar(check, kolom) for kolom in verwijderd):
            verloren.append(f"check {tabel}: {check}")
    if verloren:
        raise SchemaContractError("rebuild_constraint_lost", verloren)


def _autoincrement_teller(conn: sqlite3.Connection, tabel: str) -> int | None:
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE name = 'sqlite_sequence'"
    ).fetchone():
        return None
    rij = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = ?", (tabel,)
    ).fetchone()
    return None if rij is None else int(rij[0])


def _herstel_autoincrement_teller(
    conn: sqlite3.Connection, tabel: str, seq_voor: int | None
) -> None:
    """Zet de AUTOINCREMENT-high-water-mark terug op minimaal de oude waarde."""
    if seq_voor is None:
        return
    bestaand = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = ?", (tabel,)
    ).fetchone()
    if bestaand is None:
        conn.execute(
            "INSERT INTO sqlite_sequence (name, seq) VALUES (?, ?)", (tabel, seq_voor)
        )
    elif int(bestaand[0]) < seq_voor:
        conn.execute(
            "UPDATE sqlite_sequence SET seq = ? WHERE name = ?", (seq_voor, tabel)
        )


def _extra_kolommen(
    conn: sqlite3.Connection,
    tabel: str,
    kolommen: tuple[str, ...],
    verwijderd: frozenset[str],
) -> list[tuple[str, str]]:
    """Extra (niet-canonieke) kolommen die de rebuild moet behouden (DEF-664).

    Het contract laat extra gebruikerskolommen toe; de statische kopieerlijst
    gooide ze stil weg. Elke extra kolom wordt als ``(naam, declaratie)``
    teruggegeven zodat ze via ``ADD COLUMN`` op de nieuwe tabel terugkomt met
    type, NOT NULL en DEFAULT. Wat niet veilig via ``ADD COLUMN`` te
    reconstrueren is — primary key, NOT NULL zonder default, of een kolom in
    een CHECK-constraint — laat de migratie fail-closed falen in plaats van
    de kolom te verliezen.
    """
    from database.schema_contract import (
        fold_identifier,
        folded_columns,
        normalize_sql,
        split_top_level,
        strip_quoted,
    )

    ddl = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (tabel,)
    ).fetchone()
    genormaliseerd = normalize_sql(ddl[0] if ddl else "")
    body = genormaliseerd[genormaliseerd.find("(") + 1 : genormaliseerd.rfind(")")]
    delen = split_top_level(body)
    extra: list[tuple[str, str]] = []
    onveilig: list[str] = []
    # Codex-review 3: conflictbeleid (UNIQUE/PK ... ON CONFLICT x) en
    # uitgestelde FK-controle (DEFERRABLE) staan niet in PRAGMA-metagegevens
    # en kan de rebuild niet nabouwen. Conservatief: aanwezig buiten quotes
    # ergens in de tabel-DDL → weigeren met de bron intact.
    for deel in delen:
        kaal = strip_quoted(deel)
        for vorm in ("on conflict", "deferrable"):
            if vorm in kaal:
                onveilig.append(f"{tabel}: {vorm} in `{deel[:60]}`")
    # table_xinfo toont ook generated kolommen (hidden 2/3); table_info niet.
    canoniek = {fold_identifier(k) for k in kolommen}
    weg = {fold_identifier(k) for k in verwijderd}
    folded_columns(conn, tabel)  # fail-closed bij een botsende fold
    for _cid, naam, declared, notnull, dflt, pk, hidden in conn.execute(
        f"PRAGMA table_xinfo({tabel})"
    ):
        if fold_identifier(naam) in weg:
            continue
        if fold_identifier(naam) in canoniek:
            # Canonieke kolom: de rebuild schrijft de canonieke definitie.
            # Draagt de bron hier extra semantiek die niet in metagegevens
            # zichtbaar is (COLLATE, generated), dan zou die stil verdwijnen.
            if hidden or _kolomdefinitie_heeft(
                naam, delen, ("collate", "generated", " as(")
            ):
                onveilig.append(f"{tabel}.{naam}")
            continue
        if _kolom_heeft_semantiek(naam, delen, hidden, pk, notnull, dflt):
            onveilig.append(f"{tabel}.{naam}")
            continue
        declaratie = declared or ""
        if notnull:
            declaratie += " NOT NULL"
        if dflt is not None:
            declaratie += f" DEFAULT {dflt}"
        extra.append((naam, declaratie.strip()))
    if onveilig:
        raise SchemaContractError("rebuild_unsafe_extra_column", onveilig)
    return extra


_SEMANTIEK_SLEUTELWOORDEN = (
    "primary key",
    "references",
    "collate",
    "generated",
    "check(",
    " as(",
)


def _buiten_quotes(deel: str) -> str:
    """Alleen de tekst buiten quotes: een literal als DEFAULT 'generated' of
    'references' mag nooit als sleutelwoord tellen."""
    from database.schema_contract import strip_quoted

    return strip_quoted(deel)


def _kolomdefinitie_heeft(
    naam: str, delen: list[str], sleutels: tuple[str, ...]
) -> bool:
    """True als de eigen kolomdefinitie (buiten quotes) een sleutelwoord bevat.

    De definitie wordt met de gedeelde ``column_definition`` gevonden op het
    echte identifier-token (kaal, ``"…"``, ```…```, ``[…]`` of ``'…'``,
    hoofdletterongevoelig) — Codex-review 4. Onvindbaar telt als onveilig:
    een niet herkende declaratie mag nooit "geen semantiek" betekenen.
    """
    from database.schema_contract import column_definition

    deel = column_definition(naam, delen)
    if not deel:
        return True
    kaal = _buiten_quotes(deel)
    return any(sleutel in kaal for sleutel in sleutels)


def _kolom_heeft_semantiek(
    naam: str,
    delen: list[str],
    hidden: int,
    pk: int,
    notnull: int,
    dflt: str | None,
) -> bool:
    """True als ``ADD COLUMN type [NOT NULL] [DEFAULT]`` de kolom niet volledig
    zou reproduceren: generated (hidden), primary key, NOT NULL zonder default,
    of een kolom- of tabelconstraint (FK, COLLATE, CHECK, ...) die de kolom
    raakt. UNIQUE telt hier niet: die semantiek wordt na de rebuild uit de
    metagegevens als unique index teruggezet. Dan faalt de rebuild gesloten en
    blijft het origineel intact.
    """
    if hidden or pk or (notnull and dflt is None):
        return True
    if _kolomdefinitie_heeft(naam, delen, _SEMANTIEK_SLEUTELWOORDEN):
        return True
    from database.schema_contract import _zonder_constraintnaam

    return any(
        _zonder_constraintnaam(deel).startswith(
            ("primary key(", "foreign key(", "check(")
        )
        and _verwijst_naar(deel, naam)
        for deel in delen
    )


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

    DEF-664: één transactie en geen foutafhandeling — een halve normalisatie
    of een geslikte fout liet de migratie voorheen tóch succes melden.

    Returns aantal gewijzigde rijen.
    """
    changed = 0
    with migration_transaction(conn):
        rows = conn.execute("SELECT id, wettelijke_basis FROM definities").fetchall()
        for _id, raw in rows:
            new_val = _normalize_list_json(raw)
            # Update only when changed to reduce write load
            if new_val != (raw or json.dumps([], ensure_ascii=False)):
                conn.execute(
                    "UPDATE definities SET wettelijke_basis = ? WHERE id = ?",
                    (new_val, _id),
                )
                changed += 1
    if changed:
        logger.info(f"✅ Genormaliseerd: {changed} rijen voor wettelijke_basis")
    else:
        logger.info("i  Geen normalisaties nodig voor wettelijke_basis")
    return changed


def _kolom_bestaat(conn: sqlite3.Connection, tabel: str, kolom: str) -> bool:
    return any(rij[1] == kolom for rij in conn.execute(f"PRAGMA table_info({tabel})"))


def _verwijst_naar_definities_old(conn: sqlite3.Connection, tabel: str) -> bool:
    """True als de tabel-DDL nog een FK naar `definities_old` draagt (DEF-688)."""
    rij = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (tabel,)
    ).fetchone()
    return bool(rij and rij[0] and "definities_old" in rij[0])


def _voeg_ontbrekende_kolommen_toe(
    conn: sqlite3.Connection, missing_columns: list[tuple[str, str]]
) -> None:
    """ALTER TABLE voor de legacy kolommen; elke fout loopt door naar de aanroeper."""
    # Use whitelist for security: only predefined columns
    allowed_columns = {
        "datum_voorstel": "TIMESTAMP",
        "ketenpartners": "TEXT",
        "wettelijke_basis": "TEXT",
        "ufo_categorie": "TEXT",
    }
    for column_name, column_type in missing_columns:
        if allowed_columns.get(column_name) != column_type:
            logger.warning(f"⚠️ Kolom '{column_name}' niet toegestaan vanwege security")
            continue
        conn.execute(f"ALTER TABLE definities ADD COLUMN {column_name} {column_type}")
        logger.info(f"✅ Kolom toegevoegd: {column_name}")
        if column_name == "datum_voorstel":
            conn.execute(
                "UPDATE definities SET datum_voorstel = created_at "
                "WHERE datum_voorstel IS NULL"
            )
            logger.info("✅ Default waardes gezet voor datum_voorstel")


def _zorg_voor_voorkeursterm(conn: sqlite3.Connection) -> None:
    """Voeg `definities.voorkeursterm` toe en backfill uit de oude bronnen.

    DEF-664: de verouderde kolommen `is_voorkeursterm` en
    `voorkeursterm_is_begrip` worden niet meer eerst toegevoegd — dat dwong
    op élke run een volledige tabelrebuild af. De backfill gebruikt ze alleen
    als ze werkelijk nog bestaan, en faalt hard in plaats van met een warning.
    """
    if _kolom_bestaat(conn, "definities", "voorkeursterm"):
        return
    conn.execute("ALTER TABLE definities ADD COLUMN voorkeursterm TEXT")
    logger.info("✅ Kolom 'voorkeursterm' toegevoegd aan 'definities'")
    if _kolom_bestaat(conn, "definitie_voorbeelden", "is_voorkeursterm"):
        conn.execute(VOORKEURSTERM_BACKFILL_UIT_SYNONIEMEN_SQL)
    if _kolom_bestaat(conn, "definities", "voorkeursterm_is_begrip"):
        conn.execute(VOORKEURSTERM_BACKFILL_UIT_VLAG_SQL)
    logger.info("✅ Backfill voor 'voorkeursterm' uitgevoerd")


def _zorg_voor_extra_indexen(conn: sqlite3.Connection) -> None:
    conn.execute(DATUM_VOORSTEL_INDEX_DDL)
    logger.info("✅ Index toegevoegd voor datum_voorstel")
    # Case-insensitive synoniem lookup index (SQLite supports expression indexes)
    conn.execute(SYNONIEMEN_INDEX_DDL)
    logger.info("✅ Index toegevoegd voor synoniemen (CI)")


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

    # DEF-664: geverifieerde WAL-veilige backup vóór de eerste schrijfactie.
    # De DEF-663-guard weigert een bron zonder kernschema; dan wordt niets
    # gewijzigd.
    try:
        backup_path = create_migration_backup(
            Path(db_path), "pre_legacy_migration", datetime.now()
        )
    except SchemaContractError as exc:
        logger.error(
            "❌ Backup geweigerd (%s); migratie afgebroken, niets gewijzigd",
            ", ".join(exc.details),
        )
        return False
    logger.info("Backup geverifieerd: %s", backup_path)

    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.Error as e:
        logger.error(f"❌ Kan niet verbinden met database: {e}")
        return False

    try:
        # DEF-664: geen `with sqlite3.connect(...)` — die context commit alleen
        # en sluit niet. Het `finally` hieronder sluit altijd.
        if True:
            # DEF-672: autocommit, zodat de transactiegrens expliciet is. Met de
            # impliciete transactie van de sqlite3-module zou BEGIN botsen.
            conn.isolation_level = None

            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")

            # DEF-664: de route verandert de schemaversie niet; het profiel
            # van de bron is ook het doelcontract. Onbekende versies weigeren.
            bronversie = schema_version(conn)
            profiel = 0 if bronversie is None else bronversie
            if profiel not in SUPPORTED_VERSIONS:
                logger.error(
                    "❌ Schemaversie %s wordt niet ondersteund; niets gewijzigd",
                    bronversie,
                )
                return False

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

            # DEF-664: de héle logische migratie is één transactie — ADD COLUMN,
            # backfill, indexen, rebuilds (als SAVEPOINT), normalisatie én de
            # eindverificatie. Faalt ook maar iets, inclusief de COMMIT zelf,
            # dan is de database exact zoals ervoor. De PRAGMA's van
            # `_migratiemodus` staan bewust búiten de transactie: binnen een
            # transactie is `foreign_keys` een no-op.
            with _migratiemodus(conn), migration_transaction(conn):
                _voeg_ontbrekende_kolommen_toe(conn, missing_columns)
                _zorg_voor_voorkeursterm(conn)
                _zorg_voor_extra_indexen(conn)
                _herbouw_tabellen_indien_nodig(conn)

                # Normaliseer wettelijke_basis voor betrouwbare duplicate-check
                _normalize_wettelijke_basis(conn)

                # DEF-672: succes is een uitkomst, geen aanname. DEF-664: plus
                # het volledige doelcontract van het bronprofiel; alles nog
                # binnen de transactie, zodat een afwijzing niets achterlaat.
                problemen = _verifieer_migratie(conn, verwachte_objecten)
                problemen += verify_target_contract(conn, profiel)
                if problemen:
                    for probleem in problemen:
                        logger.error(f"❌ Migratieverificatie: {probleem}")
                    raise SchemaContractError(
                        "migration_verification_failed", problemen
                    )

            logger.info("✅ Database migratie + normalisatie succesvol!")
            return True

    except Exception as e:
        logger.error(f"❌ Database migratie mislukt: {e}")
        return False
    finally:
        conn.close()


def _herbouw_tabellen_indien_nodig(conn: sqlite3.Connection) -> None:
    """De DEF-672-rebuilds, elk als SAVEPOINT binnen de buitenste transactie.

    Elke stap die faalt rolt de héle migratie terug; de uitzondering loopt
    door naar de buitenste handler, die de migratie als mislukt rapporteert.
    Geen warning-plus-doorgaan meer voor verplichte migratiestappen.
    """
    # 1) definitie_voorbeelden: rebuild als de verouderde kolom er nog is óf
    #    als de FK nog naar `definities_old` wijst (DEF-688). DEF-664: voorheen
    #    dwong de migratie deze rebuild elke run af door de kolom eerst zelf
    #    toe te voegen.
    if _kolom_bestaat(
        conn, "definitie_voorbeelden", "is_voorkeursterm"
    ) or _verwijst_naar_definities_old(conn, "definitie_voorbeelden"):
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
            verwijderd=frozenset({"is_voorkeursterm"}),
        )
        logger.info("✅ Kolom 'is_voorkeursterm' verwijderd")

    # 2) definities: drop voorkeursterm_is_begrip if present
    if _kolom_bestaat(conn, "definities", "voorkeursterm_is_begrip"):
        logger.info("🔧 Rebuild 'definities' zonder kolom 'voorkeursterm_is_begrip'")
        _rebuild_tabel_atomair(
            conn,
            tabel="definities",
            tijdelijke_naam="definities_old",
            maak_tabel=_create_definities_table,
            kolommen=DEFINITIES_KOLOMMEN,
            zorg_voor_indexen=_ensure_definities_indexes,
            verwijderd=frozenset({"voorkeursterm_is_begrip"}),
        )
        logger.info("✅ Kolom 'voorkeursterm_is_begrip' verwijderd")


def verify_migration(db_path: str = "data/definities.db") -> bool:
    """
    Verifieer dat de migratie succesvol was.

    Args:
        db_path: Pad naar database
    """
    logger.info("Verifying database schema...")

    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.Error as e:
        logger.error(f"Verificatie mislukt: {e}")
        return False

    try:
        # DEF-664 (Codex-herreview): expliciete closure; de sqlite3-context
        # committe alleen en sloot nooit.
        if True:
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
    finally:
        conn.close()


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
            # DEF-664: een incomplete uitkomst is een mislukking, geen warning.
            logger.error("Database migratie incompleet")
            sys.exit(1)
    else:
        logger.error("Database migratie mislukt!")
        sys.exit(1)
