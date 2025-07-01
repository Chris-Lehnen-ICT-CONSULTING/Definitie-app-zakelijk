# 🔧 Bestand: generate_definitie.py
# 📍 in de root van je project

import os
from typing import Optional

from openai import OpenAI, OpenAIError

from web_lookup import zoek_definitie_combinatie              # ✅ extern web‐lookup
from config_loader import laad_toetsregels                    # ✅ laad toetsregels
from prompt_builder import (
    PromptBouwer,
    PromptConfiguratie,
    stuur_prompt_naar_gpt,
)
# ✅ Init OpenAI-client (één keer)
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def genereer_definitie(
    begrip: str,
    context: Optional[str] = None,
    juridische_context: Optional[str] = None,
    wettelijke_basis: Optional[str] = None,

    model: str = "gpt-4",
    temperature: float = 0.4,
    max_tokens: int = 300
) -> str:
    """
    Genereert via GPT-4 een *ongecorrigeerde* definitie voor het opgegeven begrip:
      • haalt achtergrondinformatie op
      • laadt en splitst toetsregels
      • bouwt de prompt
      • voert GPT-aanroep uit

    Retourneert:
        definitie_origineel (str): exact wat GPT-4 teruggeeft
    """
    # 1️⃣ Achtergrond ophalen
    web_uitleg = zoek_definitie_combinatie(begrip)

    # 2️⃣ Toetsregels laden & splitsen
    toetsregels       = laad_toetsregels()


    # 3️⃣ Prompt bouwen
    configuratie = PromptConfiguratie(
        begrip=begrip,
        context=context,
        juridische_context=juridische_context,
        wettelijke_basis=wettelijke_basis,
        web_uitleg=web_uitleg,
        toetsregels=toetsregels
    )
    bouwer = PromptBouwer(configuratie)
    prompt = bouwer.bouw_prompt()

    # 4️⃣ GPT-aanroep
    try:
        definitie_origineel = stuur_prompt_naar_gpt(
            prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except OpenAIError as e:
        raise RuntimeError(f"Fout bij definitiegeneratie: {e}") from e

    # 5️⃣ Return alleen ongecorrigeerde definitie
    return definitie_origineel
