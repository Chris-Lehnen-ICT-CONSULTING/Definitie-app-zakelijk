"""
Context-based filtering and relevance scoring for web lookup results.

Comprehensive Fix B: Post-query filtering op basis van context match.
Dit vermijdt context pollution in queries terwijl precision behouden blijft.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContextMatch:
    """Result van context matching analyse."""

    has_org_match: bool = False
    has_jur_match: bool = False
    has_wet_match: bool = False
    org_matches: list[str] = field(default_factory=list)
    jur_matches: list[str] = field(default_factory=list)
    wet_matches: list[str] = field(default_factory=list)
    relevance_score: float = 0.0
    match_count: int = 0


class ContextFilter:
    """Filter en score results op basis van context relevantie."""

    def __init__(self):
        """Initialize context filter met keyword patterns."""
        # Organizational context patterns (case-insensitive)
        self.org_patterns = {
            "OM": r"\b(openbaar\s+ministerie|om)\b",
            "ZM": r"\b(zittingsmanager|zm)\b",
            "NP": r"\b(nationale\s+politie|politie|np)\b",
            "DJI": r"\b(dji|dienst\s+justitiële\s+inrichtingen)\b",
            "KMAR": r"\b(kmar|koninklijke\s+marechaussee|marechaussee)\b",
        }

        # Juridical domain patterns (zonder word boundary aan einde voor -e, -elijk, etc.)
        self.jur_patterns = {
            "Strafrecht": r"\bstrafrecht\w*|\bstrafzaak\w*",
            "Civiel recht": r"\bciviel\s+recht\w*|\bcivielrecht\w*|\bciviele\s+zaak\w*",
            "Bestuursrecht": r"\bbestuursrecht\w*|\bbestuurlijk\w*",
        }

        # Legal basis patterns
        self.wet_patterns = {
            "Sv": r"\b(sv|wetboek\s+van\s+strafvordering|strafvordering)\b",
            "Sr": r"\b(sr|wetboek\s+van\s+strafrecht)\b",
            "Awb": r"\b(awb|algemene\s+wet\s+bestuursrecht)\b",
            "Rv": r"\b(rv|wetboek\s+van\s+burgerlijke\s+rechtsvordering)\b",
        }

    def match_context(
        self,
        text: str,
        org_context: list[str] | None = None,
        jur_context: list[str] | None = None,
        wet_context: list[str] | None = None,
    ) -> ContextMatch:
        """
        Analyseer text voor context matches.

        Args:
            text: Text to analyze (title + snippet + definition)
            org_context: Organizational context tokens (e.g., ["OM", "ZM"])
            jur_context: Juridical domain tokens (e.g., ["Strafrecht"])
            wet_context: Legal basis tokens (e.g., ["Sv", "Wetboek van Strafvordering"])

        Returns:
            ContextMatch with match details and relevance score
        """
        if not text:
            return ContextMatch()

        text_lower = text.lower()
        match = ContextMatch()

        # Match organizational context
        if org_context:
            for token in org_context:
                token_upper = token.upper()
                if token_upper in self.org_patterns:
                    pattern = self.org_patterns[token_upper]
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        match.has_org_match = True
                        match.org_matches.append(token)
                        match.match_count += 1

        # Match juridical domain
        if jur_context:
            for token in jur_context:
                token_lower = token.lower()
                # Check if any jur_pattern matches in text
                for domain, pattern in self.jur_patterns.items():
                    domain_lower = domain.lower()
                    # Check if token relates to this domain
                    # E.g., "Strafrecht" relates to "Strafrecht" pattern
                    if (
                        domain_lower in token_lower
                        or token_lower in domain_lower
                        or any(
                            keyword in token_lower
                            for keyword in ["straf", "civiel", "bestuurs"]
                        )
                    ):
                        # Now check if pattern actually matches in text
                        if re.search(pattern, text_lower, re.IGNORECASE):
                            match.has_jur_match = True
                            match.jur_matches.append(token)
                            match.match_count += 1
                            break

        # Match legal basis
        if wet_context:
            for token in wet_context:
                # Normalize token for matching
                token_norm = token.lower().strip()
                for law_code, pattern in self.wet_patterns.items():
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        # Check if token references this law
                        if (
                            law_code.lower() in token_norm
                            or token_norm in law_code.lower()
                        ):
                            match.has_wet_match = True
                            match.wet_matches.append(token)
                            match.match_count += 1
                            break

        # Calculate relevance score (0.0 - 1.0)
        # Weights: wet > jur > org (legal basis is most important)
        score = 0.0
        if match.has_wet_match:
            score += 0.5  # Legal basis match is highly relevant
        if match.has_jur_match:
            score += 0.3  # Juridical domain match is moderately relevant
        if match.has_org_match:
            score += 0.2  # Organizational match is less relevant

        # Bonus for multiple matches (up to 1.0 max)
        if match.match_count > 1:
            score = min(1.0, score + 0.1 * (match.match_count - 1))

        match.relevance_score = score
        return match

    def filter_results(
        self,
        results: list[dict[str, Any]],
        org_context: list[str] | None = None,
        jur_context: list[str] | None = None,
        wet_context: list[str] | None = None,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Filter results op basis van context relevantie.

        Args:
            results: List of result dicts (from rank_and_dedup)
            org_context: Organizational context
            jur_context: Juridical domain context
            wet_context: Legal basis context
            min_score: Minimum relevance score (0.0 = keep all, 0.5 = moderate filter)

        Returns:
            Filtered and scored results
        """
        if not results:
            return []

        # If no context provided, return all results unfiltered
        if not any([org_context, jur_context, wet_context]):
            return results

        scored_results = []
        for result in results:
            # Build text to analyze from all available fields
            text_parts = [
                result.get("title", ""),
                result.get("snippet", ""),
                result.get("definition", ""),
                result.get("summary", ""),
            ]
            text = " ".join([str(p) for p in text_parts if p])

            # Match context
            match = self.match_context(text, org_context, jur_context, wet_context)

            # Only keep results above min_score
            if match.relevance_score >= min_score:
                # Add context match metadata to result
                result_copy = result.copy()
                result_copy["context_match"] = {
                    "relevance_score": match.relevance_score,
                    "match_count": match.match_count,
                    "org_matches": match.org_matches,
                    "jur_matches": match.jur_matches,
                    "wet_matches": match.wet_matches,
                }
                scored_results.append(result_copy)

        # Re-sort by relevance score (DESC) then original score
        scored_results.sort(
            key=lambda x: (
                -x["context_match"]["relevance_score"],
                -x.get("score", 0.0),
            )
        )

        return scored_results

    def boost_score(
        self,
        original_score: float,
        context_match: ContextMatch,
        boost_factor: float = 0.3,
    ) -> float:
        """
        Boost original score op basis van context relevance.

        Args:
            original_score: Original provider-weighted score
            context_match: Context match analysis result
            boost_factor: Maximum boost (0.3 = up to 30% boost)

        Returns:
            Boosted score (capped at 1.0)
        """
        boost = context_match.relevance_score * boost_factor
        return min(1.0, original_score + boost)
