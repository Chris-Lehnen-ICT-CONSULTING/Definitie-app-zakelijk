"""
Modulaire Prompt Builder - Vervangt monolithische LegacyPromptBuilder.

Genereert de volledige 17k karakter ESS-02 prompt uit 6 configureerbare componenten:
1. Rol & Basis Instructies
2. Context Sectie
3. Ontologische Categorie Sectie (KERN)
4. Validatie Regels Sectie
5. Verboden Patronen Sectie
6. Afsluitende Instructies

Referentie: SERVICE_ARCHITECTUUR_IMPLEMENTATIE_BLAUWDRUK.md - Sectie 3
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext

logger = logging.getLogger(__name__)


@dataclass
class PromptComponentConfig:
    """Configuratie voor welke componenten te gebruiken in ModularPromptBuilder."""

    # Basis componenten
    include_role: bool = True
    include_context: bool = True
    include_ontological: bool = True
    include_validation_rules: bool = True
    include_forbidden_patterns: bool = True
    include_final_instructions: bool = True

    # Per-category customization
    detailed_category_guidance: bool = True
    include_examples_in_rules: bool = True
    compact_mode: bool = False  # Voor kortere prompts (experimenteel)

    # Advanced configuratie
    max_prompt_length: int = 20000  # Hard limit voor prompt lengte
    enable_component_metadata: bool = True


class ModularPromptBuilder:
    """
    Modulaire prompt builder die legacy functionaliteit behoudt maar opsplitst.

    BEHOUDT: Alle functionaliteit van LegacyPromptBuilder (17k karakter ESS-02 prompt)
    VERBETERT: Modulaire, testbare, configureerbare opbouw per component

    Usage:
        config = PromptComponentConfig()
        builder = ModularPromptBuilder(config)
        prompt = builder.build_prompt(begrip, context, unified_config)
    """

    def __init__(self, component_config: PromptComponentConfig = None):
        """Initialize met component configuratie."""
        self.component_config = component_config or PromptComponentConfig()
        logger.info(
            f"ModularPromptBuilder geïnitialiseerd met {self._count_active_components()} actieve componenten"
        )

    def build_prompt(
        self, begrip: str, context: EnrichedContext, config: UnifiedGeneratorConfig
    ) -> str:
        """
        Build volledige prompt uit componenten.

        Args:
            begrip: Het begrip om te definiëren
            context: Verrijkte context informatie (met ontologische categorie in metadata)
            config: Unified generator configuratie

        Returns:
            Volledige ESS-02 prompt string (15k-20k karakters)

        Raises:
            ValueError: Als essentiële componenten ontbreken
        """
        start_time = time.time()

        try:
            # Valideer input
            if not begrip or not begrip.strip():
                msg = "Begrip mag niet leeg zijn"
                raise ValueError(msg)

            # Componenten in logische volgorde bouwen
            components = []

            if self.component_config.include_role:
                role_component = self._build_role_and_basic_rules(begrip)
                components.append(role_component)
                logger.debug("Component 1 (Rol) toegevoegd")

            if self.component_config.include_context:
                context_component = self._build_context_section(context)
                if (
                    context_component
                ):  # Alleen toevoegen als er daadwerkelijk context is
                    components.append(context_component)
                    logger.debug("Component 2 (Context) toegevoegd")

            if self.component_config.include_ontological:
                ontological_component = self._build_ontological_section(context)
                components.append(ontological_component)
                logger.debug(
                    f"Component 3 (Ontologisch - {context.metadata.get('ontologische_categorie', 'geen')}) toegevoegd"
                )

            if self.component_config.include_validation_rules:
                validation_component = self._build_validation_rules_section()
                components.append(validation_component)
                logger.debug("Component 4 (Validatie regels) toegevoegd")

            if self.component_config.include_forbidden_patterns:
                forbidden_component = self._build_forbidden_patterns_section(context)
                components.append(forbidden_component)
                logger.debug("Component 5 (Verboden patronen) toegevoegd")

            if self.component_config.include_final_instructions:
                final_component = self._build_final_instructions_section(
                    begrip, context
                )
                components.append(final_component)
                logger.debug("Component 6 (Finale instructies) toegevoegd")

            # Filter lege componenten en voeg samen met consistent spacing
            active_components = list(filter(None, components))
            full_prompt = "\n\n".join(active_components)

            # Valideer resultaat
            if len(full_prompt) < 1000:
                logger.warning(
                    f"Prompt erg kort ({len(full_prompt)} chars) - mogelijk component probleem"
                )

            # Compact mode post-processing (experimenteel)
            if self.component_config.compact_mode:
                full_prompt = self._apply_compact_mode(full_prompt)

            # Logging en metadata
            generation_time = (time.time() - start_time) if start_time else 0
            metadata = {
                "total_components": len(components),
                "active_components": len(active_components),
                "ontological_category": context.metadata.get("ontologische_categorie"),
                "prompt_length": len(full_prompt),
                "generation_time_ms": (
                    round(generation_time * 1000, 2) if generation_time else None
                ),
                "estimated_tokens": self._estimate_tokens(full_prompt),
            }

            logger.info(
                f"Modulaire prompt gebouwd voor '{begrip}': {len(full_prompt)} chars, "
                f"{len(active_components)} componenten, categorie={metadata['ontological_category']}"
            )

            # Store metadata voor debugging (optioneel)
            if self.component_config.enable_component_metadata:
                self._last_generation_metadata = metadata

            return full_prompt

        except Exception as e:
            logger.error(
                f"ModularPromptBuilder.build_prompt failed voor '{begrip}': {e!s}",
                exc_info=True,
            )
            raise

    def get_strategy_name(self) -> str:
        """Verkrijg naam van deze strategy (vereist door PromptBuilder interface)."""
        return "modular"

    def get_component_metadata(
        self, begrip: str | None = None, context: EnrichedContext = None
    ) -> dict[str, Any]:
        """
        Verkrijg metadata over welke componenten worden gebruikt.

        Returns:
            Dictionary met component informatie voor debugging/monitoring
        """
        base_metadata = {
            "builder_type": "ModularPromptBuilder",
            "total_available_components": 6,
            "active_components": self._count_active_components(),
            "component_config": {
                "include_role": self.component_config.include_role,
                "include_context": self.component_config.include_context,
                "include_ontological": self.component_config.include_ontological,
                "include_validation_rules": self.component_config.include_validation_rules,
                "include_forbidden_patterns": self.component_config.include_forbidden_patterns,
                "include_final_instructions": self.component_config.include_final_instructions,
            },
        }

        # Context-specific metadata indien beschikbaar
        if context:
            base_metadata.update(
                {
                    "ontological_category": context.metadata.get(
                        "ontologische_categorie"
                    ),
                    "has_organizational_context": bool(
                        context.base_context.get("organisatorisch")
                    ),
                    "has_domain_context": bool(context.base_context.get("domein")),
                    "estimated_prompt_tokens": self._estimate_total_tokens(
                        begrip or "unknown", context
                    ),
                }
            )

        # Last generation metadata indien beschikbaar
        if hasattr(self, "_last_generation_metadata"):
            base_metadata["last_generation"] = self._last_generation_metadata

        return base_metadata

    # ==========================================
    # COMPONENT IMPLEMENTATION METHODEN
    # ==========================================
    # Deze methoden worden geïmplementeerd in Fase 1.2, 2.1, 3.1-3.3

    def _build_role_and_basic_rules(self, begrip: str) -> str:
        """
        Component 1: Expert rol en fundamentele schrijfregels.

        Behoudt de essentiële opener uit legacy prompt builder:
        - Expert rol in beleidsmatige definities
        - Fundamentele instructie: één zin, geen toelichting
        - Zakelijke en generieke stijl
        """
        return """Je bent een expert in beleidsmatige definities voor overheidsgebruik.
Formuleer een definitie in één enkele zin, zonder toelichting.
Gebruik een zakelijke en generieke stijl voor het definiëren van dit begrip."""

    def _build_context_section(self, context: EnrichedContext) -> str:
        """
        Component 2: Organisatorische en domein context - ADAPTIEF.

        Genereert alleen context sectie als er daadwerkelijk context is.
        Behoudt de format uit legacy prompt voor consistency:
        📌 Context:
        - Organisatorische context(en): [lijst]
        - domein: [lijst]
        """
        # Check of er context informatie beschikbaar is
        has_org_context = context.base_context.get("organisatorisch")
        has_domain_context = context.base_context.get("domein")

        if not (has_org_context or has_domain_context):
            logger.debug(
                "Geen context informatie beschikbaar, Component 2 overgeslagen"
            )
            return ""

        lines = ["📌 Context:"]

        # Organisatorische context (NP, DJI, etc.)
        if has_org_context:
            org_list = (
                has_org_context
                if isinstance(has_org_context, list)
                else [has_org_context]
            )
            lines.append(f"- Organisatorische context(en): {', '.join(org_list)}")
            logger.debug(f"Organisatorische context toegevoegd: {org_list}")

        # Domein context (Nederlands Politie, Rechtspraak, etc.)
        if has_domain_context:
            domain_list = (
                has_domain_context
                if isinstance(has_domain_context, list)
                else [has_domain_context]
            )
            lines.append(f"- domein: {', '.join(domain_list)}")
            logger.debug(f"Domein context toegevoegd: {domain_list}")

        return "\n".join(lines)

    def _build_ontological_section(self, context: EnrichedContext) -> str:
        """
        Component 3: ESS-02 ontologische categorie instructies - DYNAMISCH per categorie.

        DIT IS DE KERN COMPONENT - category-specific guidance per ontologische categorie.

        Behoudt de ESS-02 structure uit legacy prompt maar voegt intelligente
        category-specific guidance toe per categorie.

        Supported categories:
        - "proces": Activiteit/handeling focus
        - "type": Classificatie/soort focus
        - "resultaat": Oorsprong/gevolg focus
        - "exemplaar": Specificiteit/individualiteit focus
        """
        categorie = context.metadata.get("ontologische_categorie")

        # Basis ESS-02 sectie (identiek aan legacy)
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

        # INTELLIGENTE CATEGORY-SPECIFIC GUIDANCE
        if categorie and self.component_config.detailed_category_guidance:
            category_guidance = self._get_category_specific_guidance(categorie.lower())
            if category_guidance:
                logger.debug(f"Category-specific guidance toegevoegd voor: {categorie}")
                return f"{base_section}\n\n{category_guidance}"

        # Fallback naar basis sectie
        if categorie:
            logger.debug(
                f"Basis ESS-02 sectie gebruikt voor onbekende categorie: {categorie}"
            )
        else:
            logger.debug(
                "Geen ontologische categorie gespecificeerd, basis ESS-02 sectie gebruikt"
            )

        return base_section

    def _get_category_specific_guidance(self, categorie: str) -> str:
        """
        Verkrijg category-specific guidance per ontologische categorie.

        Deze methode implementeert de intelligente template selectie die
        voorheen ontbrak in het systeem.
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
- Maak duidelijk tot welke bredere klasse het behoort""",
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
- besluit: uitkomst van een besluitvormingsproces""",
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
- Gebruik specificerende taal (specifiek, individueel, concreet, bepaald)""",
        }

        return category_guidance_map.get(categorie, "")

    def _build_validation_rules_section(self) -> str:
        """Component 4: Alle toetsregels gegroepeerd per categorie."""
        return """### ✅ Richtlijnen voor de definitie:
🔹 **CON-01 - Eigen definitie voor elke context. Contextspecifieke formulering zonder expliciete benoeming**
- Formuleer de definitie zó dat deze past binnen de opgegeven context(en), zonder deze expliciet te benoemen in de definitie zelf.
- Toetsvraag: Is de betekenis van het begrip contextspecifiek geformuleerd, zonder dat de context letterlijk of verwijzend in de definitie wordt genoemd?
  ✅ Toezicht is het systematisch volgen van handelingen om te beoordelen of ze voldoen aan vastgestelde normen.
  ✅ Registratie is het formeel vastleggen van gegevens in een geautoriseerd systeem.
  ✅ Een maatregel is een opgelegde beperking of correctie bij vastgestelde overtredingen.
  ❌ Toezicht is controle uitgevoerd door DJI in juridische context, op basis van het Wetboek van Strafvordering.
  ❌ Registratie: het vastleggen van persoonsgegevens binnen de organisatie DJI, in strafrechtelijke context.
  ❌ Een maatregel is, binnen de context van het strafrecht, een corrigerende sanctie.
🔹 **CON-02 - Baseren op authentieke bron**
- Gebruik een gezaghebbende of officiële bron als basis voor de definitie.
- Toetsvraag: Is duidelijk op welke authentieke of officiële bron de definitie is gebaseerd?
  ✅ gegevensverwerking: iedere handeling met gegevens zoals bedoeld in de AVG
  ✅ delict: gedraging die volgens het Wetboek van Strafrecht strafbaar is gesteld
  ❌ gegevensverwerking: handeling met gegevens (geen bron vermeld)
  ❌ delict: iets strafbaars (geen verwijzing naar wet)
🔹 **ESS-01 - Essentie, niet doel**
- Een definitie beschrijft wat iets is, niet wat het doel of de bedoeling ervan is.
- Toetsvraag: Bevat de definitie uitsluitend de essentie van het begrip, zonder doel- of gebruiksgericht taalgebruik?
  ✅ meldpunt: instantie die meldingen registreert over strafbare feiten
  ✅ sanctie: maatregel die volgt op normovertreding
  ❌ meldpunt: instantie om meldingen te kunnen verwerken
  ❌ sanctie: maatregel met als doel naleving te bevorderen
🔹 **ESS-02 - Ontologische categorie expliciteren (type / particulier / proces / resultaat)**
- Indien een begrip meerdere ontologische categorieën kan aanduiden, moet uit de definitie ondubbelzinnig blijken welke van deze vier bedoeld wordt: soort (type), exemplaar (particulier), proces (activiteit) of resultaat (uitkomst).
- Toetsvraag: Geeft de definitie ondubbelzinnig aan of het begrip een type, een particular, een proces of een resultaat is?
🔹 **ESS-04 - Toetsbaarheid**
- Een definitie bevat objectief toetsbare elementen (harde deadlines, aantallen, percentages, meetbare criteria).
- Toetsvraag: Bevat de definitie elementen waarmee je objectief kunt vaststellen of iets wel of niet onder het begrip valt?
  ✅ …binnen 3 dagen nadat het verzoek is ingediend…
  ✅ …tenminste 80% van de steekproef voldoet…
  ✅ …uiterlijk na 1 week na ontvangst…
  ❌ …zo snel mogelijk na ontvangst…
  ❌ …zo veel mogelijk resultaten…
  ❌ …moet zo mogelijk conform…
🔹 **ESS-05 - Voldoende onderscheidend**
- Een definitie moet duidelijk maken wat het begrip uniek maakt ten opzichte van andere verwante begrippen.
- Toetsvraag: Maakt de definitie expliciet duidelijk waarin het begrip zich onderscheidt van andere begrippen?
  ✅ Reclasseringstoezicht: toezicht gericht op gedragsverandering, in tegenstelling tot detentietoezicht dat gericht is op vrijheidsbeneming.
  ✅ Een onttrekking is een incident waarbij een jeugdige zonder toestemming één van de volgende voorzieningen verlaat: open justitiële inrichting of gesloten inrichtingsgebied.
  ✅ Auto: vierwielig motorvoertuig met uniek chassisnummer en kenteken, waardoor elke auto individueel wordt geïdentificeerd.
  ❌ Toezicht: het houden van toezicht op iemand.
  ❌ Een onttrekking is een incident waarbij een jeugdige zonder toestemming de inrichting verlaat.
🔹 **INT-01 - Compacte en begrijpelijke zin**
- Een definitie is compact en in één enkele zin geformuleerd.
- Toetsvraag: Is de definitie geformuleerd als één enkele, begrijpelijke zin?
  ✅ transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken.
  ❌ transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken. In tegenstelling tot andere eisen vertegenwoordigen transitie-eisen tijdelijke behoeften, in plaats van meer permanente.
🔹 **INT-02 - Geen beslisregel**
- Een definitie bevat geen beslisregels of voorwaarden.
- Toetsvraag: Bevat de definitie geen voorwaardelijke of normatieve formuleringen zoals beslisregels?
  ✅ transitie-eis: eis die een organisatie ondersteunt om migratie van de huidige naar de toekomstige situatie mogelijk te maken.
  ✅ Toegang: toestemming verleend door een bevoegde autoriteit om een systeem te gebruiken.
  ✅ Beschikking: schriftelijk besluit genomen door een bevoegde autoriteit.
  ✅ Register: officiële inschrijving in een openbaar register door een bevoegde instantie.
  ❌ transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken.
  ❌ Toegang: toestemming verleend door een bevoegde autoriteit, indien alle voorwaarden zijn vervuld.
  ❌ Beschikking: schriftelijk besluit, mits de aanvraag compleet is ingediend.
  ❌ Register: officiële inschrijving in een openbaar register, tenzij er bezwaar ligt.
🔹 **INT-03 - Voornaamwoord-verwijzing duidelijk**
- Definities mogen geen voornaamwoorden bevatten waarvan niet direct duidelijk is waarnaar verwezen wordt.
- Toetsvraag: Bevat de definitie voornaamwoorden zoals 'deze', 'dit', 'die'? Zo ja: is voor de lezer direct helder waarnaar ze verwijzen?
  ✅ Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor die gebeurtenis volledig kan worden begrepen en geanalyseerd.
  ✅ Voorwaarde: bepaling die aangeeft onder welke omstandigheden een handeling is toegestaan.
  ❌ Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor het volledig kan worden begrepen en geanalyseerd.
  ❌ Voorwaarde: bepaling die aangeeft onder welke omstandigheden deze geldt.
🔹 **INT-04 - Lidwoord-verwijzing duidelijk**
- Definities mogen geen onduidelijke verwijzingen met de lidwoorden 'de' of 'het' bevatten.
- Toetsvraag: Bevat de definitie zinnen als 'de instelling', 'het systeem'? Zo ja: is in diezelfde zin expliciet benoemd welke instelling of welk systeem wordt bedoeld?
  ✅ Een instelling (de Raad voor de Rechtspraak) neemt beslissingen binnen het strafrechtelijk systeem.
  ✅ Het systeem (Reclasseringsapplicatie) voert controles automatisch uit.
  ❌ De instelling neemt beslissingen binnen het strafrechtelijk systeem.
  ❌ Het systeem voert controles uit zonder verdere specificatie.
🔹 **INT-06 - Definitie bevat geen toelichting**
- Een definitie bevat geen nadere toelichting of voorbeelden, maar uitsluitend de afbakening van het begrip.
- Toetsvraag: Bevat de definitie signalen van toelichting zoals 'bijvoorbeeld', 'zoals', 'dit houdt in', enzovoort?
  ✅ model: vereenvoudigde weergave van de werkelijkheid
  ❌ model: vereenvoudigde weergave van de werkelijkheid, die visueel wordt weergegeven
🔹 **INT-07 - Alleen toegankelijke afkortingen**
- In een definitie gebruikte afkortingen zijn voorzien van een voor de doelgroep direct toegankelijke referentie.
- Toetsvraag: Bevat de definitie afkortingen? Zo ja: zijn deze in hetzelfde stuk tekst uitgelegd of gelinkt?
  ✅ Dienst Justitiële Inrichtingen (DJI)
  ✅ OM (Openbaar Ministerie)
  ✅ AVG (Algemene verordening gegevensbescherming)
  ✅ KvK (Kamer van Koophandel)
  ✅ [[Algemene verordening gegevensbescherming]]
  ❌ DJI voert toezicht uit.
  ❌ De AVG vereist naleving.
  ❌ OM is bevoegd tot vervolging.
  ❌ KvK registreert bedrijven.
🔹 **INT-08 - Positieve formulering**
- Een definitie wordt in principe positief geformuleerd, dus zonder ontkenningen te gebruiken; uitzondering voor onderdelen die de definitie specifieker maken (bijv. relatieve bijzinnen).
- Toetsvraag: Is de definitie in principe positief geformuleerd en vermijdt deze negatieve formuleringen, behalve om specifieke onderdelen te verduidelijken?
  ✅ bevoegd persoon: medewerker met formele autorisatie om gegevens in te zien
  ✅ gevangene: persoon die zich niet vrij kan bewegen
  ❌ bevoegd persoon: iemand die niet onbevoegd is
  ❌ toegang: mogelijkheid om een ruimte te betreden, uitgezonderd voor onbevoegden
🔹 **SAM-01 - Kwalificatie leidt niet tot afwijking**
- Een definitie mag niet zodanig zijn geformuleerd dat deze afwijkt van de betekenis die de term in andere contexten heeft.
- Toetsvraag: Leidt de gebruikte kwalificatie in de definitie tot een betekenis die wezenlijk afwijkt van het algemeen aanvaarde begrip?
  ✅ proces: reeks activiteiten met een gemeenschappelijk doel
  ✅ juridisch proces: proces binnen de context van rechtspleging
  ❌ proces: technische afhandeling van informatie tussen systemen (terwijl 'proces' elders breder wordt gebruikt)
🔹 **SAM-05 - Geen cirkeldefinities**
- Een cirkeldefinitie (wederzijdse of meerdiepse verwijzing tussen begrippen) mag niet voorkomen.
- Toetsvraag: Treden er wederzijdse verwijzingen op tussen begrippen (cirkeldefinitie)?
  ✅ object: fysiek ding dat bestaat in ruimte en tijd
  ✅ entiteit: iets dat bestaat
  ❌ object: een ding is een object
  ❌ ding: een object is een ding
🔹 **SAM-07 - Geen betekenisverruiming binnen definitie**
- De definitie mag de betekenis van de term niet uitbreiden met extra elementen die niet in de term besloten liggen.
- Toetsvraag: Bevat de definitie uitsluitend elementen die inherent zijn aan de term, zonder aanvullende uitbreidingen?
  ✅ toezicht houden: het controleren of regels worden nageleefd
  ❌ toezicht houden: het controleren en indien nodig corrigeren van gedrag
🔹 **STR-01 - definitie start met zelfstandig naamwoord**
- De definitie moet starten met een zelfstandig naamwoord of naamwoordgroep, niet met een werkwoord.
- Toetsvraag: Begint de definitie met een zelfstandig naamwoord of naamwoordgroep, en niet met een werkwoord?
  ✅ proces dat beslissers identificeert...
  ✅ maatregel die recidive voorkomt...
  ❌ is een maatregel die recidive voorkomt
  ❌ wordt toegepast in het gevangeniswezen
🔹 **STR-02 - Kick-off ≠ de term**
- De definitie moet beginnen met verwijzing naar een breder begrip, en dan de verbijzondering ten opzichte daarvan aangeven.
- Toetsvraag: Begint de definitie met een breder begrip en specificeert het vervolgens hoe het te definiëren begrip daarvan verschilt?
  ✅ analist: professional verantwoordelijk voor …
  ❌ analist: analist die verantwoordelijk is voor …
🔹 **STR-03 - Definitie ≠ synoniem**
- De definitie van een begrip mag niet simpelweg een synoniem zijn van de te definiëren term.
- Toetsvraag: Is de definitie meer dan alleen een synoniem van de term?
  ✅ evaluatie: resultaat van iets beoordelen, appreciëren of interpreteren
  ❌ evaluatie: beoordeling
  ❌ registratie: vastlegging (in een systeem)
🔹 **STR-04 - Kick-off vervolgen met toespitsing**
- Een definitie moet na de algemene opening meteen toespitsen op het specifieke begrip.
- Toetsvraag: Volgt na de algemene opening direct een toespitsing die uitlegt welk soort proces of element bedoeld wordt?
  ✅ proces dat beslissers informeert
  ✅ gegeven over de verblijfplaats van een betrokkene
  ❌ proces
  ❌ gegeven
  ❌ activiteit die plaatsvindt
🔹 **STR-05 - Definitie ≠ constructie**
- Een definitie moet aangeven wat iets is, niet uit welke onderdelen het bestaat.
- Toetsvraag: Geeft de definitie aan wat het begrip is, in plaats van alleen waar het uit bestaat?
  ✅ motorvoertuig: gemotoriseerd voertuig dat niet over rails rijdt, zoals auto's, vrachtwagens en bussen
  ❌ motorvoertuig: een voertuig met een chassis, vier wielen en een motor van meer dan 50 cc
🔹 **STR-06 - Essentie ≠ informatiebehoefte**
- Een definitie geeft de aard van het begrip weer, niet de reden waarom het nodig is.
- Toetsvraag: Bevat de definitie uitsluitend wat het begrip is, en niet waarom het nodig is of waarvoor het gebruikt wordt?
  ✅ beveiligingsmaatregel: voorziening die ongeautoriseerde toegang voorkomt
  ❌ beveiligingsmaatregel: voorziening om ongeautoriseerde toegang te voorkomen
🔹 **STR-07 - Geen dubbele ontkenning**
- Een definitie bevat geen dubbele ontkenning.
- Toetsvraag: Bevat de definitie een dubbele ontkenning die de begrijpelijkheid schaadt?
  ✅ Beveiliging: maatregelen die toegang beperken tot bevoegde personen
  ❌ Beveiliging: maatregelen die het niet onmogelijk maken om geen toegang te verkrijgen
🔹 **STR-08 - Dubbelzinnige 'en' is verboden**
- Een definitie bevat geen 'en' die onduidelijk maakt of beide kenmerken vereist zijn of slechts één van beide.
- Toetsvraag: Is het gebruik van 'en' in de definitie ondubbelzinnig? Is het duidelijk of beide elementen vereist zijn of slechts één?
  ✅ Toegang is beperkt tot personen met een geldig toegangspasje en een schriftelijke toestemming
  ❌ Toegang is beperkt tot personen met een pasje en toestemming
  ❌ Het systeem vereist login en verificatie
🔹 **STR-09 - Dubbelzinnige 'of' is verboden**
- Een definitie bevat geen 'of' die onduidelijk maakt of beide mogelijkheden gelden of slechts één van de twee.
- Toetsvraag: Is het gebruik van 'of' in de definitie ondubbelzinnig? Is het duidelijk of het gaat om een inclusieve of exclusieve keuze?
  ✅ Een persoon met een paspoort of, indien niet beschikbaar, een identiteitskaart
  ❌ Een persoon met een paspoort of identiteitskaart
  ❌ Een verdachte is iemand die een misdrijf beraamt of uitvoert"""

    def _build_forbidden_patterns_section(self, context: EnrichedContext = None) -> str:
        """Component 5: Veelgemaakte fouten en verboden startwoorden."""
        # Basis verboden patronen
        base_section = """### ⚠️ Veelgemaakte fouten (vermijden!):
- ❌ Begin niet met lidwoorden ('de', 'het', 'een')
- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat')
- ❌ Herhaal het begrip niet letterlijk
- ❌ Gebruik geen synoniem als definitie
- ❌ Vermijd containerbegrippen ('proces', 'activiteit')
- ❌ Vermijd bijzinnen zoals 'die', 'waarin', 'zoals'
- ❌ Gebruik enkelvoud; infinitief bij werkwoorden
- ❌ Start niet met 'is'
- ❌ Start niet met 'betreft'
- ❌ Start niet met 'omvat'
- ❌ Start niet met 'betekent'
- ❌ Start niet met 'verwijst naar'
- ❌ Start niet met 'houdt in'
- ❌ Start niet met 'heeft betrekking op'
- ❌ Start niet met 'duidt op'
- ❌ Start niet met 'staat voor'
- ❌ Start niet met 'impliceert'
- ❌ Start niet met 'definieert'
- ❌ Start niet met 'beschrijft'
- ❌ Start niet met 'wordt'
- ❌ Start niet met 'zijn'
- ❌ Start niet met 'was'
- ❌ Start niet met 'waren'
- ❌ Start niet met 'behelst'
- ❌ Start niet met 'bevat'
- ❌ Start niet met 'bestaat uit'
- ❌ Start niet met 'de'
- ❌ Start niet met 'het'
- ❌ Start niet met 'een'
- ❌ Start niet met 'proces waarbij'
- ❌ Start niet met 'handeling die'
- ❌ Start niet met 'vorm van'
- ❌ Start niet met 'type van'
- ❌ Start niet met 'soort van'
- ❌ Start niet met 'methode voor'
- ❌ Start niet met 'wijze waarop'
- ❌ Start niet met 'manier om'
- ❌ Start niet met 'een belangrijk'
- ❌ Start niet met 'een essentieel'
- ❌ Start niet met 'een vaak gebruikte'
- ❌ Start niet met 'een veelvoorkomende'

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

🚫 Let op: context en bronnen mogen niet letterlijk of herleidbaar in de definitie voorkomen."""

        # Voeg context-specifieke verboden toe
        if context and context.base_context:
            context_verboden = []

            # Organisatorische context verboden
            if context.base_context.get("organisatorisch"):
                for org in context.base_context["organisatorisch"]:
                    context_verboden.append(
                        f"- Gebruik de term '{org}' of een variant daarvan niet letterlijk in de definitie."
                    )

                    # Voeg ook volledige namen toe voor afkortingen
                    org_mappings = {
                        "NP": "Nederlands Politie",
                        "DJI": "Dienst Justitiële Inrichtingen",
                        "OM": "Openbaar Ministerie",
                        "ZM": "Zittende Magistratuur",
                    }
                    if org in org_mappings:
                        context_verboden.append(
                            f"- Gebruik de term '{org_mappings[org]}' of een variant daarvan niet letterlijk in de definitie."
                        )

            # Domein context verboden
            if context.base_context.get("domein"):
                for domein in context.base_context["domein"]:
                    context_verboden.append(
                        f"- Vermijd expliciete vermelding van domein '{domein}' in de definitie."
                    )

            if context_verboden:
                base_section += "\n\n### 🚨 CONTEXT-SPECIFIEKE VERBODEN:\n"
                base_section += "\n".join(context_verboden)

        return base_section

    def _build_final_instructions_section(
        self, begrip: str, context: EnrichedContext
    ) -> str:
        """Component 6: Laatste instructies en metadata voor traceerbaarheid."""
        # Bepaal of er context beschikbaar is
        has_context = bool(
            context
            and (
                context.base_context.get("organisatorisch")
                or context.base_context.get("domein")
            )
        )

        # Bepaal ontologische categorie indien beschikbaar
        ont_cat = ""
        if context and context.metadata.get("ontologische_categorie"):
            category = context.metadata["ontologische_categorie"]
            category_hints = {
                "proces": "activiteit/handeling",
                "type": "soort/categorie",
                "resultaat": "uitkomst/gevolg",
                "exemplaar": "specifiek geval",
            }
            if category in category_hints:
                ont_cat = f"\n🎯 Focus: Dit is een **{category}** ({category_hints[category]})"

        return f"""### 🎯 FINALE INSTRUCTIES:

#### ✏️ Definitieopdracht:
Formuleer nu de definitie van **{begrip}** volgens deze specificaties:

📋 **CHECKLIST - Controleer voor je antwoord:**
□ Begint met zelfstandig naamwoord (geen lidwoord/koppelwerkwoord)
□ Eén enkele zin zonder punt aan het einde
□ Geen toelichting, voorbeelden of haakjes
□ Ontologische categorie is duidelijk{ont_cat}
□ Geen verboden woorden (aspect, element, kan, moet, etc.)
□ Context verwerkt zonder expliciete benoeming

#### 🔍 KWALITEITSCONTROLE:
Stel jezelf deze vragen:
1. Is direct duidelijk WAT het begrip is (niet het doel)?
2. Kan iemand hiermee bepalen of iets wel/niet onder dit begrip valt?
3. Is de formulering specifiek genoeg voor {"de gegeven context" if has_context else "algemeen gebruik"}?
4. Bevat de definitie alleen essentiële informatie?

#### 📊 METADATA voor traceerbaarheid:
- Begrip: {begrip}
- Timestamp: {context.metadata.get('timestamp', 'N/A') if context else 'N/A'}
- Context beschikbaar: {"Ja" if has_context else "Nee"}
- Builder versie: ModularPromptBuilder v1.0

---

📋 **Ontologische marker (lever als eerste regel):**
- Ontologische categorie: kies uit [soort, exemplaar, proces, resultaat]

✏️ Geef nu de definitie van het begrip **{begrip}** in één enkele zin, zonder toelichting.

🆔 Promptmetadata:
- Begrip: {begrip}
- Termtype: {"werkwoord" if begrip.endswith(("en", "eren", "ieren")) else "anders"}
- Organisatorische context(en): {', '.join(context.base_context.get('organisatorisch', [])) if context and context.base_context.get('organisatorisch') else 'geen'}"""

    # ==========================================
    # UTILITY METHODEN
    # ==========================================

    def _count_active_components(self) -> int:
        """Tel actieve componenten op basis van configuratie."""
        return sum(
            [
                self.component_config.include_role,
                self.component_config.include_context,
                self.component_config.include_ontological,
                self.component_config.include_validation_rules,
                self.component_config.include_forbidden_patterns,
                self.component_config.include_final_instructions,
            ]
        )

    def _estimate_tokens(self, text: str) -> int:
        """Schat aantal tokens voor resource planning."""
        # Simpele schatting: ~1.3 tokens per woord voor Nederlandse tekst
        word_count = len(text.split())
        return int(word_count * 1.3)

    def _estimate_total_tokens(self, begrip: str, context: EnrichedContext) -> int:
        """Schat totaal aantal tokens voor resource planning."""
        base_tokens = 3000  # Basis ESS-02 prompt

        # Context adds tokens
        if context.base_context.get("organisatorisch"):
            base_tokens += 100
        if context.base_context.get("domein"):
            base_tokens += 100

        # Ontological category adds detailed guidance
        if context.metadata.get("ontologische_categorie"):
            base_tokens += 200  # Extra category guidance

        # Validation rules are substantial
        if self.component_config.include_validation_rules:
            base_tokens += 2000

        return base_tokens

    def _apply_compact_mode(self, prompt: str) -> str:
        """Apply compact mode transformations (experimenteel)."""
        if not self.component_config.compact_mode:
            return prompt

        # TODO: Implementeer compactie logica indien gewenst
        # Bijvoorbeeld: verwijder voorbeelden, verkort uitleg, etc.
        logger.debug("Compact mode toegepast")
        return prompt


# Import time voor performance metingen (optioneel)
try:
    import time
except ImportError:
    time = None
    logger.warning("Time module niet beschikbaar - geen performance metingen")
