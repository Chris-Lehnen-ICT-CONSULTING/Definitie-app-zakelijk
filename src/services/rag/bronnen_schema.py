"""Schema van het bronnenbestand `data/bronnen.db` (DEF-620, RAG fase 3).

De bronbibliotheek (collecties, documenten, fragmenten met embeddings) staat in
een eigen SQLite-bestand, los van de definities in `data/definities.db`.
Bronnen zijn opnieuw in te lezen uit de officiële publicaties; definities niet.
Gescheiden blijven backups van de definities klein en raakt het vervangen van
bronnen de definities nooit.

De tabeldefinities zijn gelijk aan die van de RAG-tabellen in
`src/database/schema.sql` (v8), zodat `EmbeddingStore`, `RAGService` en
`RAGManagementService` ongewijzigd werken. `zorg_voor_bronnen_schema` is
idempotent; de container roept het aan vóór het eerste gebruik.

`projects.rag_collection_id` en `ontological_models.rag_collection_id` in
`definities.db` verwijzen naar collecties; over twee bestanden heen dwingt
SQLite die koppeling niet af. Beide kolommen worden in de code niet gelezen of
geschreven (06-10-2026: `projects` leeg, één ontologisch model zonder
collectie).
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from database.sqlite_backup import BRONNEN_KERN_TABELLEN

logger = logging.getLogger(__name__)

#: Versie van het bronnenschema (PRAGMA user_version van bronnen.db).
BRONNEN_SCHEMA_VERSIE = 1

RAG_TABELLEN: tuple[str, ...] = ("rag_collections", "rag_documents", "rag_chunks")

#: Kernmanifest van het bronnenbestand voor de geverifieerde backup (DEF-663).
#: Backup via de CLI: ``PYTHONPATH=src python -m database.sqlite_backup --kern
#: bronnen data/bronnen.db data/backups/bronnen_backup_<datum>.db``.
BRONNEN_KERN: dict[str, tuple[str, ...]] = dict(BRONNEN_KERN_TABELLEN)

BRONNEN_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS rag_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS rag_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER REFERENCES rag_collections(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    file_type VARCHAR(50),
    chunk_count INTEGER,
    rechtsgebied VARCHAR(100),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_path VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS rag_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER REFERENCES rag_collections(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES rag_documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding BLOB,
    chunk_index INTEGER,
    rechtsgebied VARCHAR(100),
    wet_regeling VARCHAR(255),
    artikel_lid VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    bron_type VARCHAR(50),
    metadata TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_chunks_collection ON rag_chunks(collection_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON rag_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_rechtsgebied ON rag_chunks(rechtsgebied);
CREATE INDEX IF NOT EXISTS idx_chunks_wet_regeling ON rag_chunks(wet_regeling);
CREATE INDEX IF NOT EXISTS idx_chunks_bron_type ON rag_chunks(bron_type);
"""


def _heeft_tabel(conn: sqlite3.Connection, naam: str) -> bool:
    rij = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (naam,)
    ).fetchone()
    return rij is not None


def zorg_voor_bronnen_schema(db_path: str | Path) -> None:
    """Maak de RAG-tabellen aan in het bronnenbestand (idempotent).

    Een definitiedatabase (met tabel `definities`) wordt niet aangeraakt: die
    heeft de RAG-tabellen al via zijn eigen schema en migraties, en een extra
    versiemarkering zou het schemacontract daar breken.
    """
    pad = str(db_path)
    if pad != ":memory:":
        Path(pad).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(pad)
    try:
        if _heeft_tabel(conn, "definities"):
            logger.warning(
                "Bronnenpad %s is een definitiedatabase; schema niet aangepast", pad
            )
            return
        conn.executescript(BRONNEN_SCHEMA_SQL)
        if conn.execute("PRAGMA user_version").fetchone()[0] < BRONNEN_SCHEMA_VERSIE:
            conn.execute(f"PRAGMA user_version = {BRONNEN_SCHEMA_VERSIE}")
        conn.commit()
    finally:
        conn.close()


def aantal_rag_chunks(db_path: str | Path) -> int:
    """Aantal fragmenten in een bestand met RAG-tabellen; 0 als die ontbreken."""
    pad = Path(db_path)
    if not pad.is_file():
        return 0
    conn = sqlite3.connect(f"file:{pad}?mode=ro", uri=True)
    try:
        if not _heeft_tabel(conn, "rag_chunks"):
            return 0
        return int(conn.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()[0])
    finally:
        conn.close()
