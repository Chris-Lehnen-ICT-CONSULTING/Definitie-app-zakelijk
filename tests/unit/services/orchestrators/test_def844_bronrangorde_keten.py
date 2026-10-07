"""DEF-844: bronrangorde door de echte keten orchestrator → promptservice.

Echte `DefinitionOrchestratorV2` en echte `PromptServiceV2` (stub-promptbouwer,
bekende budgetten); AI, cleaning, validatie en repository zijn offline doubles.
Bewijst voor het GAT-scenario (DEF-837 hertest 3, "verdachte"):

* weergave/opslag (`metadata["sources"]`): wetsartikelen vóór Wikipedia;
* prompt (`<bronnen>`-blok + kwitantie): wetsartikelen vóór Wikipedia;
* een webbron van een officieel wetgevingsdomein komt vóór de top-K-markering
  bovenaan en haalt zo de prompt, ook bij een lagere webscore;
* zonder RAG en zonder wetgevingsdomein blijft de webvolgorde ongewijzigd.

Geen echt model, geen netwerk, geen productiedatabase.
"""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import services.prompts.prompt_service_v2 as psv2
from services.interfaces import (
    AIGenerationResult,
    CleaningResult,
    GenerationRequest,
    LookupResult,
    OrchestratorConfig,
    WebSource,
)
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.prompts.prompt_service_v2 import PromptServiceV2

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

BEGRIP = "verdachte"
DEFINITIE = "Persoon te wiens aanzien een redelijk vermoeden van schuld bestaat."
WIKIPEDIA = {
    "provider": "Wikipedia",
    "url": "https://nl.wikipedia.org/wiki/Verdachte",
    "title": "Wikipedia",
    "snippet": "Een verdachte is iemand die verdacht wordt van een strafbaar feit.",
    "score": 1.0,
}
WIKTIONARY = {
    "provider": "Wiktionary",
    "url": "https://nl.wiktionary.org/wiki/verdachte",
    "title": "verdachte (wiktionary)",
    "snippet": "verdachte: iemand die van iets verdacht wordt.",
    "score": 0.95,
}
BRAVE = {
    "provider": "Brave Search",
    "url": "https://example.org/verdachte",
    "title": "Zoekresultaat verdachte",
    "snippet": "Algemene uitleg over de verdachte in het strafproces.",
    "score": 0.9,
}
WETTEN = {
    "provider": "Wetgeving.nl",
    "url": "https://wetten.overheid.nl/BWBR0001903/2026-07-01#Artikel27",
    "title": "Wetboek van Strafvordering art. 27",
    "snippet": "Als verdachte wordt aangemerkt degene te wiens aanzien ...",
    "score": 0.6,
}


def _chunk(chunk_id: int, artikel: str, score: float) -> dict:
    return {
        "chunk_id": chunk_id,
        "document_id": 900,
        "bron_type": "wetgeving",
        "rechtsgebied": "Strafrecht",
        "wet_regeling": "Wetboek van Strafvordering",
        "artikel_lid": artikel,
        "chunk_text": f"Artikel {artikel}: de verdachte (fragment {chunk_id}).",
        "score": score,
    }


GAT_CHUNKS = [
    _chunk(1, "1.4.1", 0.47),
    _chunk(2, "27", 0.46),
    _chunk(3, "1.4.2", 0.41),
    _chunk(4, "27d", 0.41),
    _chunk(5, "2.5.4", 0.40),
]


class _StubBuilder:
    def build_prompt(self, begrip, context):
        return "PROMPT_BODY"


@pytest.fixture
def generate(monkeypatch):
    from voorbeelden import unified_voorbeelden

    def _cfg():
        return {
            "web_lookup": {
                "prompt_augmentation": {
                    "enabled": True,
                    "max_snippets": 5,
                    "max_tokens_per_snippet": 300,
                    "total_token_budget": 1500,
                    "prioritize_juridical": True,
                },
                "rag_injection": {
                    "max_tokens_per_chunk": 600,
                    "total_token_budget": 2500,
                    "max_chunks": 5,
                },
            }
        }

    monkeypatch.setattr(psv2, "load_web_lookup_config", _cfg)
    monkeypatch.setattr(
        unified_voorbeelden,
        "genereer_alle_voorbeelden_async",
        AsyncMock(return_value={}),
    )
    monkeypatch.setenv("RAG_MIN_SCORE", "0.3")

    async def run(*, web=(), chunks=None):
        prompt = PromptServiceV2()
        prompt.prompt_generator = _StubBuilder()
        spy = AsyncMock(wraps=prompt.build_generation_prompt)
        ai = AsyncMock()
        ai.generate_definition.return_value = AIGenerationResult(
            text=DEFINITIE, model="offline", tokens_used=1, generation_time=0.0
        )
        cleaning = AsyncMock()
        cleaning.clean_text.return_value = CleaningResult(
            original_text=DEFINITIE, cleaned_text=DEFINITIE, was_cleaned=False
        )
        validation = AsyncMock()
        validation.validate_definition.return_value = {
            "version": "1.0.0",
            "overall_score": 0.85,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": [],
            "detailed_scores": {},
            "system": {},
        }
        repo = MagicMock()
        repo.save.return_value = 42
        rag = None
        if chunks is not None:
            rag = MagicMock()
            rag.retrieve_context.return_value = SimpleNamespace(
                chunks=deepcopy(chunks), collection_id=7
            )
        web_service = SimpleNamespace(
            lookup=AsyncMock(
                return_value=[
                    LookupResult(
                        term=BEGRIP,
                        source=WebSource(
                            name=w["provider"], url=w["url"], confidence=w["score"]
                        ),
                        definition=w["snippet"],
                        metadata={"dc_title": w["title"]},
                    )
                    for w in web
                ]
            )
        )
        orch = DefinitionOrchestratorV2(
            prompt_service=SimpleNamespace(build_generation_prompt=spy),
            ai_service=ai,
            validation_service=validation,
            cleaning_service=cleaning,
            repository=repo,
            web_lookup_service=web_service,
            rag_service=rag,
            config=OrchestratorConfig(
                enable_feedback_loop=False, enable_enhancement=False
            ),
        )
        response = await orch.create_definition(
            GenerationRequest(
                id="def844",
                begrip=BEGRIP,
                ontologische_categorie="type",
                organisatorische_context=["OM"],
                rag_collection_id=7 if chunks is not None else None,
            ),
        )
        assert response.success, response.error
        return SimpleNamespace(
            md=repo.save.call_args.args[0].metadata,
            context=spy.call_args.kwargs["context"],
            prompt_text=ai.generate_definition.call_args.kwargs["prompt"],
        )

    return run


def _labels(bronnen):
    return [b.get("artikel_lid") or b.get("title") for b in bronnen]


async def test_gat_scenario_weergave_wetsartikelen_boven_wikipedia(generate):
    result = await generate(web=[WIKIPEDIA], chunks=GAT_CHUNKS)
    assert _labels(result.md["sources"]) == [
        "1.4.1",
        "27",
        "1.4.2",
        "27d",
        "2.5.4",
        "Wikipedia",
    ]
    # Opslag en weergave delen dezelfde volgorde.
    assert _labels(result.md["provenance_sources"]) == _labels(result.md["sources"])


async def test_gat_scenario_prompt_wetsartikelen_boven_wikipedia(generate):
    result = await generate(web=[WIKIPEDIA], chunks=GAT_CHUNKS)
    receipt = result.md["source_receipt"]
    assert [(r["nr"], r["source_type"]) for r in receipt["sources"]] == [
        (1, "rag"),
        (2, "rag"),
        (3, "rag"),
        (4, "rag"),
        (5, "rag"),
        (6, "web"),
    ]
    tekst = result.prompt_text
    assert tekst.index("Artikel 1.4.1: de verdachte") < tekst.index(
        WIKIPEDIA["snippet"]
    )
    # De kwitantie koppelt na het herordenen nog steeds elke bron.
    assert result.md["source_receipt_correlation"]["verified"] == 6
    assert result.md["source_receipt_correlation"]["unmatched"] == 0
    nrs = {
        b.get("artikel_lid") or b["title"]: b["receipt_nr"]
        for b in result.md["sources"]
    }
    assert nrs["1.4.1"] == 1 and nrs["Wikipedia"] == 6


async def test_webbron_van_wetgevingsdomein_haalt_top_k_en_staat_bovenaan(generate):
    # Webscore van wetten.overheid.nl (0.6) is lager dan die van drie algemene
    # webbronnen; top_k = 3. Vóór DEF-844 viel zij buiten de prompt.
    result = await generate(web=[WIKIPEDIA, WIKTIONARY, BRAVE, WETTEN])
    web_ctx = result.context["web_lookup"]["sources"]
    assert web_ctx[0]["url"] == WETTEN["url"]
    assert web_ctx[0]["used_in_prompt"] is True
    bronnen = result.md["sources"]
    assert bronnen[0]["url"] == WETTEN["url"]
    assert bronnen[0]["used_in_prompt"] is True
    tekst = result.prompt_text
    assert tekst.index(WETTEN["snippet"][:30]) < tekst.index(WIKIPEDIA["snippet"])


async def test_bekendmaking_buiten_overheid_nl_staat_ook_in_prompt_voor_wikipedia(
    generate,
):
    # Host zonder "overheid" in de naam: de oude gezagsvoorkeur van de
    # promptservice zag haar niet, waardoor Wikipedia (1.00) in de prompt
    # vóór de bekendmaking (0.5) bleef staan.
    bekendmaking = {
        "provider": "Brave Search",
        "url": "https://zoek.officielebekendmakingen.nl/stb-2026-1.html",
        "title": "Staatsblad 2026, 1",
        "snippet": "Wet van 1 januari 2026 tot wijziging van het Wetboek van "
        "Strafvordering.",
        "score": 0.5,
    }
    result = await generate(web=[WIKIPEDIA, bekendmaking])
    assert [b["url"] for b in result.md["sources"]] == [
        bekendmaking["url"],
        WIKIPEDIA["url"],
    ]
    # Promptvolgorde = webkanaalvolgorde (bekendmaking op index 0).
    records = result.md["source_receipt"]["sources"]
    assert [r["input_index"] for r in records] == [0, 1]
    tekst = result.prompt_text
    assert tekst.index("Wet van 1 januari 2026") < tekst.index(WIKIPEDIA["snippet"])


async def test_zonder_rag_en_wetgeving_blijft_webvolgorde_ongewijzigd(generate):
    result = await generate(web=[WIKIPEDIA, WIKTIONARY, BRAVE])
    assert [b["url"] for b in result.md["sources"]] == [
        WIKIPEDIA["url"],
        WIKTIONARY["url"],
        BRAVE["url"],
    ]
    assert [b["used_in_prompt"] for b in result.md["sources"]] == [True] * 3
