"""Model-onafhankelijke synoniem-onderzoeksprompt (DEF-459).

Losstaande builder — gaat NIET door PromptServiceV2/PromptOrchestrator en
raakt daarmee de RAG-injectie noch de KRITIEKE definitie-prompt-modules.
Output is een (system_prompt, user_prompt)-paar voor
AIServiceV2.generate_definition(prompt=user, system_prompt=system).
"""

from __future__ import annotations

_SYSTEM_PROMPT = (
    "Je bent een expert in Nederlands juridisch taalgebruik en terminologie. "
    "Je taak is het voorstellen van synoniemen voor een juridische term: woorden "
    "of uitdrukkingen die in juridische context dezelfde of vrijwel dezelfde "
    "betekenis dragen. Je bent precies en conservatief: liever weinig sterke "
    "synoniemen dan veel zwakke. Je verzint geen termen die niet echt gangbaar zijn."
)

_JSON_INSTRUCTIE = (
    "Antwoord UITSLUITEND met geldige JSON in exact dit formaat, zonder extra "
    "tekst eromheen:\n"
    "{\n"
    '  "synoniemen": [\n'
    '    {"synoniem": "<term>", "confidence": <0.0-1.0>, '
    '"rationale": "<korte juridische onderbouwing in het Nederlands>"}\n'
    "  ]\n"
    "}\n"
    "Regels:\n"
    "- confidence is een getal tussen 0.0 en 1.0 (mate van semantische "
    "gelijkwaardigheid in juridische context).\n"
    "- Geef geen antoniemen, hyperoniemen of losjes verwante termen.\n"
    "- Laat de lijst leeg ([]) als er geen goede synoniemen zijn."
)


def build_synonym_research_prompt(
    term: str,
    definitie: str | None = None,
    juridische_context: list[str] | None = None,
    min_count: int = 5,
) -> tuple[str, str]:
    """Bouw (system_prompt, user_prompt) voor synoniem-onderzoek.

    Args:
        term: De juridische term waarvoor synoniemen gezocht worden.
        definitie: Optionele definitie van de term (extra betekenis-anker).
        juridische_context: Optionele lijst juridische/wettelijke context-items.
        min_count: Streefaantal synoniemen (indicatief in de prompt).
    """
    regels: list[str] = [
        f"Zoek synoniemen voor de juridische term: '{term}'.",
        f"Streef naar ongeveer {min_count} synoniemen, maar kwaliteit boven kwantiteit.",
    ]
    if definitie:
        regels.append(f"Definitie van de term (betekenis-anker): {definitie}")
    if juridische_context:
        context_str = "; ".join(c for c in juridische_context if c)
        if context_str:
            regels.append(f"Relevante juridische context: {context_str}")

    user_prompt = "\n".join(regels) + "\n\n" + _JSON_INSTRUCTIE
    return _SYSTEM_PROMPT, user_prompt
