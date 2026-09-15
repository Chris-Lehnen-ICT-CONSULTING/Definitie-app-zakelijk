"""Integratie test: alle 3 brontypen in één <bronnen> blok (DEF-315).

Drijft de echte collector `PromptServiceV2._collect_and_inject_bronnen()`:
RAG + web + document bronnen worden verzameld en in één XML blok gewrapped.
DEF-743: de collector geeft geen confidence/level meer door en kent geen
documentconstante 0.70; alleen de zoekscore en aangeleverde coördinaten.
"""

import pytest

from services.definition_generator_context import EnrichedContext
from services.prompts.prompt_service_v2 import PromptServiceV2

pytestmark = [pytest.mark.unit]


def _simulate_collect_bronnen(
    rag_chunks: list[dict],
    web_sources: list[dict],
    doc_snippets: list[dict],
) -> str:
    """Verzamel via de echte collector; geef alleen het <bronnen>-blok terug."""
    svc = PromptServiceV2()
    svc._aug_cfg = {
        "enabled": True,
        "max_snippets": 10,
        "max_tokens_per_snippet": 300,
        "total_token_budget": 5000,
        "prioritize_juridical": False,
    }
    enriched = EnrichedContext(
        base_context={"organisatorisch": [], "juridisch": [], "wettelijk": []},
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={
            "rag_chunks": rag_chunks,
            "web_lookup": {"sources": web_sources, "top_k": len(web_sources)},
            "documents": {"snippets": doc_snippets},
        },
    )
    text = svc._collect_and_inject_bronnen("BODY", enriched)
    if text == "BODY":
        return ""
    assert text.startswith("BODY\n\n")
    return text[len("BODY\n\n") :]


class TestThreeSourceTypesIntegration:
    """Test dat alle 3 brontypen correct combineren in één XML blok."""

    def test_all_three_types_in_one_block(self):
        result = _simulate_collect_bronnen(
            rag_chunks=[
                {
                    "chunk_text": "Artikel 1 lid 1 Awb definieert het begrip bestuursorgaan.",
                    "score": 0.92,
                    "rechtsgebied": "bestuursrecht",
                    "wet_regeling": "Awb",
                    "artikel_lid": "1:1",
                }
            ],
            web_sources=[
                {
                    "provider": "rechtspraak.nl",
                    "snippet": "De Hoge Raad overweegt dat...",
                    "score": 0.85,
                    "url": "https://rechtspraak.nl/example",
                    "legal": {
                        "ecli": "ECLI:NL:HR:2024:123",
                        "citation_text": "ECLI:NL:HR:2024:123",
                    },
                }
            ],
            doc_snippets=[
                {
                    "title": "beleidsnota.pdf",
                    "snippet": "Het begrip wordt als volgt gehanteerd...",
                    "citation_label": "¶ 2",
                }
            ],
        )

        # Eén <bronnen> blok
        assert result.startswith("<bronnen>")
        assert result.endswith("</bronnen>")

        # Drie <bron> tags
        assert result.count("<bron ") == 3
        assert result.count("</bron>") == 3

        # Type attributen
        assert 'type="rag"' in result
        assert 'type="web"' in result
        assert 'type="document"' in result

        # Doorlopende nummering
        assert 'nr="1"' in result
        assert 'nr="2"' in result
        assert 'nr="3"' in result

        # RAG-specifieke attributen
        assert 'rechtsgebied="bestuursrecht"' in result
        assert 'regeling="Awb"' in result
        assert 'artikel="1:1"' in result
        assert 'score="0.92"' in result

        # Web-specifieke attributen
        assert 'provider="rechtspraak.nl"' in result
        assert 'ecli="ECLI:NL:HR:2024:123"' in result
        assert 'url="https://rechtspraak.nl/example"' in result
        assert 'score="0.85"' in result

        # Document-specifieke attributen
        assert 'titel="beleidsnota.pdf"' in result
        assert 'citatie="¶ 2"' in result

        # DEF-743: zoekscore is geen betrouwbaarheid; geen confidence/level,
        # geen documentconstante 0.70.
        assert "confidence=" not in result
        assert "level=" not in result
        assert "0.70" not in result

        # Bronteksten
        assert "bestuursorgaan" in result
        assert "Hoge Raad" in result
        assert "gehanteerd" in result

    def test_empty_sources_returns_empty(self):
        assert _simulate_collect_bronnen([], [], []) == ""

    def test_only_rag_sources(self):
        result = _simulate_collect_bronnen(
            rag_chunks=[
                {"chunk_text": "Tekst A", "score": 0.9},
                {"chunk_text": "Tekst B", "score": 0.7},
            ],
            web_sources=[],
            doc_snippets=[],
        )
        assert 'type="rag"' in result
        assert 'type="web"' not in result
        assert 'type="document"' not in result
        assert result.count("<bron ") == 2

    def test_only_web_sources(self):
        result = _simulate_collect_bronnen(
            rag_chunks=[],
            web_sources=[
                {"provider": "wikipedia", "snippet": "Wiki tekst", "score": 0.5}
            ],
            doc_snippets=[],
        )
        assert 'type="web"' in result
        assert 'type="rag"' not in result
        assert 'nr="1"' in result

    def test_xml_escaping_across_types(self):
        """Verifieer dat XML escaping correct werkt over alle brontypen."""
        result = _simulate_collect_bronnen(
            rag_chunks=[{"chunk_text": "Art. <3> & bijlage", "score": 0.9}],
            web_sources=[{"snippet": 'Citaat "met quotes"', "score": 0.5}],
            doc_snippets=[{"snippet": "A & B < C", "title": "test.pdf"}],
        )
        # Geen onge-escape-de speciale tekens in de output
        assert "<3>" not in result
        assert "&lt;3&gt;" in result
        assert "A &amp; B &lt; C" in result

    def test_used_in_prompt_not_in_xml(self):
        """Acceptance criteria: used_in_prompt flag zit NIET in XML."""
        result = _simulate_collect_bronnen(
            rag_chunks=[],
            web_sources=[
                {
                    "provider": "overheid",
                    "snippet": "Tekst",
                    "score": 0.9,
                    "used_in_prompt": True,
                }
            ],
            doc_snippets=[],
        )
        assert "used_in_prompt" not in result
