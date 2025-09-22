"""
Moderne, unified web lookup service implementatie volgens Strangler Fig pattern.

Deze service implementeert een schone architectuur voor web lookup operaties
terwijl geleidelijk de legacy implementaties vervangt.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from .interfaces import (
    JuridicalReference,
    LookupRequest,
    LookupResult,
    WebLookupServiceInterface,
    WebSource,
)

logger = logging.getLogger(__name__)

# Domein imports met error handling voor development
try:
    from domain.autoriteit.betrouwbaarheid import BetrouwbaarheidsCalculator, BronType

    DOMAIN_AVAILABLE = True
except ImportError:
    logger.warning("Domein modules niet beschikbaar - fallback modus")
    DOMAIN_AVAILABLE = False

    class BronType:
        WETGEVING = "wetgeving"
        JURISPRUDENTIE = "jurisprudentie"
        BELEID = "beleid"
        LITERATUUR = "literatuur"


logger = logging.getLogger(__name__)


@dataclass
class SourceConfig:
    """Configuratie voor een specifieke lookup bron."""

    name: str
    base_url: str
    api_type: str  # "mediawiki", "sru", "scraping"
    timeout: int = 30
    max_retries: int = 3
    is_juridical: bool = False
    confidence_weight: float = 1.0
    enabled: bool = True


class ModernWebLookupService(WebLookupServiceInterface):
    """
    Moderne implementatie van web lookup service.

    Gebruikt Strangler Fig pattern om legacy code geleidelijk te vervangen
    met moderne, testbare en onderhoudbare implementaties.
    """

    def __init__(self):
        self.sources: dict[str, SourceConfig] = {}
        self._config: dict[str, Any] | None = None
        self._provider_weights: dict[str, float] = {}
        self._last_debug: dict[str, Any] | None = None
        self._debug_attempts: list[dict[str, Any]] = []

        # Initialize domein components als beschikbaar
        if DOMAIN_AVAILABLE:
            self.betrouwbaarheids_calculator = BetrouwbaarheidsCalculator()
        else:
            self.betrouwbaarheids_calculator = None

        # In productie geen legacy fallback meer gebruiken
        self._legacy_fallback_enabled = False
        self._setup_sources()

    def _setup_sources(self) -> None:
        """Configureer alle beschikbare lookup bronnen."""
        # Load config
        try:
            from .web_lookup.config_loader import load_web_lookup_config

            self._config = load_web_lookup_config()
            wl = self._config.get("web_lookup", {})
            providers = wl.get("providers", {})
            # Build provider weights mapping using config keys
            self._provider_weights = {
                "wikipedia": float(providers.get("wikipedia", {}).get("weight", 0.8)),
                "overheid": float(providers.get("sru_overheid", {}).get("weight", 1.0)),
                # Rechtspraak weegt standaard 0.95 tenzij specifiek geconfigureerd
                "rechtspraak": float(
                    providers.get("rechtspraak_ecli", {}).get("weight", 0.95)
                ),
                "wiktionary": float(providers.get("wiktionary", {}).get("weight", 0.9)),
                "wetgeving": float(providers.get("wetgeving_nl", {}).get("weight", 0.9)),
            }
        except Exception as e:
            logger.warning(f"Web lookup config not loaded, using defaults: {e}")
            self._config = None
            self._provider_weights = {
                "wikipedia": 0.8,
                "wiktionary": 0.9,
                "overheid": 1.0,
                "rechtspraak": 0.95,
            }

        # Helper om enabled-vlag te lezen uit config
        def _is_enabled(key: str, default: bool = True) -> bool:
            try:
                return bool(self._config.get("web_lookup", {}).get("providers", {}).get(key, {}).get("enabled", default))
            except Exception:
                return default

        self.sources = {
            "wikipedia": SourceConfig(
                name="Wikipedia",
                base_url="https://nl.wikipedia.org/api/rest_v1",
                api_type="mediawiki",
                confidence_weight=self._provider_weights.get("wikipedia", 0.8),
                is_juridical=False,
                enabled=_is_enabled("wikipedia", True),
            ),
            "wiktionary": SourceConfig(
                name="Wiktionary",
                base_url="https://nl.wiktionary.org/w/api.php",
                api_type="mediawiki",
                confidence_weight=self._provider_weights.get("wiktionary", 0.9),
                is_juridical=False,
                enabled=_is_enabled("wiktionary", True),
            ),
            "wetgeving": SourceConfig(
                name="Wetgeving.nl",
                base_url="https://wetten.overheid.nl/SRU/Search",
                api_type="sru",
                confidence_weight=self._provider_weights.get("wetgeving", 0.9),
                is_juridical=True,
                enabled=_is_enabled("wetgeving_nl", True),
            ),
            "overheid": SourceConfig(
                name="Overheid.nl",
                base_url="https://repository.overheid.nl",
                api_type="sru",
                confidence_weight=self._provider_weights.get("overheid", 1.0),
                is_juridical=True,
                enabled=_is_enabled("sru_overheid", True),
            ),
            "rechtspraak": SourceConfig(
                name="Rechtspraak.nl",
                base_url="https://www.rechtspraak.nl",
                api_type="sru",
                confidence_weight=self._provider_weights.get("rechtspraak", 0.95),
                is_juridical=True,
                enabled=_is_enabled("rechtspraak_ecli", True),
            ),
            "overheid_zoek": SourceConfig(
                name="Overheid.nl Zoekservice",
                base_url="https://zoekservice.overheid.nl",
                api_type="sru",
                confidence_weight=self._provider_weights.get("overheid", 0.9),
                is_juridical=True,
                enabled=_is_enabled("sru_overheid", True),
            ),
        }

    # === Context token parsing helpers ===
    def _classify_context_tokens(self, context: str | None) -> tuple[list[str], list[str], list[str]]:
        """Classify context tokens into organisatorisch, juridisch, wettelijk.

        Heuristics based on common abbreviations/keywords in this domain.
        """
        if not context:
            return [], [], []
        raw = [t.strip() for t in (context or "").split("|")]
        tokens = [t for t in raw if t]

        org_set = {"om", "zm", "dji", "justid", "kmar", "cjib", "reclassering"}
        jur_keywords = ["recht", "civiel", "bestuursrecht", "strafrecht", "jurid"]
        wet_keywords = ["wet", "wetboek", "awb", "sv", "sr", "rv"]

        org: list[str] = []
        jur: list[str] = []
        wet: list[str] = []

        def _norm(s: str) -> str:
            return s.lower().strip().replace("(huidig)", "").strip()

        for t in tokens:
            n = _norm(t)
            plain = n.replace("  ", " ")
            if n in org_set:
                org.append(t)
                continue
            if any(k in plain for k in wet_keywords):
                wet.append(t)
                continue
            if any(k in plain for k in jur_keywords):
                jur.append(t)
                continue
            # default: treat unknowns as org to keep cascade predictable
            org.append(t)

        # Normalize synonyms for wet targeting
        mapped_wet: list[str] = []
        for w in wet:
            nw = _norm(w)
            if "wetboek van strafvordering" in nw or nw == "sv" or "sv" in nw:
                mapped_wet.extend(["Wetboek van Strafvordering", "Sv"])
            elif "wetboek van strafrecht" in nw or nw == "sr" or "sr" in nw:
                mapped_wet.extend(["Wetboek van Strafrecht", "Sr"])
            elif nw == "awb" or "algemene wet bestuursrecht" in nw:
                mapped_wet.extend(["Algemene wet bestuursrecht", "Awb"])
            else:
                mapped_wet.append(w)

        # De-duplicate while preserving order
        def _dedup(seq: list[str]) -> list[str]:
            seen: set[str] = set()
            out: list[str] = []
            for x in seq:
                k = x.strip().lower()
                if k not in seen and k:
                    seen.add(k)
                    out.append(x)
            return out

        return _dedup(org), _dedup(jur), _dedup(mapped_wet)

    async def lookup(self, request: LookupRequest) -> list[LookupResult]:
        """
        Zoek een term op in web bronnen.

        Implementeert moderne async approach met concurrent lookups
        en intelligent fallback naar legacy implementaties.
        """
        logger.info(f"Starting lookup for term: {request.term}")
        # reset per-call debug container
        self._debug_attempts = []

        # Bepaal welke bronnen te gebruiken
        sources_to_search = self._determine_sources(request)

        # Concurrent lookups uitvoeren
        tasks = [
            self._lookup_source(request.term, source_name, request)
            for source_name in sources_to_search
            if self.sources[source_name].enabled
        ]

        # Wacht op alle resultaten
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter succesvolle resultaten
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Source lookup failed: {result}")
                continue
            if result is not None and getattr(result, "success", True):
                valid_results.append(result)

        # Ranking & dedup volgens Epic 3
        try:
            from .web_lookup.ranking import rank_and_dedup

            # Convert to contract-like dicts for ranking
            prepared = [
                self._to_contract_dict(r) for r in valid_results if r is not None
            ]
            # Provider keys mapping based on source names
            ranked = rank_and_dedup(prepared, self._provider_weights)

            # Reorder/filter original results according to ranked unique set
            final_results: list[LookupResult] = []
            # Index by canonical URL or content hash
            from hashlib import sha256

            from .web_lookup.ranking import _canonical_url  # type: ignore

            index: dict[str, LookupResult] = {}
            for r in valid_results:
                url_key = _canonical_url(getattr(r.source, "url", ""))
                if url_key:
                    index[f"url:{url_key}"] = r
                # Content hash fallback from definition
                base_text = (r.definition or r.context or "").encode(
                    "utf-8", errors="ignore"
                )
                ch = sha256(base_text).hexdigest()
                index[f"hash:{ch}"] = r

            for item in ranked:
                key = None
                if item.get("url"):
                    key = f"url:{_canonical_url(str(item['url']))}"
                else:
                    key = f"hash:{item.get('content_hash','')}"
                picked = index.get(key)
                if picked is not None:
                    final_results.append(picked)

            # Limiteer aantal resultaten
            # Save debug info
            self._last_debug = {
                "term": request.term,
                "context": request.context,
                "selected_sources": sources_to_search,
                "attempts": self._debug_attempts,
                "results": len(final_results[: request.max_results]),
            }
            return final_results[: request.max_results]
        except Exception as e:
            logger.warning(
                f"Ranking/dedup failed, falling back to confidence sort: {e}"
            )
            valid_results.sort(key=lambda r: r.source.confidence, reverse=True)
            self._last_debug = {
                "term": request.term,
                "context": request.context,
                "selected_sources": sources_to_search,
                "attempts": self._debug_attempts,
                "results": len(valid_results[: request.max_results]),
            }
            return valid_results[: request.max_results]

    def _determine_sources(self, request: LookupRequest) -> list[str]:
        """Bepaal welke bronnen te gebruiken op basis van request en context."""
        if request.sources:
            return [s for s in request.sources if s in self.sources]

        term_lower = (request.term or "").lower()
        context_lower = (request.context or "").lower()

        # Heuristiek: juridische context aanwezig → prioriteer juridische bronnen
        juridical_keywords = [
            "strafrecht",
            "bestuursrecht",
            "civiel",
            "jurid",
            "wetboek",
            "artikel",
            "ecli",
            "rechtbank",
            "jurisprudentie",
            "wetgeving",
        ]

        is_juridical = any(k in term_lower for k in ["wet", "artikel", "recht"]) or any(
            k in context_lower for k in juridical_keywords
        )

        if is_juridical:
            return [
                "wetgeving",
                "overheid",
                "rechtspraak",
                "overheid_zoek",
                "wikipedia",
                "wiktionary",
            ]

        # Voor algemene termen, start met encyclopedische bronnen
        return ["wikipedia", "wiktionary", "overheid", "rechtspraak"]

    async def _lookup_source(
        self, term: str, source_name: str, request: LookupRequest
    ) -> LookupResult | None:
        """Lookup in een specifieke bron."""
        source_config = self.sources[source_name]

        import time as _t
        start = _t.time()
        attempt: dict[str, Any] = {
            "provider": source_name,
            "term": term,
            "api_type": source_config.api_type,
        }
        try:
            if source_config.api_type == "mediawiki":
                result = await self._lookup_mediawiki(term, source_config, request)
            elif source_config.api_type == "sru":
                result = await self._lookup_sru(term, source_config, request)
            elif source_config.api_type == "scraping":
                result = await self._lookup_scraping(term, source_config, request)
            else:
                logger.warning(f"Unknown API type: {source_config.api_type}")
                result = None
            attempt["success"] = bool(result)
            attempt["duration_ms"] = int((_t.time() - start) * 1000)
            if result and getattr(result, "source", None):
                attempt["url"] = getattr(result.source, "url", "")
                attempt["confidence"] = getattr(result.source, "confidence", 0.0)
            return result
        except Exception as e:
            logger.error(f"Error in {source_name} lookup: {e}")
            # Geen legacy fallback in modern-only modus
            attempt["success"] = False
            attempt["error"] = str(e)
            attempt["duration_ms"] = int((_t.time() - start) * 1000)
            return None
        finally:
            self._debug_attempts.append(attempt)

    async def _lookup_mediawiki(
        self, term: str, source: SourceConfig, request: LookupRequest
    ) -> LookupResult | None:
        """Lookup in MediaWiki API (Wikipedia, Wiktionary)."""
        logger.info(f"MediaWiki lookup for {term} in {source.name}")

        try:
            if source.name == "Wikipedia":
                # Gebruik moderne Wikipedia service
                from .web_lookup.wikipedia_service import wikipedia_lookup

                # Stage-based context backoff: 1) org+jur+wet 2) jur+wet 3) wet 4) term
                org, jur, wet = self._classify_context_tokens(getattr(request, "context", None))
                stages: list[tuple[str, list[str]]] = []
                all_tokens = org + jur + wet
                if all_tokens:
                    stages.append(("context_full", all_tokens))
                if jur or wet:
                    stages.append(("jur_wet", jur + wet))
                if wet:
                    stages.append(("wet_only", wet))
                stages.append(("no_ctx", []))

                t = (term or "").strip()
                result: LookupResult | None = None
                for stage_name, toks in stages:
                    query_term = t if not toks else f"{t} " + " ".join(toks)
                    try:
                        res = await asyncio.wait_for(
                            wikipedia_lookup(query_term),
                            timeout=float(getattr(request, "timeout", 30) or 30),
                        )
                        # Log attempt
                        self._debug_attempts.append(
                            {
                                "provider": source.name,
                                "api_type": "mediawiki",
                                "term": query_term,
                                "stage": stage_name,
                                "success": bool(res and res.success),
                            }
                        )
                        if res and res.success:
                            result = res
                            break
                    except Exception:
                        continue

                # Heuristische fallbacks indien nog niets gevonden (hyphen/titlecase/suffix‑strip)
                if not (result and result.success):
                    fallbacks: list[str] = []
                    if " " in t and "-" not in t:
                        fallbacks.append(t.replace(" ", "-"))
                        fallbacks.append(t.title().replace(" ", "-"))
                    if t.lower().endswith("tekst") and len(t) > 6:
                        fallbacks.append(t[: -len("tekst")])
                    if t.lower() == "vonnistekst":
                        fallbacks.extend(["vonnis", "uitspraak"])  # juridische synoniemen

                    seen: set[str] = set()
                    for fb in fallbacks:
                        fbq = fb.strip()
                        if not fbq or fbq.lower() in seen or fbq.lower() == t.lower():
                            continue
                        seen.add(fbq.lower())
                        try:
                            fb_res = await asyncio.wait_for(
                                wikipedia_lookup(fbq),
                                timeout=float(getattr(request, "timeout", 30) or 30),
                            )
                            self._debug_attempts.append(
                                {
                                    "provider": source.name,
                                    "api_type": "mediawiki",
                                    "term": fbq,
                                    "fallback": True,
                                    "success": bool(fb_res and fb_res.success),
                                }
                            )
                            if fb_res and fb_res.success:
                                result = fb_res
                                break
                        except Exception:
                            continue

                if result and result.success:
                    result.source.confidence *= source.confidence_weight
                    return result

            elif source.name == "Wiktionary":
                logger.info(f"Wiktionary lookup voor {term} - nog niet geïmplementeerd")
                return None

        except ImportError as e:
            logger.warning(f"Modern MediaWiki service niet beschikbaar: {e}")
        except Exception as e:
            logger.error(f"MediaWiki lookup error: {e}")

        return None

    async def _lookup_sru(
        self, term: str, source: SourceConfig, request: LookupRequest
    ) -> LookupResult | None:
        """Lookup in SRU API (overheid.nl, rechtspraak.nl)."""
        logger.info(f"SRU lookup for {term} in {source.name}")

        try:
            # Import SRU service
            from .web_lookup.sru_service import SRUService

            # Map source names to SRU endpoints
            endpoint_map = {
                "Overheid.nl": "overheid",
                "Rechtspraak.nl": "rechtspraak",
                "Wetgeving.nl": "wetgeving_nl",
                "Overheid.nl Zoekservice": "overheid_zoek",
            }

            endpoint = endpoint_map.get(source.name)
            if not endpoint:
                logger.warning(f"No SRU endpoint mapping for source: {source.name}")
                return None

            # Stage-based SRU search using context backoff (SRU: alleen 'wet' tokens)
            async with SRUService() as sru_service:
                org, jur, wet = self._classify_context_tokens(getattr(request, "context", None))
                stages: list[tuple[str, list[str]]] = []
                # Voor Rechtspraak: term‑only eerst (context verlaagt recall)
                if endpoint == "rechtspraak":
                    stages.append(("no_ctx", []))
                # Voor overige SRU‑providers: wet‑only eerst, dan no_ctx
                if endpoint != "rechtspraak" and wet:
                    stages.append(("wet_only", wet))
                # Voeg altijd een no_ctx fallback toe
                if ("no_ctx", []) not in stages:
                    stages.append(("no_ctx", []))

                base = (term or "").strip()
                for stage_name, toks in stages:
                    combo_term = base if not toks else f"{base} " + " ".join(toks)
                    # Respecteer per-request timeout budget
                    results = await asyncio.wait_for(
                        sru_service.search(
                            term=combo_term, endpoint=endpoint, max_records=3
                        ),
                        timeout=float(getattr(request, "timeout", 30) or 30),
                    )
                    # collect attempts for this stage
                    try:
                        for att in sru_service.get_attempts() or []:
                            rec = {
                                "provider": source.name,
                                "api_type": "sru",
                                "term": combo_term,
                                "stage": stage_name,
                            }
                            rec.update(att)
                            self._debug_attempts.append(rec)
                    except Exception:
                        pass

                    if results:
                        r = results[0]
                        r.source.confidence *= source.confidence_weight
                        return r

                # Heuristische extra fallbacks op basis van term (na stages)
                extra_terms: list[str] = []
                if base.endswith("tekst") and len(base) > 6:
                    extra_terms.append(base[:-5])
                if " " in base and "-" not in base:
                    extra_terms.append(base.replace(" ", "-"))
                for et in extra_terms:
                    results = await asyncio.wait_for(
                        sru_service.search(term=et, endpoint=endpoint, max_records=3),
                        timeout=float(getattr(request, "timeout", 30) or 30),
                    )
                    self._debug_attempts.append(
                        {
                            "provider": source.name,
                            "api_type": "sru",
                            "endpoint": endpoint,
                            "term": et,
                            "fallback": True,
                            "stage": "post_stages",
                            "success": bool(results),
                        }
                    )
                    if results:
                        r = results[0]
                        r.source.confidence *= source.confidence_weight * 0.95
                        return r

                return None

        except ImportError as e:
            logger.warning(f"SRU service niet beschikbaar: {e}")
        except Exception as e:
            logger.error(f"SRU lookup error: {e}")

        return None

    async def _lookup_scraping(
        self, term: str, source: SourceConfig, request: LookupRequest
    ) -> LookupResult | None:
        """Lookup via web scraping."""
        logger.info(f"Scraping lookup for {term} in {source.name}")

        # Veilige scraping wordt in aparte user story opgepakt (US-014)
        return None

    async def _legacy_fallback(
        self, term: str, source_name: str, request: LookupRequest
    ) -> LookupResult | None:
        """Fallback naar legacy implementatie."""
        logger.info(f"Using legacy fallback for {term} in {source_name}")

        try:
            # Import legacy module dynamically om circular imports te voorkomen
            from ..web_lookup.lookup import zoek_in_bron

            # Converteer naar legacy format en terug
            legacy_result = zoek_in_bron(term, source_name)

            if legacy_result:
                return self._convert_legacy_result(legacy_result, source_name)

        except ImportError as e:
            logger.warning(f"Legacy fallback not available: {e}")
        except Exception as e:
            logger.error(f"Legacy fallback failed: {e}")

        return None

    def _convert_legacy_result(
        self, legacy_result: Any, source_name: str
    ) -> LookupResult:
        """Converteer legacy result naar moderne LookupResult."""
        self.sources.get(source_name)

        return LookupResult(
            term=getattr(legacy_result, "term", ""),
            source=WebSource(
                name=source_name,
                url=getattr(legacy_result, "url", ""),
                confidence=getattr(legacy_result, "confidence", 0.5),
                api_type="legacy",
            ),
            definition=getattr(legacy_result, "definitie", ""),
            success=True,
            metadata={"source_type": "legacy_fallback"},
        )

    async def lookup_single_source(self, term: str, source: str) -> LookupResult | None:
        """Zoek een term op in een specifieke bron."""
        request = LookupRequest(term=term, sources=[source], max_results=1)
        results = await self.lookup(request)
        return results[0] if results else None

    def get_available_sources(self) -> list[WebSource]:
        """Geef lijst van beschikbare web bronnen."""
        return [
            WebSource(
                name=config.name,
                url=config.base_url,
                confidence=config.confidence_weight,
                is_juridical=config.is_juridical,
                api_type=config.api_type,
            )
            for config in self.sources.values()
            if config.enabled
        ]

    def validate_source(self, text: str) -> WebSource:
        """Valideer en identificeer de bron van een tekst."""
        if self.betrouwbaarheids_calculator:
            # Bepaal bron type voor de calculator
            bron_type = self._determine_source_type(text)
            autoriteits_score = (
                self.betrouwbaarheids_calculator.bereken_betrouwbaarheid(
                    bron_type, text
                )
            )
            confidence = autoriteits_score.score
        else:
            confidence = 0.5  # Default confidence

        # Bepaal bron type op basis van content analyse
        bron_type = self._determine_source_type(text)

        return WebSource(
            name="Analyzed Source",
            url="",
            confidence=confidence,
            is_juridical=(bron_type in (BronType.WETGEVING, BronType.JURISPRUDENTIE)),
        )

    # --------------------
    # Helpers
    # --------------------

    def _to_contract_dict(self, result: LookupResult) -> dict[str, Any]:
        """Convert LookupResult into a minimal contract-like dict for ranking.

        Applies sanitization and computes a content hash fallback when URL is absent.
        """
        try:
            from .web_lookup.sanitization import sanitize_snippet
        except Exception:

            def sanitize_snippet(x: str, max_length: int = 500) -> str:  # type: ignore
                return (x or "")[:max_length]

        from hashlib import sha256

        provider_key = self._infer_provider_key(result)
        snippet_src = result.definition or result.context or ""
        # Verrijk snippet met artikelmetadata indien beschikbaar
        try:
            if isinstance(getattr(result, "metadata", None), dict):
                num = result.metadata.get("article_number")
                code = result.metadata.get("law_code")
                clause = result.metadata.get("law_clause")
                if num and code and snippet_src:
                    if clause:
                        snippet_src = f"Artikel {num} lid {clause} {code}: {snippet_src}"
                    else:
                        snippet_src = f"Artikel {num} {code}: {snippet_src}"
        except Exception:
            pass
        snippet = sanitize_snippet(snippet_src, max_length=500)
        url = getattr(result.source, "url", "")
        content = (snippet_src or "").encode("utf-8", errors="ignore")
        content_hash = sha256(content).hexdigest()

        score = float(getattr(result.source, "confidence", 0.0) or 0.0)
        # ECLI boost: Rechtspraak met expliciete ECLI krijgt kleine bonus
        try:
            if provider_key == "rechtspraak":
                meta = result.metadata if isinstance(result.metadata, dict) else {}
                idf = str(meta.get("dc_identifier", ""))
                if ("ECLI:" in idf) or ("ECLI:" in snippet_src):
                    score = min(1.0, score + 0.05)
        except Exception:
            pass

        return {
            "provider": provider_key,
            "source_label": result.source.name,
            "title": (
                result.metadata.get("title")
                if isinstance(result.metadata, dict)
                else None
            )
            or result.source.name,
            "url": url,
            "snippet": snippet,
            "score": score,
            "used_in_prompt": False,
            "position_in_prompt": -1,
            "retrieved_at": (
                result.metadata.get("retrieved_at")
                if isinstance(result.metadata, dict)
                else None
            ),
            "content_hash": content_hash,
            "is_authoritative": bool(getattr(result.source, "is_juridical", False)),
            "legal_weight": (
                1.0 if getattr(result.source, "is_juridical", False) else 0.0
            ),
        }

    def _infer_provider_key(self, result: LookupResult) -> str:
        name = (result.source.name or "").lower()
        if "wikipedia" in name:
            return "wikipedia"
        if "wiktionary" in name:
            return "wiktionary"
        if "rechtspraak" in name:
            return "rechtspraak"
        if "overheid" in name:
            return "overheid"
        if "wetgeving" in name:
            return "wetgeving"
        return name or "unknown"

    def _determine_source_type(self, text: str) -> BronType:
        """Bepaal het type bron op basis van tekst analyse."""
        text_lower = text.lower()

        if any(word in text_lower for word in ["artikel", "wet", "wetboek"]):
            return BronType.WETGEVING
        if any(word in text_lower for word in ["uitspraak", "rechtbank", "hof"]):
            return BronType.JURISPRUDENTIE
        if any(word in text_lower for word in ["beleid", "regeling", "circulaire"]):
            return BronType.BELEID
        return BronType.LITERATUUR

    def find_juridical_references(self, text: str) -> list[JuridicalReference]:
        """Vind juridische verwijzingen in tekst."""
        # Simpele implementatie voor nu - kan uitgebreid worden met domein modules
        references = []

        # Basis patroon matching voor juridische verwijzingen
        text_lower = text.lower()
        if "artikel" in text_lower and any(w in text_lower for w in ["wet", "wetboek"]):
            references.append(
                JuridicalReference(
                    type="artikel",
                    reference="Gevonden juridische verwijzing",
                    context=text[:200],
                    confidence=0.7,
                )
            )

        return references

    def detect_duplicates(
        self, term: str, definitions: list[str]
    ) -> list[dict[str, Any]]:
        """Detecteer duplicate definities."""
        duplicates = []

        # Simpele implementatie - kan later uitgebreid worden
        for i, def1 in enumerate(definitions):
            for j, def2 in enumerate(definitions[i + 1 :], i + 1):
                similarity = self._calculate_similarity(def1, def2)
                if similarity > 0.8:  # 80% gelijkenis threshold
                    duplicates.append(
                        {
                            "indices": [i, j],
                            "similarity": similarity,
                            "definitions": [def1, def2],
                        }
                    )

        return duplicates

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Bereken gelijkenis tussen twee teksten."""
        # Simpele Jaccard similarity voor nu
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 and not words2:
            return 1.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def enable_legacy_fallback(self, enabled: bool = True) -> None:
        """Schakel legacy fallback in/uit."""
        self._legacy_fallback_enabled = enabled
        logger.info(f"Legacy fallback {'enabled' if enabled else 'disabled'}")

    def get_source_status(self) -> dict[str, dict[str, Any]]:
        """Krijg status van alle bronnen voor monitoring."""
        return {
            name: {
                "enabled": config.enabled,
                "api_type": config.api_type,
                "confidence_weight": config.confidence_weight,
                "is_juridical": config.is_juridical,
            }
            for name, config in self.sources.items()
        }
