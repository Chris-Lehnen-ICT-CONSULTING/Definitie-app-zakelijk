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

logger = logging.getLogger(__name__)


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
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
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
        """Initialiseer database met schema."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            conn = self.get_connection()
            cursor = conn.execute("""
                SELECT COUNT(*) FROM sqlite_master
                WHERE type='table' AND name IN ('definities', 'synonym_groups')
                """)
            table_count = cursor.fetchone()[0]

            if table_count == 0:
                with open(schema_path, encoding="utf-8") as f:
                    schema_sql = f.read()
                    try:
                        conn.executescript(schema_sql)
                        logger.info("Database schema created successfully")
                    except sqlite3.Error as e:
                        logger.warning(f"Schema execution warning: {e}")
            else:
                logger.debug(
                    f"Database tables already exist ({table_count} found), skipping schema creation"
                )
        else:
            logger.warning("schema.sql not found, creating basic schema")
            conn = self.get_connection()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS definities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    begrip VARCHAR(255) NOT NULL,
                    definitie TEXT NOT NULL,
                    categorie VARCHAR(50) NOT NULL DEFAULT 'proces',
                    organisatorische_context VARCHAR(255) NOT NULL,
                    juridische_context VARCHAR(255),
                    wettelijke_basis TEXT,
                    status VARCHAR(50) NOT NULL DEFAULT 'draft',
                    version_number INTEGER NOT NULL DEFAULT 1,
                    validation_score DECIMAL(3,2),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(255),
                    source_type VARCHAR(50) DEFAULT 'generated',
                    datum_voorstel TIMESTAMP,
                    ketenpartners TEXT
                )
            """)
            conn.commit()

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
