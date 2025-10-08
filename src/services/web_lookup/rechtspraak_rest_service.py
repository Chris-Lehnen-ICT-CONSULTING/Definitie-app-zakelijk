"""
Rechtspraak Open Data (REST) service.

Implementeert ECLI-gebaseerde lookup via data.rechtspraak.nl.
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from typing import Any

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except Exception:  # pragma: no cover
    AIOHTTP_AVAILABLE = False

from datetime import UTC, datetime

from ..interfaces import LookupResult, WebSource

logger = logging.getLogger(__name__)


ECLI_RE = re.compile(r"\bECLI:[A-Z]{2}:[A-Z0-9]+:[0-9]{4}:[A-Z0-9]+\b", re.IGNORECASE)


class RechtspraakRESTService:
    """Client voor Rechtspraak Open Data (REST)."""

    def __init__(self, base_url: str = "https://data.rechtspraak.nl"):
        self.base_url = base_url.rstrip("/")
        self.session: aiohttp.ClientSession | None = None
        self.headers = {
            "User-Agent": "DefinitieApp-Rechtspraak/1.0 (https://github.com/definitie-app; support@definitie-app.nl)",
            "Accept": "application/xml, application/rdf+xml;q=0.9, */*;q=0.8",
        }

    async def __aenter__(self):
        if not AIOHTTP_AVAILABLE:  # pragma: no cover
            raise RuntimeError("aiohttp vereist voor Rechtspraak REST service")
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=20),
            trust_env=True,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()

    async def fetch_by_ecli(self, ecli: str) -> LookupResult | None:
        if not self.session:
            raise RuntimeError("Service moet gebruikt worden als async context manager")

        # Content endpoint; META retourneert vooral metadata
        url = f"{self.base_url}/uitspraken/content"
        params = {"id": ecli, "return": "META"}
        try:
            async with self.session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.info("Rechtspraak REST %s voor %s", resp.status, ecli)
                    return None
                xml_text = await resp.text()
        except Exception as e:  # pragma: no cover
            logger.warning("Rechtspraak REST error for %s: %s", ecli, e)
            return None

        # Parse RDF/XML tolerant op local-names
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return None

        def _find_local(first: ET.Element, locals: tuple[str, ...]) -> str:
            for el in first.iter():
                tag = el.tag
                if "}" in tag:
                    tag = tag.split("}", 1)[1]
                if tag.lower() in {x.lower() for x in locals} and el.text:
                    return el.text.strip()
            return ""

        title = _find_local(root, ("title", "naam", "label")) or ecli
        abstract = _find_local(root, ("abstract", "omschrijving", "description"))
        date = _find_local(root, ("date", "issued", "datum"))

        snippet = abstract or f"Uitspraak {ecli}".strip()
        if len(snippet) > 600:
            snippet = snippet[:600].rstrip() + "…"

        # Probeer canonical publieks-URL te bouwen (portaal). Val terug op data endpoint
        public_url = f"https://uitspraken.rechtspraak.nl/#!/details?id={ecli}"

        from hashlib import sha256

        retrieved_at = datetime.now(UTC).isoformat()
        content_hash = sha256(
            (snippet or title).encode("utf-8", errors="ignore")
        ).hexdigest()

        metadata: dict[str, Any] = {
            "dc_identifier": ecli,
            "dc_title": title,
            "dc_date": date,
            "retrieved_at": retrieved_at,
            "content_hash": content_hash,
            "provider": "Rechtspraak Open Data",
        }

        return LookupResult(
            term=ecli,
            source=WebSource(
                name="Rechtspraak.nl",
                url=public_url,
                confidence=0.85,
                is_juridical=True,
                api_type="rest",
            ),
            definition=snippet,
            context=f"Rechtspraak Open Data — {title}",
            success=True,
            metadata=metadata,
        )


async def rechtspraak_lookup(term: str) -> LookupResult | None:
    """
    ECLI-gedreven lookup; retourneert None als geen ECLI in term.

    BELANGRIJK: Rechtspraak.nl REST API heeft GEEN full-text search.
    Deze functie werkt ALLEEN voor expliciete ECLI's (bijv. "ECLI:NL:HR:2023:1234").

    Voor algemene juridische begrippen (bijv. "onherroepelijk vonnis") retourneert
    deze functie None, omdat de API dan random recente uitspraken zou geven
    die NIET relevant zijn voor definitiegeneratie.

    Use case: User vraagt specifieke uitspraak op basis van ECLI.
    NOT for: Algemene begripsuitleg (gebruik Wikipedia/Overheid.nl hiervoor).
    """
    m = ECLI_RE.search(term or "")
    if not m:
        # Geen ECLI gevonden - skip Rechtspraak (geen nuttige results zonder full-text search)
        logger.debug(
            f"Rechtspraak lookup skipped voor '{term}': geen ECLI gedetecteerd. "
            "API ondersteunt geen full-text search."
        )
        return None

    # ECLI gevonden - haal specifieke uitspraak op
    ecli = m.group(0).upper()
    logger.info(f"Rechtspraak ECLI lookup: {ecli}")
    async with RechtspraakRESTService() as svc:
        return await svc.fetch_by_ecli(ecli)
