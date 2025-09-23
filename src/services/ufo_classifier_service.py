"""
UFO Classifier Service - Automatische bepaling van OntoUML/UFO categorieën.

Dit module implementeert een geoptimaliseerde classifier voor UFO-categorieën
met focus op performance, onderhoudbaarheid en uitlegbaarheid.

Auteur: AI Assistant
Datum: 2025-09-23
Versie: 1.0.0
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from typing import Dict, List, Optional, Set, Tuple

import logging

logger = logging.getLogger(__name__)


class UFOCategory(Enum):
    """UFO/OntoUML categorie types."""
    KIND = "Kind"
    EVENT = "Event"
    ROLE = "Role"
    PHASE = "Phase"
    RELATOR = "Relator"
    MODE = "Mode"
    QUANTITY = "Quantity"
    QUALITY = "Quality"
    SUBKIND = "Subkind"
    CATEGORY = "Category"
    MIXIN = "Mixin"
    ROLEMIXIN = "RoleMixin"
    PHASEMIXIN = "PhaseMixin"
    ABSTRACT = "Abstract"
    UNKNOWN = "Unknown"


@dataclass
class UFOClassificationResult:
    """Resultaat van UFO classificatie."""
    primary_category: UFOCategory
    confidence: float
    explanation: List[str]
    secondary_tags: List[UFOCategory] = field(default_factory=list)
    matched_patterns: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Converteer naar dictionary voor serialisatie."""
        return {
            'primary_category': self.primary_category.value,
            'confidence': round(self.confidence, 3),
            'explanation': self.explanation,
            'secondary_tags': [tag.value for tag in self.secondary_tags],
            'matched_patterns': self.matched_patterns
        }


class PatternMatcher:
    """Efficiënte pattern matching met pre-compiled patterns en caching."""

    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.compiled_patterns = self._compile_patterns()

    def _initialize_patterns(self) -> Dict[UFOCategory, Dict[str, Set[str]]]:
        """Initialiseer Nederlandse patronen per categorie."""
        return {
            UFOCategory.KIND: {
                'core_nouns': {
                    'persoon', 'mens', 'individu', 'burger',
                    'organisatie', 'bedrijf', 'instelling', 'instantie',
                    'voorwerp', 'object', 'zaak', 'goed', 'artikel',
                    'document', 'dossier', 'akte', 'stuk', 'bescheid'
                },
                'legal_entities': {
                    'rechtspersoon', 'natuurlijk persoon', 'natuurlijke persoon',
                    'vennootschap', 'stichting', 'vereniging', 'coöperatie',
                    'overheidsorgaan', 'bestuursorgaan', 'rechterlijke instantie'
                }
            },
            UFOCategory.EVENT: {
                'process_markers': {
                    'proces', 'procedure', 'handeling', 'verrichting',
                    'gebeurtenis', 'activiteit', 'verloop', 'gang',
                    'uitvoering', 'afhandeling', 'behandeling'
                },
                'temporal_markers': {
                    'tijdens', 'gedurende', 'vanaf', 'tot', 'tussen',
                    'doorlooptijd', 'termijn', 'periode', 'tijdvak',
                    'aanvang', 'einde', 'duur', 'tijdstip'
                },
                'legal_processes': {
                    'zitting', 'verhoor', 'onderzoek', 'hoorzitting',
                    'arrestatie', 'aanhouding', 'vervolging', 'berechting',
                    'dagvaarding', 'betekening', 'tenuitvoerlegging'
                }
            },
            UFOCategory.ROLE: {
                'role_markers': {
                    'als', 'in de hoedanigheid van', 'in hoedanigheid van',
                    'in de rol van', 'fungerend als', 'optredend als',
                    'handelend als', 'in functie van', 'werkzaam als'
                },
                'legal_roles': {
                    'verdachte', 'beklaagde', 'getuige', 'rechter', 'raadsheer',
                    'officier', 'advocaat', 'procureur', 'curator', 'bewindvoerder',
                    'gemachtigde', 'vertegenwoordiger', 'belanghebbende'
                },
                'contextual_roles': {
                    'aanvrager', 'verzoeker', 'indiener', 'melder',
                    'eigenaar', 'houder', 'gebruiker', 'beheerder',
                    'werkgever', 'werknemer', 'opdrachtgever', 'opdrachtnemer'
                }
            },
            UFOCategory.PHASE: {
                'phase_markers': {
                    'fase', 'stadium', 'status', 'toestand', 'staat',
                    'in onderzoek', 'in behandeling', 'afgerond', 'gesloten',
                    'actief', 'inactief', 'voorlopig', 'definitief', 'concept'
                },
                'lifecycle_markers': {
                    'nieuw', 'lopend', 'afgehandeld', 'vervallen',
                    'geldig', 'ongeldig', 'verlopen', 'geschorst',
                    'open', 'gesloten', 'gepubliceerd', 'ingetrokken'
                }
            },
            UFOCategory.RELATOR: {
                'contract_types': {
                    'overeenkomst', 'contract', 'convenant', 'afspraak',
                    'vergunning', 'ontheffing', 'machtiging', 'mandaat',
                    'volmacht', 'lastgeving', 'opdracht', 'concessie'
                },
                'legal_relations': {
                    'huwelijk', 'partnerschap', 'voogdij', 'curatele',
                    'bewind', 'mentorschap', 'gezag', 'vruchtgebruik',
                    'erfpacht', 'hypotheek', 'pandrecht', 'eigendom'
                },
                'formal_bindings': {
                    'verbintenis', 'verplichting', 'aansprakelijkheid',
                    'gebondenheid', 'binding', 'relatie', 'verhouding',
                    'betrekking', 'band', 'connectie', 'koppeling'
                }
            },
            UFOCategory.MODE: {
                'state_markers': {
                    'toestand', 'staat', 'conditie', 'situatie',
                    'gesteldheid', 'hoedanigheid', 'omstandigheid'
                },
                'attributes': {
                    'eigenschap', 'kenmerk', 'attribuut', 'aspect',
                    'gezondheid', 'locatie', 'positie', 'plaats',
                    'kleur', 'vorm', 'grootte', 'omvang'
                }
            },
            UFOCategory.QUANTITY: {
                'units': {
                    'euro', 'eur', 'dollar', 'procent', 'percentage',
                    'kilogram', 'kg', 'gram', 'meter', 'm', 'kilometer',
                    'uur', 'minuut', 'dag', 'maand', 'jaar'
                },
                'measures': {
                    'aantal', 'hoeveelheid', 'bedrag', 'som', 'totaal',
                    'duur', 'lengte', 'breedte', 'hoogte', 'diepte',
                    'volume', 'gewicht', 'massa', 'oppervlakte'
                }
            },
            UFOCategory.QUALITY: {
                'gradations': {
                    'kwaliteit', 'graad', 'niveau', 'mate', 'schaal',
                    'ernst', 'zwaarte', 'intensiteit', 'sterkte'
                },
                'evaluations': {
                    'betrouwbaarheid', 'geloofwaardigheid', 'waarschijnlijkheid',
                    'relevantie', 'belangrijkheid', 'urgentie', 'prioriteit'
                }
            }
        }

    def _compile_patterns(self) -> Dict[UFOCategory, re.Pattern]:
        """Compileer patterns voor snelle matching."""
        compiled = {}
        for category, pattern_groups in self.patterns.items():
            all_terms = []
            for group_terms in pattern_groups.values():
                all_terms.extend(group_terms)

            # Maak regex pattern met word boundaries
            pattern = r'\b(' + '|'.join(re.escape(term) for term in all_terms) + r')\b'
            compiled[category] = re.compile(pattern, re.IGNORECASE)

        return compiled

    @lru_cache(maxsize=1024)
    def find_matches(self, text: str) -> Dict[UFOCategory, List[str]]:
        """Vind alle pattern matches in de tekst."""
        matches = defaultdict(list)

        for category, pattern in self.compiled_patterns.items():
            found = pattern.findall(text.lower())
            if found:
                matches[category] = list(set(found))  # Unieke matches

        return dict(matches)


class UFOClassifierService:
    """
    Service voor automatische UFO categorie classificatie.

    Deze service gebruikt een geoptimaliseerde beslisboom met pattern matching
    voor het classificeren van begrippen volgens het OntoUML/UFO metamodel.
    """

    def __init__(self):
        self.pattern_matcher = PatternMatcher()
        self.decision_weights = self._initialize_weights()

    def _initialize_weights(self) -> Dict[UFOCategory, float]:
        """Initialiseer gewichten voor scoring."""
        return {
            UFOCategory.KIND: 1.0,      # Hoogste prioriteit voor concrete objecten
            UFOCategory.EVENT: 0.95,
            UFOCategory.RELATOR: 0.9,
            UFOCategory.ROLE: 0.85,
            UFOCategory.PHASE: 0.8,
            UFOCategory.MODE: 0.75,
            UFOCategory.QUALITY: 0.7,
            UFOCategory.QUANTITY: 0.7,
            UFOCategory.CATEGORY: 0.6,
            UFOCategory.SUBKIND: 0.6,
            UFOCategory.MIXIN: 0.5,
            UFOCategory.ABSTRACT: 0.4,
            UFOCategory.UNKNOWN: 0.1
        }

    def classify(self,
                 term: str,
                 definition: str,
                 context: Optional[Dict] = None) -> UFOClassificationResult:
        """
        Classificeer een begrip volgens UFO/OntoUML.

        Args:
            term: Het te classificeren begrip
            definition: De definitie van het begrip
            context: Optionele context informatie

        Returns:
            UFOClassificationResult met categorie, confidence en uitleg
        """
        # Combineer term en definitie voor volledige analyse
        full_text = f"{term}. {definition}"

        # Vind pattern matches
        matches = self.pattern_matcher.find_matches(full_text)

        # Bereken scores per categorie
        scores = self._calculate_scores(matches, full_text, context)

        # Bepaal primaire categorie
        primary_category, confidence = self._determine_primary_category(scores)

        # Bepaal secundaire tags
        secondary_tags = self._determine_secondary_tags(primary_category, matches, full_text)

        # Genereer uitleg
        explanation = self._generate_explanation(primary_category, matches, confidence)

        return UFOClassificationResult(
            primary_category=primary_category,
            confidence=confidence,
            explanation=explanation,
            secondary_tags=secondary_tags,
            matched_patterns={cat.value: terms for cat, terms in matches.items()}
        )

    def _calculate_scores(self,
                         matches: Dict[UFOCategory, List[str]],
                         text: str,
                         context: Optional[Dict]) -> Dict[UFOCategory, float]:
        """Bereken scores voor elke categorie."""
        scores = defaultdict(float)

        # Pattern match scores - verhoogde base score voor betere confidence
        for category, matched_terms in matches.items():
            # Verhoogde score per match voor betere confidence values
            base_score = len(matched_terms) * 0.35  # Verhoogd van 0.2 naar 0.35
            weight = self.decision_weights.get(category, 0.5)
            scores[category] = min(base_score * weight, 1.0)

        # Heuristische regels
        heuristic_scores = self._apply_heuristics(text, matches)
        for cat, score in heuristic_scores.items():
            scores[cat] = min(scores[cat] + score, 1.0)

        # Context-based adjustments
        if context:
            scores = self._apply_context_adjustments(scores, context)

        return dict(scores)

    def _apply_heuristics(self,
                         text: str,
                         matches: Dict[UFOCategory, List[str]]) -> Dict[UFOCategory, float]:
        """Pas heuristische regels toe voor betere classificatie."""
        adjustments = defaultdict(float)
        text_lower = text.lower()

        # KIND heuristiek: zelfstandige naamwoorden zonder drager
        if UFOCategory.KIND in matches and not any(
            marker in text_lower for marker in ['van', 'voor', 'bij', 'met betrekking tot']
        ):
            adjustments[UFOCategory.KIND] += 0.3

        # EVENT heuristiek: werkwoorden en tijdsaanduidingen
        if any(marker in text_lower for marker in ['vindt plaats', 'gebeurt', 'wordt uitgevoerd']):
            adjustments[UFOCategory.EVENT] += 0.4

        # ROLE heuristiek: contextuele aanduiding
        if 'in de hoedanigheid van' in text_lower or 'als' in text_lower:
            adjustments[UFOCategory.ROLE] += 0.35

        # RELATOR heuristiek: meerdere partijen
        if any(marker in text_lower for marker in ['tussen', 'partijen', 'overeenkomst tussen']):
            adjustments[UFOCategory.RELATOR] += 0.4

        # MODE/QUALITY heuristiek: eigenschappen
        if 'eigenschap' in text_lower or 'kenmerk' in text_lower:
            if any(term in text_lower for term in ['meetbaar', 'kwantificeer']):
                adjustments[UFOCategory.QUANTITY] += 0.3
            else:
                adjustments[UFOCategory.QUALITY] += 0.25

        return adjustments

    def _apply_context_adjustments(self,
                                  scores: Dict[UFOCategory, float],
                                  context: Dict) -> Dict[UFOCategory, float]:
        """Pas context-gebaseerde aanpassingen toe."""
        adjusted = scores.copy()

        # Voorbeeld: als context aangeeft dat het om een proces gaat
        if context.get('domain') == 'process':
            adjusted[UFOCategory.EVENT] = adjusted.get(UFOCategory.EVENT, 0) + 0.2

        # Voorbeeld: juridische context
        if context.get('domain') == 'legal':
            # Juridische termen zijn vaak RELATOR (contracten) of ROLE (functies)
            adjusted[UFOCategory.RELATOR] = adjusted.get(UFOCategory.RELATOR, 0) + 0.1
            adjusted[UFOCategory.ROLE] = adjusted.get(UFOCategory.ROLE, 0) + 0.1

        return adjusted

    def _determine_primary_category(self,
                                   scores: Dict[UFOCategory, float]) -> Tuple[UFOCategory, float]:
        """Bepaal de primaire categorie op basis van scores."""
        if not scores:
            return UFOCategory.UNKNOWN, 0.1

        # Sorteer op score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        best_category, best_score = sorted_scores[0]

        # Verbeterde confidence berekening
        if len(sorted_scores) > 1:
            second_score = sorted_scores[1][1]
            # Base confidence op de best score met een bonus voor duidelijke verschillen
            confidence = min(best_score + (best_score - second_score) * 0.5, 1.0)
        else:
            # Als er maar één match is, gebruik de score direct met een kleine boost
            confidence = min(best_score * 1.2, 1.0)

        # Minimum confidence threshold - verlaagd voor betere detectie
        if confidence < 0.15:
            return UFOCategory.UNKNOWN, confidence

        return best_category, confidence

    def _determine_secondary_tags(self,
                                 primary: UFOCategory,
                                 matches: Dict[UFOCategory, List[str]],
                                 text: str) -> List[UFOCategory]:
        """Bepaal secundaire tags op basis van de primaire categorie."""
        tags = []
        text_lower = text.lower()

        # Abstractie niveau tags
        if primary == UFOCategory.KIND:
            if 'soort' in text_lower or 'type' in text_lower:
                tags.append(UFOCategory.SUBKIND)
            if 'categorie' in text_lower:
                tags.append(UFOCategory.CATEGORY)

        # Mixin patterns
        if primary == UFOCategory.ROLE and 'verschillende' in text_lower:
            tags.append(UFOCategory.ROLEMIXIN)

        if primary == UFOCategory.PHASE and 'verschillende' in text_lower:
            tags.append(UFOCategory.PHASEMIXIN)

        # Abstract patterns
        if 'abstract' in text_lower or 'algemeen' in text_lower:
            tags.append(UFOCategory.ABSTRACT)

        return tags

    def _generate_explanation(self,
                            category: UFOCategory,
                            matches: Dict[UFOCategory, List[str]],
                            confidence: float) -> List[str]:
        """Genereer een uitleg voor de classificatie."""
        explanations = []

        # Confidence niveau
        if confidence >= 0.8:
            explanations.append(f"Hoge zekerheid ({confidence:.0%})")
        elif confidence >= 0.5:
            explanations.append(f"Redelijke zekerheid ({confidence:.0%})")
        else:
            explanations.append(f"Lage zekerheid ({confidence:.0%})")

        # Gevonden patronen
        if category in matches:
            terms = matches[category][:3]  # Max 3 termen tonen
            explanations.append(f"Gevonden termen: {', '.join(terms)}")

        # Categorie-specifieke uitleg
        category_explanations = {
            UFOCategory.KIND: "Zelfstandig object zonder drager",
            UFOCategory.EVENT: "Tijdsgebonden proces of gebeurtenis",
            UFOCategory.ROLE: "Contextuele rol met drager",
            UFOCategory.PHASE: "Levensfase van een object",
            UFOCategory.RELATOR: "Relatie tussen meerdere entiteiten",
            UFOCategory.MODE: "Eigenschap of toestand met drager",
            UFOCategory.QUANTITY: "Meetbare grootheid",
            UFOCategory.QUALITY: "Kwalitatieve eigenschap",
            UFOCategory.UNKNOWN: "Geen duidelijke categorie bepaald"
        }

        if category in category_explanations:
            explanations.append(category_explanations[category])

        return explanations

    def batch_classify(self,
                       items: List[Tuple[str, str, Optional[Dict]]]) -> List[UFOClassificationResult]:
        """
        Classificeer meerdere begrippen in batch.

        Args:
            items: Lijst van (term, definition, context) tuples

        Returns:
            Lijst van UFOClassificationResult objecten
        """
        results = []

        for term, definition, context in items:
            try:
                result = self.classify(term, definition, context)
                results.append(result)
            except Exception as e:
                logger.error(f"Fout bij classificatie van '{term}': {e}")
                results.append(UFOClassificationResult(
                    primary_category=UFOCategory.UNKNOWN,
                    confidence=0.0,
                    explanation=[f"Classificatie fout: {str(e)}"]
                ))

        return results

    def get_category_examples(self, category: UFOCategory) -> Dict[str, List[str]]:
        """
        Haal voorbeelden op voor een specifieke categorie.

        Args:
            category: De UFO categorie

        Returns:
            Dictionary met pattern groepen en voorbeelden
        """
        if category not in self.pattern_matcher.patterns:
            return {}

        return {
            group: list(terms)[:5]  # Max 5 voorbeelden per groep
            for group, terms in self.pattern_matcher.patterns[category].items()
        }

    def explain_classification(self, result: UFOClassificationResult) -> str:
        """
        Genereer een uitgebreide tekstuele uitleg van de classificatie.

        Args:
            result: Het classificatie resultaat

        Returns:
            Uitgebreide uitleg als string
        """
        lines = [
            f"UFO Categorie: {result.primary_category.value}",
            f"Zekerheid: {result.confidence:.1%}",
            ""
        ]

        if result.explanation:
            lines.append("Reden voor classificatie:")
            for exp in result.explanation:
                lines.append(f"  • {exp}")
            lines.append("")

        if result.matched_patterns:
            lines.append("Gevonden patronen:")
            for cat, terms in result.matched_patterns.items():
                lines.append(f"  {cat}: {', '.join(terms[:3])}")
            lines.append("")

        if result.secondary_tags:
            lines.append("Secundaire categorieën:")
            for tag in result.secondary_tags:
                lines.append(f"  • {tag.value}")

        return "\n".join(lines)


# Singleton instance voor gebruik in de applicatie
_classifier_instance: Optional[UFOClassifierService] = None

def get_ufo_classifier() -> UFOClassifierService:
    """Get singleton instance van de UFO classifier."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = UFOClassifierService()
    return _classifier_instance