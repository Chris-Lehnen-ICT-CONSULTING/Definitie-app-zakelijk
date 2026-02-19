"""RAGService — hoofdservice voor document ingest en context retrieval.

Combineert DocumentChunker, EmbeddingService en EmbeddingStore tot één
simpele API voor de RAG pipeline. Aparte service naast HybridContextEngine.

DEF-291: Fase 1.3 van de RAG implementatie.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from services.rag.document_chunker import DocumentChunker
from services.rag.embedding_service import EmbeddingService
from services.rag.embedding_store import EmbeddingStore
from utils.xml_source_formatter import format_bron, wrap_bronnen

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RAGContext:
    """Resultaat van een retrieve_context() call.

    Bevat zowel raw chunks (voor bronvermelding/UI) als een
    formatted_context string (voor de GPT prompt).
    """

    chunks: list[dict]
    formatted_context: str
    collection_id: int
    query: str


class RAGService:
    """Hoofdservice voor de RAG pipeline.

    Verantwoordelijkheden:
    - Document ingest (chunk + embed + store in één call)
    - Context retrieval (embed query + cosine search)
    - Collection management (auto-aanmaken)
    - Document registratie in rag_documents

    Geen directe dependency op HybridContextEngine.
    """

    def __init__(
        self,
        document_chunker: DocumentChunker,
        embedding_service: EmbeddingService,
        embedding_store: EmbeddingStore,
        db_path: str,
    ) -> None:
        self._chunker = document_chunker
        self._embedder = embedding_service
        self._store = embedding_store
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        """Maak nieuwe SQLite connectie met foreign keys enabled."""
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _ensure_collection(self, collection_name: str) -> int:
        """Maak collection aan als die niet bestaat, return collection_id."""
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT id FROM rag_collections WHERE collection_name = ?",
                (collection_name,),
            )
            row = cursor.fetchone()
            if row is not None:
                return row[0]
        finally:
            conn.close()

        collection_id = self._store.create_collection(
            collection_name=collection_name,
            dimensions=EmbeddingService.DIMENSIONS,
            model=EmbeddingService.MODEL,
        )
        logger.info(
            "Collection '%s' automatisch aangemaakt (id=%d)",
            collection_name,
            collection_id,
        )
        return collection_id

    def ingest_document(
        self,
        tekst: str,
        collection_id: int,
        filename: str,
        file_type: str = "text/plain",
        rechtsgebied: str | None = None,
        file_path: str | None = None,
    ) -> int:
        """Chunk, embed en sla een document op in één call.

        Flow:
        1. Insert rij in rag_documents
        2. DocumentChunker.chunk_tekst()
        3. EmbeddingService.embed_batch()
        4. EmbeddingStore.store_batch()

        Bij failure in stap 3/4: cleanup rag_documents rij (alles-of-niets).

        Returns:
            document_id
        """
        if not tekst or not tekst.strip():
            raise ValueError("tekst mag niet leeg zijn")

        # Stap 1: Registreer document
        conn = self._connect()
        try:
            cursor = conn.execute(
                "INSERT INTO rag_documents "
                "(collection_id, filename, file_type, rechtsgebied, chunk_count, file_path) "
                "VALUES (?, ?, ?, ?, 0, ?)",
                (collection_id, filename, file_type, rechtsgebied, file_path),
            )
            conn.commit()
            document_id = cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        logger.info(
            "Document geregistreerd: id=%d, filename=%s, collection=%d",
            document_id,
            filename,
            collection_id,
        )

        try:
            # Stap 2: Chunk de tekst
            result = self._chunker.chunk_tekst(tekst, filename, file_type, rechtsgebied)

            if result.fout_melding:
                raise RuntimeError(f"Chunking mislukt: {result.fout_melding}")

            if not result.chunks:
                raise RuntimeError("Chunking leverde 0 chunks op")

            chunk_texts = [c.tekst for c in result.chunks]

            # Stap 3: Embed alle chunks
            embeddings = self._embedder.embed_batch(chunk_texts)

            # Stap 4: Store chunks + embeddings
            chunk_dicts = [
                {
                    "chunk_text": c.tekst,
                    "chunk_index": c.metadata.chunk_index,
                    "rechtsgebied": c.metadata.rechtsgebied,
                    "wet_regeling": c.metadata.wet_regeling,
                    "artikel_lid": c.metadata.artikel_nummer,
                }
                for c in result.chunks
            ]

            self._store.store_batch(
                collection_id=collection_id,
                document_id=document_id,
                chunks=chunk_dicts,
                embeddings=embeddings,
            )

            # Update chunk_count op het document
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE rag_documents SET chunk_count = ? WHERE id = ?",
                    (len(result.chunks), document_id),
                )
                conn.commit()
            finally:
                conn.close()

            logger.info(
                "Document ingested: id=%d, %d chunks, %d tokens",
                document_id,
                len(result.chunks),
                result.totaal_tokens,
            )
            return document_id

        except Exception:
            # Rollback: verwijder de rag_documents rij
            logger.warning(
                "Ingest mislukt voor document %d — rollback rag_documents rij",
                document_id,
            )
            conn = self._connect()
            try:
                conn.execute("DELETE FROM rag_documents WHERE id = ?", (document_id,))
                conn.commit()
            except Exception as cleanup_err:
                logger.error(
                    "Cleanup van rag_documents rij %d mislukt: %s",
                    document_id,
                    cleanup_err,
                )
            finally:
                conn.close()
            raise

    def retrieve_context(
        self,
        query: str,
        collection_id: int,
        top_k: int = 5,
    ) -> RAGContext:
        """Embed query, zoek vergelijkbare chunks, return RAGContext.

        Returns:
            RAGContext met raw chunks en formatted context string.
        """
        if not query or not query.strip():
            return RAGContext(
                chunks=[],
                formatted_context="",
                collection_id=collection_id,
                query=query or "",
            )

        query_embedding = self._embedder.embed(query)

        results = self._store.search_similar(
            query_embedding=query_embedding,
            collection_id=collection_id,
            top_k=top_k,
        )

        formatted = self._format_context(results)

        logger.info(
            "Context retrieved: query='%s', %d chunks, collection=%d",
            query[:50],
            len(results),
            collection_id,
        )

        return RAGContext(
            chunks=results,
            formatted_context=formatted,
            collection_id=collection_id,
            query=query,
        )

    def _format_context(self, chunks: list[dict]) -> str:
        """Format chunks als XML <bronnen> voor de prompt.

        Delegeert naar de shared xml_source_formatter utility (DEF-315).
        Metadata (score, confidence, level, rechtsgebied, regeling, artikel)
        zitten als attributen op de tag — structureel gescheiden van de tekst.
        """
        if not chunks:
            return ""

        bron_strings = []
        for i, chunk in enumerate(chunks, 1):
            score = chunk.get("score")
            bron_strings.append(
                format_bron(
                    nr=i,
                    type="rag",
                    chunk_text=chunk["chunk_text"],
                    score=score,
                    confidence=score,
                    rechtsgebied=chunk.get("rechtsgebied"),
                    regeling=chunk.get("wet_regeling"),
                    artikel=chunk.get("artikel_lid"),
                )
            )

        return wrap_bronnen(bron_strings)

    def cleanup_all_documents(self) -> int:
        """Verwijder alle documenten, chunks (CASCADE) en upload-bestanden.

        Returns:
            Aantal verwijderde documenten.
        """
        conn = self._connect()
        try:
            # Haal file_paths op voordat we verwijderen
            file_paths = [
                row[0]
                for row in conn.execute(
                    "SELECT file_path FROM rag_documents WHERE file_path IS NOT NULL"
                ).fetchall()
            ]
            count = conn.execute("SELECT COUNT(*) FROM rag_documents").fetchone()[0]
            conn.execute("DELETE FROM rag_documents")
            conn.commit()

            # Verwijder bestanden van schijf
            for fp in file_paths:
                try:
                    Path(fp).unlink(missing_ok=True)
                except OSError as e:
                    logger.warning("Upload verwijderen mislukt: %s — %s", fp, e)

            logger.info("Alle RAG documenten verwijderd: %d documenten", count)
            return count
        finally:
            conn.close()

    def get_collection_stats(self, collection_id: int) -> dict:
        """Return collection metadata + document/chunk counts.

        Returns:
            Dict met: collection_id, name, document_count, chunk_count,
            dimensions, model.
        """
        conn = self._connect()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id, collection_name, metadata_json "
                "FROM rag_collections WHERE id = ?",
                (collection_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError(f"Collection {collection_id} niet gevonden")

            metadata = {}
            if row["metadata_json"]:
                try:
                    metadata = json.loads(row["metadata_json"])
                except json.JSONDecodeError:
                    pass

            # Tel documenten en chunks
            doc_count = conn.execute(
                "SELECT COUNT(*) FROM rag_documents WHERE collection_id = ?",
                (collection_id,),
            ).fetchone()[0]

            chunk_count = conn.execute(
                "SELECT COUNT(*) FROM rag_chunks WHERE collection_id = ?",
                (collection_id,),
            ).fetchone()[0]

            return {
                "collection_id": row["id"],
                "name": row["collection_name"],
                "document_count": doc_count,
                "chunk_count": chunk_count,
                "dimensions": metadata.get("dimensions"),
                "model": metadata.get("model"),
            }
        finally:
            conn.close()
