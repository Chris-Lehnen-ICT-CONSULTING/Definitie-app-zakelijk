"""
Test voor verificatie van fix voor dubbele web lookup bug.

Dit test bevestigt dat:
1. HybridContextManager GEEN web lookup meer uitvoert
2. Alleen de orchestrator web lookup uitvoert
3. Prompt service de orchestrator's web lookup resultaten gebruikt
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.definition_generator_config import ContextConfig
from services.definition_generator_context import HybridContextManager
from services.interfaces import GenerationRequest

pytestmark = [pytest.mark.unit]


class TestDuplicateWebLookupFix:
    """Test suite voor verificatie van web lookup fix."""

    @pytest.mark.asyncio
    async def test_hybrid_context_manager_no_web_lookup(self):
        """
        Verificatie: HybridContextManager voert GEEN web lookup uit.

        BEFORE FIX: HybridContextManager had _web_lookup attribuut en _get_web_context methode
        AFTER FIX: Beide zijn verwijderd - web lookup is pure orchestrator responsibility
        """
        config = ContextConfig(
            enable_rule_interpretation=False, context_abbreviations={}
        )

        manager = HybridContextManager(config)

        # Verify web lookup components are removed
        assert not hasattr(
            manager, "_web_lookup"
        ), "HybridContextManager should NOT have _web_lookup attribute"
        assert not hasattr(
            manager, "_get_web_context"
        ), "HybridContextManager should NOT have _get_web_context method"
        assert not hasattr(
            manager, "_init_web_lookup"
        ), "HybridContextManager should NOT have _init_web_lookup method"

        print("✅ HybridContextManager has no web lookup components")

    @pytest.mark.asyncio
    async def test_context_manager_builds_without_web_lookup(self):
        """
        Verificatie: build_enriched_context werkt zonder web lookup.

        Context wordt gebouwd zonder web lookup execution, maar kan
        wel web lookup data ontvangen via metadata van de orchestrator.
        """
        config = ContextConfig(
            enable_rule_interpretation=False, context_abbreviations={}
        )

        manager = HybridContextManager(config)

        request = GenerationRequest(
            id="test-001",
            begrip="testverzuim",
            organisatorische_context=["Politie"],
            juridische_context=["Strafrecht"],
            wettelijke_basis=["Wetboek van Strafvordering"],
            ontologische_categorie="proces",
            actor="test_user",
        )

        # Mock web lookup to ensure it's NOT called by HybridContextManager
        with patch(
            "services.modern_web_lookup_service.ModernWebLookupService"
        ) as mock_wl:
            mock_wl.return_value.lookup = AsyncMock()

            # Build context
            enriched_context = await manager.build_enriched_context(request)

            # Verify web lookup was NOT called
            mock_wl.return_value.lookup.assert_not_called()

            # Verify context was built successfully
            assert enriched_context is not None
            assert enriched_context.base_context is not None
            assert "organisatorisch" in enriched_context.base_context

        print("✅ HybridContextManager builds context WITHOUT calling web lookup")

    @pytest.mark.asyncio
    async def test_prompt_service_uses_orchestrator_web_lookup_data(self):
        """
        Verificatie: PromptServiceV2 gebruikt web lookup data van orchestrator.

        De prompt service ontvangt web_lookup data via de context parameter
        en voegt deze toe aan enriched_context.metadata.
        """
        from services.prompts.prompt_service_v2 import PromptServiceV2

        prompt_service = PromptServiceV2()

        request = GenerationRequest(
            id="test-001",
            begrip="testverzuim",
            organisatorische_context=["Politie"],
            juridische_context=["Strafrecht"],
            wettelijke_basis=["Wetboek van Strafvordering"],
            ontologische_categorie="proces",
            actor="test_user",
        )

        # Simuleer orchestrator's web lookup data
        orchestrator_context = {
            "web_lookup": {
                "sources": [
                    {
                        "provider": "wikipedia",
                        "title": "Test artikel",
                        "url": "https://example.com",
                        "snippet": "Test snippet",
                        "score": 0.9,
                        "used_in_prompt": True,
                    }
                ],
                "top_k": 3,
                "debug": None,
            }
        }

        # Exercise source injection independently of the configured default.
        with patch.dict(prompt_service._aug_cfg, {"enabled": True}):
            result = await prompt_service.build_generation_prompt(
                request=request, feedback_history=None, context=orchestrator_context
            )

        # Verify prompt was built
        assert result is not None
        assert result.text is not None
        assert len(result.text) > 0
        assert "<bronnen>" in result.text
        assert "Test snippet" in result.text
        assert "https://example.com" in result.text

        print("✅ PromptServiceV2 uses orchestrator's web lookup data")


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(TestDuplicateWebLookupFix().test_hybrid_context_manager_no_web_lookup())
    asyncio.run(
        TestDuplicateWebLookupFix().test_context_manager_builds_without_web_lookup()
    )
    asyncio.run(
        TestDuplicateWebLookupFix().test_prompt_service_uses_orchestrator_web_lookup_data()
    )

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Duplicate web lookup fix verified!")
    print("=" * 80)
