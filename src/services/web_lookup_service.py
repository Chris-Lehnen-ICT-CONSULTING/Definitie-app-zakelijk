"""
Web Lookup Service implementatie.

Deze service consolideerd alle web lookup functionaliteit met:
- UTF-8 encoding fixes
- Dependency injection support
- Rate limiting
- Caching
- Unified interface
"""
import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from services.interfaces import (
    WebLookupServiceInterface, 
    LookupRequest, 
    LookupResult, 
    WebSource,
    JuridicalReference
)
from utils.cache import cache_async_result
from config.config_manager import get_config_manager

# Import legacy modules voor hergebruik
from web_lookup.lookup import (
    zoek_definitie_op_wikipedia,
    zoek_definitie_op_wiktionary,
    zoek_definitie_op_overheidnl,
    zoek_definitie_op_wettennl,
    zoek_definitie_op_ensie,
    zoek_definitie_op_strafrechtketen,
    zoek_definitie_op_kamerstukken
)
# TEMP DISABLED - Missing functions during fix
# from web_lookup.bron_lookup import valideer_bron_betrouwbaarheid
# from web_lookup.juridische_lookup import extract_juridische_verwijzingen  
# from web_lookup.definitie_lookup import GelijkenisAnalyzer

logger = logging.getLogger(__name__)


class WebLookupService(WebLookupServiceInterface):
    """
    Unified web lookup service met dependency injection support.
    
    Consolideerd alle web lookup functionaliteit in één service.
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialiseer de web lookup service.
        
        Args:
            config: Optionele configuratie
        """
        # TEMP FIX: Use config manager instead of Config class
        self.config = config or get_config_manager()
        self._rate_limits = {}  # Track rate limits per source
        self._sources = self._initialize_sources()
        # TEMP DISABLED - Missing class during fix
        # self._gelijkenis_analyzer = GelijkenisAnalyzer()
        self._gelijkenis_analyzer = None
        
    def _initialize_sources(self) -> List[WebSource]:
        """Initialiseer beschikbare web bronnen."""
        return [
            WebSource(
                name="Wikipedia",
                url="https://nl.wikipedia.org",
                confidence=0.85,
                is_juridical=False,
                api_type="mediawiki"
            ),
            WebSource(
                name="Wiktionary",
                url="https://nl.wiktionary.org",
                confidence=0.80,
                is_juridical=False,
                api_type="mediawiki"
            ),
            WebSource(
                name="Overheid.nl",
                url="https://repository.overheid.nl",
                confidence=0.95,
                is_juridical=True,
                api_type="sru"
            ),
            WebSource(
                name="Wetten.nl",
                url="https://wetten.overheid.nl",
                confidence=0.95,
                is_juridical=True,
                api_type="scraping"
            ),
            WebSource(
                name="Ensie",
                url="https://www.ensie.nl",
                confidence=0.75,
                is_juridical=False,
                api_type="scraping"
            ),
            WebSource(
                name="Strafrechtketen",
                url="https://www.strafrechtketen.nl",
                confidence=0.90,
                is_juridical=True,
                api_type="scraping"
            ),
            WebSource(
                name="Kamerstukken",
                url="https://www.tweedekamer.nl",
                confidence=0.85,
                is_juridical=True,
                api_type="scraping"
            )
        ]
    
    async def lookup(self, request: LookupRequest) -> List[LookupResult]:
        """
        Zoek een term op in web bronnen.
        
        Args:
            request: LookupRequest met zoekterm en opties
            
        Returns:
            Lijst van LookupResult objecten
        """
        results = []
        sources = request.sources or [s.name for s in self._sources]
        
        # Check rate limits
        for source_name in sources:
            if self._is_rate_limited(source_name):
                logger.warning(f"Rate limit bereikt voor {source_name}")
                continue
        
        # Parallel lookup met timeout
        tasks = []
        for source_name in sources:
            if source_name in [s.name for s in self._sources]:
                task = self._lookup_with_timeout(
                    source_name, 
                    request.term,
                    request.timeout
                )
                tasks.append(task)
        
        # Verzamel resultaten
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in completed_results:
            if isinstance(result, Exception):
                logger.error(f"Lookup fout: {result}")
                continue
            if result:
                results.append(result)
        
        # Sorteer op confidence
        results.sort(key=lambda x: x.source.confidence, reverse=True)
        
        # Limiteer resultaten
        if request.max_results:
            results = results[:request.max_results]
        
        return results
    
    async def lookup_single_source(self, term: str, source: str) -> Optional[LookupResult]:
        """
        Zoek een term op in een specifieke bron.
        
        Args:
            term: Zoekterm
            source: Naam van de bron
            
        Returns:
            LookupResult indien gevonden, anders None
        """
        if self._is_rate_limited(source):
            logger.warning(f"Rate limit bereikt voor {source}")
            return None
            
        return await self._lookup_with_timeout(source, term, 30)
    
    @cache_async_result(ttl=3600)  # Cache voor 1 uur
    async def _lookup_with_timeout(
        self, 
        source_name: str, 
        term: str, 
        timeout: int
    ) -> Optional[LookupResult]:
        """
        Voer lookup uit met timeout.
        
        Args:
            source_name: Naam van de bron
            term: Zoekterm
            timeout: Timeout in seconden
            
        Returns:
            LookupResult indien gevonden
        """
        source = next((s for s in self._sources if s.name == source_name), None)
        if not source:
            return None
        
        try:
            # Update rate limit
            self._update_rate_limit(source_name)
            
            # Voer lookup uit
            if source_name == "Wikipedia":
                result = await asyncio.wait_for(
                    zoek_wikipedia(term), 
                    timeout=timeout
                )
            elif source_name == "Wiktionary":
                result = await asyncio.wait_for(
                    zoek_wiktionary(term),
                    timeout=timeout
                )
            elif source_name == "Overheid.nl":
                result = await asyncio.wait_for(
                    zoek_overheid(term),
                    timeout=timeout
                )
            elif source_name == "Wetten.nl":
                result = await asyncio.wait_for(
                    zoek_wetten(term),
                    timeout=timeout
                )
            elif source_name == "Ensie":
                result = await asyncio.wait_for(
                    zoek_ensie(term),
                    timeout=timeout
                )
            elif source_name == "Strafrechtketen":
                result = await asyncio.wait_for(
                    zoek_strafrechtketen(term),
                    timeout=timeout
                )
            elif source_name == "Kamerstukken":
                result = await asyncio.wait_for(
                    zoek_kamerstukken(term),
                    timeout=timeout
                )
            else:
                return None
            
            # Converteer naar LookupResult
            if result:
                return LookupResult(
                    term=term,
                    source=source,
                    definition=result.get("definitie"),
                    context=result.get("context"),
                    examples=result.get("voorbeelden", []),
                    references=result.get("verwijzingen", []),
                    success=True,
                    metadata=result
                )
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout bij lookup in {source_name}")
            return LookupResult(
                term=term,
                source=source,
                success=False,
                error_message=f"Timeout na {timeout} seconden"
            )
        except Exception as e:
            logger.error(f"Fout bij lookup in {source_name}: {e}")
            return LookupResult(
                term=term,
                source=source,
                success=False,
                error_message=str(e)
            )
        
        return None
    
    def get_available_sources(self) -> List[WebSource]:
        """
        Geef lijst van beschikbare web bronnen.
        
        Returns:
            Lijst van WebSource objecten
        """
        return self._sources.copy()
    
    def validate_source(self, text: str) -> WebSource:
        """
        Valideer en identificeer de bron van een tekst.
        
        Args:
            text: Te valideren tekst
            
        Returns:
            WebSource met betrouwbaarheidsscore
        """
        bron_info = valideer_bron_betrouwbaarheid(text)
        
        # Zoek matching source
        for source in self._sources:
            if source.name.lower() in text.lower():
                source.confidence = bron_info.get("betrouwbaarheid", 0.5)
                return source
        
        # Default source
        return WebSource(
            name="Onbekend",
            url="",
            confidence=bron_info.get("betrouwbaarheid", 0.0),
            is_juridical=bron_info.get("is_juridisch", False)
        )
    
    def find_juridical_references(self, text: str) -> List[JuridicalReference]:
        """
        Vind juridische verwijzingen in tekst.
        
        Args:
            text: Te analyseren tekst
            
        Returns:
            Lijst van gevonden juridische verwijzingen
        """
        verwijzingen = extract_juridische_verwijzingen(text)
        
        juridical_refs = []
        for verwijzing in verwijzingen:
            juridical_refs.append(JuridicalReference(
                type=verwijzing.get("type", "onbekend"),
                reference=verwijzing.get("verwijzing", ""),
                context=verwijzing.get("context", ""),
                confidence=verwijzing.get("betrouwbaarheid", 0.8)
            ))
        
        return juridical_refs
    
    def detect_duplicates(self, term: str, definitions: List[str]) -> List[Dict[str, Any]]:
        """
        Detecteer duplicate definities.
        
        Args:
            term: Zoekterm
            definitions: Lijst van definities om te vergelijken
            
        Returns:
            Lijst van duplicaat analyses
        """
        duplicates = []
        
        for i, def1 in enumerate(definitions):
            for j, def2 in enumerate(definitions[i+1:], i+1):
                gelijkenis = self._gelijkenis_analyzer.bereken_gelijkenis(def1, def2)
                
                if gelijkenis > 0.7:  # Threshold voor duplicaat
                    duplicates.append({
                        "index1": i,
                        "index2": j,
                        "definition1": def1,
                        "definition2": def2,
                        "similarity": gelijkenis,
                        "is_duplicate": gelijkenis > 0.85
                    })
        
        return duplicates
    
    def _is_rate_limited(self, source: str) -> bool:
        """
        Check of een bron rate limited is.
        
        Args:
            source: Naam van de bron
            
        Returns:
            True indien rate limited
        """
        if source not in self._rate_limits:
            return False
        
        last_request, count = self._rate_limits[source]
        now = datetime.now()
        
        # Reset counter na 1 minuut
        if now - last_request > timedelta(minutes=1):
            self._rate_limits[source] = (now, 0)
            return False
        
        # Max 10 requests per minuut per bron
        return count >= 10
    
    def _update_rate_limit(self, source: str) -> None:
        """
        Update rate limit counter voor een bron.
        
        Args:
            source: Naam van de bron
        """
        now = datetime.now()
        
        if source not in self._rate_limits:
            self._rate_limits[source] = (now, 1)
        else:
            last_request, count = self._rate_limits[source]
            if now - last_request > timedelta(minutes=1):
                self._rate_limits[source] = (now, 1)
            else:
                self._rate_limits[source] = (last_request, count + 1)


# Factory functie voor dependency injection
def create_web_lookup_service(config: Optional[Any] = None) -> WebLookupService:
    """
    Factory functie voor het creëren van een WebLookupService.
    
    Args:
        config: Optionele configuratie
        
    Returns:
        WebLookupService instantie
    """
    return WebLookupService(config)