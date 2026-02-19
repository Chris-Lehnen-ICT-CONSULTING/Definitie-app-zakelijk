"""
EmbeddingService — zet tekst om naar vectors via OpenAI's embedding API.

Wordt gebruikt door de RAG pipeline om document chunks doorzoekbaar te maken.
Eigen OpenAI client, onafhankelijk van de chat provider-keuze in de sidebar.
"""

from __future__ import annotations

import logging

import numpy as np
import openai
import tiktoken

logger = logging.getLogger(__name__)

# Lazy-loaded encoder (module-level singleton, zelfde encoding als token_counter.py)
_encoder: tiktoken.Encoding | None = None


def _get_encoder() -> tiktoken.Encoding:
    """Haal tiktoken encoder op (lazy singleton)."""
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding("cl100k_base")
    return _encoder


class EmbeddingService:
    """Genereert embeddings via OpenAI text-embedding-3-large.

    Kenmerken:
    - Aparte OpenAI client (niet afhankelijk van chat provider)
    - Auto-truncatie bij >8191 tokens
    - Batch-split bij >100 inputs
    - max_retries=3, daarna bubbelt de exception omhoog
    """

    MODEL = "text-embedding-3-large"
    DIMENSIONS = 3072
    MAX_TOKENS = 8191
    BATCH_SIZE = 100

    def __init__(self, api_key: str) -> None:
        """Initialiseer met eigen OpenAI client.

        Args:
            api_key: OpenAI API key (uit os.environ, NIET uit sidebar).
        """
        self.client = openai.OpenAI(api_key=api_key, max_retries=3)

    def _truncate(self, text: str) -> str:
        """Kap tekst af tot MAX_TOKENS als nodig."""
        enc = _get_encoder()
        tokens = enc.encode(text)
        if len(tokens) <= self.MAX_TOKENS:
            return text
        logger.warning(
            "Tekst afgekapt van %d naar %d tokens voor embedding",
            len(tokens),
            self.MAX_TOKENS,
        )
        return enc.decode(tokens[: self.MAX_TOKENS])

    def embed(self, text: str) -> np.ndarray:
        """Embed enkele tekst naar een 3072-dimensionale vector.

        Args:
            text: De tekst om te embedden.

        Returns:
            numpy array van shape (3072,).

        Raises:
            ValueError: Als text None of leeg is.
            openai.APIError: Bij API failures na 3 retries.
        """
        if not text or not text.strip():
            raise ValueError("text mag niet None of leeg zijn")
        truncated_text = self._truncate(text)
        response = self.client.embeddings.create(
            input=truncated_text,
            model=self.MODEL,
            dimensions=self.DIMENSIONS,
        )
        return np.array(response.data[0].embedding, dtype=np.float32)

    def embed_batch(self, texts: list[str]) -> list[np.ndarray]:
        """Embed meerdere teksten efficiënt via auto-batching.

        Splitst automatisch in blokken van BATCH_SIZE (100).
        Aanroeper merkt niks van de batching.

        Args:
            texts: Lijst van teksten om te embedden.

        Returns:
            Lijst van numpy arrays, elk shape (3072,).

        Raises:
            openai.APIError: Bij API failures na 3 retries.
        """
        if not texts:
            return []

        truncated = [self._truncate(t) for t in texts]
        all_embeddings: list[np.ndarray] = []

        for i in range(0, len(truncated), self.BATCH_SIZE):
            batch = truncated[i : i + self.BATCH_SIZE]
            logger.debug(
                "Embedding batch %d/%d (%d teksten)",
                i // self.BATCH_SIZE + 1,
                (len(truncated) - 1) // self.BATCH_SIZE + 1,
                len(batch),
            )
            response = self.client.embeddings.create(
                input=batch,
                model=self.MODEL,
                dimensions=self.DIMENSIONS,
            )
            # OpenAI retourneert embeddings gesorteerd op index
            batch_embeddings = sorted(response.data, key=lambda x: x.index)
            all_embeddings.extend(
                np.array(e.embedding, dtype=np.float32) for e in batch_embeddings
            )

        return all_embeddings
