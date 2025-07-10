"""
DefinitieGenerator Module - Intelligente definitie generatie met feedback integration.
Interpreteert toetsregels als creatieve richtlijnen voor optimale GPT prompts.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

from config.toetsregel_manager import get_toetsregel_manager, ToetsregelManager
from config.config_adapters import get_api_config

logger = logging.getLogger(__name__)


class OntologischeCategorie(Enum):
    """Ontologische categorieën voor begrippen."""
    TYPE = "type"
    PROCES = "proces" 
    RESULTAAT = "resultaat"
    EXEMPLAAR = "exemplaar"


@dataclass
class GenerationInstruction:
    """Instructie voor definitie generatie uit een toetsregel."""
    rule_id: str
    guidance: str                    # Positieve instructie
    template: Optional[str] = None   # Template structuur
    examples: List[str] = None       # Goede voorbeelden
    focus_areas: List[str] = None    # Waar op te focussen
    priority: str = "medium"         # Prioriteit van deze instructie
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []
        if self.focus_areas is None:
            self.focus_areas = []


@dataclass
class GenerationContext:
    """Context voor definitie generatie."""
    begrip: str
    organisatorische_context: str
    juridische_context: str
    categorie: OntologischeCategorie
    feedback_history: List[str] = None
    custom_instructions: List[str] = None
    
    def __post_init__(self):
        if self.feedback_history is None:
            self.feedback_history = []
        if self.custom_instructions is None:
            self.custom_instructions = []


@dataclass
class GenerationResult:
    """Resultaat van definitie generatie."""
    definitie: str
    gebruikte_instructies: List[GenerationInstruction]
    prompt_template: str
    iteration_nummer: int = 1
    context: GenerationContext = None


class RegelInterpreter:
    """Interpreteert toetsregels voor definitie generatie."""
    
    def __init__(self):
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
        
        Args:
            context: GenerationContext met begrip en context info
            model: GPT model override
            temperature: Temperature override
            max_tokens: Max tokens override
            
        Returns:
            GenerationResult met gegenereerde definitie
        """
        logger.info(f"Generating definitie voor '{context.begrip}' categorie {context.categorie.value}")
        
        # 1. Laad relevante regels
        instructies = self._load_generation_instructions(context)
        
        # 2. Bouw prompt
        prompt = self._build_generation_prompt(context, instructies)
        
        # 3. Roep GPT aan
        definitie = self._call_gpt(prompt, model, temperature, max_tokens)
        
        # 4. Return resultaat
        return GenerationResult(
            definitie=definitie,
            gebruikte_instructies=instructies,
            prompt_template=prompt,
            context=context
        )
    
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
    
    def _build_generation_prompt(
        self, 
        context: GenerationContext, 
        instructies: List[GenerationInstruction]
    ) -> str:
        """Bouw intelligente GPT prompt voor definitie generatie."""
        
        # Basis template voor categorie
        category_template = self.category_templates[context.categorie]
        
        # Kern instructies
        kern_instructies = []
        for instructie in instructies[:8]:  # Top 8 belangrijkste
            kern_instructies.append(f"• {instructie.guidance}")
        
        # Feedback integration
        feedback_section = ""
        if context.feedback_history:
            feedback_section = f"""
VERBETERINGEN OP BASIS VAN VORIGE VERSIE:
{chr(10).join(f"• {feedback}" for feedback in context.feedback_history[-3:])}
"""
        
        # Bouw complete prompt
        prompt = f"""TAAK: Genereer een professionele definitie voor '{context.begrip}'

CONTEXT:
• Organisatorisch: {context.organisatorische_context}
• Juridisch: {context.juridische_context}  
• Ontologische categorie: {context.categorie.value.upper()}

STRUCTUUR TEMPLATE ({context.categorie.value}):
{category_template['base_structure']}

VOORBEELDEN VAN GOEDE {context.categorie.value.upper()} DEFINITIES:
{chr(10).join(f"• {example}" for example in category_template['examples'])}

ESSENTIËLE VEREISTEN:
{chr(10).join(kern_instructies)}

FOCUS GEBIEDEN VOOR {context.categorie.value.upper()}:
{chr(10).join(f"• {focus}" for focus in category_template['focus'])}
{feedback_section}
OPDRACHT:
Genereer nu een definitie voor '{context.begrip}' die:
1. Voldoet aan alle essentiële vereisten
2. Past bij de {context.categorie.value} categorie structuur  
3. Specifiek is voor de gegeven context zonder deze expliciet te noemen
4. Professional en helder geformuleerd is

DEFINITIE:"""

        return prompt
    
    def _call_gpt(
        self, 
        prompt: str, 
        model: str = None, 
        temperature: float = None, 
        max_tokens: int = None
    ) -> str:
        """
        Roep GPT API aan voor definitie generatie.
        
        Note: Dit is een placeholder implementatie.
        In productie zou dit de echte OpenAI API aanroepen.
        """
        # Get config parameters
        gpt_params = self.api_config.get_gpt_call_params(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        logger.info(f"Calling GPT with model {gpt_params['model']}, temp {gpt_params['temperature']}")
        
        # TODO: Implement actual OpenAI API call
        # Voor nu returnen we een placeholder
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