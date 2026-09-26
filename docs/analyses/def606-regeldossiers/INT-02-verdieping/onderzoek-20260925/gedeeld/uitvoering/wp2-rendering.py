"""DEF-771 WP2 — schrijft de werkelijk gerenderde INT-02-sectie weg.

Echte JSONBasedRulesModule.execute met juridische context (INT-02 wordt anders
niet getoond, DEF-770), met en zonder voorbeelden. Ook de INT-01-sectie (voor
het DEF-612-voorbeeldconflict). Geen modelaanroep. Weigert te overschrijven.

Gebruik (vanuit de app-root): .venv/bin/python <dit script> <uitvoermap>
"""

import sys
from pathlib import Path

sys.path.insert(0, "src")

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.json_based_rules_module import (
    JSONBasedRulesModule,
)
from toetsregels.rule_cache import get_rule_cache

doel = Path(sys.argv[1])
get_rule_cache().clear_cache()
for include_examples, naam in ((True, "met"), (False, "zonder")):
    module = JSONBasedRulesModule("INT", "integrity_rules", "INT", "🔒", "INT", 70)
    module.initialize({"include_examples": include_examples})
    context = ModuleContext(
        begrip="stelselmatige dader",
        enriched_context=EnrichedContext(
            base_context={"juridisch": ["Strafrecht"]},
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={},
        ),
        config=UnifiedGeneratorConfig(),
        shared_state={},
    )
    uitvoer = module.execute(context)
    assert uitvoer.success
    for regel, volgende in (("INT-01", "INT-02"), ("INT-02", "INT-03")):
        sectie = uitvoer.content.split(f"🔹 **{regel}")[1].split(f"🔹 **{volgende}")[0]
        pad = doel / f"wp2-rendering-{regel.lower()}-{naam}-voorbeelden.txt"
        if pad.exists():
            raise SystemExit(f"{pad} bestaat al; niet overschreven")
        pad.write_text(f"🔹 **{regel}{sectie}", encoding="utf-8")
        print(pad)
