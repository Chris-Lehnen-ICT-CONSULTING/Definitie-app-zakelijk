"""
Context Fusion - Combineert web lookup en document context tot unified context.
Resolveert conflicten en creëert coherente context voor definitie generatie.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class FusionResult:
    """Resultaat van context fusion proces."""
    unified_context: str
    confidence_score: float
    strategy: str
    conflicts_resolved: int
    quality_assessment: str
    web_sources: List[str]
    primary_sources: List[str]
    supporting_sources: List[str]
    fusion_metadata: Dict[str, Any]

class ContextFusion:
    """
    Context Fusion Engine - Combineert web en document context intelligent.
    
    Functionaliteiten:
    - Conflict detection en resolution
    - Context prioritization
    - Coherentie validatie
    - Quality assessment
    - Source attribution
    """
    
    def __init__(self):
        """Initialiseer context fusion engine."""
        self.fusion_strategies = self._initialize_fusion_strategies()
        self.quality_metrics = self._initialize_quality_metrics()
        
    def fuse_contexts(
        self,
        web_context: Dict[str, Any],
        document_context: Dict[str, Any],
        begrip: str
    ) -> Dict[str, Any]:
        """
        Fuseer web en document context tot unified context.
        
        Args:
            web_context: Context uit web lookup
            document_context: Context uit document processing
            begrip: Het begrip waarvoor context gefuseerd wordt
            
        Returns:
            Dictionary met fusion resultaat
        """
        try:
            logger.info(f"Start context fusion voor '{begrip}'")
            
            # Stap 1: Analyseer beschikbare context
            context_analysis = self._analyze_available_context(web_context, document_context)
            
            # Stap 2: Detecteer potentiële conflicten
            conflicts = self._detect_conflicts(web_context, document_context, begrip)
            
            # Stap 3: Selecteer fusion strategy
            strategy_name = self._select_fusion_strategy(context_analysis, conflicts)
            
            # Stap 4: Voer fusion uit
            fusion_result = self._execute_fusion(
                web_context=web_context,
                document_context=document_context,
                begrip=begrip,
                strategy=strategy_name,
                conflicts=conflicts
            )
            
            # Stap 5: Valideer en assess quality
            quality_assessment = self._assess_fusion_quality(fusion_result, context_analysis)
            
            # Stap 6: Creëer final result
            result = {
                'unified_context': fusion_result.unified_context,
                'confidence_score': fusion_result.confidence_score,
                'strategy': strategy_name,
                'conflicts_resolved': len(conflicts),
                'quality_assessment': quality_assessment,
                'web_sources': fusion_result.web_sources,
                'primary_sources': fusion_result.primary_sources,
                'supporting_sources': fusion_result.supporting_sources
            }
            
            logger.info(f"Context fusion voltooid voor '{begrip}' (strategy: {strategy_name}, quality: {quality_assessment})")
            return result
            
        except Exception as e:
            logger.error(f"Fout bij context fusion voor '{begrip}': {e}")
            return self._create_fallback_fusion(web_context, document_context, begrip)
    
    def _analyze_available_context(
        self, 
        web_context: Dict[str, Any], 
        document_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyseer beschikbare context voor fusion planning."""
        
        # Web context analyse
        web_sources = [k for k, v in web_context.items() 
                      if isinstance(v, dict) and 'tekst' in v and k != '_enhancement_metadata']
        web_quality = self._assess_web_context_quality(web_context)
        
        # Document context analyse
        doc_count = document_context.get('document_count', 0)
        doc_keywords = len(document_context.get('aggregated_keywords', []))
        doc_concepts = len(document_context.get('aggregated_concepts', []))
        doc_quality = self._assess_document_context_quality(document_context)
        
        return {
            'web_sources_available': len(web_sources),
            'web_sources': web_sources,
            'web_quality': web_quality,
            'document_count': doc_count,
            'document_keywords': doc_keywords,
            'document_concepts': doc_concepts,
            'document_quality': doc_quality,
            'has_strong_web': web_quality in ['high', 'medium'],
            'has_strong_docs': doc_quality in ['high', 'medium'],
            'balance_ratio': self._calculate_balance_ratio(web_quality, doc_quality)
        }
    
    def _assess_web_context_quality(self, web_context: Any) -> str:
        """Beoordeel kwaliteit van web context."""
        if not web_context:
            return 'none'
        
        # Handle different web_context formats
        if isinstance(web_context, dict):
            source_count = len([k for k, v in web_context.items() 
                               if isinstance(v, dict) and 'tekst' in v])
        elif isinstance(web_context, list):
            source_count = len([item for item in web_context 
                               if isinstance(item, dict) and 'tekst' in item])
        else:
            return 'none'
        
        # Check content richness
        total_content = 0
        authoritative_sources = 0
        
        for source_name, source_data in web_context.items():
            if isinstance(source_data, dict) and 'tekst' in source_data:
                content_length = len(source_data['tekst'])
                total_content += content_length
                
                # Check voor authoritative sources
                if source_name in ['wetten_nl', 'overheid_nl', 'strafrechtketen_nl']:
                    authoritative_sources += 1
        
        if source_count >= 3 and total_content > 1000 and authoritative_sources > 0:
            return 'high'
        elif source_count >= 2 and total_content > 500:
            return 'medium'
        elif source_count >= 1 and total_content > 100:
            return 'low'
        else:
            return 'minimal'
    
    def _assess_document_context_quality(self, document_context: Dict[str, Any]) -> str:
        """Beoordeel kwaliteit van document context."""
        doc_count = document_context.get('document_count', 0)
        if doc_count == 0:
            return 'none'
            
        total_length = document_context.get('total_text_length', 0)
        keyword_count = len(document_context.get('aggregated_keywords', []))
        concept_count = len(document_context.get('aggregated_concepts', []))
        legal_ref_count = len(document_context.get('aggregated_legal_refs', []))
        
        if (doc_count >= 2 and total_length > 5000 and 
            keyword_count > 15 and concept_count > 5):
            return 'high'
        elif (doc_count >= 1 and total_length > 1000 and 
              keyword_count > 8):
            return 'medium'
        elif doc_count >= 1 and total_length > 200:
            return 'low'
        else:
            return 'minimal'
    
    def _calculate_balance_ratio(self, web_quality: str, doc_quality: str) -> float:
        """Bereken balance ratio tussen web en document context."""
        quality_scores = {'none': 0, 'minimal': 1, 'low': 2, 'medium': 3, 'high': 4}
        
        web_score = quality_scores.get(web_quality, 0)
        doc_score = quality_scores.get(doc_quality, 0)
        
        if web_score + doc_score == 0:
            return 0.5
        
        return web_score / (web_score + doc_score)
    
    def _detect_conflicts(
        self, 
        web_context: Dict[str, Any], 
        document_context: Dict[str, Any], 
        begrip: str
    ) -> List[Dict[str, Any]]:
        """Detecteer potentiële conflicten tussen web en document context."""
        conflicts = []
        
        # Extract key terms from both contexts
        web_terms = self._extract_key_terms_from_web(web_context)
        doc_terms = document_context.get('aggregated_keywords', [])
        
        # Check voor contradictory terms
        contradictions = self._find_contradictory_terms(web_terms, doc_terms)
        if contradictions:
            conflicts.append({
                'type': 'terminology_conflict',
                'severity': 'medium',
                'description': f"Contradictory terms found: {contradictions}",
                'web_terms': contradictions['web_terms'],
                'doc_terms': contradictions['doc_terms']
            })
        
        # Check voor focus divergence
        web_focus = self._determine_context_focus(web_terms)
        doc_focus = self._determine_document_focus(document_context)
        
        if web_focus != doc_focus and web_focus != 'general' and doc_focus != 'general':
            conflicts.append({
                'type': 'focus_divergence',
                'severity': 'low',
                'description': f"Different focus areas: web={web_focus}, docs={doc_focus}",
                'web_focus': web_focus,
                'doc_focus': doc_focus
            })
        
        return conflicts
    
    def _extract_key_terms_from_web(self, web_context: Dict[str, Any]) -> List[str]:
        """Extraheer key terms uit web context."""
        terms = []
        
        for source_name, source_data in web_context.items():
            if isinstance(source_data, dict) and 'tekst' in source_data:
                text = source_data['tekst'].lower()
                
                # Simple term extraction (kan uitgebreid worden)
                words = re.findall(r'\b\w{4,}\b', text)
                terms.extend(words[:10])  # Top 10 per source
        
        return list(set(terms))
    
    def _find_contradictory_terms(self, web_terms: List[str], doc_terms: List[str]) -> Optional[Dict[str, List[str]]]:
        """Vind contradictoire termen tussen web en document context."""
        # Eenvoudige conflict detectie - kan uitgebreid worden
        conflicting_patterns = [
            (['niet', 'geen', 'verboden'], ['wel', 'toegestaan', 'verplicht']),
            (['oud', 'voormalig', 'vervallen'], ['nieuw', 'huidig', 'geldig']),
            (['optioneel', 'facultatief'], ['verplicht', 'vereist'])
        ]
        
        for negative_pattern, positive_pattern in conflicting_patterns:
            web_has_negative = any(term in web_terms for term in negative_pattern)
            doc_has_positive = any(term in doc_terms for term in positive_pattern)
            
            if web_has_negative and doc_has_positive:
                return {
                    'web_terms': [term for term in web_terms if term in negative_pattern],
                    'doc_terms': [term for term in doc_terms if term in positive_pattern]
                }
        
        return None
    
    def _determine_context_focus(self, terms: List[str]) -> str:
        """Bepaal focus van context op basis van terms."""
        focus_patterns = {
            'legal': ['wet', 'artikel', 'juridisch', 'recht', 'regelgeving'],
            'technical': ['systeem', 'technisch', 'digitaal', 'elektronisch'],
            'process': ['proces', 'procedure', 'stappen', 'workflow'],
            'security': ['beveiliging', 'veiligheid', 'bescherming']
        }
        
        scores = {}
        for focus, pattern in focus_patterns.items():
            scores[focus] = sum(1 for term in terms if any(p in term for p in pattern))
        
        return max(scores, key=scores.get) if max(scores.values()) > 0 else 'general'
    
    def _determine_document_focus(self, document_context: Dict[str, Any]) -> str:
        """Bepaal focus van document context."""
        keywords = document_context.get('aggregated_keywords', [])
        return self._determine_context_focus(keywords)
    
    def _select_fusion_strategy(self, context_analysis: Dict[str, Any], conflicts: List[Dict[str, Any]]) -> str:
        """Selecteer optimale fusion strategy."""
        
        has_strong_web = context_analysis['has_strong_web']
        has_strong_docs = context_analysis['has_strong_docs']
        conflict_count = len(conflicts)
        balance_ratio = context_analysis['balance_ratio']
        
        if has_strong_web and has_strong_docs:
            if conflict_count > 0:
                return 'balanced_with_resolution'
            else:
                return 'balanced_merge'
        elif has_strong_web and not has_strong_docs:
            return 'web_primary_with_doc_support'
        elif not has_strong_web and has_strong_docs:
            return 'doc_primary_with_web_support'
        elif balance_ratio > 0.7:
            return 'web_focused'
        elif balance_ratio < 0.3:
            return 'document_focused'
        else:
            return 'simple_concatenation'
    
    def _execute_fusion(
        self,
        web_context: Dict[str, Any],
        document_context: Dict[str, Any],
        begrip: str,
        strategy: str,
        conflicts: List[Dict[str, Any]]
    ) -> FusionResult:
        """Voer de daadwerkelijke fusion uit op basis van strategy."""
        
        if strategy == 'balanced_merge':
            return self._balanced_merge_fusion(web_context, document_context, begrip)
        elif strategy == 'balanced_with_resolution':
            return self._balanced_with_resolution_fusion(web_context, document_context, begrip, conflicts)
        elif strategy == 'web_primary_with_doc_support':
            return self._web_primary_fusion(web_context, document_context, begrip)
        elif strategy == 'doc_primary_with_web_support':
            return self._doc_primary_fusion(web_context, document_context, begrip)
        elif strategy == 'web_focused':
            return self._web_focused_fusion(web_context, document_context, begrip)
        elif strategy == 'document_focused':
            return self._document_focused_fusion(web_context, document_context, begrip)
        else:  # simple_concatenation
            return self._simple_concatenation_fusion(web_context, document_context, begrip)
    
    def _balanced_merge_fusion(
        self, 
        web_context: Dict[str, Any], 
        document_context: Dict[str, Any], 
        begrip: str
    ) -> FusionResult:
        """Gebalanceerde merge van web en document context."""
        
        sections = []
        
        # Document context eerst (meer specifiek)
        if document_context.get('document_count', 0) > 0:
            sections.append("=== DOCUMENT CONTEXT ===")
            
            keywords = document_context.get('aggregated_keywords', [])
            if keywords:
                sections.append(f"Gerelateerde termen: {', '.join(keywords[:10])}")
            
            concepts = document_context.get('aggregated_concepts', [])
            if concepts:
                sections.append(f"Geïdentificeerde concepten: {', '.join(concepts[:5])}")
            
            legal_refs = document_context.get('aggregated_legal_refs', [])
            if legal_refs:
                sections.append(f"Juridische verwijzingen: {', '.join(legal_refs[:5])}")
        
        # Web context
        sections.append("\n=== WEB BRONNEN ===")
        web_sources = []
        
        for source_name, source_data in web_context.items():
            if isinstance(source_data, dict) and 'tekst' in source_data:
                web_sources.append(source_name)
                content = source_data['tekst'][:300] + "..." if len(source_data['tekst']) > 300 else source_data['tekst']
                sections.append(f"\n[{source_name.upper()}]: {content}")
        
        unified_context = "\n".join(sections)
        
        return FusionResult(
            unified_context=unified_context,
            confidence_score=0.8,
            strategy='balanced_merge',
            conflicts_resolved=0,
            quality_assessment='good',
            web_sources=web_sources,
            primary_sources=web_sources[:2] + [f"documents({document_context.get('document_count', 0)})"],
            supporting_sources=web_sources[2:],
            fusion_metadata={'sections_created': len(sections)}
        )
    
    def _balanced_with_resolution_fusion(
        self, 
        web_context: Dict[str, Any], 
        document_context: Dict[str, Any], 
        begrip: str, 
        conflicts: List[Dict[str, Any]]
    ) -> FusionResult:
        """Gebalanceerde fusion met conflict resolution."""
        
        # Start met balanced merge
        base_result = self._balanced_merge_fusion(web_context, document_context, begrip)
        
        # Voeg conflict resolution toe
        if conflicts:
            resolution_section = "\n=== CONFLICT RESOLUTION ==="
            for conflict in conflicts:
                resolution_section += f"\n⚠️ {conflict['description']}"
                if conflict['type'] == 'terminology_conflict':
                    resolution_section += " (Documenten krijgen prioriteit voor specifieke termen)"
                elif conflict['type'] == 'focus_divergence':
                    resolution_section += " (Beide perspectieven worden gecombineerd)"
            
            base_result.unified_context += resolution_section
        
        base_result.conflicts_resolved = len(conflicts)
        base_result.confidence_score = max(0.7, base_result.confidence_score - 0.1 * len(conflicts))
        
        return base_result
    
    def _web_primary_fusion(
        self, 
        web_context: Dict[str, Any], 
        document_context: Dict[str, Any], 
        begrip: str
    ) -> FusionResult:
        """Web-primary fusion met document support."""
        
        sections = ["=== PRIMAIRE CONTEXT (WEB BRONNEN) ==="]
        web_sources = []
        
        for source_name, source_data in web_context.items():
            if isinstance(source_data, dict) and 'tekst' in source_data:
                web_sources.append(source_name)
                content = source_data['tekst'][:400] + "..." if len(source_data['tekst']) > 400 else source_data['tekst']
                sections.append(f"\n[{source_name.upper()}]: {content}")
        
        # Document context als aanvulling
        if document_context.get('document_count', 0) > 0:
            sections.append("\n=== AANVULLENDE CONTEXT (DOCUMENTEN) ===")
            keywords = document_context.get('aggregated_keywords', [])[:8]
            if keywords:
                sections.append(f"Aanvullende termen: {', '.join(keywords)}")
        
        return FusionResult(
            unified_context="\n".join(sections),
            confidence_score=0.75,
            strategy='web_primary',
            conflicts_resolved=0,
            quality_assessment='good',
            web_sources=web_sources,
            primary_sources=web_sources[:3],
            supporting_sources=[f"documents({document_context.get('document_count', 0)})"],
            fusion_metadata={'web_primary': True}
        )
    
    def _doc_primary_fusion(
        self, 
        web_context: Dict[str, Any], 
        document_context: Dict[str, Any], 
        begrip: str
    ) -> FusionResult:
        """Document-primary fusion met web support."""
        
        sections = ["=== PRIMAIRE CONTEXT (DOCUMENTEN) ==="]
        
        if document_context.get('document_count', 0) > 0:
            keywords = document_context.get('aggregated_keywords', [])
            concepts = document_context.get('aggregated_concepts', [])
            legal_refs = document_context.get('aggregated_legal_refs', [])
            
            if keywords:
                sections.append(f"Kernbegrippen: {', '.join(keywords[:12])}")
            if concepts:
                sections.append(f"Geïdentificeerde concepten: {', '.join(concepts[:8])}")
            if legal_refs:
                sections.append(f"Juridische kaders: {', '.join(legal_refs[:6])}")
        
        # Web context als validatie
        sections.append("\n=== VALIDATIE CONTEXT (WEB BRONNEN) ===")
        web_sources = []
        
        for source_name, source_data in web_context.items():
            if isinstance(source_data, dict) and 'tekst' in source_data:
                web_sources.append(source_name)
                content = source_data['tekst'][:200] + "..." if len(source_data['tekst']) > 200 else source_data['tekst']
                sections.append(f"\n[{source_name}]: {content}")
        
        return FusionResult(
            unified_context="\n".join(sections),
            confidence_score=0.85,
            strategy='document_primary',
            conflicts_resolved=0,
            quality_assessment='excellent',
            web_sources=web_sources,
            primary_sources=[f"documents({document_context.get('document_count', 0)})"],
            supporting_sources=web_sources,
            fusion_metadata={'document_primary': True}
        )
    
    def _web_focused_fusion(
        self, 
        web_context: Dict[str, Any], 
        document_context: Dict[str, Any], 
        begrip: str
    ) -> FusionResult:
        """Web-focused fusion."""
        sections = []
        web_sources = []
        
        for source_name, source_data in web_context.items():
            if isinstance(source_data, dict) and 'tekst' in source_data:
                web_sources.append(source_name)
                sections.append(f"[{source_name.upper()}]: {source_data['tekst']}")
        
        return FusionResult(
            unified_context="\n\n".join(sections),
            confidence_score=0.65,
            strategy='web_focused',
            conflicts_resolved=0,
            quality_assessment='moderate',
            web_sources=web_sources,
            primary_sources=web_sources,
            supporting_sources=[],
            fusion_metadata={'web_only': True}
        )
    
    def _document_focused_fusion(
        self, 
        web_context: Dict[str, Any], 
        document_context: Dict[str, Any], 
        begrip: str
    ) -> FusionResult:
        """Document-focused fusion."""
        sections = ["=== DOCUMENT CONTEXT ==="]
        
        if document_context.get('document_count', 0) > 0:
            keywords = document_context.get('aggregated_keywords', [])
            concepts = document_context.get('aggregated_concepts', [])
            
            if keywords:
                sections.append(f"Gerelateerde begrippen: {', '.join(keywords)}")
            if concepts:
                sections.append(f"Concepten: {', '.join(concepts)}")
        
        return FusionResult(
            unified_context="\n".join(sections),
            confidence_score=0.7,
            strategy='document_focused',
            conflicts_resolved=0,
            quality_assessment='good',
            web_sources=[],
            primary_sources=[f"documents({document_context.get('document_count', 0)})"],
            supporting_sources=[],
            fusion_metadata={'document_only': True}
        )
    
    def _simple_concatenation_fusion(
        self, 
        web_context: Dict[str, Any], 
        document_context: Dict[str, Any], 
        begrip: str
    ) -> FusionResult:
        """Eenvoudige concatenatie als fallback."""
        sections = []
        web_sources = []
        
        # Web content
        for source_name, source_data in web_context.items():
            if isinstance(source_data, dict) and 'tekst' in source_data:
                web_sources.append(source_name)
                sections.append(f"{source_name}: {source_data['tekst'][:200]}...")
        
        # Document content
        if document_context.get('document_count', 0) > 0:
            keywords = document_context.get('aggregated_keywords', [])[:10]
            if keywords:
                sections.append(f"Document termen: {', '.join(keywords)}")
        
        return FusionResult(
            unified_context="\n\n".join(sections),
            confidence_score=0.5,
            strategy='simple_concatenation',
            conflicts_resolved=0,
            quality_assessment='basic',
            web_sources=web_sources,
            primary_sources=web_sources[:2],
            supporting_sources=web_sources[2:],
            fusion_metadata={'simple_merge': True}
        )
    
    def _assess_fusion_quality(self, fusion_result: FusionResult, context_analysis: Dict[str, Any]) -> str:
        """Beoordeel kwaliteit van fusion resultaat."""
        
        score = 0
        
        # Content richness
        content_length = len(fusion_result.unified_context)
        if content_length > 1000:
            score += 3
        elif content_length > 500:
            score += 2
        elif content_length > 200:
            score += 1
        
        # Source diversity
        total_sources = len(fusion_result.web_sources) + len(fusion_result.primary_sources)
        if total_sources >= 4:
            score += 2
        elif total_sources >= 2:
            score += 1
        
        # Strategy appropriateness
        if fusion_result.strategy in ['balanced_merge', 'document_primary']:
            score += 2
        elif fusion_result.strategy in ['web_primary', 'balanced_with_resolution']:
            score += 1
        
        # Confidence score
        if fusion_result.confidence_score > 0.8:
            score += 2
        elif fusion_result.confidence_score > 0.6:
            score += 1
        
        # Quality mapping
        if score >= 8:
            return 'excellent'
        elif score >= 6:
            return 'good'
        elif score >= 4:
            return 'moderate'
        elif score >= 2:
            return 'basic'
        else:
            return 'minimal'
    
    def _create_fallback_fusion(
        self, 
        web_context: Dict[str, Any], 
        document_context: Dict[str, Any], 
        begrip: str
    ) -> Dict[str, Any]:
        """Creëer fallback fusion bij errors."""
        
        fallback_content = f"Basis context voor '{begrip}'."
        
        if web_context:
            fallback_content += " Web bronnen beschikbaar."
        if document_context.get('document_count', 0) > 0:
            fallback_content += f" {document_context['document_count']} document(en) beschikbaar."
        
        return {
            'unified_context': fallback_content,
            'confidence_score': 0.3,
            'strategy': 'fallback',
            'conflicts_resolved': 0,
            'quality_assessment': 'minimal',
            'web_sources': [],
            'primary_sources': [],
            'supporting_sources': []
        }
    
    def _initialize_fusion_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialiseer fusion strategies."""
        return {
            'balanced_merge': {
                'description': 'Gebalanceerde merge van web en document context',
                'confidence_base': 0.8,
                'quality_target': 'good'
            },
            'balanced_with_resolution': {
                'description': 'Gebalanceerde merge met conflict resolution',
                'confidence_base': 0.75,
                'quality_target': 'good'
            },
            'web_primary_with_doc_support': {
                'description': 'Web primair met document ondersteuning',
                'confidence_base': 0.7,
                'quality_target': 'moderate'
            },
            'doc_primary_with_web_support': {
                'description': 'Document primair met web validatie',
                'confidence_base': 0.85,
                'quality_target': 'excellent'
            }
        }
    
    def _initialize_quality_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Initialiseer quality metrics."""
        return {
            'content_richness': {'weight': 0.3, 'thresholds': [200, 500, 1000]},
            'source_diversity': {'weight': 0.25, 'thresholds': [1, 2, 4]},
            'coherence': {'weight': 0.2, 'thresholds': [0.5, 0.7, 0.9]},
            'relevance': {'weight': 0.25, 'thresholds': [0.6, 0.8, 0.95]}
        }