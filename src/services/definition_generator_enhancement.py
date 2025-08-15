"""
Definition Generator Enhancement Module.

Enhancement systeem voor definitie verbetering:
- Quality improvement (van services implementatie)
- Context integration (van definitie_generator implementatie) 
- Ontological enhancement (van generation implementatie)
- Feedback integration voor iteratieve verbetering
"""

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from services.definition_generator_config import QualityConfig
from services.interfaces import Definition

logger = logging.getLogger(__name__)


class EnhancementType(Enum):
    """Types van enhancements die we kunnen toepassen."""
    
    CLARITY = "clarity"                    # Helderheid verbetering
    CONCISENESS = "conciseness"           # Beknoptheid verbetering  
    COMPLETENESS = "completeness"         # Volledigheid verbetering
    CONSISTENCY = "consistency"           # Consistentie verbetering
    CONTEXT_INTEGRATION = "context"       # Context integratie
    DOMAIN_SPECIFICITY = "domain"         # Domein specificiteit
    ONTOLOGICAL = "ontological"           # Ontologische verbetering
    LINGUISTIC = "linguistic"             # Taalkunde verbetering


@dataclass
class EnhancementResult:
    """Resultaat van een enhancement operatie."""
    
    enhancement_type: EnhancementType
    original_text: str
    enhanced_text: str
    confidence: float  # 0.0 - 1.0
    explanation: str
    applied: bool = False
    
    @property
    def improvement_score(self) -> float:
        """Berekent een score voor de verbetering."""
        if not self.applied or self.original_text == self.enhanced_text:
            return 0.0
        
        # Simple scoring based on length and confidence
        length_factor = abs(len(self.enhanced_text) - len(self.original_text)) / len(self.original_text)
        return self.confidence * (1.0 - min(length_factor, 0.5))


class EnhancementStrategy(ABC):
    """Abstract base class voor enhancement strategieën."""
    
    @abstractmethod
    def enhance(self, definition: Definition) -> List[EnhancementResult]:
        """
        Pas enhancement toe op een definitie.
        
        Args:
            definition: Te verbeteren definitie
            
        Returns:
            Lijst van mogelijke enhancements
        """
        pass
    
    @abstractmethod 
    def get_strategy_name(self) -> str:
        """Verkrijg naam van deze strategy."""
        pass


class ClarityEnhancer(EnhancementStrategy):
    """Enhancement voor helderheid van definities."""
    
    def __init__(self):
        # Patterns die onduidelijkheid indiceren
        self.unclear_patterns = [
            r'\b(enigszins|soms|wellicht|mogelijk|misschien)\b',  # Vague terms
            r'\b(enzovoort|etc\.?|enz\.?)\b',                     # Non-specific endings
            r'\b(diverse|verschillende|meerdere)\b(?!\s+\w+)',   # Vague quantities
            r'\b(dergelijke|soortgelijke)\b(?!\s+\w+)',         # Vague references
        ]
        
        # Verbeteringssuggesties
        self.clarity_improvements = {
            'cirkelredenering': r'\b(\w+)\b.*\b\1\b',  # Word repeated in definition
            'te_kort': lambda text: len(text.strip()) < 30,
            'te_lang': lambda text: len(text.split('.')) > 3,  # More than 3 sentences
        }
    
    def enhance(self, definition: Definition) -> List[EnhancementResult]:
        """Verbeter helderheid van definitie."""
        results = []
        text = definition.definitie
        
        # Check voor vage termen
        vague_score = self._calculate_vagueness_score(text)
        if vague_score > 0.3:
            enhanced_text = self._improve_clarity(text, definition.begrip)
            if enhanced_text != text:
                results.append(EnhancementResult(
                    enhancement_type=EnhancementType.CLARITY,
                    original_text=text,
                    enhanced_text=enhanced_text,
                    confidence=min(vague_score, 0.8),
                    explanation=f"Verbeterde helderheid (vagueness score: {vague_score:.2f})"
                ))
        
        # Check voor cirkelredenering
        if self._has_circular_reasoning(text, definition.begrip):
            enhanced_text = self._fix_circular_reasoning(text, definition.begrip)
            if enhanced_text != text:
                results.append(EnhancementResult(
                    enhancement_type=EnhancementType.CLARITY,
                    original_text=text,
                    enhanced_text=enhanced_text,
                    confidence=0.9,
                    explanation="Cirkelredenering weggenomen"
                ))
        
        return results
    
    def _calculate_vagueness_score(self, text: str) -> float:
        """Bereken vagueness score (0.0 = helder, 1.0 = vaag)."""
        text_lower = text.lower()
        matches = 0
        
        for pattern in self.unclear_patterns:
            matches += len(re.findall(pattern, text_lower, re.IGNORECASE))
        
        # Normalize by text length
        return min(matches / max(len(text.split()), 1) * 10, 1.0)
    
    def _improve_clarity(self, text: str, begrip: str) -> str:
        """Verbeter helderheid van tekst."""
        enhanced = text
        
        # Replace vague terms with more specific ones
        replacements = {
            r'\benzovoort\b': 'en andere gerelateerde aspecten',
            r'\betc\.?\b': 'en andere gerelateerde aspecten',
            r'\benz\.?\b': 'en andere',
            r'\benigszins\b': 'in zekere mate',
            r'\bwellicht\b': 'mogelijk',
            r'\bdergelijke\b': f'vergelijkbare {begrip.lower()}-gerelateerde',
        }
        
        for pattern, replacement in replacements.items():
            enhanced = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)
        
        return enhanced
    
    def _has_circular_reasoning(self, text: str, begrip: str) -> bool:
        """Check of definitie cirkelredenering bevat."""
        text_lower = text.lower()
        begrip_lower = begrip.lower()
        
        # Simple check: begrip appears in definition
        return begrip_lower in text_lower and text_lower.count(begrip_lower) > 1
    
    def _fix_circular_reasoning(self, text: str, begrip: str) -> str:
        """Probeer cirkelredenering te repareren."""
        # Replace second occurrence of begrip with "dit" or similar
        parts = text.lower().split(begrip.lower())
        if len(parts) > 2:
            # Replace subsequent occurrences
            enhanced = begrip.lower().join(parts[:2]) + "dit" + "dit".join(parts[2:])
            return enhanced.capitalize()
        return text
    
    def get_strategy_name(self) -> str:
        return "clarity_enhancer"


class ContextIntegrationEnhancer(EnhancementStrategy):
    """Enhancement voor context integratie."""
    
    def enhance(self, definition: Definition) -> List[EnhancementResult]:
        """Integreer context informatie in definitie."""
        results = []
        text = definition.definitie
        
        # Domein integratie
        if definition.domein and definition.domein.lower() not in text.lower():
            enhanced_text = self._integrate_domain(text, definition.domein)
            if enhanced_text != text:
                results.append(EnhancementResult(
                    enhancement_type=EnhancementType.DOMAIN_SPECIFICITY,
                    original_text=text,
                    enhanced_text=enhanced_text,
                    confidence=0.7,
                    explanation=f"Domein '{definition.domein}' geïntegreerd"
                ))
        
        # Context integratie
        if definition.context and "context" not in text.lower():
            enhanced_text = self._integrate_context(text, definition.context)
            if enhanced_text != text:
                results.append(EnhancementResult(
                    enhancement_type=EnhancementType.CONTEXT_INTEGRATION,
                    original_text=text,
                    enhanced_text=enhanced_text,
                    confidence=0.8,
                    explanation="Context informatie geïntegreerd"
                ))
        
        return results
    
    def _integrate_domain(self, text: str, domein: str) -> str:
        """Integreer domein informatie."""
        if not text.endswith('.'):
            text += '.'
        
        domain_hint = f" Dit begrip wordt gebruikt binnen het {domein.lower()}."
        return text + domain_hint
    
    def _integrate_context(self, text: str, context: str) -> str:
        """Integreer context informatie.""" 
        if not text.endswith('.'):
            text += '.'
        
        # Parse context for meaningful parts
        context_parts = [part.strip() for part in context.split(',')]
        relevant_parts = [part for part in context_parts if len(part) > 2]
        
        if relevant_parts:
            context_hint = f" (binnen de context van {', '.join(relevant_parts)})"
            return text[:-1] + context_hint + '.'
        
        return text
    
    def get_strategy_name(self) -> str:
        return "context_integration_enhancer"


class CompletenessEnhancer(EnhancementStrategy):
    """Enhancement voor volledigheid van definities."""
    
    def __init__(self):
        # Aspecten die vaak missen in definities
        self.completeness_aspects = {
            'doel': ['doel', 'bedoeling', 'functie', 'nut'],
            'scope': ['omvang', 'bereik', 'toepassingsgebied'],  
            'voorwaarden': ['voorwaarde', 'vereiste', 'criteria'],
            'proces': ['stap', 'procedure', 'methode', 'proces'],
            'verantwoordelijk': ['verantwoordelijk', 'bevoegd', 'eigenaar'],
        }
    
    def enhance(self, definition: Definition) -> List[EnhancementResult]:
        """Verbeter volledigheid van definitie.""" 
        results = []
        text = definition.definitie.lower()
        
        # Check missing aspects
        missing_aspects = []
        for aspect, keywords in self.completeness_aspects.items():
            if not any(keyword in text for keyword in keywords):
                missing_aspects.append(aspect)
        
        # Only suggest if significantly incomplete
        if len(missing_aspects) >= 2:
            enhanced_text = self._add_completeness_hints(definition.definitie, 
                                                       missing_aspects, definition.begrip)
            if enhanced_text != definition.definitie:
                results.append(EnhancementResult(
                    enhancement_type=EnhancementType.COMPLETENESS,
                    original_text=definition.definitie,
                    enhanced_text=enhanced_text,
                    confidence=0.6,
                    explanation=f"Volledigheid verbeterd (ontbrekende aspecten: {', '.join(missing_aspects)})"
                ))
        
        return results
    
    def _add_completeness_hints(self, text: str, missing_aspects: List[str], begrip: str) -> str:
        """Voeg volledigheid hints toe."""
        if not text.endswith('.'):
            text += '.'
        
        # Add generic completeness improvement
        if 'doel' in missing_aspects and 'proces' in missing_aspects:
            addition = f" Het {begrip.lower()} heeft een specifiek doel en volgt een bepaalde procedure."
            return text + addition
        elif 'scope' in missing_aspects:
            addition = f" Het toepassingsgebied van {begrip.lower()} is duidelijk afgebakend."
            return text + addition
        
        return text
    
    def get_strategy_name(self) -> str:
        return "completeness_enhancer"


class LinguisticEnhancer(EnhancementStrategy):
    """Enhancement voor taalkundige kwaliteit."""
    
    def __init__(self):
        # Common linguistic improvements
        self.linguistic_patterns = {
            # Passive to active voice suggestions
            'passive_voice': [
                (r'\bwordt\s+(\w+)', r'(\w+) wordt'),  # Simple passive detection
            ],
            # Redundancy patterns
            'redundancy': [
                (r'\b(\w+)\s+\w*\s+\1\b', 'Word repetition'),  # Word repetition
                (r'\bhet\s+begrip\s+(\w+)', r'\1'),             # "het begrip X" -> "X"
            ],
            # Formality improvements
            'formality': [
                (r'\bje\b', 'men'),     # "je" -> "men"
                (r'\bjij\b', 'men'),    # "jij" -> "men" 
                (r'\bwij\b', 'men'),    # "wij" -> "men"
            ]
        }
    
    def enhance(self, definition: Definition) -> List[EnhancementResult]:
        """Verbeter taalkundige kwaliteit."""
        results = []
        text = definition.definitie
        
        for improvement_type, patterns in self.linguistic_patterns.items():
            enhanced_text = text
            changes_made = 0
            
            for pattern, replacement in patterns:
                if isinstance(replacement, str) and '(' in pattern:
                    # Regex replacement
                    new_text = re.sub(pattern, replacement, enhanced_text, flags=re.IGNORECASE)
                    if new_text != enhanced_text:
                        enhanced_text = new_text
                        changes_made += 1
                elif isinstance(replacement, str):
                    # Simple replacement  
                    new_text = enhanced_text.replace(pattern.replace(r'\b', ''), replacement)
                    if new_text != enhanced_text:
                        enhanced_text = new_text
                        changes_made += 1
            
            if changes_made > 0 and enhanced_text != text:
                results.append(EnhancementResult(
                    enhancement_type=EnhancementType.LINGUISTIC,
                    original_text=text,
                    enhanced_text=enhanced_text,
                    confidence=0.7,
                    explanation=f"Taalkundige verbetering: {improvement_type} ({changes_made} wijzigingen)"
                ))
                text = enhanced_text  # Chain improvements
        
        return results
    
    def get_strategy_name(self) -> str:
        return "linguistic_enhancer"


class DefinitionEnhancer:
    """
    Hoofdklasse voor definitie enhancement die alle strategieën combineert.
    
    Integreert enhancement functionaliteiten van alle drie implementaties:
    - Quality improvement (van services)
    - Context integration (van definitie_generator) 
    - Comprehensive enhancement (van generation)
    """
    
    def __init__(self, config: QualityConfig):
        self.config = config
        self.strategies: List[EnhancementStrategy] = []
        
        # Initialize available enhancement strategies
        self._init_strategies()
        
        logger.info(f"DefinitionEnhancer geïnitialiseerd met {len(self.strategies)} strategieën")
    
    def _init_strategies(self):
        """Initialiseer beschikbare enhancement strategieën."""
        # Altijd beschikbare strategieën
        self.strategies.append(ClarityEnhancer())
        self.strategies.append(ContextIntegrationEnhancer())
        
        if self.config.enable_completeness_enhancement:
            self.strategies.append(CompletenessEnhancer())
        
        if self.config.enable_linguistic_enhancement:
            self.strategies.append(LinguisticEnhancer())
    
    def enhance_definition(self, definition: Definition, 
                          max_enhancements: int = 3) -> Tuple[Definition, List[EnhancementResult]]:
        """
        Pas enhancements toe op een definitie.
        
        Args:
            definition: Te verbeteren definitie
            max_enhancements: Maximum aantal enhancements toe te passen
            
        Returns:
            Tuple van (enhanced_definition, list_of_applied_enhancements)
        """
        if not self.config.enable_enhancement:
            return definition, []
        
        # Collect all possible enhancements
        all_enhancements = []
        for strategy in self.strategies:
            try:
                enhancements = strategy.enhance(definition)
                all_enhancements.extend(enhancements)
            except Exception as e:
                logger.warning(f"Enhancement strategy {strategy.get_strategy_name()} failed: {e}")
        
        # Sort by confidence and apply top enhancements
        all_enhancements.sort(key=lambda x: x.confidence, reverse=True)
        applied_enhancements = []
        current_definition = definition
        
        for enhancement in all_enhancements[:max_enhancements]:
            if enhancement.confidence >= self.config.enhancement_confidence_threshold:
                # Apply enhancement
                enhanced_def = self._apply_enhancement(current_definition, enhancement)
                if enhanced_def != current_definition:
                    enhancement.applied = True
                    applied_enhancements.append(enhancement)
                    current_definition = enhanced_def
                    
                    logger.debug(f"Applied {enhancement.enhancement_type.value} enhancement "
                               f"(confidence: {enhancement.confidence:.2f})")
        
        # Update metadata
        if applied_enhancements:
            enhanced_metadata = current_definition.metadata.copy()
            enhanced_metadata["enhanced"] = True
            enhanced_metadata["enhancement_applied"] = [e.enhancement_type.value for e in applied_enhancements]
            enhanced_metadata["enhancement_confidence"] = [e.confidence for e in applied_enhancements]
            
            current_definition = Definition(
                begrip=current_definition.begrip,
                definitie=current_definition.definitie,
                context=current_definition.context,
                domein=current_definition.domein,
                categorie=current_definition.categorie,
                bron=f"{current_definition.bron} (Enhanced)",
                metadata=enhanced_metadata,
            )
        
        return current_definition, applied_enhancements
    
    def _apply_enhancement(self, definition: Definition, 
                         enhancement: EnhancementResult) -> Definition:
        """Pas een specifiek enhancement toe op een definitie."""
        return Definition(
            begrip=definition.begrip,
            definitie=enhancement.enhanced_text,
            context=definition.context,
            domein=definition.domein,
            categorie=definition.categorie,
            bron=definition.bron,
            metadata=definition.metadata,
        )
    
    def get_available_strategies(self) -> List[str]:
        """Verkrijg lijst van beschikbare enhancement strategieën."""
        return [strategy.get_strategy_name() for strategy in self.strategies]
    
    def evaluate_definition_quality(self, definition: Definition) -> Dict[str, Any]:
        """
        Evalueer de kwaliteit van een definitie zonder enhancements toe te passen.
        
        Args:
            definition: Te evalueren definitie
            
        Returns:
            Dictionary met kwaliteitsmetrics
        """
        quality_scores = {}
        improvement_suggestions = []
        
        for strategy in self.strategies:
            try:
                enhancements = strategy.enhance(definition)
                if enhancements:
                    strategy_name = strategy.get_strategy_name()
                    # Calculate average confidence as quality indicator
                    avg_confidence = sum(e.confidence for e in enhancements) / len(enhancements)
                    quality_scores[strategy_name] = 1.0 - avg_confidence  # Higher confidence = lower quality score
                    
                    # Collect suggestions
                    for enhancement in enhancements:
                        if enhancement.confidence > 0.5:
                            improvement_suggestions.append({
                                "type": enhancement.enhancement_type.value,
                                "explanation": enhancement.explanation,
                                "confidence": enhancement.confidence
                            })
            except Exception as e:
                logger.warning(f"Quality evaluation failed for {strategy.get_strategy_name()}: {e}")
        
        overall_quality = sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0.8
        
        logger.info("Definition quality evaluation completed")
        
        return {
            "overall_quality_score": max(overall_quality, 0.0),
            "strategy_scores": quality_scores,
            "improvement_suggestions": improvement_suggestions,
            "evaluation_timestamp": "completed"
        }