"""Database connection management voor de DefinitieAgent.

Beheert SQLite lifecycle, schema-initialisatie, en pragmas.
Wordt als connection provider doorgegeven aan sub-repositories (compositie).
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any

from database.models import DefinitieRecord

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Connection provider — beheert SQLite lifecycle, schema-init, pragmas."""

    def __init__(self, db_path: str = "data/definities.db"):
        self.db_path = db_path

    def get_connection(self, timeout: float = 30.0) -> sqlite3.Connection:
        """Maak database connectie met proper timeout en settings."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=timeout,
            isolation_level=None,
            check_same_thread=False,
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.row_factory = sqlite3.Row
        return conn

    def has_legacy_columns(self) -> bool:
        """Check if database has legacy columns (datum_voorstel, ketenpartners)."""
        try:
            with self.get_connection() as conn:
                return self.has_legacy_columns_in_conn(conn)
        except Exception as e:
            logger.warning(f"Legacy columns check gefaald: {e}")
            return False

    @staticmethod
    def has_legacy_columns_in_conn(conn: sqlite3.Connection) -> bool:
        """Determine legacy column presence using an existing connection."""
        cursor = conn.execute("PRAGMA table_info(definities)")
        columns = {row[1] for row in cursor.fetchall()}
        return "datum_voorstel" in columns and "ketenpartners" in columns

    @staticmethod
    def build_insert_columns(
        record: DefinitieRecord, wb_value: str, include_legacy: bool
    ) -> tuple[list[str], list[Any]]:
        """Compose insert columns/values for definities table."""
        columns = [
            "begrip",
            "definitie",
            "categorie",
            "organisatorische_context",
            "juridische_context",
            "wettelijke_basis",
            "ufo_categorie",
            "toelichting_proces",
            "status",
            "version_number",
            "previous_version_id",
            "validation_score",
            "validation_date",
            "validation_issues",
            "source_type",
            "source_reference",
            "imported_from",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "approved_by",
            "approved_at",
            "approval_notes",
            "last_exported_at",
            "export_destinations",
            "generation_prompt_data",
        ]

        values: list[Any] = [
            record.begrip,
            record.definitie,
            record.categorie,
            record.organisatorische_context,
            record.juridische_context,
            wb_value,
            record.ufo_categorie,
            record.toelichting_proces,
            record.status,
            record.version_number,
            record.previous_version_id,
            record.validation_score,
            record.validation_date,
            record.validation_issues,
            record.source_type,
            record.source_reference,
            record.imported_from,
            record.created_at,
            record.updated_at,
            record.created_by,
            record.updated_by,
            record.approved_by,
            record.approved_at,
            record.approval_notes,
            record.last_exported_at,
            record.export_destinations,
            record.generation_prompt_data,
        ]

        if include_legacy:
            columns.extend(["datum_voorstel", "ketenpartners"])
            values.extend([record.datum_voorstel, record.ketenpartners])

        return columns, values

    def init_database(self):
        """Initialiseer database met schema."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) FROM sqlite_master
                    WHERE type='table' AND name IN ('definities', 'synonym_groups')
                    """
                )
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
            with self.get_connection() as conn:
                conn.execute(
                    """
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
                """
                )
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
