"""
Smart Source Selector - Intelligente selectie van web bronnen op basis van document context.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SourceStrategy:
    """Strategy voor web source selectie."""

    strategy_name: str
    priority_sources: list[str]
    excluded_sources: list[str]
    boost_keywords: list[str]
    confidence_modifier: float
    reasoning: str


class SmartSourceSelector:
    """
    Intelligente selector voor web bronnen op basis van document context.

    Analyseert document content om te bepalen welke web bronnen het meest relevant zijn
    en welke zoekstrategieën het beste zullen werken.
    """

    def __init__(self):
        """Initialiseer smart source selector."""
        self.source_profiles = self._initialize_source_profiles()
        self.context_patterns = self._initialize_context_patterns()

    def select_optimal_sources(
        self,
        begrip: str,
        organisatorische_context: str | None = None,
        juridische_context: str | None = None,
        document_context: dict[str, Any] | None = None,
    ) -> SourceStrategy:
        """
        Selecteer optimale web bronnen op basis van alle beschikbare context.

        Args:
            begrip: Het begrip waarvoor bronnen geselecteerd worden
            organisatorische_context: Organisatorische context
            juridische_context: Juridische context
            document_context: Context uit geüploade documenten

        Returns:
            SourceStrategy met optimale bron selectie
        """
        try:
            logger.info(f"Selecteer optimale bronnen voor '{begrip}'")

            # Analyseer document context voor hints
            doc_analysis = self._analyze_document_context(document_context)

            # Analyseer begrip karakteristieken
            term_analysis = self._analyze_term_characteristics(begrip)

            # Analyseer juridische en organisatorische context
            context_analysis = self._analyze_formal_context(
                organisatorische_context, juridische_context
            )

            # Combineer analyses tot source strategy
            strategy = self._create_source_strategy(
                begrip=begrip,
                doc_analysis=doc_analysis,
                term_analysis=term_analysis,
                context_analysis=context_analysis,
            )

            logger.info(
                f"Source strategy '{strategy.strategy_name}' geselecteerd voor '{begrip}'"
            )
            return strategy

        except Exception as e:
            logger.error(f"Fout bij source selectie voor '{begrip}': {e}")
            return self._create_default_strategy(begrip)

    def _analyze_document_context(
        self, document_context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Analyseer document context voor source selection hints."""
        if not document_context or document_context.get("document_count", 0) == 0:
            return {
                "has_documents": False,
                "document_type": "none",
                "legal_complexity": "unknown",
                "topic_focus": "general",
                "keyword_themes": [],
                "recommended_sources": [],
            }

        keywords = document_context.get("aggregated_keywords", [])
        concepts = document_context.get("aggregated_concepts", [])
        legal_refs = document_context.get("aggregated_legal_refs", [])

        # Bepaal document type op basis van content
        doc_type = self._classify_document_type(keywords, concepts, legal_refs)

        # Bepaal juridische complexiteit
        legal_complexity = self._assess_legal_complexity(legal_refs, keywords)

        # Identificeer topic focus
        topic_focus = self._identify_topic_focus(keywords, concepts)

        # Bepaal keyword themes
        keyword_themes = self._extract_keyword_themes(keywords)

        # Recommandeer bronnen op basis van analyse
        recommended_sources = self._recommend_sources_for_content(
            doc_type, legal_complexity, topic_focus, keyword_themes
        )

        return {
            "has_documents": True,
            "document_type": doc_type,
            "legal_complexity": legal_complexity,
            "topic_focus": topic_focus,
            "keyword_themes": keyword_themes,
            "recommended_sources": recommended_sources,
            "keyword_count": len(keywords),
            "concept_count": len(concepts),
            "legal_ref_count": len(legal_refs),
        }

    def _classify_document_type(
        self, keywords: list[str], concepts: list[str], legal_refs: list[str]
    ) -> str:
        """Classificeer type document op basis van content."""
        # Legal document indicators
        legal_indicators = [
            "wet",
            "artikel",
            "wetgeving",
            "juridisch",
            "recht",
            "besluit",
            "verordening",
        ]
        legal_score = sum(
            1
            for keyword in keywords
            if any(ind in keyword.lower() for ind in legal_indicators)
        )

        # Policy document indicators
        policy_indicators = [
            "beleid",
            "procedure",
            "proces",
            "richtlijn",
            "protocol",
            "handboek",
        ]
        policy_score = sum(
            1
            for keyword in keywords
            if any(ind in keyword.lower() for ind in policy_indicators)
        )

        # Technical document indicators
        tech_indicators = [
            "systeem",
            "technisch",
            "implementatie",
            "architectuur",
            "specificatie",
        ]
        tech_score = sum(
            1
            for keyword in keywords
            if any(ind in keyword.lower() for ind in tech_indicators)
        )

        # Definitional document indicators
        def_indicators = ["definitie", "betekenis", "omschrijving", "begrip", "concept"]
        def_score = sum(
            1
            for keyword in keywords
            if any(ind in keyword.lower() for ind in def_indicators)
        )

        if legal_score > 0 or len(legal_refs) > 0:
            return "legal"
        if policy_score > tech_score and policy_score > def_score:
            return "policy"
        if tech_score > def_score:
            return "technical"
        if def_score > 0:
            return "definitional"
        return "general"

    def _assess_legal_complexity(
        self, legal_refs: list[str], keywords: list[str]
    ) -> str:
        """Beoordeel juridische complexiteit van content."""
        if len(legal_refs) >= 5:
            return "high"
        if len(legal_refs) >= 2:
            return "medium"
        if len(legal_refs) >= 1 or any(
            "juridisch" in kw.lower() or "wet" in kw.lower() for kw in keywords
        ):
            return "low"
        return "none"

    def _identify_topic_focus(self, keywords: list[str], concepts: list[str]) -> str:
        """Identificeer hoofdonderwerp focus."""
        # Strafrecht focus
        strafrecht_terms = [
            "straf",
            "politie",
            "openbaar",
            "ministerie",
            "gevangenis",
            "reclassering",
        ]
        strafrecht_score = sum(
            1 for term in strafrecht_terms if any(term in kw.lower() for kw in keywords)
        )

        # Identiteit focus
        identiteit_terms = [
            "identiteit",
            "authenticatie",
            "verificatie",
            "identiteitsbewijs",
            "identificatie",
        ]
        identiteit_score = sum(
            1 for term in identiteit_terms if any(term in kw.lower() for kw in keywords)
        )

        # Administratief focus
        admin_terms = ["administratie", "registratie", "beheer", "systeem", "gegevens"]
        admin_score = sum(
            1 for term in admin_terms if any(term in kw.lower() for kw in keywords)
        )

        if identiteit_score > max(strafrecht_score, admin_score):
            return "identity"
        if strafrecht_score > admin_score:
            return "criminal_law"
        if admin_score > 0:
            return "administrative"
        return "general"

    def _extract_keyword_themes(self, keywords: list[str]) -> list[str]:
        """Extraheer thematische groepen uit keywords."""
        themes = []

        # Process themes
        if any("proces" in kw.lower() or "procedure" in kw.lower() for kw in keywords):
            themes.append("process")

        # Technology themes
        if any("systeem" in kw.lower() or "digitaal" in kw.lower() for kw in keywords):
            themes.append("technology")

        # Legal themes
        if any("wet" in kw.lower() or "juridisch" in kw.lower() for kw in keywords):
            themes.append("legal")

        # Security themes
        if any(
            "beveiliging" in kw.lower() or "veiligheid" in kw.lower() for kw in keywords
        ):
            themes.append("security")

        return themes

    def _recommend_sources_for_content(
        self, doc_type: str, legal_complexity: str, topic_focus: str, themes: list[str]
    ) -> list[str]:
        """Recommandeer bronnen op basis van content analyse."""
        recommended = []

        # Altijd nuttig
        recommended.extend(["wikipedia", "wiktionary"])

        # Legal content - prioriteer juridische bronnen
        if doc_type == "legal" or legal_complexity in ["medium", "high"]:
            recommended.extend(["wetten_nl", "overheid_nl"])

        # Criminal law focus
        if topic_focus == "criminal_law":
            recommended.extend(["strafrechtketen_nl", "kamerstukken_nl"])

        # Identity focus
        if topic_focus == "identity":
            recommended.extend(["overheid_nl", "wetten_nl"])

        # EU/International content
        if "legal" in themes and any(
            term in str(themes) for term in ["european", "international"]
        ):
            recommended.append("iate")

        return list(set(recommended))  # Remove duplicates

    def _analyze_term_characteristics(self, begrip: str) -> dict[str, Any]:
        """Analyseer karakteristieken van de term zelf."""
        term_lower = begrip.lower()

        # Bepaal term type
        if any(suffix in term_lower for suffix in ["atie", "eren", "ing"]):
            term_type = "process"
        elif any(suffix in term_lower for suffix in ["bewijs", "middel", "document"]):
            term_type = "object"
        elif any(word in term_lower for word in ["wet", "artikel", "regel"]):
            term_type = "legal_concept"
        else:
            term_type = "general"

        # Bepaal complexiteit op basis van lengte en samenstelling
        word_count = len(begrip.split())
        if word_count >= 3:
            complexity = "high"
        elif word_count == 2:
            complexity = "medium"
        else:
            complexity = "low"

        return {
            "term_type": term_type,
            "complexity": complexity,
            "word_count": word_count,
            "length": len(begrip),
        }

    def _analyze_formal_context(
        self, organisatorische_context: str | None, juridische_context: str | None
    ) -> dict[str, Any]:
        """Analyseer formele context parameters."""
        org_analysis = {}
        if organisatorische_context:
            org_lower = organisatorische_context.lower()
            if any(org in org_lower for org in ["om", "openbaar", "ministerie"]):
                org_analysis["domain"] = "prosecution"
            elif any(org in org_lower for org in ["politie", "kmar"]):
                org_analysis["domain"] = "law_enforcement"
            elif any(org in org_lower for org in ["dji", "gevangenis", "reclassering"]):
                org_analysis["domain"] = "corrections"
            else:
                org_analysis["domain"] = "general"

        jur_analysis = {}
        if juridische_context:
            jur_lower = juridische_context.lower()
            if "strafrecht" in jur_lower:
                jur_analysis["law_area"] = "criminal"
            elif "bestuursrecht" in jur_lower:
                jur_analysis["law_area"] = "administrative"
            elif "europees" in jur_lower:
                jur_analysis["law_area"] = "european"
            else:
                jur_analysis["law_area"] = "general"

        return {"organizational": org_analysis, "juridical": jur_analysis}

    def _create_source_strategy(
        self,
        begrip: str,
        doc_analysis: dict[str, Any],
        term_analysis: dict[str, Any],
        context_analysis: dict[str, Any],
    ) -> SourceStrategy:
        """Creëer source strategy op basis van alle analyses."""

        # Start met basis bronnen
        priority_sources = ["wikipedia", "wiktionary"]
        excluded_sources = []
        boost_keywords = []
        confidence_modifier = 1.0

        # Document-driven prioritization
        if doc_analysis["has_documents"]:
            priority_sources.extend(doc_analysis["recommended_sources"])
            boost_keywords.extend(doc_analysis["keyword_themes"])
            confidence_modifier += 0.2

            # Special handling voor legal content
            if doc_analysis["legal_complexity"] in ["medium", "high"]:
                priority_sources = ["wetten_nl", "overheid_nl"] + priority_sources
                confidence_modifier += 0.1

        # Term-driven adjustments
        if term_analysis["term_type"] == "legal_concept":
            if "wetten_nl" not in priority_sources:
                priority_sources.insert(0, "wetten_nl")
            confidence_modifier += 0.1

        # Context-driven adjustments
        org_domain = context_analysis.get("organizational", {}).get("domain")
        if org_domain == "prosecution":
            if "strafrechtketen_nl" not in priority_sources:
                priority_sources.append("strafrechtketen_nl")
        elif org_domain == "law_enforcement":
            if "kamerstukken_nl" not in priority_sources:
                priority_sources.append("kamerstukken_nl")

        # EU context
        law_area = context_analysis.get("juridical", {}).get("law_area")
        if law_area == "european":
            if "iate" not in priority_sources:
                priority_sources.append("iate")

        # Bepaal strategy name
        if doc_analysis["has_documents"] and doc_analysis["legal_complexity"] != "none":
            strategy_name = "document_enhanced_legal"
        elif doc_analysis["has_documents"]:
            strategy_name = "document_enhanced_general"
        elif term_analysis["term_type"] == "legal_concept":
            strategy_name = "legal_focused"
        else:
            strategy_name = "general_comprehensive"

        # Reasoning
        reasoning_parts = []
        if doc_analysis["has_documents"]:
            reasoning_parts.append(
                f"Document context beschikbaar ({doc_analysis['document_type']} type)"
            )
        if doc_analysis.get("legal_complexity", "none") != "none":
            reasoning_parts.append(
                f"Juridische complexiteit: {doc_analysis['legal_complexity']}"
            )
        if term_analysis["term_type"] != "general":
            reasoning_parts.append(f"Term type: {term_analysis['term_type']}")

        reasoning = (
            "; ".join(reasoning_parts) if reasoning_parts else "Standaard bron selectie"
        )

        return SourceStrategy(
            strategy_name=strategy_name,
            priority_sources=list(
                dict.fromkeys(priority_sources)
            ),  # Remove duplicates, keep order
            excluded_sources=excluded_sources,
            boost_keywords=boost_keywords,
            confidence_modifier=min(confidence_modifier, 1.5),  # Cap at 1.5x
            reasoning=reasoning,
        )

    def _create_default_strategy(self, begrip: str) -> SourceStrategy:
        """Creëer default strategy als analyse faalt."""
        return SourceStrategy(
            strategy_name="default_fallback",
            priority_sources=["wikipedia", "wiktionary", "overheid_nl"],
            excluded_sources=[],
            boost_keywords=[],
            confidence_modifier=1.0,
            reasoning=f"Fallback strategy voor '{begrip}'",
        )

    def _initialize_source_profiles(self) -> dict[str, dict[str, Any]]:
        """Initialiseer profielen van beschikbare bronnen."""
        return {
            "wikipedia": {
                "strengths": ["general_knowledge", "broad_coverage", "context"],
                "weaknesses": ["not_authoritative", "variable_quality"],
                "best_for": ["general_terms", "background_context"],
                "legal_relevance": "low",
            },
            "wiktionary": {
                "strengths": ["definitions", "etymology", "linguistic"],
                "weaknesses": ["limited_context", "basic_definitions"],
                "best_for": ["word_meanings", "basic_definitions"],
                "legal_relevance": "low",
            },
            "wetten_nl": {
                "strengths": ["authoritative_legal", "current_law", "official"],
                "weaknesses": ["complex_language", "limited_explanation"],
                "best_for": ["legal_terms", "official_definitions"],
                "legal_relevance": "high",
            },
            "overheid_nl": {
                "strengths": ["government_perspective", "policy_context", "official"],
                "weaknesses": ["bureaucratic_language", "limited_scope"],
                "best_for": ["policy_terms", "government_procedures"],
                "legal_relevance": "medium",
            },
            "strafrechtketen_nl": {
                "strengths": ["criminal_law_focus", "practical_context"],
                "weaknesses": ["narrow_scope", "specific_domain"],
                "best_for": ["criminal_justice_terms"],
                "legal_relevance": "high",
            },
        }

    def _initialize_context_patterns(self) -> dict[str, list[str]]:
        """Initialiseer context patronen voor source selectie."""
        return {
            "legal_high_priority": ["wetten_nl", "overheid_nl", "strafrechtketen_nl"],
            "general_balanced": ["wikipedia", "wiktionary", "overheid_nl"],
            "technical_focused": ["wikipedia", "overheid_nl"],
            "policy_focused": ["overheid_nl", "kamerstukken_nl", "wikipedia"],
        }
