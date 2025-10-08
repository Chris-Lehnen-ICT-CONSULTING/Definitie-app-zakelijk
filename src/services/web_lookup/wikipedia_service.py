"""
Wikipedia API service voor moderne web lookup implementatie.

Proof of concept voor MediaWiki API integratie als onderdeel van het
Strangler Fig pattern voor web lookup modernisering.
"""

import logging
from typing import Any
from urllib.parse import quote

# Probeer aiohttp te importeren, fallback voor testing
try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("Warning: aiohttp niet beschikbaar - Wikipedia service werkt niet volledig")

from datetime import UTC, datetime

from ..interfaces import LookupResult, WebSource

logger = logging.getLogger(__name__)


class WikipediaService:
    """
    Service voor Wikipedia API integratie.

    Implementeert moderne async approach voor Wikipedia lookup
    als proof of concept voor het vervangen van legacy scrapers.
    """

    def __init__(self, language: str = "nl", enable_synonyms: bool = True):
        self.language = language
        self.base_url = f"https://{language}.wikipedia.org"
        self.api_url = f"{self.base_url}/w/api.php"
        self.rest_url = f"{self.base_url}/api/rest_v1"
        self.session: aiohttp.ClientSession | None = None

        # User agent voor Wikipedia API (vereist)
        self.headers = {
            "User-Agent": "DefinitieApp/1.0 (https://github.com/definitie-app; support@definitie-app.nl)"
        }

        # Synoniemen service voor fallback (optioneel)
        self.enable_synonyms = enable_synonyms
        self._synonym_service = None
        if enable_synonyms:
            try:
                from .synonym_service import get_synonym_service

                self._synonym_service = get_synonym_service()
                logger.info("Wikipedia synoniemen fallback ingeschakeld")
            except Exception as e:
                logger.warning(f"Kon synoniemen service niet laden: {e}")
                self._synonym_service = None

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

    async def lookup(
        self, term: str, include_extract: bool = True
    ) -> LookupResult | None:
        """
        Zoek een term op in Wikipedia.

        Args:
            term: Zoekterm
            include_extract: Include page extract als definitie

        Returns:
            LookupResult met Wikipedia informatie
        """
        if not AIOHTTP_AVAILABLE:
            return LookupResult(
                term=term,
                source=WebSource(
                    name="Wikipedia", url="", confidence=0.0, api_type="mediawiki"
                ),
                success=False,
                error_message="aiohttp niet beschikbaar",
            )

        if not self.session:
            msg = "Service moet gebruikt worden als async context manager"
            raise RuntimeError(msg)

        logger.info(f"Wikipedia lookup voor term: {term}")

        try:
            # Zoek naar pagina met beste match (kwaliteit > generieke hits)
            page_info = await self._search_page(term)

            # SYNONYM FALLBACK: Als primaire search faalt, probeer synoniemen
            if not page_info and self._synonym_service:
                logger.info(
                    f"Primaire Wikipedia search gefaald, probeer synoniemen voor: {term}"
                )
                synoniemen = self._synonym_service.expand_query_terms(
                    term, max_synonyms=3
                )

                # Probeer elk synoniem (skip originele term, die hebben we al geprobeerd)
                for synonym in synoniemen[1:]:
                    logger.debug(f"Wikipedia synonym fallback: probeer '{synonym}'")
                    page_info = await self._search_page(synonym)
                    if page_info:
                        logger.info(
                            f"Wikipedia match gevonden via synoniem: '{synonym}' voor '{term}'"
                        )
                        break

            if not page_info:
                logger.info(
                    f"Geen Wikipedia pagina gevonden voor: {term} (inclusief synoniemen)"
                )
                return None

            # Haal pagina details op
            page_details = await self._get_page_details(page_info["title"])

            # Sla disambiguation-pagina's over (te weinig inhoudelijk bruikbaar)
            if page_details and page_details.get("type") == "disambiguation":
                logger.info(
                    "Wikipedia disambiguation page skipped: %s", page_info["title"]
                )
                return None

            if not page_details:
                logger.warning(
                    f"Kon pagina details niet ophalen voor: {page_info['title']}"
                )
                return None

            # Bouw LookupResult
            return self._build_lookup_result(term, page_info, page_details)

        except Exception as e:
            logger.error(f"Wikipedia lookup fout voor {term}: {e}")
            return LookupResult(
                term=term,
                source=WebSource(
                    name="Wikipedia", url="", confidence=0.0, api_type="mediawiki"
                ),
                success=False,
                error_message=str(e),
            )

    async def _search_page(self, term: str) -> dict[str, Any] | None:
        """Zoek naar beste match pagina met eenvoudige scoringsheuristiek."""
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": term,
            "srlimit": 5,
            "srprop": "titlesnippet|snippet",
        }

        async with self.session.get(self.api_url, params=params) as response:
            if response.status != 200:
                logger.error(f"Wikipedia search API error: {response.status}")
                return None

            data = await response.json()
            search_results = data.get("query", {}).get("search", [])

            if not search_results:
                return None

            # Kies beste kandidaat: exacte titelmatch > prefixmatch > woordgrensmatch > overige
            t = term.lower().strip()

            def score(res: dict[str, Any]) -> int:
                title = str(res.get("title", "")).strip().lower()
                if title == t:
                    return 100
                if title.startswith(t):
                    return 90
                # Woordgrensmatch
                if f" {t} " in f" {title} ":
                    return 70
                return 10

            best = max(search_results, key=score)
            # Als de beste score erg laag is, liever geen Wikipedia-resultaat gebruiken
            if score(best) < 50:
                return None
            return best

    async def _get_page_details(self, title: str) -> dict[str, Any] | None:
        """Haal pagina details op via REST API."""
        encoded_title = quote(title.replace(" ", "_"), safe="")
        url = f"{self.rest_url}/page/summary/{encoded_title}"

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                if response.status == 404:
                    logger.info(f"Wikipedia pagina niet gevonden: {title}")
                    return None
                logger.error(
                    f"Wikipedia REST API error {response.status} voor: {title}"
                )
                return None

        except Exception as e:
            logger.error(f"Error fetching page details voor {title}: {e}")
            return None

    def _build_lookup_result(
        self, term: str, page_info: dict[str, Any], page_details: dict[str, Any]
    ) -> LookupResult:
        """Bouw LookupResult van Wikipedia data."""

        # Bereken confidence based op title match
        title = page_info["title"].lower()
        term_lower = term.lower()

        if title == term_lower:
            confidence = 0.95
        elif term_lower in title or title in term_lower:
            confidence = 0.85
        else:
            confidence = 0.70

        # Extract definitie tekst
        definition = page_details.get("extract", "")

        # Haal first sentence als korte definitie
        if definition and "." in definition:
            first_sentence = definition.split(".")[0] + "."
            if len(first_sentence) < len(definition) * 0.3:  # Als eerste zin kort is
                definition = first_sentence

        # Build metadata
        from hashlib import sha256

        retrieved_at = datetime.now(UTC).isoformat()
        content_hash = sha256(
            (definition or "").encode("utf-8", errors="ignore")
        ).hexdigest()

        metadata = {
            "wikipedia_page_id": page_details.get("pageid"),
            "wikipedia_title": page_details.get("title"),
            "language": self.language,
            "page_type": page_details.get("type", "standard"),
            "last_modified": page_details.get("timestamp"),
            "coordinates": page_details.get("coordinates"),
            "disambiguation": page_details.get("type") == "disambiguation",
            "retrieved_at": retrieved_at,
            "content_hash": content_hash,
        }

        # Add thumbnail if available
        if "thumbnail" in page_details:
            metadata["thumbnail"] = page_details["thumbnail"]["source"]

        return LookupResult(
            term=term,
            source=WebSource(
                name="Wikipedia",
                url=page_details.get("content_urls", {})
                .get("desktop", {})
                .get("page", ""),
                confidence=confidence,
                is_juridical=False,
                api_type="mediawiki",
            ),
            definition=definition,
            context=f"Wikipedia pagina: {page_details.get('title', '')}",
            success=True,
            metadata=metadata,
        )

    async def get_page_categories(self, title: str) -> list[str]:
        """Haal categorieën van een pagina op."""
        params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "categories",
            "cllimit": 50,
        }

        try:
            async with self.session.get(self.api_url, params=params) as response:
                if response.status != 200:
                    return []

                data = await response.json()
                pages = data.get("query", {}).get("pages", {})

                for page_data in pages.values():
                    categories = page_data.get("categories", [])
                    return [
                        cat["title"].replace("Categorie:", "") for cat in categories
                    ]

                return []

        except Exception as e:
            logger.error(f"Error fetching categories voor {title}: {e}")
            return []

    async def suggest_search_terms(self, partial_term: str) -> list[str]:
        """Suggesties voor zoektermen."""
        params = {
            "action": "opensearch",
            "format": "json",
            "search": partial_term,
            "limit": 10,
        }

        try:
            async with self.session.get(self.api_url, params=params) as response:
                if response.status != 200:
                    return []

                data = await response.json()
                # OpenSearch returns [query, [suggestions], [descriptions], [urls]]
                return data[1] if len(data) > 1 else []

        except Exception as e:
            logger.error(f"Error getting suggestions voor {partial_term}: {e}")
            return []


# Standalone functies voor gebruik in bestaande code
async def wikipedia_lookup(term: str, language: str = "nl") -> LookupResult | None:
    """
    Standalone Wikipedia lookup functie.

    Args:
        term: Zoekterm
        language: Wikipedia taal code (default: nl)

    Returns:
        LookupResult of None
    """
    async with WikipediaService(language) as service:
        return await service.lookup(term)


async def wikipedia_suggestions(partial_term: str, language: str = "nl") -> list[str]:
    """
    Standalone Wikipedia suggesties functie.

    Args:
        partial_term: Gedeeltelijke zoekterm
        language: Wikipedia taal code (default: nl)

    Returns:
        Lijst van suggesties
    """
    async with WikipediaService(language) as service:
        return await service.suggest_search_terms(partial_term)
