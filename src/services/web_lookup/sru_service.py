"""
SRU (Search/Retrieve via URL) service voor Nederlandse juridische bronnen.

Implementeert moderne async approach voor overheid.nl en rechtspraak.nl
als onderdeel van het Strangler Fig pattern voor web lookup modernisering.
"""

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from urllib.parse import quote_plus, urlencode

# Probeer aiohttp te importeren, fallback voor testing
try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("Warning: aiohttp niet beschikbaar - SRU service werkt niet volledig")

from datetime import UTC

UTC = UTC  # Python 3.10 compatibility

from ..interfaces import LookupResult, WebSource

logger = logging.getLogger(__name__)


@dataclass
class SRUConfig:
    """Configuratie voor een SRU endpoint."""

    name: str
    base_url: str
    default_collection: str
    record_schema: str = "dc"  # Dublin Core default
    maximum_records: int = 10
    confidence_weight: float = 1.0
    is_juridical: bool = True
    # Alternatieve endpoints (fallbacks) voor wanneer het primaire pad 404/5xx geeft
    alt_base_urls: list[str] = field(default_factory=list)


class SRUService:
    """
    Service voor SRU API integratie met Nederlandse overheids- en juridische bronnen.

    Ondersteunt:
    - overheid.nl (officiële wetgeving en documenten)
    - rechtspraak.nl (jurisprudentie en uitspraken)
    - zoekoperatie.overheid.nl (zoekservice)
    """

    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
        self.endpoints = self._setup_endpoints()

        # User agent voor SRU requests
        self.headers = {
            "User-Agent": "DefinitieApp-SRU/1.0 (https://github.com/definitie-app; support@definitie-app.nl)"
        }

    def _setup_endpoints(self) -> dict[str, SRUConfig]:
        """Configureer alle SRU endpoints."""
        return {
            "overheid": SRUConfig(
                name="Overheid.nl",
                base_url="https://repository.overheid.nl/sru",
                default_collection="rijksoverheid",
                record_schema="dc",
                confidence_weight=1.0,
                is_juridical=True,
            ),
            "rechtspraak": SRUConfig(
                name="Rechtspraak.nl",
                # Primair werkend SRU‑endpoint (Search)
                base_url="https://zoeken.rechtspraak.nl/SRU/Search",
                default_collection="",  # Rechtspraak heeft geen collectie parameter
                record_schema="dc",
                confidence_weight=0.95,
                is_juridical=True,
                alt_base_urls=[
                    # Alternatieve paden (case‑varianten en data endpoint)
                    "https://zoeken.rechtspraak.nl/sru/Search",
                    "https://data.rechtspraak.nl/uitspraken/sru",
                ],
            ),
            "wetgeving_nl": SRUConfig(
                name="Wetgeving.nl",
                base_url="https://wetten.overheid.nl/SRU/Search",
                default_collection="",
                record_schema="dc",
                confidence_weight=0.9,
                is_juridical=True,
                alt_base_urls=[
                    "https://wetten.overheid.nl/sru/Search",
                    "https://wetten.overheid.nl/sru",
                ],
            ),
            "overheid_zoek": SRUConfig(
                name="Overheid.nl Zoekservice",
                base_url="https://zoekservice.overheid.nl/sru/Search",
                default_collection="rijksoverheid",
                record_schema="gzd",  # Government Zoekmachine Dublin Core
                confidence_weight=0.85,
                is_juridical=True,
            ),
        }

    async def __aenter__(self):
        """Async context manager entry."""
        if not AIOHTTP_AVAILABLE:
            msg = "aiohttp is vereist voor SRU service"
            raise RuntimeError(msg)

        self.session = aiohttp.ClientSession(
            headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def search(
        self,
        term: str,
        endpoint: str = "overheid",
        max_records: int = 5,
        collection: str | None = None,
    ) -> list[LookupResult]:
        """
        Zoek een term in een SRU endpoint.

        Args:
            term: Zoekterm
            endpoint: SRU endpoint ("overheid", "rechtspraak", "overheid_zoek")
            max_records: Maximum aantal resultaten
            collection: Specifieke collectie (optioneel)

        Returns:
            Lijst van LookupResult objecten
        """
        if not AIOHTTP_AVAILABLE:
            logger.error("aiohttp niet beschikbaar voor SRU search")
            return []

        if not self.session:
            msg = "Service moet gebruikt worden als async context manager"
            raise RuntimeError(msg)

        if endpoint not in self.endpoints:
            logger.error(f"Onbekend SRU endpoint: {endpoint}")
            return []

        config = self.endpoints[endpoint]
        logger.info(f"SRU search voor '{term}' in {config.name}")

        try:
            # Helper om 1 query (string) tegen alle endpoints te proberen
            async def _try_query(query_str: str) -> list[LookupResult]:
                from urllib.parse import urlencode, quote_plus

                # Primary URL
                params = {
                    "operation": "searchRetrieve",
                    "version": "1.2",
                    "recordSchema": config.record_schema,
                    "maximumRecords": min(max_records, config.maximum_records),
                    "query": query_str,
                    "startRecord": "1",
                }
                urls: list[str] = [
                    f"{config.base_url}?{urlencode(params, quote_via=quote_plus)}"
                ]
                for alt in (config.alt_base_urls or []):
                    try:
                        urls.append(f"{alt}?{urlencode(params, quote_via=quote_plus)}")
                    except Exception:
                        continue

                last_status: int | None = None
                last_text: str | None = None
                for u in urls:
                    async with self.session.get(u) as response:
                        if response.status == 200:
                            xml_content = await response.text()
                            parsed = self._parse_sru_response(xml_content, term, config)
                            if parsed:
                                return parsed
                        else:
                            last_status = response.status
                            try:
                                txt = await response.text()
                                last_text = txt[:200]
                            except Exception:
                                last_text = None
                # Nothing found for this query across endpoints
                if last_status and last_status != 200:
                    logger.error(
                        f"SRU API error {last_status} voor {config.name} (query fallback)."
                        + (f" Body preview: {last_text}" if last_text else "")
                    )
                return []

            # Query 1: onze standaard DC-velden (exact/contains per server-choice)
            base_query = self._build_cql_query(term, collection or config.default_collection)
            results = await _try_query(base_query)
            if results:
                return results

            # Query 2: serverChoice (breder) — verhoogt trefkans bij Rechtspraak
            escaped = term.replace('"', '\\"')
            sc_query = f'cql.serverChoice all "{escaped}"'
            results = await _try_query(sc_query)
            if results:
                return results

            # Query 3: hyphen-variant bij samengestelde termen
            if " " in term and "-" not in term:
                hyphen = term.replace(" ", "-")
                hy_query = f'cql.serverChoice all "{hyphen.replace("\"", "\\\"")}"'
                results = await _try_query(hy_query)
                if results:
                    return results

            # Geen resultaten
            return []

        except Exception as e:
            logger.error(f"SRU search error voor {term} in {config.name}: {e}")
            return []

    def _build_query_url(
        self,
        term: str,
        config: SRUConfig,
        max_records: int,
        collection: str | None = None,
    ) -> str:
        """Bouw SRU query URL."""
        # SRU parameters
        params = {
            "operation": "searchRetrieve",
            "version": "1.2",
            "recordSchema": config.record_schema,
            "maximumRecords": min(max_records, config.maximum_records),
            "query": self._build_cql_query(
                term, collection or config.default_collection
            ),
        }

        # Voeg startRecord toe voor paging (future enhancement)
        params["startRecord"] = "1"

        # Build URL
        query_string = urlencode(params, quote_via=quote_plus)
        return f"{config.base_url}?{query_string}"

    def _build_cql_query(self, term: str, collection: str) -> str:
        """
        Bouw CQL (Contextual Query Language) query.

        CQL is de standaard query taal voor SRU.
        """
        # Escape speciale karakters in term
        escaped_term = term.replace('"', '\\"')

        # Basis query - zoek in titel en inhoud
        # Gebruik contains-achtige matching door wildcard te ondersteunen indien endpoint dit toelaat.
        # Conservatief: probeer exact, maar laat SRU server-choice ook toe.
        base_query = (
            f'(dc.title="{escaped_term}" OR dc.subject="{escaped_term}" OR dc.description="{escaped_term}")'
        )

        # Voeg collectie filter toe als specifiek
        if collection:
            base_query = f'{base_query} AND overheidnl.collection="{collection}"'

        return base_query

    def _parse_sru_response(
        self, xml_content: str, term: str, config: SRUConfig
    ) -> list[LookupResult]:
        """Parse SRU XML response naar LookupResult objecten."""
        try:
            root = ET.fromstring(xml_content)

            # SRU namespace handling
            namespaces = {
                "srw": "http://www.loc.gov/zing/srw/",
                "dc": "http://purl.org/dc/elements/1.1/",
                "dcterms": "http://purl.org/dc/terms/",
            }

            # Find records
            records = root.findall(".//srw:record", namespaces)
            results = []

            for record in records:
                result = self._parse_record(record, term, config, namespaces)
                if result:
                    results.append(result)

            # Sorteer op relevantie (title match eerst)
            results.sort(key=lambda r: r.source.confidence, reverse=True)

            logger.info(f"Parsed {len(results)} results from {config.name}")
            return results

        except ET.ParseError as e:
            logger.error(f"XML parse error voor {config.name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing {config.name} response: {e}")
            return []

    def _parse_record(
        self,
        record: ET.Element,
        term: str,
        config: SRUConfig,
        namespaces: dict[str, str],
    ) -> LookupResult | None:
        """Parse een individueel SRU record."""
        try:
            # Extract Dublin Core metadata
            title_elem = record.find(".//dc:title", namespaces)
            description_elem = record.find(".//dc:description", namespaces)
            identifier_elem = record.find(".//dc:identifier", namespaces)
            subject_elem = record.find(".//dc:subject", namespaces)
            type_elem = record.find(".//dc:type", namespaces)
            date_elem = record.find(".//dc:date", namespaces)

            # Extract values
            title = (
                title_elem.text.strip()
                if title_elem is not None and title_elem.text
                else ""
            )
            description = (
                description_elem.text.strip()
                if description_elem is not None and description_elem.text
                else ""
            )
            identifier = (
                identifier_elem.text.strip()
                if identifier_elem is not None and identifier_elem.text
                else ""
            )
            subject = (
                subject_elem.text.strip()
                if subject_elem is not None and subject_elem.text
                else ""
            )
            doc_type = (
                type_elem.text.strip()
                if type_elem is not None and type_elem.text
                else ""
            )
            date = (
                date_elem.text.strip()
                if date_elem is not None and date_elem.text
                else ""
            )

            # Skip als geen titel of beschrijving
            if not title and not description:
                return None

            # Bereken confidence based op term matching
            confidence = self._calculate_confidence(
                term, title, description, subject, config
            )

            # Build URL (gebruik identifier als beschikbaar)
            url = identifier if identifier.startswith(("http://", "https://")) else ""

            # Build definitie tekst
            definition_parts = []
            if description:
                definition_parts.append(description)
            if subject and subject not in description:
                definition_parts.append(f"Onderwerp: {subject}")

            definition = ". ".join(definition_parts) if definition_parts else title

            # Build metadata
            from datetime import datetime
            from hashlib import sha256

            content_hash = sha256(
                (identifier or title or description or term or "").encode(
                    "utf-8", errors="ignore"
                )
            ).hexdigest()

            metadata = {
                "sru_endpoint": config.name,
                "dc_title": title,
                "dc_subject": subject,
                "dc_type": doc_type,
                "dc_date": date,
                "dc_identifier": identifier,
                "record_schema": config.record_schema,
                "retrieved_at": datetime.now(UTC).isoformat(),
                "content_hash": content_hash,
            }

            return LookupResult(
                term=term,
                source=WebSource(
                    name=config.name,
                    url=url,
                    confidence=confidence,
                    is_juridical=config.is_juridical,
                    api_type="sru",
                ),
                definition=definition,
                context=f"{config.name} - {doc_type}" if doc_type else config.name,
                success=True,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error parsing individual record: {e}")
            return None

    def _calculate_confidence(
        self, term: str, title: str, description: str, subject: str, config: SRUConfig
    ) -> float:
        """Bereken confidence score voor een SRU result."""
        base_confidence = 0.5
        term_lower = term.lower()

        # Title match (hoogste score)
        if title and term_lower in title.lower():
            if term_lower == title.lower().strip():
                base_confidence = 0.95  # Exact match
            else:
                base_confidence = 0.85  # Partial title match

        # Subject match
        elif subject and term_lower in subject.lower():
            base_confidence = 0.80

        # Description match
        elif description and term_lower in description.lower():
            base_confidence = 0.70

        # Pas confidence weight toe
        final_confidence = base_confidence * config.confidence_weight

        # Clamp tussen 0 en 1
        return max(0.0, min(1.0, final_confidence))

    async def search_legislation(
        self, term: str, max_records: int = 5
    ) -> list[LookupResult]:
        """Specifieke zoekfunctie voor wetgeving."""
        return await self.search(
            term=term,
            endpoint="overheid",
            max_records=max_records,
            collection="rijksoverheid",
        )

    async def search_jurisprudence(
        self, term: str, max_records: int = 5
    ) -> list[LookupResult]:
        """Specifieke zoekfunctie voor jurisprudentie."""
        return await self.search(
            term=term, endpoint="rechtspraak", max_records=max_records
        )

    async def search_all_sources(
        self, term: str, max_records_per_source: int = 3
    ) -> list[LookupResult]:
        """Zoek in alle beschikbare SRU bronnen."""
        all_results = []

        for endpoint in self.endpoints:
            try:
                results = await self.search(term, endpoint, max_records_per_source)
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Search in {endpoint} failed: {e}")
                continue

        # Sorteer alle resultaten op confidence
        all_results.sort(key=lambda r: r.source.confidence, reverse=True)

        return all_results

    def get_available_endpoints(self) -> list[str]:
        """Geef lijst van beschikbare SRU endpoints."""
        return list(self.endpoints.keys())

    def get_endpoint_config(self, endpoint: str) -> SRUConfig | None:
        """Geef configuratie voor een specifiek endpoint."""
        return self.endpoints.get(endpoint)


# Standalone functies voor gebruik in bestaande code
async def sru_search_legislation(term: str, max_records: int = 5) -> list[LookupResult]:
    """
    Standalone functie voor wetgeving zoeken.

    Args:
        term: Zoekterm
        max_records: Maximum aantal resultaten

    Returns:
        Lijst van LookupResult objecten
    """
    async with SRUService() as service:
        return await service.search_legislation(term, max_records)


async def sru_search_jurisprudence(
    term: str, max_records: int = 5
) -> list[LookupResult]:
    """
    Standalone functie voor jurisprudentie zoeken.

    Args:
        term: Zoekterm
        max_records: Maximum aantal resultaten

    Returns:
        Lijst van LookupResult objecten
    """
    async with SRUService() as service:
        return await service.search_jurisprudence(term, max_records)


async def sru_search_all(
    term: str, max_records_per_source: int = 3
) -> list[LookupResult]:
    """
    Standalone functie voor zoeken in alle SRU bronnen.

    Args:
        term: Zoekterm
        max_records_per_source: Maximum aantal resultaten per bron

    Returns:
        Lijst van LookupResult objecten (gesorteerd op confidence)
    """
    async with SRUService() as service:
        return await service.search_all_sources(term, max_records_per_source)
