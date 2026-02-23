"""Tests voor RAGService (DEF-291)."""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from services.rag.models import ChunkingResult, ChunkMetadata, DocumentChunk
from services.rag.rag_service import RAGContext, RAGService

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


def _make_embedding(seed: int = 0, dims: int = DIMS) -> np.ndarray:
    rng = np.random.RandomState(seed)
    return rng.randn(dims).astype(np.float32)


def _make_chunk(
    tekst: str, index: int, rechtsgebied: str | None = None
) -> DocumentChunk:
    return DocumentChunk(
        tekst=tekst,
        metadata=ChunkMetadata(
            bronbestand="test.pdf",
            chunk_index=index,
            rechtsgebied=rechtsgebied,
            wet_regeling=None,
            artikel_nummer=None,
        ),
        token_count=len(tekst.split()),
    )


@pytest.fixture
def db_path(tmp_path):
    """In-memory-achtige SQLite DB met schema."""
    path = str(tmp_path / "test.db")
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA_SQL)
    conn.close()
    return path


@pytest.fixture
def mock_chunker():
    return MagicMock(spec=["chunk_tekst"])


@pytest.fixture
def mock_embedder():
    embedder = MagicMock(spec=["embed", "embed_batch", "DIMENSIONS", "MODEL"])
    embedder.DIMENSIONS = DIMS
    embedder.MODEL = "test-model"
    return embedder


@pytest.fixture
def store(db_path):
    """Echte EmbeddingStore met test DB."""
    from services.rag.embedding_store import EmbeddingStore

    return EmbeddingStore(db_path=db_path)


@pytest.fixture
def service(mock_chunker, mock_embedder, store, db_path):
    return RAGService(
        document_chunker=mock_chunker,
        embedding_service=mock_embedder,
        embedding_store=store,
        db_path=db_path,
    )


@pytest.fixture
def collection_id(store):
    """Maak een test-collection aan."""
    return store.create_collection("test-collectie", dimensions=DIMS, model="test")


# ---------------------------------------------------------------------------
# _ensure_collection
# ---------------------------------------------------------------------------
class TestEnsureCollection:
    def test_creates_new_collection(self, service, db_path):
        """Nieuwe collection wordt aangemaakt als die niet bestaat."""
        with patch.object(
            service._store,
            "create_collection",
            return_value=42,
        ) as mock_create:
            cid = service._ensure_collection("nieuwe-collectie")
            assert cid == 42
            mock_create.assert_called_once()

    def test_returns_existing_collection(self, service, collection_id):
        """Bestaande collection wordt niet opnieuw aangemaakt."""
        cid = service._ensure_collection("test-collectie")
        assert cid == collection_id


# ---------------------------------------------------------------------------
# ingest_document
# ---------------------------------------------------------------------------
class TestIngestDocument:
    def test_happy_path(
        self, service, mock_chunker, mock_embedder, collection_id, db_path
    ):
        """Ingest chunked, embed en slaat op in één call."""
        chunks = [_make_chunk("Eerste chunk.", 0), _make_chunk("Tweede chunk.", 1)]
        mock_chunker.chunk_tekst.return_value = ChunkingResult(
            chunks=tuple(chunks),
            bronbestand="wet.pdf",
            bestandstype="application/pdf",
            totaal_tokens=10,
        )
        embeddings = [_make_embedding(0), _make_embedding(1)]
        mock_embedder.embed_batch.return_value = embeddings

        doc_id = service.ingest_document(
            tekst="Eerste chunk. Tweede chunk.",
            collection_id=collection_id,
            filename="wet.pdf",
            file_type="application/pdf",
            rechtsgebied="bestuursrecht",
        )

        assert doc_id > 0
        mock_chunker.chunk_tekst.assert_called_once()
        mock_embedder.embed_batch.assert_called_once_with(
            ["Eerste chunk.", "Tweede chunk."]
        )

        # Verifieer rag_documents rij
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT filename, chunk_count, rechtsgebied FROM rag_documents WHERE id = ?",
            (doc_id,),
        ).fetchone()
        conn.close()
        assert row[0] == "wet.pdf"
        assert row[1] == 2
        assert row[2] == "bestuursrecht"

    def test_empty_text_raises(self, service, collection_id):
        """Lege tekst geeft ValueError."""
        with pytest.raises(ValueError, match="tekst mag niet leeg"):
            service.ingest_document("", collection_id, "test.txt")

        with pytest.raises(ValueError, match="tekst mag niet leeg"):
            service.ingest_document("   ", collection_id, "test.txt")

    def test_chunking_error_rolls_back(
        self, service, mock_chunker, collection_id, db_path
    ):
        """Bij chunking-fout wordt rag_documents rij verwijderd."""
        mock_chunker.chunk_tekst.return_value = ChunkingResult(
            bronbestand="fout.pdf",
            bestandstype="application/pdf",
            fout_melding="Chunking fout!",
        )

        with pytest.raises(RuntimeError, match="Chunking mislukt"):
            service.ingest_document("Tekst", collection_id, "fout.pdf")

        # Geen orphan documents
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM rag_documents").fetchone()[0]
        conn.close()
        assert count == 0

    def test_embed_error_rolls_back(
        self, service, mock_chunker, mock_embedder, collection_id, db_path
    ):
        """Bij embed-failure wordt rag_documents rij verwijderd (alles-of-niets)."""
        chunks = [_make_chunk("Chunk tekst.", 0)]
        mock_chunker.chunk_tekst.return_value = ChunkingResult(
            chunks=tuple(chunks),
            bronbestand="test.pdf",
            bestandstype="application/pdf",
            totaal_tokens=5,
        )
        mock_embedder.embed_batch.side_effect = RuntimeError("API error")

        with pytest.raises(RuntimeError, match="API error"):
            service.ingest_document("Chunk tekst.", collection_id, "test.pdf")

        conn = sqlite3.connect(db_path)
        doc_count = conn.execute("SELECT COUNT(*) FROM rag_documents").fetchone()[0]
        chunk_count = conn.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()[0]
        conn.close()
        assert doc_count == 0
        assert chunk_count == 0

    def test_zero_chunks_rolls_back(
        self, service, mock_chunker, collection_id, db_path
    ):
        """0 chunks resultaat wordt als fout behandeld."""
        mock_chunker.chunk_tekst.return_value = ChunkingResult(
            chunks=(),
            bronbestand="leeg.pdf",
            bestandstype="application/pdf",
            totaal_tokens=0,
        )

        with pytest.raises(RuntimeError, match="0 chunks"):
            service.ingest_document("Tekst", collection_id, "leeg.pdf")

        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM rag_documents").fetchone()[0]
        conn.close()
        assert count == 0


# ---------------------------------------------------------------------------
# retrieve_context
# ---------------------------------------------------------------------------
class TestRetrieveContext:
    def test_returns_rag_context(
        self, service, mock_chunker, mock_embedder, store, collection_id
    ):
        """retrieve_context retourneert RAGContext met chunks en formatted string."""
        # Seed data: sla 2 chunks op
        emb1 = _make_embedding(10)
        emb2 = _make_embedding(20)
        conn = sqlite3.connect(service._db_path)
        conn.execute(
            "INSERT INTO rag_documents (collection_id, filename, chunk_count) VALUES (?, 'doc.pdf', 2)",
            (collection_id,),
        )
        conn.commit()
        doc_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        store.store_batch(
            collection_id=collection_id,
            document_id=doc_id,
            chunks=[
                {"chunk_text": "Artikel 1 lid 1", "chunk_index": 0},
                {"chunk_text": "Artikel 2 lid 1", "chunk_index": 1},
            ],
            embeddings=[emb1, emb2],
        )

        # Query embedding die dicht bij emb1 ligt
        mock_embedder.embed.return_value = emb1

        ctx = service.retrieve_context("artikel 1", collection_id, top_k=2)

        assert isinstance(ctx, RAGContext)
        assert ctx.query == "artikel 1"
        assert ctx.collection_id == collection_id
        assert len(ctx.chunks) == 2
        assert ctx.chunks[0]["chunk_text"] in ("Artikel 1 lid 1", "Artikel 2 lid 1")
        assert ctx.formatted_context  # niet leeg
        assert "<bronnen>" in ctx.formatted_context
        assert "<bron " in ctx.formatted_context

    def test_empty_query_returns_empty(self, service, collection_id):
        """Lege query retourneert lege RAGContext."""
        ctx = service.retrieve_context("", collection_id)
        assert ctx.chunks == []
        assert ctx.formatted_context == ""

    def test_whitespace_query_returns_empty(self, service, collection_id):
        """Alleen whitespace retourneert lege RAGContext."""
        ctx = service.retrieve_context("   ", collection_id)
        assert ctx.chunks == []


# ---------------------------------------------------------------------------
# get_collection_stats
# ---------------------------------------------------------------------------
class TestGetCollectionStats:
    def test_returns_stats(self, service, collection_id):
        """get_collection_stats retourneert correct dict."""
        stats = service.get_collection_stats(collection_id)

        assert stats["collection_id"] == collection_id
        assert stats["name"] == "test-collectie"
        assert stats["document_count"] == 0
        assert stats["chunk_count"] == 0
        assert stats["dimensions"] == DIMS
        assert stats["model"] == "test"

    def test_nonexistent_collection_raises(self, service):
        """Niet-bestaande collection geeft ValueError."""
        with pytest.raises(ValueError, match="niet gevonden"):
            service.get_collection_stats(99999)


# ---------------------------------------------------------------------------
# _format_context
# ---------------------------------------------------------------------------
class TestFormatContext:
    def test_empty_list(self, service):
        assert service._format_context([]) == ""

    def test_xml_structure(self, service):
        """Output is valid XML met <bronnen><bron> tags."""
        result = service._format_context([{"chunk_text": "Tekst hier.", "score": 0.91}])
        assert result.startswith("<bronnen>")
        assert result.endswith("</bronnen>")
        assert "<bron " in result
        assert "</bron>" in result
        assert "Tekst hier." in result

    def test_type_rag_attribute(self, service):
        """Elke <bron> krijgt type='rag' attribuut (DEF-315 compatible)."""
        result = service._format_context([{"chunk_text": "X", "score": 0.5}])
        assert 'type="rag"' in result

    def test_score_attribute(self, service):
        result = service._format_context([{"chunk_text": "X", "score": 0.8567}])
        assert 'score="0.86"' in result

    def test_metadata_as_attributes(self, service):
        result = service._format_context(
            [
                {
                    "chunk_text": "Art. 1",
                    "score": 0.92,
                    "rechtsgebied": "bestuursrecht",
                    "wet_regeling": "Awb",
                    "artikel_lid": "1:3",
                }
            ]
        )
        assert 'rechtsgebied="bestuursrecht"' in result
        assert 'regeling="Awb"' in result
        assert 'artikel="1:3"' in result

    def test_optional_attributes_omitted(self, service):
        """Lege metadata wordt niet als attribuut opgenomen."""
        result = service._format_context([{"chunk_text": "Tekst", "score": 0.5}])
        assert "rechtsgebied=" not in result
        assert "regeling=" not in result
        assert "artikel=" not in result

    def test_multiple_chunks_numbered(self, service):
        result = service._format_context(
            [
                {"chunk_text": "A", "score": 0.9},
                {"chunk_text": "B", "score": 0.8},
            ]
        )
        assert 'nr="1"' in result
        assert 'nr="2"' in result
        assert result.count("<bron ") == 2
        assert result.count("</bron>") == 2

    def test_escapes_xml_special_chars_in_text(self, service):
        """XML-speciale tekens in chunk_text worden ge-escaped."""
        result = service._format_context(
            [{"chunk_text": 'Art. 1 lid <3> & "bijlage"', "score": 0.9}]
        )
        assert "&lt;3&gt;" in result
        assert "&amp;" in result
        # Originele onveilige tekens mogen NIET voorkomen in de body
        assert "<3>" not in result

    def test_escapes_xml_special_chars_in_attributes(self, service):
        """XML-speciale tekens in attributen worden ge-escaped via quoteattr."""
        result = service._format_context(
            [
                {
                    "chunk_text": "Tekst",
                    "score": 0.8,
                    "rechtsgebied": 'recht & "plicht"',
                    "wet_regeling": "BW <boek 7>",
                    "artikel_lid": "1&2",
                }
            ]
        )
        # quoteattr escaped & < > " en kiest juiste quoting
        assert "recht &amp; " in result
        assert "BW &lt;boek 7&gt;" in result
        assert "1&amp;2" in result


# ---------------------------------------------------------------------------
# RAGContext dataclass
# ---------------------------------------------------------------------------
class TestRAGContext:
    def test_frozen(self):
        ctx = RAGContext(chunks=[], formatted_context="", collection_id=1, query="q")
        with pytest.raises(AttributeError):
            ctx.query = "mutated"


# ---------------------------------------------------------------------------
# cleanup_all_documents (DEF-358)
# ---------------------------------------------------------------------------
class TestCleanupAllDocuments:
    def test_leeg_scenario(self, service):
        """Cleanup op lege database retourneert 0."""
        count = service.cleanup_all_documents()
        assert count == 0

    def test_verwijdert_documenten(
        self, service, mock_chunker, mock_embedder, store, collection_id, db_path
    ):
        """Cleanup verwijdert alle documenten en retourneert correct aantal."""
        # Seed: voeg 2 documenten toe
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO rag_documents (collection_id, filename, chunk_count) "
            "VALUES (?, 'a.pdf', 1)",
            (collection_id,),
        )
        conn.execute(
            "INSERT INTO rag_documents (collection_id, filename, chunk_count) "
            "VALUES (?, 'b.pdf', 1)",
            (collection_id,),
        )
        conn.commit()
        conn.close()

        count = service.cleanup_all_documents()
        assert count == 2

        # Verifieer database leeg
        conn = sqlite3.connect(db_path)
        remaining = conn.execute("SELECT COUNT(*) FROM rag_documents").fetchone()[0]
        conn.close()
        assert remaining == 0

    def test_cascade_verwijdert_chunks(
        self, service, mock_chunker, mock_embedder, store, collection_id, db_path
    ):
        """Cleanup cascade verwijdert ook bijbehorende chunks."""
        # Seed: document + chunks
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO rag_documents (id, collection_id, filename, chunk_count) "
            "VALUES (100, ?, 'test.pdf', 1)",
            (collection_id,),
        )
        conn.commit()
        conn.close()

        emb = np.random.randn(DIMS).astype(np.float32)
        store.store_batch(
            collection_id=collection_id,
            document_id=100,
            chunks=[{"chunk_text": "Test chunk", "chunk_index": 0}],
            embeddings=[emb],
        )

        # Verifieer chunks bestaan
        conn = sqlite3.connect(db_path)
        chunk_count = conn.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()[0]
        conn.close()
        assert chunk_count > 0

        service.cleanup_all_documents()

        # Chunks moeten ook weg zijn (CASCADE)
        conn = sqlite3.connect(db_path)
        chunk_count = conn.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()[0]
        conn.close()
        assert chunk_count == 0

    def test_verwijdert_upload_bestanden(
        self, service, collection_id, db_path, tmp_path
    ):
        """Cleanup verwijdert ook bestanden van schijf via file_path."""
        # Maak een tijdelijk bestand aan
        upload_file = tmp_path / "test_upload.pdf"
        upload_file.write_text("dummy content")
        assert upload_file.exists()

        # Seed: document met file_path
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO rag_documents "
            "(collection_id, filename, chunk_count, file_path) "
            "VALUES (?, 'test.pdf', 0, ?)",
            (collection_id, str(upload_file)),
        )
        conn.commit()
        conn.close()

        service.cleanup_all_documents()

        # Bestand moet van schijf verwijderd zijn
        assert not upload_file.exists()
