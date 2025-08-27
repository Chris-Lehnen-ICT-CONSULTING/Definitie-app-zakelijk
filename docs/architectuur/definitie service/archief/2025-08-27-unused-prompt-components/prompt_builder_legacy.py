# ✅ PromptBouwer - genereert Nederlandstalige GPT-instructie op basis van begripsdata en toetsregels

import logging  # Logging faciliteiten voor debug en monitoring
import os  # Operating system interface voor environment variabelen
from dataclasses import (  # Dataklassen voor gestructureerde prompt configuratie
    dataclass,
    field,
)

from dotenv import load_dotenv  # .env bestand ondersteuning voor configuratie
from openai import OpenAI, OpenAIError  # OpenAI API client en foutafhandeling

from config.config_loader import laad_toetsregels  # Toetsregels configuratie loader
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
        msg = "OPENAI_API_KEY ontbreekt. Zet deze in .env of je CI-secrets."
        raise RuntimeError(msg)  # Gooi fout bij ontbrekende key
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
    context_dict: dict[
        str, list[str]
    ]  # verwacht sleutels: 'organisatorisch', 'juridisch', 'wettelijk'
    web_uitleg: str = ""
    toetsregels: dict[str, dict] = field(default_factory=laad_toetsregels)


# ✅ PromptBouwer - FACADE naar modulaire architectuur
class PromptBouwer:
    """
    Legacy PromptBouwer - nu een facade naar het modulaire systeem.
    
    Deze klasse behoud de oude interface maar gebruikt intern
    het nieuwe UnifiedPromptBuilder systeem.
    """
    
    def __init__(self, configuratie: PromptConfiguratie):
        """
        Initialize PromptBouwer facade.
        
        Args:
            configuratie: Legacy prompt configuratie
        """
        self.configuratie = configuratie
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Import het nieuwe systeem
        from services.definition_generator_prompts import UnifiedPromptBuilder
        from services.definition_generator_config import UnifiedGeneratorConfig
        from services.definition_generator_context import EnrichedContext
        
        self._unified_builder = UnifiedPromptBuilder(None)
        
        # Convert legacy config naar nieuwe context
        self._enriched_context = self._convert_legacy_config_to_context()
        
        self.logger.info("PromptBouwer facade geïnitialiseerd met modulaire backend")
    
    def _convert_legacy_config_to_context(self) -> 'EnrichedContext':
        """
        Convert legacy PromptConfiguratie naar nieuwe EnrichedContext.
        
        Returns:
            EnrichedContext voor het nieuwe systeem
        """
        from services.definition_generator_context import EnrichedContext
        
        # Convert legacy context_dict naar nieuwe base_context
        base_context = {}
        for key, value in self.configuratie.context_dict.items():
            if isinstance(value, list) and value:
                base_context[key] = value
            elif isinstance(value, bool) and value:
                base_context[key] = [key]  # Convert boolean True naar lijst
        
        # Create EnrichedContext
        return EnrichedContext(
            base_context=base_context,
            sources=[],  # Geen legacy sources
            expanded_terms={},  # Geen legacy expanded terms
            metadata={},  # Geen legacy metadata
            confidence_scores={}  # Geen legacy confidence
        )

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

    def filter_regels(self) -> dict[str, dict]:
        # 💚 Filtert alleen de toetsregels die geschikt zijn voor promptopbouw
        return {
            k: v
            for k, v in self.configuratie.toetsregels.items()
            if k in TOEGESTANE_TOETSREGELS
        }

    def voeg_contextverbod_toe(self, regels: list[str], term: str | None):
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
        """
        Bouw prompt met nieuwe modulaire architectuur.
        
        Deze method is een facade die intern het UnifiedPromptBuilder
        systeem gebruikt voor consistency en onderhoud.
        
        Returns:
            Complete prompt string
            
        Raises:
            ValueError: Bij ontbrekend begrip
        """
        begrip = self.configuratie.begrip
        if not begrip:
            raise ValueError("Begrip mag niet leeg zijn.")
        
        try:
            # Gebruik het nieuwe modulaire systeem
            prompt = self._unified_builder.build_prompt(
                begrip=begrip,
                context=self._enriched_context
            )
            
            self.logger.info(f"Prompt gegenereerd via modulaire architectuur voor '{begrip}'")
            return prompt
            
        except Exception as e:
            self.logger.error(f"Fout bij genereren prompt via modulair systeem: {e}")
            # Fallback naar legacy implementatie indien nodig
            return self._build_legacy_fallback_prompt()
    
    def _build_legacy_fallback_prompt(self) -> str:
        """
        Minimale fallback prompt builder.
        
        Alleen gebruikt als laatste redmiddel wanneer het modulaire
        systeem faalt. Biedt basis functionaliteit.
        
        Returns:
            Basis fallback prompt
        """
        self.logger.warning("Gebruikmaking van legacy fallback prompt builder")
        
        begrip = self.configuratie.begrip
        
        # Minimale prompt voor fallback
        return f"""Je bent een expert in beleidsmatige definities voor overheidsgebruik.
Formuleer een definitie in één enkele zin, zonder toelichting.

Begrip: {begrip}

Gebruik objectieve, neutrale taal en vermijd vage termen.
Geef nu de definitie van het begrip **{begrip}** in één enkele zin."""

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
### 📐 Let op betekenislaag (ESS-02 - Ontologische categorie):
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
            regels.append(f"🔹 **{sleutel} - {inhoud.get('naam')}**")
            regels.append(f"- {inhoud.get('uitleg')}")
            if "toetsvraag" in inhoud:
                regels.append(f"- Toetsvraag: {inhoud['toetsvraag']}")
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
        regels.append(f"- Begrip: {begrip}")
        regels.append(f"- Termtype: {woordsoort}")
        for v in context_dict:
            waarden = context_dict[v]
            if isinstance(waarden, list) and waarden:
                regels.append(f"- {labelmapping.get(v, v)}: {', '.join(waarden)}")
            elif isinstance(waarden, bool) and waarden:
                regels.append(f"- {labelmapping.get(v, v)}")
        # ✅ Voorkomt TypeError door alleen lists te joinen
        # ✅ Booleans (zoals True bij "Organisatorisch") geven correcte promptregel
        # ✅ False en lege lijsten worden genegeerd

        return "\n".join(regels)


# ✅ Functie om prompt aan GPT te sturen (with caching)
def stuur_prompt_naar_gpt(
    prompt: str, model: str = "gpt-5", temperatuur: float = 0.0, max_tokens: int = 300
) -> str:
    """
    Legacy function - DEPRECATED.
    
    Nu gebruikt nieuwe AI Service voor consistency en betere error handling.
    Gebruik direct AIService.generate_definition() voor nieuwe code.
    
    Args:
        prompt: De prompt tekst
        model: OpenAI model naam
        temperatuur: Temperature waarde
        max_tokens: Maximum tokens
        
    Returns:
        AI gegenereerde content
    """
    try:
        # Import en gebruik nieuwe AI Service
        from services.ai_service import get_ai_service
        
        service = get_ai_service()
        return service.generate_definition(
            prompt=prompt,
            model=model,
            temperature=temperatuur,
            max_tokens=max_tokens
        )
        
    except Exception as e:
        # Fallback naar legacy implementatie bij problemen
        logging.warning(f"AI Service fallback: {e}")
        return _legacy_gpt_call(prompt, model, temperatuur, max_tokens)


def _legacy_gpt_call(
    prompt: str, model: str, temperatuur: float, max_tokens: int
) -> str:
    """
    Legacy GPT call implementatie als fallback.
    
    Args:
        prompt: De prompt tekst
        model: OpenAI model naam  
        temperatuur: Temperature waarde
        max_tokens: Maximum tokens
        
    Returns:
        AI gegenereerde content
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
            msg = f"GPT-aanroep mislukt: {fout}"
            raise RuntimeError(msg) from fout

    return _make_gpt_call(cache_key, prompt, model, temperatuur, max_tokens)


# ✅ Temperatuur nu standaard 0.01. Dit is zeer voorspelbaar, dus zeer geschikt voor strikte validatie- en logtoepassingen.
