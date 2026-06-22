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
    DefinitionTaskModule) automatisch de juiste templates, patronen en "focus"-regels kiezen.
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

    def __init__(self) -> None:
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
        base_section = """### 📐 Let op betekenislaag (ESS-02 - Ontologische categorie):
Je **moet** de opgegeven ontologische categorie volgen door de JUISTE KICK-OFF term te kiezen:

• PROCES begrippen → start met: 'activiteit waarbij...', 'handeling die...', 'proces waarin...'
• TYPE begrippen → start met: [kernwoord] dat/die [kenmerk] (bijv. 'woord dat...', 'document dat...', 'persoon die...')
• RESULTAAT begrippen → start met: 'resultaat van...', 'uitkomst van...', 'product dat...'
• EXEMPLAAR begrippen → start met: 'exemplaar van... dat...', 'specifiek geval van...'

⚠️ Let op: Start NOOIT met 'is een' of andere koppelwerkwoorden!
⚠️ Voor TYPE: Start NOOIT met meta-woorden als kick-off ('soort...', 'type...', 'categorie...')!
De kick-off term MOET een concreet zelfstandig naamwoord zijn (bijv. 'woord', 'document', 'persoon').
Je MAG wel 'soort' gebruiken in de UITLEG, niet als START."""

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

        Args:
            categorie: Ontologische categorie

        Returns:
            Category-specific guidance of None
        """
        category_guidance_map = {
            "proces": """**PROCES CATEGORIE - Formuleer als ACTIVITEIT/HANDELING:**

⚠️ BELANGRIJK: De kick-off termen hieronder zijn ZELFSTANDIGE NAAMWOORDEN (handelingsnaamwoorden),
geen werkwoorden! Ze voldoen dus aan STR-01 (start met zelfstandig naamwoord) en ARAI-01
(geen vervoegd werkwoord als kern).

KICK-OFF opties (kies één):
- 'activiteit waarbij...' → focus op wat er gebeurt
- 'handeling die...' → focus op de actie
- 'proces waarin...' → focus op het verloop

VERVOLG met:
- WIE voert het uit (actor/rol)
- WAT er precies gebeurt (actie)
- HOE het verloopt (stappen/methode)
- WAAR het begint en eindigt (scope)

VOORBEELDEN (GOED):
✅ "activiteit waarbij gegevens worden verzameld door directe waarneming"
✅ "handeling waarin door middel van vraaggesprekken informatie wordt verzameld"
✅ "proces waarin documenten systematisch worden geanalyseerd"

VOORBEELDEN (FOUT):
❌ "is een activiteit waarbij..." (start met 'is')
❌ "het observeren van..." (werkwoordelijk)
❌ "manier om gegevens te verzamelen" (te abstract)""",
            "type": """**TYPE CATEGORIE - Begin met het ZELFSTANDIG NAAMWOORD dat de klasse aanduidt:**

⚠️ BELANGRIJK: Begin DIRECT met het kernwoord, NIET met meta-woorden als kick-off!

INSTRUCTIE: Start met het concrete zelfstandig naamwoord (bijv. 'woord', 'document', 'persoon')
die de klasse benoemt, gevolgd door onderscheidende kenmerken

STRUCTUUR van je definitie:
1. Start: [Zelfstandig naamwoord van de klasse]
2. Vervolg: [die/dat/met] [onderscheidend kenmerk]

VERVOLG met:
- BREDERE KLASSE (impliciet door kernwoord keuze)
- ONDERSCHEIDENDE KENMERKEN (wat maakt dit uniek)
- VERSCHIL met andere types (hoe te onderscheiden)

VOORBEELDEN (GOED):
✅ "woord dat handelingen of toestanden uitdrukt"
✅ "document dat juridische beslissingen formeel vastlegt"
✅ "persoon die bevoegd is tot het nemen van besluiten"
✅ "maatregel die recidive moet voorkomen"
✅ "interventie gericht op gedragsverandering"

VOORBEELDEN (FOUT):
❌ "soort woord dat..." (begin niet met 'soort')
❌ "type document dat..." (begin niet met 'type')
❌ "categorie van personen die..." (begin niet met 'categorie')
❌ "is een woord dat..." (geen koppelwerkwoord)
❌ "betreft een..." (geen koppelwerkwoord)""",
            "resultaat": """**RESULTAAT CATEGORIE - Formuleer als UITKOMST/PRODUCT:**

KICK-OFF opties (kies één):
- 'resultaat van...' → algemene uitkomst
- 'uitkomst van...' → proces resultaat
- 'product dat ontstaat door...' → tastbaar resultaat
- 'gevolg van...' → causaal resultaat

VERVOLG met:
- UIT WELK PROCES het voortkomt (oorsprong)
- WAT het betekent/bewerkstelligt (doel/functie)
- WIE het produceert (actor)

VOORBEELDEN (GOED):
✅ "resultaat van het uitwerken en analyseren van interviews"
✅ "uitkomst van een beoordelingsproces waarbij criteria worden toegepast"
✅ "product dat ontstaat door het combineren van verschillende databronnen"

VOORBEELDEN (FOUT):
❌ "is het resultaat van..." (start met 'is')
❌ "de uitkomst..." (lidwoord)""",
            "exemplaar": """**EXEMPLAAR CATEGORIE - Formuleer als SPECIFIEK GEVAL:**

KICK-OFF opties (kies één):
- 'exemplaar van... dat...' → concrete instantie
- 'specifiek geval van...' → individueel voorbeeld
- 'individuele instantie van...' → uniek voorkomen

VERVOLG met:
- Van welke ALGEMENE KLASSE dit een exemplaar is
- Wat dit exemplaar UNIEK maakt (identificerende kenmerken)
- WANNEER/WAAR het voorkomt (contextualisering)

VOORBEELDEN (GOED):
✅ "exemplaar van een adelaar dat op 25 mei 2024 in de Biesbosch werd waargenomen"
✅ "specifiek geval van een observatie uitgevoerd op 12 maart 2024"
✅ "individuele instantie van een besluit genomen door de rechtbank op 1 april 2024"

VOORBEELDEN (FOUT):
❌ "is een exemplaar van..." (start met 'is')
❌ "het exemplaar..." (lidwoord)""",
        }

        return category_guidance_map.get(categorie)
