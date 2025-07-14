"""
DefinitieGenerator Module - Intelligente definitie generatie met feedback integration.
Interpreteert toetsregels als creatieve richtlijnen voor optimale GPT prompts.

Deze module bevat de kern AI definitie generatie logica,
inclusief context verwerking en hybride bron integratie.
"""

import logging  # Logging faciliteiten voor debug en monitoring
from typing import Dict, List, Any, Optional  # Type hints voor betere code documentatie
from dataclasses import dataclass  # Dataklassen voor gestructureerde generatie data
from enum import Enum  # Enumeraties voor categorieën
import json  # JSON verwerking voor API communicatie

# Importeer configuratie en voorbeeld generatie componenten
from config.toetsregel_manager import get_toetsregel_manager, ToetsregelManager  # Toetsregel beheer
from config.config_adapters import get_api_config  # API configuratie toegang
from voorbeelden.unified_voorbeelden import (
    get_examples_generator, ExampleRequest, ExampleType, GenerationMode,  # Voorbeeld generatie klassen
    genereer_alle_voorbeelden  # Bulk voorbeeld generatie functie
)
# Hybride context imports
try:
    from hybrid_context.hybrid_context_engine import get_hybrid_context_engine, HybridContext
    HYBRID_CONTEXT_AVAILABLE = True
except ImportError:
    # Fallback als hybride context niet beschikbaar is
    HYBRID_CONTEXT_AVAILABLE = False  # Markeer als niet beschikbaar
    logger = logging.getLogger(__name__)  # Verkrijg logger
    logger.warning("Hybrid context module niet beschikbaar - fallback naar standaard generatie")

logger = logging.getLogger(__name__)  # Logger instantie voor dit bestand


class OntologischeCategorie(Enum):
    """Ontologische categorieën voor begrippen classificatie."""
    TYPE = "type"              # Categorie voor types/klassen
    PROCES = "proces"          # Categorie voor processen/activiteiten
    RESULTAAT = "resultaat"    # Categorie voor uitkomsten/resultaten
    EXEMPLAAR = "exemplaar"    # Categorie voor specifieke instanties


@dataclass
class GenerationInstruction:
    """Instructie voor definitie generatie uit een toetsregel."""
    rule_id: str                     # Unieke identificatie van de toetsregel
    guidance: str                    # Positieve instructie voor definitie generatie
    template: Optional[str] = None   # Template structuur voor consistente opbouw
    examples: List[str] = None       # Goede voorbeelden ter referentie
    focus_areas: List[str] = None    # Aandachtsgebieden voor kwaliteit
    priority: str = "medium"         # Prioriteit niveau van deze instructie
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []
        if self.focus_areas is None:
            self.focus_areas = []


@dataclass
class GenerationContext:
    """Context voor definitie generatie.
    
    Bevat alle informatie die nodig is voor het genereren van een definitie,
    inclusief basis context en optionele hybride uitbreidingen.
    """
    # Basis context informatie
    begrip: str  # Het begrip dat gedefinieerd moet worden
    organisatorische_context: str  # Organisatorische context (bijv. OM, DJI)
    juridische_context: str  # Juridische context (bijv. Strafrecht)
    categorie: OntologischeCategorie  # Ontologische categorie van het begrip
    
    # Feedback en instructies
    feedback_history: List[str] = None  # Eerdere feedback voor iteratieve verbetering
    custom_instructions: List[str] = None  # Aangepaste instructies van gebruiker
    
    # Hybride context uitbreidingen voor document/web integratie
    hybrid_context: Optional[Any] = None  # HybridContext object voor uitgebreide context
    use_hybrid_enhancement: bool = False  # Of hybride verrijking gebruikt moet worden
    web_context: Optional[Dict[str, Any]] = None  # Context uit web bronnen
    document_context: Optional[Dict[str, Any]] = None  # Context uit geüploade documenten
    
    def __post_init__(self):
        """Initialiseer lege lijsten voor optionele velden."""
        # Initialiseer feedback history als lege lijst indien None
        if self.feedback_history is None:
            self.feedback_history = []
        # Initialiseer custom instructions als lege lijst indien None
        if self.custom_instructions is None:
            self.custom_instructions = []


@dataclass
class GenerationResult:
    """Resultaat van definitie generatie.
    
    Bevat de gegenereerde definitie plus alle metadata over
    hoe de definitie is gegenereerd.
    """
    # Kern resultaat
    definitie: str  # De gegenereerde definitie tekst
    gebruikte_instructies: List[GenerationInstruction]  # Welke regels zijn gebruikt
    prompt_template: str  # De gebruikte AI prompt template
    
    # Metadata
    iteration_nummer: int = 1  # Welke iteratie van verbetering
    context: GenerationContext = None  # Context die gebruikt is
    
    # Voorbeelden uitbreidingen voor aanvullende content
    voorbeelden: Dict[str, List[str]] = None  # Gegenereerde voorbeelden per type
    voorbeelden_gegenereerd: bool = False  # Of voorbeelden succesvol zijn gegenereerd
    voorbeelden_error: Optional[str] = None  # Eventuele fout bij voorbeelden generatie
    
    def __post_init__(self):
        """Initialiseer lege dictionary voor voorbeelden."""
        # Initialiseer voorbeelden als lege dictionary indien None
        if self.voorbeelden is None:
            self.voorbeelden = {}


class RegelInterpreter:
    """Interpreteert toetsregels voor definitie generatie.
    
    Deze klasse vertaalt kwaliteitstoetsregels naar positieve
    instructies die gebruikt kunnen worden in AI prompts.
    """
    
    def __init__(self):
        """Initialiseer regel interpreter met toetsregel manager."""
        # Verkrijg toetsregel manager voor toegang tot regels
        self.rule_manager = get_toetsregel_manager()
    
    def for_generation(self, regel_data: Dict[str, Any]) -> GenerationInstruction:
        """
        Converteer toetsregel naar generatie instructie.
        
        Args:
            regel_data: Regel data uit ToetsregelManager
            
        Returns:
            GenerationInstruction met positieve guidance
        """
        regel_id = regel_data.get("id", "")
        
        # Basis guidance uit uitleg
        base_guidance = self._extract_positive_guidance(regel_data)
        
        # Template op basis van regel type
        template = self._build_template(regel_data)
        
        # Goede voorbeelden extraheren
        examples = regel_data.get("goede_voorbeelden", [])
        
        # Focus areas bepalen
        focus_areas = self._determine_focus_areas(regel_data)
        
        # Prioriteit
        priority = regel_data.get("prioriteit", "medium")
        
        return GenerationInstruction(
            rule_id=regel_id,
            guidance=base_guidance,
            template=template,
            examples=examples,
            focus_areas=focus_areas,
            priority=priority
        )
    
    def _extract_positive_guidance(self, regel_data: Dict[str, Any]) -> str:
        """Extraheer positieve guidance uit regel."""
        regel_id = regel_data.get("id", "")
        uitleg = regel_data.get("uitleg", "")
        
        # Regel-specifieke positive guidance
        guidance_mapping = {
            "CON-01": "Formuleer de definitie specifiek voor de gegeven context zonder de context expliciet te benoemen. Gebruik terminologie en concepten die herkenbaar zijn binnen de context.",
            
            "CON-02": "Baseer de definitie op een authentieke, gezaghebbende bron zoals wetgeving of officiële documenten. Verwijs impliciet naar de bron door gebruik van gerelateerde terminologie.",
            
            "ESS-01": "Beschrijf wat het begrip IS, niet wat het doel of de bedoeling ervan is. Focus op de essentie en kenmerken, niet op functionaliteit.",
            
            "ESS-02": "Maak expliciet duidelijk of het begrip een type/soort, een specifiek exemplaar, een proces/activiteit, of een resultaat/uitkomst betreft.",
            
            "ESS-03": "Voeg unieke identificerende kenmerken toe waarmee verschillende instanties van het begrip onderscheiden kunnen worden.",
            
            "ESS-04": "Gebruik objectief toetsbare criteria zoals aantallen, percentages, deadlines of meetbare kenmerken waar relevant.",
            
            "ESS-05": "Benadruk de onderscheidende kenmerken die dit begrip uniek maken ten opzichte van gerelateerde begrippen.",
            
            "INT-01": "Formuleer als één helder gestructureerde zin die compact maar volledig is.",
            
            "INT-03": "Gebruik duidelijke verwijzingen - als je 'deze', 'die', 'het' gebruikt, zorg dat duidelijk is waarnaar verwezen wordt.",
            
            "INT-06": "Geef alleen de kernafbakening van het begrip, geen toelichting of voorbeelden in de definitie zelf.",
            
            "STR-01": "Start de definitie met het centrale zelfstandig naamwoord dat het begrip het beste weergeeft.",
            
            "STR-02": "Vermijd abstracte of nietszeggende termen. Gebruik concrete, specifieke benamingen.",
        }
        
        return guidance_mapping.get(regel_id, uitleg)
    
    def _build_template(self, regel_data: Dict[str, Any]) -> Optional[str]:
        """Bouw template structuur voor regel."""
        regel_id = regel_data.get("id", "")
        
        # Template mapping per regel
        template_mapping = {
            "ESS-02": "[KERNWOORD] [dat/die] [SPECIFICATIE] [ONDERSCHEIDENDE_KENMERKEN]",
            "STR-01": "[KERNZELFSTANDIGNAAMWOORD] [nadere_specificatie]",
            "ESS-05": "[BEGRIP] [dat zich onderscheidt door] [UNIEKE_KENMERKEN] [van vergelijkbare begrippen]",
            "CON-01": "[BEGRIP] [contextspecifieke_kenmerken] [zonder_expliciete_contextvermelding]"
        }
        
        return template_mapping.get(regel_id)
    
    def _determine_focus_areas(self, regel_data: Dict[str, Any]) -> List[str]:
        """Bepaal focus areas voor regel."""
        regel_id = regel_data.get("id", "")
        thema = regel_data.get("thema", "")
        
        focus_mapping = {
            "CON-01": ["context_specificiteit", "impliciete_aanpassingen"],
            "CON-02": ["authentieke_bronnen", "gezaghebbendheid"], 
            "ESS-01": ["wat_het_is", "essentie_vs_doel"],
            "ESS-02": ["ontologische_categorie", "type_proces_resultaat"],
            "ESS-03": ["unieke_identificatie", "onderscheidbaarheid"],
            "ESS-04": ["objectieve_criteria", "meetbaarheid"],
            "ESS-05": ["onderscheidende_kenmerken", "uniciteit"],
            "INT-01": ["compacte_formulering", "enkele_zin"],
            "INT-03": ["duidelijke_verwijzingen", "pronomen_duidelijkheid"],
            "STR-01": ["kernzelfstandignaamwoord", "juiste_startwoord"]
        }
        
        return focus_mapping.get(regel_id, [thema] if thema else [])


class DefinitieGenerator:
    """Intelligente generator voor definities met toetsregel-gebaseerde guidance."""
    
    def __init__(self):
        self.rule_manager = get_toetsregel_manager()
        self.interpreter = RegelInterpreter()
        self.api_config = get_api_config()
        
        # Template structuren per ontologische categorie
        self.category_templates = {
            OntologischeCategorie.TYPE: {
                "base_structure": "[KERNZELFSTANDIGNAAMWOORD] die/dat [ONDERSCHEIDENDE_KENMERKEN] [SCOPE_AFBAKENING]",
                "examples": [
                    "Document dat eigendomsrechten vastlegt voor onroerend goed",
                    "Proces dat systematisch gegevens verzamelt voor besluitvorming"
                ],
                "focus": ["categorisering", "onderscheidende_kenmerken", "scope_definitie"]
            },
            
            OntologischeCategorie.PROCES: {
                "base_structure": "[ACTIVITEIT_ZELFSTANDIGNAAMWOORD] waarbij [SPECIFIEKE_HANDELINGEN] [DOEL_RESULTAAT]",
                "examples": [
                    "Verificatie waarbij identiteitsgegevens worden gecontroleerd tegen authentieke bronnen",
                    "Beoordeling waarbij risicofactoren worden geanalyseerd voor besluitvorming"
                ],
                "focus": ["activiteit_beschrijving", "concrete_stappen", "meetbaar_resultaat"]
            },
            
            OntologischeCategorie.RESULTAAT: {
                "base_structure": "[RESULTAAT_ZELFSTANDIGNAAMWOORD] dat ontstaat uit [OORSPRONG_PROCES] [KENMERKEN]",
                "examples": [
                    "Besluit dat volgt uit beoordeling van aanvraaggegevens volgens vastgestelde criteria",
                    "Rapport dat resulteert uit analyse van verzamelde onderzoeksgegevens"
                ],
                "focus": ["outcome_beschrijving", "oorsprong_link", "resultaat_kenmerken"]
            },
            
            OntologischeCategorie.EXEMPLAAR: {
                "base_structure": "[SPECIFIEK_ITEM] behorend tot [BREDERE_CATEGORIE] [UNIEKE_IDENTIFICATIE]",
                "examples": [
                    "Document met uniek registratienummer behorend tot de categorie bewijsstukken",
                    "Persoon met specifieke rol geregistreerd in het systeem voor casemanagement"
                ],
                "focus": ["specifieke_identificatie", "categorie_behorend", "unieke_eigenschappen"]
            }
        }
    
    def generate(
        self, 
        context: GenerationContext,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> GenerationResult:
        """
        Genereer definitie op basis van context en toetsregels.
        Ondersteunt hybride context verrijking wanneer beschikbaar.
        
        Args:
            context: GenerationContext met begrip en context info
            model: GPT model override
            temperature: Temperature override
            max_tokens: Max tokens override
            
        Returns:
            GenerationResult met gegenereerde definitie
        """
        logger.info(f"Generating definitie voor '{context.begrip}' categorie {context.categorie.value}")
        
        # 1. Check voor hybrid context enhancement
        if context.use_hybrid_enhancement and HYBRID_CONTEXT_AVAILABLE:
            context = self._enhance_with_hybrid_context(context)
        
        # 2. Laad relevante regels
        instructies = self._load_generation_instructions(context)
        
        # 3. Bouw prompt (nu mogelijk met hybrid context)
        prompt = self._build_generation_prompt(context, instructies)
        
        # 4. Roep GPT aan
        definitie = self._call_gpt(prompt, model, temperature, max_tokens)
        
        # 5. Return resultaat met definitie
        result = GenerationResult(
            definitie=definitie,
            gebruikte_instructies=instructies,
            prompt_template=prompt,
            context=context
        )
        
        return result
    
    def generate_with_examples(
        self,
        context: GenerationContext,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        generate_examples: bool = True,
        example_types: List[ExampleType] = None
    ) -> GenerationResult:
        """
        Genereer definitie met voorbeelden.
        
        Args:
            context: GenerationContext met begrip en context info
            model: GPT model override
            temperature: Temperature override  
            max_tokens: Max tokens override
            generate_examples: Of voorbeelden gegenereerd moeten worden
            example_types: Specifieke types voorbeelden (standaard: sentence, practical, counter)
            
        Returns:
            GenerationResult met definitie en voorbeelden
        """
        logger.info(f"Generating definitie met voorbeelden voor '{context.begrip}'")
        
        # 1. Genereer basis definitie
        result = self.generate(context, model, temperature, max_tokens)
        
        # 2. Genereer voorbeelden indien gewenst
        if generate_examples and result.definitie:
            try:
                # Standaard example types
                if example_types is None:
                    example_types = [ExampleType.SENTENCE, ExampleType.PRACTICAL, ExampleType.COUNTER]
                
                # Context dictionary voorbereiden
                context_dict = {
                    'organisatorisch': [context.organisatorische_context] if context.organisatorische_context else [],
                    'juridisch': [context.juridische_context] if context.juridische_context else [],
                    'wettelijk': []  # Kan later uitgebreid worden
                }
                
                # Genereer alle gevraagde voorbeelden
                voorbeelden_result = {}
                examples_generator = get_examples_generator()
                
                for example_type in example_types:
                    logger.debug(f"Generating {example_type.value} examples")
                    
                    request = ExampleRequest(
                        begrip=context.begrip,
                        definitie=result.definitie,
                        context_dict=context_dict,
                        example_type=example_type,
                        generation_mode=GenerationMode.RESILIENT,
                        max_examples=3
                    )
                    
                    response = examples_generator.generate_examples(request)
                    
                    if response.success:
                        voorbeelden_result[example_type.value] = response.examples
                        logger.debug(f"Generated {len(response.examples)} {example_type.value} examples")
                    else:
                        logger.warning(f"Failed to generate {example_type.value}: {response.error_message}")
                        voorbeelden_result[example_type.value] = []
                
                # Update result met voorbeelden
                result.voorbeelden = voorbeelden_result
                result.voorbeelden_gegenereerd = True
                
                logger.info(f"Successfully generated examples for {len(voorbeelden_result)} types")
                
            except Exception as e:
                logger.error(f"Voorbeelden generatie gefaald: {e}")
                result.voorbeelden_error = str(e)
                result.voorbeelden_gegenereerd = False
        
        return result
    
    def generate_examples_only(
        self,
        begrip: str,
        definitie: str,
        organisatorische_context: str = "",
        juridische_context: str = "",
        example_types: List[ExampleType] = None
    ) -> Dict[str, List[str]]:
        """
        Genereer alleen voorbeelden voor een bestaande definitie.
        
        Args:
            begrip: Het begrip waarvoor voorbeelden gegenereerd worden
            definitie: De bestaande definitie
            organisatorische_context: Organisatorische context
            juridische_context: Juridische context
            example_types: Types voorbeelden (standaard: sentence, practical, counter)
            
        Returns:
            Dictionary met voorbeelden per type
        """
        logger.info(f"Generating examples only voor '{begrip}'")
        
        # Standaard example types
        if example_types is None:
            example_types = [ExampleType.SENTENCE, ExampleType.PRACTICAL, ExampleType.COUNTER]
        
        # Context dictionary voorbereiden
        context_dict = {
            'organisatorisch': [organisatorische_context] if organisatorische_context else [],
            'juridisch': [juridische_context] if juridische_context else [],
            'wettelijk': []
        }
        
        # Genereer voorbeelden
        voorbeelden_result = {}
        examples_generator = get_examples_generator()
        
        for example_type in example_types:
            try:
                logger.debug(f"Generating {example_type.value} examples")
                
                request = ExampleRequest(
                    begrip=begrip,
                    definitie=definitie,
                    context_dict=context_dict,
                    example_type=example_type,
                    generation_mode=GenerationMode.RESILIENT,
                    max_examples=3
                )
                
                response = examples_generator.generate_examples(request)
                
                if response.success:
                    voorbeelden_result[example_type.value] = response.examples
                    logger.debug(f"Generated {len(response.examples)} {example_type.value} examples")
                else:
                    logger.warning(f"Failed to generate {example_type.value}: {response.error_message}")
                    voorbeelden_result[example_type.value] = []
                    
            except Exception as e:
                logger.error(f"Failed to generate {example_type.value} examples: {e}")
                voorbeelden_result[example_type.value] = []
        
        logger.info(f"Generated examples for {len([k for k, v in voorbeelden_result.items() if v])} types")
        return voorbeelden_result
    
    def _load_generation_instructions(self, context: GenerationContext) -> List[GenerationInstruction]:
        """Laad relevante toetsregels als generatie instructies."""
        instructies = []
        
        # Laad kritieke regels (verplicht + hoog prioriteit)
        kritieke_regels = self.rule_manager.get_kritieke_regels()
        
        # Laad categorie-specifieke regels
        categorie_regels = self.rule_manager.get_regels_voor_categorie(context.categorie.value)
        
        # Combineer en deduplicate
        alle_regels = {regel['id']: regel for regel in kritieke_regels + categorie_regels}
        
        # Converteer naar instructies
        for regel_data in alle_regels.values():
            instructie = self.interpreter.for_generation(regel_data)
            instructies.append(instructie)
        
        # Sorteer op prioriteit
        prioriteit_order = {"hoog": 3, "midden": 2, "laag": 1}
        instructies.sort(key=lambda x: prioriteit_order.get(x.priority, 1), reverse=True)
        
        logger.debug(f"Loaded {len(instructies)} generatie instructies")
        return instructies
    
    # Oude _build_generation_prompt methode vervangen door hybrid versie hierboven
    
    def _call_gpt(
        self, 
        prompt: str, 
        model: str = None, 
        temperature: float = None, 
        max_tokens: int = None
    ) -> str:
        """
        Roep GPT API aan voor definitie generatie.
        """
        # Get config parameters
        gpt_params = self.api_config.get_gpt_call_params(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        logger.info(f"Calling GPT with model {gpt_params['model']}, temp {gpt_params['temperature']}")
        
        try:
            # Import OpenAI client
            from ai_toetser.core import _get_openai_client
            
            # Get OpenAI client
            client = _get_openai_client()
            
            # Make API call
            response = client.chat.completions.create(
                model=gpt_params['model'],
                messages=[{"role": "user", "content": prompt}],
                temperature=gpt_params['temperature'],
                max_tokens=gpt_params['max_tokens']
            )
            
            # Extract and return content
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"GPT API call failed: {e}")
            # Return placeholder on error
            return f"[PLACEHOLDER] Definitie voor begrip zou hier komen op basis van prompt met {len(prompt)} karakters"
    
    def generate_with_feedback(
        self,
        context: GenerationContext,
        max_iterations: int = 3
    ) -> GenerationResult:
        """
        Genereer definitie met iteratieve verbetering.
        Dit wordt later uitgebreid in de DefinitieAgent.
        """
        # Voor nu simpele generatie - wordt uitgebreid in Fase 2
        return self.generate(context)
    
    def _enhance_with_hybrid_context(self, context: GenerationContext) -> GenerationContext:
        """
        Enhance generation context met hybrid context verrijking.
        
        Args:
            context: Basis generation context
            
        Returns:
            Enhanced context met hybrid data
        """
        try:
            if not HYBRID_CONTEXT_AVAILABLE:
                logger.warning("Hybrid context niet beschikbaar - skip enhancement")
                return context
            
            logger.info(f"Enhancing context voor '{context.begrip}' met hybrid context")
            
            # Gebruik bestaande hybrid context of creëer nieuwe
            if context.hybrid_context is None:
                hybrid_engine = get_hybrid_context_engine()
                
                # Bepaal selected document IDs (zou uit context moeten komen)
                selected_doc_ids = getattr(context, 'selected_document_ids', None)
                
                # Creëer hybrid context
                hybrid_context = hybrid_engine.create_hybrid_context(
                    begrip=context.begrip,
                    organisatorische_context=context.organisatorische_context,
                    juridische_context=context.juridische_context,
                    selected_document_ids=selected_doc_ids
                )
                
                # Update context
                context.hybrid_context = hybrid_context
                context.web_context = hybrid_context.web_context
                context.document_context = hybrid_context.document_context
            
            logger.info(f"Hybrid context enhanced (confidence: {context.hybrid_context.confidence_score:.2f})")
            return context
            
        except Exception as e:
            logger.error(f"Fout bij hybrid context enhancement: {e}")
            # Return original context als fallback
            return context
    
    def _build_generation_prompt(self, context: GenerationContext, instructies: List[GenerationInstruction]) -> str:
        """
        Bouw generation prompt, mogelijk met hybrid context enhancement.
        
        Args:
            context: Generation context (mogelijk enhanced)
            instructies: Generation instructies uit toetsregels
            
        Returns:
            Complete generation prompt
        """
        # Basis prompt onderdelen
        prompt_sections = []
        
        # Systeem instructies
        prompt_sections.append("=== SYSTEEM INSTRUCTIE ===")
        prompt_sections.append("Je bent een expert in juridische definitie generatie.")
        prompt_sections.append("Genereer een precieze, juridisch correcte definitie.")
        
        # Ontologische categorie template
        category_template = self.category_templates.get(context.categorie, {})
        if category_template:
            prompt_sections.append(f"\n=== STRUCTUUR TEMPLATE ({context.categorie.value.upper()}) ===")
            prompt_sections.append(f"Basis structuur: {category_template.get('base_structure', '')}")
            prompt_sections.append(f"Focus op: {', '.join(category_template.get('focus', []))}")
        
        # Toetsregel instructies
        if instructies:
            prompt_sections.append("\n=== GENERATIE RICHTLIJNEN ===")
            for instructie in instructies:
                prompt_sections.append(f"• {instructie.guidance}")
                if instructie.focus_areas:
                    prompt_sections.append(f"  Focus: {', '.join(instructie.focus_areas)}")
        
        # Hybrid context (indien beschikbaar)
        if context.use_hybrid_enhancement and context.hybrid_context:
            hybrid_section = self._build_hybrid_context_section(context.hybrid_context)
            prompt_sections.append(hybrid_section)
        
        # Basis context informatie
        prompt_sections.append(f"\n=== CONTEXT INFORMATIE ===")
        prompt_sections.append(f"Begrip: {context.begrip}")
        prompt_sections.append(f"Organisatorische context: {context.organisatorische_context}")
        prompt_sections.append(f"Juridische context: {context.juridische_context}")
        prompt_sections.append(f"Ontologische categorie: {context.categorie.value}")
        
        # Custom instructies
        if context.custom_instructions:
            prompt_sections.append("\n=== AANVULLENDE INSTRUCTIES ===")
            for instruction in context.custom_instructions:
                prompt_sections.append(f"• {instruction}")
        
        # Feedback history
        if context.feedback_history:
            prompt_sections.append("\n=== FEEDBACK HISTORIE ===")
            for feedback in context.feedback_history[-3:]:  # Laatste 3 feedback items
                prompt_sections.append(f"• {feedback}")
        
        # Generatie opdracht
        prompt_sections.append(f"\n=== OPDRACHT ===")
        prompt_sections.append(f"Genereer een definitie voor '{context.begrip}' volgens bovenstaande richtlijnen.")
        prompt_sections.append("Zorg voor:")
        prompt_sections.append("- Juridische precisie en correctheid")
        prompt_sections.append("- Duidelijke afbakening en scope")
        prompt_sections.append("- Praktische toepasbaarheid")
        prompt_sections.append("- Consistentie met bestaande terminologie")
        
        if context.hybrid_context:
            confidence = context.hybrid_context.confidence_score
            if confidence > 0.8:
                prompt_sections.append("- Integreer de rijke context uit bronnen optimaal")
            elif confidence > 0.6:
                prompt_sections.append("- Gebruik beschikbare context waar relevant")
            else:
                prompt_sections.append("- Gebruik context zorgvuldig, valideer waar mogelijk")
        
        return "\n".join(prompt_sections)
    
    def _build_hybrid_context_section(self, hybrid_context) -> str:
        """
        Bouw hybrid context sectie voor de prompt.
        
        Args:
            hybrid_context: HybridContext object
            
        Returns:
            Formatted context sectie
        """
        try:
            sections = ["\n=== HYBRIDE CONTEXT VERRIJKING ==="]
            
            # Context quality en confidence
            sections.append(f"Context kwaliteit: {hybrid_context.context_quality}")
            sections.append(f"Betrouwbaarheidscore: {hybrid_context.confidence_score:.2f}")
            sections.append(f"Fusion strategie: {hybrid_context.fusion_strategy}")
            
            # Unified context (de geaggregeerde context)
            if hybrid_context.unified_context:
                sections.append(f"\n=== GEAGGREGEERDE CONTEXT ===")
                # Limiteer context lengte voor prompt efficiency
                context_text = hybrid_context.unified_context
                if len(context_text) > 2000:
                    context_text = context_text[:2000] + "... (afgekapt)"
                sections.append(context_text)
            
            # Bronvermelding
            all_sources = []
            if hybrid_context.web_sources:
                all_sources.extend([f"Web: {src}" for src in hybrid_context.web_sources])
            if hybrid_context.document_sources:
                all_sources.extend([f"Doc: {src.get('filename', 'onbekend')}" for src in hybrid_context.document_sources])
            
            if all_sources:
                sections.append(f"\n=== BRONNEN ===")
                sections.append(f"Primaire bronnen: {', '.join(hybrid_context.primary_sources)}")
                if hybrid_context.supporting_sources:
                    sections.append(f"Ondersteunende bronnen: {', '.join(hybrid_context.supporting_sources)}")
            
            # Instructie voor context gebruik
            sections.append(f"\n=== CONTEXT GEBRUIK INSTRUCTIE ===")
            if hybrid_context.confidence_score > 0.8:
                sections.append("Gebruik deze rijke context optimaal voor een uitgebreide, goed onderbouwde definitie.")
            elif hybrid_context.confidence_score > 0.6:
                sections.append("Integreer relevante elementen uit deze context in je definitie.")
            else:
                sections.append("Gebruik deze context ondersteunend, maar blijf kritisch op relevantie.")
            
            if hybrid_context.conflicts_resolved > 0:
                sections.append(f"Let op: {hybrid_context.conflicts_resolved} conflict(en) zijn opgelost in deze context.")
            
            return "\n".join(sections)
            
        except Exception as e:
            logger.error(f"Fout bij bouwen hybrid context sectie: {e}")
            return "\n=== HYBRID CONTEXT === (fout bij verwerking)"


# Convenience functions
def create_generation_context(
    begrip: str,
    organisatorische_context: str,
    juridische_context: str = "",
    categorie: OntologischeCategorie = OntologischeCategorie.TYPE
) -> GenerationContext:
    """Helper functie om GenerationContext te maken."""
    return GenerationContext(
        begrip=begrip,
        organisatorische_context=organisatorische_context,
        juridische_context=juridische_context,
        categorie=categorie
    )

def create_hybrid_generation_context(
    begrip: str,
    organisatorische_context: str,
    juridische_context: str = "",
    categorie: OntologischeCategorie = OntologischeCategorie.TYPE,
    selected_document_ids: Optional[List[str]] = None,
    enable_hybrid: bool = True
) -> GenerationContext:
    """
    Helper functie om GenerationContext met hybrid context support te maken.
    
    Args:
        begrip: Het te definiëren begrip
        organisatorische_context: Organisatorische context
        juridische_context: Juridische context
        categorie: Ontologische categorie
        selected_document_ids: IDs van geselecteerde documenten
        enable_hybrid: Of hybrid context enhancement gebruikt moet worden
        
    Returns:
        GenerationContext klaar voor hybrid enhancement
    """
    context = GenerationContext(
        begrip=begrip,
        organisatorische_context=organisatorische_context,
        juridische_context=juridische_context,
        categorie=categorie,
        use_hybrid_enhancement=enable_hybrid and HYBRID_CONTEXT_AVAILABLE
    )
    
    # Voeg selected_document_ids toe als attribuut
    if selected_document_ids:
        context.selected_document_ids = selected_document_ids
    
    return context


def generate_definitie(
    begrip: str,
    organisatorische_context: str,
    categorie: str = "type",
    **kwargs
) -> str:
    """
    Convenience functie voor snelle definitie generatie.
    
    Args:
        begrip: Het te definiëren begrip
        organisatorische_context: Organisatorische context
        categorie: Ontologische categorie ("type", "proces", "resultaat", "exemplaar")
        **kwargs: Extra parameters voor GPT call
        
    Returns:
        Gegenereerde definitie string
    """
    generator = DefinitieGenerator()
    
    # Converteer string naar enum
    cat_mapping = {
        "type": OntologischeCategorie.TYPE,
        "proces": OntologischeCategorie.PROCES,
        "resultaat": OntologischeCategorie.RESULTAAT,
        "exemplaar": OntologischeCategorie.EXEMPLAAR
    }
    
    context = GenerationContext(
        begrip=begrip,
        organisatorische_context=organisatorische_context,
        juridische_context=kwargs.get("juridische_context", ""),
        categorie=cat_mapping.get(categorie.lower(), OntologischeCategorie.TYPE)
    )
    
    result = generator.generate(context, **kwargs)
    return result.definitie


if __name__ == "__main__":
    # Test de DefinitieGenerator
    print("🚀 Testing DefinitieGenerator")
    print("=" * 30)
    
    # Test RegelInterpreter
    interpreter = RegelInterpreter()
    rule_manager = get_toetsregel_manager()
    
    # Test met CON-01 regel
    con01 = rule_manager.load_regel("CON-01")
    if con01:
        instructie = interpreter.for_generation(con01)
        print(f"✅ CON-01 instructie: {instructie.guidance[:100]}...")
        print(f"📝 Template: {instructie.template}")
        print(f"🎯 Focus areas: {instructie.focus_areas}")
    
    # Test DefinitieGenerator
    generator = DefinitieGenerator()
    
    # Test context
    context = create_generation_context(
        begrip="toezicht",
        organisatorische_context="DJI",
        categorie=OntologischeCategorie.PROCES
    )
    
    # Genereer definitie
    result = generator.generate(context)
    print(f"\n✅ Definitie gegenereerd: {result.definitie[:100]}...")
    print(f"📊 Gebruikte instructies: {len(result.gebruikte_instructies)}")
    
    # Test convenience function
    quick_def = generate_definitie("registratie", "OM", "proces")
    print(f"\n🔧 Quick definitie: {quick_def[:100]}...")
    
    print("\n🎯 DefinitieGenerator test voltooid!")