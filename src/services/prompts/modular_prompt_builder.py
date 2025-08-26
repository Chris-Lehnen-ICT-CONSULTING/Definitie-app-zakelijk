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
from dataclasses import dataclass
from typing import Any

from abc import ABC, abstractmethod
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
        start_time = time.time() if "time" in globals() else None

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
                forbidden_component = self._build_forbidden_patterns_section()
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
⚠️ Ondubbelzinnigheid is vereist."""

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
- Gebruik actieve in plaats van passieve bewoordingen""",
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

⚠️ **RESULTAAT SPECIFIEKE RICHTLIJNEN:**
- Beschrijf WAAR het uit voortkomt (oorsprong)
- Leg uit WAT het betekent of bewerkstelligt (gevolg)
- Focus op de CAUSALE RELATIE
- Vermeld het proces of de handeling die het resultaat oplevert
- Gebruik resultatgerichte taal (uitkomst, gevolg, product)""",
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

#### 🔷 STRUCTUUR (STR) - Opbouw van de definitie
**STR-01**: Begin ALTIJD met een zelfstandig naamwoord ✓
  - ✅ "Een **overeenkomst** is..."
  - ❌ "**Controleren** is..." (werkwoord)

**STR-02**: Herhaal NIET het te definiëren begrip aan het begin ✗
  - ✅ "Een proces waarbij..." (voor begrip 'validatie')
  - ❌ "Validatie is een validatie van..."

**STR-03**: Geen synoniemen als definitie ✗
  - ✅ "Een proces waarbij documenten worden gecontroleerd"
  - ❌ "Een verificatie" (synoniem)

**STR-04**: Na het hoofdbegrip volgt een TOESPITSING ✓
  - ✅ "Een document **dat** vereisten bevat..."
  - ❌ "Een document" (geen toespitsing)

**STR-07**: GEEN dubbele ontkenning ✗
  - ✅ "Een proces dat fouten detecteert"
  - ❌ "Een proces dat niet zonder fouten is"

#### 🔶 ESSENTIE (ESS) - De kern van het begrip
**ESS-01**: Definieer WAT iets IS, niet waarvoor het dient ✓
  - ✅ "Een overzicht van taken die..."
  - ❌ "Een hulpmiddel om taken te beheren"

**ESS-02**: Maak de ONTOLOGISCHE CATEGORIE duidelijk (KRITIEK!) ✓
  - Type: "is een soort/categorie..."
  - Exemplaar: "is een specifiek geval van..."
  - Proces: "is een activiteit waarbij..."
  - Resultaat: "is het resultaat van..."

**ESS-03**: Instanties moeten TELBAAR zijn ✓
  - ✅ "Een document" (telbaar: 1, 2, 3 documenten)
  - ❌ "Documentatie" (massa-naamwoord)

**ESS-04**: De definitie moet TOETSBAAR zijn ✓
  - ✅ "Een rapport met minimaal 5 hoofdstukken"
  - ❌ "Een goed rapport" (subjectief)

#### 🔸 CONTEXT (CON) - Aanpassing aan de situatie
**CON-01**: Pas de formulering aan op de CONTEXT zonder deze te noemen ✓
  - ✅ Context impliciet: "Een verzoek tot wijziging van..."
  - ❌ "In de ICT-context is dit..."

#### 🔹 INTERNE COHERENTIE (INT) - Helderheid en eenvoud
**INT-01**: Houd de definitie COMPACT en begrijpelijk ✓
  - ✅ Eén heldere zin van max 25 woorden
  - ❌ Lange zinnen met meerdere bijzinnen

**INT-02**: GEEN beslisregels in de definitie ✗
  - ✅ "Een verzoek tot wijziging"
  - ❌ "Een verzoek dat goedgekeurd moet worden als..."

**INT-06**: GEEN toelichting in de definitie ✗
  - ✅ "Een systematische controle van..."
  - ❌ "Een controle (dit wordt uitgevoerd door...)"

**INT-08**: Gebruik POSITIEVE formulering ✓
  - ✅ "Een proces dat fouten detecteert"
  - ❌ "Een proces dat niet foutloos is"

#### 🔺 SAMENHANG (SAM) - Relatie met andere begrippen
**SAM-05**: Voorkom CIRKELDEFINITIES ✗
  - ✅ "Een overzicht van geplande activiteiten"
  - ❌ "Een planning van taken" (voor begrip 'takenplanning')

#### ⚡ AI-SPECIFIEK (ARAI) - Veelgemaakte AI-fouten voorkomen
**ARAI-02**: Vermijd VAGE containerbegrippen ✗
  - ❌ "aspect", "element", "onderdeel", "component", "factor"
  - ✓ Gebruik specifieke termen

**ARAI-03**: BEPERK bijvoeglijke naamwoorden ✓
  - ✅ "Een gestructureerd overzicht"
  - ❌ "Een zeer uitgebreid en gedetailleerd overzicht"

**ARAI-04**: GEEN modale hulpwerkwoorden ✗
  - ❌ "kan", "moet", "mag", "zou", "dient"
  - ✓ Gebruik feitelijke formuleringen

**ARAI-06**: Start CORRECT: geen lidwoord, geen koppelwerkwoord ✓
  - ✅ "Proces waarbij..."
  - ❌ "Het is een proces..." of "Een proces is..."

#### 📋 SAMENVATTING KERNREGELS:
1. Start met zelfstandig naamwoord, NIET met het begrip zelf
2. Expliciteer de ontologische categorie (proces/type/resultaat/exemplaar)
3. Definieer WAT het is, niet het doel
4. Eén compacte zin zonder toelichting
5. Vermijd vage woorden en modale werkwoorden"""

    def _build_forbidden_patterns_section(self) -> str:
        """Component 5: Veelgemaakte fouten en verboden startwoorden."""
        return """### ⚠️ Veelgemaakte fouten (vermijden!):

#### 🚫 VERBODEN STARTWOORDEN:
**NOOIT beginnen met:**
- ❌ "Het..." → "Het proces waarbij..."
- ❌ "De..." → "De activiteit die..."
- ❌ "Een..." als het begrip al "een" bevat
- ❌ Het begrip zelf → "Validatie is een validatie..."
- ❌ Werkwoorden → "Controleren is..."
- ❌ "Dit is..." / "Dat is..."

**WEL beginnen met:**
- ✅ Direct het hoofdwoord: "Proces waarbij..."
- ✅ "Activiteit waarbij..." (voor processen)
- ✅ "Document dat..." (voor objecten)
- ✅ "Systematische aanpak waarbij..." (voor methoden)

#### 🔴 VAGE CONTAINERBEGRIPPEN - ABSOLUUT VERMIJDEN:
**Lexicale containers** (te abstract):
- ❌ "aspect", "element", "onderdeel", "component", "factor"
- ❌ "kwestie", "item", "punt", "deel", "stuk"
- ❌ "gebied", "terrein", "veld", "domein" (als vage aanduiding)

**Ambtelijke containers** (nietszeggende):
- ❌ "aangelegenheid", "materie", "zaak", "geval"
- ❌ "situatie", "omstandigheid", "toestand", "conditie"
- ❌ "middel", "instrument" (tenzij letterlijk een instrument)

**Alternatieven - gebruik specifieke termen:**
- ✅ "proces", "methode", "systeem", "structuur"
- ✅ "document", "rapport", "overzicht", "analyse"
- ✅ "beoordeling", "evaluatie", "controle", "verificatie"

#### ⛔ MODALE WERKWOORDEN - NIET GEBRUIKEN:
**Verboden modaliteiten:**
- ❌ "kan", "moet", "mag", "zou", "dient", "behoort"
- ❌ "mogelijke", "eventuele", "potentiële"
- ❌ "verplichte", "noodzakelijke", "vereiste" (als bijvoeglijk)

**Schrijf feitelijk:**
- ❌ "Een proces dat uitgevoerd **kan** worden..."
- ✅ "Een proces waarbij... wordt uitgevoerd"
- ❌ "Een document dat **moet** bevatten..."
- ✅ "Een document met..."

#### 🚨 CONTEXT-SPECIFIEKE VALKUILEN:
**Vermijd expliciete contextbenoeming:**
- ❌ "In de context van X is dit..."
- ❌ "Voor organisatie Y betekent dit..."
- ❌ "Binnen domein Z wordt dit gezien als..."

**Context impliciet verwerken:**
- ✅ Terminologie aanpassen aan domein
- ✅ Relevante processen/systemen noemen zonder "in context van"
- ✅ Domeinspecifieke termen natuurlijk integreren

#### 💥 TOELICHTING & UITWEIDINGEN:
**Absoluut GEEN:**
- ❌ Haakjes met uitleg: "(dit wordt gebruikt voor...)"
- ❌ Voorbeelden in de definitie: "bijvoorbeeld..."
- ❌ Opsommingen: "zoals A, B, C..."
- ❌ Bijzinnen met "waarbij opgemerkt dat..."

#### 📝 POSITIEVE ALTERNATIEVEN:
In plaats van vage/verboden patronen, gebruik:
1. **Concrete hoofdwoorden** als startpunt
2. **Actieve, feitelijke formuleringen**
3. **Eén hoofdgedachte** zonder uitweidingen
4. **Specifieke terminologie** uit het domein
5. **Heldere relaties** (proces/resultaat/type)"""

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

**ANTWOORD:** Geef nu direct de definitie zonder verdere uitleg of formatting:"""

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
