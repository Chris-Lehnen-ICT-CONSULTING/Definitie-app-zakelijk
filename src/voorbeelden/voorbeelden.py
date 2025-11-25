import os
import re
from typing import cast

from openai import OpenAI, OpenAIError

# Importeer context afkortingen mapping
from services.definition_generator_context import CONTEXT_AFKORTINGEN

# ✅ Initialiseer de OpenAI-client met de api_key uit de omgeving
_client = OpenAI(
    api_key=(os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_PROD"))
)

# Default model voor voorbeelden generatie
_DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _expand_context_abbreviations(context_items: list[str]) -> str:
    """
    Expandeer afkortingen in context items naar volledige namen.

    Args:
        context_items: Liste van context items (mogelijk met afkortingen)

    Returns:
        String met geëxpandeerde context items, gescheiden door komma's

    Voorbeeld:
        ["ZM", "OM"] -> "ZM (Zittende Magistratuur), OM (Openbaar Ministerie)"
    """
    if not context_items:
        return "geen"

    expanded_items = []
    for item in context_items:
        # Check of het item een bekende afkorting is
        if item in CONTEXT_AFKORTINGEN:
            # Toon zowel afkorting als volledige naam
            expanded_items.append(f"{item} ({CONTEXT_AFKORTINGEN[item]})")
        else:
            expanded_items.append(item)

    return ", ".join(expanded_items)


def genereer_voorbeeld_zinnen(
    begrip: str, definitie: str, context_dict: dict[str, list[str]]
) -> list[str]:
    prompt = (
        f"Geef 2 tot 3 korte voorbeeldzinnen waarin het begrip '{begrip}' "
        "op een duidelijke manier wordt gebruikt.\n"
        "Gebruik onderstaande contexten alleen als achtergrond, maar noem ze niet letterlijk:\n\n"
        f"Definitie ter referentie: {definitie}\n"
        f"Organisatorische context: {_expand_context_abbreviations(context_dict.get('organisatorisch', []))}\n"
        f"Juridische context:      {_expand_context_abbreviations(context_dict.get('juridisch', []))}\n"
        f"Wettelijke basis:        {_expand_context_abbreviations(context_dict.get('wettelijk', []))}"
    )
    try:
        resp = _client.chat.completions.create(
            model=_DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200,
        )
        blob = cast(str, resp.choices[0].message.content or "").strip()
    except OpenAIError as e:
        return [f"❌ Fout bij genereren korte voorbeelden: {e}"]

    # splitsen op regels en nummering weghalen
    zinnen: list[str] = []
    for line in blob.splitlines():
        # als AI "1. ..." of "- ..." gebruikt, strip dat eraf
        zin = re.sub(r"^\s*(?:\d+\.|-)\s*", "", line).strip()
        if zin:
            zinnen.append(zin)
    # fallback: retourneer de hele blob als er geen losse regels gevonden zijn
    return zinnen or [blob]


def genereer_praktijkvoorbeelden(
    begrip: str, definitie: str, context_dict: dict[str, list[str]], aantal: int = 3
) -> list[str]:
    """
    Genereert `aantal` praktijkvoorbeelden (verification by instantiation).
    Elke casus instantiëert alle elementen uit de definitie.
    Retourneert een lijst van strings, één per casus.
    """
    prompt = (
        f"Genereer {aantal} uitgewerkte praktijkvoorbeelden voor het begrip '{begrip}'\n"
        f'met definitie: "{definitie.strip()}".\n'
        "Zorg dat elk voorbeeld:\n"
        "  • Alle onderdelen uit de definitie concreet invult (dus alle variabelen).\n"
        "  • De organisatie-, juridische- en wettelijke context duidelijk bevat.\n\n"
        f"Organisatorische context: {_expand_context_abbreviations(context_dict.get('organisatorisch', []))}\n"
        f"Juridische context:      {_expand_context_abbreviations(context_dict.get('juridisch', []))}\n"
        f"Wettelijke basis:        {_expand_context_abbreviations(context_dict.get('wettelijk', []))}"
    )
    try:
        resp = _client.chat.completions.create(
            model=_DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=800,
        )
        text = cast(str, resp.choices[0].message.content or "").strip()
    except OpenAIError as e:
        return [f"❌ Fout bij genereren praktijkvoorbeelden: {e}"]

    # 🔧 Splits de respons op in afzonderlijke voorbeelden
    voorbeelden: list[str] = []
    current: list[str] = []
    # We gaan ervan uit dat de AI elk voorbeeld laat beginnen met "1.", "2.", etc.
    for line in text.splitlines():
        # nieuw voorbeeld
        if any(line.lstrip().startswith(f"{i}.") for i in range(1, aantal + 1)):
            if current:
                voorbeelden.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        voorbeelden.append("\n".join(current).strip())

    return voorbeelden


def genereer_tegenvoorbeelden(
    begrip: str, definitie: str, context_dict: dict[str, list[str]], aantal: int = 2
) -> list[str]:
    """
    Genereert 'aantal' tegenvoorbeelden waarin:
     - een of meer criteria uit de definitie niet (correct) worden ingevuld, of
     - het begrip geheel misbruikt wordt.
    Retourneert een lijst met string-beschrijvingen.
    """
    prompt = (
        f"Geef {aantal} korte tegenvoorbeelden voor het begrip '{begrip}' met definitie:\n"
        f'  "{definitie.strip()}"\n'
        "Elk voorbeeld moet kort aangeven **welke** variabelen of contextregels **niet** worden gevolgd.\n\n"
        f"Organisatorische context: {_expand_context_abbreviations(context_dict.get('organisatorisch', []))}\n"
        f"Juridische context:      {_expand_context_abbreviations(context_dict.get('juridisch', []))}\n"
        f"Wettelijke basis:        {_expand_context_abbreviations(context_dict.get('wettelijk', []))}"
    )
    try:
        resp = _client.chat.completions.create(
            model=_DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300,
        )
        text = cast(str, resp.choices[0].message.content or "").strip()
    except OpenAIError as e:
        return [f"❌ Fout bij genereren tegenvoorbeelden: {e}"]

    # 🔧 Splits de respons op in afzonderlijke voorbeelden
    voorbeelden: list[str] = []
    current: list[str] = []
    # We gaan ervan uit dat de AI elk voorbeeld laat beginnen met "1.", "2.", etc.
    for line in text.splitlines():
        # nieuw voorbeeld
        if any(line.lstrip().startswith(f"{i}.") for i in range(1, aantal + 1)):
            if current:
                voorbeelden.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        voorbeelden.append("\n".join(current).strip())

    return voorbeelden


def genereer_synoniemen(
    begrip: str, definitie: str, context_dict: dict[str, list[str]], aantal: int = 8
) -> list[str]:
    """Genereer synoniemen/naambeschrijvingen die passen bij de definitie/context."""
    prompt = (
        f"Geef {aantal} synoniemen of naambeschrijvingen voor het begrip '{begrip}'.\n"
        f"Definitie: {definitie.strip()}\n"
        "Beperk je tot termen die in juridische/overheidscontext gangbaar zijn.\n"
        "Geef één term per regel, zonder nummering of uitleg.\n\n"
        f"Context ter referentie:\n"
        f"Organisatorische context: {_expand_context_abbreviations(context_dict.get('organisatorisch', []))}\n"
        f"Juridische context:      {_expand_context_abbreviations(context_dict.get('juridisch', []))}\n"
        f"Wettelijke basis:        {_expand_context_abbreviations(context_dict.get('wettelijk', []))}"
    )
    try:
        resp = _client.chat.completions.create(
            model=_DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=200,
        )
        blob = cast(str, resp.choices[0].message.content or "").strip()
    except OpenAIError as e:
        return [f"❌ Fout bij genereren synoniemen: {e}"]

    out: list[str] = []
    for line in blob.splitlines():
        term = re.sub(r"^\s*(?:\d+\.|-)\s*", "", line).strip()
        if term:
            out.append(term)
    return out or [blob]


def genereer_antoniemen(
    begrip: str, definitie: str, context_dict: dict[str, list[str]], aantal: int = 5
) -> list[str]:
    """Genereer antoniemen of contrasterende termen voor het begrip."""
    prompt = (
        f"Geef {aantal} antoniemen of contrasterende termen bij '{begrip}'.\n"
        f"Definitie: {definitie.strip()}\n"
        "Alleen juridische/overheidsrelevante tegenhangers. Eén term per regel, geen uitleg.\n\n"
        f"Context ter referentie:\n"
        f"Organisatorische context: {_expand_context_abbreviations(context_dict.get('organisatorisch', []))}\n"
        f"Juridische context:      {_expand_context_abbreviations(context_dict.get('juridisch', []))}\n"
        f"Wettelijke basis:        {_expand_context_abbreviations(context_dict.get('wettelijk', []))}"
    )
    try:
        resp = _client.chat.completions.create(
            model=_DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=150,
        )
        blob = cast(str, resp.choices[0].message.content or "").strip()
    except OpenAIError as e:
        return [f"❌ Fout bij genereren antoniemen: {e}"]

    out: list[str] = []
    for line in blob.splitlines():
        term = re.sub(r"^\s*(?:\d+\.|-)\s*", "", line).strip()
        if term:
            out.append(term)
    return out or [blob]


def genereer_toelichting(
    begrip: str, definitie: str, context_dict: dict[str, list[str]], max_zinnen: int = 3
) -> str:
    """Genereer een korte toelichting (2-3 zinnen) bij de definitie."""
    prompt = (
        f"Schrijf een korte toelichting (max {max_zinnen} zinnen) bij de definitie van '{begrip}'.\n"
        f"Definitie: {definitie.strip()}\n"
        "Toelichting moet bondig zijn, geen herhaling van de definitie, en toepasbaarheid verduidelijken.\n\n"
        f"Context ter referentie:\n"
        f"Organisatorische context: {_expand_context_abbreviations(context_dict.get('organisatorisch', []))}\n"
        f"Juridische context:      {_expand_context_abbreviations(context_dict.get('juridisch', []))}\n"
        f"Wettelijke basis:        {_expand_context_abbreviations(context_dict.get('wettelijk', []))}"
    )
    try:
        resp = _client.chat.completions.create(
            model=_DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=220,
        )
        return cast(str, resp.choices[0].message.content or "").strip()
    except OpenAIError as e:
        return f"❌ Fout bij genereren toelichting: {e}"
