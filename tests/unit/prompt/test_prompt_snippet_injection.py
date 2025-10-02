import pytest


def test_prompt_includes_document_snippets_block():
    from services.definition_generator_context import EnrichedContext
    from services.prompts.prompt_service_v2 import PromptServiceV2

    svc = PromptServiceV2()

    # Minimal enriched context met document‑snippets metadata
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

    text = svc._maybe_augment_with_document_snippets("PROMPT-REST", enriched)
    assert "DOCUMENTCONTEXT (snippets)" in text
    assert "test.docx (¶ 2):" in text
    assert text.endswith("PROMPT-REST")
