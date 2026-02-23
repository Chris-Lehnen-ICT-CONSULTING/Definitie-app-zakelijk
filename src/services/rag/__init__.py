"""
RAG (Retrieval-Augmented Generation) services voor de Definitie-app.

Juridisch-aware document chunking en embedding voor de RAG-pipeline.
"""

from services.rag.constants import COLLECTION_TYPE_MAP, COLLECTION_TYPES, RECHTSGEBIEDEN
from services.rag.document_chunker import DocumentChunker
from services.rag.embedding_service import EmbeddingService
from services.rag.embedding_store import EmbeddingStore
from services.rag.models import ChunkingResult, ChunkMetadata, DocumentChunk
from services.rag.rag_management_service import RAGManagementService
from services.rag.rag_service import RAGContext, RAGService

__all__ = [
    "COLLECTION_TYPES",
    "COLLECTION_TYPE_MAP",
    "RECHTSGEBIEDEN",
    "ChunkMetadata",
    "ChunkingResult",
    "DocumentChunk",
    "DocumentChunker",
    "EmbeddingService",
    "EmbeddingStore",
    "RAGContext",
    "RAGManagementService",
    "RAGService",
]
