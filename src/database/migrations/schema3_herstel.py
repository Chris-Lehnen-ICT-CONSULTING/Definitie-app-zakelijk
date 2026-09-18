"""Herstelroute: verouderde schema-3-database → nieuw doel op schemaversie 4.

Aanleiding (DEF-751, ESS-02 lokale activering): de bestaande gebruikersdatabase
draagt versiemarker 3 maar voldoet niet aan het schema-3-contract. De marker
is geen bewijs. Concreet (gemeten, read-only):

- ``definitie_geschiedenis``, ``definitie_tags`` en ``import_export_logs``
  missen hun foreign keys en CHECK-constraints en gebruiken ``TEXT`` in
  plaats van ``TIMESTAMP``-affiniteit;
- tabel ``externe_bronnen``, vier indexen op ``definities``, de triggers
  ``update_definities_timestamp``/``log_definitie_changes`` en de drie views
  ontbreken;
- een deel van de geschiedenisrijen verwijst naar een definitie die niet
  (meer) bestaat.

De bestaande v8-route en de legacy-route weigeren zo'n bron terecht
(``migration_target_contract_failed``). Deze module is de kleinste expliciete
route ernaartoe. Zij:

1. opent de bron uitsluitend read-only en maakt met het DEF-663-contract
   (``create_verified_backup``) een geverifieerde kopie in een eigen
   tijdelijke map naast het doel — de bron wordt nooit geopend voor schrijven;
2. herstelt op die kopie, in één transactie, uitsluitend de bekende
   afwijkingen: de drie tabellen worden herbouwd naar de canonieke DDL uit
   ``schema.sql``; geschiedenisrijen zonder bestaande definitie gaan volledig
   (originele id, originele ``definitie_id``, alle velden) naar de
   bewaartabel ``definitie_geschiedenis_verweesd`` — zonder FK, met een
   herleidbare reden; ontbrekende objecten worden uit ``schema.sql``
   aangemaakt. Daarna moet het volledige schema-3-contract slagen;
3. voert de bestaande v8-migratie uit (versie 4);
4. vergelijkt vóór publicatie de volledige inhoud van bron en doel: elke
   brontabel rij-voor-rij (waarde én ``typeof``) gelijk, de geschiedenis
   exact gesplitst in gekoppeld + bewaard, ``schema_version`` behouden plus
   4, autoincrement-tellers niet teruggezet, contract v4 en
   integrity/foreign_key_check groen;
5. publiceert eerst het optionele rapport exclusief (nieuw bestand, geen
   overschrijven, geen symlink volgen) en daarna het doel atomisch
   (``publish_staged_file``; weigert een bestaand doel); faalt het doel, dan
   wordt het eigen rapport weer verwijderd. Daarna wordt de eigen tijdelijke
   map opgeruimd.

Fail-closed: elke onbekende variant (extra of generated kolom, collatie,
andere declaratie of constraint, waarde die door de affiniteitswissel zou
veranderen, ongeldige enumwaarde, verweesde tag) wordt geweigerd; er wordt
nooit een waarde aangepast of weggegooid en nooit een ontbrekende definitie
verzonnen. Bron, doel en rapport mogen geen alias van elkaar zijn. Bij elke
fout bestaat het doel niet. Logging en het rapport bevatten alleen codes,
namen, aantallen en hashes — nooit rijinhoud.

De kopie is een momentopname: schrijvers op de bron moeten vóór de
definitieve kopie gestopt zijn en gestopt blijven tot de nieuwe database
actief is (zie de beheerinstructie); de route zelf kan latere schrijfacties
niet zien.

CLI: ``python -m database.migrations.schema3_herstel BRON DOEL [--rapport PAD]``.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import logging
import os
import re
import shutil
import sqlite3
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from database.migrate_database import (
    _autoincrement_teller,
    _bewaar_afhankelijke_objecten,
    _ensure_definities_indexes,
    _herstel_afhankelijke_objecten,
    _herstel_autoincrement_teller,
    _migratiemodus,
)
from database.migrations.v8_migration import run_migration as v8_run_migration
from database.schema_contract import (
    SCHEMA_PATH,
    SchemaContract,
    SchemaContractError,
    migration_transaction,
    normalize_sql,
    read_contract,
    schema_objects,
    schema_version,
    split_top_level,
    strict_versions,
    target_contract,
    verify_target_contract,
)
from database.sqlite_backup import (
    BackupError,
    create_verified_backup,
    open_readonly_snapshot,
    publish_staged_file,
    validate_new_destination,
)

logger = logging.getLogger(__name__)

BRONVERSIE = 3
DOELVERSIE = 4

BEWAARTABEL = "definitie_geschiedenis_verweesd"
BEWAAR_REDEN = "definitie_ontbreekt"
BEWAARD_DOOR = "DEF-751 schema3_herstel"

#: De tabellen die in de bekende legacy-vorm herbouwd worden naar canoniek.
HERSTEL_TABELLEN: tuple[str, ...] = (
    "definitie_geschiedenis",
    "definitie_tags",
    "import_export_logs",
)

#: Objecten die in de legacy-bron ontbreken en uit schema.sql worden aangemaakt.
AANVULLEN_TABELLEN: tuple[str, ...] = ("externe_bronnen",)
AANVULLEN_TRIGGERS: tuple[str, ...] = (
    "update_definities_timestamp",
    "log_definitie_changes",
)
AANVULLEN_VIEWS: tuple[str, ...] = (
    "actieve_definities",
    "vastgestelde_definities",
    "definitie_statistieken",
)

# De bekende legacy-vorm (letterlijk zoals gemeten in de gebruikersdatabase):
# geen FK, geen CHECK, TEXT-tijdstempels. Alleen een tabel die structureel
# hiermee overeenkomt (kolommen, affiniteit, NOT NULL, DEFAULT, sleutels,
# uniciteit, geen FK/CHECK) wordt herbouwd; elke andere vorm is onbekend.
LEGACY_DDL: dict[str, str] = {
    "definitie_geschiedenis": """
CREATE TABLE definitie_geschiedenis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL,
    begrip TEXT NOT NULL,
    definitie_oude_waarde TEXT,
    definitie_nieuwe_waarde TEXT,
    wijziging_type TEXT NOT NULL,
    wijziging_reden TEXT,
    gewijzigd_door TEXT,
    gewijzigd_op TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    context_snapshot TEXT
)""",
    "definitie_tags": """
CREATE TABLE definitie_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL,
    tag_naam TEXT NOT NULL,
    tag_waarde TEXT,
    toegevoegd_door TEXT,
    toegevoegd_op TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(definitie_id, tag_naam)
)""",
    "import_export_logs": """
CREATE TABLE import_export_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operatie_type TEXT NOT NULL,
    bron_bestemming TEXT NOT NULL,
    aantal_verwerkt INTEGER NOT NULL DEFAULT 0,
    aantal_succesvol INTEGER NOT NULL DEFAULT 0,
    aantal_gefaald INTEGER NOT NULL DEFAULT 0,
    bestand_pad TEXT,
    formaat TEXT,
    fouten_details TEXT,
    gestart_op TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    voltooid_op TEXT,
    gestart_door TEXT,
    status TEXT NOT NULL DEFAULT 'running'
)""",
}

_VERWEESD_PREDICAAT = "definitie_id NOT IN (SELECT id FROM definities)"


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------
@dataclass
class TabelVergelijking:
    """Veldvolgorde = twee ``tabelhash``-tupels (aantal, hash): bron, dan doel."""

    bron_aantal: int
    bron_hash: str
    doel_aantal: int
    doel_hash: str

    @property
    def gelijk(self) -> bool:
        return self.bron_aantal == self.doel_aantal and self.bron_hash == self.doel_hash


@dataclass
class HerstelRapport:
    """Veilige metadata van een geslaagde herstelroute: codes, aantallen, hashes."""

    bronversie: int
    doelversie: int
    tabellen: dict[str, TabelVergelijking] = field(default_factory=dict)
    geschiedenis_totaal: int = 0
    geschiedenis_gekoppeld: int = 0
    geschiedenis_verweesd: int = 0
    geschiedenis_gekoppeld_hash: str = ""
    geschiedenis_verweesd_hash: str = ""
    schema_version_bron: list[int] = field(default_factory=list)
    schema_version_doel: list[int] = field(default_factory=list)
    sqlite_sequence_bron: dict[str, int] = field(default_factory=dict)
    sqlite_sequence_doel: dict[str, int] = field(default_factory=dict)
    nieuwe_tabellen: list[str] = field(default_factory=list)
    herbouwde_tabellen: list[str] = field(default_factory=list)
    aangevulde_objecten: list[str] = field(default_factory=list)
    doel_schema_hash: str = ""
    integrity_check: str = ""
    foreign_key_check_schendingen: int = -1
    contract_problemen: list[str] = field(default_factory=list)

    def als_dict(self) -> dict:
        uit = asdict(self)
        for naam, vergelijking in self.tabellen.items():
            uit["tabellen"][naam]["gelijk"] = vergelijking.gelijk
        return uit


# ---------------------------------------------------------------------------
# Hashing (inhoud verlaat nooit het proces; alleen de digest)
# ---------------------------------------------------------------------------
def _q(naam: str) -> str:
    return '"' + naam.replace('"', '""') + '"'


def _kolomnamen(conn: sqlite3.Connection, tabel: str) -> tuple[str, ...]:
    """Alle kolommen, óók verborgen generated kolommen (``table_xinfo``):
    een kolom die ``table_info`` niet toont mag niet stil verdwijnen."""
    return tuple(rij[1] for rij in conn.execute(f"PRAGMA table_xinfo({_q(tabel)})"))


def _rijhash(rij: tuple) -> bytes:
    """Digest van één rij: per waarde het SQLite-type én de waarde zelf.

    ``typeof`` staat expliciet in de invoer: een tekst ``'7'`` en een integer
    ``7`` hashen verschillend, zodat een affiniteitswissel die waarden
    stil zou omzetten altijd zichtbaar is.
    """
    h = hashlib.sha256()
    for i in range(0, len(rij), 2):
        soort, waarde = rij[i], rij[i + 1]
        h.update(str(soort).encode())
        h.update(b"\x00")
        if isinstance(waarde, bytes):
            h.update(waarde)
        elif waarde is None:
            h.update(b"")
        else:
            h.update(repr(waarde).encode())
        h.update(b"\x01")
    return h.digest()


def tabelhash(
    conn: sqlite3.Connection,
    tabel: str,
    kolommen: tuple[str, ...],
    predicaat: str = "1=1",
) -> tuple[int, str]:
    """(aantal, sha256) van de rijen van ``tabel`` over ``kolommen``.

    Volgorde-onafhankelijk: rijdigests worden gesorteerd vóór de totaalhash,
    zodat een herbouwde tabel met dezelfde rijen dezelfde hash krijgt.
    """
    selectie = ", ".join(f"typeof({_q(k)}), {_q(k)}" for k in kolommen)
    digests = sorted(
        _rijhash(rij)
        for rij in conn.execute(f"SELECT {selectie} FROM {_q(tabel)} WHERE {predicaat}")
    )
    totaal = hashlib.sha256()
    for digest in digests:
        totaal.update(digest)
    return len(digests), totaal.hexdigest()


def schemahash(conn: sqlite3.Connection) -> str:
    """sha256 over de volledige, gesorteerde sqlite_master-DDL (zonder inhoud)."""
    h = hashlib.sha256()
    for rij in conn.execute(
        "SELECT type, name, tbl_name, COALESCE(sql, '') FROM sqlite_master "
        "ORDER BY type, name"
    ):
        h.update("\x1f".join(rij).encode())
        h.update(b"\n")
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Canonieke en legacy contracten
# ---------------------------------------------------------------------------
CanoniekeDDL = dict[tuple[str, str], tuple[str, str]]
"""(type, naam) → (tabel, DDL-tekst) van elk object in ``schema.sql``."""


def _canonieke_ddl() -> CanoniekeDDL:
    """De canonieke DDL, letterlijk uit ``schema.sql`` via een geheugendatabase."""
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        return {
            (soort, naam): (tabel, sql)
            for soort, naam, tabel, sql in conn.execute(
                "SELECT type, name, tbl_name, sql FROM sqlite_master "
                "WHERE sql IS NOT NULL"
            )
        }
    finally:
        conn.close()


def _if_not_exists(ddl: str) -> str:
    """``CREATE [UNIQUE] INDEX x`` → ``CREATE [UNIQUE] INDEX IF NOT EXISTS x``."""
    return re.sub(
        r"^\s*create\s+(unique\s+)?index\s+(?!if\s+not\s+exists)",
        lambda m: f"CREATE {m.group(1) or ''}INDEX IF NOT EXISTS ",
        ddl,
        count=1,
        flags=re.IGNORECASE,
    )


def _legacy_contract() -> SchemaContract:
    conn = sqlite3.connect(":memory:")
    try:
        for ddl in LEGACY_DDL.values():
            conn.execute(ddl)
        return read_contract(conn)
    finally:
        conn.close()


def _tabelstructuur(contract: SchemaContract, tabel: str) -> tuple:
    """De structuur van één tabel, los van indexen/triggers: kolommen (naam,
    affiniteit, NOT NULL, DEFAULT, sleutelsemantiek), CHECKs, UNIQUE's, FK's."""
    return (
        contract.columns.get(tabel),
        contract.checks.get(tabel, frozenset()),
        contract.unique_constraints.get(tabel, frozenset()),
        contract.foreign_keys.get(tabel, frozenset()),
    )


def _ddl_delen(table_sql: str | None) -> frozenset[str]:
    """De genormaliseerde top-level onderdelen (kolomdefinities en
    tabelconstraints) van een ``CREATE TABLE``, volgorde-onafhankelijk."""
    genormaliseerd = normalize_sql(table_sql)
    begin, einde = genormaliseerd.find("("), genormaliseerd.rfind(")")
    if begin < 0 or einde <= begin:
        return frozenset()
    return frozenset(split_top_level(genormaliseerd[begin + 1 : einde]))


def _is_bekende_legacy_vorm(conn: sqlite3.Connection, tabel: str) -> bool:
    """Strikt: de volledige tabel-DDL is, genormaliseerd en per onderdeel,
    gelijk aan ``LEGACY_DDL`` en er zijn geen verborgen (generated) kolommen.

    Codex-review 1544296bc: de PRAGMA-metagegevens van het contract zien
    generated kolommen en kolomcollaties niet; een ``GENERATED … VIRTUAL``-
    kolom of ``COLLATE NOCASE`` verdween daardoor stil uit de herbouwde en
    de bewaarde historie terwijl de route succes meldde. Alleen de letterlijke
    (genormaliseerde) declaratie telt nu als bekend; elke andere semantiek —
    generated, collatie, ander type, andere DEFAULT, kolom-CHECK, FK — is
    onbekend en wordt vóór de herbouw geweigerd.
    """
    rij = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?", (tabel,)
    ).fetchone()
    if rij is None or _ddl_delen(rij[0]) != _ddl_delen(LEGACY_DDL[tabel]):
        return False
    verborgen = [
        naam
        for _cid, naam, *_rest, hidden in conn.execute(
            f"PRAGMA table_xinfo({_q(tabel)})"
        )
        if hidden
    ]
    return not verborgen


def classificeer_tabel(
    conn: sqlite3.Connection,
    waargenomen: SchemaContract,
    tabel: str,
    canoniek: SchemaContract,
    legacy: SchemaContract,
) -> str:
    """``canoniek`` (niets te doen), ``legacy`` (herbouwen) of ``onbekend``.

    Canoniek = contractstructuur gelijk aan ``schema.sql`` (de tabel wordt
    dan niet herbouwd, dus extra semantiek gaat niet verloren). Legacy =
    contractstructuur gelijk aan de legacy-vorm én de letterlijke DDL gelijk
    (``_is_bekende_legacy_vorm``). Al het andere is onbekend.
    """
    if waargenomen.columns.get(tabel) is None:
        return "onbekend"
    structuur = _tabelstructuur(waargenomen, tabel)
    if structuur == _tabelstructuur(canoniek, tabel):
        return "canoniek"
    if structuur == _tabelstructuur(legacy, tabel) and _is_bekende_legacy_vorm(
        conn, tabel
    ):
        return "legacy"
    return "onbekend"


# ---------------------------------------------------------------------------
# Herstelstappen (binnen één transactie op de kopie)
# ---------------------------------------------------------------------------
def _controleer_rijwaarden(
    conn: sqlite3.Connection, nieuw: str, oud: str, kolommen: tuple[str, ...]
) -> None:
    """Weiger als de kopie naar de canonieke tabel ook maar één waarde of type
    veranderde (bijv. ``'20250101'`` dat door NUMERIC-affiniteit integer wordt).

    Vergelijkt per rij op ``id`` tussen de nieuwe en de oude tabel; meldt alleen
    tabel, kolom en aantal — nooit de waarde.
    """
    afwijkingen: list[str] = []
    for kolom in kolommen:
        n, o = f"n.{_q(kolom)}", f"o.{_q(kolom)}"
        aantal = conn.execute(
            f"SELECT COUNT(*) FROM {_q(nieuw)} n JOIN {_q(oud)} o ON n.id = o.id "
            f"WHERE {n} IS NOT {o} OR typeof({n}) <> typeof({o})"
        ).fetchone()[0]
        if aantal:
            afwijkingen.append(f"{nieuw}.{kolom}: {aantal} rij(en)")
    if afwijkingen:
        raise SchemaContractError("herstel_waarden_gewijzigd", afwijkingen)


def _kopieer_rijen(
    conn: sqlite3.Connection,
    doel: str,
    bron: str,
    kolommen: tuple[str, ...],
    predicaat: str,
    extra: tuple[tuple[str, str], ...] = (),
) -> int:
    """``INSERT … SELECT`` van ``bron`` naar ``doel``; een constraintschending
    (CHECK/NOT NULL/UNIQUE van de canonieke DDL) is een weigering, geen fix."""
    doelkolommen = ", ".join(_q(k) for k in kolommen) + "".join(
        f", {_q(k)}" for k, _ in extra
    )
    bronkolommen = ", ".join(_q(k) for k in kolommen) + "".join(
        f", {waarde}" for _, waarde in extra
    )
    try:
        cursor = conn.execute(
            f"INSERT INTO {_q(doel)} ({doelkolommen}) "
            f"SELECT {bronkolommen} FROM {_q(bron)} WHERE {predicaat}"
        )
    except sqlite3.IntegrityError as exc:
        # De SQLite-melding noemt constraint en kolom, nooit een rijwaarde.
        raise SchemaContractError(
            "herstel_ongeldige_waarden", (f"{doel}: {exc}",)
        ) from None
    return int(cursor.rowcount)


def _herbouw_naar_canoniek(
    conn: sqlite3.Connection,
    tabel: str,
    ddl: CanoniekeDDL,
    *,
    verweesd_naar: str | None = None,
) -> tuple[int, int]:
    """Herbouw ``tabel`` naar de canonieke DDL; geeft (gekoppeld, verweesd).

    Rename → canonieke CREATE → kopie (alle bronkolommen, alle rijen behalve
    de verweesde) → rijwaardencontrole → DROP oud → indexen/triggers terug →
    autoincrement-teller terug. Met ``verweesd_naar`` gaan de rijen zonder
    bestaande definitie volledig naar die bewaartabel.
    """
    oud = f"{tabel}_old"
    kolommen = _kolomnamen(conn, tabel)
    bewaard = _bewaar_afhankelijke_objecten(conn, tabel)
    seq_voor = _autoincrement_teller(conn, tabel)
    with migration_transaction(conn, savepoint=f"herstel_{tabel}"):
        conn.execute(f"ALTER TABLE {_q(tabel)} RENAME TO {_q(oud)}")
        conn.execute(ddl[("table", tabel)][1])
        predicaat = "1=1"
        verweesd = 0
        if verweesd_naar is not None:
            predicaat = f"NOT ({_VERWEESD_PREDICAAT})"
            _maak_bewaartabel(conn, verweesd_naar, oud, kolommen)
            verweesd = _kopieer_rijen(
                conn,
                verweesd_naar,
                oud,
                kolommen,
                _VERWEESD_PREDICAAT,
                extra=(
                    ("bewaar_reden", f"'{BEWAAR_REDEN}'"),
                    ("bewaard_door", f"'{BEWAARD_DOOR}'"),
                ),
            )
            _controleer_rijwaarden(conn, verweesd_naar, oud, kolommen)
        gekoppeld = _kopieer_rijen(conn, tabel, oud, kolommen, predicaat)
        _controleer_rijwaarden(conn, tabel, oud, kolommen)
        totaal = conn.execute(f"SELECT COUNT(*) FROM {_q(oud)}").fetchone()[0]
        if gekoppeld + verweesd != totaal:
            raise SchemaContractError(
                "herstel_rijen_verloren", (f"{tabel}: {totaal - gekoppeld - verweesd}",)
            )
        conn.execute(f"DROP TABLE {_q(oud)}")
        # De eigen indexen/triggers van de bron komen letterlijk terug (ook
        # extra gebruikersindexen); canonieke indexen die de bron miste erbij.
        _herstel_afhankelijke_objecten(conn, bewaard)
        for (soort, _naam), (eigenaar, tekst) in ddl.items():
            if soort == "index" and eigenaar == tabel:
                conn.execute(_if_not_exists(tekst))
        _herstel_autoincrement_teller(conn, tabel, seq_voor)
    logger.info(
        "herstel: %s herbouwd (gekoppeld=%d, verweesd=%d)", tabel, gekoppeld, verweesd
    )
    return gekoppeld, verweesd


def _maak_bewaartabel(
    conn: sqlite3.Connection, naam: str, bron: str, kolommen: tuple[str, ...]
) -> None:
    """Bewaartabel met exact de brondeclaraties (type, NOT NULL, DEFAULT) van
    elke oorspronkelijke kolom — geen affiniteitswissel, geen FK — plus de
    herkomstkolommen. ``id`` blijft de originele geschiedenis-id."""
    declaraties: list[str] = []
    for _cid, kolom, declared, notnull, dflt, pk in conn.execute(
        f"PRAGMA table_info({_q(bron)})"
    ):
        if kolom not in kolommen:
            continue
        if pk:
            declaraties.append(f"{_q(kolom)} {declared} PRIMARY KEY")
            continue
        tekst = f"{_q(kolom)} {declared}"
        if notnull:
            tekst += " NOT NULL"
        if dflt is not None:
            tekst += f" DEFAULT {dflt}"
        declaraties.append(tekst)
    declaraties += [
        "bewaar_reden TEXT NOT NULL",
        "bewaard_door TEXT NOT NULL",
        "bewaard_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ]
    conn.execute(
        f"CREATE TABLE {_q(naam)} (\n    " + ",\n    ".join(declaraties) + "\n)"
    )
    conn.execute(
        f"CREATE INDEX {_q('idx_' + naam + '_definitie_id')} ON {_q(naam)}(definitie_id)"
    )


def _precondities(conn: sqlite3.Connection) -> None:
    """Weiger vóór enige schrijfactie wat deze route niet mag oplossen."""
    details: list[str] = []
    versie = schema_version(conn)
    if versie != BRONVERSIE:
        details.append(f"schema_version {versie}, verwacht {BRONVERSIE}")
    if _bestaat(conn, "table", BEWAARTABEL):
        details.append(f"tabel {BEWAARTABEL} bestaat al in de bron")
    for tabel in HERSTEL_TABELLEN:
        if _bestaat(conn, "table", f"{tabel}_old"):
            details.append(f"tabel {tabel}_old bestaat al in de bron")
    if details:
        raise SchemaContractError("herstel_precondition_failed", details)
    verweesde_tags = conn.execute(
        f"SELECT COUNT(*) FROM definitie_tags WHERE {_VERWEESD_PREDICAAT}"
    ).fetchone()[0]
    if verweesde_tags:
        raise SchemaContractError(
            "herstel_ongeldige_waarden",
            (f"definitie_tags: {verweesde_tags} rij(en) zonder definitie",),
        )


def _bestaat(conn: sqlite3.Connection, soort: str, naam: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = ? AND name = ?", (soort, naam)
        ).fetchone()
        is not None
    )


def _herstelplan(conn: sqlite3.Connection) -> list[str]:
    """De herstel-tabellen die in de bekende legacy-vorm staan (te herbouwen).

    Canonieke tabellen slaan over; elke andere vorm is een weigering
    (``herstel_onbekende_variant``) vóór enige schrijfactie.
    """
    canoniek, legacy = target_contract(DOELVERSIE), _legacy_contract()
    waargenomen = read_contract(conn)
    plan = {
        tabel: classificeer_tabel(conn, waargenomen, tabel, canoniek, legacy)
        for tabel in HERSTEL_TABELLEN
    }
    onbekend = [
        f"tabel {tabel}: noch canoniek, noch bekende legacy-vorm"
        for tabel, soort in plan.items()
        if soort == "onbekend"
    ]
    if onbekend:
        raise SchemaContractError("herstel_onbekende_variant", onbekend)
    return [tabel for tabel, soort in plan.items() if soort == "legacy"]


def _vul_ontbrekende_objecten_aan(
    conn: sqlite3.Connection, ddl: CanoniekeDDL, rapport: HerstelRapport
) -> None:
    """Maak de canonieke objecten aan die de legacy-bron mist; bestaande
    objecten blijven staan (het contract toetst ze daarna)."""
    for soort, namen in (
        ("table", AANVULLEN_TABELLEN),
        ("trigger", AANVULLEN_TRIGGERS),
        ("view", AANVULLEN_VIEWS),
    ):
        for naam in namen:
            if _bestaat(conn, soort, naam):
                continue
            conn.execute(ddl[(soort, naam)][1])
            rapport.aangevulde_objecten.append(f"{soort} {naam}")
            if soort == "table":
                rapport.nieuwe_tabellen.append(naam)
    # Ontbrekende canonieke indexen op definities (idempotente helper van de
    # legacy-route: IF NOT EXISTS).
    voor = schema_objects(conn)
    _ensure_definities_indexes(conn)
    rapport.aangevulde_objecten += sorted(
        f"{soort} {naam}" for soort, naam in schema_objects(conn) - voor
    )


def herstel_schema3(conn: sqlite3.Connection, rapport: HerstelRapport) -> None:
    """Herstel de bekende schema-3-afwijkingen op ``conn`` (de kopie), in één
    transactie, en eis daarna het volledige schema-3-contract.

    Vereist een autocommit-connectie. De aanroeper heeft de bron al verwacht
    op versie 3; deze functie verandert de versiemarkers niet.
    """
    _precondities(conn)
    te_herbouwen = _herstelplan(conn)
    ddl = _canonieke_ddl()
    bronobjecten = schema_objects(conn)
    with _migratiemodus(conn), migration_transaction(conn):
        for tabel in te_herbouwen:
            bewaar = BEWAARTABEL if tabel == "definitie_geschiedenis" else None
            _herbouw_naar_canoniek(conn, tabel, ddl, verweesd_naar=bewaar)
            rapport.herbouwde_tabellen.append(tabel)
            if bewaar:
                rapport.nieuwe_tabellen.append(bewaar)
        _vul_ontbrekende_objecten_aan(conn, ddl, rapport)
        problemen = [
            f"verdwenen: {obj}"
            for obj in sorted(
                f"{s} {n}" for s, n in bronobjecten - schema_objects(conn)
            )
        ]
        problemen += verify_target_contract(conn, BRONVERSIE)
        if problemen:
            for probleem in problemen:
                logger.error("herstel: contract v%d: %s", BRONVERSIE, probleem)
            raise SchemaContractError("migration_target_contract_failed", problemen)
    logger.info("herstel: schema-3-contract volledig; wijzigingen gecommit")


# ---------------------------------------------------------------------------
# Vergelijking bron ↔ doel (vóór publicatie)
# ---------------------------------------------------------------------------
def vergelijk_bron_en_doel(
    bron: sqlite3.Connection, doel: sqlite3.Connection, rapport: HerstelRapport
) -> list[str]:
    """Volledige inhoudsvergelijking; leeg = het doel is de bron zonder verlies.

    Elke brontabel moet in het doel dezelfde rijen dragen (waarde + type),
    met drie bekende, exact getoetste uitzonderingen: de geschiedenis is
    gesplitst (gekoppeld ↔ bewaard, samen = bron), ``schema_version`` is de
    bron plus precies versie 4, ``sqlite_sequence`` is per teller gelijk
    (``schema_version`` één hoger). Doeltabellen die de bron niet had zijn
    uitsluitend de bewaartabel en de aangevulde canonieke tabellen.
    """
    problemen: list[str] = []
    brontabellen = [
        rij[0]
        for rij in bron.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND lower(substr(name, 1, 7)) <> 'sqlite_' ORDER BY name"
        )
    ]
    for tabel in brontabellen:
        if not _bestaat(doel, "table", tabel):
            problemen.append(f"tabel {tabel} ontbreekt in doel")
            continue
        kolommen = _kolomnamen(bron, tabel)
        ontbrekend = set(kolommen) - set(_kolomnamen(doel, tabel))
        if ontbrekend:
            problemen.append(f"kolommen verloren in {tabel}: {sorted(ontbrekend)}")
            continue
        if tabel == "definitie_geschiedenis":
            problemen += _vergelijk_geschiedenis(bron, doel, kolommen, rapport)
            continue
        if tabel == "schema_version":
            problemen += _vergelijk_schema_version(bron, doel, kolommen, rapport)
            continue
        vergelijking = TabelVergelijking(
            *tabelhash(bron, tabel, kolommen), *tabelhash(doel, tabel, kolommen)
        )
        rapport.tabellen[tabel] = vergelijking
        if not vergelijking.gelijk:
            problemen.append(f"inhoud van {tabel} wijkt af")
    problemen += _vergelijk_sqlite_sequence(bron, doel, rapport)
    doeltabellen = {
        rij[0]
        for rij in doel.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND lower(substr(name, 1, 7)) <> 'sqlite_'"
        )
    }
    onverwacht = doeltabellen - set(brontabellen) - set(rapport.nieuwe_tabellen)
    if onverwacht:
        problemen.append(f"onverwachte doeltabellen: {sorted(onverwacht)}")
    verdwenen = sorted(
        f"{s} {n}" for s, n in schema_objects(bron) - schema_objects(doel)
    )
    if verdwenen:
        problemen.append(f"bronobjecten verdwenen: {verdwenen}")
    return problemen


def _vergelijk_geschiedenis(
    bron: sqlite3.Connection,
    doel: sqlite3.Connection,
    kolommen: tuple[str, ...],
    rapport: HerstelRapport,
) -> list[str]:
    problemen: list[str] = []
    totaal, _ = tabelhash(bron, "definitie_geschiedenis", kolommen)
    gekoppeld_bron = tabelhash(
        bron, "definitie_geschiedenis", kolommen, f"NOT ({_VERWEESD_PREDICAAT})"
    )
    verweesd_bron = tabelhash(
        bron, "definitie_geschiedenis", kolommen, _VERWEESD_PREDICAAT
    )
    gekoppeld_doel = tabelhash(doel, "definitie_geschiedenis", kolommen)
    if _bestaat(doel, "table", BEWAARTABEL):
        verweesd_doel = tabelhash(doel, BEWAARTABEL, kolommen)
        reden_ok = doel.execute(
            f"SELECT COUNT(*) FROM {_q(BEWAARTABEL)} WHERE bewaar_reden <> ? "
            "OR bewaard_door <> ? OR bewaard_op IS NULL",
            (BEWAAR_REDEN, BEWAARD_DOOR),
        ).fetchone()[0]
        if reden_ok:
            problemen.append(
                f"{BEWAARTABEL}: {reden_ok} rij(en) zonder herleidbare reden"
            )
    else:
        verweesd_doel = (
            0,
            tabelhash(doel, "definitie_geschiedenis", kolommen, "1=0")[1],
        )
    rapport.geschiedenis_totaal = totaal
    rapport.geschiedenis_gekoppeld = gekoppeld_doel[0]
    rapport.geschiedenis_verweesd = verweesd_doel[0]
    rapport.geschiedenis_gekoppeld_hash = gekoppeld_doel[1]
    rapport.geschiedenis_verweesd_hash = verweesd_doel[1]
    rapport.tabellen["definitie_geschiedenis"] = TabelVergelijking(
        *gekoppeld_bron, *gekoppeld_doel
    )
    rapport.tabellen[BEWAARTABEL] = TabelVergelijking(*verweesd_bron, *verweesd_doel)
    if gekoppeld_bron != gekoppeld_doel:
        problemen.append("gekoppelde geschiedenis wijkt af van de bron")
    if verweesd_bron != verweesd_doel:
        problemen.append("bewaarde (verweesde) geschiedenis wijkt af van de bron")
    if gekoppeld_doel[0] + verweesd_doel[0] != totaal:
        problemen.append("geschiedenis: gekoppeld + bewaard is niet het brontotaal")
    return problemen


def _vergelijk_schema_version(
    bron: sqlite3.Connection,
    doel: sqlite3.Connection,
    kolommen: tuple[str, ...],
    rapport: HerstelRapport,
) -> list[str]:
    problemen: list[str] = []
    rapport.schema_version_bron = sorted(strict_versions(bron))
    rapport.schema_version_doel = sorted(strict_versions(doel))
    behouden = tabelhash(bron, "schema_version", kolommen)
    in_doel = tabelhash(doel, "schema_version", kolommen, f"version <= {BRONVERSIE}")
    rapport.tabellen["schema_version"] = TabelVergelijking(*behouden, *in_doel)
    if behouden != in_doel:
        problemen.append("bestaande schema_version-rijen niet exact behouden")
    nieuw = doel.execute(
        "SELECT COUNT(*) FROM schema_version WHERE version = ?", (DOELVERSIE,)
    ).fetchone()[0]
    if nieuw != 1 or rapport.schema_version_doel != [
        *rapport.schema_version_bron,
        DOELVERSIE,
    ]:
        problemen.append(
            f"schema_version doel {rapport.schema_version_doel}, verwacht "
            f"{[*rapport.schema_version_bron, DOELVERSIE]}"
        )
    return problemen


def _vergelijk_sqlite_sequence(
    bron: sqlite3.Connection, doel: sqlite3.Connection, rapport: HerstelRapport
) -> list[str]:
    def _lees(conn: sqlite3.Connection) -> dict[str, int]:
        if not _bestaat(conn, "table", "sqlite_sequence"):
            return {}
        return {
            naam: int(seq)
            for naam, seq in conn.execute("SELECT name, seq FROM sqlite_sequence")
        }

    rapport.sqlite_sequence_bron = _lees(bron)
    rapport.sqlite_sequence_doel = _lees(doel)
    problemen: list[str] = []
    for naam, seq in rapport.sqlite_sequence_bron.items():
        verwacht = seq + 1 if naam == "schema_version" else seq
        if rapport.sqlite_sequence_doel.get(naam) != verwacht:
            problemen.append(
                f"autoincrement-teller {naam}: {rapport.sqlite_sequence_doel.get(naam)}, "
                f"verwacht {verwacht}"
            )
    return problemen


# ---------------------------------------------------------------------------
# Route: read-only bron → nieuw doel
# ---------------------------------------------------------------------------
def _zelfde_pad(a: Path, b: Path) -> bool:
    """Padalias: gelijk na normalisatie (``.``, ``..``) óf na realpath."""
    return os.path.abspath(a) == os.path.abspath(b) or os.path.realpath(
        a
    ) == os.path.realpath(b)


def _valideer_paden(bron: Path, doel: Path, rapport_pad: Path | None) -> None:
    """Doel én rapport zijn nieuwe, onderling verschillende bestanden die geen
    alias van de bron of van elkaar zijn. Vóór enig werk.

    Codex-review 1544296bc: ``--rapport`` gelijk aan het doel verving de
    gepubliceerde database door JSON. Aliassen worden nu vooraf geweigerd;
    de exclusieve aanmaak in ``_publiceer_rapport`` dekt wat ná deze controle
    op het pad verschijnt.
    """
    try:
        validate_new_destination(doel)
    except BackupError as exc:
        raise SchemaContractError("herstel_doel_ongeldig", (exc.reason,)) from None
    try:
        if bron.exists() and _zelfde_pad(bron, doel):
            raise SchemaContractError(
                "herstel_doel_ongeldig", ("source_is_destination",)
            )
        if rapport_pad is None:
            return
        try:
            validate_new_destination(rapport_pad)
        except BackupError as exc:
            raise SchemaContractError(
                "herstel_rapport_ongeldig", (exc.reason,)
            ) from None
        if _zelfde_pad(rapport_pad, doel):
            raise SchemaContractError(
                "herstel_rapport_ongeldig", ("report_is_destination",)
            )
        if bron.exists() and _zelfde_pad(rapport_pad, bron):
            raise SchemaContractError("herstel_rapport_ongeldig", ("report_is_source",))
    except OSError:
        raise SchemaContractError(
            "herstel_doel_ongeldig", ("path_unreadable",)
        ) from None


def _publiceer_rapport(rapport_pad: Path, rapport: HerstelRapport) -> None:
    """Schrijf het rapport exclusief: nieuw bestand, nooit overschrijven, nooit
    een symlink volgen (``O_CREAT|O_EXCL|O_NOFOLLOW``), modus 0600.

    Codex-review 1544296bc: een symlink die ná de padvalidatie op het
    rapportpad verscheen werd gevolgd en overschreef de bron. Een pad dat
    intussen bestaat (bestand of symlink) geeft nu ``herstel_rapport_mislukt``.
    Grens: een symlink die op een *bovenliggende map* verschijnt tussen de
    controle hier en de ``open`` blijft een venster van enkele microseconden;
    de eindcomponent zelf is door de kernel gegarandeerd nieuw en geen link.
    """
    try:
        validate_new_destination(rapport_pad)
    except BackupError as exc:
        raise SchemaContractError("herstel_rapport_mislukt", (exc.reason,)) from None
    vlaggen = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    inhoud = json.dumps(rapport.als_dict(), indent=2, ensure_ascii=False) + "\n"
    try:
        fd = os.open(rapport_pad, vlaggen, 0o600)
    except OSError as exc:
        # Alleen de errno-naam: de fouttekst bevat het pad.
        raise SchemaContractError(
            "herstel_rapport_mislukt", (exc.__class__.__name__,)
        ) from None
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as bestand:
            bestand.write(inhoud)
    except OSError as exc:
        with contextlib.suppress(OSError):
            os.unlink(rapport_pad)
        raise SchemaContractError(
            "herstel_rapport_mislukt", (exc.__class__.__name__,)
        ) from None


def _eindcontrole(werk: Path, bron: Path, rapport: HerstelRapport) -> None:
    """Contract v4, integriteit, FK en de volledige inhoudsvergelijking; daarna
    het werkbestand zelfstandig maken (journal DELETE) voor publicatie."""
    conn = sqlite3.connect(str(werk), isolation_level=None)
    try:
        conn.execute("PRAGMA journal_mode=DELETE")
        rapport.contract_problemen = verify_target_contract(conn, DOELVERSIE)
        rapport.integrity_check = ",".join(
            str(rij[0]) for rij in conn.execute("PRAGMA integrity_check")
        )
        rapport.foreign_key_check_schendingen = len(
            conn.execute("PRAGMA foreign_key_check").fetchall()
        )
        rapport.doel_schema_hash = schemahash(conn)
        if rapport.contract_problemen:
            raise SchemaContractError(
                "migration_target_contract_failed", rapport.contract_problemen
            )
    finally:
        conn.close()
    bronconn = open_readonly_snapshot(bron)
    doelconn = open_readonly_snapshot(werk)
    try:
        problemen = vergelijk_bron_en_doel(bronconn, doelconn, rapport)
    finally:
        doelconn.close()
        bronconn.close()
    if problemen:
        for probleem in problemen:
            logger.error("herstel: gegevensvergelijking: %s", probleem)
        raise SchemaContractError("herstel_gegevensvergelijking_mislukt", problemen)


def herstel_naar_nieuw_doel(
    bron: Path, doel: Path, *, rapport_pad: Path | None = None
) -> HerstelRapport:
    """Maak op ``doel`` een nieuwe, volledig geldige schema-4-database uit de
    read-only schema-3-bron ``bron``. Raist ``SchemaContractError`` met een
    veilige ``reason``; dan bestaat ``doel`` niet. De bron wordt nooit
    beschreven; herhaald gebruik met een nieuw doel geeft dezelfde uitkomst.
    """
    bron, doel = Path(bron), Path(doel)
    _valideer_paden(bron, doel, rapport_pad)
    rapport = HerstelRapport(bronversie=BRONVERSIE, doelversie=DOELVERSIE)
    werkmap = Path(tempfile.mkdtemp(prefix=f"{doel.name}.herstel-", dir=doel.parent))
    werk = werkmap / "werk.db"
    try:
        try:
            create_verified_backup(bron, werk)
        except BackupError as exc:
            raise SchemaContractError(
                "herstel_kopie_geweigerd", (exc.reason,)
            ) from None
        conn = sqlite3.connect(str(werk), isolation_level=None)
        try:
            herstel_schema3(conn, rapport)
        finally:
            conn.close()
        if not v8_run_migration(werk):
            raise SchemaContractError("herstel_v8_mislukt", ("zie v8-log",))
        _eindcontrole(werk, bron, rapport)
        # Twee afzonderlijke publicaties, in deze volgorde: eerst het rapport
        # (exclusief; faalt dat, dan bestaat er ook geen doel), dan het doel.
        # Faalt het doel, dan wordt het zojuist aangemaakte rapport weer
        # verwijderd — zodat een rapport nooit succes claimt zonder doel.
        if rapport_pad is not None:
            _publiceer_rapport(rapport_pad, rapport)
        try:
            publish_staged_file(werk, doel)
        except BackupError as exc:
            if rapport_pad is not None:
                with contextlib.suppress(OSError):
                    os.unlink(rapport_pad)
            raise SchemaContractError(
                "herstel_publicatie_mislukt", (exc.reason,)
            ) from None
    except SchemaContractError as exc:
        logger.error("herstel geweigerd of mislukt: %s", exc.reason)
        raise
    finally:
        # Uitsluitend de eigen werkmap (kopie, v8-backup, journals); nooit iets
        # daarbuiten. Na publicatie is `werk` een tweede link naar het doel.
        shutil.rmtree(werkmap, ignore_errors=True)
    logger.info(
        "herstel gepubliceerd: geschiedenis gekoppeld=%d, bewaard=%d, tabellen=%d",
        rapport.geschiedenis_gekoppeld,
        rapport.geschiedenis_verweesd,
        len(rapport.tabellen),
    )
    return rapport


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="schema3_herstel",
        description=(
            "Herstel een verouderde schema-3-database naar een NIEUW doel op "
            "schemaversie 4 (DEF-751). De bron wordt alleen gelezen."
        ),
    )
    parser.add_argument("bron", type=Path, help="bestaande database (read-only)")
    parser.add_argument("doel", type=Path, help="nieuw doelbestand (mag niet bestaan)")
    parser.add_argument(
        "--rapport",
        type=Path,
        default=None,
        help="schrijf JSON-rapport (alleen metadata)",
    )
    args = parser.parse_args(argv)
    try:
        rapport = herstel_naar_nieuw_doel(
            args.bron, args.doel, rapport_pad=args.rapport
        )
    except SchemaContractError as exc:
        parser.exit(1, f"schema3_herstel: {exc}\n")
    except (sqlite3.Error, OSError) as exc:
        # Alleen de foutklasse: de tekst van zo'n fout kan een pad bevatten.
        parser.exit(1, f"schema3_herstel: afgebroken ({type(exc).__name__})\n")
    logger.info(
        "schema3_herstel: gepubliceerd; geschiedenis gekoppeld=%d, bewaard=%d",
        rapport.geschiedenis_gekoppeld,
        rapport.geschiedenis_verweesd,
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
