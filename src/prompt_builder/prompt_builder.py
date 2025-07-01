import os
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from typing import Optional, List, Dict
from config.verboden_woorden import laad_verboden_woorden

# ✅ Initialiseer OpenAI-client pas wanneer nodig
load_dotenv()
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _get_openai_client() -> OpenAI:
    """
    ✅ Initialiseert OpenAI-client als die nog niet bestond.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY ontbreekt. Zet deze in .env of je CI-secrets.")
    return OpenAI(api_key=api_key)

# ✅ Toegestane toetsregels voor AI-generatie van definities
TOEGESTANE_REGELS_VOOR_PROMPT = {
    "CON-01", "CON-02",
    "ESS-01", "ESS-02", "ESS-04", "ESS-05",
    "INT-01", "INT-02", "INT-03", "INT-04", "INT-06", "INT-07", "INT-08",
    "SAM-01", "SAM-05",
    "STR-01", "STR-02", "STR-03", "STR-04", "STR-05", "STR-06", "STR-07", "STR-08", "STR-09",
    "ARAI01", "ARAI02", "ARAI02SUB1", "ARAI02SUB2", "ARAI03", "ARAI04", "ARAI04SUB1", "ARAI05", "ARAI06"
}

# ✅ Actuele lijst van context-afkortingen en hun betekenissen
AFKORTINGEN = {
    "OM": "Openbaar Ministerie",
    "ZM": "Zittende Magistratuur",
    "3RO": "Samenwerkingsverband Reclasseringsorganisaties",
    "DJI": "Dienst Justitiële Inrichtingen",
    "KMAR": "Koninklijke Marechaussee",
    "CJIB": "Centraal Justitieel Incassobureau",
    "AVG": "Algemene verordening gegevensbescherming"
}

def bepaal_term_type(begrip: str) -> str:
    """
    ✅ Bepaalt of begrip een werkwoord, deverbaal of naamwoord is.
    """
    txt = begrip.strip().lower()
    if len(txt) > 4 and txt.endswith("en") and not txt.endswith(("ing", "atie", "isatie")):
        return "werkwoord"
    if txt.endswith(("ing", "atie", "isatie")):
        return "deverbaal"
    return "anders"

def filter_toetsregels_voor_prompt(alle_regels: dict) -> dict:
    """
    ✅ Filtert alleen de regels die geschikt zijn voor AI-generatie.
    """
    return {k: v for k, v in alle_regels.items() if k in TOEGESTANE_REGELS_VOOR_PROMPT}

def voeg_contextverboden_toe(prompt: str, context_term: Optional[str]) -> str:
    """
    ✅ Voegt verbod toe voor contextterm én bijbehorende betekenis (indien afkorting).
    Alleen als die term opgegeven is als context.
    """
    if not context_term:
        return prompt
    context_clean = context_term.strip().upper()
    forbidden = [context_clean]
    if context_clean in AFKORTINGEN:
        forbidden.append(AFKORTINGEN[context_clean])
    for term in forbidden:
        prompt += f"- Gebruik de term '{term}' niet letterlijk in de definitie.\n"
    return prompt

def bouw_prompt_met_gesplitste_richtlijnen(
    begrip: str,
    context: Optional[str],
    juridische_context: Optional[str],
    wettelijke_basis: Optional[str],
    web_uitleg: str,
    toetsregels: dict
) -> str:
    """
    ✅ Bouwt een robuuste instructieprompt voor GPT o.b.v. geselecteerde regels en context.
    """

    term_type = bepaal_term_type(begrip)
    relevante_regels = filter_toetsregels_voor_prompt(toetsregels)
    verboden_startwoorden = laad_verboden_woorden()

    # 1️⃣ Rol en term-instructie
    prompt = (
        "Je bent een expert in beleidsmatige definities voor overheidsgebruik.\n"
        "Formuleer een definitie in één enkele zin, zonder toelichting.\n"
    )
    if term_type == "werkwoord":
        prompt += "Als het begrip een handeling beschrijft, definieer het dan als proces of activiteit.\n"
    elif term_type == "deverbaal":
        prompt += "Als het begrip een resultaat is, beschrijf het dan als uitkomst van een proces.\n"
    else:
        prompt += "Gebruik een zakelijke en generieke stijl voor het definiëren van dit begrip.\n"

    # 2️⃣ Contextvermelding
    kaders = []
    if context:
        kaders.append(f"binnen {context}")
    if juridische_context:
        kaders.append(f"in een {juridische_context.lower()} context")
    if wettelijke_basis:
        kaders.append(f"met wettelijke basis {wettelijke_basis}")
    if kaders:
        prompt += "\n📌 Context: " + " en ".join(kaders) + "\n"

    # 3️⃣ Relevante richtlijnen
    prompt += "\n### ✅ Richtlijnen voor de definitie:\n"
    for regel_id, regel in relevante_regels.items():
        prompt += f"\n🔹 **{regel_id} – {regel.get('naam')}**\n"
        prompt += f"– {regel.get('uitleg')}\n"
        if 'toetsvraag' in regel:
            prompt += f"– Toetsvraag: {regel['toetsvraag']}\n"
        if 'goede_voorbeelden' in regel:
            prompt += "– Goede voorbeelden:\n"
            for vb in regel['goede_voorbeelden']:
                prompt += f"  ✅ {vb}\n"
        if 'foute_voorbeelden' in regel:
            prompt += "– Foute voorbeelden:\n"
            for vb in regel['foute_voorbeelden']:
                prompt += f"  ❌ {vb}\n"
    # 💚 3b. Expliciete instructie voor ESS-02 (ontologische categorie)
    prompt += (
        "\n### 📐 Let op betekenislaag (ESS-02 – Ontologische categorie):\n"
        "Indien een begrip meerdere ontologische categorieën kan aanduiden, "
        "moet uit de definitie ondubbelzinnig blijken welke van deze vier bedoeld wordt:\n"
        "• type (soort),\n"
        "• exemplaar (specifiek geval),\n"
        "• proces (activiteit), of\n"
        "• resultaat (uitkomst).\n"
        "Gebruik formuleringen zoals:\n"
        "- 'is een activiteit waarbij...'\n"
        "- 'is het resultaat van...'\n"
        "- 'betreft een specifieke soort...'\n"
        "- 'is een exemplaar van...'\n"
    )
# ✅ Stuurt GPT aan om expliciete ontologische markers toe te voegen ter ondersteuning van ESS-02
    # 4️⃣ Webuitleg
    if web_uitleg.strip():
        prompt += f"\n📎 Achtergrond (niet letterlijk overnemen):\n{web_uitleg.strip()}\n"

    # 5️⃣ Veelgemaakte fouten
    prompt += "\n### ⚠️ Veelgemaakte fouten (vermijden!):\n"
    prompt += "- Begin niet met een lidwoord (‘de’, ‘het’, ‘een’)\n"
    prompt += "- Gebruik geen koppelwerkwoord aan het begin (‘is’, ‘betekent’, ‘omvat’)\n"
    prompt += "- Herhaal het begrip niet letterlijk\n"
    prompt += "- Gebruik geen synoniem als definitie\n"
    prompt += "- Vermijd containerbegrippen zonder concretisering (‘proces’, ‘activiteit’, ‘ding’)\n"
    prompt += "- Vermijd bijzinnen zoals 'die', 'waarin', 'waarbij', 'zoals' – schrijf bondig en zelfstandig.\n"
    prompt += "- Schrijf in het enkelvoud. Gebruik de infinitief als het begrip een werkwoord is.\n"
    for woord in verboden_startwoorden:
        prompt += f"- Start niet met '{woord}'\n"

    # 6️⃣ Dynamisch contextverbod
    prompt = voeg_contextverboden_toe(prompt, context)
    prompt = voeg_contextverboden_toe(prompt, juridische_context)
    prompt = voeg_contextverboden_toe(prompt, wettelijke_basis)

    # 7️⃣ Validatiematrix
    prompt += (
        "\n| Probleem                             | Afgedekt? | Toelichting                                |\n"
        "|--------------------------------------|-----------|---------------------------------------------|\n"
        "| Start met begrip                     | ✅        | Vermijd cirkeldefinities                     |\n"
        "| Abstracte constructies               | ✅        | 'proces waarbij', 'handeling die', enz.      |\n"
        "| Koppelwerkwoorden aan het begin      | ✅        | 'is', 'omvat', 'betekent'                    |\n"
        "| Lidwoorden aan het begin             | ✅        | 'de', 'het', 'een'                           |\n"
        "| Letterlijke contextvermelding        | ✅        | Noem context niet letterlijk                 |\n"
        "| Afkortingen onverklaard              | ✅        | Licht afkortingen toe in de definitie       |\n"
        "| Subjectieve termen                   | ✅        | Geen 'essentieel', 'belangrijk', 'adequaat' |\n"
        "| Bijzinconstructies                   | ✅        | Vermijd 'die', 'waarin', 'zoals' enz.       |\n"
    )

    # 8️⃣ Slotinstructie
    prompt += f"\n✏️ Geef nu de definitie van het begrip **{begrip}** in één enkele zin, zonder toelichting."

    # 9️⃣ Promptmetadata
    prompt += "\n\n🆔 Promptmetadata:"
    prompt += f"\n– Begrip: {begrip}"
    if context:
        prompt += f"\n– Context: {context}"
    if juridische_context:
        prompt += f"\n– Juridisch: {juridische_context}"
    if wettelijke_basis:
        prompt += f"\n– Wettelijke basis: {wettelijke_basis}"
    prompt += f"\n– Termtype: {term_type}"

    return prompt

def stuur_prompt_naar_gpt(
    prompt: str,
    model: str = "gpt-4",
    temperature: float = 0.4,
    max_tokens: int = 300
) -> str:
    """
    ✅ Roept het GPT-model aan en retourneert de gegenereerde tekst.
    """
    try:
        resp = _client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except OpenAIError as e:
        raise RuntimeError(f"GPT-aanroep mislukt: {e}") from e