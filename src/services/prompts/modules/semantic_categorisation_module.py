"""
Semantic Categorisation Module - ESS-02 betekenisniveau en aard.

Deze module is verantwoordelijk voor:
1. De gedeelde ESS-02-aanwijzing (betekenisniveau en aard, DEF-750)
2. Richtinggevende hints per praktische categorie type/proces/resultaat/exemplaar
3. Doorzetten van de opgegeven categorie naar shared state

Toelichting (ESS-02 vs. UI-injectie van categorie)
- De app/UI bepaalt of kiest de ontologische categorie (type/proces/resultaat/exemplaar)
  en injecteert die in de promptcontext/metadata.
- De vier categorieën zijn praktische, overlappende richtingen — geen vier
  elkaar uitsluitende ontologische klassen en geen verplicht woordenlijstje.
  ESS-02 vraagt dat de definitiekern met een passend bovenbegrip en kenmerken
  duidelijk maakt of een algemeen begrip of één bepaald ding/voorval wordt
  bedoeld, en waar relevant of de kern een activiteit of haar uitkomst is.
- De opgegeven categorie is een te controleren betekenisclaim: zij stuurt de
  hints en templates (TemplateModule, DefinitionTaskModule via shared state),
  maar geeft geen toestemming om strijdige broninhoud te herschrijven en is
  geen validatiebewijs. Zonder categorie blijft de gedeelde aanwijzing staan.
- Er is geen aparte markerregel in de uitvoer: de uitvoer is uitsluitend de
  definitiekern (DEF-750).
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput
from .ess02_aanwijzing import GEDEELDE_ESS02_AANWIJZING

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
        # Basis ESS-02 sectie (altijd aanwezig). DEF-750: één gedeelde
        # aanwijzing — niveau en aard apart, vier richtingen als hulp, geen
        # markerplicht en geen onvoorwaardelijk verbod op 'soort' of 'type'.
        base_section = f"""### 📐 Betekenislaag (ESS-02 - betekenisniveau en aard):
{GEDEELDE_ESS02_AANWIJZING}

Praktische richtingen (hulpmiddelen, overlappend, niet exclusief):
• TYPE — algemeen begrip; benoem een passend genus (bijv. "document dat informatie over één behandeld onderwerp vastlegt")
• PROCES — activiteit als kern; algemeen begrip of één bepaald voorval (bijv. "activiteit waarbij meetwaarden in een register worden vastgelegd")
• RESULTAAT — uitkomst als kern; relevante ontstaansrelatie behouden (bijv. "resultaat van het vastleggen van meetwaarden in een register")
• EXEMPLAAR — één bepaald ding, ook abstract, of voorval; gegeven identificatie en aard behouden (bijv. "meting M-17 van 16 september 2026 aan sensor S-4")"""

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
        # DEF-750: hints per praktische richting. Kick-offs zijn voorbeelden,
        # geen verplicht vocabulaire; de ESS-01-grensgevallen (DEF-746) blijven
        # letterlijk staan. 'soort'/'type' zijn geen fout op zichzelf: een
        # genus 'soort ...' past niet wanneer de dingen zelf bedoeld zijn, maar
        # kan passen bij een begrip waarvan de instanties soorten zijn.
        category_guidance_map = {
            "proces": """**PROCES — activiteit als kern:**

De kick-off is een handelingsnaamwoord ('activiteit', 'handeling', 'proces'), geen werkwoord (STR-01, ARAI-01).
Onderscheid waar nodig het algemene begrip van één bepaald voorval. Een activiteit mag haar uitkomst noemen
zonder een uitkomstbegrip te worden.

Bijvoorbeeld:
- 'activiteit waarbij...' → wat er gebeurt
- 'handeling die...' → de actie
- 'proces waarin...' → het verloop

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
❌ "is een activiteit waarbij..." (koppelwerkwoord als start)
❌ "het observeren van..." (werkwoordelijk)
❌ "activiteit of resultaat van het vastleggen van meetwaarden" (twee betekenislagen als alternatief in één kern)""",
            "type": """**TYPE — algemeen begrip; benoem een passend genus:**

Start met het zelfstandig naamwoord dat het bovenbegrip benoemt (bijv. 'woord', 'document', 'persoon',
'sanctie'), gevolgd door onderscheidende kenmerken. Een genus als 'soort ...' of 'type ...' past niet
wanneer de woorden of documenten zelf bedoeld zijn, maar kan passen bij een begrip waarvan de instanties
zelf soorten zijn; het woord is geen fout op zichzelf. Onderscheid waar relevant het algemene begrip van
één bepaald ding of voorval.

STRUCTUUR van je definitie:
1. Start: [zelfstandig naamwoord van het bovenbegrip]
2. Vervolg: [die/dat/met] [onderscheidend kenmerk]

VERVOLG met:
- BOVENBEGRIP (impliciet door de keuze van het kernwoord)
- ONDERSCHEIDENDE KENMERKEN (wat maakt dit uniek)
- VERSCHIL met verwante begrippen (hoe te onderscheiden)

VOORBEELDEN (GOED):
✅ "woord dat handelingen of toestanden uitdrukt"
✅ "document dat juridische beslissingen formeel vastlegt"
✅ "persoon die bevoegd is tot het nemen van besluiten"
Grensgevallen: maatregel en interventie. Leid een begripsbepalend doel niet af uit de categorie TYPE; gebruik gegeven domeingrond en ESS-01. Zonder grond geen voorbeeld als algemeen correct presenteren.
Grensgeval — "soort collegiale toetsing waarbij deelnemers samen een voorgestelde oplossing doorlopen": past niet wanneer concrete toetsingen bedoeld zijn, wel wanneer soorten toetsingen bedoeld zijn; de bedoeling volgt uit de gegeven context, niet uit het woord.

VOORBEELDEN (FOUT):
❌ "is een woord dat..." (koppelwerkwoord als start)
❌ "betreft een..." (koppelwerkwoord als start)""",
            "resultaat": """**RESULTAAT — uitkomst als kern:**

Benoem de onderbouwde uitkomst met een passend zelfstandig naamwoord; een uitkomst is niet noodzakelijk een maatregel.
Behoud de relevante ontstaansrelatie zonder de activiteit tot hoofdbetekenis te maken.

Bijvoorbeeld:
- 'resultaat van...' → algemene uitkomst
- 'uitkomst van...' → uitkomst van een beoordeling of proces
- 'product dat ontstaat door...' → tastbare uitkomst
- 'gevolg van...' → causale uitkomst

VERVOLG met:
- UIT WELK PROCES het voortkomt (oorsprong)
- WAT het resultaat vastlegt of inhoudt; een doel of functie alleen met begripsbepalende grond volgens ESS-01
- WIE het produceert (actor)

VOORBEELDEN (GOED):
✅ "resultaat van het uitwerken en analyseren van interviews"
✅ "uitkomst van een beoordelingsproces waarbij criteria worden toegepast"
✅ "product dat ontstaat door het combineren van verschillende databronnen"

VOORBEELDEN (FOUT):
❌ "is het resultaat van..." (koppelwerkwoord als start)
❌ "de uitkomst..." (lidwoord)""",
            "exemplaar": """**EXEMPLAAR — één bepaald ding, ook abstract, of voorval:**

Benoem het bepaalde ding of voorval met de gegeven identificatie (nummer, datum, plaats) en behoud zijn
aard: een specifieke meting blijft een activiteit, een specifiek rapport blijft een document. Het woord
'exemplaar' is niet vereist; dat er nu maar één geval bestaat maakt een begrip nog geen exemplaar.

Bijvoorbeeld:
- 'meting met identificatie M-17 die op ... is uitgevoerd aan ...' → geïdentificeerd voorval
- 'exemplaar van... dat...' → geïdentificeerd ding
- 'specifiek geval van...' → geïdentificeerde gebeurtenis

VERVOLG met:
- Van welk ALGEMEEN BEGRIP dit één geval is
- Wat dit geval UNIEK maakt (identificerende kenmerken)
- WANNEER/WAAR het voorkomt (contextualisering)

VOORBEELDEN (GOED):
✅ "meting met identificatie M-17 die op 16 september 2026 om 10:00 is uitgevoerd aan sensor S-4"
✅ "exemplaar van een adelaar dat op 25 mei 2024 in de Biesbosch werd waargenomen"
✅ "individuele instantie van een besluit genomen door de rechtbank op 1 april 2024"

VOORBEELDEN (FOUT):
❌ "is een exemplaar van..." (koppelwerkwoord als start)
❌ "het exemplaar..." (lidwoord)""",
        }

        return category_guidance_map.get(categorie)
