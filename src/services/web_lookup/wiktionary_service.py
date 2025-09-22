"""
Wiktionary API service voor moderne web lookup implementatie.

Implementeert een lichte integratie met de MediaWiki API van
nl.wiktionary.org om een korte definitie op te halen.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback voor omgevingen zonder aiohttp
    AIOHTTP_AVAILABLE = False
    print("Warning: aiohttp niet beschikbaar - Wiktionary service niet actief")

from datetime import UTC, datetime

from ..interfaces import LookupResult, WebSource

logger = logging.getLogger(__name__)


class WiktionaryService:
    """Service voor Wiktionary (nl) via MediaWiki API."""

    def __init__(self, language: str = "nl"):
        self.language = language
        self.base_url = f"https://{language}.wiktionary.org"
        self.api_url = f"{self.base_url}/w/api.php"
        self.session: aiohttp.ClientSession | None = None
        self.headers = {
            "User-Agent": "DefinitieApp/1.0 (https://github.com/definitie-app; support@definitie-app.nl)",
        }

    async def __aenter__(self):
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp vereist voor WiktionaryService")
        self.session = aiohttp.ClientSession(
            headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def lookup(self, term: str) -> LookupResult | None:
        """Zoek een lemma en retourneer een korte tekstuele definitie."""
        if not AIOHTTP_AVAILABLE:
            return LookupResult(
                term=term,
                source=WebSource(
                    name="Wiktionary", url="", confidence=0.0, api_type="mediawiki"
                ),
                success=False,
                error_message="aiohttp niet beschikbaar",
            )

        if not self.session:
            raise RuntimeError("Service moet gebruikt worden als async context manager")

        try:
            page = await self._search_page(term)
            if not page:
                return None
            title = str(page.get("title", "")).strip()
            extract = await self._get_extract(title)
            if not extract:
                return None

            # Heuristische confidence: exacte titel > bevat-term > anders
            t = term.lower().strip()
            tl = title.lower()
            if tl == t:
                conf = 0.85
            elif t in tl or tl in t:
                conf = 0.75
            else:
                conf = 0.6

            url = f"{self.base_url}/wiki/{quote(title.replace(' ', '_'), safe='')}"

            # Beperk extract tot een compact snippet
            snippet = extract.strip()
            if len(snippet) > 500:
                snippet = snippet[:500].rstrip() + "…"

            # Metadata
            from hashlib import sha256

            retrieved_at = datetime.now(UTC).isoformat()
            content_hash = sha256(snippet.encode("utf-8", errors="ignore")).hexdigest()

            metadata = {
                "wiktionary_title": title,
                "language": self.language,
                "retrieved_at": retrieved_at,
                "content_hash": content_hash,
            }

            return LookupResult(
                term=term,
                source=WebSource(
                    name="Wiktionary",
                    url=url,
                    confidence=conf,
                    is_juridical=False,
                    api_type="mediawiki",
                ),
                definition=snippet,
                context=f"Wiktionary lemma: {title}",
                success=True,
                metadata=metadata,
            )
        except Exception as e:  # pragma: no cover - beschermt tegen onverwachte API-issues
            logger.error("Wiktionary lookup error for %s: %s", term, e)
            return None

    async def _search_page(self, term: str) -> dict[str, Any] | None:
        """Zoek naar het beste lemma met eenvoudige scoringsheuristiek."""
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": term,
            "srlimit": 5,
            "srprop": "snippet|titlesnippet",
        }
        async with self.session.get(self.api_url, params=params) as resp:
            if resp.status != 200:
                logger.error("Wiktionary search API error: %s", resp.status)
                return None
            data = await resp.json()
            results = data.get("query", {}).get("search", [])
            if not results:
                return None

            t = term.lower().strip()

            def score(r: dict[str, Any]) -> int:
                title = str(r.get("title", "")).strip().lower()
                if title == t:
                    return 100
                if title.startswith(t):
                    return 90
                if f" {t} " in f" {title} ":
                    return 70
                return 10

            best = max(results, key=score)
            return best if score(best) >= 30 else None

    async def _get_extract(self, title: str) -> str | None:
        """Haal een korte tekst uit het lemma. Prefer plaintext extract; fallback naar wikitext-parse."""
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "explaintext": 1,
            "exintro": 1,
            "titles": title,
        }
        async with self.session.get(self.api_url, params=params) as resp:
            if resp.status != 200:
                return await self._extract_from_wikitext(title)
            data = await resp.json()
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                extract = page.get("extract")
                if extract:
                    # Knip na eerste lege regel / sectiescheiding
                    text = str(extract).strip()
                    # Probeer hoofddefinitie (eerste regel) te pakken
                    first = text.split("\n", 1)[0].strip()
                    return first or text
            # Fallback: parse wikitext en haal eerste definitie
            return await self._extract_from_wikitext(title)

    async def _extract_from_wikitext(self, title: str) -> str | None:
        """Fallback: haal wikitext op en parse eerste definitieregel (# ...)."""
        params = {
            "action": "parse",
            "format": "json",
            "prop": "wikitext",
            "page": title,
        }
        async with self.session.get(self.api_url, params=params) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            wtxt = (
                data.get("parse", {})
                .get("wikitext", {})
                .get("*", "")
            )
            if not wtxt:
                return None

            # Heuristisch: focus op '== Nederlands ==' sectie
            text = str(wtxt)
            lower = text.lower()
            start = lower.find("== nederlands ==")
            if start != -1:
                segment = text[start:]
            else:
                segment = text

            # Pak eerste regel die met '# ' begint (definitie)
            first_def: str | None = None
            for line in segment.splitlines():
                s = line.strip()
                if s.startswith("# "):
                    first_def = s[2:].strip()
                    break
            if not first_def:
                return None

            # Eenvoudige wikimarkup-strip: [[link|label]] / [[link]] / ''italic'' / '''bold'''
            import re

            def _replace_link(m: re.Match[str]) -> str:
                inner = m.group(1)
                if "|" in inner:
                    return inner.split("|")[-1]
                return inner

            s = re.sub(r"\[\[([^\]]+)\]\]", _replace_link, first_def)
            s = re.sub(r"'''+(.*?)'''+", r"\1", s)
            s = re.sub(r"''(.*?)''", r"\1", s)
            s = re.sub(r"\{\{[^}]+\}\}", "", s)  # templates verwijderen
            return s.strip() or None


async def wiktionary_lookup(term: str, language: str = "nl") -> LookupResult | None:
    """Standalone lookup helper."""
    async with WiktionaryService(language) as svc:
        return await svc.lookup(term)
