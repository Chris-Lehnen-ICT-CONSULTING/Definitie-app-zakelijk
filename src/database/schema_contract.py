"""Canoniek schemacontract, versieprofiel en migratiegrenzen (DEF-664).

Eén compacte module met drie verantwoordelijkheden:

1. **Contract**: ``schema.sql`` is de declaratieve, canonieke versie-3-vorm.
   ``read_contract`` leest de structuur van een database en
   ``contract_problems`` vergelijkt die met het canonieke contract:

   - tabellen en kolommen: affiniteit, NOT NULL, DEFAULT, primary key;
   - CHECK-constraints en UNIQUE-constraints (met collatie) per tabel;
   - indexen: tabel, uniek, partieel, kolommen met sortering en collatie,
     én de genormaliseerde DDL (predicaat en expressies staan alleen daar);
   - triggers en views: genormaliseerde DDL;
   - foreign keys: kolomgroep, doeltabel, ON UPDATE en ON DELETE.

   Normalisatie raakt uitsluitend tekst búiten quotes (commentaar,
   witruimte, hoofdletters, ``IF NOT EXISTS``); literals en gequote
   identifiers blijven letterlijk. Kolomvolgorde en de letterlijke
   tabel-DDL tellen niet: de DEF-672-rebuild schrijft ``definities`` met een
   andere tekst en volgorde maar dezelfde structuur. Extra gebruikersobjecten
   en -kolommen zijn toegestaan; ontbrekende canonieke objecten of afwijkende
   definities niet.
2. **Startup**: ``assert_startup_contract`` weigert fail-closed elke database
   die niet op de canonieke versie staat of het contract niet haalt. Startup
   migreert nooit; oudere versies zijn migratie-input voor de expliciete
   v5/v6/v7-routes, nooit een automatisch toegelaten startupschema.
3. **Migratiegrenzen**: ``migration_transaction`` (verificatie vóór commit,
   rollback bij elke fout inclusief een falende COMMIT),
   ``create_migration_backup`` (het DEF-663-contract; geen tweede
   backupimplementatie) en ``require_migration_preconditions``.

Fouten zijn altijd ``SchemaContractError`` met een veilige ``reason`` en
objectnamen als details; nooit paden of rijinhoud.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import datetime
from functools import cache
from pathlib import Path

from database.sqlite_backup import (
    CORE_TABLE_COLUMNS,
    BackupError,
    create_verified_backup,
)

logger = logging.getLogger(__name__)

CANONICAL_VERSION = 3
"""Schemaversie die ``schema.sql`` beschrijft en die startup vereist."""

SUPPORTED_VERSIONS: tuple[int, ...] = (0, 1, 2, 3)
"""Expliciete profielen: 0 = pre-v5 (geen schema_version), 1 = v5, 2 = v6, 3 = v7."""

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Declaratieve afleiding van de lagere profielen uit het canonieke schema:
# precies de wijzigingen van v7, v6 en v5 teruggedraaid. Zo heeft elke
# migratieroute een volledig, versiespecifiek doelcontract.
_NAAR_PROFIEL_2 = """
ALTER TABLE rag_collections ADD COLUMN document_count INTEGER DEFAULT 0;
ALTER TABLE rag_collections ADD COLUMN chunk_count INTEGER DEFAULT 0;
DELETE FROM schema_version WHERE version = 3;
"""
_NAAR_PROFIEL_1 = """
DROP INDEX idx_chunks_rechtsgebied;
DROP INDEX idx_chunks_wet_regeling;
DROP INDEX idx_chunks_bron_type;
ALTER TABLE rag_chunks DROP COLUMN bron_type;
ALTER TABLE rag_chunks DROP COLUMN metadata;
DELETE FROM schema_version WHERE version = 2;
"""
_V5_TABELLEN: tuple[str, ...] = (
    "projects",
    "ontology_relationships",
    "ontology_terms",
    "ontological_models",
    "rag_chunks",
    "rag_documents",
    "rag_collections",
    "schema_version",
)

_USER_OBJECTS_SQL = (
    "SELECT type, name, tbl_name, sql FROM sqlite_master "
    "WHERE lower(substr(name, 1, 7)) <> 'sqlite_' ORDER BY type, name"
)
_QUOTES = {"'": "'", '"': '"', "`": "`", "[": "]"}
_ASCII_FOLD = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def fold_identifier(naam: str) -> str:
    """SQLite-conforme hoofdletterongevoeligheid: alleen ASCII A–Z ↔ a–z.

    SQLite vergelijkt identifiers (en keywords) met ``sqlite3StrICmp``, dat
    uitsluitend ASCII-letters vouwt. Python ``str.lower()`` vouwt ook
    ``É``→``é`` en het Kelvinteken ``K`` (U+212A)→``k`` en trok daardoor
    verschillende SQLite-kolommen samen (Codex-review 5, rootprobe 13). Eén
    gedeelde fold voor élke identifier-, keyword- en typevergelijking;
    string-literals worden nooit gevouwen.
    """
    return naam.translate(_ASCII_FOLD)


_PUNCTUATION = set("(),;=<>!")
_IF_NOT_EXISTS = re.compile(r"if\s+not\s+exists\s+", re.IGNORECASE)


class SchemaContractError(RuntimeError):
    """Schema geweigerd of migratiegrens geschonden; ``reason`` is veilig."""

    def __init__(self, reason: str, details: Iterable[str] = ()) -> None:
        self.reason = reason
        self.details: tuple[str, ...] = tuple(details)
        tekst = reason if not self.details else f"{reason}: {'; '.join(self.details)}"
        super().__init__(tekst)


@dataclass(frozen=True)
class ContractProblem:
    kind: str
    """``ontbreekt`` (object niet aanwezig) of ``afwijkend`` (verkeerde definitie)."""

    detail: str

    def __str__(self) -> str:
        return f"{self.kind}: {self.detail}"


Column = tuple[str, int, str, int, int, int]
"""(affiniteit, notnull, genormaliseerde default, primary-key-positie,
rowid-alias, autoincrement).

De laatste twee leggen de echte sleutelsemantiek vast (Codex-herreview P1):
alleen ``INTEGER PRIMARY KEY`` (zonder ``DESC``) is een rowid-alias die zelf
ids uitgeeft; ``BIGINT PRIMARY KEY`` of ``INT PRIMARY KEY`` heeft dezelfde
affiniteit en pk-positie maar geeft bij een gewone INSERT ``id = NULL``.
``AUTOINCREMENT`` bepaalt of ids ooit hergebruikt kunnen worden."""

IndexKey = tuple[tuple[str | None, int, str], ...]
"""((kolom of None bij expressie, desc, collatie), ...)."""

ForeignKey = tuple[str, tuple[tuple[str, str], ...], str, str]
"""(doeltabel, ((kolom, doelkolom), ...), on_update, on_delete)."""


@dataclass(frozen=True)
class SchemaContract:
    """Structuur van een database, onafhankelijk van tabel-DDL-tekst en volgorde."""

    columns: dict[str, dict[str, Column]]
    checks: dict[str, frozenset[str]]
    """tabel -> genormaliseerde CHECK-expressies."""

    unique_constraints: dict[str, frozenset[tuple[tuple[str, str], ...]]]
    """tabel -> {((kolom, collatie), ...)} van UNIQUE-constraints (autoindexen)."""

    indexes: dict[str, tuple[str, int, int, IndexKey, str]]
    """index -> (tabel, uniek, partieel, sleutel, genormaliseerde DDL)."""

    triggers: dict[str, tuple[str, str]]
    """trigger -> (tabel, genormaliseerde DDL)."""

    views: dict[str, str]
    """view -> genormaliseerde DDL."""

    foreign_keys: dict[str, frozenset[ForeignKey]]


# ---------------------------------------------------------------------------
# Normalisatie (alleen buiten quotes)
# ---------------------------------------------------------------------------
def normalize_sql(sql: str | None) -> str:
    """Vergelijkbare vorm van SQL: letterlijk binnen quotes, canoniek erbuiten.

    Buiten quotes: ``--``- en ``/* */``-commentaar weg, witruimte tot één
    spatie, geen spaties rond leestekens, kleine letters, ``if not exists``
    weg. Binnen ``'…'``, ``"…"``, ```…``` en ``[…]`` blijft alles staan
    (inclusief hoofdletters, spaties en ``--``), want dat is inhoud.
    """
    tekst = sql or ""
    uit: list[str] = []
    i, n = 0, len(tekst)
    while i < n:
        teken = tekst[i]
        if teken in _QUOTES:
            sluiter = _QUOTES[teken]
            j = i + 1
            while j < n:
                if tekst[j] == sluiter:
                    if sluiter != "]" and tekst[j + 1 : j + 2] == sluiter:
                        j += 2  # verdubbelde quote binnen de literal
                        continue
                    break
                j += 1
            uit.append(tekst[i : j + 1])
            i = j + 1
            continue
        if tekst.startswith("--", i) or tekst.startswith("/*", i):
            # Commentaar is in SQLite een tokenscheiding (Codex-review 4):
            # `ON/**/CONFLICT` is `on conflict`, niet `onconflict`. Het
            # commentaar zelf verdwijnt, de scheiding blijft als één spatie,
            # met dezelfde samenvoegregels als gewone witruimte.
            if tekst.startswith("--", i):
                einde = tekst.find("\n", i)
                i = n if einde < 0 else einde
            else:
                einde = tekst.find("*/", i + 2)
                i = n if einde < 0 else einde + 2
            if uit and uit[-1] != " " and uit[-1] not in _PUNCTUATION:
                uit.append(" ")
            continue
        if teken in "iI" and (uit == [] or uit[-1] == " "):
            # `IF NOT EXISTS` alleen als los sleutelwoord buiten quotes; nooit
            # via een globale replace, die zou literals raken.
            gevonden = _IF_NOT_EXISTS.match(tekst, i)
            if gevonden:
                i = gevonden.end()
                continue
        if teken.isspace():
            # Geen spatie na een leesteken (ook niet als er een commentaar
            # tussen stond): spaties rond leestekens tellen niet.
            if uit and uit[-1] != " " and uit[-1] not in _PUNCTUATION:
                uit.append(" ")
            i += 1
            continue
        if teken in _PUNCTUATION:
            if uit and uit[-1] == " ":
                uit.pop()
            uit.append(teken)
            i += 1
            # witruimte ná een leesteken wordt overgeslagen
            while i < n and tekst[i].isspace():
                i += 1
            continue
        # Alleen ASCII vouwen: een ongequote niet-ASCII identifier blijft
        # zichzelf, zoals in SQLite.
        uit.append(fold_identifier(teken))
        i += 1
    return "".join(uit).strip()


def _kolomdefinities(table_sql: str | None) -> list[str]:
    """De top-level onderdelen (kolommen en tabelconstraints) van een CREATE TABLE."""
    genormaliseerd = normalize_sql(table_sql)
    begin, einde = genormaliseerd.find("("), genormaliseerd.rfind(")")
    if begin < 0 or einde <= begin:
        return []
    return _split_top_level(genormaliseerd[begin + 1 : einde])


_CONSTRAINT_STARTS = frozenset({"constraint", "primary", "foreign", "check", "unique"})


def column_definition(kolom: str, delen: list[str]) -> str:
    """De kolomdefinitie (genormaliseerd top-level deel) van ``kolom``.

    Het eerste identifier-token van een deel bepaalt de kolomnaam: een kaal
    woord, of een gequote naam (``"…"``, ```…```, ``[…]`` én ``'…'`` — SQLite
    accepteert een enkel gequote naam in deze positie). Vergelijking is
    hoofdletterongevoelig, zoals SQLite-identifiers. Tabelconstraints
    (``constraint``, ``primary key(``, ``foreign key(``, ``check(``,
    ``unique(``) zijn geen kolommen. Eén gedeelde herkenning voor contract én
    rebuild (Codex-review 4), geen prefixraden per quotevorm.
    """
    doel = fold_identifier(kolom)
    for deel in delen:
        segmenten = list(lex_segments(deel))
        if not segmenten:
            continue
        soort, tekst = segmenten[0]
        if soort == "plain":
            if not tekst.strip():
                if len(segmenten) < 2:
                    continue
                soort, tekst = segmenten[1]
            else:
                woord = re.match(r"\s*([^\W\d]\w*)", tekst)
                if not woord or fold_identifier(woord.group(1)) in _CONSTRAINT_STARTS:
                    continue
                if fold_identifier(woord.group(1)) == doel:
                    return deel
                continue
        if soort in ("identifier", "string") and fold_identifier(tekst) == doel:
            return deel
    return ""


def _eigen_definitie(kolom: str, delen: list[str]) -> str:
    return column_definition(kolom, delen)


def _zonder_constraintnaam(deel: str) -> str:
    """``constraint <naam> <rest>`` → ``<rest>``; anders ongewijzigd."""
    if not deel.startswith("constraint "):
        return deel
    segmenten = list(lex_segments(deel[len("constraint ") :]))
    if not segmenten:
        return deel
    soort, tekst = segmenten[0]
    if soort == "plain":
        return tekst.split(" ", 1)[1] if " " in tekst.strip() else ""
    rest = "".join(t if s == "plain" else f'"{t}"' for s, t in segmenten[1:])
    return rest.strip()


def _sleutelsemantiek(
    kolom: str, declared: str | None, pk: int, pk_aantal: int, delen: list[str]
) -> tuple[int, int]:
    """(rowid_alias, autoincrement) volgens de SQLite-grammatica.

    Rowid-alias: exact het type ``INTEGER``, enige primary key, en niet
    ``PRIMARY KEY DESC`` (inline of als tabelconstraint). AUTOINCREMENT is
    alleen het sleutelwoord dat in de grammatica direct op
    ``PRIMARY KEY [ASC|DESC] [ON CONFLICT x]`` volgt (Codex-review 3): het
    woord in een gequote constraintnaam, een literal of commentaar is geen
    sleutelwoord. Alle patronen lopen over ``strip_quoted``-tekst.
    """
    if not pk or pk_aantal != 1:
        return 0, 0
    kaal = strip_quoted(_eigen_definitie(kolom, delen))
    autoincrement = int(
        re.search(
            r"primary key(\s+(asc|desc))?(\s+on conflict\s+\w+)?\s+autoincrement\b",
            kaal,
        )
        is not None
    )
    if fold_identifier((declared or "").strip()) != "integer":
        return 0, autoincrement
    if re.search(r"primary key\s+desc\b", kaal):
        return 0, autoincrement
    naam = fold_identifier(kolom)
    for deel in delen:
        deel = _zonder_constraintnaam(deel)
        if deel.startswith("primary key(") and re.search(
            rf"\(\s*{re.escape(naam)}\s+desc\s*\)",
            fold_identifier(identifier_text(deel)),
        ):
            return 0, autoincrement
    return 1, autoincrement


def _split_top_level(tekst: str) -> list[str]:
    """Splits op komma's die niet binnen haakjes of quotes staan."""
    delen: list[str] = []
    diepte = 0
    quote: str | None = None
    huidig: list[str] = []
    for teken in tekst:
        if quote:
            huidig.append(teken)
            if teken == quote:
                quote = None
            continue
        if teken in _QUOTES:
            quote = _QUOTES[teken]
        elif teken == "(":
            diepte += 1
        elif teken == ")":
            diepte -= 1
        elif teken == "," and diepte == 0:
            delen.append("".join(huidig).strip())
            huidig = []
            continue
        huidig.append(teken)
    rest = "".join(huidig).strip()
    if rest:
        delen.append(rest)
    return delen


def lex_segments(tekst: str) -> Iterator[tuple[str, str]]:
    """Lexeer SQL in segmenten ``(soort, tekst)``: ``plain``, ``string``
    (``'…'``) of ``identifier`` (``"…"``, ```…```, ``[…]``; tekst zonder de
    quotes). Dezelfde compacte lexing als ``normalize_sql``; commentaar is in
    genormaliseerde tekst al weg."""
    i, n = 0, len(tekst)
    plain: list[str] = []
    while i < n:
        teken = tekst[i]
        if teken in _QUOTES:
            if plain:
                yield "plain", "".join(plain)
                plain = []
            sluiter = _QUOTES[teken]
            j = i + 1
            while j < n:
                if tekst[j] == sluiter:
                    if sluiter != "]" and tekst[j + 1 : j + 2] == sluiter:
                        j += 2
                        continue
                    break
                j += 1
            soort = "string" if teken == "'" else "identifier"
            yield soort, tekst[i + 1 : j]
            i = j + 1
            continue
        plain.append(teken)
        i += 1
    if plain:
        yield "plain", "".join(plain)


def strip_quoted(tekst: str) -> str:
    """Alleen de tekst buiten élke quote: sleutelwoordherkenning mag nooit op
    een literal of een gequote naam afgaan."""
    return "".join(t for soort, t in lex_segments(tekst) if soort == "plain")


def identifier_text(tekst: str) -> str:
    """Tekst buiten string-literals, met gequote identifiers als kale namen.

    Voor verwijzingsdetectie: ``"kolom"`` is een identifier, ``'kolom'`` is
    een waarde en telt niet.
    """
    return " ".join(
        t if soort == "plain" else f" {t} "
        for soort, t in lex_segments(tekst)
        if soort != "string"
    )


def _scan_outside_quotes(tekst: str) -> Iterator[tuple[int, str]]:
    """Geef (positie, teken) van elk teken dat búiten quotes staat.

    Dezelfde compacte lexing als ``normalize_sql``: ``'…'``, ``"…"``,
    ```…``` en ``[…]`` worden als geheel overgeslagen, verdubbelde quotes
    binnen een literal meegenomen.
    """
    i, n = 0, len(tekst)
    while i < n:
        teken = tekst[i]
        if teken in _QUOTES:
            sluiter = _QUOTES[teken]
            j = i + 1
            while j < n:
                if tekst[j] == sluiter:
                    if sluiter != "]" and tekst[j + 1 : j + 2] == sluiter:
                        j += 2
                        continue
                    break
                j += 1
            i = j + 1
            continue
        yield i, teken
        i += 1


def check_expressions(table_sql: str | None) -> frozenset[str]:
    """Alle CHECK(...)-expressies uit een tabeldefinitie, genormaliseerd.

    Rootprobe (probe-check-literal): een ``find("check(")`` zonder
    quotecontext telde een DEFAULT-literal met die tekst als constraint. De
    scan loopt daarom uitsluitend over tekens buiten quotes; een ``check(``
    binnen een literal (of, vóór normalisatie, in commentaar) bestaat voor
    deze functie niet. De haakjesbalans binnen de expressie is eveneens
    quote-bewust.
    """
    genormaliseerd = normalize_sql(table_sql)
    checks: set[str] = set()
    diepte = 0
    start: int | None = None
    sleutel = "check("
    for positie, teken in _scan_outside_quotes(genormaliseerd):
        if start is None:
            if genormaliseerd.startswith(sleutel, positie) and (
                positie == 0 or not genormaliseerd[positie - 1].isalnum()
            ):
                start = positie + len(sleutel)
                diepte = 1
            continue
        if positie < start:
            continue
        if teken == "(":
            diepte += 1
        elif teken == ")":
            diepte -= 1
            if diepte == 0:
                checks.add(genormaliseerd[start:positie])
                start = None
    return frozenset(checks)


# ---------------------------------------------------------------------------
# Lezen
# ---------------------------------------------------------------------------
def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _affinity(declared: str | None) -> str:
    """Kolomaffiniteit volgens de SQLite-regels (datatype3, §3.1).

    De keywordvergelijking gebruikt dezelfde ASCII-fold als identifiers:
    ``sqlite3AffinityType`` vouwt uitsluitend ASCII. Python ``str.upper()``
    trok niet-ASCII de keywords in — het geldige REAL-type ``FLOATING POıNT``
    (dotloze ``ı``, U+0131) werd ``FLOATING POINT`` en dus INTEGER, en de
    ligatuur ``ﬂ`` (U+FB02) maakte van ``ﬂOAT`` ten onrechte ``FLOAT``
    (Codex-review 6, rootprobe ``probe-unicode-affinity``). Die classificatie
    stuurt de startupdrift-controle én de rebuildgrens, dus een fout hier
    verandert opgeslagen waarden. Regelvolgorde blijft die van SQLite.
    """
    tekst = fold_identifier(declared or "")
    if "int" in tekst:
        return "INTEGER"
    if any(k in tekst for k in ("char", "clob", "text")):
        return "TEXT"
    if "blob" in tekst or not tekst:
        return "BLOB"
    if any(k in tekst for k in ("real", "floa", "doub")):
        return "REAL"
    return "NUMERIC"


def column_affinity(declared: str | None) -> str:
    """Publieke naam van ``_affinity`` voor hergebruik in de migratiegrens."""
    return _affinity(declared)


def key_semantics(conn: sqlite3.Connection, table: str) -> dict[str, tuple[int, int]]:
    """(rowid_alias, autoincrement) per kolom van ``table``, uit dezelfde
    grammatica als het startupcontract — voor de rebuildgrens (rootprobe
    rebuild-primary-key-values-v2): een `INT PRIMARY KEY`-bron kent een
    NULL-id, een rowid-alias niet."""
    rij = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    delen = _kolomdefinities(rij[0] if rij else "")
    kolominfo = conn.execute(f"PRAGMA table_info({_quote(table)})").fetchall()
    pk_aantal = sum(1 for k in kolominfo if k[5])
    return {
        fold_identifier(kolom): _sleutelsemantiek(
            kolom, declared, int(pk), pk_aantal, delen
        )
        for _cid, kolom, declared, _notnull, _dflt, pk in kolominfo
    }


def folded_columns(conn: sqlite3.Connection, table: str) -> dict[str, str]:
    """``gevouwen naam -> werkelijke naam`` van alle kolommen; fail-closed bij
    een botsing (twee kolommen met dezelfde SQLite-gelijke naam kan SQLite
    zelf niet maken, dus een botsing betekent een verkeerde transformatie)."""
    mapping: dict[str, str] = {}
    for rij in conn.execute(f"PRAGMA table_info({_quote(table)})"):
        sleutel = fold_identifier(rij[1])
        if sleutel in mapping:
            raise SchemaContractError(
                "identifier_ambiguous", (f"{table}: {mapping[sleutel]} / {rij[1]}",)
            )
        mapping[sleutel] = rij[1]
    return mapping


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def has_user_objects(conn: sqlite3.Connection) -> bool:
    """True als de database al één of meer niet-interne schemaobjecten heeft."""
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE lower(substr(name, 1, 7)) <> 'sqlite_' LIMIT 1"
    ).fetchone()
    return row is not None


def schema_version(conn: sqlite3.Connection) -> int | None:
    """Hoogste ``schema_version.version``; None zonder tabel of zonder rijen.

    Strikt: elke niet-NULL waarde moet een echt geheel getal zijn. ``3.5``
    of ``'unexpected'`` is geen versie maar een beschadigde markering en
    geeft ``schema_version_invalid`` in plaats van een stille afronding of
    een rauwe ``ValueError``.
    """
    if not _table_exists(conn, "schema_version"):
        return None
    waarden = strict_versions(conn)
    return max(waarden) if waarden else None


def strict_versions(conn: sqlite3.Connection) -> set[int]:
    """Alle ruwe ``schema_version.version``-waarden, strikt als ``int``.

    Gedeeld door startup, fresh init en de migratieverificaties (Codex-review
    3): nooit converteren vóór de typecontrole, zodat ``2.5`` niet tot 2 wordt
    en tekst geen ``ValueError`` lekt maar ``schema_version_invalid`` geeft.
    """
    waarden = [
        rij[0]
        for rij in conn.execute("SELECT version FROM schema_version")
        if rij[0] is not None
    ]
    ongeldig = [w for w in waarden if isinstance(w, bool) or not isinstance(w, int)]
    if ongeldig:
        raise SchemaContractError(
            "schema_version_invalid",
            (f"ongeldige versiewaarde van type {type(w).__name__}" for w in ongeldig),
        )
    return set(waarden)


def split_top_level(tekst: str) -> list[str]:
    """Splits op komma's die niet binnen haakjes of quotes staan."""
    return _split_top_level(tekst)


def _index_key(conn: sqlite3.Connection, name: str) -> IndexKey:
    return tuple(
        (
            fold_identifier(kolom) if kolom is not None else None,
            int(desc),
            str(collatie).upper(),
        )
        for _seqno, _cid, kolom, desc, collatie, is_sleutel in conn.execute(
            f"PRAGMA index_xinfo({_quote(name)})"
        )
        if is_sleutel
    )


def _read_indexes(
    conn: sqlite3.Connection, table: str, index_sql: dict[str, str]
) -> tuple[
    frozenset[tuple[tuple[str, str], ...]],
    dict[str, tuple[str, int, int, IndexKey, str]],
]:
    uniek: set[tuple[tuple[str, str], ...]] = set()
    indexen: dict[str, tuple[str, int, int, IndexKey, str]] = {}
    for _seq, naam, is_uniek, oorsprong, partieel in conn.execute(
        f"PRAGMA index_list({_quote(table)})"
    ):
        sleutel = _index_key(conn, naam)
        if oorsprong == "u":
            uniek.add(tuple((kolom or "", coll) for kolom, _desc, coll in sleutel))
        elif oorsprong == "c":
            indexen[naam] = (
                table,
                int(is_uniek),
                int(partieel),
                sleutel,
                index_sql.get(naam, ""),
            )
    return frozenset(uniek), indexen


def _read_foreign_keys(conn: sqlite3.Connection, table: str) -> frozenset[ForeignKey]:
    groepen: dict[int, tuple[str, list[tuple[str, str]], str, str]] = {}
    for fk_id, _seq, doel, van, naar, on_update, on_delete, _match in conn.execute(
        f"PRAGMA foreign_key_list({_quote(table)})"
    ):
        groep = groepen.setdefault(
            fk_id, (doel, [], str(on_update).upper(), str(on_delete).upper())
        )
        groep[1].append((fold_identifier(van), fold_identifier(naar or "")))
    return frozenset(
        (doel, tuple(kolommen), on_update, on_delete)
        for doel, kolommen, on_update, on_delete in groepen.values()
    )


def read_contract(conn: sqlite3.Connection) -> SchemaContract:
    """Lees de structuur van alle niet-interne objecten uit ``conn``."""
    objecten = conn.execute(_USER_OBJECTS_SQL).fetchall()
    index_sql = {
        naam: normalize_sql(sql)
        for soort, naam, _t, sql in objecten
        if soort == "index"
    }
    columns: dict[str, dict[str, Column]] = {}
    checks: dict[str, frozenset[str]] = {}
    unique_constraints: dict[str, frozenset[tuple[tuple[str, str], ...]]] = {}
    indexes: dict[str, tuple[str, int, int, IndexKey, str]] = {}
    foreign_keys: dict[str, frozenset[ForeignKey]] = {}
    triggers: dict[str, tuple[str, str]] = {}
    views: dict[str, str] = {}

    for soort, naam, tabel, sql in objecten:
        if soort == "table":
            kolominfo = conn.execute(f"PRAGMA table_info({_quote(naam)})").fetchall()
            pk_aantal = sum(1 for rij in kolominfo if rij[5])
            delen = _kolomdefinities(sql)
            # Kolomnamen zijn in SQLite alleen ASCII-hoofdletterongevoelig:
            # sleutels via fold_identifier, zodat "ID" en id dezelfde kolom
            # zijn maar "Éxtra" en "éxtra" niet.
            folded_columns(conn, naam)  # fail-closed bij een botsing
            columns[naam] = {
                fold_identifier(kolom): (
                    _affinity(declared),
                    int(notnull),
                    normalize_sql(dflt),
                    int(pk),
                    *_sleutelsemantiek(kolom, declared, int(pk), pk_aantal, delen),
                )
                for _cid, kolom, declared, notnull, dflt, pk in kolominfo
            }
            checks[naam] = check_expressions(sql)
            unique_constraints[naam], eigen = _read_indexes(conn, naam, index_sql)
            indexes.update(eigen)
            foreign_keys[naam] = _read_foreign_keys(conn, naam)
        elif soort == "trigger":
            triggers[naam] = (tabel, normalize_sql(sql))
        elif soort == "view":
            views[naam] = normalize_sql(sql)

    return SchemaContract(
        columns, checks, unique_constraints, indexes, triggers, views, foreign_keys
    )


@cache
def _target_contract_for(schema_path: Path, version: int) -> SchemaContract:
    try:
        schema_sql = schema_path.read_text(encoding="utf-8")
    except OSError:
        raise SchemaContractError(
            "canonical_schema_unreadable", ("schema.sql niet leesbaar",)
        ) from None
    conn = sqlite3.connect(":memory:")
    try:
        try:
            conn.executescript(schema_sql)
        except sqlite3.Error as exc:
            raise SchemaContractError(
                "canonical_schema_unreadable", (type(exc).__name__,)
            ) from exc
        if version < 3:
            conn.executescript(_NAAR_PROFIEL_2)
        if version < 2:
            conn.executescript(_NAAR_PROFIEL_1)
        if version < 1:
            for tabel in _V5_TABELLEN:
                conn.execute(f"DROP TABLE {tabel}")
        return read_contract(conn)
    finally:
        conn.close()


def target_contract(version: int) -> SchemaContract:
    """Het volledige doelcontract van een ondersteund profiel (gecachet)."""
    if version not in SUPPORTED_VERSIONS:
        raise SchemaContractError(
            "schema_version_unsupported",
            (f"geen doelcontract voor schemaversie {version}",),
        )
    return _target_contract_for(SCHEMA_PATH, version)


def canonical_contract() -> SchemaContract:
    """Het contract dat ``schema.sql`` beschrijft (in-memory opgebouwd, gecachet)."""
    return target_contract(CANONICAL_VERSION)


def schema_objects(conn: sqlite3.Connection) -> set[tuple[str, str]]:
    """Alle niet-interne schemaobjecten als (type, naam) — voor bronbehoud."""
    return {
        (soort, naam)
        for soort, naam, _tbl, _sql in conn.execute(_USER_OBJECTS_SQL).fetchall()
    }


def lost_objects(
    before: set[tuple[str, str]],
    after: set[tuple[str, str]],
    allowed: Iterable[tuple[str, str]] = (),
) -> list[str]:
    """Bronobjecten die na een migratie ontbreken, behalve de bewust verwijderde.

    Bronbehoud staat los van het doelcontract: dat laat extra objecten toe en
    ziet het verlies van een gebruikersobject dus niet.
    """
    return sorted(f"{soort} {naam}" for soort, naam in before - after - set(allowed))


def verify_target_contract(
    conn: sqlite3.Connection, version: int, *, integrity: bool = True
) -> list[str]:
    """Volledige doelcontrole van een migratie, binnen haar transactie.

    Toetst het complete versiespecifieke contract (niet alleen de eigen
    mutaties van de route), de volledige versiemarkerverzameling en, met
    ``integrity``, ``integrity_check`` en ``foreign_key_check``. Leeg =
    conform. Bronbehoud (bestaande objecten en rijen) blijft een
    afzonderlijke controle van de route zelf (``lost_objects``).
    """
    problemen = [
        str(p) for p in contract_problems(read_contract(conn), target_contract(version))
    ]
    if version > 0:
        aanwezig = (
            strict_versions(conn) if _table_exists(conn, "schema_version") else set()
        )
        verwacht = set(range(1, version + 1))
        if aanwezig != verwacht:
            problemen.append(
                f"afwijkend: schema_version {sorted(aanwezig)}, verwacht {sorted(verwacht)}"
            )
    elif _table_exists(conn, "schema_version"):
        problemen.append("afwijkend: schema_version aanwezig in pre-v5-profiel")
    if not integrity:
        return problemen
    integriteit = [rij[0] for rij in conn.execute("PRAGMA integrity_check")]
    if integriteit != ["ok"]:
        problemen.append("afwijkend: integrity_check niet ok")
    if conn.execute("PRAGMA foreign_key_check").fetchall():
        problemen.append("afwijkend: foreign_key_check meldt schendingen")
    return problemen


# ---------------------------------------------------------------------------
# Vergelijken
# ---------------------------------------------------------------------------
def _column_problems(
    observed: SchemaContract, canonical: SchemaContract
) -> Iterator[ContractProblem]:
    for tabel, kolommen in canonical.columns.items():
        aanwezig = observed.columns.get(tabel)
        if aanwezig is None:
            yield ContractProblem("ontbreekt", f"tabel {tabel}")
            continue
        for kolom, verwacht in kolommen.items():
            gevonden = aanwezig.get(kolom)
            if gevonden is None:
                yield ContractProblem("ontbreekt", f"kolom {tabel}.{kolom}")
            elif gevonden != verwacht:
                yield ContractProblem(
                    "afwijkend",
                    f"kolom {tabel}.{kolom} (affiniteit/notnull/default/pk/"
                    f"rowid-alias/autoincrement {gevonden}; verwacht {verwacht})",
                )
        for check in canonical.checks.get(tabel, frozenset()):
            if check not in observed.checks.get(tabel, frozenset()):
                yield ContractProblem("afwijkend", f"check-constraint {tabel}: {check}")
        for constraint in canonical.unique_constraints.get(tabel, frozenset()):
            if constraint not in observed.unique_constraints.get(tabel, frozenset()):
                yield ContractProblem(
                    "afwijkend", f"unique-constraint {tabel}{constraint}"
                )
        for fk in canonical.foreign_keys.get(tabel, frozenset()):
            if fk not in observed.foreign_keys.get(tabel, frozenset()):
                kolommen_tekst = ", ".join(f"{van}->{naar}" for van, naar in fk[1])
                yield ContractProblem(
                    "afwijkend",
                    f"foreign key {tabel}({kolommen_tekst}) -> {fk[0]} "
                    f"ON UPDATE {fk[2]} ON DELETE {fk[3]}",
                )


def _named_problems(
    soort: str, observed: dict, canonical: dict
) -> Iterator[ContractProblem]:
    for naam, verwacht in canonical.items():
        gevonden = observed.get(naam)
        if gevonden is None:
            yield ContractProblem("ontbreekt", f"{soort} {naam}")
        elif gevonden != verwacht:
            yield ContractProblem("afwijkend", f"{soort} {naam}")


def contract_problems(
    observed: SchemaContract, canonical: SchemaContract
) -> list[ContractProblem]:
    """Alle afwijkingen van ``observed`` t.o.v. ``canonical``; leeg = conform."""
    return [
        *_column_problems(observed, canonical),
        *_named_problems("index", observed.indexes, canonical.indexes),
        *_named_problems("trigger", observed.triggers, canonical.triggers),
        *_named_problems("view", observed.views, canonical.views),
    ]


def problems_to_error(problemen: list[ContractProblem]) -> SchemaContractError:
    reason = (
        "schema_incomplete"
        if any(p.kind == "ontbreekt" for p in problemen)
        else "schema_drift"
    )
    return SchemaContractError(reason, (str(p) for p in problemen))


def assert_startup_contract(conn: sqlite3.Connection) -> None:
    """Weiger fail-closed elke bestaande database die niet canoniek versie 3 is.

    Volgorde: een database zonder de kerntabellen is een onbekend deelschema
    (``schema_incomplete``), geen "oudere versie"; pas met de kern aanwezig is
    een lagere of ontbrekende versie een ondersteunde migratie-input
    (``schema_version_outdated``).
    """
    versie = schema_version(conn)
    if versie is None or versie < CANONICAL_VERSION:
        ontbrekende_kern = [
            tabel for tabel in CORE_TABLE_COLUMNS if not _table_exists(conn, tabel)
        ]
        if ontbrekende_kern:
            raise SchemaContractError(
                "schema_incomplete",
                (f"ontbreekt: tabel {tabel}" for tabel in ontbrekende_kern),
            )
        gevonden = "geen" if versie is None else str(versie)
        raise SchemaContractError(
            "schema_version_outdated",
            (
                (
                    f"gevonden schemaversie {gevonden}, vereist {CANONICAL_VERSION}; "
                    "startup migreert niet, draai de migraties v5/v6/v7 expliciet"
                ),
            ),
        )
    if versie > CANONICAL_VERSION:
        raise SchemaContractError(
            "schema_version_unsupported",
            (f"gevonden schemaversie {versie}, ondersteund t/m {CANONICAL_VERSION}",),
        )
    problemen = contract_problems(read_contract(conn), canonical_contract())
    if problemen:
        raise problems_to_error(problemen)
    # Niet alleen het maximum: de volledige markerverzameling {1, 2, 3}.
    afwijkende_markers = verify_target_contract(
        conn, CANONICAL_VERSION, integrity=False
    )
    if afwijkende_markers:
        raise SchemaContractError("schema_drift", afwijkende_markers)


# ---------------------------------------------------------------------------
# Migratiegrenzen
# ---------------------------------------------------------------------------
def _commit(conn: sqlite3.Connection) -> None:
    """Commitpunt; apart zodat een falende COMMIT functioneel te injecteren is."""
    conn.execute("COMMIT")


def rollback_quietly(conn: sqlite3.Connection) -> None:
    """Rol een nog open transactie terug; een rollbackfout maskeert nooit de oorzaak."""
    if not conn.in_transaction:
        return
    try:
        conn.execute("ROLLBACK")
    except sqlite3.Error:
        logger.warning("ROLLBACK na fout mislukt", exc_info=True)


@contextmanager
def migration_transaction(
    conn: sqlite3.Connection, savepoint: str = "migratiestap"
) -> Iterator[sqlite3.Connection]:
    """``BEGIN IMMEDIATE`` … ``COMMIT``; bij élke fout (ook in COMMIT) ``ROLLBACK``.

    De aanroeper verifieert binnen de scope en raist bij een afwijking, zodat
    versiemarker, DDL en verificatie samen committen of samen terugrollen.
    Vereist een connectie in autocommit-modus (``isolation_level=None``).

    SQLite nest geen ``BEGIN``; binnen een al open transactie wordt de scope
    een ``SAVEPOINT``: een fout rolt alleen die stap terug en loopt door naar
    de buitenste grens, die dan als geheel terugrolt. Zo blijven de
    standalone rebuildhelpers bruikbaar én kan een hele logische migratie één
    transactie zijn.
    """
    if conn.in_transaction:
        conn.execute(f"SAVEPOINT {savepoint}")
        try:
            yield conn
            conn.execute(f"RELEASE {savepoint}")
        except BaseException:
            with suppress(sqlite3.Error):
                conn.execute(f"ROLLBACK TO {savepoint}")
                conn.execute(f"RELEASE {savepoint}")
            raise
        return
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
        _commit(conn)
    except BaseException:
        rollback_quietly(conn)
        raise


def create_migration_backup(db_path: Path, prefix: str, now: datetime) -> Path:
    """Geverifieerde WAL-veilige backup vóór een migratie (DEF-663-contract).

    Bestandsnaam ``<prefix>_<YYYYmmdd_HHMMSS_ffffff>.db`` in ``<db>/../backups``.
    Raist FileNotFoundError zonder database en ``SchemaContractError``
    (``backup_refused``, detail = veilige helperreden) als de helper weigert;
    dan is er niets geschreven en blijft er geen lege backupmap achter.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    backup_dir = db_path.parent / "backups"
    nieuw_aangemaakt = not backup_dir.exists()
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Bijv. PermissionError: geen rauwe fout, geen migratie zonder backup.
        raise SchemaContractError(
            "backup_refused", ("backup_dir_unwritable",)
        ) from None
    backup_path = backup_dir / f"{prefix}_{now.strftime('%Y%m%d_%H%M%S_%f')}.db"
    try:
        create_verified_backup(db_path, backup_path)
    except BackupError as exc:
        if nieuw_aangemaakt:
            # Geen artefact achterlaten van een geweigerde backup; alleen de
            # eigen, nog lege map.
            with suppress(OSError):
                backup_dir.rmdir()
        raise SchemaContractError("backup_refused", (exc.reason,)) from None
    return backup_path


def require_migration_preconditions(
    conn: sqlite3.Connection,
    *,
    previous_version: int | None,
    tables: Iterable[str],
) -> None:
    """Weiger vóór enige schrijfactie als de bronversie of doeltabel ontbreekt."""
    details: list[str] = []
    if previous_version is not None:
        aanwezig = _table_exists(conn, "schema_version") and (
            conn.execute(
                "SELECT 1 FROM schema_version WHERE version = ?", (previous_version,)
            ).fetchone()
            is not None
        )
        if not aanwezig:
            details.append(f"schema_version {previous_version} ontbreekt")
    details.extend(
        f"tabel {tabel} ontbreekt" for tabel in tables if not _table_exists(conn, tabel)
    )
    if details:
        raise SchemaContractError("migration_precondition_failed", details)
