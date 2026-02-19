"""RAGManagementService — CRUD beheer voor RAG collections en documenten (DEF-365).

Gescheiden van RAGService om beide bestanden onder de 300-regels limiet te houden.
RAGService doet ingest + retrieval; deze service doet management operaties.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

from services.rag.constants import COLLECTION_TYPE_MAP
from services.rag.embedding_service import EmbeddingService
from services.rag.embedding_store import EmbeddingStore

logger = logging.getLogger(__name__)


class RAGManagementService:
    """CRUD operaties voor RAG collections en documenten.

    Verantwoordelijkheden:
    - Collections: list, create (met type), delete (CASCADE)
    - Documenten: list, delete (CASCADE), duplicaat check
    - File cleanup bij delete operaties
    """

    def __init__(self, db_path: str, embedding_store: EmbeddingStore) -> None:
        self._db_path = db_path
        self._store = embedding_store

    def _connect(self) -> sqlite3.Connection:
        """Maak nieuwe SQLite connectie met foreign keys enabled."""
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def list_collections(self) -> list[dict]:
        """Alle collections met live doc/chunk counts + type uit metadata.

        Returns:
            Lijst van dicts met: id, name, type_key, type_icon, type_label,
            document_count, chunk_count, rechtsgebied, created_at.
        """
        conn = self._connect()
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, collection_name, metadata_json, created_at "
                "FROM rag_collections ORDER BY created_at DESC"
            ).fetchall()

            result = []
            for row in rows:
                cid = row["id"]
                metadata = _parse_metadata(row["metadata_json"])
                type_key = metadata.get("type", "vrij")
                ct = COLLECTION_TYPE_MAP.get(type_key)

                doc_count = conn.execute(
                    "SELECT COUNT(*) FROM rag_documents WHERE collection_id = ?",
                    (cid,),
                ).fetchone()[0]

                chunk_count = conn.execute(
                    "SELECT COUNT(*) FROM rag_chunks WHERE collection_id = ?",
                    (cid,),
                ).fetchone()[0]

                result.append(
                    {
                        "id": cid,
                        "name": row["collection_name"],
                        "type_key": type_key,
                        "type_icon": ct.icon if ct else "\U0001f4c1",
                        "type_label": ct.label if ct else "Vrij",
                        "document_count": doc_count,
                        "chunk_count": chunk_count,
                        "rechtsgebied": metadata.get("rechtsgebied"),
                        "created_at": row["created_at"],
                    }
                )
            return result
        finally:
            conn.close()

    def create_collection(
        self,
        name: str,
        collection_type: str = "vrij",
        rechtsgebied: str | None = None,
    ) -> int:
        """Maak nieuwe collection aan met type metadata.

        Args:
            name: Unieke collection naam.
            collection_type: Key uit COLLECTION_TYPES (default "vrij").
            rechtsgebied: Optioneel rechtsgebied.

        Returns:
            collection_id
        """
        extra: dict = {"type": collection_type}
        if rechtsgebied:
            extra["rechtsgebied"] = rechtsgebied

        collection_id = self._store.create_collection(
            collection_name=name,
            dimensions=EmbeddingService.DIMENSIONS,
            model=EmbeddingService.MODEL,
            extra_metadata=extra,
        )
        logger.info(
            "Collection '%s' aangemaakt (id=%d, type=%s)",
            name,
            collection_id,
            collection_type,
        )
        return collection_id

    def delete_collection(self, collection_id: int) -> bool:
        """Verwijder collection met CASCADE (documenten, chunks, bestanden).

        Returns:
            True als collection bestond en is verwijderd.
        """
        conn = self._connect()
        try:
            # Haal file_paths op voordat we verwijderen
            file_paths = [
                row[0]
                for row in conn.execute(
                    "SELECT file_path FROM rag_documents "
                    "WHERE collection_id = ? AND file_path IS NOT NULL",
                    (collection_id,),
                ).fetchall()
            ]

            cursor = conn.execute(
                "DELETE FROM rag_collections WHERE id = ?",
                (collection_id,),
            )
            conn.commit()
            deleted = cursor.rowcount > 0

            if deleted:
                _cleanup_files(file_paths)
                logger.info("Collection %d verwijderd (CASCADE)", collection_id)
            return deleted
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def list_documents(self, collection_id: int) -> list[dict]:
        """Documenten in een collection.

        Returns:
            Lijst van dicts met: id, filename, file_type, chunk_count,
            rechtsgebied, processed_at, file_path.
        """
        conn = self._connect()
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, filename, file_type, chunk_count, rechtsgebied, "
                "processed_at, file_path "
                "FROM rag_documents WHERE collection_id = ? "
                "ORDER BY processed_at DESC",
                (collection_id,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def delete_document(self, document_id: int) -> bool:
        """Verwijder document met CASCADE (chunks) + file cleanup.

        Returns:
            True als document bestond en is verwijderd.
        """
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT file_path FROM rag_documents WHERE id = ?",
                (document_id,),
            ).fetchone()
            if row is None:
                return False

            file_path = row[0]
            conn.execute("DELETE FROM rag_documents WHERE id = ?", (document_id,))
            conn.commit()

            if file_path:
                _cleanup_files([file_path])

            logger.info("Document %d verwijderd (CASCADE)", document_id)
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def check_duplicate_document(self, collection_id: int, filename: str) -> bool:
        """Check of een document met dezelfde filename al bestaat in de collection.

        Returns:
            True als er al een document met die filename bestaat.
        """
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT 1 FROM rag_documents "
                "WHERE collection_id = ? AND filename = ? LIMIT 1",
                (collection_id, filename),
            ).fetchone()
            return row is not None
        finally:
            conn.close()


def _parse_metadata(metadata_json: str | None) -> dict:
    """Parse metadata_json, return leeg dict bij None of invalid JSON."""
    if not metadata_json:
        return {}
    try:
        return json.loads(metadata_json)
    except (json.JSONDecodeError, TypeError):
        return {}


def _cleanup_files(file_paths: list[str]) -> None:
    """Verwijder bestanden van schijf, log warnings bij fouten."""
    for fp in file_paths:
        try:
            Path(fp).unlink(missing_ok=True)
        except OSError as e:
            logger.warning("Upload verwijderen mislukt: %s — %s", fp, e)
