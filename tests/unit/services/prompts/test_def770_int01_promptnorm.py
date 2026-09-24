"""DEF-770: werkelijke INT-01-promptuitvoer; geen claim over modelkwaliteit.

Een promptwijziging bewijst geen betere generatie (dat vraagt de G24-proef).
Deze tests bewijzen alleen dat generatie en toetsing dezelfde norm spreken:
het getoonde goede voorbeeld is voor de evaluator één zin, het foute voorbeeld
twee, en de instructie legt geen hoofdzinplicht of verzonnen doelgroep op.
"""

import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule
from services.validation.evaluators.sentence_boundary import segmenteer

pytestmark = [pytest.mark.unit]


def _context() -> ModuleContext:
    return ModuleContext(
        begrip="transitie-eis",
        enriched_context=EnrichedContext(
            base_context={},
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={},
        ),
        config=UnifiedGeneratorConfig(),
        shared_state={},
    )


def _int01_sectie() -> str:
    module = JSONBasedRulesModule("INT", "integrity_rules", "INT", "🔒", "INT", 70)
    output = module.execute(_context())
    assert output.success
    return output.content.split("🔹 **INT-01")[1].split("🔹 **INT-02")[0]


def test_instructie_zonder_hoofdzinplicht_en_zonder_verzonnen_doelgroep():
    sectie = _int01_sectie()
    assert "één compacte zin in de geldende substitutiestijl" in sectie
    assert "begrijpelijk voor de vastgelegde doelgroep" in sectie
    assert "zelfstandige hoofdzin is niet vereist" in sectie
    assert "registratiecontext is geen doelgroep" in sectie
    assert "vakpubliek" not in sectie
    assert "behoud negaties en de bronbetekenis" in sectie
    assert "verschil met een verwant begrip" in sectie
    assert "Formuleer de definitie als één enkele, begrijpelijke zin" not in sectie


def test_voorbeeldpaar_zonder_label_en_gelijk_aan_toetsing():
    sectie = _int01_sectie()
    goed = next(r for r in sectie.splitlines() if r.strip().startswith("✅"))
    fout = next(r for r in sectie.splitlines() if r.strip().startswith("❌"))
    assert "transitie-eis:" not in goed
    assert goed.strip().removeprefix("✅").strip().startswith("eis die")
    # G spreekt T niet tegen: het goede voorbeeld is voor de evaluator één
    # zin, het foute voorbeeld heeft precies één zekere tweede zin.
    goed_seg = segmenteer(goed.strip().removeprefix("✅").strip())
    fout_seg = segmenteer(fout.strip().removeprefix("❌").strip())
    assert not goed_seg.zekere_grenzen and not goed_seg.onzekere_grenzen
    assert len(fout_seg.zekere_grenzen) == 1
