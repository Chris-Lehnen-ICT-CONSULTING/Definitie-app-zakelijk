"""
Duplicate Detection Service - Pure business logic voor duplicate detection.

Deze service bevat alle business logic voor het detecteren van duplicaten,
zonder enige database dependencies. Dit maakt de logic testbaar en herbruikbaar.
"""

import logging
from dataclasses import dataclass
from typing import cast

from services.interfaces import Definition

logger = logging.getLogger(__name__)


@dataclass
class DuplicateMatch:
    """Match resultaat voor duplicate detection."""

    definition: Definition
    score: float
    reason: str
    match_type: str = "fuzzy"  # "exact" or "fuzzy"


class DuplicateDetectionService:
    """
    Pure business logic voor duplicate detection.
    Geen database dependencies!
    """

    def __init__(self, similarity_threshold: float = 0.7):
        """
        Initialiseer de duplicate detection service.

        Args:
            similarity_threshold: Minimum score voor fuzzy matches (0.0-1.0)
        """
        self.threshold = similarity_threshold
        logger.info(
            f"DuplicateDetectionService initialized with threshold {similarity_threshold}"
        )

    def find_duplicates(
        self, new_definition: Definition, existing_definitions: list[Definition]
    ) -> list[DuplicateMatch]:
        """
        Business logic voor duplicate detection.

        Zoekt naar exacte en fuzzy matches op basis van begrip en context.

        Args:
            new_definition: De nieuwe definitie om te checken
            existing_definitions: Lijst van bestaande definities

        Returns:
            Lijst van DuplicateMatch objecten, gesorteerd op score (hoogste eerst)
        """
        matches = []

        for existing in existing_definitions:
            # Skip archived definitions (status may be attribute or in metadata)
            status_val = getattr(existing, "status", None)
            if not status_val and getattr(existing, "metadata", None):
                status_val = existing.metadata.get("status")
            if status_val == "archived":
                continue

            # Check exact match
            if self._is_exact_match(new_definition, existing):
                matches.append(
                    DuplicateMatch(
                        definition=existing,
                        score=1.0,
                        reason="Exact match: begrip + context",
                        match_type="exact",
                    )
                )
            # Check fuzzy match
            else:
                score = self._calculate_similarity(
                    new_definition.begrip, existing.begrip
                )
                if score > self.threshold:
                    matches.append(
                        DuplicateMatch(
                            definition=existing,
                            score=score,
                            reason=f"Similar: {score:.0%} match op begrip",
                            match_type="fuzzy",
                        )
                    )

        # Sort by score (highest first)
        return sorted(matches, key=lambda x: x.score, reverse=True)

    def _is_exact_match(self, def1: Definition, def2: Definition) -> bool:
        """
        Business rule voor exact match.

        Een exacte match is wanneer begrip en context identiek zijn.

        Args:
            def1: Eerste definitie
            def2: Tweede definitie

        Returns:
            True als het een exacte match is
        """
        # Begrip moet exact matchen (case insensitive)
        if def1.begrip.lower() != def2.begrip.lower():
            return False

        # Context moet ook matchen (drie lijsten, order-onafhankelijk)
        def _norm_list(lst):
            return tuple(sorted([str(x).lower().strip() for x in (lst or [])]))

        return cast(
            bool,
            _norm_list(getattr(def1, "organisatorische_context", []))
            == _norm_list(getattr(def2, "organisatorische_context", []))
            and _norm_list(getattr(def1, "juridische_context", []))
            == _norm_list(getattr(def2, "juridische_context", []))
            and _norm_list(getattr(def1, "wettelijke_basis", []))
            == _norm_list(getattr(def2, "wettelijke_basis", [])),
        )

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Jaccard similarity algoritme voor fuzzy matching.

        Berekent de similarity score tussen twee strings op basis van
        gemeenschappelijke woorden.

        Args:
            str1: Eerste string
            str2: Tweede string

        Returns:
            Similarity score tussen 0.0 en 1.0
        """
        # Handle empty strings
        if not str1 or not str2:
            return 0.0

        # Convert to lowercase and split into words with light stemming
        def _normalize_tokens(s: str) -> set[str]:
            tokens = []
            import re

            cleaned = re.sub(r"[-/._]", " ", (s or "").lower())
            for t in cleaned.split():
                base = t.strip()
                # Light Dutch-ish stemming to catch e/elijk/elijke variants
                for suf in ("elijke", "elijk", "en", "e"):
                    if base.endswith(suf) and len(base) > len(suf) + 1:
                        base = base[: -len(suf)]
                        break
                tokens.append(base)
            return set(tokens)

        set1 = _normalize_tokens(str1)
        set2 = _normalize_tokens(str2)

        # Handle empty sets
        if not set1 or not set2:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def check_duplicate_risk(
        self, new_definition: Definition, existing_definitions: list[Definition]
    ) -> str:
        """
        Bepaal het risico niveau voor duplicaten.

        Args:
            new_definition: De nieuwe definitie
            existing_definitions: Bestaande definities

        Returns:
            Risk level: "high", "medium", "low", or "none"
        """
        duplicates = self.find_duplicates(new_definition, existing_definitions)

        if not duplicates:
            return "none"

        # Check voor exact matches
        exact_matches = [d for d in duplicates if d.match_type == "exact"]
        if exact_matches:
            return "high"

        # Check hoogste fuzzy score
        highest_score = max(d.score for d in duplicates)
        if highest_score >= 0.9:
            return "high"
        if highest_score >= 0.8:
            return "medium"
        return "low"

    def get_duplicate_summary(self, matches: list[DuplicateMatch]) -> dict:
        """
        Genereer een summary van gevonden duplicaten.

        Args:
            matches: Lijst van duplicate matches

        Returns:
            Dictionary met summary informatie
        """
        if not matches:
            return {
                "total": 0,
                "exact_matches": 0,
                "fuzzy_matches": 0,
                "highest_score": 0.0,
                "risk_level": "none",
            }

        exact_count = sum(1 for m in matches if m.match_type == "exact")
        fuzzy_count = sum(1 for m in matches if m.match_type == "fuzzy")
        highest_score = max(m.score for m in matches)

        # Determine risk level
        if exact_count > 0 or highest_score >= 0.9:
            risk_level = "high"
        elif highest_score >= 0.8:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "total": len(matches),
            "exact_matches": exact_count,
            "fuzzy_matches": fuzzy_count,
            "highest_score": highest_score,
            "risk_level": risk_level,
        }

    def update_threshold(self, new_threshold: float):
        """
        Update de similarity threshold.

        Args:
            new_threshold: Nieuwe threshold (0.0-1.0)
        """
        if not 0.0 <= new_threshold <= 1.0:
            msg = "Threshold moet tussen 0.0 en 1.0 zijn"
            raise ValueError(msg)

        self.threshold = new_threshold
        logger.info(f"Similarity threshold updated to {new_threshold}")
