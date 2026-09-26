"""DEF-771 WP2: werkelijke INT-02-promptuitvoer op moduleniveau.

Besluit B4 (25 september 2026): de hardgecodeerde INT-02-generatie-instructie
wordt de G-tekst uit synthese v5 §3 (na SC-C-02). De verwachte G wordt hier
rechtstreeks uit die getrackte synthese gelezen, zodat er geen tweede lange
tekstkopie ontstaat.

Wat deze tests bewijzen: de gerenderde INT-02-sectie bevat de exacte G, niet
langer het vormverbod op voorwaardewoorden, behoudt het één-zin-uitvoercontract
en toont de recordvoorbeelden alleen wanneer die zijn ingeschakeld. Wat ze niet
bewijzen: beter modelgedrag, juridische juistheid of de volledige verzonden
prompt.
"""

import json
from pathlib import Path

import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule
from toetsregels.rule_cache import get_rule_cache

pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def _verse_regelcache():
    # De FileCache in cache/ kan anders een ouder INT-02-record tonen.
    get_rule_cache().clear_cache()


ROOT = Path(__file__).resolve().parents[4]
SYNTHESE = (
    ROOT / "docs/analyses/def606-regeldossiers/INT-02-verdieping"
    "/onderzoek-20260925/gedeeld/gezamenlijke-synthese-v5.md"
)
OUDE_INSTRUCTIE = (
    "Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij', "
    "'alleen als'"
)
EEN_ZIN = (
    "Lever uitsluitend de definitiekern als één zin, zonder vraag, "
    "bronverantwoording, onzekerheidsmelding of toelichting."
)


def _g_uit_synthese() -> str:
    regels = [
        r
        for r in SYNTHESE.read_text(encoding="utf-8").splitlines()
        if r.startswith("> Beschrijf wat het begrip is met de kenmerken")
    ]
    assert len(regels) == 1, "G-paragraaf niet eenduidig in synthese §3"
    return regels[0].removeprefix("> ")


def _record() -> dict:
    pad = ROOT / "src/toetsregels/regels/INT-02.json"
    return json.loads(pad.read_text(encoding="utf-8"))


def _int02_sectie(include_examples: bool) -> str:
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
    output = module.execute(context)
    assert output.success
    assert OUDE_INSTRUCTIE not in output.content
    return output.content.split("🔹 **INT-02")[1].split("🔹 **INT-03")[0]


@pytest.mark.parametrize("include_examples", [True, False])
def test_int02_sectie_bevat_exacte_g_en_een_zin_contract(include_examples):
    sectie = _int02_sectie(include_examples)
    g = _g_uit_synthese()
    assert f"\n- **Instructie:** {g}\n" in sectie
    assert EEN_ZIN in g
    assert f"\n- {_record()['uitleg']}\n" in sectie


@pytest.mark.parametrize("include_examples", [True, False])
def test_int02_voorbeelden_volgen_de_instelling(include_examples):
    regels = _int02_sectie(include_examples).splitlines()
    goed = [r.strip().removeprefix("✅ ") for r in regels if r.strip()[:1] == "✅"]
    fout = [r.strip().removeprefix("❌ ") for r in regels if r.strip()[:1] == "❌"]
    record = _record()
    if include_examples:
        assert goed == record["goede_voorbeelden"]
        assert fout == record["foute_voorbeelden"]
    else:
        assert goed == [] and fout == []
