"""
Wikipedia Synonym Extractor voor juridische termen.

Deze service extraheert synoniem kandidaten uit Dutch Wikipedia door:
1. Wikipedia redirects te analyseren (directe synoniemen)
2. Disambiguation pages te parsen voor alternatieve termen
3. Confidence scores te berekenen op basis van redirect type en similariteit

De service filtert false positives zoals categories, templates en meta pages.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, cast
from urllib.parse import quote

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("Warning: aiohttp niet beschikbaar - Wikipedia synonym extractor werkt niet")

logger = logging.getLogger(__name__)


@dataclass
class SynonymCandidate:
    """
    Represents a synonym candidate extracted from Wikipedia.

    Attributes:
        hoofdterm: De originele juridische term
        synoniem: De gevonden synoniem kandidaat
        confidence: Confidence score (0.0-1.0)
        source_type: Type van bron (redirect, disambiguation, similar)
        wikipedia_url: URL van de Wikipedia pagina
        metadata: Extra informatie over de match
    """

    hoofdterm: str
    synoniem: str
    confidence: float
    source_type: (
        str  # "redirect", "disambiguation", "similar_term", "category_redirect"
    )
    wikipedia_url: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for CSV export."""
        return {
            "hoofdterm": self.hoofdterm,
            "synoniem_kandidaat": self.synoniem,
            "confidence": self.confidence,
            "source_type": self.source_type,
            "wikipedia_url": self.wikipedia_url,
            "edit_distance": self.metadata.get("edit_distance", ""),
            "redirect_type": self.metadata.get("redirect_type", ""),
        }


class WikipediaSynonymExtractor:
    """
    Service voor het extraheren van synoniemen uit Dutch Wikipedia.

    Gebruikt Wikipedia API voor:
    - Redirect analysis (directe synoniemen)
    - Disambiguation page parsing (alternatieve termen)
    - Edit distance calculation voor similariteit
    """

    def __init__(self, language: str = "nl", rate_limit_delay: float = 1.0):
        """
        Initialize Wikipedia synonym extractor.

        Args:
            language: Wikipedia taal code (default: nl voor Nederlands)
            rate_limit_delay: Delay tussen requests in seconden (Wikipedia API limit: 1 req/sec)
        """
        self.language = language
        self.base_url = f"https://{language}.wikipedia.org"
        self.api_url = f"{self.base_url}/w/api.php"
        self.rate_limit_delay = rate_limit_delay
        self.session: aiohttp.ClientSession | None = None
        self.last_request_time = 0.0

        # User agent voor Wikipedia API (vereist)
        self.headers = {
            "User-Agent": "DefinitieApp/1.0 (https://github.com/definitie-app; support@definitie-app.nl)"
        }

        # Filters voor false positives
        self.excluded_namespaces = {
            "Categorie:",
            "Category:",
            "Wikipedia:",
            "Sjabloon:",
            "Template:",
            "Bestand:",
            "File:",
            "Help:",
            "Portal:",
            "Portaal:",
        }

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _rate_limit(self) -> None:
        """Enforce rate limiting (max 1 req/sec for Wikipedia API)."""
        import time

        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)

        self.last_request_time = time.time()

    def _is_valid_term(self, term: str) -> bool:
        """
        Check if term is valid (not a category, template, etc.).

        Args:
            term: Term to validate

        Returns:
            True if valid, False if it's a meta page
        """
        for namespace in self.excluded_namespaces:
            if term.startswith(namespace):
                return False
        return True

    def _calculate_edit_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein edit distance between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Edit distance (number of edits needed)
        """
        # Use SequenceMatcher for similarity ratio
        ratio = SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
        # Convert to distance (0 = identical, higher = more different)
        max_len = max(len(s1), len(s2))
        return int((1 - ratio) * max_len)

    def calculate_confidence(
        self, redirect_type: str, edit_distance: int, term_length_diff: int
    ) -> float:
        """
        Calculate confidence score for a synonym candidate.

        Confidence scoring:
        - Direct redirect (exact match): 0.90
        - Redirect from disambiguation: 0.85
        - Similar term (edit distance < 3): 0.75
        - Longer related term: 0.70
        - Questionable (high edit distance or length diff): < 0.60

        Args:
            redirect_type: Type of redirect ("direct", "disambiguation", "similar")
            edit_distance: Edit distance between terms
            term_length_diff: Absolute difference in term length

        Returns:
            Confidence score (0.0-1.0)
        """
        # Base score op redirect type
        if redirect_type == "direct":
            base_score = 0.90
        elif redirect_type == "disambiguation":
            base_score = 0.85
        elif redirect_type == "similar_term":
            base_score = 0.75
        else:
            base_score = 0.60

        # Penalty voor edit distance
        if edit_distance == 0:
            edit_penalty = 0.0
        elif edit_distance <= 2:
            edit_penalty = 0.05
        elif edit_distance <= 5:
            edit_penalty = 0.10
        else:
            edit_penalty = 0.20

        # Penalty voor grote lengte verschillen (likely niet synoniem)
        if term_length_diff <= 5:
            length_penalty = 0.0
        elif term_length_diff <= 10:
            length_penalty = 0.05
        elif term_length_diff <= 20:
            length_penalty = 0.10
        else:
            length_penalty = 0.20

        # Finale score
        confidence = base_score - edit_penalty - length_penalty
        return max(0.0, min(1.0, confidence))  # Clamp to [0.0, 1.0]

    async def get_redirects(self, term: str) -> list[str]:
        """
        Get Wikipedia redirects for a term.

        A redirect indicates that one term redirects to another,
        which often means they are synonyms or closely related.

        Args:
            term: Term to check for redirects

        Returns:
            List of redirect page titles
        """
        if not AIOHTTP_AVAILABLE or not self.session:
            return []

        await self._rate_limit()

        params = {
            "action": "query",
            "format": "json",
            "titles": term,
            "redirects": "1",
        }

        try:
            async with self.session.get(self.api_url, params=params) as response:
                if response.status != 200:
                    logger.error(
                        f"Wikipedia API error for redirects: {response.status}"
                    )
                    return []

                data = await response.json()

                # Check for redirects in response
                redirects = data.get("query", {}).get("redirects", [])
                redirect_titles = []

                for redirect in redirects:
                    from_title = redirect.get("from", "")
                    to_title = redirect.get("to", "")

                    # Skip if not valid
                    if not self._is_valid_term(from_title) or not self._is_valid_term(
                        to_title
                    ):
                        continue

                    # Add both directions
                    if from_title and from_title.lower() != term.lower():
                        redirect_titles.append(from_title)
                    if to_title and to_title.lower() != term.lower():
                        redirect_titles.append(to_title)

                logger.debug(f"Found {len(redirect_titles)} redirects for '{term}'")
                return redirect_titles

        except Exception as e:
            logger.error(f"Error fetching redirects for '{term}': {e}")
            return []

    async def parse_disambiguation(self, term: str) -> list[str]:
        """
        Parse disambiguation page for alternative terms.

        Disambiguation pages list different meanings of a term,
        which can include synonyms or related concepts.

        Args:
            term: Term to check for disambiguation page

        Returns:
            List of alternative terms from disambiguation page
        """
        if not AIOHTTP_AVAILABLE or not self.session:
            return []

        await self._rate_limit()

        # First check if page is disambiguation
        params: dict[str, str | int] = {
            "action": "query",
            "format": "json",
            "titles": term,
            "prop": "categories",
            "cllimit": 50,
        }

        try:
            async with self.session.get(
                self.api_url, params=cast(dict[str, str], params)
            ) as response:
                if response.status != 200:
                    return []

                data = await response.json()
                pages = data.get("query", {}).get("pages", {})

                # Check if it's a disambiguation page
                is_disambiguation = False
                for page_data in pages.values():
                    categories = page_data.get("categories", [])
                    for cat in categories:
                        cat_title = cat.get("title", "")
                        if (
                            "Doorverwijspagina" in cat_title
                            or "Disambiguation" in cat_title
                        ):
                            is_disambiguation = True
                            break

                if not is_disambiguation:
                    return []

                # Get page links (alternative terms)
                await self._rate_limit()

                links_params: dict[str, str | int] = {
                    "action": "query",
                    "format": "json",
                    "titles": term,
                    "prop": "links",
                    "pllimit": 50,
                }

                async with self.session.get(
                    self.api_url, params=cast(dict[str, str], links_params)
                ) as links_response:
                    if links_response.status != 200:
                        return []

                    links_data = await links_response.json()
                    links_pages = links_data.get("query", {}).get("pages", {})

                    alternative_terms = []
                    for page_data in links_pages.values():
                        links = page_data.get("links", [])
                        for link in links:
                            link_title = link.get("title", "")

                            # Skip invalid terms
                            if not self._is_valid_term(link_title):
                                continue

                            # Skip if same as original term
                            if link_title.lower() == term.lower():
                                continue

                            alternative_terms.append(link_title)

                    logger.debug(
                        f"Found {len(alternative_terms)} alternatives from disambiguation for '{term}'"
                    )
                    return alternative_terms[:10]  # Limit to 10 most relevant

        except Exception as e:
            logger.error(f"Error parsing disambiguation for '{term}': {e}")
            return []

    async def extract_synonyms(self, term: str) -> list[SynonymCandidate]:
        """
        Extract synonym candidates for a term from Wikipedia.

        This combines:
        1. Direct redirects (high confidence)
        2. Disambiguation page parsing (medium confidence)
        3. Similar terms based on edit distance (lower confidence)

        Args:
            term: Juridische term om synoniemen voor te vinden

        Returns:
            List of SynonymCandidate objects with confidence scores
        """
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp not available - cannot extract synonyms")
            return []

        logger.info(f"Extracting Wikipedia synonyms for: {term}")
        candidates: list[SynonymCandidate] = []

        # 1. Get redirects (direct synonyms)
        redirects = await self.get_redirects(term)
        for redirect in redirects:
            edit_dist = self._calculate_edit_distance(term, redirect)
            length_diff = abs(len(term) - len(redirect))

            confidence = self.calculate_confidence("direct", edit_dist, length_diff)

            # Filter low confidence
            if confidence < 0.60:
                continue

            candidate = SynonymCandidate(
                hoofdterm=term,
                synoniem=redirect,
                confidence=confidence,
                source_type="redirect",
                wikipedia_url=f"{self.base_url}/wiki/{quote(redirect.replace(' ', '_'))}",
                metadata={
                    "redirect_type": "direct",
                    "edit_distance": edit_dist,
                    "length_diff": length_diff,
                },
            )
            candidates.append(candidate)

        # 2. Parse disambiguation page
        disambiguation_terms = await self.parse_disambiguation(term)
        for dis_term in disambiguation_terms:
            # Skip if already in redirects
            if any(c.synoniem.lower() == dis_term.lower() for c in candidates):
                continue

            edit_dist = self._calculate_edit_distance(term, dis_term)
            length_diff = abs(len(term) - len(dis_term))

            confidence = self.calculate_confidence(
                "disambiguation", edit_dist, length_diff
            )

            # Filter low confidence
            if confidence < 0.60:
                continue

            candidate = SynonymCandidate(
                hoofdterm=term,
                synoniem=dis_term,
                confidence=confidence,
                source_type="disambiguation",
                wikipedia_url=f"{self.base_url}/wiki/{quote(dis_term.replace(' ', '_'))}",
                metadata={
                    "redirect_type": "disambiguation",
                    "edit_distance": edit_dist,
                    "length_diff": length_diff,
                },
            )
            candidates.append(candidate)

        # 3. Sort by confidence (highest first)
        candidates.sort(key=lambda c: c.confidence, reverse=True)

        logger.info(f"Found {len(candidates)} synonym candidates for '{term}'")
        return candidates


# Standalone function voor convenience
async def extract_wikipedia_synonyms(
    term: str, language: str = "nl", rate_limit_delay: float = 1.0
) -> list[SynonymCandidate]:
    """
    Standalone functie om Wikipedia synoniemen te extraheren.

    Args:
        term: Juridische term
        language: Wikipedia taal code (default: nl)
        rate_limit_delay: Delay tussen requests (default: 1.0 sec)

    Returns:
        List of SynonymCandidate objects
    """
    async with WikipediaSynonymExtractor(
        language=language, rate_limit_delay=rate_limit_delay
    ) as extractor:
        result: list[SynonymCandidate] = await extractor.extract_synonyms(term)
        return result
