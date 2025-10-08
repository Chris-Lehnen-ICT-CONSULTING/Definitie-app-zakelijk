"""
SRU (Search/Retrieve via URL) service voor Nederlandse juridische bronnen.

Implementeert moderne async approach voor overheid.nl en rechtspraak.nl
als onderdeel van het Strangler Fig pattern voor web lookup modernisering.
"""

import asyncio
import logging
import os
import re
import socket
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
    sru_version: str = "1.2"  # SRU protocol version (e.g., 1.2 or 2.0)
    maximum_records: int = 10
    confidence_weight: float = 1.0
    is_juridical: bool = True
    # Alternatieve endpoints (fallbacks) voor wanneer het primaire pad 404/5xx geeft
    alt_base_urls: list[str] = field(default_factory=list)
    # Extra query parameters (e.g., {"x-connection": "BWB"})
    extra_params: dict[str, str] = field(default_factory=dict)


class SRUService:
    """
    Service voor SRU API integratie met Nederlandse overheids- en juridische bronnen.

    Ondersteunt:
    - overheid.nl (officiële wetgeving en documenten)
    - rechtspraak.nl (jurisprudentie en uitspraken)
    - zoekoperatie.overheid.nl (zoekservice)
    """

    def __init__(self, circuit_breaker_config: dict | None = None):
        self.session: aiohttp.ClientSession | None = None
        self.endpoints = self._setup_endpoints()
        self._attempts: list[dict] = []

        # User agent voor SRU requests
        self.headers = {
            "User-Agent": "DefinitieApp-SRU/1.0 (https://github.com/definitie-app; support@definitie-app.nl)"
        }

        # Circuit breaker configuration
        self.circuit_breaker_config = circuit_breaker_config or {
            "enabled": True,
            "consecutive_empty_threshold": 2,
            "providers": {
                "overheid": 2,
                "rechtspraak": 3,
                "wetgeving_nl": 2,
                "overheid_zoek": 2,
            },
        }

    def _setup_endpoints(self) -> dict[str, SRUConfig]:
        """Configureer alle SRU endpoints."""
        return {
            "overheid": SRUConfig(
                name="Overheid.nl",
                base_url="https://repository.overheid.nl/sru",
                default_collection="rijksoverheid",
                record_schema="gzd",  # FIX: Government Zoek Dublin Core (dc niet ondersteund)
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
                    # Alleen case‑variant als fallback; data.rechtspraak endpoint verwijderd (404‑ruis)
                    "https://zoeken.rechtspraak.nl/sru/Search",
                ],
            ),
            # Basiswettenbestand (BWB) via Zoekservice SRU (x-connection=BWB)
            "wetgeving_nl": SRUConfig(
                name="Wetgeving.nl",
                base_url="https://zoekservice.overheid.nl/sru/Search",
                default_collection="",
                record_schema="oai_dc",
                sru_version="2.0",
                confidence_weight=0.9,
                is_juridical=True,
                alt_base_urls=[],
                extra_params={"x-connection": "BWB"},
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

        # Voeg lichte DNS-cache toe en expliciete Accept voor XML/SRU
        # DNS-resolver hardening: enable DNS cache and threaded resolver; optional IPv4 preference via env
        try:
            from aiohttp import resolver as _resolver  # type: ignore

            _threaded = getattr(_resolver, "ThreadedResolver", None)
        except Exception:
            _threaded = None

        self.family = 0
        try:
            if str(os.getenv("SRU_FORCE_IPV4", "")).lower() in {"1", "true", "yes"}:
                self.family = socket.AF_INET
        except Exception:
            self.family = 0

        connector = aiohttp.TCPConnector(
            ttl_dns_cache=300,
            resolver=_threaded() if _threaded else None,
            family=self.family or 0,
        )
        # SRU-servers verwachten XML responses
        self.headers.setdefault("Accept", "application/xml, text/xml;q=0.9, */*;q=0.8")
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30),
            connector=connector,
            trust_env=True,  # Honor HTTP(S)_PROXY, NO_PROXY etc.
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
            # reset per-call attempts
            self._attempts = []
            # Helper om 1 query (string) tegen alle endpoints te proberen
            parked_503 = False

            # Rechtspraak.nl: snelle DNS preflight om network issues vroeg te detecteren
            try:
                if endpoint == "rechtspraak":
                    from urllib.parse import urlparse as _urlparse

                    host = _urlparse(config.base_url).hostname or ""
                    if host:
                        loop = asyncio.get_running_loop()
                        # Prefer IPv4 if SRU_FORCE_IPV4 is set
                        fam = (
                            socket.AF_INET
                            if (self.family or 0) == socket.AF_INET
                            else socket.AF_UNSPEC
                        )
                        await loop.getaddrinfo(host, 443, family=fam)
            except Exception as ex:
                # Record a single preflight failure and skip provider gracefully
                self._attempts.append(
                    {
                        "endpoint": config.name,
                        "url": None,
                        "query": None,
                        "strategy": "dns_preflight",
                        "status": None,
                        "error": f"dns_preflight_failed: {ex}",
                    }
                )
                logger.warning("SRU DNS preflight failed for %s: %s", config.name, ex)
                return []

            async def _try_query(query_str: str, strategy: str) -> list[LookupResult]:
                from urllib.parse import quote_plus, urlencode

                nonlocal parked_503

                # Primary URL
                base_params = {
                    "operation": "searchRetrieve",
                    "version": config.sru_version or "1.2",
                    "maximumRecords": min(max_records, config.maximum_records),
                    "query": query_str,
                    "startRecord": "1",
                }
                # SRU 2.0 servers zijn soms strikt in packing/accept
                if (config.sru_version or "").startswith("2"):
                    base_params["recordPacking"] = "xml"
                    base_params["httpAccept"] = "application/xml"
                # Voeg extra config-parameters toe (zoals x-connection=BWB)
                for k, v in (config.extra_params or {}).items():
                    base_params[k] = v

                # Bepaal volgorde van schemas om te proberen (vooral relevant voor SRU 2.0/BWB)
                schemas_to_try: list[str] = [config.record_schema or "dc"]
                if (config.sru_version or "").startswith("2"):
                    for extra in ("oai_dc", "srw_dc", "dc"):
                        if extra not in schemas_to_try:
                            schemas_to_try.append(extra)

                last_status: int | None = None
                last_text: str | None = None

                # Parse subset van SRU diagnostics voor betere logging
                def _extract_diag(xml_text: str) -> dict:
                    try:
                        r = ET.fromstring(xml_text)
                        ns = {
                            "srw": "http://docs.oasis-open.org/ns/search-ws/sruResponse"
                        }
                        d = r.find(".//srw:diagnostics", ns)
                        if d is None:
                            return {}
                        first = None
                        for n in d:
                            first = n
                            break
                        if first is None:
                            return {}

                        # Probeer message/details/uri te lezen (namespaces tolerant)
                        def _txt(tag: str) -> str | None:
                            el = first.find(f"srw:{tag}", ns)
                            if el is not None and el.text:
                                return el.text.strip()
                            for e in first:
                                t = e.tag
                                if "}" in t:
                                    t = t.split("}", 1)[1]
                                if t.lower() == tag and e.text:
                                    return e.text.strip()
                            return None

                        return {
                            "diag_uri": _txt("uri"),
                            "diag_message": _txt("message"),
                            "diag_details": _txt("details"),
                        }
                    except Exception:
                        return {}

                # Doorloop schemas (indien van toepassing) en probeer primary + alternatieve URLs
                for schema in schemas_to_try:
                    params = dict(base_params)
                    params["recordSchema"] = schema
                    urls: list[str] = [
                        f"{config.base_url}?{urlencode(params, quote_via=quote_plus)}"
                    ]
                    for alt in config.alt_base_urls or []:
                        try:
                            urls.append(
                                f"{alt}?{urlencode(params, quote_via=quote_plus)}"
                            )
                        except Exception:
                            continue

                    for u in urls:
                        # Kleine retry op connectieproblemen met jitter
                        for attempt in range(1, 3 + 1):
                            try:
                                async with self.session.get(u) as response:
                                    attempt_rec: dict = {
                                        "endpoint": config.name,
                                        "url": u,
                                        "query": query_str,
                                        "strategy": strategy,
                                        "status": response.status,
                                        "recordSchema": schema,
                                    }
                                    if response.status == 200:
                                        xml_content = await response.text()
                                        parsed = self._parse_sru_response(
                                            xml_content, term, config
                                        )
                                        attempt_rec["records"] = len(parsed or [])
                                        self._attempts.append(attempt_rec)
                                        if parsed:
                                            return parsed
                                    else:
                                        last_status = response.status
                                        try:
                                            txt = await response.text()
                                            last_text = txt[:200]
                                            attempt_rec["body_preview"] = last_text

                                            # Extract and log diagnostics
                                            diag = _extract_diag(txt)
                                            if diag:
                                                logger.warning(
                                                    f"SRU diagnostic from {config.name}: {diag.get('diag_message', 'Unknown error')}",
                                                    extra={
                                                        "diagnostic_uri": diag.get(
                                                            "diag_uri"
                                                        ),
                                                        "diagnostic_details": diag.get(
                                                            "diag_details"
                                                        ),
                                                        "endpoint": config.name,
                                                        "query": query_str,
                                                        "status": response.status,
                                                        "recordSchema": schema,
                                                    },
                                                )
                                                attempt_rec.update(diag)
                                        except Exception:
                                            last_text = None
                                        self._attempts.append(attempt_rec)
                                        # Specifiek gedrag voor Wetgeving.nl: bij 503 niet blijven hangen
                                        if (
                                            config.name == "Wetgeving.nl"
                                            and response.status == 503
                                        ):
                                            attempt_rec["parked"] = True
                                            attempt_rec["reason"] = (
                                                "503 service unavailable"
                                            )
                                            parked_503 = True
                                            return []
                                        # Bij 406 en SRU 2.0: probeer volgende schema
                                        if response.status == 406 and (
                                            config.sru_version or ""
                                        ).startswith("2"):
                                            break  # switch schema
                                    break  # geen retry nodig bij HTTP-status
                            except Exception as ex:
                                # Retry alleen voor connectieproblemen, anders registreren en doorgaan
                                if attempt >= 3:
                                    self._attempts.append(
                                        {
                                            "endpoint": config.name,
                                            "url": u,
                                            "query": query_str,
                                            "strategy": strategy,
                                            "status": None,
                                            "error": str(ex),
                                            "recordSchema": schema,
                                        }
                                    )
                                    break
                                await asyncio.sleep(min(0.2 * attempt, 1.0))
                # Nothing found for this query across endpoints
                if last_status and last_status != 200:
                    logger.error(
                        f"SRU API error {last_status} voor {config.name} (query fallback)."
                        + (f" Body preview: {last_text}" if last_text else "")
                    )
                return []

            # ECLI quick path voor Rechtspraak (sneller en preciezer)
            try:
                if endpoint == "rechtspraak" and re.search(
                    r"ECLI:[A-Z0-9:]+", term or ""
                ):
                    ecli_escaped = term.replace('"', '\\"')
                    ecli_query = f'cql.serverChoice any "{ecli_escaped}"'
                    results = await _try_query(ecli_query, strategy="ecli")
                    if results:
                        return results
            except Exception:
                pass

            # BWB titel-index alleen gebruiken indien expliciet ondersteund (niet zonder explain)

            # Circuit breaker configuration
            cb_enabled = self.circuit_breaker_config.get("enabled", True)
            cb_threshold = self.circuit_breaker_config.get(
                "consecutive_empty_threshold", 2
            )

            # Provider-specific threshold override
            provider_thresholds = self.circuit_breaker_config.get("providers", {})
            if endpoint in provider_thresholds:
                cb_threshold = provider_thresholds[endpoint]

            # Circuit breaker state
            empty_result_count = 0
            query_count = 0

            # Query 1: onze standaard DC-velden (exact/contains per server-choice)
            query_count += 1
            base_query = self._build_cql_query(
                term, collection or config.default_collection
            )
            results = await _try_query(base_query, strategy="dc")
            if results:
                return results

            empty_result_count += 1
            if cb_enabled and empty_result_count >= cb_threshold:
                logger.info(
                    f"Circuit breaker triggered for {config.name}: "
                    f"{empty_result_count} consecutive empty results after {query_count} queries",
                    extra={
                        "provider": endpoint,
                        "empty_count": empty_result_count,
                        "query_count": query_count,
                        "circuit_breaker_threshold": cb_threshold,
                    },
                )
                return []

            # Query 2: serverChoice (breder) — verhoogt trefkans bij Rechtspraak
            query_count += 1
            escaped = term.replace('"', '\\"')
            sc_query = f'cql.serverChoice all "{escaped}"'
            results = await _try_query(sc_query, strategy="serverChoice")
            if results:
                return results
            if parked_503 and config.name == "Wetgeving.nl":
                return []

            empty_result_count += 1
            if cb_enabled and empty_result_count >= cb_threshold:
                logger.info(
                    f"Circuit breaker triggered for {config.name}: "
                    f"{empty_result_count} consecutive empty results after {query_count} queries",
                    extra={
                        "provider": endpoint,
                        "empty_count": empty_result_count,
                        "query_count": query_count,
                        "circuit_breaker_threshold": cb_threshold,
                    },
                )
                return []

            # Query 3: hyphen-variant bij samengestelde termen
            query_count += 1
            if " " in term and "-" not in term:
                hyphen = term.replace(" ", "-")
                escaped_hyphen = hyphen.replace('"', '\\"')
                hy_query = f'cql.serverChoice all "{escaped_hyphen}"'
                results = await _try_query(hy_query, strategy="hyphen")
            else:
                results = []
            if results:
                return results
            if parked_503 and config.name == "Wetgeving.nl":
                return []

            empty_result_count += 1
            if cb_enabled and empty_result_count >= cb_threshold:
                logger.info(
                    f"Circuit breaker triggered for {config.name}: "
                    f"{empty_result_count} consecutive empty results after {query_count} queries",
                    extra={
                        "provider": endpoint,
                        "empty_count": empty_result_count,
                        "query_count": query_count,
                        "circuit_breaker_threshold": cb_threshold,
                    },
                )
                return []

            # Query 4: serverChoice any (OR i.p.v. AND)
            query_count += 1
            any_query = f'cql.serverChoice any "{escaped}"'
            results = await _try_query(any_query, strategy="serverChoice_any")
            if results:
                return results
            if parked_503 and config.name == "Wetgeving.nl":
                return []

            empty_result_count += 1
            if cb_enabled and empty_result_count >= cb_threshold:
                logger.info(
                    f"Circuit breaker triggered for {config.name}: "
                    f"{empty_result_count} consecutive empty results after {query_count} queries",
                    extra={
                        "provider": endpoint,
                        "empty_count": empty_result_count,
                        "query_count": query_count,
                        "circuit_breaker_threshold": cb_threshold,
                    },
                )
                return []

            # Query 5: prefix wildcard (ruimer, laatste redmiddel)
            # Gebruik een conservatieve prefix (eerste 6 letters) om ruis te beperken
            query_count += 1
            base = term.strip().replace('"', "").replace("'", "")
            if len(base) >= 6:
                prefix = base[:6]
                wc_query = f'cql.serverChoice any "{prefix}*"'
                results = await _try_query(wc_query, strategy="prefix_wildcard")
                if results:
                    return results
                if parked_503 and config.name == "Wetgeving.nl":
                    return []

            # Geen resultaten - log final state
            logger.info(
                f"SRU search completed with no results for {config.name}",
                extra={
                    "provider": endpoint,
                    "empty_count": empty_result_count + 1,
                    "query_count": query_count,
                    "all_queries_exhausted": True,
                },
            )
            return []

        except Exception as e:
            logger.error(f"SRU search error voor {term} in {config.name}: {e}")
            return []

    def get_attempts(self) -> list[dict]:
        """Return attempts metadata for last search call."""
        return list(self._attempts)

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
        Bouw een SRU CQL‑query op basis van de zoekterm en (indien aanwezig)
        afgeleide wettelijke context. Deze versie vermijdt één grote gequote
        frase en gebruikt in plaats daarvan AND/OR‑blokken:

        (cql.serverChoice any "<term>") AND (
            cql.serverChoice any "Wetboek van Strafvordering" OR cql.serverChoice any "Sv"
        )

        Wanneer geen wettelijke context kan worden herkend, valt de builder
        terug op de eerdere DC‑velden (title/subject/description).
        """

        # Interne helpers
        def _escape(s: str) -> str:
            return (s or "").replace('"', '\\"').strip()

        def _detect_wet_variants(text: str) -> list[str]:
            """Herken wet‑synoniemen (Sv/Sr/Awb/Rv en uitgeschreven varianten)."""
            t = (text or "").lower()
            variants: list[str] = []
            # Voluit namen en gebruikelijke afkortingen
            if (
                ("wetboek van strafvordering" in t)
                or (" sv" in f" {t}")
                or ("strafvordering" in t)
            ):
                variants.extend(["Wetboek van Strafvordering", "Sv"])
            if ("wetboek van strafrecht" in t) or (" sr" in f" {t}"):
                variants.extend(["Wetboek van Strafrecht", "Sr"])
            if ("algemene wet bestuursrecht" in t) or (" awb" in f" {t}"):
                variants.extend(["Algemene wet bestuursrecht", "Awb"])
            # Burgerlijke Rechtsvordering (Rv)
            if ("burgerlijke rechtsvordering" in t) or (" rv" in f" {t}"):
                variants.extend(["Wetboek van Burgerlijke Rechtsvordering", "Rv"])

            # De‑dupe while preserving order (case‑insensitive)
            seen: set[str] = set()
            out: list[str] = []
            for v in variants:
                k = v.lower()
                if k not in seen:
                    seen.add(k)
                    out.append(v)
            return out

        def _strip_org_tokens(text: str) -> str:
            """Verwijder bekende organisatorische tokens die trefkans verlagen in SRU."""
            org_tokens = {"om", "zm", "justid", "dji", "cjib", "kmar", "reclassering"}
            parts = [p for p in (text or "").split() if p]
            kept: list[str] = []
            for p in parts:
                if p.lower() in org_tokens:
                    continue
                kept.append(p)
            return " ".join(kept)

        # Stap 1: haal wet‑varianten uit de term, strip org‑tokens uit basisterm
        wet_variants = _detect_wet_variants(term)
        base_term = _strip_org_tokens(term)
        # Verwijder wet‑varianten uit de basisterm om ruis te beperken
        if wet_variants:
            bt = base_term
            for v in wet_variants:
                if not v:
                    continue
                import re as _re

                # case‑insensitive vervanging, als los woord of frase
                pattern = _re.compile(r"\b" + _re.escape(v) + r"\b", _re.IGNORECASE)
                bt = pattern.sub(" ", bt)
            base_term = " ".join(bt.split())

        # Als we wet‑context hebben, bouw een AND/OR query met serverChoice any
        if wet_variants:
            term_block = f'cql.serverChoice any "{_escape(base_term)}"'
            wet_block_parts = [
                f'cql.serverChoice any "{_escape(w)}"' for w in wet_variants
            ]
            wet_block = " OR ".join(wet_block_parts)
            query = f"({term_block}) AND ({wet_block})"
            # Voeg collectie filter toe indien aanwezig (alleen voor overheid.nl verzameling)
            if collection:
                query = f'{query} AND c.product-area="{_escape(collection)}"'
            return query

        # Geen herkende wet‑context ⇒ gebruik schema-agnostic serverChoice
        # FIX A.1: DC fields falen met gzd schema ("unknown prefix dc")
        # serverChoice werkt met alle schemas (gzd, dc, oai_dc)
        escaped_term = _escape(term)
        base_query = f'cql.serverChoice any "{escaped_term}"'
        if collection:
            base_query = f'{base_query} AND c.product-area="{_escape(collection)}"'
        return base_query

    def _extract_diag_from_response(self, xml_text: str) -> dict:
        """Extract SRU diagnostics uit XML response.

        Helper method voor het extraheren van SRU diagnostic messages.
        Ondersteunt beide SRU 1.2 en 2.0 namespaces.
        """
        try:
            r = ET.fromstring(xml_text)
            # Probeer beide namespace varianten (SRU 1.2 en 2.0)
            namespace_variants = [
                {
                    "srw": "http://docs.oasis-open.org/ns/search-ws/sruResponse"
                },  # SRU 2.0
                {"srw": "http://www.loc.gov/zing/srw/"},  # SRU 1.2
            ]

            d = None
            for ns in namespace_variants:
                d = r.find(".//srw:diagnostics", ns)
                if d is not None:
                    break

            if d is None:
                return {}

            first = None
            for n in d:
                first = n
                break
            if first is None:
                return {}

            # Probeer message/details/uri te lezen (namespaces tolerant)
            def _txt(tag: str) -> str | None:
                # Probeer met namespace
                for ns in namespace_variants:
                    el = first.find(f"srw:{tag}", ns)
                    if el is not None and el.text:
                        return el.text.strip()

                # Fallback: zonder namespace
                for e in first:
                    t = e.tag
                    if "}" in t:
                        t = t.split("}", 1)[1]
                    if t.lower() == tag and e.text:
                        return e.text.strip()
                return None

            return {
                "diag_uri": _txt("uri"),
                "diag_message": _txt("message"),
                "diag_details": _txt("details"),
            }
        except Exception:
            return {}

    # === Legal metadata extraction ===
    _ART_RE = re.compile(r"(?i)\b(?:artikel|art\.)\s+(\d+[a-z]?)\b")
    _LID_NUM_RE = re.compile(r"(?i)\blid\s+(\d+)\b")
    _LID_ORDINAL_RE = re.compile(r"(?i)\b(\d+)(?:e|ste)\s+lid\b")
    _LID_WORDS = {
        "eerste": "1",
        "tweede": "2",
        "derde": "3",
        "vierde": "4",
        "vijfde": "5",
        "zesde": "6",
        "zevende": "7",
        "achtste": "8",
        "negende": "9",
        "tiende": "10",
    }

    def _extract_legal_metadata(self, text: str) -> dict[str, str] | None:
        """Probeert artikelnummer en wetcode/titel uit tekst te halen.

        Heuristieken:
        - Artikel: 'Artikel' of 'Art.' gevolgd door nummer (optionele letter)
        - Wetcode: detecteer Sv/Sr/Awb/Rv op basis van veelvoorkomende namen/afkortingen
        """
        if not text:
            return None

        m = self._ART_RE.search(text)
        article_number: str | None = m.group(1) if m else None

        # Lid extractie (verschillende varianten)
        law_clause: str | None = None
        m_lid = self._LID_NUM_RE.search(text)
        if m_lid:
            law_clause = m_lid.group(1)
        else:
            m_ord = self._LID_ORDINAL_RE.search(text)
            if m_ord:
                law_clause = m_ord.group(1)
            else:
                low = text.lower()
                for word, num in self._LID_WORDS.items():
                    if f" {word} lid" in low:
                        law_clause = num
                        break

        low = text.lower()
        law_code: str | None = None
        law_title: str | None = None

        if (
            ("wetboek van strafvordering" in low)
            or (" sv" in f" {low}")
            or ("strafvordering" in low)
        ):
            law_code = "Sv"
            law_title = "Wetboek van Strafvordering"
        elif (
            ("wetboek van strafrecht" in low)
            or (" sr" in f" {low}")
            or ("strafrecht" in low)
        ):
            law_code = "Sr"
            law_title = "Wetboek van Strafrecht"
        elif (
            ("algemene wet bestuursrecht" in low)
            or (" awb" in f" {low}")
            or ("awb" in low)
        ):
            law_code = "Awb"
            law_title = "Algemene wet bestuursrecht"
        elif ("burgerlijke rechtsvordering" in low) or (" rv" in f" {low}"):
            law_code = "Rv"
            law_title = "Wetboek van Burgerlijke Rechtsvordering"

        if article_number or law_code or law_clause:
            out: dict[str, str] = {}
            if article_number:
                out["article_number"] = article_number
            if law_code:
                out["law_code"] = law_code
            if law_title:
                out["law_title"] = law_title
            if law_clause:
                out["law_clause"] = law_clause
            return out
        return None

    def _parse_sru_response(
        self, xml_content: str, term: str, config: SRUConfig
    ) -> list[LookupResult]:
        """Parse SRU XML response naar LookupResult objecten."""
        try:
            root = ET.fromstring(xml_content)

            # SRU namespace variants (support voor SRU 1.2 en 2.0)
            namespace_variants = [
                {
                    "srw": "http://www.loc.gov/zing/srw/",  # SRU 1.2
                    "dc": "http://purl.org/dc/elements/1.1/",
                    "dcterms": "http://purl.org/dc/terms/",
                    "gzd": "http://overheid.nl/gzd",
                },
                {
                    "srw": "http://docs.oasis-open.org/ns/search-ws/sruResponse",  # SRU 2.0
                    "dc": "http://purl.org/dc/elements/1.1/",
                    "dcterms": "http://purl.org/dc/terms/",
                    "gzd": "http://overheid.nl/gzd",
                },
            ]

            # Probeer beide namespaces (SRU 1.2 en 2.0 auto-detect)
            records = []
            namespaces = None
            for ns_variant in namespace_variants:
                records = root.findall(".//srw:record", ns_variant)
                if records:
                    namespaces = ns_variant
                    logger.debug(
                        f"Found {len(records)} records using namespace: {ns_variant['srw']}"
                    )
                    break

            if not records:
                logger.warning(
                    f"No records found in SRU response from {config.name}",
                    extra={
                        "xml_length": len(xml_content),
                        "xml_preview": (
                            xml_content[:500] if len(xml_content) > 500 else xml_content
                        ),
                        "endpoint": config.name,
                        "term": term,
                    },
                )

                # Check for diagnostics in XML
                diag = self._extract_diag_from_response(xml_content)
                if diag:
                    logger.error(
                        f"SRU diagnostic found: {diag.get('diag_message', 'Unknown')}",
                        extra={
                            "endpoint": config.name,
                            "term": term,
                            "diagnostic_uri": diag.get("diag_uri"),
                            "diagnostic_message": diag.get("diag_message"),
                            "diagnostic_details": diag.get("diag_details"),
                        },
                    )

                return []

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
            # Tolerante extractie van metadata: probeer bekende namespaces, anders local-name fallback
            def _find_text_local(element: ET.Element, local: str) -> str:
                # 1) Zoek via bekende namespaces
                for ns in ("dc", "dcterms", "gzd"):
                    try:
                        el = element.find(f".//{ns}:{local}", namespaces)
                        if el is not None and el.text:
                            return el.text.strip()
                    except Exception:
                        continue
                # 2) Fallback: loop alle subelements en match op lokale tagnaam
                for el in element.iter():
                    try:
                        tag = el.tag
                        if "}" in tag:
                            tag = tag.split("}", 1)[1]
                        if tag.lower() == local.lower() and el.text:
                            return el.text.strip()
                    except Exception:
                        continue
                return ""

            title = _find_text_local(record, "title")
            description = _find_text_local(record, "description")
            identifier = _find_text_local(record, "identifier")
            subject = _find_text_local(record, "subject")
            doc_type = _find_text_local(record, "type")
            date = _find_text_local(record, "date")

            # Skip als geen titel of beschrijving
            if not title and not description:
                return None

            # Bereken confidence based op term matching
            confidence = self._calculate_confidence(
                term, title, description, subject, config
            )

            # Build URL (gebruik identifier als beschikbaar)
            url = identifier if identifier.startswith(("http://", "https://")) else ""

            # Build definitie tekst (uitgebreid met meer context)
            definition_parts = []

            # Primair: gebruik title als start (meestal meest informatief)
            if title:
                definition_parts.append(title)

            # Voeg description toe (vaak de hoofdcontent)
            if description and description not in (title or ""):
                definition_parts.append(description)

            # Voeg subject toe als extra context (tenzij al in vorige velden)
            combined_text = " ".join(definition_parts).lower()
            if subject and (subject.lower() not in combined_text):
                definition_parts.append(f"Onderwerp: {subject}")

            # Voeg document type toe als het informatief is
            if doc_type and len(definition_parts) < 2:
                doc_type_lower = doc_type.lower()
                if doc_type_lower not in ("document", "text", "resource"):
                    definition_parts.append(f"Type: {doc_type}")

            # Fallback naar identifier als er weinig info is
            if len(definition_parts) == 0:
                definition_parts.append(identifier or "Geen beschrijving beschikbaar")

            definition = " — ".join(definition_parts)

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

            # Probeer legal metadata toe te voegen (Artikel X Sv/Sr/Awb/Rv)
            legal_meta = self._extract_legal_metadata(
                f"{title} {description} {subject}"
            )
            if legal_meta:
                metadata.update(legal_meta)

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

    def get_circuit_breaker_threshold(self, endpoint: str) -> int:
        """Get circuit breaker threshold for a specific endpoint."""
        if not self.circuit_breaker_config.get("enabled", True):
            return 999  # Effectively disabled

        # Provider-specific threshold override
        provider_thresholds = self.circuit_breaker_config.get("providers", {})
        if endpoint in provider_thresholds:
            return provider_thresholds[endpoint]

        # Default threshold
        return self.circuit_breaker_config.get("consecutive_empty_threshold", 2)


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
