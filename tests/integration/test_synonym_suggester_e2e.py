"""End-to-end integratie-test voor de model-onafhankelijke SynonymSuggester (DEF-459).

Dekt de echte round-trip: prompt-builder → geconfigureerd model (via AIServiceV2 +
ModelRouter) → defensieve parser → SynonymSuggestion-objecten. Vereist een geldige
AI-key en wordt in CI overgeslagen (net als de andere synoniem-e2e-tests).
"""

import os

import pytest

# Skip zonder ECHTE key: default-provider is anthropic; de suggester werkt ook
# met OpenAI. Guard op de echte key-prefixes (sk-.../sk-ant-...) zodat CI-dummy-keys
# ('dummy') de test niet laten draaien — die zou dan op een connection-error falen.
_HAS_KEY = os.environ.get("OPENAI_API_KEY", "").startswith("sk-") or os.environ.get(
    "ANTHROPIC_API_KEY", ""
).startswith("sk-ant-")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _HAS_KEY,
        reason="Geen geldige AI-key (OPENAI_API_KEY=sk-... of ANTHROPIC_API_KEY) - e2e vereist echte API",
    ),
]

from models.synonym_models import SynonymSuggestion
from services.container import ServiceContainer
from services.synonym_suggester import SynonymSuggester


@pytest.mark.asyncio
async def test_suggest_synonyms_echte_roundtrip():
    """De suggester levert echte, geldige suggesties op via het geconfigureerde model."""
    container = ServiceContainer({"db_path": ":memory:", "use_json_rules": False})

    suggester = container.synonym_suggester()
    assert isinstance(suggester, SynonymSuggester)

    result = await suggester.suggest_synonyms(
        term="verdachte",
        context=["Wetboek van Strafvordering"],
    )

    # Model kan legitiem 0 teruggeven, maar wat er is moet geldig zijn.
    assert isinstance(result, list)
    for suggestion in result:
        assert isinstance(suggestion, SynonymSuggestion)
        assert suggestion.synoniem.strip()
        assert 0.0 <= suggestion.confidence <= 1.0

    # Voor een gangbare juridische term verwachten we minstens één synoniem.
    assert len(result) >= 1, "verwacht minstens één synoniem voor 'verdachte'"
