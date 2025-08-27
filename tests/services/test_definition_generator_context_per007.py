import pytest

from services.interfaces import GenerationRequest
from services.definition_generator_context import HybridContextManager, EnrichedContext
from services.definition_generator_config import ContextConfig
from services.prompts.prompt_service_v2 import PromptServiceV2
from services.prompts.modules.context_awareness_module import (
    ContextAwarenessModule,
)
from services.definition_generator_config import UnifiedGeneratorConfig
from services.prompts.modules.base_module import ModuleContext


def make_request() -> GenerationRequest:
    return GenerationRequest(
        id="test-per-007",
        begrip="verdachte",
        organisatorische_context=["DJI", "OM"],
        juridische_context=["Strafrecht", "Wetboek van Strafvordering"],
        wettelijke_basis=["Art. 27 Sv", "Art. 67 Sv"],
    )


def test_base_context_includes_all_three_lists():
    request = make_request()
    config = ContextConfig()
    ctx = HybridContextManager(config)
    # Test de interne mapping functie direct (geen async afhankelijkheden nodig)
    base = ctx._build_base_context(request)

    assert "DJI" in base["organisatorisch"] and "OM" in base["organisatorisch"]
    assert "Strafrecht" in base["juridisch"]
    assert "Art. 27 Sv" in base["wettelijk"]


def test_prompt_service_v2_converts_all_context_fields():
    request = make_request()
    svc = PromptServiceV2()
    enriched = svc._convert_request_to_context(request)

    assert set(enriched.base_context.get("organisatorisch", [])) >= {"DJI", "OM"}
    assert "Strafrecht" in enriched.base_context.get("juridisch", [])
    assert "Art. 27 Sv" in enriched.base_context.get("wettelijk", [])


def test_context_awareness_module_renders_all_sections():
    # Bouw een minimale EnrichedContext die de drie contextcategorieën bevat
    base = {
        "organisatorisch": ["DJI", "OM"],
        "juridisch": ["Strafrecht"],
        "wettelijk": ["Art. 27 Sv"],
        "domein": [],
        "technisch": [],
        "historisch": [],
    }
    enriched = EnrichedContext(
        base_context=base,
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={},
    )
    mod = ContextAwarenessModule()
    mod.initialize({})
    module_context = ModuleContext(
        begrip="verdachte",
        enriched_context=enriched,
        config=UnifiedGeneratorConfig(),
        shared_state={},
    )

    output = mod.execute(module_context)
    text = output.content

    # Verwacht categorie labels en waarden (format uit get_all_context_text)
    assert "Organisatorisch" in text
    assert "DJI" in text and "OM" in text
    assert "Juridisch" in text and "Strafrecht" in text
    assert "Wettelijk" in text and "Art. 27 Sv" in text
def test_legacy_context_ignored_when_structured_present():
    # Wanneer de gestructureerde velden aanwezig zijn, mag de vrije context-string niet toegevoegd worden
    request = make_request()
    request.context = "Legacy vrije context"

    config = ContextConfig()
    ctx = HybridContextManager(config)
    base = ctx._build_base_context(request)

    # De vrije context-string hoort niet als item in organisatorisch te staan
    assert "Legacy vrije context" not in base.get("organisatorisch", [])

    # En de gestructureerde velden blijven aanwezig
    assert "DJI" in base.get("organisatorisch", [])
    assert "Strafrecht" in base.get("juridisch", [])
