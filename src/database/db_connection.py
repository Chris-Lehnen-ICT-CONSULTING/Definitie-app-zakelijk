"""Database connection management voor de DefinitieAgent.

Beheert SQLite lifecycle, schema-initialisatie, en pragmas.
Wordt als connection provider doorgegeven aan sub-repositories (compositie).
"""

import logging
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from pathlib import Path

from database import schema_contract
from database.schema_contract import (
    CANONICAL_VERSION,
    SchemaContractError,
    assert_startup_contract,
    has_user_objects,
    rollback_quietly,
    verify_target_contract,
)

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class _ThreadConnectionState:
    """Bezit en sluit de SQLite-connectie van één thread."""

    def __init__(self) -> None:
        self.connection: sqlite3.Connection | None = None

    def close(self) -> None:
        connection = self.connection
        self.connection = None
        if connection is not None:
            connection.close()

    def __del__(self) -> None:
        with suppress(sqlite3.Error):
            self.close()


class DatabaseConnection:
    """Connection provider — beheert SQLite lifecycle, schema-init, pragmas.

    Thread-local connection: PRAGMAs worden eenmaal gezet per thread.
    De provider geeft iedere thread uitsluitend zijn eigen connectie terug.
    """

    def __init__(self, db_path: str = "data/definities.db"):
        self.db_path = db_path
        self._thread_local = threading.local()

    def get_connection(self, timeout: float = 30.0) -> sqlite3.Connection:
        """Retourneer de connectie van de huidige thread."""
        state: _ThreadConnectionState | None = getattr(
            self._thread_local, "state", None
        )
        if state is None:
            state = _ThreadConnectionState()
            self._thread_local.state = state

        conn = state.connection
        if conn is not None:
            try:
                conn.execute("SELECT 1")
                return conn
            except sqlite3.Error:
                state.connection = None

        conn = sqlite3.connect(
            self.db_path,
            timeout=timeout,
            isolation_level=None,
            # Connecties worden nooit gedeeld; teardown kan wel plaatsvinden
            # op de thread die een vrijgegeven TLS-state opruimt.
            check_same_thread=False,
        )
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA busy_timeout=5000")
        except sqlite3.Error:
            # DEF-664: een net verkregen verbinding die haar setup niet haalt
            # (bv. "file is not a database") mag niet open blijven hangen.
            conn.close()
            raise
        conn.row_factory = sqlite3.Row
        state.connection = conn
        return conn

    @contextmanager
    def transaction(self, timeout: float = 30.0) -> Iterator[sqlite3.Connection]:
        """Expliciete transactie met rollback (DEF-391).

        De connectie draait in autocommit-modus (``isolation_level=None``);
        daardoor bieden ``with conn:`` en losse ``conn.commit()``/``rollback()``
        géén atomiciteit. Deze context manager voert expliciet
        ``BEGIN IMMEDIATE``/``COMMIT``/``ROLLBACK`` uit zodat een multi-step
        operatie die halverwege faalt volledig terugrolt.

        Nesting: als de connectie al in een transactie zit sluit de binnenste
        aan zonder nieuwe ``BEGIN`` (SQLite kent geen geneste transacties) —
        de buitenste bepaalt commit/rollback.

        Let op: aangeroepen helpers mogen binnen deze scope géén committende
        ``with conn:`` gebruiken (die zou de transactie vroegtijdig sluiten);
        gebruik een kale ``conn = self.get_connection()``.
        """
        conn = self.get_connection(timeout)
        if conn.in_transaction:
            # Sluit aan bij de lopende transactie van de aanroeper.
            yield conn
            return

        conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
            conn.execute("COMMIT")
        except BaseException:
            # Rol terug als er nog een transactie openstaat — dit dekt zowel een
            # fout in de body als een falende COMMIT. Zonder deze guard zou op de
            # langlevende singleton-connectie de write-lock lekken en zou
            # `in_transaction` vals True blijven, waardoor élke volgende
            # transaction()-call degradeert tot een commit-loze join (stil
            # dataverlies). De ROLLBACK-fout wordt gelogd maar nooit doorgegooid,
            # zodat de oorspronkelijke exception via `raise` behouden blijft.
            if conn.in_transaction:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error:
                    logger.warning(
                        "ROLLBACK na fout in transaction() mislukt", exc_info=True
                    )
            raise

    def has_legacy_columns(self) -> bool:
        """Check if database has legacy columns (datum_voorstel, ketenpartners)."""
        try:
            conn = self.get_connection()
            cursor = conn.execute("PRAGMA table_info(definities)")
            columns = {row[1] for row in cursor.fetchall()}
            return "datum_voorstel" in columns and "ketenpartners" in columns
        except Exception as e:
            logger.warning(f"Legacy columns check gefaald: {e}")
            return False

    def init_database(self) -> None:
        """Initialiseer een verse database of weiger een afwijkende (DEF-664).

        Fail-closed: een database zonder schemaobjecten krijgt het volledige
        canonieke schema uit ``schema.sql`` in één transactie, geverifieerd
        tegen het contract vóór de commit. Elke bestaande database moet op
        ``CANONICAL_VERSION`` staan en het contract halen; anders volgt een
        ``SchemaContractError`` en wordt er niets aangevuld of gemigreerd.

        Vóór deze reparatie telde init alleen twee tabelnamen, slikte een
        halverwege falend script met een warning in, en maakte zonder
        ``schema.sql`` een noodschema van één tabel.
        """
        # DEF-664: de hele I/O- en SQL-grens van init is getypeerd; reasons
        # zijn veilige classificaties, nooit paden of exceptietekst.
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            raise SchemaContractError(
                "schema_init_failed", ("database_dir_unavailable",)
            ) from None
        try:
            conn = self.get_connection()
        except sqlite3.Error as exc:
            raise SchemaContractError(
                "database_unreadable", (type(exc).__name__,)
            ) from exc
        if conn.in_transaction:
            # Een buitenste transactie van de aanroeper wordt nooit door init
            # gecommit of teruggerold.
            raise SchemaContractError(
                "schema_init_failed", ("init binnen een open transactie",)
            )
        try:
            bestaand = has_user_objects(conn)
            if bestaand:
                assert_startup_contract(conn)
        except sqlite3.Error as exc:
            raise SchemaContractError(
                "database_unreadable", (type(exc).__name__,)
            ) from exc
        if bestaand:
            logger.debug(
                "Database schema conform contract (versie %d)", CANONICAL_VERSION
            )
            return
        self._create_fresh_schema(conn)

    @staticmethod
    def _create_fresh_schema(conn: sqlite3.Connection) -> None:
        """Voer schema.sql uit in één transactie en commit alleen bij conformiteit."""
        try:
            schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        except OSError:
            raise SchemaContractError(
                "schema_init_failed", ("schema.sql niet leesbaar",)
            ) from None

        try:
            # `BEGIN` staat in het script zelf: executescript zou een vóóraf
            # geopende transactie eerst impliciet committen.
            conn.executescript("BEGIN;\n" + schema_sql)
            # Codex-herreview P2: niet alleen de hoogste versie maar het
            # volledige doelcontract inclusief de complete markerverzameling
            # {1, 2, 3}, integrity_check en foreign_key_check, vóór de commit.
            problemen = verify_target_contract(conn, CANONICAL_VERSION)
            if problemen:
                reason = (
                    "schema_incomplete"
                    if any(p.startswith("ontbreekt") for p in problemen)
                    else "schema_drift"
                )
                raise SchemaContractError(reason, problemen)
            schema_contract._commit(conn)
        except SchemaContractError:
            rollback_quietly(conn)
            raise
        except Exception as exc:
            # Elke fout ná BEGIN — SQLite, I/O óf een onverwachte Python-fout
            # in de verificatie — rolt terug en wordt getypeerd (Codex-review
            # 3: een ValueError liet 62 objecten met open transactie achter).
            rollback_quietly(conn)
            logger.error("Schema-initialisatie mislukt: %s", type(exc).__name__)
            raise SchemaContractError(
                "schema_init_failed", (type(exc).__name__,)
            ) from exc
        logger.info(
            "Database schema created successfully (versie %d)", CANONICAL_VERSION
        )

    def split_sql_statements(self, sql: str) -> list[str]:
        """Split SQL bestand in individuele statements."""
        statements = []
        current_statement = ""
        in_multiline = False

        for line in sql.split("\n"):
            line = line.strip()

            if line.startswith("--") or not line:
                continue

            if current_statement:
                current_statement += " " + line
            else:
                current_statement = line

            if line.endswith(";") and not in_multiline:
                stmt = current_statement.strip()
                if stmt and not stmt.startswith("--"):
                    statements.append(stmt)
                current_statement = ""

            if any(
                keyword in line.upper()
                for keyword in ["CREATE", "INSERT", "UPDATE", "DELETE", "ALTER"]
            ):
                in_multiline = True
            if line.endswith(";"):
                in_multiline = False

        if current_statement.strip():
            statements.append(current_statement.strip())

        return statements
