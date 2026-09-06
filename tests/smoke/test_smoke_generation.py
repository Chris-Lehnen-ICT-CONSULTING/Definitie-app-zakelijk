#!/usr/bin/env python
"""Smoke test voor definitie generatie na US-043 wijzigingen.

DEF-519 — deze node is `live`
-----------------------------
Deze test doet naar eigen zeggen een ECHTE AI-generatie en rekent op een echte
providerrespons. Dat is precies wat een verplichte gate niet mag starten: het
raakt een externe dienst en kost geld. Anders dan het gemockte Brave-geval —
dat op `MockBraveService` draait en daarom required bleef — is hier geen enkele
providergrens vervangen. De node krijgt daarom de `live`-marker en heeft geen
runnerprofiel; er wordt hier geen echte call uitgevoerd of gerepareerd.

De marker is geen skip en geen xfail: er wordt niets stilgezet en de positieve
verwachting (`assert await _run_generation_smoke()`) blijft onverkort staan.
Eigenaar, reden, trigger en herbeoordelingsdatum staan in
`docs/testing/def519-testdispositions.json`.

De `live`-marker is niet de enige rem
-------------------------------------
Hij houdt deze node uit de runnerprofielen (`unit`, `integration`,
`acceptance-smoke`, `contract`), maar niet uit élke automatische start: de
bestaande pre-commit-hook draait `pytest -m smoke` zónder `not live`. De
skip-guard hieronder is daar de enige rem, en die toetste alleen of er íéts in
de omgeving stond. De offline-bootstrap zet providerkeys hard op `dummy` — niet
leeg — dus de guard liet de node door en de test viel vervolgens om op de
geblokkeerde uitgaande call (`root-final-acceptance-01/make.log`).

De guard toetst nu de sleutelvórm, hetzelfde contract dat
`tests/integration/test_synonym_suggester_e2e.py` al hanteert. Dat is géén
bewijs dat een sleutel geldig is of dat er budget is — het is alleen een harde
afwijzing van dummyconfiguratie. Bewezen door
`tests/ci/test_offline_gate_bootstrap.py`, dat exact de pre-commit-opdracht
onder de echte gate draait met de providerfunctie vervangen door een spy.

Openstaande diagnostiekbeperking, hier vastgelegd en bewust niet nu gerepareerd
(dat vraagt een goedgekeurde live-run om te kunnen verifiëren): de
uitkomstafhandeling hieronder gebruikt `result.get(...)`, het oude
dict-contract. `generate_definition` levert inmiddels een
`DefinitionResponseV2`; die heeft geen `.get`. Ook zonder providerprobleem zou
deze body dus op het responsecontract stuklopen.
"""

import asyncio
import logging
import os
import sys

import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.live]

# Skip-guard: deze smoke-test doet een ECHTE AI-generatie (kost API-calls).
# DEF-519: op sleutelvórm, hetzelfde contract als test_synonym_suggester_e2e.py,
# zodat dummyconfiguratie (`dummy`, lege string) er niet doorheen komt. Dit zegt
# niets over geldigheid of budget; het is alleen een harde afwijzing van een
# niet-live omgeving.
_HAS_API_KEY = os.getenv("OPENAI_API_KEY", "").startswith("sk-") or os.getenv(
    "ANTHROPIC_API_KEY", ""
).startswith("sk-ant-")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, "src")


async def _run_generation_smoke() -> bool:
    """Test basis definitie generatie functionaliteit. Returnt True bij succes."""

    from services.service_factory import get_definition_service

    # Get V2 service (always V2 na US-043)
    service = get_definition_service()

    # Test context (list-based per US-043)
    context_dict = {
        "organisatorisch": ["Openbaar Ministerie"],
        "juridisch": ["Strafrecht"],
        "wettelijk": ["Wetboek van Strafrecht"],
    }

    logger.info("Starting smoke test for definition generation...")

    try:
        # Generate definition (use generate_definition method)
        result = await service.generate_definition(
            begrip="verdachte", context_dict=context_dict
        )

        # Check result
        if result and result.get("success"):
            logger.info("✅ Generation successful!")
            logger.info(
                f"  Definitie: {result.get('definitie_gecorrigeerd', '')[:100]}..."
            )

            # Check validation
            if result.get("validation_details"):
                score = result["validation_details"].get("overall_score", 0)
                logger.info(f"  Validation score: {score}")

            # Check voorbeelden
            voorbeelden = result.get("voorbeelden", {})
            if voorbeelden:
                logger.info(f"  Voorbeelden types: {list(voorbeelden.keys())}")

            return True
        logger.error(f"❌ Generation failed: {result}")
        return False

    except Exception as e:
        logger.error(f"❌ Smoke test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.asyncio
@pytest.mark.skipif(
    not _HAS_API_KEY, reason="geen AI API-key beschikbaar (OPENAI/ANTHROPIC)"
)
async def test_smoke_generation():
    """Pytest-collecteerbare smoke-test (vereist API-key, draait via make test-smoke)."""
    assert await _run_generation_smoke(), "Definitie-generatie smoke-test faalde"


if __name__ == "__main__":
    success = asyncio.run(_run_generation_smoke())

    if success:
        print("\n" + "=" * 60)
        print("✅ SMOKE TEST PASSED - Core functionality works!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ SMOKE TEST FAILED - Core functionality broken!")
        print("=" * 60)
        sys.exit(1)
