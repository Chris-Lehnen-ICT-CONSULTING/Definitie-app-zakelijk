"""De prompt-assemblage mag niet van thread-voltooiingsvolgorde afhangen (DEF-582).

`_execute_batch_parallel` vult `outputs` in `as_completed`-volgorde. De fallback
in `_combine_outputs` — voor modules die niet in `_custom_module_order` staan —
itereerde over `outputs.items()` en erfde die niet-deterministische volgorde.

Vandaag staan alle geregistreerde modules in de vaste volgorde, dus de fallback
is dood. Precies daarom is dit een footgun: de eerstvolgende module die iemand
vergeet toe te voegen, maakt de prompt stil niet-deterministisch.
"""

import pytest

pytestmark = pytest.mark.unit

from services.prompts.modules.base_module import ModuleOutput
from services.prompts.modules.prompt_orchestrator import PromptOrchestrator


def _output(inhoud: str) -> ModuleOutput:
    return ModuleOutput(content=inhoud, metadata={})


def test_modules_buiten_de_vaste_volgorde_worden_deterministisch_geordend():
    orchestrator = PromptOrchestrator()
    orchestrator.set_module_order(["eerste"])

    # `outputs` gevuld in een volgorde die niets met de gewenste te maken heeft
    # (zoals `as_completed` doet).
    outputs = {
        "zeta": _output("Z"),
        "alpha": _output("A"),
        "eerste": _output("EERSTE"),
        "midden": _output("M"),
    }
    resultaat = orchestrator._combine_outputs(outputs)

    # De module uit de vaste volgorde staat vooraan; de rest alfabetisch.
    assert resultaat == "EERSTE\n\nA\n\nM\n\nZ"


def test_zelfde_outputs_in_andere_insertion_order_geven_dezelfde_prompt():
    """De kern: dict-insertion-order mag de prompt niet bepalen."""
    orchestrator = PromptOrchestrator()
    orchestrator.set_module_order([])

    een = {"b": _output("B"), "a": _output("A"), "c": _output("C")}
    twee = {"c": _output("C"), "b": _output("B"), "a": _output("A")}

    assert orchestrator._combine_outputs(een) == orchestrator._combine_outputs(twee)


def test_lege_en_gefaalde_outputs_blijven_weggelaten():
    orchestrator = PromptOrchestrator()
    orchestrator.set_module_order([])

    outputs = {
        "goed": _output("INHOUD"),
        "leeg": _output(""),
        "kapot": ModuleOutput(
            content="genegeerd", metadata={}, success=False, error_message="stuk"
        ),
    }
    assert orchestrator._combine_outputs(outputs) == "INHOUD"
