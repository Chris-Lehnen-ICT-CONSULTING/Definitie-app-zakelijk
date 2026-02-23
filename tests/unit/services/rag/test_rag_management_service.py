"""Tests voor RAGManagementService (DEF-365)."""

from __future__ import annotations

import json
import sqlite3

import numpy as np
import pytest

from services.rag.embedding_store import EmbeddingStore
from services.rag.rag_management_service import RAGManagementService

# ---------------------------------------------------------------------------
# Schema (mirrors v5_migration tables)
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
"""

DIMS = 8


@pytest.fixture
def db_path(tmp_path):
    """SQLite DB met RAG schema."""
    path = str(tmp_path / "test.db")
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA_SQL)
    conn.close()
    return path


@pytest.fixture
def store(db_path):
    return EmbeddingStore(db_path=db_path)


@pytest.fixture
def service(db_path, store):
    return RAGManagementService(db_path=db_path, embedding_store=store)


@pytest.fixture
def collection_id(store):
    """Maak test-collection aan met type metadata."""
    return store.create_collection(
        "test-collectie",
        dimensions=DIMS,
        model="test",
        extra_metadata={"type": "wetgeving"},
    )


@pytest.fixture
def doc_id(db_path, collection_id):
    """Insert een test-document."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "INSERT INTO rag_documents "
        "(collection_id, filename, file_type, chunk_count, rechtsgebied) "
        "VALUES (?, 'test.pdf', 'application/pdf', 2, 'strafrecht')",
        (collection_id,),
    )
    conn.commit()
    did = cursor.lastrowid
    conn.close()
    return did


# ---------------------------------------------------------------------------
# list_collections
# ---------------------------------------------------------------------------
class TestListCollections:
    def test_empty(self, service):
        """Lege database geeft lege lijst."""
        assert service.list_collections() == []

    def test_with_data(self, service, collection_id):
        """Collection met metadata wordt correct gelist."""
        result = service.list_collections()
        assert len(result) == 1
        coll = result[0]
        assert coll["id"] == collection_id
        assert coll["name"] == "test-collectie"
        assert coll["type_key"] == "wetgeving"
        assert coll["type_label"] == "Wetgeving"
        assert coll["document_count"] == 0
        assert coll["chunk_count"] == 0

    def test_live_counts(self, service, collection_id, doc_id, db_path, store):
        """Document/chunk counts worden live geteld."""
        emb = np.random.randn(DIMS).astype(np.float32)
        store.store_batch(
            collection_id=collection_id,
            document_id=doc_id,
            chunks=[{"chunk_text": "Test chunk", "chunk_index": 0}],
            embeddings=[emb],
        )

        result = service.list_collections()
        coll = result[0]
        assert coll["document_count"] == 1
        assert coll["chunk_count"] == 1

    def test_default_type_vrij(self, store, db_path):
        """Collection zonder type metadata krijgt default 'vrij'."""
        # Maak collection zonder extra_metadata
        store.create_collection("bare", dimensions=DIMS, model="test")
        svc = RAGManagementService(db_path=db_path, embedding_store=store)
        result = svc.list_collections()
        bare = next(c for c in result if c["name"] == "bare")
        assert bare["type_key"] == "vrij"


# ---------------------------------------------------------------------------
# create_collection
# ---------------------------------------------------------------------------
class TestCreateCollection:
    def test_basic(self, service, db_path):
        """Nieuwe collection wordt aangemaakt met type metadata."""
        cid = service.create_collection("nieuwe", collection_type="beleid")
        assert cid > 0

        # Verifieer metadata
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT metadata_json FROM rag_collections WHERE id = ?", (cid,)
        ).fetchone()
        conn.close()
        meta = json.loads(row[0])
        assert meta["type"] == "beleid"
        assert meta["dimensions"] > 0

    def test_with_rechtsgebied(self, service, db_path):
        """Rechtsgebied wordt opgeslagen in metadata."""
        cid = service.create_collection("strafrechtdocs", rechtsgebied="strafrecht")
        conn = sqlite3.connect(db_path)
        meta = json.loads(
            conn.execute(
                "SELECT metadata_json FROM rag_collections WHERE id = ?", (cid,)
            ).fetchone()[0]
        )
        conn.close()
        assert meta["rechtsgebied"] == "strafrecht"

    def test_duplicate_name_raises(self, service, collection_id):
        """Duplicate collection naam geeft IntegrityError."""
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
            service.create_collection("test-collectie")


# ---------------------------------------------------------------------------
# delete_collection
# ---------------------------------------------------------------------------
class TestDeleteCollection:
    def test_cascade_deletes_docs_and_chunks(
        self, service, collection_id, doc_id, store, db_path
    ):
        """Delete cascade verwijdert documenten en chunks."""
        emb = np.random.randn(DIMS).astype(np.float32)
        store.store_batch(
            collection_id=collection_id,
            document_id=doc_id,
            chunks=[{"chunk_text": "Chunk", "chunk_index": 0}],
            embeddings=[emb],
        )

        result = service.delete_collection(collection_id)
        assert result is True

        conn = sqlite3.connect(db_path)
        assert conn.execute("SELECT COUNT(*) FROM rag_collections").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM rag_documents").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()[0] == 0
        conn.close()

    def test_deletes_files(self, service, collection_id, db_path, tmp_path):
        """Delete verwijdert bestanden van schijf."""
        upload = tmp_path / "test_upload.pdf"
        upload.write_text("dummy")

        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO rag_documents "
            "(collection_id, filename, chunk_count, file_path) "
            "VALUES (?, 'test.pdf', 0, ?)",
            (collection_id, str(upload)),
        )
        conn.commit()
        conn.close()

        service.delete_collection(collection_id)
        assert not upload.exists()

    def test_nonexistent_returns_false(self, service):
        """Verwijderen van niet-bestaande collection retourneert False."""
        assert service.delete_collection(99999) is False


# ---------------------------------------------------------------------------
# list_documents
# ---------------------------------------------------------------------------
class TestListDocuments:
    def test_empty(self, service, collection_id):
        assert service.list_documents(collection_id) == []

    def test_with_doc(self, service, collection_id, doc_id):
        docs = service.list_documents(collection_id)
        assert len(docs) == 1
        assert docs[0]["id"] == doc_id
        assert docs[0]["filename"] == "test.pdf"
        assert docs[0]["rechtsgebied"] == "strafrecht"


# ---------------------------------------------------------------------------
# delete_document
# ---------------------------------------------------------------------------
class TestDeleteDocument:
    def test_cascade_deletes_chunks(
        self, service, collection_id, doc_id, store, db_path
    ):
        """Delete document cascade verwijdert bijbehorende chunks."""
        emb = np.random.randn(DIMS).astype(np.float32)
        store.store_batch(
            collection_id=collection_id,
            document_id=doc_id,
            chunks=[{"chunk_text": "Test", "chunk_index": 0}],
            embeddings=[emb],
        )

        result = service.delete_document(doc_id)
        assert result is True

        conn = sqlite3.connect(db_path)
        assert conn.execute("SELECT COUNT(*) FROM rag_documents").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()[0] == 0
        conn.close()

    def test_deletes_file(self, service, collection_id, db_path, tmp_path):
        """Delete document verwijdert bestand van schijf."""
        upload = tmp_path / "doc.pdf"
        upload.write_text("dummy")

        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "INSERT INTO rag_documents "
            "(collection_id, filename, chunk_count, file_path) "
            "VALUES (?, 'doc.pdf', 0, ?)",
            (collection_id, str(upload)),
        )
        conn.commit()
        did = cursor.lastrowid
        conn.close()

        service.delete_document(did)
        assert not upload.exists()

    def test_nonexistent_returns_false(self, service):
        assert service.delete_document(99999) is False


# ---------------------------------------------------------------------------
# check_duplicate_document
# ---------------------------------------------------------------------------
class TestCheckDuplicateDocument:
    def test_no_duplicate(self, service, collection_id):
        assert service.check_duplicate_document(collection_id, "new.pdf") is False

    def test_has_duplicate(self, service, collection_id, doc_id):
        assert service.check_duplicate_document(collection_id, "test.pdf") is True

    def test_different_collection(self, service, store, doc_id):
        """Duplicate check is collection-scoped."""
        other_cid = store.create_collection("other", dimensions=DIMS, model="test")
        assert service.check_duplicate_document(other_cid, "test.pdf") is False
