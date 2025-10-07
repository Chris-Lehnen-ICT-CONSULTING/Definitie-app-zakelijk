"""
Improved Ontological Classifier - Drop-in vervanging voor OntologischeAnalyzer.

DOEL: Betere classificatie met 3-context support, zonder UI wijzigingen.
"""

import re
from dataclasses import dataclass

from domain.ontological_categories import OntologischeCategorie


@dataclass
class ClassificationResult:
    """Resultaat van classificatie (backward compatible format)."""

    categorie: OntologischeCategorie
    reasoning: str
    test_scores: dict


class ImprovedOntologyClassifier:
    """
    Verbeterde classifier met:
    - 3-context support (org, jur, wet)
    - Pattern matching + semantic analysis
    - Policy-based confidence thresholds
    - GEEN web dependencies (500x sneller)
    """

    def __init__(self):
        """Initialize classifier met patterns."""
        self._init_patterns()

    def _init_patterns(self):
        """Nederlandse linguistic patterns per categorie."""
        self.patterns = {
            "type": {
                "suffixes": [
                    "systeem",
                    "model",
                    "type",
                    "soort",
                    "klasse",
                    "categorie",
                ],
                "indicators": [
                    r"\b(soort|type|categorie|klasse|vorm) van\b",
                    r"\bbehoort tot\b",
                    r"\bvalt onder\b",
                    r"\bis een\b.*\b(systeem|model|instrument)\b",
                ],
                "words": ["toets", "formulier", "register", "document"],
            },
            "proces": {
                "suffixes": ["atie", "tie", "ing", "eren", "isatie"],
                "indicators": [
                    r"\b(handeling|proces|procedure|verloop)\b",
                    r"\bwordt uitgevoerd\b",
                    r"\b(uitvoeren|verrichten|doen) van\b",
                    r"\b(waarbij|waardoor|waarmee)\b",
                ],
                "words": ["validatie", "verificatie", "beoordeling", "controle"],
            },
            "resultaat": {
                "suffixes": ["besluit", "uitspraak", "vonnis"],
                "indicators": [
                    r"\b(resultaat|uitkomst|gevolg|effect)\b",
                    r"\b(na afloop|als gevolg)\b",
                    r"\b(opgeleverd|ontstaan|voortgekomen)\b",
                    r"\bwordt verleend\b",
                ],
                "words": [
                    "besluit",
                    "rapport",
                    "conclusie",
                    "advies",
                    "vergunning",
                    "beschikking",
                ],
            },
            "exemplaar": {
                "suffixes": [],
                "indicators": [
                    r"\b(dit|deze|dat) (specifieke|concrete)\b",
                    r"\bmet betrekking tot\b",
                    r"\b(gelegen|gevestigd|wonende) te\b",
                    r"\bmet kenmerk\b",
                ],
                "words": ["verdachte", "betrokkene", "aanvrager"],
            },
        }

    def classify(
        self,
        begrip: str,
        org_context: str = "",
        jur_context: str = "",
        wet_context: str = "",
    ) -> ClassificationResult:
        """
        Classificeer begrip met 3-context support.

        Args:
            begrip: Het te classificeren begrip
            org_context: Organisatorische context
            jur_context: Juridische context
            wet_context: Wettelijke basis context (nieuw!)

        Returns:
            ClassificationResult met categorie, reasoning, test_scores
        """
        # Stap 1: Genereer scores uit begrip + contexten
        scores = self._generate_scores(begrip, org_context, jur_context, wet_context)

        # Stap 2: Classificeer op basis van scores (met policies)
        categorie = self._classify_from_scores(scores, begrip)

        # Stap 3: Genereer reasoning
        reasoning = self._generate_reasoning(begrip, categorie, scores)

        return ClassificationResult(
            categorie=categorie,
            reasoning=reasoning,
            test_scores=scores,
        )

    def _generate_scores(
        self, begrip: str, org_ctx: str, jur_ctx: str, wet_ctx: str
    ) -> dict:
        """
        Genereer scores per categorie (0.0-1.0).

        Gebruikt:
        - Pattern matching op begrip
        - Semantic analysis van contexten
        - Weighted scoring
        """
        scores = {"type": 0.0, "proces": 0.0, "resultaat": 0.0, "exemplaar": 0.0}

        begrip_lower = begrip.lower()

        # =======================================
        # Score 1: Pattern matching op begrip
        # =======================================
        for categorie, patterns in self.patterns.items():
            pattern_score = 0.0

            # Check exact words FIRST (strongest signal)
            if begrip_lower in patterns["words"]:
                pattern_score += 0.6  # Verhoogd: exact match is sterkste signaal

            # Check suffixes (strong signal, maar minder dan exact match)
            for suffix in patterns["suffixes"]:
                if begrip_lower.endswith(suffix):
                    pattern_score += 0.4
                elif suffix in begrip_lower:
                    pattern_score += 0.2

            # Check indicators (weak signal)
            for indicator_pattern in patterns["indicators"]:
                if re.search(indicator_pattern, begrip_lower, re.IGNORECASE):
                    pattern_score += 0.1

            scores[categorie] += min(pattern_score, 1.0)  # Cap at 1.0

        # =======================================
        # Score 2: Context analysis (nieuw!)
        # =======================================
        combined_context = f"{org_ctx} {jur_ctx} {wet_ctx}".lower()

        if combined_context.strip():
            # TYPE indicators in context
            if re.search(
                r"\b(soort|type|klasse|categorie|instrument|model)\b", combined_context
            ):
                scores["type"] += 0.2

            # PROCES indicators in context
            if re.search(
                r"\b(uitvoer|procedure|handeling|verloop|proces|stappen)\b",
                combined_context,
            ):
                scores["proces"] += 0.2

            # RESULTAAT indicators in context
            if re.search(
                r"\b(besluit|uitkomst|resultaat|verleend|afgegeven)\b",
                combined_context,
            ):
                scores["resultaat"] += 0.2

            # EXEMPLAAR indicators in context
            if re.search(
                r"\b(specifiek|concreet|individueel|bepaald|betreffend)\b",
                combined_context,
            ):
                scores["exemplaar"] += 0.2

        # =======================================
        # Score 3: Juridische context boost (nieuw!)
        # =======================================
        if jur_ctx.strip():
            jur_lower = jur_ctx.lower()

            # Juridische TYPE begrippen
            if re.search(r"\b(belasting|heffing|recht|plicht)\b", jur_lower):
                scores["type"] += 0.15

            # Juridische PROCES begrippen
            if re.search(
                r"\b(procedure|beroep|aanvraag|toets|beoordeling)\b", jur_lower
            ):
                scores["proces"] += 0.15

            # Juridische RESULTAAT begrippen
            if re.search(
                r"\b(besluit|beschikking|uitspraak|vonnis|vergunning)\b", jur_lower
            ):
                scores["resultaat"] += 0.15

        # =======================================
        # Score 4: Wettelijke basis boost (nieuw!)
        # =======================================
        if wet_ctx.strip():
            wet_lower = wet_ctx.lower()

            # Als wet DEFINIEERT iets → TYPE
            if re.search(r"\b(wordt verstaan onder|definitie|begrip)\b", wet_lower):
                scores["type"] += 0.15

            # Als wet BESCHRIJFT handeling → PROCES
            if re.search(r"\b(dient te|moet|zal|procedure)\b", wet_lower):
                scores["proces"] += 0.15

            # Als wet RESULTAAT noemt → RESULTAAT
            if re.search(r"\b(verleent|afwijst|beslist|bepaalt)\b", wet_lower):
                scores["resultaat"] += 0.15

        # Normaliseer scores naar [0, 1]
        max_score = max(scores.values()) if max(scores.values()) > 0 else 1.0
        return {k: min(v / max_score, 1.0) for k, v in scores.items()}

    def _classify_from_scores(self, scores: dict, begrip: str) -> OntologischeCategorie:
        """
        Classificeer op basis van scores met policy thresholds.

        Policy: "gebalanceerd"
        - Winnaar moet minimaal 0.30 scoren
        - Winnaar moet minimaal 0.12 marge hebben op runner-up
        - Anders: fallback op basis van begrip type
        """
        MIN_WINNER_SCORE = 0.30
        MIN_MARGIN = 0.12

        # Sorteer scores
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        winner_cat, winner_score = sorted_scores[0]
        runner_up_cat, runner_up_score = sorted_scores[1]

        margin = winner_score - runner_up_score

        # Check thresholds
        if winner_score >= MIN_WINNER_SCORE and margin >= MIN_MARGIN:
            # Duidelijke winnaar
            return self._string_to_enum(winner_cat)

        # Threshold niet gehaald → fallback strategie
        # Fallback 1: PROCES is meest voorkomend (43% in tests)
        if winner_cat == "proces" and winner_score > 0.2:
            return OntologischeCategorie.PROCES

        # Fallback 2: Check suffix patterns (sterk signaal)
        begrip_lower = begrip.lower()
        if begrip_lower.endswith(("atie", "tie", "ing")):
            return OntologischeCategorie.PROCES
        if begrip_lower in ["besluit", "vergunning", "beschikking"]:
            return OntologischeCategorie.RESULTAAT
        if begrip_lower in ["toets", "formulier", "document"]:
            return OntologischeCategorie.TYPE

        # Fallback 3: Use winner anyway (met lage confidence)
        return self._string_to_enum(winner_cat)

    def _string_to_enum(self, cat_string: str) -> OntologischeCategorie:
        """Convert string naar enum."""
        mapping = {
            "type": OntologischeCategorie.TYPE,
            "proces": OntologischeCategorie.PROCES,
            "resultaat": OntologischeCategorie.RESULTAAT,
            "exemplaar": OntologischeCategorie.EXEMPLAAR,
        }
        return mapping.get(cat_string, OntologischeCategorie.PROCES)

    def _generate_reasoning(
        self, begrip: str, categorie: OntologischeCategorie, scores: dict
    ) -> str:
        """Genereer menselijke uitleg van classificatie."""
        cat_string = categorie.value
        cat_score = scores.get(cat_string, 0.0)

        # Vind welke patterns matchten
        matched_patterns = []
        begrip_lower = begrip.lower()

        for suffix in self.patterns[cat_string]["suffixes"]:
            if begrip_lower.endswith(suffix):
                matched_patterns.append(f"eindigt op '-{suffix}'")
            elif suffix in begrip_lower:
                matched_patterns.append(f"bevat '{suffix}'")

        if begrip_lower in self.patterns[cat_string]["words"]:
            matched_patterns.append("komt voor in typische woordenlijst")

        # Build reasoning
        parts = [
            f"Classificatie: **{categorie.value.upper()}** (score: {cat_score:.2f})"
        ]

        if matched_patterns:
            parts.append(f"Patronen: {', '.join(matched_patterns[:2])}")

        # Runner-up info
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_scores) > 1:
            runner_up, runner_score = sorted_scores[1]
            margin = cat_score - runner_score
            parts.append(f"Marge t.o.v. {runner_up}: {margin:.2f}")

        return " | ".join(parts)


# ============================================================
# BACKWARD COMPATIBILITY: Legacy interface
# ============================================================


class QuickOntologischeAnalyzer:
    """
    Legacy adapter - gebruikt nieuwe classifier maar behoudt oude interface.
    Voor compatibility met bestaande code.
    """

    def quick_categoriseer(self, begrip: str) -> tuple[OntologischeCategorie, str]:
        """Legacy method signature."""
        classifier = ImprovedOntologyClassifier()
        result = classifier.classify(begrip=begrip)
        return (result.categorie, result.reasoning)
