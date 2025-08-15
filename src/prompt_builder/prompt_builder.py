# ✅ PromptBouwer – genereert Nederlandstalige GPT-instructie op basis van begripsdata en toetsregels

import logging  # Logging faciliteiten voor debug en monitoring
import os  # Operating system interface voor environment variabelen
from dataclasses import (  # Dataklassen voor gestructureerde prompt configuratie
    dataclass,
    field,
)
from typing import Dict, List, Optional, Set  # Type hints voor betere code documentatie

from dotenv import load_dotenv  # .env bestand ondersteuning voor configuratie
from openai import OpenAI, OpenAIError  # OpenAI API client en foutafhandeling

from config import laad_toetsregels  # Toetsregels configuratie loader
from config.verboden_woorden import (  # Verboden woorden configuratie
    laad_verboden_woorden,
)

# ✅ Initialiseer OpenAI-client slechts één keer voor hergebruik
load_dotenv()  # Laad environment variabelen uit .env bestand
_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)  # Maak globale OpenAI client instantie


# ✅ Alternatieve clientfunctie als _client niet bruikbaar is
def verkrijg_openai_client() -> OpenAI:
    """Verkrijgt OpenAI client met error handling voor ontbrekende API key."""
    sleutel = os.getenv("OPENAI_API_KEY")  # Haal API key op uit environment
    if not sleutel:  # Controleer of key bestaat
        raise RuntimeError(
            "OPENAI_API_KEY ontbreekt. Zet deze in .env of je CI-secrets."
        )  # Gooi fout bij ontbrekende key
    return OpenAI(api_key=sleutel)  # Retourneer nieuwe client instantie


# ✅ Bekende contextafkortingen voor CON-01-blokkade
AFKORTINGEN = {
    "OM": "Openbaar Ministerie",
    "ZM": "Zittende Magistratuur",
    "3RO": "Samenwerkingsverband Reclasseringsorganisaties",
    "DJI": "Dienst Justitiële Inrichtingen",
    "NP": "Nederlands Politie",
    "FIOD": "Fiscale Inlichtingen- en Opsporingsdienst",
    "Justid": "Dienst Justitiële Informatievoorziening",
    "KMAR": "Koninklijke Marechaussee",
    "CJIB": "Centraal Justitieel Incassobureau",
    "AVG": "Algemene verordening gegevensbescherming",
}

# ✅ Toegestane regels voor promptopbouw
TOEGESTANE_TOETSREGELS = {
    "CON-01",
    "CON-02",
    "ESS-01",
    "ESS-02",
    "ESS-04",
    "ESS-05",
    "INT-01",
    "INT-02",
    "INT-03",
    "INT-04",
    "INT-06",
    "INT-07",
    "INT-08",
    "SAM-01",
    "SAM-05",
    "SAM-07",
    "STR-01",
    "STR-02",
    "STR-03",
    "STR-04",
    "STR-05",
    "STR-06",
    "STR-07",
    "STR-08",
    "STR-09",
    "ARAI01",
    "ARAI02",
    "ARAI02SUB1",
    "ARAI02SUB2",
    "ARAI03",
    "ARAI04",
    "ARAI04SUB1",
    "ARAI05",
    "ARAI06",
}


## ✅ Nieuwe versie van PromptConfiguratie: gebruikt context_dict in plaats van losse velden
@dataclass
class PromptConfiguratie:
    begrip: str
    context_dict: Dict[
        str, List[str]
    ]  # verwacht sleutels: 'organisatorisch', 'juridisch', 'wettelijk'
    web_uitleg: str = ""
    toetsregels: Dict[str, Dict] = field(default_factory=laad_toetsregels)


# ✅ PromptBouwer – genereert de volledige instructietekst
class PromptBouwer:
    def __init__(self, configuratie: PromptConfiguratie):
        # 💚 Slaat de configuratie op en initialiseert helperdata
        self.configuratie = configuratie
        self.geziene_termen: Set[str] = set()
        self.verboden_startwoorden = laad_verboden_woorden()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def bepaal_woordsoort(self) -> str:
        # 💚 Detecteert automatisch of begrip een werkwoord, deverbaal of naamwoord is
        woord = self.configuratie.begrip.strip().lower()
        if (
            len(woord) > 4
            and woord.endswith("en")
            and not woord.endswith(("ing", "atie", "isatie"))
        ):
            return "werkwoord"
        if woord.endswith(("ing", "atie", "isatie")):
            return "deverbaal"
        return "anders"

    def filter_regels(self) -> Dict[str, Dict]:
        # 💚 Filtert alleen de toetsregels die geschikt zijn voor promptopbouw
        return {
            k: v
            for k, v in self.configuratie.toetsregels.items()
            if k in TOEGESTANE_TOETSREGELS
        }

    def voeg_contextverbod_toe(self, regels: List[str], term: Optional[str]):
        # 💚 Vermijdt herhaalde of herleidbare contextvermeldingen
        if not term:
            return
        boven = term.strip().upper()
        kandidaten = [boven, AFKORTINGEN.get(boven, "")]
        for kandidaat in kandidaten:
            sleutel = kandidaat.lower()
            if kandidaat and sleutel not in self.geziene_termen:
                regels.append(
                    f"- Gebruik de term '{kandidaat}' of een variant daarvan niet letterlijk in de definitie."
                )
                self.geziene_termen.add(sleutel)

    def bouw_prompt(self) -> str:
        regels: List[str] = []
        begrip = self.configuratie.begrip
        if not begrip:
            raise ValueError("Begrip mag niet leeg zijn.")

        woordsoort = self.bepaal_woordsoort()
        geselecteerde_regels = self.filter_regels()

        # ✅ Inleiding
        regels.append(
            "Je bent een expert in beleidsmatige definities voor overheidsgebruik."
        )
        regels.append("Formuleer een definitie in één enkele zin, zonder toelichting.")

        # ✅ Schrijfadvies op basis van woordsoort
        if woordsoort == "werkwoord":
            regels.append(
                "Als het begrip een handeling beschrijft, definieer het dan als proces of activiteit."
            )
        elif woordsoort == "deverbaal":
            regels.append(
                "Als het begrip een resultaat is, beschrijf het dan als uitkomst van een proces."
            )
        else:
            regels.append(
                "Gebruik een zakelijke en generieke stijl voor het definiëren van dit begrip."
            )

        # ✅ Contextkaders (meervoudcorrectie)
        context_dict = self.configuratie.context_dict
        labelmapping = {
            "organisatorisch": "Organisatorische context(en)",
            "juridisch": "Juridische context(en)",
            "wettelijk": "Wettelijke basis(sen)",
            "Strafrechtketen": "Samenwerkingsverband Strafrechtketen",
            "Anders": "Overige context",
        }

        # ✅ Flexibele verwerking: werkt zowel met booleans (True/False) als met lijsten (zoals ['penitentiair'])
        contextregels = []
        for v in context_dict:
            waarde = context_dict.get(v)
            if isinstance(waarde, bool):
                if waarde:
                    contextregels.append(f"- {labelmapping.get(v, v)}")
            elif isinstance(waarde, list):
                if waarde:  # alleen toevoegen als lijst niet leeg is
                    contextregels.append(
                        f"- {labelmapping.get(v, v)}: {', '.join(waarde)}"
                    )
        if contextregels:
            regels.append("\n📌 Context:")
            regels.extend(contextregels)

        # ✅ Essentiële instructie voor ESS-02
        regels.append(
            """
### 📐 Let op betekenislaag (ESS-02 – Ontologische categorie):
Je **moet** één van de vier categorieën expliciet maken:
• type (soort), • exemplaar (specifiek geval), • proces (activiteit), • resultaat (uitkomst)
Gebruik formuleringen zoals:
- 'is een activiteit waarbij...'
- 'is het resultaat van...'
- 'betreft een specifieke soort...'
- 'is een exemplaar van...'
⚠️ Ondubbelzinnigheid is vereist.
"""
        )

        # ✅ Toetsregels (Richtlijnen)
        regels.append("\n### ✅ Richtlijnen voor de definitie:")
        for sleutel, inhoud in geselecteerde_regels.items():
            regels.append(f"🔹 **{sleutel} – {inhoud.get('naam')}**")
            regels.append(f"– {inhoud.get('uitleg')}")
            if "toetsvraag" in inhoud:
                regels.append(f"– Toetsvraag: {inhoud['toetsvraag']}")
            for goed in inhoud.get("goede_voorbeelden", []):
                regels.append(f"  ✅ {goed}")
            for fout in inhoud.get("foute_voorbeelden", []):
                regels.append(f"  ❌ {fout}")

        # ✅ Verwerk web_uitleg als lijst van dicts of fallback naar string
        if isinstance(self.configuratie.web_uitleg, list):
            "\n\n".join(
                f"[{blok['bron']}] {blok['definitie']}"
                for blok in self.configuratie.web_uitleg
                if isinstance(blok, dict) and blok.get("status") == "ok"
            ).strip()
        else:
            str(self.configuratie.web_uitleg).strip()

        # ✅ Veelgemaakte fouten
        fouten = [
            "- ❌ Begin niet met lidwoorden (‘de’, ‘het’, ‘een’)",
            "- ❌ Gebruik geen koppelwerkwoord aan het begin (‘is’, ‘betekent’, ‘omvat’)",
            "- ❌ Herhaal het begrip niet letterlijk",
            "- ❌ Gebruik geen synoniem als definitie",
            "- ❌ Vermijd containerbegrippen (‘proces’, ‘activiteit’)",
            "- ❌ Vermijd bijzinnen zoals 'die', 'waarin', 'zoals'",
            "- ❌ Gebruik enkelvoud; infinitief bij werkwoorden",
        ]
        regels.append("\n### ⚠️ Veelgemaakte fouten (vermijden!):")
        regels.extend(
            fouten + [f"- ❌ Start niet met '{w}'" for w in self.verboden_startwoorden]
        )

        # ✅ Dynamisch contextverbod (CON-01)
        for v in context_dict:
            # Flexibele verwerking: kan bool of list zijn
            if isinstance(context_dict.get(v), list):
                for item in context_dict[v]:
                    self.voeg_contextverbod_toe(regels, item)
            elif isinstance(context_dict.get(v), bool):
                if context_dict.get(v):
                    self.voeg_contextverbod_toe(regels, v)
        # ✅ Validatiematrix
        regels.append(
            """
| Probleem                             | Afgedekt? | Toelichting                                |
|--------------------------------------|-----------|---------------------------------------------|
| Start met begrip                     | ✅        | Vermijd cirkeldefinities                     |
| Abstracte constructies               | ✅        | 'proces waarbij', 'handeling die', enz.      |
| Koppelwerkwoorden aan het begin      | ✅        | 'is', 'omvat', 'betekent'                    |
| Lidwoorden aan het begin             | ✅        | 'de', 'het', 'een'                           |
| Letterlijke contextvermelding        | ✅        | Noem context niet letterlijk                 |
| Afkortingen onverklaard              | ✅        | Licht afkortingen toe in de definitie       |
| Subjectieve termen                   | ✅        | Geen 'essentieel', 'belangrijk', 'adequaat' |
| Bijzinconstructies                   | ✅        | Vermijd 'die', 'waarin', 'zoals' enz.       |
"""
        )

        # ✅ Definitie-opdracht
        regels.append(
            "🚫 Let op: context en bronnen mogen niet letterlijk of herleidbaar in de definitie voorkomen."
        )
        regels.append("\n📋 **Ontologische marker (lever als eerste regel):**")
        regels.append(
            "- Ontologische categorie: kies uit [soort, exemplaar, proces, resultaat]"
        )
        regels.append(
            f"✏️ Geef nu de definitie van het begrip **{begrip}** in één enkele zin, zonder toelichting."
        )

        # ✅ Metadata
        regels.append("\n🆔 Promptmetadata:")
        regels.append(f"– Begrip: {begrip}")
        regels.append(f"– Termtype: {woordsoort}")
        for v in context_dict:
            waarden = context_dict[v]
            if isinstance(waarden, list) and waarden:
                regels.append(f"– {labelmapping.get(v, v)}: {', '.join(waarden)}")
            elif isinstance(waarden, bool) and waarden:
                regels.append(f"– {labelmapping.get(v, v)}")
        # ✅ Voorkomt TypeError door alleen lists te joinen
        # ✅ Booleans (zoals True bij "Organisatorisch") geven correcte promptregel
        # ✅ False en lege lijsten worden genegeerd

        return "\n".join(regels)


# ✅ Functie om prompt aan GPT te sturen (with caching)
def stuur_prompt_naar_gpt(
    prompt: str, model: str = "gpt-4", temperatuur: float = 0.01, max_tokens: int = 300
) -> str:
    """
    ✅ Standaardtemperatuur verlaagd naar 0.01 voor maximale voorspelbaarheid en herhaalbaarheid.
    ✅ Deze aanpassing zorgt ervoor dat de GPT-output bij gelijke input zo identiek mogelijk blijft.
    ✅ Now includes intelligent caching to avoid redundant API calls.
    """
    from utils.cache import cache_gpt_call, cached

    # Generate cache key for this specific call
    cache_key = cache_gpt_call(
        prompt=prompt, model=model, temperature=temperatuur, max_tokens=max_tokens
    )

    # Use cached decorator for the actual GPT call
    @cached(ttl=3600)  # Cache for 1 hour
    def _make_gpt_call(
        cache_key: str, prompt: str, model: str, temperatuur: float, max_tokens: int
    ) -> str:
        try:
            antwoord = _client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperatuur,
                max_tokens=max_tokens,
            )
            return antwoord.choices[0].message.content.strip()
        except OpenAIError as fout:
            raise RuntimeError(f"GPT-aanroep mislukt: {fout}") from fout

    return _make_gpt_call(cache_key, prompt, model, temperatuur, max_tokens)


# ✅ Temperatuur nu standaard 0.01. Dit is zeer voorspelbaar, dus zeer geschikt voor strikte validatie- en logtoepassingen.
