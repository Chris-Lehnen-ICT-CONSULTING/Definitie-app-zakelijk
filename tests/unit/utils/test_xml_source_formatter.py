"""Tests voor xml_source_formatter (DEF-315)."""

import pytest

from utils.xml_source_formatter import confidence_to_level, format_bron, wrap_bronnen

pytestmark = [pytest.mark.unit]


# ---------------------------------------------------------------------------
# confidence_to_level
# ---------------------------------------------------------------------------
class TestConfidenceToLevel:
    def test_high(self):
        assert confidence_to_level(0.8) == "high"
        assert confidence_to_level(0.95) == "high"
        assert confidence_to_level(1.0) == "high"

    def test_medium(self):
        assert confidence_to_level(0.5) == "medium"
        assert confidence_to_level(0.79) == "medium"

    def test_low(self):
        assert confidence_to_level(0.0) == "low"
        assert confidence_to_level(0.49) == "low"


# ---------------------------------------------------------------------------
# format_bron — basisgedrag
# ---------------------------------------------------------------------------
class TestFormatBron:
    def test_minimal_rag(self):
        result = format_bron(1, "rag", "Tekst hier.")
        assert '<bron nr="1" type="rag">' in result
        assert "Tekst hier." in result
        assert "</bron>" in result

    def test_score_formatted_two_decimals(self):
        result = format_bron(1, "rag", "X", score=0.8567)
        assert 'score="0.86"' in result

    def test_confidence_and_auto_level(self):
        result = format_bron(1, "web", "X", confidence=0.92)
        assert 'confidence="0.92"' in result
        assert 'level="high"' in result

    def test_confidence_low_level(self):
        result = format_bron(1, "web", "X", confidence=0.3)
        assert 'level="low"' in result

    def test_explicit_level_overrides_auto(self):
        result = format_bron(1, "web", "X", confidence=0.3, level="high")
        assert 'level="high"' in result

    def test_level_without_confidence(self):
        result = format_bron(1, "document", "X", level="medium")
        assert 'level="medium"' in result
        assert "confidence=" not in result

    def test_no_optional_attrs_when_none(self):
        result = format_bron(1, "rag", "X")
        assert "score=" not in result
        assert "confidence=" not in result
        assert "level=" not in result


# ---------------------------------------------------------------------------
# format_bron — type-specifieke attributen
# ---------------------------------------------------------------------------
class TestFormatBronTypeAttrs:
    def test_rag_legal_metadata(self):
        result = format_bron(
            1,
            "rag",
            "Art. 1",
            score=0.92,
            confidence=0.92,
            rechtsgebied="bestuursrecht",
            regeling="Awb",
            artikel="1:3",
        )
        assert 'rechtsgebied="bestuursrecht"' in result
        assert 'regeling="Awb"' in result
        assert 'artikel="1:3"' in result

    def test_web_legal_metadata(self):
        result = format_bron(
            2,
            "web",
            "Snippet",
            confidence=0.85,
            provider="rechtspraak.nl",
            ecli="ECLI:NL:HR:2024:123",
            wet="Awb",
            artikel="1:3",
            citatie="HR 15 maart 2024",
            url="https://example.com",
        )
        assert 'type="web"' in result
        assert 'provider="rechtspraak.nl"' in result
        assert 'ecli="ECLI:NL:HR:2024:123"' in result
        assert 'url="https://example.com"' in result

    def test_document_attrs(self):
        result = format_bron(
            3,
            "document",
            "Fragment",
            confidence=0.70,
            titel="beleidsnota.pdf",
            citatie="¶ 2",
        )
        assert 'type="document"' in result
        assert 'titel="beleidsnota.pdf"' in result

    def test_none_attrs_omitted(self):
        result = format_bron(1, "web", "X", confidence=0.5, ecli=None, wet="")
        assert "ecli=" not in result
        assert "wet=" not in result

    def test_empty_string_attrs_omitted(self):
        result = format_bron(1, "rag", "X", rechtsgebied="", regeling=None)
        assert "rechtsgebied=" not in result
        assert "regeling=" not in result


# ---------------------------------------------------------------------------
# format_bron — XML escaping
# ---------------------------------------------------------------------------
class TestFormatBronEscaping:
    def test_escapes_text_content(self):
        result = format_bron(1, "rag", 'Art. 1 lid <3> & "bijlage"')
        assert "&lt;3&gt;" in result
        assert "&amp;" in result
        assert "<3>" not in result

    def test_escapes_attr_values_via_quoteattr(self):
        result = format_bron(
            1,
            "rag",
            "X",
            rechtsgebied='recht & "plicht"',
            regeling="BW <boek 7>",
        )
        assert "recht &amp;" in result
        assert "BW &lt;boek 7&gt;" in result


# ---------------------------------------------------------------------------
# wrap_bronnen
# ---------------------------------------------------------------------------
class TestWrapBronnen:
    def test_wraps_single_bron(self):
        bron = format_bron(1, "rag", "Tekst")
        result = wrap_bronnen([bron])
        assert result.startswith("<bronnen>")
        assert result.endswith("</bronnen>")
        assert "<bron " in result

    def test_wraps_multiple_bronnen(self):
        brons = [
            format_bron(1, "rag", "RAG tekst", score=0.9, confidence=0.9),
            format_bron(2, "web", "Web snippet", confidence=0.85, provider="overheid"),
            format_bron(
                3, "document", "Doc fragment", confidence=0.7, titel="nota.pdf"
            ),
        ]
        result = wrap_bronnen(brons)
        assert result.count("<bron ") == 3
        assert result.count("</bron>") == 3
        assert 'type="rag"' in result
        assert 'type="web"' in result
        assert 'type="document"' in result

    def test_empty_list_returns_empty_string(self):
        assert wrap_bronnen([]) == ""

    def test_sequential_numbering_across_types(self):
        """Verify nr attributen doorlopend zijn over alle brontypen."""
        brons = [
            format_bron(1, "rag", "A"),
            format_bron(2, "web", "B"),
            format_bron(3, "document", "C"),
        ]
        result = wrap_bronnen(brons)
        assert 'nr="1"' in result
        assert 'nr="2"' in result
        assert 'nr="3"' in result
