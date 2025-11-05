"""
Improved Ontological Classifier - Drop-in vervanging voor OntologischeAnalyzer.

DEF-35: MVP Term-Based Classifier Essentials
- Externe YAML configuratie voor patterns
- Priority cascade voor tie-breaking
- 3-tier confidence scoring (HIGH/MEDIUM/LOW)

DOEL: Betere classificatie met 3-context support, zonder UI wijzigingen.
"""

import logging
import re
from dataclasses import dataclass

from domain.ontological_categories import OntologischeCategorie
from services.classification.term_config import TermPatternConfig, load_term_config

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """
    Resultaat van classificatie.

    DEF-35: Extended met confidence scoring.
    """

    categorie: OntologischeCategorie
    reasoning: str
    test_scores: dict
    confidence: float  # NEW: 0.0-1.0 confidence score
    confidence_label: str  # NEW: "HIGH"/"MEDIUM"/"LOW"
    all_scores: dict  # NEW: All category scores voor debugging


class ImprovedOntologyClassifier:
    """
    Verbeterde classifier met:
    - 3-context support (org, jur, wet)
    - Pattern matching + semantic analysis
    - YAML configuratie (DEF-35)
    - Priority cascade tie-breaking (DEF-35)
    - 3-tier confidence scoring (DEF-35)
    - GEEN web dependencies (500x sneller)
    """

    def __init__(self, config: TermPatternConfig | None = None):
        """
        Initialize classifier met patterns.

        Args:
            config: Optionele custom configuratie (default: laadt uit YAML)
        """
        # DEF-35: Laad config uit YAML (cached)
        self.config = config or load_term_config()
        self._init_patterns()
        logger.info(
            f"ImprovedOntologyClassifier initialized with "
            f"{len(self.config.domain_overrides)} overrides, "
            f"{sum(len(w) for w in self.config.suffix_weights.values())} patterns"
        )

    def _init_patterns(self):
        """
        Initialize Nederlandse linguistic patterns per categorie.

        DEF-35: Gebruikt nu config.suffix_weights in plaats van hardcoded patterns.
        """
        # Build patterns dict vanuit config
        self.patterns = {
            "type": {
                "suffixes": list(
                    self.config.suffix_weights.get("TYPE", {}).keys()
                ),  # Config-driven
                "indicators": [
                    r"\b(soort|type|categorie|klasse|vorm) van\b",
                    r"\bbehoort tot\b",
                    r"\bvalt onder\b",
                    r"\bis een\b.*\b(systeem|model|instrument)\b",
                ],
                "words": ["toets", "formulier", "register", "document"],
            },
            "proces": {
                "suffixes": list(
                    self.config.suffix_weights.get("PROCES", {}).keys()
                ),  # Config-driven
                "indicators": [
                    r"\b(handeling|proces|procedure|verloop)\b",
                    r"\bwordt uitgevoerd\b",
                    r"\b(uitvoeren|verrichten|doen) van\b",
                    r"\b(waarbij|waardoor|waarmee)\b",
                ],
                "words": ["validatie", "verificatie", "beoordeling", "controle"],
            },
            "resultaat": {
                "suffixes": list(
                    self.config.suffix_weights.get("RESULTAAT", {}).keys()
                ),  # Config-driven
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
                "suffixes": [],  # EXEMPLAAR heeft geen suffix patterns
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

        DEF-35: Extended met confidence scoring en all_scores.

        Args:
            begrip: Het te classificeren begrip
            org_context: Organisatorische context
            jur_context: Juridische context
            wet_context: Wettelijke basis context

        Returns:
            ClassificationResult met categorie, reasoning, scores, confidence
        """
        # DEF-35: Check domain overrides FIRST (hoogste prioriteit)
        begrip_lower = begrip.lower().strip()
        if begrip_lower in self.config.domain_overrides:
            override_cat = self.config.domain_overrides[begrip_lower]
            categorie = self._string_to_enum(override_cat.lower())

            # Domain override = HIGH confidence (0.95)
            confidence = 0.95
            confidence_label = "HIGH"

            reasoning = (
                f"Classificatie: **{categorie.value.upper()}** (domain override)\n"
                f"Confidence: {confidence:.2f} ({confidence_label})\n"
                f"Reden: Expliciete configuratie voor '{begrip}'"
            )

            # Scores dict voor backward compatibility
            scores = {
                cat.lower(): 0.0 for cat in ["TYPE", "PROCES", "RESULTAAT", "EXEMPLAAR"]
            }
            scores[override_cat.lower()] = 1.0

            return ClassificationResult(
                categorie=categorie,
                reasoning=reasoning,
                test_scores=scores,
                confidence=confidence,
                confidence_label=confidence_label,
                all_scores=scores.copy(),
            )

        # Stap 1: Genereer scores uit begrip + contexten
        scores = self._generate_scores(begrip, org_context, jur_context, wet_context)

        # Stap 2: Classificeer op basis van scores (met policies)
        categorie = self._classify_from_scores(scores, begrip)

        # DEF-35: Stap 3: Bereken confidence
        confidence, confidence_label = self._calculate_confidence(scores)

        # Stap 4: Genereer reasoning
        reasoning = self._generate_reasoning(
            begrip, categorie, scores, confidence, confidence_label
        )

        return ClassificationResult(
            categorie=categorie,
            reasoning=reasoning,
            test_scores=scores,
            confidence=confidence,
            confidence_label=confidence_label,
            all_scores=scores.copy(),
        )

    def _generate_scores(
        self, begrip: str, org_ctx: str, jur_ctx: str, wet_ctx: str
    ) -> dict:
        """
        Genereer scores per categorie (0.0-1.0).

        DEF-35: Gebruikt config.suffix_weights voor weighted scoring.

        Gebruikt:
        - Pattern matching op begrip (weighted via config)
        - Semantic analysis van contexten
        - Weighted scoring
        """
        scores = {"type": 0.0, "proces": 0.0, "resultaat": 0.0, "exemplaar": 0.0}

        begrip_lower = begrip.lower()

        # =======================================
        # Score 1: Pattern matching op begrip (DEF-35: weighted)
        # =======================================
        for categorie, patterns in self.patterns.items():
            pattern_score = 0.0

            # Check exact words FIRST (strongest signal)
            if begrip_lower in patterns["words"]:
                pattern_score += 0.6

            # DEF-35: Check suffixes met CONFIG WEIGHTS
            category_upper = categorie.upper()
            suffix_weights = self.config.suffix_weights.get(category_upper, {})

            for suffix in patterns["suffixes"]:
                weight = suffix_weights.get(
                    suffix, 0.4
                )  # Fallback 0.4 als niet in config

                if begrip_lower.endswith(suffix):
                    # Exact suffix match: full weight
                    pattern_score += weight
                elif suffix in begrip_lower:
                    # Substring match: half weight
                    pattern_score += weight * 0.5

            # Check indicators (weak signal)
            for indicator_pattern in patterns["indicators"]:
                if re.search(indicator_pattern, begrip_lower, re.IGNORECASE):
                    pattern_score += 0.1

            scores[categorie] += min(pattern_score, 1.0)  # Cap at 1.0

        # =======================================
        # Score 2: Context analysis
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
        # Score 3: Juridische context boost
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
        # Score 4: Wettelijke basis boost
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

        DEF-35: Priority cascade voor tie-breaking.

        Policy: "gebalanceerd"
        - Winnaar moet minimaal 0.30 scoren
        - Winnaar moet minimaal 0.12 marge hebben op runner-up
        - Bij ties (<0.15 verschil): gebruik priority cascade
        - Anders: fallback op basis van begrip type
        """
        MIN_WINNER_SCORE = 0.30
        MIN_MARGIN = 0.12

        # Sorteer scores
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        winner_cat, winner_score = sorted_scores[0]
        runner_up_cat, runner_up_score = (
            sorted_scores[1] if len(sorted_scores) > 1 else ("", 0.0)
        )

        margin = winner_score - runner_up_score

        # DEF-35: Priority cascade bij kleine marges
        if margin < 0.15:
            cascade_result = self._apply_priority_cascade(scores, begrip)
            if cascade_result:
                logger.debug(
                    f"Priority cascade applied for '{begrip}': "
                    f"{cascade_result.value} (margin={margin:.2f})"
                )
                return cascade_result

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

    def _apply_priority_cascade(
        self, scores: dict[str, float], begrip: str
    ) -> OntologischeCategorie | None:
        """
        Apply priority cascade tie-breaking logic.

        DEF-35: Bij verschil < 0.15 tussen top scores, gebruik config priority order.

        Args:
            scores: Dict van categorie (lowercase) → score
            begrip: Het begrip (voor logging)

        Returns:
            OntologischeCategorie uit priority order, of None als geen match

        Logic:
        1. Check of top 2 scores binnen 0.15 van elkaar liggen (tied)
        2. Loop door category_priority in volgorde
        3. Return eerste categorie met score >= 0.30 (viable candidate)
        4. Return None als geen viable candidate gevonden
        """
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        winner_score = sorted_scores[0][1]
        runner_up_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0

        # Check tied condition
        if winner_score - runner_up_score >= 0.15:
            return None  # Not tied, no cascade needed

        # Apply priority cascade
        MIN_VIABLE_SCORE = 0.30
        for category in self.config.category_priority:
            category_lower = category.lower()
            score = scores.get(category_lower, 0.0)

            if score >= MIN_VIABLE_SCORE:
                logger.debug(
                    f"Priority cascade winner: {category} "
                    f"(score={score:.2f}, tied within 0.15)"
                )
                return self._string_to_enum(category_lower)

        # No viable candidate in priority order
        return None

    def _calculate_confidence(self, scores: dict[str, float]) -> tuple[float, str]:
        """
        Calculate confidence using margin + winner score.

        DEF-35: 3-tier confidence scoring (HIGH/MEDIUM/LOW).

        Formula:
        - margin = (winner - runner_up)
        - margin_factor = min(margin / 0.30, 1.0)  # Normalize to [0, 1]
        - confidence = winner * margin_factor

        Thresholds (uit config):
        - HIGH: >= 0.70 (groen, auto-accept)
        - MEDIUM: >= 0.45 (oranje, review aanbevolen)
        - LOW: < 0.45 (rood, handmatig)

        Args:
            scores: Dict van categorie (lowercase) → score

        Returns:
            Tuple van (confidence_score, confidence_label)
        """
        sorted_scores = sorted(scores.values(), reverse=True)
        winner = sorted_scores[0]
        runner_up = sorted_scores[1] if len(sorted_scores) > 1 else 0.0
        margin = winner - runner_up

        # Bereken margin factor (normalized naar [0, 1])
        margin_factor = min(margin / 0.30, 1.0)

        # Confidence = winner score * margin factor
        confidence = winner * margin_factor

        # Apply thresholds uit config
        if confidence >= self.config.confidence_thresholds["high"]:
            label = "HIGH"
        elif confidence >= self.config.confidence_thresholds["medium"]:
            label = "MEDIUM"
        else:
            label = "LOW"

        return confidence, label

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
        self,
        begrip: str,
        categorie: OntologischeCategorie,
        scores: dict,
        confidence: float,
        confidence_label: str,
    ) -> str:
        """
        Genereer menselijke uitleg van classificatie.

        DEF-35: Extended met confidence info.
        """
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

        # DEF-35: Add confidence info
        confidence_emoji = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🔴"}
        parts.append(
            f"Confidence: {confidence:.2f} {confidence_emoji.get(confidence_label, '')} ({confidence_label})"
        )

        if matched_patterns:
            parts.append(f"Patronen: {', '.join(matched_patterns[:2])}")

        # Runner-up info
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_scores) > 1:
            runner_up, runner_score = sorted_scores[1]
            margin = cat_score - runner_score
            parts.append(f"Marge t.o.v. {runner_up}: {margin:.2f}")

        return " | ".join(parts)
