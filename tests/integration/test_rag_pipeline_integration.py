"""DEF-271: Integratie tests voor RAG pipeline.

Test de volledige keten: document ingest → embedding → store → retrieve → prompt injectie.
Gebruikt mock embeddings (geen OpenAI API calls nodig).
"""

import os
import sqlite3
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from services.rag.document_chunker import DocumentChunker
from services.rag.embedding_service import EmbeddingService
from services.rag.embedding_store import EmbeddingStore
from services.rag.rag_service import RAGContext, RAGService
from utils.xml_source_formatter import (
    confidence_to_level,
    format_bron,
    wrap_bronnen,
)

DIMENSIONS = EmbeddingService.DIMENSIONS  # 3072


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _random_embedding(seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    vec = rng.standard_normal(DIMENSIONS).astype(np.float32)
    return vec / np.linalg.norm(vec)


def _similar_embedding(base: np.ndarray, noise_scale: float = 0.05) -> np.ndarray:
    rng = np.random.default_rng(99)
    noise = rng.standard_normal(DIMENSIONS).astype(np.float32) * noise_scale
    vec = base + noise
    return vec / np.linalg.norm(vec)


def _distant_embedding(base: np.ndarray) -> np.ndarray:
    """Create vector nearly orthogonal to base."""
    rng = np.random.default_rng(12345)
    vec = rng.standard_normal(DIMENSIONS).astype(np.float32)
    # Remove component in base direction
    vec = vec - np.dot(vec, base) * base
    return vec / np.linalg.norm(vec)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def rag_db():
    """Temp SQLite database met RAG tabellen."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS rag_collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_name VARCHAR(255) NOT NULL UNIQUE,
            document_count INTEGER DEFAULT 0,
            chunk_count INTEGER DEFAULT 0,
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_chunks_collection ON rag_chunks(collection_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_document ON rag_chunks(document_id);
        PRAGMA foreign_keys=ON;
    """
    )
    conn.close()

    yield db_path
    os.unlink(db_path)


@pytest.fixture
def mock_embedding_service():
    """Mock EmbeddingService — geen OpenAI calls."""
    svc = MagicMock(spec=EmbeddingService)
    svc.DIMENSIONS = DIMENSIONS
    svc.MODEL = "text-embedding-3-large"

    # embed_batch retourneert random embeddings per chunk
    def _embed_batch(texts):
        return [_random_embedding(seed=i) for i in range(len(texts))]

    svc.embed_batch.side_effect = _embed_batch
    svc.embed.side_effect = lambda q: _random_embedding(seed=hash(q) % 10000)
    return svc


@pytest.fixture
def embedding_store(rag_db):
    return EmbeddingStore(db_path=rag_db)


@pytest.fixture
def rag_service(rag_db, mock_embedding_service, embedding_store):
    chunker = DocumentChunker()
    return RAGService(
        document_chunker=chunker,
        embedding_service=mock_embedding_service,
        embedding_store=embedding_store,
        db_path=rag_db,
    )


@pytest.fixture
def collection_id(rag_service):
    return rag_service._ensure_collection("test_collection")


@pytest.fixture
def sample_juridisch_document():
    return (
        "Wet op de gemeentelijke basisadministratie persoonsgegevens\n\n"
        "HOOFDSTUK 1. ALGEMENE BEPALINGEN\n\n"
        "Artikel 1\n"
        "In deze wet wordt verstaan onder:\n"
        "a. basisregistratie: een registratie als bedoeld in artikel 2;\n"
        "b. ingezetene: degene die zijn adres heeft in een gemeente;\n"
        "c. niet-ingezetene: degene die zijn adres heeft buiten Nederland;\n"
        "d. persoonsgegeven: elk gegeven betreffende een geidentificeerde of "
        "identificeerbare natuurlijke persoon.\n\n"
        "Artikel 2\n"
        "1. Er is een basisregistratie personen.\n"
        "2. De basisregistratie personen heeft tot doel de overheid te voorzien "
        "van betrouwbare persoonsgegevens.\n"
        "3. De basisregistratie personen bevat persoonsgegevens over ingezetenen "
        "en niet-ingezetenen.\n\n"
        "Artikel 3\n"
        "Het college van de gemeente is verantwoordelijk voor het bijhouden van "
        "persoonsgegevens over de ingezetenen van die gemeente.\n"
    )


# ===========================================================================
# Test 1: Happy path — ingest + retrieve
# ===========================================================================
@pytest.mark.integration
class TestRAGIngestAndRetrieve:
    def test_ingest_creates_chunks(
        self, rag_service, collection_id, sample_juridisch_document
    ):
        doc_id = rag_service.ingest_document(
            tekst=sample_juridisch_document,
            collection_id=collection_id,
            filename="wet_brp.txt",
            rechtsgebied="publiekrecht",
        )
        assert doc_id > 0

        stats = rag_service.get_collection_stats(collection_id)
        assert stats["document_count"] == 1
        assert stats["chunk_count"] > 0

    def test_retrieve_returns_chunks(
        self,
        rag_service,
        mock_embedding_service,
        embedding_store,
        collection_id,
        sample_juridisch_document,
        rag_db,
    ):
        rag_service.ingest_document(
            tekst=sample_juridisch_document,
            collection_id=collection_id,
            filename="wet_brp.txt",
        )

        # Haal opgeslagen embeddings op
        conn = sqlite3.connect(rag_db)
        row = conn.execute(
            "SELECT embedding FROM rag_chunks WHERE collection_id = ? LIMIT 1",
            (collection_id,),
        ).fetchone()
        conn.close()
        stored_vec = np.frombuffer(row[0], dtype=np.float32).copy()

        # Mock embed() om vergelijkbare vector te retourneren
        mock_embedding_service.embed.side_effect = None
        mock_embedding_service.embed.return_value = _similar_embedding(stored_vec, 0.01)

        ctx = rag_service.retrieve_context(
            query="Wat is een ingezetene?",
            collection_id=collection_id,
            top_k=5,
        )

        assert isinstance(ctx, RAGContext)
        assert len(ctx.chunks) > 0
        for chunk in ctx.chunks:
            assert "score" in chunk
            assert isinstance(chunk["score"], float)
            assert "chunk_text" in chunk

    def test_ingest_creates_document_record(self, rag_service, collection_id, rag_db):
        doc_id = rag_service.ingest_document(
            tekst="Artikel 1\nEenvoudige testtekst voor registratie.",
            collection_id=collection_id,
            filename="registratie_test.txt",
            file_type="text/plain",
            rechtsgebied="civielrecht",
        )

        conn = sqlite3.connect(rag_db)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM rag_documents WHERE id = ?", (doc_id,)
        ).fetchone()
        conn.close()

        assert row is not None
        assert row["filename"] == "registratie_test.txt"
        assert row["rechtsgebied"] == "civielrecht"


# ===========================================================================
# Test 2: XML formatting
# ===========================================================================
@pytest.mark.integration
class TestRAGChunksInPromptInjection:
    def test_format_context_produces_xml(self, rag_service):
        chunks = [
            {
                "chunk_text": "Er is een basisregistratie personen.",
                "score": 0.92,
                "rechtsgebied": "publiekrecht",
                "wet_regeling": "Wet BRP",
                "artikel_lid": "Artikel 2 lid 1",
            },
            {
                "chunk_text": "Ingezetene is degene die zijn adres heeft in een gemeente.",
                "score": 0.85,
                "rechtsgebied": "publiekrecht",
                "wet_regeling": "Wet BRP",
                "artikel_lid": "Artikel 1 sub b",
            },
        ]

        xml = rag_service._format_context(chunks)
        assert xml.startswith("<bronnen>")
        assert xml.endswith("</bronnen>")
        assert xml.count("<bron ") == 2
        assert 'type="rag"' in xml
        assert 'score="0.92"' in xml
        assert "basisregistratie personen" in xml

    def test_format_context_empty(self, rag_service):
        assert rag_service._format_context([]) == ""


# ===========================================================================
# Test 3: Score threshold filtering
# ===========================================================================
@pytest.mark.integration
class TestRAGScoreThresholdFiltering:
    def test_cosine_similarity_ordering(self, embedding_store, collection_id, rag_db):
        # Maak document record aan voor FK constraint
        conn = sqlite3.connect(rag_db)
        conn.execute("PRAGMA foreign_keys=ON")
        cursor = conn.execute(
            "INSERT INTO rag_documents (collection_id, filename, chunk_count) VALUES (?, ?, 0)",
            (collection_id, "ordering_test.txt"),
        )
        conn.commit()
        doc_id = cursor.lastrowid
        conn.close()

        base = _random_embedding(seed=42)
        very_close = _similar_embedding(base, 0.01)
        far_away = _distant_embedding(base)

        embedding_store.store_chunk(
            collection_id=collection_id,
            document_id=doc_id,
            chunk_text="Zeer relevant",
            embedding=very_close,
            chunk_index=0,
        )
        embedding_store.store_chunk(
            collection_id=collection_id,
            document_id=doc_id,
            chunk_text="Niet relevant",
            embedding=far_away,
            chunk_index=1,
        )

        results = embedding_store.search_similar(
            query_embedding=base,
            collection_id=collection_id,
            top_k=2,
        )

        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)
        assert scores[0] > 0.8
        assert scores[-1] < 0.3

    def test_application_level_filtering(self, embedding_store, collection_id, rag_db):
        # Maak document record aan voor FK constraint
        conn = sqlite3.connect(rag_db)
        conn.execute("PRAGMA foreign_keys=ON")
        cursor = conn.execute(
            "INSERT INTO rag_documents (collection_id, filename, chunk_count) VALUES (?, ?, 0)",
            (collection_id, "filtering_test.txt"),
        )
        conn.commit()
        doc_id = cursor.lastrowid
        conn.close()

        base = _random_embedding(seed=42)
        for i, noise in enumerate([0.01, 0.1, 0.5]):
            embedding_store.store_chunk(
                collection_id=collection_id,
                document_id=doc_id,
                chunk_text=f"Chunk {i}",
                embedding=_similar_embedding(base, noise),
                chunk_index=i,
            )
        embedding_store.store_chunk(
            collection_id=collection_id,
            document_id=doc_id,
            chunk_text="Irrelevant",
            embedding=_distant_embedding(base),
            chunk_index=3,
        )

        results = embedding_store.search_similar(
            query_embedding=base,
            collection_id=collection_id,
            top_k=10,
        )
        filtered = [r for r in results if r["score"] >= 0.3]
        assert len(filtered) < len(results)
        for c in filtered:
            assert c["score"] >= 0.3


# ===========================================================================
# Test 4: Lege collection — graceful degradation
# ===========================================================================
@pytest.mark.integration
class TestRAGEmptyCollection:
    def test_retrieve_from_empty(
        self, rag_service, mock_embedding_service, collection_id
    ):
        ctx = rag_service.retrieve_context(
            query="Wat is een ingezetene?",
            collection_id=collection_id,
        )
        assert isinstance(ctx, RAGContext)
        assert ctx.chunks == []
        assert ctx.formatted_context == ""

    def test_empty_query(self, rag_service, collection_id):
        ctx = rag_service.retrieve_context(query="", collection_id=collection_id)
        assert ctx.chunks == []


# ===========================================================================
# Test 5: Token budget in prompt injectie
# ===========================================================================
@pytest.mark.integration
class TestRAGTokenBudget:
    def test_max_chunks_respected(self):
        from services.prompts.prompt_service_v2 import PromptServiceV2

        rag_chunks = [
            {
                "chunk_text": f"Juridische tekst chunk {i}. " * 10,
                "score": 0.9 - i * 0.05,
                "rechtsgebied": "publiekrecht",
                "wet_regeling": "TestWet",
                "artikel_lid": f"Art. {i}",
            }
            for i in range(10)
        ]

        with patch.object(PromptServiceV2, "__init__", lambda self, *a, **kw: None):
            svc = PromptServiceV2.__new__(PromptServiceV2)
            svc._rag_injection_cfg = {
                "max_tokens_per_chunk": 600,
                "total_token_budget": 2500,
                "max_chunks": 5,
            }
            svc._aug_cfg = {}

        mock_ctx = MagicMock()
        mock_ctx.metadata = {"rag_chunks": rag_chunks}

        with (
            patch.object(svc, "_collect_web_brons", return_value=[]),
            patch.object(svc, "_collect_document_brons", return_value=[]),
        ):
            result = svc._collect_and_inject_bronnen("Test prompt", mock_ctx)

        bron_count = result.count("<bron ")
        assert 0 < bron_count <= 5

    def test_token_budget_limits_output(self):
        from services.prompts.prompt_service_v2 import PromptServiceV2

        rag_chunks = [
            {
                "chunk_text": "W" * 1000,
                "score": 0.9 - i * 0.01,
                "rechtsgebied": "publiekrecht",
                "wet_regeling": "TestWet",
                "artikel_lid": f"Art. {i}",
            }
            for i in range(20)
        ]

        with patch.object(PromptServiceV2, "__init__", lambda self, *a, **kw: None):
            svc = PromptServiceV2.__new__(PromptServiceV2)
            svc._rag_injection_cfg = {
                "max_tokens_per_chunk": 600,
                "total_token_budget": 500,
                "max_chunks": 20,
            }
            svc._aug_cfg = {}

        mock_ctx = MagicMock()
        mock_ctx.metadata = {"rag_chunks": rag_chunks}

        with (
            patch.object(svc, "_collect_web_brons", return_value=[]),
            patch.object(svc, "_collect_document_brons", return_value=[]),
        ):
            result = svc._collect_and_inject_bronnen("Test prompt", mock_ctx)

        bron_count = result.count("<bron ")
        assert 0 < bron_count <= 3

    def test_no_bronnen_returns_original(self):
        from services.prompts.prompt_service_v2 import PromptServiceV2

        with patch.object(PromptServiceV2, "__init__", lambda self, *a, **kw: None):
            svc = PromptServiceV2.__new__(PromptServiceV2)
            svc._rag_injection_cfg = {}
            svc._aug_cfg = {}

        mock_ctx = MagicMock()
        mock_ctx.metadata = {}

        with (
            patch.object(svc, "_collect_web_brons", return_value=[]),
            patch.object(svc, "_collect_document_brons", return_value=[]),
        ):
            result = svc._collect_and_inject_bronnen("Originele prompt", mock_ctx)

        assert result == "Originele prompt"


# ===========================================================================
# Test 6: Collection management
# ===========================================================================
@pytest.mark.integration
class TestRAGCollectionManagement:
    def test_ensure_collection_creates(self, rag_service, rag_db):
        cid = rag_service._ensure_collection("nieuwe_collection")
        assert cid > 0

        conn = sqlite3.connect(rag_db)
        row = conn.execute(
            "SELECT collection_name FROM rag_collections WHERE id = ?", (cid,)
        ).fetchone()
        conn.close()
        assert row[0] == "nieuwe_collection"

    def test_ensure_collection_idempotent(self, rag_service):
        cid1 = rag_service._ensure_collection("hergebruik_test")
        cid2 = rag_service._ensure_collection("hergebruik_test")
        assert cid1 == cid2


# ===========================================================================
# Test 7: Error handling
# ===========================================================================
@pytest.mark.integration
class TestRAGErrorHandling:
    def test_empty_text_raises(self, rag_service, collection_id):
        with pytest.raises(ValueError, match="tekst mag niet leeg zijn"):
            rag_service.ingest_document(
                tekst="",
                collection_id=collection_id,
                filename="empty.txt",
            )

    def test_whitespace_text_raises(self, rag_service, collection_id):
        with pytest.raises(ValueError, match="tekst mag niet leeg zijn"):
            rag_service.ingest_document(
                tekst="   \n\t  ",
                collection_id=collection_id,
                filename="ws.txt",
            )

    def test_rollback_on_embedding_failure(
        self, rag_service, mock_embedding_service, collection_id, rag_db
    ):
        mock_embedding_service.embed_batch.side_effect = RuntimeError("API down")

        with pytest.raises(RuntimeError, match="API down"):
            rag_service.ingest_document(
                tekst="Artikel 1\nTesttekst voor rollback.",
                collection_id=collection_id,
                filename="rollback.txt",
            )

        conn = sqlite3.connect(rag_db)
        count = conn.execute(
            "SELECT COUNT(*) FROM rag_documents WHERE collection_id = ?",
            (collection_id,),
        ).fetchone()[0]
        conn.close()
        assert count == 0


# ===========================================================================
# Test 8: XML source formatter standalone
# ===========================================================================
@pytest.mark.integration
class TestXMLSourceFormatter:
    def test_format_bron_rag(self):
        result = format_bron(
            nr=1,
            type="rag",
            chunk_text="Testtekst",
            score=0.88,
            confidence=0.88,
            rechtsgebied="publiekrecht",
        )
        assert 'type="rag"' in result
        assert 'score="0.88"' in result
        assert "Testtekst" in result

    def test_confidence_levels(self):
        assert confidence_to_level(0.95) == "high"
        assert confidence_to_level(0.80) == "high"
        assert confidence_to_level(0.79) == "medium"
        assert confidence_to_level(0.49) == "low"

    def test_wrap_bronnen_empty(self):
        assert wrap_bronnen([]) == ""
