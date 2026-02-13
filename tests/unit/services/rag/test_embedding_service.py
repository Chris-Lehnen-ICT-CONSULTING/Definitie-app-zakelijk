"""Tests voor EmbeddingService (DEF-269)."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from services.rag.embedding_service import EmbeddingService


@pytest.fixture
def service():
    """EmbeddingService met gemockte OpenAI client."""
    with patch("services.rag.embedding_service.openai.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        svc = EmbeddingService(api_key="test-key")
        svc._mock_client = mock_client  # expose voor test assertions
        yield svc


def _mock_response(embeddings: list[list[float]]):
    """Helper: bouw een mock OpenAI embeddings response."""
    response = MagicMock()
    response.data = []
    for i, emb in enumerate(embeddings):
        item = MagicMock()
        item.embedding = emb
        item.index = i
        response.data.append(item)
    return response


class TestInit:
    def test_client_created_with_api_key(self):
        with patch("services.rag.embedding_service.openai.OpenAI") as mock_cls:
            EmbeddingService(api_key="sk-test123")
            mock_cls.assert_called_once_with(api_key="sk-test123", max_retries=3)

    def test_model_constants(self, service):
        assert service.MODEL == "text-embedding-3-large"
        assert service.DIMENSIONS == 3072
        assert service.MAX_TOKENS == 8191
        assert service.BATCH_SIZE == 100


class TestEmbed:
    def test_returns_ndarray(self, service):
        fake_embedding = [0.1] * 3072
        service._mock_client.embeddings.create.return_value = _mock_response(
            [fake_embedding]
        )
        result = service.embed("test tekst")

        assert isinstance(result, np.ndarray)
        assert result.shape == (3072,)
        assert result.dtype == np.float32

    def test_calls_openai_with_correct_params(self, service):
        service._mock_client.embeddings.create.return_value = _mock_response(
            [[0.0] * 3072]
        )
        service.embed("Hallo wereld")

        service._mock_client.embeddings.create.assert_called_once_with(
            input="Hallo wereld",
            model="text-embedding-3-large",
            dimensions=3072,
        )

    def test_truncates_long_text(self, service):
        service._mock_client.embeddings.create.return_value = _mock_response(
            [[0.0] * 3072]
        )
        # Maak tekst die zeker >8191 tokens is
        long_text = "woord " * 20000

        with patch("services.rag.embedding_service.logger") as mock_logger:
            service.embed(long_text)
            mock_logger.warning.assert_called_once()
            assert "afgekapt" in mock_logger.warning.call_args[0][0]

    def test_short_text_not_truncated(self, service):
        service._mock_client.embeddings.create.return_value = _mock_response(
            [[0.0] * 3072]
        )
        short_text = "Korte tekst"

        with patch("services.rag.embedding_service.logger") as mock_logger:
            service.embed(short_text)
            mock_logger.warning.assert_not_called()

    @pytest.mark.parametrize("bad_input", [None, "", "   "])
    def test_rejects_none_and_empty(self, service, bad_input):
        with pytest.raises(ValueError, match="text mag niet None of leeg zijn"):
            service.embed(bad_input)

    def test_api_error_bubbles_up(self, service):
        import openai as openai_mod

        service._mock_client.embeddings.create.side_effect = openai_mod.APIError(
            message="rate limit", request=MagicMock(), body=None
        )
        with pytest.raises(openai_mod.APIError):
            service.embed("test")


class TestEmbedBatch:
    def test_empty_list(self, service):
        result = service.embed_batch([])
        assert result == []

    def test_single_batch(self, service):
        texts = ["tekst een", "tekst twee", "tekst drie"]
        fake_embeddings = [[float(i)] * 3072 for i in range(3)]
        service._mock_client.embeddings.create.return_value = _mock_response(
            fake_embeddings
        )

        result = service.embed_batch(texts)

        assert len(result) == 3
        assert all(isinstance(r, np.ndarray) for r in result)
        assert all(r.shape == (3072,) for r in result)
        service._mock_client.embeddings.create.assert_called_once()

    def test_auto_split_batches(self, service):
        texts = [f"tekst {i}" for i in range(250)]

        # Drie batches: 100, 100, 50
        def create_response(**kwargs):
            batch_input = kwargs["input"]
            return _mock_response([[0.0] * 3072] * len(batch_input))

        service._mock_client.embeddings.create.side_effect = create_response

        result = service.embed_batch(texts)

        assert len(result) == 250
        assert service._mock_client.embeddings.create.call_count == 3

    def test_preserves_order(self, service):
        """Embeddings moeten in dezelfde volgorde als input staan."""
        texts = ["eerste", "tweede"]
        # Simuleer out-of-order response van OpenAI
        response = MagicMock()
        item_1 = MagicMock()
        item_1.embedding = [1.0] * 3072
        item_1.index = 1  # tweede, maar eerst in response
        item_0 = MagicMock()
        item_0.embedding = [0.0] * 3072
        item_0.index = 0  # eerste, maar tweede in response
        response.data = [item_1, item_0]
        service._mock_client.embeddings.create.return_value = response

        result = service.embed_batch(texts)

        # Index 0 moet [0.0, ...] zijn, index 1 moet [1.0, ...]
        assert result[0][0] == pytest.approx(0.0)
        assert result[1][0] == pytest.approx(1.0)

    def test_batch_truncates_long_texts(self, service):
        long_text = "woord " * 20000
        short_text = "kort"
        service._mock_client.embeddings.create.return_value = _mock_response(
            [[0.0] * 3072, [0.0] * 3072]
        )

        with patch("services.rag.embedding_service.logger") as mock_logger:
            service.embed_batch([long_text, short_text])
            # Alleen de lange tekst triggert een warning
            assert mock_logger.warning.call_count == 1
