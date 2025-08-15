"""
Unified Definition Service - Geconsolideerde service voor definitie verwerking.

Deze service combineert synchrone en asynchrone functionaliteit in één adaptieve
interface, met ondersteuning voor zowel legacy als moderne architectuur componenten.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import functools

# Utils en error handling imports
from utils.exceptions import (
    handle_api_error, handle_validation_error,
    APIError, ValidationError, safe_execute
)

# UI Session State Management
from ui.session_state import SessionStateManager

# Core functionaliteit imports
from definitie_generator.generator import genereer_definitie
from prompt_builder.prompt_builder import stuur_prompt_naar_gpt, PromptBouwer, PromptConfiguratie
from ai_toetser import toets_definitie
from opschoning.opschoning import opschonen

# Unified voorbeelden module - recent geconsolideerd
from voorbeelden.unified_voorbeelden import (
    get_examples_generator, ExampleRequest, ExampleType, GenerationMode,
    genereer_alle_voorbeelden, genereer_alle_voorbeelden_async
)

# Moderne architectuur imports (optioneel)
try:
    from generation.definitie_generator import DefinitieGenerator, GenerationContext, OntologischeCategorie
    from validation.definitie_validator import DefinitieValidator, validate_definitie, ValidationResult
    from database.definitie_repository import DefinitieRepository, DefinitieRecord, DefinitieStatus
    from integration.definitie_checker import DefinitieChecker
    MODERN_ARCHITECTURE_AVAILABLE = True
except ImportError:
    MODERN_ARCHITECTURE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Moderne architectuur modules niet beschikbaar - gebruik legacy mode")

# Web lookup imports (optioneel)
try:
    from web_lookup.bron_lookup import zoek_bronnen_voor_begrip, valideer_definitie_bronnen
    from web_lookup.definitie_lookup import zoek_definitie, detecteer_duplicaten
    WEB_LOOKUP_AVAILABLE = True
except (ImportError, UnicodeDecodeError):
    WEB_LOOKUP_AVAILABLE = False

# Monitoring imports (optioneel)
try:
    from monitoring.api_monitor import record_api_call
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

# Logging setup
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from logs.application.log_definitie import log_definitie

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """Verwerkingsmodus voor de service."""
    SYNC = "sync"      # Synchrone verwerking
    ASYNC = "async"    # Asynchrone verwerking
    AUTO = "auto"      # Automatisch kiezen op basis van context


class ArchitectureMode(Enum):
    """Architectuur modus voor de service."""
    LEGACY = "legacy"  # Gebruik legacy componenten
    MODERN = "modern"  # Gebruik moderne componenten
    AUTO = "auto"      # Automatisch kiezen op basis van beschikbaarheid


@dataclass
class UnifiedServiceConfig:
    """Configuratie voor de unified service."""
    processing_mode: ProcessingMode = ProcessingMode.AUTO
    architecture_mode: ArchitectureMode = ArchitectureMode.AUTO
    enable_caching: bool = True
    enable_monitoring: bool = True
    enable_web_lookup: bool = True
    enable_validation: bool = True
    enable_examples: bool = True
    default_timeout: float = 30.0
    max_retries: int = 3
    parallel_processing: bool = True
    progress_callback: Optional[Callable[[str, float], None]] = None


@dataclass
class UnifiedResult:
    """Unified result container voor alle service operaties."""
    success: bool
    processing_time: float
    processing_mode: ProcessingMode
    architecture_mode: ArchitectureMode
    
    # Core definitie data
    definitie_origineel: str = ""
    definitie_gecorrigeerd: str = ""
    marker: str = ""
    
    # Validatie resultaten
    toetsresultaten: List[str] = field(default_factory=list)
    validation_score: float = 0.0
    validation_result: Optional[Any] = None
    
    # Voorbeelden en extra content
    voorbeelden: Dict[str, List[str]] = field(default_factory=dict)
    bronnen_tekst: str = ""
    web_lookup_results: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata en metrics
    metadata: Dict[str, Any] = field(default_factory=dict)
    cache_hits: int = 0
    total_requests: int = 0
    error_message: str = ""
    
    # Modern architecture data (optional)
    definitie_record: Optional[Any] = None


class UnifiedDefinitionService:
    """
    Geconsolideerde service voor definitie verwerking.
    
    Deze service combineert:
    - Synchrone en asynchrone verwerking
    - Legacy en moderne architectuur
    - Alle functionaliteit uit 3 separate services
    """
    
    # Singleton instance
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger(__name__)
            self.config = UnifiedServiceConfig()
            self._stats = {
                'total_generations': 0,
                'sync_operations': 0,
                'async_operations': 0,
                'cache_hits': 0,
                'errors': 0
            }
            self._initialized = True
    
    def configure(self, config: UnifiedServiceConfig) -> None:
        """Update service configuratie."""
        self.config = config
        self.logger.info(f"Service geconfigureerd: processing={config.processing_mode.value}, architecture={config.architecture_mode.value}")
    
    # ===== PUBLIC API METHODS =====
    
    def generate_definition(
        self, 
        begrip: str, 
        context_dict: Dict[str, List[str]],
        force_sync: bool = False,
        force_async: bool = False,
        **kwargs
    ) -> UnifiedResult:
        """
        Genereer definitie met adaptieve sync/async verwerking.
        
        Args:
            begrip: Het begrip om te definiëren
            context_dict: Context informatie
            force_sync: Forceer synchrone verwerking
            force_async: Forceer asynchrone verwerking
            **kwargs: Extra opties voor specifieke implementaties
            
        Returns:
            UnifiedResult met alle gegenereerde data
        """
        # Bepaal verwerkingsmodus
        if force_async or (self.config.processing_mode == ProcessingMode.ASYNC and not force_sync):
            return asyncio.run(self.agenerate_definition(begrip, context_dict, **kwargs))
        else:
            return self._generate_definition_sync(begrip, context_dict, **kwargs)
    
    async def agenerate_definition(
        self,
        begrip: str,
        context_dict: Dict[str, List[str]],
        **kwargs
    ) -> UnifiedResult:
        """Asynchrone definitie generatie met parallelle verwerking."""
        start_time = time.time()
        self._stats['async_operations'] += 1
        
        result = UnifiedResult(
            success=False,
            processing_time=0,
            processing_mode=ProcessingMode.ASYNC,
            architecture_mode=self._get_architecture_mode()
        )
        
        try:
            # Progress callback
            if self.config.progress_callback:
                self.config.progress_callback("Definitie generatie gestart...", 0.1)
            
            # Genereer definitie (basis)
            definitie_task = self._generate_base_definition_async(begrip, context_dict)
            
            # Start parallelle taken indien geconfigureerd
            tasks = [definitie_task]
            
            if self.config.enable_web_lookup and WEB_LOOKUP_AVAILABLE:
                tasks.append(self._lookup_sources_async(begrip, context_dict))
            
            # Wacht op basis definitie
            definitie_result = await definitie_task
            result.definitie_origineel = definitie_result[0]
            result.definitie_gecorrigeerd = definitie_result[1]
            result.marker = definitie_result[2]
            
            # Progress update
            if self.config.progress_callback:
                self.config.progress_callback("Definitie gegenereerd, validatie gestart...", 0.4)
            
            # Validatie
            if self.config.enable_validation:
                validation_result = await self._validate_definition_async(
                    result.definitie_gecorrigeerd,
                    begrip,
                    context_dict
                )
                result.toetsresultaten = validation_result[0]
                result.validation_score = validation_result[1]
            
            # Voorbeelden generatie (parallel)
            if self.config.enable_examples:
                if self.config.progress_callback:
                    self.config.progress_callback("Voorbeelden genereren...", 0.6)
                
                voorbeelden = await genereer_alle_voorbeelden_async(
                    begrip,
                    result.definitie_gecorrigeerd,
                    context_dict
                )
                result.voorbeelden = voorbeelden
            
            # Verzamel alle parallelle resultaten
            if len(tasks) > 1:
                parallel_results = await asyncio.gather(*tasks[1:], return_exceptions=True)
                for task_result in parallel_results:
                    if isinstance(task_result, dict) and 'bronnen' in task_result:
                        result.bronnen_tekst = task_result.get('bronnen_tekst', '')
                        result.web_lookup_results = task_result
            
            # Update session state
            self._update_session_state(result)
            
            # Log definitie
            self._log_definition_version(begrip, result)
            
            result.success = True
            result.processing_time = time.time() - start_time
            result.total_requests = self._stats['total_generations']
            
            if self.config.progress_callback:
                self.config.progress_callback("Verwerking voltooid!", 1.0)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Async definitie generatie mislukt: {e}")
            result.error_message = str(e)
            result.processing_time = time.time() - start_time
            self._stats['errors'] += 1
            return result
    
    def _generate_definition_sync(
        self,
        begrip: str,
        context_dict: Dict[str, List[str]],
        **kwargs
    ) -> UnifiedResult:
        """Synchrone definitie generatie implementatie."""
        start_time = time.time()
        self._stats['sync_operations'] += 1
        
        result = UnifiedResult(
            success=False,
            processing_time=0,
            processing_mode=ProcessingMode.SYNC,
            architecture_mode=self._get_architecture_mode()
        )
        
        try:
            # Genereer definitie
            definitie_origineel, definitie_gecorrigeerd, marker = self._generate_base_definition_sync(
                begrip, context_dict
            )
            
            result.definitie_origineel = definitie_origineel
            result.definitie_gecorrigeerd = definitie_gecorrigeerd
            result.marker = marker
            
            # Validatie
            if self.config.enable_validation:
                toetsresultaten, score = self._validate_definition_sync(
                    definitie_gecorrigeerd,
                    begrip,
                    context_dict
                )
                result.toetsresultaten = toetsresultaten
                result.validation_score = score
            
            # Bronnen lookup
            if self.config.enable_web_lookup and WEB_LOOKUP_AVAILABLE:
                bronnen_data = self._lookup_sources_sync(begrip, context_dict)
                result.bronnen_tekst = bronnen_data.get('bronnen_tekst', '')
                result.web_lookup_results = bronnen_data
            
            # Voorbeelden generatie
            if self.config.enable_examples:
                voorbeelden = genereer_alle_voorbeelden(
                    begrip,
                    definitie_gecorrigeerd,
                    context_dict,
                    mode=GenerationMode.SYNC
                )
                result.voorbeelden = voorbeelden
            
            # Update session state
            self._update_session_state(result)
            
            # Log definitie
            self._log_definition_version(begrip, result)
            
            result.success = True
            result.processing_time = time.time() - start_time
            result.total_requests = self._stats['total_generations']
            
            return result
            
        except Exception as e:
            self.logger.error(f"Sync definitie generatie mislukt: {e}")
            result.error_message = str(e)
            result.processing_time = time.time() - start_time
            self._stats['errors'] += 1
            return result
    
    # ===== PRIVATE HELPER METHODS =====
    
    def _get_architecture_mode(self) -> ArchitectureMode:
        """Bepaal welke architectuur modus te gebruiken."""
        if self.config.architecture_mode != ArchitectureMode.AUTO:
            return self.config.architecture_mode
        
        if MODERN_ARCHITECTURE_AVAILABLE:
            return ArchitectureMode.MODERN
        else:
            return ArchitectureMode.LEGACY
    
    @handle_api_error
    def _generate_base_definition_sync(
        self, 
        begrip: str, 
        context_dict: Dict[str, List[str]]
    ) -> Tuple[str, str, str]:
        """Genereer basis definitie (sync)."""
        self._stats['total_generations'] += 1
        
        # Build prompt
        prompt = self._build_prompt(begrip, context_dict)
        
        # Generate definition
        definitie = stuur_prompt_naar_gpt(prompt, "gpt-4", 0.4, 500)
        
        # Clean up
        definitie_gecorrigeerd = opschonen(definitie, begrip)
        
        # Determine marker
        if definitie == definitie_gecorrigeerd:
            marker = "✅ Opschoning niet nodig"
        else:
            marker = "🔧 Definitie is opgeschoond"
        
        return definitie, definitie_gecorrigeerd, marker
    
    async def _generate_base_definition_async(
        self,
        begrip: str,
        context_dict: Dict[str, List[str]]
    ) -> Tuple[str, str, str]:
        """Genereer basis definitie (async)."""
        # Gebruik executor voor sync functie
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._generate_base_definition_sync,
            begrip,
            context_dict
        )
    
    def _validate_definition_sync(
        self,
        definitie: str,
        begrip: str,
        context_dict: Dict[str, List[str]]
    ) -> Tuple[List[str], float]:
        """Valideer definitie (sync)."""
        beoordeling = toets_definitie(
            definitie,
            begrip,
            context_dict.get('organisatorisch', []),
            context_dict.get('juridisch', [])
        )
        
        # Bereken score
        passed = sum(1 for regel in beoordeling if "✔️" in regel)
        total = len(beoordeling)
        score = passed / total if total > 0 else 0.0
        
        return beoordeling, score
    
    async def _validate_definition_async(
        self,
        definitie: str,
        begrip: str,
        context_dict: Dict[str, List[str]]
    ) -> Tuple[List[str], float]:
        """Valideer definitie (async)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._validate_definition_sync,
            definitie,
            begrip,
            context_dict
        )
    
    def _lookup_sources_sync(
        self,
        begrip: str,
        context_dict: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Zoek bronnen (sync)."""
        try:
            bronnen = zoek_bronnen_voor_begrip(begrip, context_dict)
            bronnen_tekst = "\n".join([
                f"- {bron['titel']} ({bron['type']})"
                for bron in bronnen[:5]
            ])
            
            return {
                'bronnen': bronnen,
                'bronnen_tekst': bronnen_tekst,
                'count': len(bronnen)
            }
        except Exception as e:
            self.logger.warning(f"Bronnen lookup mislukt: {e}")
            return {'bronnen': [], 'bronnen_tekst': '', 'count': 0}
    
    async def _lookup_sources_async(
        self,
        begrip: str,
        context_dict: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Zoek bronnen (async)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._lookup_sources_sync,
            begrip,
            context_dict
        )
    
    def _build_prompt(self, begrip: str, context_dict: Dict[str, List[str]]) -> str:
        """Bouw prompt voor definitie generatie."""
        configuratie = PromptConfiguratie(
            begrip=begrip,
            organisatorische_context=", ".join(context_dict.get('organisatorisch', [])),
            juridische_context=", ".join(context_dict.get('juridisch', [])),
            wettelijke_basis=", ".join(context_dict.get('wettelijk', [])),
            use_sophisticated_prompt=True
        )
        
        prompt_builder = PromptBouwer(configuratie)
        return prompt_builder.bouw_definitie_prompt()
    
    def _update_session_state(self, result: UnifiedResult) -> None:
        """Update session state met resultaten."""
        SessionStateManager.update_definition_results(
            result.definitie_origineel,
            result.definitie_gecorrigeerd,
            result.marker
        )
        
        SessionStateManager.set_value("bronnen_tekst", result.bronnen_tekst)
        SessionStateManager.set_value("beoordeling_gen", result.toetsresultaten)
        
        # Update voorbeelden
        if result.voorbeelden:
            SessionStateManager.set_value("voorbeeld_zinnen", result.voorbeelden.get('sentence', []))
            SessionStateManager.set_value("praktijkvoorbeelden", result.voorbeelden.get('practical', []))
            SessionStateManager.set_value("tegenvoorbeelden", result.voorbeelden.get('counter', []))
            SessionStateManager.set_value("synoniemen", "\n".join(result.voorbeelden.get('synonyms', [])))
            SessionStateManager.set_value("antoniemen", "\n".join(result.voorbeelden.get('antonyms', [])))
            
            explanation = result.voorbeelden.get('explanation', [])
            SessionStateManager.set_value("toelichting", explanation[0] if explanation else "")
    
    def _log_definition_version(self, begrip: str, result: UnifiedResult) -> None:
        """Log definitie versie."""
        log_data = {
            'begrip': begrip,
            'definitie_origineel': result.definitie_origineel,
            'definitie_gecorrigeerd': result.definitie_gecorrigeerd,
            'opgeschoond': result.definitie_origineel != result.definitie_gecorrigeerd,
            'validation_score': result.validation_score,
            'processing_mode': result.processing_mode.value,
            'architecture_mode': result.architecture_mode.value,
            'processing_time': result.processing_time,
            'success': result.success
        }
        
        log_definitie(log_data)
    
    # ===== CONVENIENCE METHODS =====
    
    def get_statistics(self) -> Dict[str, Any]:
        """Haal service statistieken op."""
        return {
            **self._stats,
            'success_rate': (
                (self._stats['total_generations'] - self._stats['errors']) / 
                self._stats['total_generations']
            ) if self._stats['total_generations'] > 0 else 0
        }
    
    def reset_statistics(self) -> None:
        """Reset service statistieken."""
        self._stats = {
            'total_generations': 0,
            'sync_operations': 0,
            'async_operations': 0,
            'cache_hits': 0,
            'errors': 0
        }


# ===== BACKWARD COMPATIBILITY LAYER =====

class DefinitionService(UnifiedDefinitionService):
    """Backward compatibility wrapper voor legacy DefinitionService."""
    
    def __init__(self):
        super().__init__()
        self.configure(UnifiedServiceConfig(
            processing_mode=ProcessingMode.SYNC,
            architecture_mode=ArchitectureMode.LEGACY
        ))
    
    def generate_definition(self, begrip: str, context_dict: Dict[str, List[str]]) -> Tuple[str, str, str]:
        """Legacy interface voor definitie generatie."""
        result = super().generate_definition(begrip, context_dict, force_sync=True)
        return result.definitie_origineel, result.definitie_gecorrigeerd, result.marker
    
    def generate_sources(self, begrip: str, context_dict: Dict[str, List[str]]) -> str:
        """Legacy interface voor bronnen generatie."""
        if WEB_LOOKUP_AVAILABLE:
            bronnen_data = self._lookup_sources_sync(begrip, context_dict)
            return bronnen_data.get('bronnen_tekst', '')
        return ""
    
    def validate_definition(self, definitie: str, begrip: str, context_dict: Dict[str, List[str]]) -> List[str]:
        """Legacy interface voor definitie validatie."""
        toetsresultaten, _ = self._validate_definition_sync(definitie, begrip, context_dict)
        return toetsresultaten


class AsyncDefinitionService(UnifiedDefinitionService):
    """Backward compatibility wrapper voor legacy AsyncDefinitionService."""
    
    def __init__(self):
        super().__init__()
        self.configure(UnifiedServiceConfig(
            processing_mode=ProcessingMode.ASYNC,
            architecture_mode=ArchitectureMode.LEGACY
        ))
    
    async def process_definition(
        self,
        begrip: str,
        context_dict: Dict[str, List[str]],
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Any:
        """Legacy interface voor async definitie verwerking."""
        # Update config met callback
        self.config.progress_callback = progress_callback
        
        # Genereer definitie
        result = await self.agenerate_definition(begrip, context_dict)
        
        # Converteer naar legacy AsyncProcessingResult
        from services.async_definition_service import AsyncProcessingResult
        
        return AsyncProcessingResult(
            success=result.success,
            processing_time=result.processing_time,
            definitie_origineel=result.definitie_origineel,
            definitie_gecorrigeerd=result.definitie_gecorrigeerd,
            marker=result.marker,
            bronnen_tekst=result.bronnen_tekst,
            toetsresultaten=result.toetsresultaten,
            error_message=result.error_message,
            cache_hits=result.cache_hits,
            total_requests=result.total_requests
        )


# ===== FACTORY FUNCTIONS =====

def get_definition_service(
    mode: Union[str, ProcessingMode] = ProcessingMode.AUTO,
    **kwargs
) -> UnifiedDefinitionService:
    """
    Factory functie voor het verkrijgen van de juiste service instantie.
    
    Args:
        mode: Processing mode (sync/async/auto)
        **kwargs: Extra configuratie opties
        
    Returns:
        Geconfigureerde UnifiedDefinitionService instantie
    """
    service = UnifiedDefinitionService()
    
    # Parse mode
    if isinstance(mode, str):
        mode = ProcessingMode(mode)
    
    # Configureer service
    config = UnifiedServiceConfig(processing_mode=mode, **kwargs)
    service.configure(config)
    
    return service


# Global instance voor gemakkelijke toegang
_default_service = None

def get_default_service() -> UnifiedDefinitionService:
    """Verkrijg default service instantie."""
    global _default_service
    if _default_service is None:
        _default_service = UnifiedDefinitionService()
    return _default_service