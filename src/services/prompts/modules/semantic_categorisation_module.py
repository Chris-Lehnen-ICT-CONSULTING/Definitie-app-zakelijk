"""
Semantic Categorisation Module - ESS-02 ontologische categorie instructies.

Deze module is verantwoordelijk voor:
1. ESS-02 basis instructies
2. Category-specific guidance voor type/proces/resultaat/exemplaar
3. Dynamische categorie bepaling

Toelichting (ESS-02 vs. UI-injectie van categorie)
- De app/UI bepaalt de ontologische categorie (bv. type/proces/resultaat/exemplaar) en injecteert die in de
  promptcontext/metadata.
- ESS-02 maakt deze categorie zichtbaar en dwingend voor het taalmodel door:
  - Expliciete, categorie-specifieke schrijfaanwijzingen en voorbeeldformuleringen te geven.
  - De categorie door te zetten naar shared state zodat andere modules (bijv. TemplateModule en
    DefinitionTaskModule) automatisch de juiste templates, patronen en “focus”-regels kiezen.
  - Veilige basisinstructies te tonen als de categorie ontbreekt, zodat het model alsnog goede keuzes kan maken.
- Zonder ESS-02 blijft de categorie alleen metadata; met ESS-02 krijgt het model concrete guidance om de categorie
  ondubbelzinnig in de definitie tot uitdrukking te brengen (consistent over de hele prompt).
- Compacte modus (optioneel): beperk ESS-02 tot de verplichte keuze tussen de vier categorieën plus korte hints,
  zonder uitgebreide voorbeelden, om tokens te besparen.
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class SemanticCategorisationModule(BasePromptModule):
    """
    Module voor ESS-02 ontologische categorie instructies.

    Genereert categorie-specifieke guidance op basis van de
    ontologische categorie van het begrip.
    """

    def __init__(self):
        """Initialize de semantic categorisation module."""
        super().__init__(
            module_id="semantic_categorisation",
            module_name="ESS-02 Ontological Category Instructions",
        )
        self.detailed_guidance_enabled = True

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.detailed_guidance_enabled = config.get("detailed_guidance", True)
        self._initialized = True
        logger.debug(
            f"SemanticCategorisationModule geïnitialiseerd "
            f"(detailed_guidance={self.detailed_guidance_enabled})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Valideer input - deze module draait altijd.

        Args:
            context: Module context

        Returns:
            Altijd (True, None)
        """
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer ESS-02 ontologische categorie instructies.

        Args:
            context: Module context met categorie info

        Returns:
            ModuleOutput met categorie instructies
        """
        try:
            # Haal ontologische categorie op uit metadata
            categorie = context.get_metadata("ontologische_categorie")

            # Sla categorie op voor andere modules
            if categorie:
                context.set_shared("ontological_category", categorie)

            # Bouw de ESS-02 sectie
            content = self._build_ess02_section(categorie)

            return ModuleOutput(
                content=content,
                metadata={
                    "ontological_category": categorie or "none",
                    "detailed_guidance_added": bool(
                        categorie and self.detailed_guidance_enabled
                    ),
                },
            )

        except Exception as e:
            logger.error(
                f"SemanticCategorisationModule execution failed: {e}", exc_info=True
            )
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate ESS-02 section: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module heeft geen dependencies.

        Returns:
            Lege lijst
        """
        return []

    def _build_ess02_section(self, categorie: str | None) -> str:
        """
        Bouw de complete ESS-02 sectie.

        Args:
            categorie: Ontologische categorie (optioneel)

        Returns:
            ESS-02 sectie tekst
        """
        # Basis ESS-02 sectie (altijd aanwezig)
        base_section = """### 🎯 ONTOLOGISCHE CATEGORIE INSTRUCTIES:

⚠️ BELANGRIJK: Deze instructies helpen je de definitie te STRUCTUREREN.
De definitie zelf begint DIRECT met een zelfstandig naamwoord, NOOIT met 'is een' of meta-woorden.

BEPAAL eerst de categorie van het begrip:
• PROCES → Beschrijft een handeling/activiteit (vaak eindigt op -ing, -tie, -atie)
• TYPE → Classificeert of categoriseert iets
• RESULTAAT → Is de uitkomst/gevolg van een proces
• EXEMPLAAR → Is een specifiek, uniek geval

⛔ DEFINITIE REGELS:
- Begin DIRECT met het zelfstandig naamwoord
- GEEN 'is een', 'betreft', 'betekent' aan het begin
- GEEN meta-woorden zoals 'proces', 'type', 'resultaat', 'exemplaar' aan het begin
- WEL: De categorie bepaalt de STRUCTUUR van je definitie"""

        # Voeg category-specific guidance toe indien beschikbaar
        if categorie and self.detailed_guidance_enabled:
            category_guidance = self._get_category_specific_guidance(categorie.lower())
            if category_guidance:
                logger.debug(f"Category-specific guidance toegevoegd voor: {categorie}")
                return f"{base_section}\n\n{category_guidance}"

        # Log waarom geen specifieke guidance
        if categorie and not self.detailed_guidance_enabled:
            logger.debug("Detailed guidance uitgeschakeld via config")
        elif categorie:
            logger.debug(f"Geen specifieke guidance voor categorie: {categorie}")
        else:
            logger.debug("Geen ontologische categorie gespecificeerd")

        return base_section

    def _get_category_specific_guidance(self, categorie: str) -> str | None:
        """
        Verkrijg category-specific guidance per ontologische categorie.

        BELANGRIJK: Deze instructies zijn voor het MODEL om de definitie te structureren.
        De definitie zelf begint NOOIT met de meta-woorden uit de instructies.

        Args:
            categorie: Ontologische categorie

        Returns:
            Category-specific guidance of None
        """
        category_guidance_map = {
            "proces": """**🔄 PROCES CATEGORIE - Focus op HANDELING en VERLOOP:**

⚠️ INSTRUCTIE: Begin direct met een HANDELINGSNAAMWOORD (zelfstandig naamwoord van een werkwoord)

STRUCTUUR van je definitie:
1. Start: [Handelingsnaamwoord]
2. Vervolg: [van/door/waarbij] [actor/object]
3. Detail: [methode/doel/resultaat]

VOORBEELDEN (✅ GOED):
• "observatie van gedrag in natuurlijke omgeving"
• "verzameling van data door systematische meting"
• "beoordeling van prestaties volgens vastgestelde criteria"
• "analyse waarbij documenten worden vergeleken op kernmerken"

VOORBEELDEN (❌ FOUT):
• "proces waarin..." (begin NIET met 'proces')
• "activiteit waarbij..." (begin NIET met 'activiteit')
• "het observeren van..." (GEEN werkwoordelijke vorm)
• "is een handeling..." (GEEN koppelwerkwoord)

FOCUS ELEMENTEN:
- WIE voert uit (actor)
- WAT gebeurt er (handeling)
- HOE verloopt het (methode)
- WANNEER begint/eindigt het (temporeel)""",
            "type": """**📦 TYPE CATEGORIE - Focus op CLASSIFICATIE en KENMERKEN:**

⚠️ INSTRUCTIE: Begin direct met het ZELFSTANDIG NAAMWOORD dat de klasse aanduidt

STRUCTUUR van je definitie:
1. Start: [Zelfstandig naamwoord van de klasse]
2. Vervolg: [die/dat/met] [onderscheidend kenmerk]
3. Detail: [specifieke eigenschappen/functie]

VOORBEELDEN (✅ GOED):
• "document dat juridische beslissingen formeel vastlegt"
• "persoon die bevoegd is tot het nemen van besluiten"
• "maatregel die recidive moet voorkomen"
• "interventie gericht op gedragsverandering bij jeugdigen"

VOORBEELDEN (❌ FOUT):
• "soort document dat..." (begin NIET met 'soort')
• "type persoon die..." (begin NIET met 'type')
• "categorie van maatregelen..." (begin NIET met 'categorie')
• "is een document..." (GEEN koppelwerkwoord)

FOCUS ELEMENTEN:
- BREDERE KLASSE waartoe het behoort (impliciet in het naamwoord)
- ONDERSCHEIDENDE KENMERKEN t.o.v. andere in dezelfde klasse
- FUNCTIE of DOEL waarvoor het dient
- CRITERIA waaraan het moet voldoen""",
            "resultaat": """**📊 RESULTAAT CATEGORIE - Focus op UITKOMST en OORSPRONG:**

⚠️ INSTRUCTIE: Begin direct met het ZELFSTANDIG NAAMWOORD dat de uitkomst benoemt

STRUCTUUR van je definitie:
1. Start: [Zelfstandig naamwoord van de uitkomst]
2. Vervolg: [ontstaan uit/voortkomend uit/volgend op]
3. Detail: [proces/handeling die eraan voorafging]

VOORBEELDEN (✅ GOED):
• "rapport opgesteld na systematische analyse van gegevens"
• "besluit genomen na beoordeling van alle relevante factoren"
• "sanctie opgelegd wegens overtreding van voorschriften"
• "overzicht samengesteld uit meerdere databronnen"

VOORBEELDEN (❌ FOUT):
• "resultaat van analyse..." (begin NIET met 'resultaat')
• "uitkomst van een proces..." (begin NIET met 'uitkomst')
• "product dat ontstaat..." (begin NIET met 'product')
• "is een rapport..." (GEEN koppelwerkwoord)

FOCUS ELEMENTEN:
- OORSPRONG: uit welk proces komt het voort
- DOEL: waarvoor dient de uitkomst
- VORM: hoe manifesteert het zich
- EFFECT: wat bewerkstelligt het""",
            "exemplaar": """**🔍 EXEMPLAAR CATEGORIE - Focus op SPECIFIEKE INSTANTIE:**

⚠️ INSTRUCTIE: Begin direct met de NAAM of AANDUIDING van het specifieke geval

STRUCTUUR van je definitie:
1. Start: [Eigennaam of specifieke aanduiding]
2. Vervolg: [betreffende/zijnde] [wat het is]
3. Detail: [unieke kenmerken/context]

VOORBEELDEN (✅ GOED):
• "Wet van 15 maart 2024 betreffende de digitale overheid"
• "Zaak 2024/1234 waarin verdachte zich moet verantwoorden voor fraude"
• "Besluit d.d. 1 april 2024 waarbij vergunning is verleend"
• "Arrest HR 25 mei 2024 inzake staatsaansprakelijkheid"

VOORBEELDEN (❌ FOUT):
• "exemplaar van een wet..." (begin NIET met 'exemplaar')
• "specifiek geval van zaak..." (begin NIET met 'specifiek geval')
• "individuele instantie..." (begin NIET met 'individuele instantie')
• "is de Wet van..." (GEEN koppelwerkwoord)

FOCUS ELEMENTEN:
- IDENTIFICATIE: datum, nummer, naam
- CONTEXT: waar/wanneer/door wie
- UNICITEIT: wat maakt dit geval specifiek
- KLASSE: tot welke algemene categorie behoort het""",
        }

        return category_guidance_map.get(categorie)
