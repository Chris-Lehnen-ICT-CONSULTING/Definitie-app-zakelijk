import os
from openai import OpenAI, OpenAIError
from config.verboden_woorden import laad_verboden_woorden
from typing import Optional, List, Dict
from dotenv import load_dotenv

def check_ascii(label: str, value: str):
    """Raise fout als string niet ASCII-safe is."""
    try:
        value.encode("ascii")
    except UnicodeEncodeError as e:
        raise RuntimeError(f"{label} bevat niet-ASCII tekens: {e}")

# 🌱 Initialiseer OpenAI-client
load_dotenv()
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 💚 --------------- VERPLAATSTE OPENAI-CLIENT ---------------  
def _get_openai_client() -> OpenAI:          # ✅ privé helper  
    """
    # ✅ Maakt OpenAI-client alléén aan wanneer hij voor het eerst nodig is.
    #    Zo kan het pakket zonder OPENAI_API_KEY geïmporteerd worden.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY ontbreekt. Zet deze variabele in .env of in je CI-secrets."
        )
    return OpenAI(api_key=api_key)
# 💚 ----------------------------------------------------------



def bepaal_term_type(begrip: str) -> str:
    """
    Classificeer het begrip via simpele regex:
      - werkwoord: eindigt op 'en' (en niet te kort)
      - deverbaal: eindigt op 'ing', 'atie', 'isatie'
      - anders: elk ander geval
    """
    txt = begrip.strip().lower()
    # ✅ heuristiek: werkwoordificale suffix
    if len(txt) > 4 and txt.endswith("en") and not txt.endswith(("ing", "atie", "isatie")):
        return "werkwoord"
    # ✅ heuristiek: deverbaal (resultaatswoord)
    if txt.endswith(("ing", "atie", "isatie")):
        return "deverbaal"
    # ✅ fallback
    return "anders"

def selecteer_essentiele_regels(toetsregels: Dict) -> List[Dict]:
    """Regels met prioriteit=hoog & aanbeveling=verplicht."""
    return [r for r in toetsregels.values()
            if r.get("prioriteit")=="hoog" and r.get("aanbeveling")=="verplicht"]

def selecteer_aanvullende_regels(toetsregels: Dict) -> List[Dict]:
    """Overige toetsregels."""
    return [r for r in toetsregels.values()
            if not (r.get("prioriteit")=="hoog" and r.get("aanbeveling")=="verplicht")]

def bouw_prompt_met_gesplitste_richtlijnen(
    begrip: str,
    context: Optional[str],
    juridische_context: Optional[str],
    wettelijke_basis: Optional[str],
    web_uitleg: str,
    regels_essentieel: List[Dict],
    regels_aanvullend: List[Dict]
) -> str:

    """
    Bouwt GPT-prompt in 7 blokken, met conditionele introductie op basis van term-type:
      1. Rol-instructie
      2. Context
      3. Essentiële regels
      4. Aanvullende richtlijnen
      5. Achtergrond (referentie)
      6. 🚫 Veelgemaakte fouten (uitgebreide lijst + matrix)
      7. Slotinstructie
    """


    """Bouwt GPT-prompt met conditionele introductie op basis van term-type."""
    # 1️⃣ Term-classificatie
    term_type = bepaal_term_type(begrip)
    header = ""
    if term_type == "werkwoord":
        header = (
            "Als dit een handeling is, beschrijf het als een proces of activiteit.\n"
        )
    elif term_type == "deverbaal":
        header = (
            "Als dit een resultaat is van een proces, beschrijf het als het resultaat of uitkomst.\n"
        )
    else:
        header = "Formuleer een generieke, zakelijke definitie in één zin.\n"

    # 🧠 1. Rol-instructie
    prompt = (
        "Je bent een expert in beleidsmatige definities voor overheidsgebruik.\n"
        "Formuleer in één zin een heldere, zakelijke definitie.\n"
    )

    # 📌 2. Context
    kaders = []
    if context:
        kaders.append(f"binnen {context}")
    if juridische_context:
        kaders.append(f"in een {juridische_context.lower()} context")
    if wettelijke_basis:
        kaders.append(f"met wettelijke basis {wettelijke_basis}")
    if kaders:
        prompt += "\n📌 Context: " + " en ".join(kaders) + "\n"

    # ✅ 3. Essentiële regels (hoog & verplicht)
    if regels_essentieel:
        prompt += "\n✅ Verplichte kwaliteitseisen:\n"
        for r in regels_essentieel:
            prompt += f"- {r['id']}: {r['uitleg']}\n"

    # 💡 4. Aanvullende richtlijnen
    if regels_aanvullend:
        prompt += "\n💡 Aanvullende richtlijnen:\n"
        for r in regels_aanvullend:
            prompt += f"- {r['id']}: {r['uitleg']}\n"

    # 📎 5. Achtergrondinformatie (referentie)
    prompt += "\n📎 Achtergrond (referentie, niet letterlijk):\n" + web_uitleg + "\n"

    # 🚫 6. Veelgemaakte fouten & Validatiematrix
    # --- Haal de actuele verboden startwoordenlijst op ---
    verboden_startwoorden = laad_verboden_woorden()

    # --- Sterk “Verboden”-blok (inclusief de dynamische lijst) ---
    prompt += (
        "\n🚫 Verboden (NIET doen):\n"
        "- Definitie starten met het begrip zelf\n"
        "- Koppelwerkwoorden aan het begin (bijv. 'is', 'omvat', 'betekent')\n"
        "- Lidwoorden aan het begin (bijv. 'de', 'het', 'een')\n"
        "- Abstracte constructies aan het begin (bijv. 'proces waarbij')\n"
        "- Context, wet of organisatie letterlijk noemen\n"
        "- Opsommingen, bijzinnen of vage formuleringen\n"
        "- Subjectieve termen zoals 'essentieel', 'belangrijk', 'relevant'\n"
        # nu de dynamische verboden-startwoordenlijst:
        + "".join(f"- Starten met '{w}'\n" for w in verboden_startwoorden)
    )

    prompt += (
        "\n| Probleem                             | Afgedekt? | Toelichting                                                                 |\n"
        "|--------------------------------------|-----------|-----------------------------------------------------------------------------|\n"
        "| Start met begrip                     | ✅        | Vermijd dat de definitie start met het begrip zelf                           |\n"
        "| Abstracte constructies               | ✅        | Vermijd zinnen als 'proces waarbij', 'handeling die', 'vorm van'             |\n"
        "| Gebruik van begrip                   | ✅        | Verboden het begrip te herhalen, parafraseren of gebruiken aan het begin      |\n"
        "| Koppelwerkwoorden aan het begin      | ✅        | Verboden: 'is', 'omvat', 'betekent', etc.                                     |\n"
        "| Lidwoorden aan het begin             | ✅        | Verboden: 'de', 'het', 'een'                                                  |\n"
        "| Organisaties of afkortingen          | ✅        | Vermijd benoemen van 'de KMAR', 'het OM', tenzij strikt noodzakelijk          |\n"
        "| Letterlijke contextvermelding        | ✅        | Verboden: 'in de context van...', 'volgens de AVG', etc.                      |\n"
        "| Subjectieve bijvoeglijkheid          | ✅        | Vermijd 'essentieel', 'belangrijk', 'relevant', etc.                          |\n"
        "| Toelichting of inleiding             | ✅        | Geen toelichting, geen inleiding; alleen de één-zins definitie                |\n"
    )

    # ✏️ 7. Slotinstructie
    prompt += (
        "\n✏️ Geef één enkele zin, voldoe aan alle instructies.\n"
        f"Begrip: {begrip}"
    )

    return prompt

def stuur_prompt_naar_gpt(
    prompt: str,
    model: str = "gpt-4",
    temperature: float = 0.4,
    max_tokens: int = 300
) -> str:
    """Voert GPT-aanroep uit en valideert input op ASCII-veiligheid."""

    # ✅ 1. Check API-key op niet-ASCII tekens
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    check_ascii("API-key", api_key)

    # ✅ 2. Check prompttekst
    check_ascii("Prompt", prompt)

    # (optioneel) 3. Als je later headers gebruikt, voeg die dan hier toe
    # headers = {"X-Custom": "…" }  # ← voorbeeld van foute waarde
    # for k, v in headers.items():
    #     check_ascii(f"Header '{k}'", v)

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
