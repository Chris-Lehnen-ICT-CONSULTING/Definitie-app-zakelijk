"""
Semantic Categorisation Module - ESS-02 ontologische categorie instructies.

Deze module is verantwoordelijk voor:
1. ESS-02 basis instructies
2. Category-specific guidance voor type/proces/resultaat/exemplaar
3. Dynamische categorie bepaling
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
        logger.info(
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
Je **moet** één van de vier categorieën expliciet maken:
• type (soort), • exemplaar (specifiek geval), • proces (activiteit), • resultaat (uitkomst)
Gebruik formuleringen zoals:
- 'is een activiteit waarbij...'
- 'is het resultaat van...'
- 'betreft een specifieke soort...'
- 'is een exemplaar van...'
⚠️ Ondubbelzinnigheid is vereist.

BELANGRIJK: Bepaal de juiste categorie op basis van het BEGRIP zelf:
- Eindigt op -ING of -TIE en beschrijft een handeling? → PROCES
- Is het een gevolg/uitkomst van iets? → RESULTAAT (bijv. sanctie, rapport, besluit)
- Is het een classificatie/soort? → TYPE
- Is het een specifiek geval? → EXEMPLAAR"""

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
            "proces": """**PROCES CATEGORIE - Focus op HANDELING en VERLOOP:**
Gebruik formuleringen zoals:
- 'is een activiteit waarbij...'
- 'is het proces waarin...'
- 'behelst de handeling van...'
- 'omvat de stappen die...'

⚠️ **PROCES SPECIFIEKE RICHTLIJNEN:**
- Beschrijf WIE doet WAT en HOE het verloopt
- Geef aan waar het proces BEGINT en EINDIGT
- Vermeld de ACTOREN (wie voert uit)
- Focus op de HANDELING, niet het doel
- Gebruik actieve in plaats van passieve bewoordingen

VOORBEELDEN van procesbegrippen:
- validatie: proces waarbij gecontroleerd wordt of...
- toezicht: activiteit waarbij systematisch gevolgd wordt...
- sanctionering: het proces van opleggen van maatregelen (NIET de sanctie zelf!)""",
            "type": """**TYPE CATEGORIE - Focus op CLASSIFICATIE en KENMERKEN:**
Gebruik formuleringen zoals:
- 'is een soort...'
- 'betreft een categorie van...'
- 'is een type...'
- 'is een vorm van...'

⚠️ **TYPE SPECIFIEKE RICHTLIJNEN:**
- Geef aan waarin dit TYPE verschilt van andere types
- Beschrijf de ONDERSCHEIDENDE KENMERKEN
- Gebruik classificerende taal (soort, categorie, type)
- Focus op WAT het is, niet wat het doet
- Maak duidelijk tot welke bredere klasse het behoort

VOORBEELDEN van typebegrippen:
- voorwaarde: type bepaling die aangeeft wanneer...
- maatregel: soort interventie die...
- systeem: categorie van samenhangende componenten...""",
            "resultaat": """**RESULTAAT CATEGORIE - Focus op OORSPRONG en GEVOLG:**
Gebruik formuleringen zoals:
- 'is het resultaat van...'
- 'is de uitkomst van...'
- 'ontstaat door...'
- 'wordt veroorzaakt door...'
- 'is een maatregel die volgt op...'
- 'is een besluit/beslissing genomen door...'

⚠️ **RESULTAAT SPECIFIEKE RICHTLIJNEN:**
- Beschrijf WAAR het uit voortkomt (oorsprong)
- Leg uit WAT het betekent of bewerkstelligt (gevolg)
- Focus op de CAUSALE RELATIE
- Vermeld het proces of de handeling die het resultaat oplevert
- Gebruik resultatgerichte taal (uitkomst, gevolg, product, maatregel, besluit)

VOORBEELDEN van resultaatbegrippen:
- sanctie: maatregel die volgt op normovertreding
- rapport: document dat het resultaat is van onderzoek
- besluit: uitkomst van een besluitvormingsproces
- registratie: vastlegging die resulteert uit...""",
            "exemplaar": """**EXEMPLAAR CATEGORIE - Focus op SPECIFICITEIT en INDIVIDUALITEIT:**
Gebruik formuleringen zoals:
- 'is een specifiek exemplaar van...'
- 'betreft een individueel geval van...'
- 'is een concrete instantie van...'
- 'is een bepaald voorbeeld van...'

⚠️ **EXEMPLAAR SPECIFIEKE RICHTLIJNEN:**
- Maak duidelijk dat het een CONCRETE instantie betreft
- Geef aan van welke algemene klasse dit een specifiek geval is
- Focus op de INDIVIDUELE KENMERKEN
- Beschrijf wat dit exemplaar UNIEK maakt
- Gebruik specificerende taal (specifiek, individueel, concreet, bepaald)

VOORBEELDEN van exemplaarbegrippen:
- incident: specifiek voorval waarbij...
- casus: individueel geval van...
- dossier: concrete verzameling documenten over...""",
        }

        return category_guidance_map.get(categorie)
