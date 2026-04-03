import pytest

pytestmark = [pytest.mark.unit]


def test_prompt_includes_document_snippets_as_xml_brons():
    """DEF-315: Document snippets produce <bron type="document"> XML tags."""
    from services.definition_generator_context import EnrichedContext
    from services.prompts.prompt_service_v2 import PromptServiceV2

    svc = PromptServiceV2()

    # Minimal enriched context met document-snippets metadata
    enriched = EnrichedContext(
        base_context={"organisatorisch": [], "juridisch": [], "wettelijk": []},
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={
            "documents": {
                "snippets": [
                    {
                        "title": "test.docx",
                        "snippet": "Korte tekst rondom het begrip.",
                        "citation_label": "¶ 2",
                        "used_in_prompt": True,
                    },
                ]
            }
        },
    )

    brons = svc._collect_document_brons(enriched, nr_offset=0)
    assert len(brons) == 1
    bron = brons[0]
    assert 'type="document"' in bron
    assert 'nr="1"' in bron
    assert 'confidence="0.70"' in bron
    assert 'titel="test.docx"' in bron
    assert "Korte tekst rondom het begrip." in bron


def test_collect_document_brons_empty_when_disabled(monkeypatch):
    """When DOCUMENT_SNIPPETS_ENABLED=false, returns empty list."""
    from services.definition_generator_context import EnrichedContext
    from services.prompts.prompt_service_v2 import PromptServiceV2

    monkeypatch.setenv("DOCUMENT_SNIPPETS_ENABLED", "false")

    svc = PromptServiceV2()
    enriched = EnrichedContext(
        base_context={"organisatorisch": [], "juridisch": [], "wettelijk": []},
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={
            "documents": {
                "snippets": [
                    {"title": "doc.pdf", "snippet": "Text", "citation_label": "p1"},
                ]
            }
        },
    )

    brons = svc._collect_document_brons(enriched, nr_offset=0)
    assert brons == []


def test_collect_document_brons_respects_offset():
    """Nr offset is applied correctly for sequential numbering."""
    from services.definition_generator_context import EnrichedContext
    from services.prompts.prompt_service_v2 import PromptServiceV2

    svc = PromptServiceV2()
    enriched = EnrichedContext(
        base_context={"organisatorisch": [], "juridisch": [], "wettelijk": []},
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={
            "documents": {
                "snippets": [
                    {"title": "doc.pdf", "snippet": "Snippet text."},
                ]
            }
        },
    )

    brons = svc._collect_document_brons(enriched, nr_offset=5)
    assert len(brons) == 1
    assert 'nr="6"' in brons[0]
