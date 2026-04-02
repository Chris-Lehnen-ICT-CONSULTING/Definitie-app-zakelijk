"""DEF-316: Tests voor RAG token budget — truncatie per chunk en totaalbudget."""

import pytest

from services.definition_generator_context import EnrichedContext
from services.prompts.prompt_service_v2 import PromptServiceV2

pytestmark = [pytest.mark.unit]


def _make_enriched_context(rag_chunks: list[dict]) -> EnrichedContext:
    """Helper: maak EnrichedContext met RAG chunks."""
    return EnrichedContext(
        base_context={"organisatorisch": [], "juridisch": [], "wettelijk": []},
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={"rag_chunks": rag_chunks},
    )


def _make_chunk(text: str, score: float = 0.85) -> dict:
    """Helper: maak een RAG chunk dict."""
    return {
        "chunk_text": text,
        "score": score,
        "rechtsgebied": "strafrecht",
        "wet_regeling": "WvSr",
        "artikel_lid": "Art. 1",
    }


# ==================================================
# Static method tests
# ==================================================


class TestApproxTokens:
    def test_empty_string(self):
        assert PromptServiceV2._approx_tokens("") == 1

    def test_short_string(self):
        # "hello" = 5 chars → (5+3)//4 = 2
        assert PromptServiceV2._approx_tokens("hello") == 2

    def test_longer_string(self):
        text = "a" * 400  # 400 chars → (400+3)//4 = 100
        assert PromptServiceV2._approx_tokens(text) == 100


class TestTruncateToTokens:
    def test_short_text_unchanged(self):
        text = "kort stukje tekst"
        assert PromptServiceV2._truncate_to_tokens(text, 100) == text

    def test_long_text_truncated(self):
        # 100 tokens × 4 chars = 400 char limit
        text = " ".join(["woord"] * 200)  # ~1000 chars
        result = PromptServiceV2._truncate_to_tokens(text, 100)
        assert len(result) <= 400

    def test_truncates_on_word_boundary(self):
        text = "Dit is een zin met meerdere woorden die afgekapt moet worden"
        result = PromptServiceV2._truncate_to_tokens(text, 5)  # 20 chars
        assert not result.endswith(" ")
        assert " " in result  # Has at least one word break


# ==================================================
# RAG injection tests
# ==================================================


class TestRagInjectionBudget:
    def test_5_large_chunks_respect_total_budget(self):
        """5 chunks van ~1000 tokens → output moet ≤ 2500 tokens zijn."""
        svc = PromptServiceV2()
        # Elk chunk ~1000 tokens = ~4000 tekens
        big_text = "woord " * 666  # ~4000 chars ≈ 1000 tokens
        chunks = [_make_chunk(big_text) for _ in range(5)]
        enriched = _make_enriched_context(chunks)

        brons = svc._collect_and_inject_bronnen("BASE PROMPT", enriched)

        # Tel de geschatte RAG tokens in de output
        # De base prompt + bronnen block bevat XML overhead, maar
        # de RAG content zelf moet begrensd zijn door het budget
        # We verifiëren indirect: niet alle 5 chunks kunnen erin (5×600 = 3000 > 2500)
        rag_bron_count = brons.count('type="rag"')
        assert (
            rag_bron_count < 5
        ), f"Verwacht minder dan 5 RAG brons (budget 2500), maar kreeg {rag_bron_count}"

    def test_small_chunks_all_included(self):
        """Kleine chunks die binnen budget passen moeten allemaal mee."""
        svc = PromptServiceV2()
        small_text = "Korte juridische tekst."  # ~6 tokens
        chunks = [_make_chunk(small_text) for _ in range(5)]
        enriched = _make_enriched_context(chunks)

        brons = svc._collect_and_inject_bronnen("BASE PROMPT", enriched)
        rag_bron_count = brons.count('type="rag"')
        assert rag_bron_count == 5

    def test_per_chunk_truncation(self):
        """Individuele chunks worden afgekapt op max_tokens_per_chunk (default 600)."""
        svc = PromptServiceV2()
        # Chunk van ~1000 tokens (4000 tekens), moet getrunceerd worden tot ~600 tokens (2400 tekens)
        big_text = "a" * 4000
        chunks = [_make_chunk(big_text)]
        enriched = _make_enriched_context(chunks)

        brons = svc._collect_and_inject_bronnen("BASE PROMPT", enriched)
        # Het chunk_text in de output mag niet de volledige 4000 tekens bevatten
        assert big_text not in brons
        # Maar er moet wel content zijn
        assert 'type="rag"' in brons

    def test_budget_break_stops_adding(self):
        """Als het budget op is, worden verdere chunks niet meer toegevoegd."""
        svc = PromptServiceV2()
        # Overschrijf config voor stricter budget
        svc._rag_injection_cfg = {
            "max_tokens_per_chunk": 600,
            "total_token_budget": 100,  # Heel krap budget
            "max_chunks": 5,
        }
        # Elk chunk ~150 tokens
        text = "woord " * 100  # ~600 chars ≈ 150 tokens
        chunks = [_make_chunk(text) for _ in range(5)]
        enriched = _make_enriched_context(chunks)

        brons = svc._collect_and_inject_bronnen("BASE PROMPT", enriched)
        rag_bron_count = brons.count('type="rag"')
        # Met budget 100 past er maar ~1 chunk van 150 tokens (eerste past, rest niet)
        assert rag_bron_count <= 1

    def test_max_chunks_respected(self):
        """max_chunks limiet wordt gerespecteerd."""
        svc = PromptServiceV2()
        svc._rag_injection_cfg = {
            "max_tokens_per_chunk": 600,
            "total_token_budget": 99999,  # Ruim budget
            "max_chunks": 2,  # Maar max 2 chunks
        }
        small_text = "Kort."
        chunks = [_make_chunk(small_text) for _ in range(5)]
        enriched = _make_enriched_context(chunks)

        brons = svc._collect_and_inject_bronnen("BASE PROMPT", enriched)
        rag_bron_count = brons.count('type="rag"')
        assert rag_bron_count == 2

    def test_empty_rag_chunks(self):
        """Geen RAG chunks → geen <bron type="rag"> in output."""
        svc = PromptServiceV2()
        enriched = _make_enriched_context([])

        result = svc._collect_and_inject_bronnen("BASE PROMPT", enriched)
        assert result == "BASE PROMPT"

    def test_rag_metadata_preserved(self):
        """Juridische metadata (rechtsgebied, regeling, artikel) wordt doorgestuurd."""
        svc = PromptServiceV2()
        chunk = {
            "chunk_text": "Wettekst fragment.",
            "score": 0.92,
            "rechtsgebied": "bestuursrecht",
            "wet_regeling": "Awb",
            "artikel_lid": "Art. 3:2",
        }
        enriched = _make_enriched_context([chunk])

        brons = svc._collect_and_inject_bronnen("BASE PROMPT", enriched)
        assert "bestuursrecht" in brons
        assert "Awb" in brons
        assert "Art. 3:2" in brons


# ==================================================
# Web budget tests (verhoogde waarden)
# ==================================================


class TestWebBudgetConfig:
    def test_web_budget_defaults_from_config(self):
        """Verify de config defaults (na DEF-316 verhogingen)."""
        svc = PromptServiceV2()
        aug = svc._aug_cfg
        # Na DEF-316: 400→1500, 100→300, 3→5
        assert int(aug.get("total_token_budget", 0)) == 1500
        assert int(aug.get("max_tokens_per_snippet", 0)) == 300
        assert int(aug.get("max_snippets", 0)) == 5

    def test_rag_injection_defaults_from_config(self):
        """Verify RAG injection config defaults."""
        svc = PromptServiceV2()
        rag = svc._rag_injection_cfg
        assert int(rag.get("max_tokens_per_chunk", 0)) == 600
        assert int(rag.get("total_token_budget", 0)) == 2500
        assert int(rag.get("max_chunks", 0)) == 5
