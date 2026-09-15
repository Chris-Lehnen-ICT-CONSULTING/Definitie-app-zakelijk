"""DEF-743 pakket E (vervolg) — geen betrouwbaarheidslabel op contextbronnen.

`ContextAwarenessModule` rendert `ContextSource`-inhoud (o.a. de
documentsamenvatting uit `request.document_context`, met een vaste
confidence van 0.9) in het rijke pad. Dat label (`[high] Document
(confidence=0.90)`) suggereerde gezag/betrouwbaarheid uit een constante.
De presentatie is nu neutraal: route + aangeleverde inhoud, binnen het
`context`-datablok, met de CON-01-norm en de datablok-afspraak intact.
"""

from __future__ import annotations

import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import ContextSource, EnrichedContext
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.context_awareness_module import ContextAwarenessModule

pytestmark = [pytest.mark.unit]

DOCUMENT = "Toezichthouder: persoon bij of krachtens wettelijk voorschrift belast."
VERBODEN_LABELS = (
    "[high]",
    "[medium]",
    "[low]",
    "confidence=",
    "(confidence",
    "level=",
)


def _ctx(base_items: int, sources: int, expanded: int) -> ModuleContext:
    enriched = EnrichedContext(
        base_context={
            "organisatorisch": [f"Organisatie {i}" for i in range(base_items)],
            "juridisch": [],
            "wettelijk": [],
        },
        sources=[
            ContextSource(
                source_type="document",
                confidence=0.9,
                content=DOCUMENT,
                metadata={"source": "user_document"},
            )
            for _ in range(sources)
        ],
        expanded_terms={f"K{i}": f"V{i}" for i in range(expanded)},
        confidence_scores={"document": 0.9} if sources else {},
        metadata={},
    )
    return ModuleContext(
        begrip="toezichthouder",
        enriched_context=enriched,
        config=UnifiedGeneratorConfig(),
        shared_state={},
    )


def _datablok(content: str) -> str:
    start = content.index("<context>") + len("<context>")
    return content[start : content.index("</context>", start)]


@pytest.mark.parametrize(
    ("base_items", "sources", "expanded", "niveau"),
    [
        (10, 2, 5, "rich"),
        (2, 1, 0, "moderate"),
        (0, 1, 0, "minimal"),
    ],
)
def test_contextbron_wordt_neutraal_gepresenteerd(
    base_items, sources, expanded, niveau
):
    mod = ContextAwarenessModule()
    mod.initialize({"include_abbreviations": True})
    out = mod.execute(_ctx(base_items, sources, expanded))
    assert out.success is True
    assert out.metadata["formatting_level"] == niveau, out.metadata

    tekst = out.content
    for label in VERBODEN_LABELS:
        assert label not in tekst, label
    assert "0.90" not in tekst
    # Route + aangeleverde inhoud, binnen het datablok.
    binnen = _datablok(tekst)
    assert "Toezichthouder: persoon bij of krachtens" in binnen
    assert "ocument" in binnen  # "Document:"/"document:" als route
    # CON-01-norm en datablok-afspraak blijven.
    assert "inhoudelijk noodzakelijk" in tekst
    assert "registratiecontext" in tekst


def test_rijk_pad_toont_route_en_inhoud_zonder_gezagsclaim():
    mod = ContextAwarenessModule()
    mod.initialize({})
    out = mod.execute(_ctx(10, 1, 5))
    assert out.metadata["formatting_level"] == "rich"
    regels = [r for r in _datablok(out.content).splitlines() if "Toezichthouder" in r]
    assert len(regels) == 1
    regel = regels[0]
    assert regel.strip().startswith("Document:")
    assert "confidence" not in regel
    assert "[" not in regel.split(":", 1)[0]
