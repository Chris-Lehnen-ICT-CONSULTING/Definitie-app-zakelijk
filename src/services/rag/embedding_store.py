"""EmbeddingStore: SQLite BLOB + numpy cosine similarity (DEF-304).

Slaat chunk-tekst + metadata + embeddings op in SQLite en voert
cosine similarity search uit met numpy. Geen externe vector database nodig.

Optimaal tot ~50.000 chunks per collection (~50ms voor 5000, ~200ms voor 50.000).
"""

from __future__ import annotations

import json
import logging
import sqlite3

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingStore:
    """Slaat chunk-tekst + metadata + embeddings op in SQLite.

    Voert cosine similarity search uit met numpy.
    Nieuwe connectie per operatie (veilig voor Streamlit reruns).
    """

    def __init__(self, db_path: str):
        """Configureer database pad. Geen persistente connectie.

        Args:
            db_path: Pad naar SQLite database (data/definities.db)
        """
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        """Maak nieuwe SQLite connectie met foreign keys enabled."""
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _get_collection_dimensions(
        self, conn: sqlite3.Connection, collection_id: int
    ) -> int | None:
        """Lees verwachte embedding dimensies uit collection metadata.

        Returns:
            Dimensie-getal of None als niet geconfigureerd.

        Raises:
            ValueError: Als collection niet gevonden is.
        """
        cursor = conn.execute(
            "SELECT metadata_json FROM rag_collections WHERE id = ?",
            (collection_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"Collection {collection_id} niet gevonden")

        metadata_json = row[0]
        if not metadata_json:
            return None

        try:
            metadata = json.loads(metadata_json)
        except json.JSONDecodeError:
            logger.warning(
                "Ongeldige JSON in metadata van collection %d, "
                "dimensievalidatie overgeslagen",
                collection_id,
            )
            return None
        return metadata.get("dimensions")

    def _validate_embedding(
        self, embedding: np.ndarray, expected_dims: int | None
    ) -> None:
        """Valideer type, shape en dimensies van embedding."""
        if not isinstance(embedding, np.ndarray):
            raise TypeError(
                f"Embedding moet numpy.ndarray zijn, kreeg: {type(embedding).__name__}"
            )
        if embedding.ndim != 1:
            raise ValueError(
                f"Embedding moet 1-dimensionaal zijn, kreeg shape: {embedding.shape}"
            )
        if expected_dims is not None and embedding.shape[0] != expected_dims:
            raise ValueError(
                f"Embedding dimensie {embedding.shape[0]} matcht niet met "
                f"collection dimensie {expected_dims}"
            )

    def create_collection(
        self,
        collection_name: str,
        dimensions: int = 3072,
        model: str = "text-embedding-3-large",
        extra_metadata: dict | None = None,
    ) -> int:
        """Maak nieuwe collection aan met dimensie-metadata.

        Slaat {"dimensions": N, "model": "...", ...extra} op in
        rag_collections.metadata_json.
        NB: de kolommen document_count en chunk_count in rag_collections
        worden niet bijgewerkt — gebruik RAGService.get_collection_stats()
        voor actuele tellingen (DEF-363).

        Args:
            extra_metadata: Optionele extra velden (bijv. type, rechtsgebied)
                die worden samengevoegd in metadata_json.

        Returns:
            collection_id
        """
        if dimensions <= 0:
            raise ValueError(f"Dimensions moet positief zijn, kreeg: {dimensions}")
        meta = {"dimensions": dimensions, "model": model}
        if extra_metadata:
            meta.update(extra_metadata)
        metadata = json.dumps(meta)
        conn = self._connect()
        try:
            cursor = conn.execute(
                "INSERT INTO rag_collections (collection_name, metadata_json) "
                "VALUES (?, ?)",
                (collection_name, metadata),
            )
            conn.commit()
            collection_id = cursor.lastrowid
            logger.info(
                "Collection '%s' aangemaakt (id=%d, dimensions=%d, model=%s)",
                collection_name,
                collection_id,
                dimensions,
                model,
            )
            return collection_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def store_chunk(
        self,
        collection_id: int,
        document_id: int,
        chunk_text: str,
        embedding: np.ndarray,
        chunk_index: int,
        rechtsgebied: str | None = None,
        wet_regeling: str | None = None,
        artikel_lid: str | None = None,
        bron_type: str | None = None,
        metadata: dict | None = None,
    ) -> int:
        """Sla chunk-tekst + metadata + embedding op in één INSERT.

        Valideert embedding dimensies tegen collection metadata.
        Metadata wordt opgeslagen als JSONB via jsonb() wrapper.

        Args:
            bron_type: Brontype filter ("wetgeving", "website", "pdf", "api").
            metadata: Extensibele metadata dict (opgeslagen als JSONB).

        Returns:
            chunk_id
        """
        if not chunk_text or not chunk_text.strip():
            raise ValueError("chunk_text mag niet leeg zijn")
        metadata_json = json.dumps(metadata or {})
        conn = self._connect()
        try:
            dims = self._get_collection_dimensions(conn, collection_id)
            self._validate_embedding(embedding, dims)

            cursor = conn.execute(
                "INSERT INTO rag_chunks "
                "(collection_id, document_id, chunk_text, embedding, chunk_index, "
                "rechtsgebied, wet_regeling, artikel_lid, bron_type, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, jsonb(?))",
                (
                    collection_id,
                    document_id,
                    chunk_text,
                    embedding.astype(np.float32).tobytes(),
                    chunk_index,
                    rechtsgebied,
                    wet_regeling,
                    artikel_lid,
                    bron_type,
                    metadata_json,
                ),
            )
            conn.commit()
            chunk_id = cursor.lastrowid
            logger.debug(
                "Chunk opgeslagen (id=%d, collection=%d)", chunk_id, collection_id
            )
            return chunk_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def store_batch(
        self,
        collection_id: int,
        document_id: int,
        chunks: list[dict],
        embeddings: list[np.ndarray],
    ) -> list[int]:
        """Sla meerdere chunks op in één transactie.

        Eén connectie, één transactie voor de hele batch.

        Args:
            collection_id: ID van de collection.
            document_id: ID van het document.
            chunks: Lijst van dicts met keys: chunk_text, chunk_index,
                    en optioneel: rechtsgebied, wet_regeling, artikel_lid.
            embeddings: Lijst van numpy arrays (zelfde lengte als chunks).

        Returns:
            Lijst van chunk_ids.
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Aantal chunks ({len(chunks)}) matcht niet met "
                f"aantal embeddings ({len(embeddings)})"
            )
        if not chunks:
            return []

        conn = self._connect()
        try:
            dims = self._get_collection_dimensions(conn, collection_id)
            for emb in embeddings:
                self._validate_embedding(emb, dims)

            chunk_ids = []
            sql = (
                "INSERT INTO rag_chunks "
                "(collection_id, document_id, chunk_text, embedding, chunk_index, "
                "rechtsgebied, wet_regeling, artikel_lid, bron_type, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, jsonb(?))"
            )
            for chunk, emb in zip(chunks, embeddings, strict=True):
                if not chunk["chunk_text"] or not chunk["chunk_text"].strip():
                    raise ValueError("chunk_text mag niet leeg zijn")
                metadata_json = json.dumps(chunk.get("metadata") or {})
                cursor = conn.execute(
                    sql,
                    (
                        collection_id,
                        document_id,
                        chunk["chunk_text"],
                        emb.astype(np.float32).tobytes(),
                        chunk["chunk_index"],
                        chunk.get("rechtsgebied"),
                        chunk.get("wet_regeling"),
                        chunk.get("artikel_lid"),
                        chunk.get("bron_type"),
                        metadata_json,
                    ),
                )
                chunk_ids.append(cursor.lastrowid)

            conn.commit()

            logger.info(
                "Batch opgeslagen: %d chunks in collection %d",
                len(chunk_ids),
                collection_id,
            )
            return chunk_ids
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _parse_metadata(raw: str | None) -> dict:
        """Parse metadata JSON string naar dict. Lege/ongeldige waarden → {}."""
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def search_similar(
        self,
        query_embedding: np.ndarray,
        collection_id: int,
        top_k: int = 5,
    ) -> list[dict]:
        """Zoek meest relevante chunks via cosine similarity.

        1. Laad alle embeddings uit collection
        2. Cosine similarity: dot(a,b) / (norm(a) * norm(b))
        3. Sorteer op score, return top_k

        Metadata wordt geparsed naar dict. Lees-conventie (overgangsperiode):
        artikel_lid veld wordt gevuld uit metadata.artikel_nummer met
        fallback op de legacy artikel_lid kolom.

        Returns:
            list[dict] met keys: chunk_id, chunk_text, score, rechtsgebied,
            wet_regeling, artikel_lid, bron_type, metadata,
            document_id, chunk_index, created_at
        """
        conn = self._connect()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id, chunk_text, embedding, rechtsgebied, wet_regeling, "
                "artikel_lid, bron_type, json(metadata) AS metadata, "
                "document_id, chunk_index, created_at "
                "FROM rag_chunks "
                "WHERE collection_id = ? AND embedding IS NOT NULL",
                (collection_id,),
            )
            rows = cursor.fetchall()

            if not rows:
                return []

            query_vec = query_embedding.astype(np.float32)
            query_norm = np.linalg.norm(query_vec)
            if query_norm == 0:
                return []

            # Vectorized cosine similarity
            embeddings_matrix = np.array(
                [np.frombuffer(row["embedding"], dtype=np.float32) for row in rows]
            )

            dot_products = embeddings_matrix @ query_vec
            norms = np.linalg.norm(embeddings_matrix, axis=1)

            # Avoid division by zero for any zero-norm embeddings
            safe_norms = np.where(norms == 0, 1.0, norms)
            similarities = dot_products / (safe_norms * query_norm)
            similarities = np.where(norms == 0, 0.0, similarities)

            # Get top_k indices sorted by similarity descending
            k = min(top_k, len(rows))
            top_indices = np.argsort(similarities)[::-1][:k]

            results = []
            for idx in top_indices:
                row = rows[idx]
                meta = self._parse_metadata(row["metadata"])

                # Lees-conventie: metadata.artikel_nummer met fallback op
                # legacy artikel_lid kolom
                artikel_lid = meta.get("artikel_nummer") or row["artikel_lid"]

                results.append(
                    {
                        "chunk_id": row["id"],
                        "chunk_text": row["chunk_text"],
                        "score": float(similarities[idx]),
                        "rechtsgebied": row["rechtsgebied"],
                        "wet_regeling": row["wet_regeling"],
                        "artikel_lid": artikel_lid,
                        "bron_type": row["bron_type"],
                        "metadata": meta,
                        "document_id": row["document_id"],
                        "chunk_index": row["chunk_index"],
                        "created_at": row["created_at"],
                    }
                )

            return results
        finally:
            conn.close()

    def get_embedding(self, chunk_id: int) -> np.ndarray | None:
        """Haal enkele embedding op.

        Returns:
            numpy array of None als chunk niet gevonden.
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT embedding FROM rag_chunks WHERE id = ?",
                (chunk_id,),
            )
            row = cursor.fetchone()
            if row is None or row[0] is None:
                return None
            return np.frombuffer(row[0], dtype=np.float32).copy()
        finally:
            conn.close()

    def delete_collection_embeddings(self, collection_id: int) -> int:
        """Verwijder alle chunks + embeddings van een collection.

        Returns:
            Aantal verwijderde rijen.
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                "DELETE FROM rag_chunks WHERE collection_id = ?",
                (collection_id,),
            )
            conn.commit()
            count = cursor.rowcount
            logger.info("%d chunks verwijderd uit collection %d", count, collection_id)
            return count
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
