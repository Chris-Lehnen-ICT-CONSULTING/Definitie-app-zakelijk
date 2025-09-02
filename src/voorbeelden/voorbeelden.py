import os
import re

from openai import OpenAI, OpenAIError

# ✅ Initialiseer de OpenAI-client met de api_key uit de omgeving
_client = OpenAI(
    api_key=(os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_PROD"))
)


def genereer_voorbeeld_zinnen(
    begrip: str, definitie: str, context_dict: dict[str, list[str]]
) -> list[str]:
    prompt = (
        f"Geef 2 tot 3 korte voorbeeldzinnen waarin het begrip '{begrip}' "
        "op een duidelijke manier wordt gebruikt.\n"
        "Gebruik onderstaande contexten alleen als achtergrond, maar noem ze niet letterlijk:\n\n"
        f"Definitie ter referentie: {definitie}\n"
        f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
        f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
        f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
    )
    try:
        resp = _client.chat.completions.create(
            model=None,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200,
        )
        blob = resp.choices[0].message.content.strip()
    except OpenAIError as e:
        return [f"❌ Fout bij genereren korte voorbeelden: {e}"]

    # splitsen op regels en nummering weghalen
    zinnen: list[str] = []
    for line in blob.splitlines():
        # als AI “1. ...” of “- ...” gebruikt, strip dat eraf
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
        f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
        f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
        f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
    )
    try:
        resp = _client.chat.completions.create(
            model=None,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=800,
        )
        text = resp.choices[0].message.content.strip()
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
        f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
        f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
        f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
    )
    try:
        resp = _client.chat.completions.create(
            model=None,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300,
        )
        text = resp.choices[0].message.content.strip()
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
