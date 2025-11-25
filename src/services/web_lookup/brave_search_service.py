"""
Brave Search API service voor moderne web lookup implementatie.

Integreert Brave Search via MCP tool voor hoogwaardige Nederlandse juridische zoekresultaten.
Gebruikt dezelfde LookupResult interface als andere providers voor naadloze integratie.
"""

import logging
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any, cast

from ..interfaces import LookupResult, WebSource

logger = logging.getLogger(__name__)


class BraveSearchService:
    """
    Service voor Brave Search API integratie via MCP.

    Implementeert moderne MCP-based approach voor web search lookup
    met focus op Nederlandse juridische bronnen.
    """

    def __init__(
        self,
        count: int = 5,
        enable_synonyms: bool = True,
        mcp_search_function: Any = None,
    ):
        """
        Initialiseer Brave Search service.

        Args:
            count: Aantal resultaten per query (default: 5, max: 20)
            enable_synonyms: Schakel synoniemen fallback in
            mcp_search_function: MCP search functie voor dependency injection (optioneel)
        """
        self.count = min(count, 20)  # Brave API max is 20
        self.enable_synonyms = enable_synonyms
        self._synonym_service = None
        self._mcp_search = mcp_search_function

        # Laad synoniemen service voor fallback (optioneel)
        if enable_synonyms:
            try:
                from .synonym_service import get_synonym_service

                self._synonym_service = get_synonym_service()
                logger.info("Brave Search synoniemen fallback ingeschakeld")
            except Exception as e:
                logger.warning(f"Kon synoniemen service niet laden: {e}")
                self._synonym_service = None

    async def __aenter__(self):
        """Async context manager entry - no session needed for MCP."""
        # Import MCP function here to avoid circular imports during init
        if self._mcp_search is None:
            try:
                # Dynamic import om circular dependency te voorkomen
                import inspect

                inspect.currentframe()
                # MCP functies zijn beschikbaar in de globals van de caller
                # maar voor testbaarheid accepteren we het ook via constructor
            except Exception:
                pass
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - no cleanup needed for MCP."""

    async def lookup(
        self, term: str, include_snippet: bool = True
    ) -> LookupResult | None:
        """
        Zoek een term op via Brave Search.

        Args:
            term: Zoekterm
            include_snippet: Include snippet als definitie

        Returns:
            LookupResult met Brave Search informatie, of None als geen resultaten
        """
        logger.info(f"Brave Search lookup voor term: {term}")

        try:
            # Primaire search
            result = await self._search(term)

            # SYNONYM FALLBACK: Als primaire search faalt, probeer synoniemen
            if not result and self._synonym_service:
                logger.info(
                    f"Primaire Brave Search gefaald, probeer synoniemen voor: {term}"
                )
                synoniemen = self._synonym_service.expand_query_terms(
                    term, max_synonyms=3
                )

                # Probeer elk synoniem (skip originele term)
                for synonym in synoniemen[1:]:
                    logger.debug(f"Brave Search synonym fallback: probeer '{synonym}'")
                    result = await self._search(synonym)
                    if result:
                        logger.info(
                            f"Brave Search match gevonden via synoniem: '{synonym}' voor '{term}'"
                        )
                        break

            if not result:
                logger.info(
                    f"Geen Brave Search resultaten gevonden voor: {term} (inclusief synoniemen)"
                )
                return None

            return result

        except Exception as e:
            logger.error(f"Brave Search lookup fout voor {term}: {e}")
            return LookupResult(
                term=term,
                source=WebSource(
                    name="Brave Search",
                    url="",
                    confidence=0.0,
                    api_type="brave_mcp",
                ),
                success=False,
                error_message=str(e),
            )

    async def _search(self, query: str) -> LookupResult | None:
        """
        Voer Brave Search uit via MCP tool.

        Args:
            query: Zoekquery

        Returns:
            LookupResult met beste match, of None
        """
        try:
            # MCP tool call - we kunnen de tool direct aanroepen vanuit async context
            # De tool wordt geïnjecteerd via de orchestrator/caller
            if self._mcp_search:
                results = await self._mcp_search(query=query, count=self.count)
            else:
                # Fallback: probeer directe import (alleen in runtime, niet tijdens tests)
                try:
                    from anthropic import AnthropicBedrock  # noqa: F401

                    # Als MCP tool beschikbaar is, gebruiken we die
                    # Anders retourneren we None (graceful degradation)
                    logger.warning(
                        "Brave Search MCP tool niet beschikbaar, skip search"
                    )
                    return None
                except ImportError:
                    logger.warning(
                        "Brave Search MCP tool niet beschikbaar, skip search"
                    )
                    return None

            # Parse MCP response (komt binnen als dict met Title, Description, URL)
            if not results or not isinstance(results, list):
                return None

            # Neem beste resultaat (eerste is meestal meest relevant)
            best_result = results[0] if results else None
            if not best_result:
                return None

            # Bouw LookupResult
            return self._build_lookup_result(query, best_result, position=0)

        except Exception as e:
            logger.error(f"Brave Search MCP call failed voor '{query}': {e}")
            return None

    def _build_lookup_result(
        self, term: str, result: dict[str, Any], position: int
    ) -> LookupResult:
        """
        Bouw LookupResult van Brave Search data.

        Args:
            term: Originele zoekterm
            result: Brave Search result dict (Title, Description, URL)
            position: Positie in resultaten (0 = beste)

        Returns:
            LookupResult object
        """
        title = result.get("Title", "")
        description = result.get("Description", "")
        url = result.get("URL", "")

        # Bereken confidence op basis van positie en title match
        confidence = self._calculate_confidence(term, title, description, position)

        # Gebruik description als definitie
        definition = description if description else None

        # Detecteer juridische bronnen
        is_juridical = self._is_juridical_source(url, title, description)

        # Build metadata
        retrieved_at = datetime.now(UTC).isoformat()
        content_hash = sha256(
            (description or "").encode("utf-8", errors="ignore")
        ).hexdigest()

        metadata = {
            "title": title,
            "search_position": position,
            "is_juridical": is_juridical,
            "retrieved_at": retrieved_at,
            "content_hash": content_hash,
            "search_engine": "brave",
        }

        return LookupResult(
            term=term,
            source=WebSource(
                name="Brave Search",
                url=url,
                confidence=confidence,
                is_juridical=is_juridical,
                api_type="brave_mcp",
            ),
            definition=definition,
            context=f"Brave Search: {title}",
            success=True,
            metadata=metadata,
        )

    def _calculate_confidence(
        self, term: str, title: str, description: str, position: int
    ) -> float:
        """
        Bereken confidence score op basis van match kwaliteit.

        Args:
            term: Zoekterm
            title: Resultaat title
            description: Resultaat description
            position: Positie in zoekresultaten (0-based)

        Returns:
            Confidence score (0.0-1.0)
        """
        term_lower = term.lower().strip()
        title_lower = title.lower().strip()
        desc_lower = description.lower().strip()

        # Base confidence op basis van positie
        # Positie 0 = 0.90, positie 1 = 0.85, etc.
        base_confidence = max(0.60, 0.90 - (position * 0.05))

        # Boost voor exacte title match
        if title_lower == term_lower:
            return min(0.98, base_confidence + 0.10)

        # Boost voor title prefix match
        if title_lower.startswith(term_lower):
            return min(0.95, base_confidence + 0.08)

        # Boost voor term in title
        if term_lower in title_lower:
            return min(0.92, base_confidence + 0.05)

        # Boost voor term in description
        if term_lower in desc_lower:
            return min(0.88, base_confidence + 0.03)

        # Default: base confidence
        return base_confidence

    def _is_juridical_source(self, url: str, title: str, description: str) -> bool:
        """
        Detecteer of een bron juridisch is.

        Args:
            url: URL van de bron
            title: Titel van de bron
            description: Beschrijving van de bron

        Returns:
            True als de bron waarschijnlijk juridisch is
        """
        # Bekende Nederlandse juridische domeinen
        juridical_domains = [
            "overheid.nl",
            "rechtspraak.nl",
            "wetten.nl",
            "wetboek-online.nl",
            "denederlandsegrondwet.nl",
            "officielebekendmakingen.nl",
            "cbs.nl",  # CBS definities zijn vaak juridisch relevant
            "rijksoverheid.nl",
            "om.nl",  # Openbaar Ministerie
            "politie.nl",
        ]

        # Check domain
        url_lower = url.lower()
        if any(domain in url_lower for domain in juridical_domains):
            return True

        # Check juridische keywords in title/description
        juridical_keywords = [
            "juridisch",
            "rechts",
            "wetboek",
            "artikel",
            "wet-",
            "burgerlijk",
            "strafrecht",
            "civiel",
            "grondwet",
            "rechtspraak",
            "uitspraak",
        ]

        combined_text = f"{title} {description}".lower()
        return bool(any(keyword in combined_text for keyword in juridical_keywords))


# Standalone functie voor gebruik in bestaande code
async def brave_search_lookup(
    term: str, count: int = 5, mcp_search_function: Any = None
) -> LookupResult | None:
    """
    Standalone Brave Search lookup functie.

    Args:
        term: Zoekterm
        count: Aantal resultaten (max 20)
        mcp_search_function: MCP search functie voor dependency injection

    Returns:
        LookupResult of None
    """
    async with BraveSearchService(
        count=count, mcp_search_function=mcp_search_function
    ) as service:
        result = await service.lookup(term)
        return cast("LookupResult | None", result)
