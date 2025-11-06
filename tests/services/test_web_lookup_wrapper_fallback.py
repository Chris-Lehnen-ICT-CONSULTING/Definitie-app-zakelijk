from unittest.mock import AsyncMock, patch

import pytest
from services.definition_generator_config import ContextConfig
from services.definition_generator_context import HybridContextManager
from services.interfaces import GenerationRequest, LookupResult, WebSource


@pytest.mark.asyncio()
async def test_web_lookup_wrapper_title_fallbacks():
    """Ensure web lookup wrapper formats labels without relying on r.title."""
    config = ContextConfig()
    manager = HybridContextManager(config)

    # Prepare results without a 'title' attribute; use metadata/term instead
    r1 = LookupResult(
        term="TermOnly",
        source=WebSource(name="Overheid.nl", url="", confidence=0.9),
        definition="Desc A",
        success=True,
        metadata={},
    )
    r2 = LookupResult(
        term="Context",
        source=WebSource(name="Wikipedia", url="", confidence=0.8),
        definition="Desc B",
        success=True,
        metadata={"dc_title": "Wetboek"},
    )

    with patch(
        "services.modern_web_lookup_service.ModernWebLookupService.lookup",
        new=AsyncMock(return_value=[r1, r2]),
    ):
        enriched = await manager.build_enriched_context(
            GenerationRequest(id="t1", begrip="context")
        )

    # Must include a web_lookup source and formatted content using fallbacks
    web_sources = [s for s in enriched.sources if s.source_type == "web_lookup"]
    assert web_sources, "Expected web_lookup source present"
    content = web_sources[0].content
    assert "Web informatie voor context:" in content
    # Fallback for r1: uses term when no metadata title present
    assert "TermOnly (Overheid.nl)" in content
    # r2 uses dc_title from metadata
    assert "Wetboek (Wikipedia)" in content
