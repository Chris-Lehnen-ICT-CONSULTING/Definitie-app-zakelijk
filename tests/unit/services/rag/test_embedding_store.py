"""Tests voor EmbeddingStore (DEF-304)."""

from __future__ import annotations

import json
import sqlite3

import numpy as np
import pytest

from services.rag.embedding_store import EmbeddingStore

# ---------------------------------------------------------------------------
# Schema setup (mirrors v5_migration tables)
# ---------------------------------------------------------------------------
SCHEMA_SQL = """
CREATE TABLE rag_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_name VARCHAR(255) NOT NULL UNIQUE,
    document_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT
);

CREATE TABLE rag_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER REFERENCES rag_collections(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    file_type VARCHAR(50),
    chunk_count INTEGER,
    rechtsgebied VARCHAR(100),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_path VARCHAR(500)
);

CREATE TABLE rag_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER REFERENCES rag_collections(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES rag_documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding BLOB,
    chunk_index INTEGER,
    rechtsgebied VARCHAR(100),
    wet_regeling VARCHAR(255),
    artikel_lid VARCHAR(100),
    bron_type VARCHAR(50),
    metadata TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chunks_collection ON rag_chunks(collection_id);
CREATE INDEX idx_chunks_document ON rag_chunks(document_id);
CREATE INDEX idx_chunks_rechtsgebied ON rag_chunks(rechtsgebied);
CREATE INDEX idx_chunks_wet_regeling ON rag_chunks(wet_regeling);
CREATE INDEX idx_chunks_bron_type ON rag_chunks(bron_type);
"""

DIMS = 8  # Small dimension for fast tests


def _make_embedding(seed: int = 0, dims: int = DIMS) -> np.ndarray:
    """Deterministic embedding vector for testing."""
    rng = np.random.RandomState(seed)
    return rng.randn(dims).astype(np.float32)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def db_path(tmp_path):
    """Create a temporary SQLite database with RAG schema."""
    path = str(tmp_path / "test.db")
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA_SQL)
    conn.close()
    return path


@pytest.fixture
def store(db_path):
    """EmbeddingStore instance connected to test database."""
    return EmbeddingStore(db_path=db_path)


@pytest.fixture
def collection_id(store):
    """Pre-created collection with DIMS dimensions."""
    return store.create_collection("test_collection", dimensions=DIMS)


@pytest.fixture
def document_id(db_path, collection_id):
    """Pre-created document in the test collection."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "INSERT INTO rag_documents (collection_id, filename, file_type) "
        "VALUES (?, ?, ?)",
        (collection_id, "test.pdf", "application/pdf"),
    )
    conn.commit()
    doc_id = cursor.lastrowid
    conn.close()
    return doc_id


# ---------------------------------------------------------------------------
# Tests: create_collection
# ---------------------------------------------------------------------------
class TestCreateCollection:
    def test_returns_collection_id(self, store):
        cid = store.create_collection("mijn_collectie", dimensions=128)
        assert isinstance(cid, int)
        assert cid > 0

    def test_stores_dimensions_in_metadata(self, store, db_path):
        cid = store.create_collection("dims_test", dimensions=256, model="voyage-3")
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT metadata_json FROM rag_collections WHERE id = ?", (cid,)
        ).fetchone()
        conn.close()
        metadata = json.loads(row[0])
        assert metadata["dimensions"] == 256
        assert metadata["model"] == "voyage-3"

    def test_default_dimensions_and_model(self, store, db_path):
        cid = store.create_collection("defaults_test")
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT metadata_json FROM rag_collections WHERE id = ?", (cid,)
        ).fetchone()
        conn.close()
        metadata = json.loads(row[0])
        assert metadata["dimensions"] == 3072
        assert metadata["model"] == "text-embedding-3-large"

    def test_duplicate_name_raises(self, store):
        store.create_collection("uniek")
        with pytest.raises(sqlite3.IntegrityError):
            store.create_collection("uniek")


# ---------------------------------------------------------------------------
# Tests: store_chunk
# ---------------------------------------------------------------------------
class TestStoreChunk:
    def test_returns_chunk_id(self, store, collection_id, document_id):
        emb = _make_embedding(0)
        chunk_id = store.store_chunk(
            collection_id=collection_id,
            document_id=document_id,
            chunk_text="Artikel 1. De wet is van toepassing.",
            embedding=emb,
            chunk_index=0,
        )
        assert isinstance(chunk_id, int)
        assert chunk_id > 0

    def test_stores_all_metadata(self, store, collection_id, document_id, db_path):
        emb = _make_embedding(1)
        chunk_id = store.store_chunk(
            collection_id=collection_id,
            document_id=document_id,
            chunk_text="Artikel 2 lid 3.",
            embedding=emb,
            chunk_index=5,
            rechtsgebied="strafrecht",
            wet_regeling="Wetboek van Strafrecht",
            artikel_lid="art. 2 lid 3",
        )
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT chunk_text, chunk_index, rechtsgebied, wet_regeling, artikel_lid "
            "FROM rag_chunks WHERE id = ?",
            (chunk_id,),
        ).fetchone()
        conn.close()
        assert row[0] == "Artikel 2 lid 3."
        assert row[1] == 5
        assert row[2] == "strafrecht"
        assert row[3] == "Wetboek van Strafrecht"
        assert row[4] == "art. 2 lid 3"

    def test_embedding_roundtrip(self, store, collection_id, document_id):
        emb = _make_embedding(42)
        chunk_id = store.store_chunk(
            collection_id=collection_id,
            document_id=document_id,
            chunk_text="test",
            embedding=emb,
            chunk_index=0,
        )
        retrieved = store.get_embedding(chunk_id)
        np.testing.assert_array_almost_equal(retrieved, emb)

    def test_wrong_dimensions_raises(self, store, collection_id, document_id):
        wrong_emb = np.zeros(DIMS + 1, dtype=np.float32)
        with pytest.raises(ValueError, match="matcht niet"):
            store.store_chunk(
                collection_id=collection_id,
                document_id=document_id,
                chunk_text="test",
                embedding=wrong_emb,
                chunk_index=0,
            )

    def test_invalid_collection_raises(self, store, document_id):
        emb = _make_embedding(0)
        with pytest.raises(ValueError, match="niet gevonden"):
            store.store_chunk(
                collection_id=99999,
                document_id=document_id,
                chunk_text="test",
                embedding=emb,
                chunk_index=0,
            )

    def test_float64_converted_to_float32(self, store, collection_id, document_id):
        emb_f64 = np.random.randn(DIMS).astype(np.float64)
        chunk_id = store.store_chunk(
            collection_id=collection_id,
            document_id=document_id,
            chunk_text="float64 test",
            embedding=emb_f64,
            chunk_index=0,
        )
        retrieved = store.get_embedding(chunk_id)
        assert retrieved.dtype == np.float32
        np.testing.assert_array_almost_equal(retrieved, emb_f64.astype(np.float32))


# ---------------------------------------------------------------------------
# Tests: store_batch
# ---------------------------------------------------------------------------
class TestStoreBatch:
    def test_returns_chunk_ids(self, store, collection_id, document_id):
        chunks = [{"chunk_text": f"Chunk {i}", "chunk_index": i} for i in range(5)]
        embeddings = [_make_embedding(i) for i in range(5)]

        ids = store.store_batch(collection_id, document_id, chunks, embeddings)

        assert len(ids) == 5
        assert all(isinstance(i, int) for i in ids)
        assert ids == sorted(ids)  # Sequential IDs

    def test_batch_metadata_preserved(self, store, collection_id, document_id):
        chunks = [
            {
                "chunk_text": "Met metadata",
                "chunk_index": 0,
                "rechtsgebied": "bestuursrecht",
                "wet_regeling": "Awb",
                "artikel_lid": "art. 1:1",
            }
        ]
        embeddings = [_make_embedding(0)]

        store.store_batch(collection_id, document_id, chunks, embeddings)
        result = store.search_similar(_make_embedding(0), collection_id, top_k=1)
        assert result[0]["rechtsgebied"] == "bestuursrecht"

    def test_empty_batch(self, store, collection_id, document_id):
        ids = store.store_batch(collection_id, document_id, [], [])
        assert ids == []

    def test_mismatched_lengths_raises(self, store, collection_id, document_id):
        chunks = [{"chunk_text": "test", "chunk_index": 0}]
        embeddings = [_make_embedding(0), _make_embedding(1)]
        with pytest.raises(ValueError, match="matcht niet"):
            store.store_batch(collection_id, document_id, chunks, embeddings)

    def test_batch_validates_dimensions(self, store, collection_id, document_id):
        chunks = [{"chunk_text": "test", "chunk_index": 0}]
        wrong_emb = [np.zeros(DIMS + 1, dtype=np.float32)]
        with pytest.raises(ValueError, match="matcht niet"):
            store.store_batch(collection_id, document_id, chunks, wrong_emb)

    def test_batch_embeddings_retrievable(self, store, collection_id, document_id):
        chunks = [{"chunk_text": f"Chunk {i}", "chunk_index": i} for i in range(3)]
        embeddings = [_make_embedding(i) for i in range(3)]

        ids = store.store_batch(collection_id, document_id, chunks, embeddings)

        for chunk_id, expected_emb in zip(ids, embeddings, strict=True):
            retrieved = store.get_embedding(chunk_id)
            np.testing.assert_array_almost_equal(retrieved, expected_emb)


# ---------------------------------------------------------------------------
# Tests: search_similar
# ---------------------------------------------------------------------------
class TestSearchSimilar:
    def test_finds_most_similar(self, store, collection_id, document_id):
        # Store 3 chunks with known embeddings
        target = np.array([1.0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)
        similar = np.array([0.9, 0.1, 0, 0, 0, 0, 0, 0], dtype=np.float32)
        different = np.array([0, 0, 0, 0, 0, 0, 0, 1.0], dtype=np.float32)

        store.store_chunk(collection_id, document_id, "target", target, 0)
        store.store_chunk(collection_id, document_id, "similar", similar, 1)
        store.store_chunk(collection_id, document_id, "different", different, 2)

        results = store.search_similar(target, collection_id, top_k=3)

        assert len(results) == 3
        assert results[0]["chunk_text"] == "target"
        assert results[0]["score"] == pytest.approx(1.0, abs=1e-5)
        assert results[1]["chunk_text"] == "similar"
        assert results[2]["chunk_text"] == "different"
        assert results[2]["score"] == pytest.approx(0.0, abs=1e-5)

    def test_cosine_not_dot_product(self, store, collection_id, document_id):
        """Cosine similarity normaliseert — verschil met dot product."""
        # Two vectors: same direction, different magnitude
        short = np.array([1, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)
        long = np.array([10, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)

        store.store_chunk(collection_id, document_id, "short", short, 0)
        store.store_chunk(collection_id, document_id, "long", long, 1)

        query = np.array([5, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)
        results = store.search_similar(query, collection_id, top_k=2)

        # Both should have score ~1.0 (same direction)
        assert results[0]["score"] == pytest.approx(1.0, abs=1e-5)
        assert results[1]["score"] == pytest.approx(1.0, abs=1e-5)

    def test_returns_all_fields(self, store, collection_id, document_id):
        emb = _make_embedding(0)
        store.store_chunk(
            collection_id,
            document_id,
            "tekst",
            emb,
            0,
            rechtsgebied="civiel",
            wet_regeling="BW",
            artikel_lid="art. 6:1",
            bron_type="wetgeving",
            metadata={"artikel_nummer": "art. 6:1", "lid_nummer": "1"},
        )
        results = store.search_similar(emb, collection_id, top_k=1)
        result = results[0]

        expected_keys = {
            "chunk_id",
            "chunk_text",
            "score",
            "rechtsgebied",
            "wet_regeling",
            "artikel_lid",
            "bron_type",
            "metadata",
            "document_id",
            "chunk_index",
            "created_at",
        }
        assert set(result.keys()) == expected_keys
        assert result["rechtsgebied"] == "civiel"
        assert result["wet_regeling"] == "BW"
        assert result["artikel_lid"] == "art. 6:1"
        assert result["bron_type"] == "wetgeving"
        assert result["metadata"]["artikel_nummer"] == "art. 6:1"
        assert result["metadata"]["lid_nummer"] == "1"

    def test_top_k_limits_results(self, store, collection_id, document_id):
        for i in range(10):
            store.store_chunk(
                collection_id,
                document_id,
                f"chunk {i}",
                _make_embedding(i),
                i,
            )

        results = store.search_similar(_make_embedding(0), collection_id, top_k=3)
        assert len(results) == 3

    def test_top_k_larger_than_collection(self, store, collection_id, document_id):
        store.store_chunk(
            collection_id,
            document_id,
            "only one",
            _make_embedding(0),
            0,
        )
        results = store.search_similar(_make_embedding(0), collection_id, top_k=100)
        assert len(results) == 1

    def test_empty_collection_returns_empty(self, store, collection_id):
        results = store.search_similar(_make_embedding(0), collection_id, top_k=5)
        assert results == []

    def test_scores_descending(self, store, collection_id, document_id):
        for i in range(5):
            store.store_chunk(
                collection_id,
                document_id,
                f"chunk {i}",
                _make_embedding(i),
                i,
            )
        results = store.search_similar(_make_embedding(0), collection_id, top_k=5)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# Tests: get_embedding
# ---------------------------------------------------------------------------
class TestGetEmbedding:
    def test_returns_correct_embedding(self, store, collection_id, document_id):
        emb = _make_embedding(7)
        chunk_id = store.store_chunk(
            collection_id,
            document_id,
            "test",
            emb,
            0,
        )
        result = store.get_embedding(chunk_id)
        np.testing.assert_array_almost_equal(result, emb)

    def test_nonexistent_chunk_returns_none(self, store):
        assert store.get_embedding(99999) is None

    def test_returned_array_is_writable(self, store, collection_id, document_id):
        emb = _make_embedding(0)
        chunk_id = store.store_chunk(
            collection_id,
            document_id,
            "test",
            emb,
            0,
        )
        result = store.get_embedding(chunk_id)
        result[0] = 999.0  # Should not raise


# ---------------------------------------------------------------------------
# Tests: delete_collection_embeddings
# ---------------------------------------------------------------------------
class TestDeleteCollectionEmbeddings:
    def test_deletes_all_chunks(self, store, collection_id, document_id):
        for i in range(3):
            store.store_chunk(
                collection_id,
                document_id,
                f"chunk {i}",
                _make_embedding(i),
                i,
            )

        count = store.delete_collection_embeddings(collection_id)
        assert count == 3

        results = store.search_similar(_make_embedding(0), collection_id)
        assert results == []

    def test_returns_zero_for_empty_collection(self, store, collection_id):
        count = store.delete_collection_embeddings(collection_id)
        assert count == 0

    def test_does_not_affect_other_collections(
        self, store, collection_id, document_id, db_path
    ):
        # Create second collection + document
        cid2 = store.create_collection("other", dimensions=DIMS)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "INSERT INTO rag_documents (collection_id, filename) VALUES (?, ?)",
            (cid2, "other.pdf"),
        )
        doc2 = cursor.lastrowid
        conn.commit()
        conn.close()

        # Store chunks in both
        store.store_chunk(collection_id, document_id, "c1", _make_embedding(0), 0)
        store.store_chunk(cid2, doc2, "c2", _make_embedding(1), 0)

        # Delete only first collection
        store.delete_collection_embeddings(collection_id)

        assert store.search_similar(_make_embedding(0), collection_id) == []
        assert len(store.search_similar(_make_embedding(1), cid2)) == 1


# ---------------------------------------------------------------------------
# Tests: dimension validation
# ---------------------------------------------------------------------------
class TestDimensionValidation:
    def test_collection_without_metadata_skips_validation(self, store, db_path):
        """Collections zonder metadata_json: dimensievalidatie overgeslagen."""
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        cursor = conn.execute(
            "INSERT INTO rag_collections (collection_name) VALUES (?)",
            ("no_metadata",),
        )
        cid = cursor.lastrowid
        cursor = conn.execute(
            "INSERT INTO rag_documents (collection_id, filename) VALUES (?, ?)",
            (cid, "test.pdf"),
        )
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Should not raise — no dimensions to validate against
        emb = np.zeros(999, dtype=np.float32)
        chunk_id = store.store_chunk(cid, doc_id, "test", emb, 0)
        assert chunk_id > 0

    def test_negative_dimensions_rejected(self, store):
        with pytest.raises(ValueError, match="positief"):
            store.create_collection("bad", dimensions=-5)

    def test_zero_dimensions_rejected(self, store):
        with pytest.raises(ValueError, match="positief"):
            store.create_collection("bad", dimensions=0)

    def test_matching_dimensions_accepted(self, store, collection_id, document_id):
        emb = _make_embedding(0)
        assert emb.shape[0] == DIMS
        chunk_id = store.store_chunk(
            collection_id,
            document_id,
            "test",
            emb,
            0,
        )
        assert chunk_id > 0


# ---------------------------------------------------------------------------
# Tests: edge cases
# ---------------------------------------------------------------------------
class TestEdgeCases:
    def test_no_print_statements(self):
        """Acceptatiecriterium: 0 print() statements."""
        import ast
        import inspect

        import services.rag.embedding_store as mod

        source = inspect.getsource(mod)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "print"
            ):
                pytest.fail(f"Found print() on line {node.lineno}")

    def test_uses_logging(self):
        """Verifieert dat de module logging gebruikt."""
        import services.rag.embedding_store as mod

        assert hasattr(mod, "logger")

    def test_non_ndarray_embedding_raises(self, store, collection_id, document_id):
        with pytest.raises(TypeError, match=r"numpy\.ndarray"):
            store.store_chunk(
                collection_id,
                document_id,
                "test",
                [0.1] * DIMS,
                0,
            )

    def test_2d_embedding_raises(self, store, collection_id, document_id):
        emb_2d = np.zeros((1, DIMS), dtype=np.float32)
        with pytest.raises(ValueError, match="1-dimensionaal"):
            store.store_chunk(collection_id, document_id, "test", emb_2d, 0)

    @pytest.mark.parametrize("bad_text", ["", "   ", None])
    def test_empty_chunk_text_raises(self, store, collection_id, document_id, bad_text):
        emb = _make_embedding(0)
        with pytest.raises((ValueError, TypeError)):
            store.store_chunk(
                collection_id,
                document_id,
                bad_text,
                emb,
                0,
            )


# ---------------------------------------------------------------------------
# Tests: review items — ontbrekende tests
# ---------------------------------------------------------------------------
class TestReviewMissingTests:
    """Tests geidentificeerd in code review als ontbrekend."""

    def test_zero_norm_query_returns_empty(self, store, collection_id, document_id):
        """Zero-norm query vector moet [] teruggeven."""
        store.store_chunk(
            collection_id,
            document_id,
            "test",
            _make_embedding(0),
            0,
        )
        zero_query = np.zeros(DIMS, dtype=np.float32)
        results = store.search_similar(zero_query, collection_id)
        assert results == []

    def test_invalid_document_id_foreign_key(self, store, collection_id):
        """FK constraint: ongeldig document_id moet IntegrityError geven."""
        emb = _make_embedding(0)
        with pytest.raises(sqlite3.IntegrityError):
            store.store_chunk(
                collection_id,
                document_id=99999,
                chunk_text="test",
                embedding=emb,
                chunk_index=0,
            )

    def test_delete_nonexistent_collection_returns_zero(self, store):
        """Delete op niet-bestaande collection moet 0 teruggeven."""
        count = store.delete_collection_embeddings(99999)
        assert count == 0

    def test_connection_cleanup_after_error(self, store, collection_id, document_id):
        """Na een error moet de store nog bruikbaar zijn."""
        wrong_emb = np.zeros(DIMS + 1, dtype=np.float32)
        with pytest.raises(ValueError, match="matcht niet"):
            store.store_chunk(
                collection_id,
                document_id,
                "test",
                wrong_emb,
                0,
            )

        # Store moet nog werken na de error
        good_emb = _make_embedding(0)
        chunk_id = store.store_chunk(
            collection_id,
            document_id,
            "test",
            good_emb,
            0,
        )
        assert chunk_id > 0

    def test_store_batch_rollback_on_failure(self, store, collection_id, document_id):
        """Bij failure midden in batch mogen er geen partial inserts overblijven."""
        chunks = [
            {"chunk_text": "good chunk", "chunk_index": 0},
            {"chunk_text": "bad chunk", "chunk_index": 1},
        ]
        good_emb = _make_embedding(0)
        bad_emb = np.zeros(DIMS + 1, dtype=np.float32)  # Verkeerde dimensie

        with pytest.raises(ValueError, match="matcht niet"):
            store.store_batch(
                collection_id,
                document_id,
                chunks,
                [good_emb, bad_emb],
            )

        # Niets mag opgeslagen zijn
        results = store.search_similar(_make_embedding(0), collection_id)
        assert results == []

    def test_zero_norm_stored_embedding_gets_zero_score(
        self,
        store,
        collection_id,
        document_id,
    ):
        """Opgeslagen zero-vector moet score 0.0 krijgen, geen crash."""
        zero_emb = np.zeros(DIMS, dtype=np.float32)
        normal_emb = _make_embedding(42)

        store.store_chunk(collection_id, document_id, "zero", zero_emb, 0)
        store.store_chunk(collection_id, document_id, "normal", normal_emb, 1)

        results = store.search_similar(normal_emb, collection_id, top_k=2)
        assert len(results) == 2

        # De zero-vector moet score ~0.0 krijgen
        zero_result = next(r for r in results if r["chunk_text"] == "zero")
        assert zero_result["score"] == pytest.approx(0.0, abs=1e-5)


# ---------------------------------------------------------------------------
# Tests: JSONB metadata (DEF-370)
# ---------------------------------------------------------------------------
class TestMetadataJSONB:
    """Tests voor bron_type en JSONB metadata kolommen."""

    def test_store_chunk_with_metadata(
        self, store, collection_id, document_id, db_path
    ):
        """Metadata dict wordt opgeslagen als JSONB."""
        emb = _make_embedding(0)
        meta = {
            "artikel_nummer": "art. 1",
            "lid_nummer": "3",
            "structuur_type": "artikel",
        }
        chunk_id = store.store_chunk(
            collection_id,
            document_id,
            "Artikel 1 lid 3.",
            emb,
            0,
            bron_type="wetgeving",
            metadata=meta,
        )

        # Verifieer opslag in DB
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT bron_type, json(metadata) FROM rag_chunks WHERE id = ?",
            (chunk_id,),
        ).fetchone()
        conn.close()

        assert row[0] == "wetgeving"
        stored_meta = json.loads(row[1])
        assert stored_meta["artikel_nummer"] == "art. 1"
        assert stored_meta["lid_nummer"] == "3"

    def test_store_chunk_without_metadata_defaults_empty(
        self, store, collection_id, document_id, db_path
    ):
        """Zonder metadata → lege dict als JSONB opgeslagen."""
        emb = _make_embedding(0)
        chunk_id = store.store_chunk(collection_id, document_id, "test", emb, 0)

        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT json(metadata) FROM rag_chunks WHERE id = ?",
            (chunk_id,),
        ).fetchone()
        conn.close()

        stored_meta = json.loads(row[0])
        assert stored_meta == {}

    def test_store_batch_with_metadata(self, store, collection_id, document_id):
        """Batch store met bron_type en metadata."""
        chunks = [
            {
                "chunk_text": "Artikel 1",
                "chunk_index": 0,
                "bron_type": "wetgeving",
                "metadata": {"artikel_nummer": "art. 1"},
            },
            {
                "chunk_text": "Pagina 2",
                "chunk_index": 1,
                "bron_type": "pdf",
                "metadata": {"pagina_nummer": 2, "bronbestand": "doc.pdf"},
            },
        ]
        embeddings = [_make_embedding(i) for i in range(2)]

        ids = store.store_batch(collection_id, document_id, chunks, embeddings)
        assert len(ids) == 2

        results = store.search_similar(_make_embedding(0), collection_id, top_k=2)
        bron_types = {r["bron_type"] for r in results}
        assert "wetgeving" in bron_types
        assert "pdf" in bron_types

    def test_search_returns_parsed_metadata(self, store, collection_id, document_id):
        """search_similar() retourneert metadata als dict, niet als string."""
        emb = _make_embedding(0)
        meta = {"artikel_nummer": "art. 5", "structuur_type": "lid"}
        store.store_chunk(collection_id, document_id, "test", emb, 0, metadata=meta)

        results = store.search_similar(emb, collection_id, top_k=1)
        assert isinstance(results[0]["metadata"], dict)
        assert results[0]["metadata"]["artikel_nummer"] == "art. 5"

    def test_search_metadata_fallback_artikel_lid(
        self, store, collection_id, document_id
    ):
        """Legacy data: artikel_lid kolom als fallback als metadata leeg is."""
        emb = _make_embedding(0)
        # Sla op met artikel_lid maar zonder metadata.artikel_nummer
        store.store_chunk(
            collection_id,
            document_id,
            "legacy chunk",
            emb,
            0,
            artikel_lid="art. 42",
        )

        results = store.search_similar(emb, collection_id, top_k=1)
        # Fallback: artikel_lid moet gevuld zijn vanuit de legacy kolom
        assert results[0]["artikel_lid"] == "art. 42"

    def test_search_metadata_artikel_nummer_overrides_legacy(
        self, store, collection_id, document_id
    ):
        """metadata.artikel_nummer heeft prioriteit boven legacy artikel_lid kolom."""
        emb = _make_embedding(0)
        store.store_chunk(
            collection_id,
            document_id,
            "new style chunk",
            emb,
            0,
            artikel_lid="old_value",
            metadata={"artikel_nummer": "new_value"},
        )

        results = store.search_similar(emb, collection_id, top_k=1)
        assert results[0]["artikel_lid"] == "new_value"

    def test_search_empty_metadata_returns_empty_dict(
        self, store, collection_id, document_id
    ):
        """Chunk zonder metadata → lege dict in search resultaat."""
        emb = _make_embedding(0)
        store.store_chunk(collection_id, document_id, "no meta", emb, 0)

        results = store.search_similar(emb, collection_id, top_k=1)
        assert results[0]["metadata"] == {}
        assert results[0]["bron_type"] is None

    def test_parse_metadata_edge_cases(self):
        """_parse_metadata helper edge cases."""
        assert EmbeddingStore._parse_metadata(None) == {}
        assert EmbeddingStore._parse_metadata("") == {}
        assert EmbeddingStore._parse_metadata("invalid json") == {}
        assert EmbeddingStore._parse_metadata("[]") == {}
        assert EmbeddingStore._parse_metadata('{"key": "val"}') == {"key": "val"}
