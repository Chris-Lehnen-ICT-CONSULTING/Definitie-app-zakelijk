"""Integratie test: alle 3 brontypen in één <bronnen> blok (DEF-315).

Simuleert het pad dat prompt_service_v2._collect_and_inject_bronnen() aflegt:
RAG + web + document bronnen worden verzameld en in één XML blok gewrapped.
"""

import pytest

from utils.xml_source_formatter import format_bron, wrap_bronnen


def _simulate_collect_bronnen(
    rag_chunks: list[dict],
    web_sources: list[dict],
    doc_snippets: list[dict],
) -> str:
    """Simuleer de bron-verzameling zoals prompt_service_v2 dat doet."""
    all_brons: list[str] = []
    nr = 0

    # RAG
    for chunk in rag_chunks:
        nr += 1
        all_brons.append(
            format_bron(
                nr=nr,
                type="rag",
                chunk_text=chunk["chunk_text"],
                score=chunk.get("score"),
                confidence=chunk.get("score"),
                rechtsgebied=chunk.get("rechtsgebied"),
                regeling=chunk.get("wet_regeling"),
                artikel=chunk.get("artikel_lid"),
            )
        )

    # Web
    for src in web_sources:
        nr += 1
        legal = src.get("legal", {}) or {}
        all_brons.append(
            format_bron(
                nr=nr,
                type="web",
                chunk_text=src.get("snippet", ""),
                score=float(src.get("score", 0.0)),
                confidence=float(src.get("score", 0.0)),
                provider=src.get("provider", ""),
                url=src.get("url", ""),
                ecli=legal.get("ecli", ""),
                wet=legal.get("law", ""),
                artikel=legal.get("article", ""),
                citatie=legal.get("citation_text", ""),
            )
        )

    # Document
    for doc in doc_snippets:
        nr += 1
        all_brons.append(
            format_bron(
                nr=nr,
                type="document",
                chunk_text=doc.get("snippet", ""),
                confidence=0.70,
                titel=doc.get("title", ""),
                citatie=doc.get("citation_label", ""),
            )
        )

    return wrap_bronnen(all_brons)


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
        assert 'confidence="0.92"' in result
        assert 'level="high"' in result

        # Web-specifieke attributen
        assert 'provider="rechtspraak.nl"' in result
        assert 'ecli="ECLI:NL:HR:2024:123"' in result

        # Document-specifieke attributen
        assert 'titel="beleidsnota.pdf"' in result
        assert 'confidence="0.70"' in result
        assert 'level="medium"' in result

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
