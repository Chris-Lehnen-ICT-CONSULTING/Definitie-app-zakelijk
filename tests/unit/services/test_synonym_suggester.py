import pytest

pytestmark = pytest.mark.unit

from unittest.mock import AsyncMock, MagicMock

from services.gpt4_synonym_suggester import SynonymSuggester, SynonymSuggestion


def _fake_ai_service(text: str) -> MagicMock:
    svc = MagicMock()
    result = MagicMock()
    result.text = text
    svc.generate_definition = AsyncMock(return_value=result)
    return svc


@pytest.mark.asyncio
async def test_suggest_synonyms_roept_model_onafhankelijk_aan():
    ai = _fake_ai_service(
        '{"synoniemen": [{"synoniem": "beklaagde", "confidence": 0.9, "rationale": "strafproces"}]}'
    )
    suggester = SynonymSuggester(ai_service=ai)
    result = await suggester.suggest_synonyms(term="verdachte")
    assert len(result) == 1
    assert result[0].synoniem == "beklaagde"
    _, kwargs = ai.generate_definition.call_args
    assert kwargs.get("task_type") == "synonyms"
    assert kwargs.get("model") is None


@pytest.mark.asyncio
async def test_suggest_synonyms_geeft_juridische_context_door_aan_prompt():
    ai = _fake_ai_service('{"synoniemen": []}')
    suggester = SynonymSuggester(ai_service=ai)
    await suggester.suggest_synonyms(
        term="verdachte", context=["Wetboek van Strafvordering"]
    )
    _, kwargs = ai.generate_definition.call_args
    # de context moet in de user-prompt zijn beland
    assert "Wetboek van Strafvordering" in kwargs["prompt"]


@pytest.mark.asyncio
async def test_suggest_synonyms_lege_output_geeft_lege_lijst():
    ai = _fake_ai_service('{"synoniemen": []}')
    suggester = SynonymSuggester(ai_service=ai)
    assert await suggester.suggest_synonyms(term="verdachte") == []


@pytest.mark.asyncio
async def test_suggest_synonyms_ai_fout_degradeert_naar_leeg():
    ai = MagicMock()
    ai.generate_definition = AsyncMock(side_effect=RuntimeError("boom"))
    suggester = SynonymSuggester(ai_service=ai)
    assert await suggester.suggest_synonyms(term="verdachte") == []


@pytest.mark.asyncio
async def test_suggest_synonyms_confidence_blijft_in_bereik():
    ai = _fake_ai_service(
        '{"synoniemen": [{"synoniem": "x", "confidence": 5.0, "rationale": "y"}]}'
    )
    suggester = SynonymSuggester(ai_service=ai)
    result = await suggester.suggest_synonyms(term="verdachte")
    assert 0.0 <= result[0].confidence <= 1.0


def test_get_stats_behouden():
    suggester = SynonymSuggester(ai_service=MagicMock())
    stats = suggester.get_stats()
    assert "status" in stats
