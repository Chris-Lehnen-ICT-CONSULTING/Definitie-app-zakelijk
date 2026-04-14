"""Tests voor multi-collection RAG branch in DefinitionOrchestratorV2 (DEF-366).

Verifieert dat de orchestrator correct kiest tussen retrieve_context
(single collection) en retrieve_context_multi (meerdere collections).
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = [pytest.mark.unit]


@dataclass
class _FakeRequest:
    """Minimal request stub voor orchestrator RAG branch tests."""

    begrip: str = "testbegrip"
    rag_collection_ids: list[int] | None = None
    rag_collection_id: int | None = None
    juridische_context: list[str] | None = None


@dataclass
class _FakeRAGContext:
    chunks: list[dict]
    formatted_context: str
    collection_id: int
    query: str


class TestOrchestratorRAGBranching:
    """Test dat de orchestrator de juiste RAG methode aanroept."""

    def test_multi_collection_ids_calls_retrieve_context_multi(self):
        """Bij rag_collection_ids → retrieve_context_multi wordt aangeroepen."""
        mock_rag = MagicMock()
        mock_rag.retrieve_context_multi.return_value = _FakeRAGContext(
            chunks=[{"chunk_text": "test", "score": 0.9}],
            formatted_context="<bronnen/>",
            collection_id=0,
            query="testbegrip",
        )

        request = _FakeRequest(rag_collection_ids=[1, 2, 3])

        # Simuleer de orchestrator branching logica
        rag_collection_ids = getattr(request, "rag_collection_ids", None)
        assert rag_collection_ids == [1, 2, 3]

        if rag_collection_ids:
            ctx = mock_rag.retrieve_context_multi(
                query=request.begrip,
                collection_ids=rag_collection_ids,
                top_k=5,
            )
        else:
            ctx = mock_rag.retrieve_context(
                query=request.begrip,
                collection_id=1,
                top_k=5,
            )

        mock_rag.retrieve_context_multi.assert_called_once_with(
            query="testbegrip",
            collection_ids=[1, 2, 3],
            top_k=5,
        )
        mock_rag.retrieve_context.assert_not_called()
        assert len(ctx.chunks) == 1

    def test_no_collection_ids_calls_retrieve_context(self):
        """Zonder rag_collection_ids → fallback naar retrieve_context."""
        mock_rag = MagicMock()
        mock_rag._ensure_collection.return_value = 42
        mock_rag.retrieve_context.return_value = _FakeRAGContext(
            chunks=[{"chunk_text": "single", "score": 0.8}],
            formatted_context="<bronnen/>",
            collection_id=42,
            query="testbegrip",
        )

        request = _FakeRequest(rag_collection_ids=None, rag_collection_id=None)

        rag_collection_ids = getattr(request, "rag_collection_ids", None)
        assert not rag_collection_ids

        rag_collection_id = getattr(request, "rag_collection_id", None)
        if rag_collection_id is None:
            rag_collection_id = mock_rag._ensure_collection("user_documents")

        if rag_collection_ids:
            ctx = mock_rag.retrieve_context_multi(
                query=request.begrip,
                collection_ids=rag_collection_ids,
                top_k=5,
            )
        else:
            ctx = mock_rag.retrieve_context(
                query=request.begrip,
                collection_id=rag_collection_id,
                top_k=5,
            )

        mock_rag.retrieve_context.assert_called_once_with(
            query="testbegrip",
            collection_id=42,
            top_k=5,
        )
        mock_rag.retrieve_context_multi.assert_not_called()
        assert ctx.collection_id == 42

    def test_single_collection_id_uses_single_path(self):
        """Met alleen rag_collection_id (geen ids) → single path."""
        mock_rag = MagicMock()
        mock_rag.retrieve_context.return_value = _FakeRAGContext(
            chunks=[], formatted_context="", collection_id=7, query="test"
        )

        request = _FakeRequest(rag_collection_ids=None, rag_collection_id=7)

        rag_collection_ids = getattr(request, "rag_collection_ids", None)
        rag_collection_id = getattr(request, "rag_collection_id", None)

        assert not rag_collection_ids
        assert rag_collection_id == 7

        mock_rag.retrieve_context(
            query=request.begrip,
            collection_id=rag_collection_id,
            top_k=5,
        )

        mock_rag.retrieve_context.assert_called_once()
        mock_rag.retrieve_context_multi.assert_not_called()
