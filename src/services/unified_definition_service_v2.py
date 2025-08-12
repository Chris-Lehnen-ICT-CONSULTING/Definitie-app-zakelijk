"""
UnifiedDefinitionService V2 - Met nieuwe services integratie.

Deze versie van UnifiedDefinitionService kan zowel de legacy implementatie
als de nieuwe clean services gebruiken op basis van configuratie.
"""
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Importeer de originele UnifiedDefinitionService
from services.unified_definition_service import (
    UnifiedDefinitionService as LegacyService,
    UnifiedServiceConfig,
    UnifiedResult,
    ProcessingMode,
    ArchitectureMode
)

# Importeer nieuwe services
from services.container import ServiceContainer, get_container
from services.interfaces import GenerationRequest, Definition
from services.service_factory import ServiceAdapter

logger = logging.getLogger(__name__)


class ServiceMode(Enum):
    """Mode voor service selectie."""
    LEGACY = "legacy"          # Gebruik originele implementatie
    NEW_SERVICES = "new"       # Gebruik nieuwe clean services
    AUTO = "auto"              # Automatisch kiezen op basis van feature flag


@dataclass
class UnifiedServiceConfigV2(UnifiedServiceConfig):
    """Uitgebreide configuratie met nieuwe service opties."""
    service_mode: ServiceMode = ServiceMode.AUTO
    container_config: Optional[Dict[str, Any]] = None
    use_adapter: bool = True  # Gebruik ServiceAdapter voor compatibility


class UnifiedDefinitionService(LegacyService):
    """
    Enhanced UnifiedDefinitionService met nieuwe services integratie.
    
    Deze klasse extend de legacy service en voegt ondersteuning toe
    voor de nieuwe clean service architectuur. Het behoudt volledige
    backward compatibility.
    """
    
    _instance = None  # Singleton instance
    
    def __init__(self):
        """Initialiseer met uitgebreide functionaliteit."""
        super().__init__()
        self.config_v2 = UnifiedServiceConfigV2()
        self._container: Optional[ServiceContainer] = None
        self._adapter: Optional[ServiceAdapter] = None
        self._service_mode_cache: Optional[ServiceMode] = None
        
    def configure(self, config: Union[UnifiedServiceConfig, UnifiedServiceConfigV2]) -> None:
        """
        Update service configuratie.
        
        Args:
            config: Configuratie object (legacy of v2)
        """
        if isinstance(config, UnifiedServiceConfigV2):
            self.config_v2 = config
            # Update ook legacy config
            super().configure(config)
        else:
            # Legacy config
            super().configure(config)
            # Update alleen de legacy velden in v2
            for field in UnifiedServiceConfig.__dataclass_fields__:
                setattr(self.config_v2, field, getattr(config, field))
        
        # Reset cache
        self._service_mode_cache = None
        
        self.logger.info(f"Service V2 geconfigureerd: mode={self.config_v2.service_mode.value}")
    
    def _get_service_mode(self) -> ServiceMode:
        """Bepaal welke service mode te gebruiken."""
        if self._service_mode_cache:
            return self._service_mode_cache
        
        if self.config_v2.service_mode != ServiceMode.AUTO:
            self._service_mode_cache = self.config_v2.service_mode
        else:
            # Auto detect op basis van environment of session
            import os
            use_new = os.getenv('USE_NEW_SERVICES', 'false').lower() == 'true'
            
            try:
                import streamlit as st
                # Streamlit session state heeft voorrang
                use_new = st.session_state.get('use_new_services', use_new)
            except:
                pass
            
            self._service_mode_cache = ServiceMode.NEW_SERVICES if use_new else ServiceMode.LEGACY
        
        return self._service_mode_cache
    
    def _get_container(self) -> ServiceContainer:
        """Get of create service container."""
        if not self._container:
            self._container = get_container(self.config_v2.container_config)
        return self._container
    
    def _get_adapter(self) -> ServiceAdapter:
        """Get of create service adapter."""
        if not self._adapter:
            self._adapter = ServiceAdapter(self._get_container())
        return self._adapter
    
    # Override de hoofdmethodes
    
    def generate_definition(
        self, 
        begrip: str, 
        context_dict: Dict[str, List[str]],
        force_sync: bool = False,
        force_async: bool = False,
        **kwargs
    ) -> UnifiedResult:
        """
        Genereer definitie met nieuwe of legacy services.
        
        Deze methode routeert naar de juiste implementatie op basis
        van de service mode.
        """
        mode = self._get_service_mode()
        
        if mode == ServiceMode.NEW_SERVICES:
            return self._generate_with_new_services(begrip, context_dict, **kwargs)
        else:
            # Gebruik legacy implementatie
            return super().generate_definition(
                begrip, context_dict, force_sync, force_async, **kwargs
            )
    
    async def agenerate_definition(
        self,
        begrip: str,
        context_dict: Dict[str, List[str]],
        **kwargs
    ) -> UnifiedResult:
        """Async versie met nieuwe services ondersteuning."""
        mode = self._get_service_mode()
        
        if mode == ServiceMode.NEW_SERVICES:
            # Nieuwe services zijn al async
            return self._generate_with_new_services(begrip, context_dict, **kwargs)
        else:
            # Gebruik legacy async implementatie
            return await super().agenerate_definition(begrip, context_dict, **kwargs)
    
    def _generate_with_new_services(
        self,
        begrip: str,
        context_dict: Dict[str, List[str]],
        **kwargs
    ) -> UnifiedResult:
        """
        Genereer definitie met nieuwe clean services.
        
        Deze methode gebruikt de nieuwe architectuur maar returned
        een UnifiedResult voor compatibility.
        """
        start_time = time.time()
        
        try:
            if self.config_v2.use_adapter:
                # Gebruik adapter voor gemakkelijke conversie
                adapter = self._get_adapter()
                
                # Run async functie in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    legacy_result = loop.run_until_complete(
                        adapter.generate_definition(begrip, context_dict, **kwargs)
                    )
                finally:
                    loop.close()
                
                # Converteer naar UnifiedResult
                return self._convert_adapter_result(legacy_result, start_time)
            else:
                # Directe aanroep van orchestrator
                return self._generate_direct(begrip, context_dict, start_time, **kwargs)
                
        except Exception as e:
            self.logger.error(f"Nieuwe services generatie mislukt: {e}")
            return UnifiedResult(
                success=False,
                processing_time=time.time() - start_time,
                processing_mode=ProcessingMode.AUTO,
                architecture_mode=ArchitectureMode.MODERN,
                error_message=str(e)
            )
    
    def _generate_direct(
        self,
        begrip: str,
        context_dict: Dict[str, List[str]],
        start_time: float,
        **kwargs
    ) -> UnifiedResult:
        """Directe aanroep van orchestrator zonder adapter."""
        orchestrator = self._get_container().orchestrator()
        
        # Maak GenerationRequest
        request = GenerationRequest(
            begrip=begrip,
            context=", ".join(context_dict.get('organisatorisch', [])),
            domein=", ".join(context_dict.get('domein', [])),
            organisatie=kwargs.get('organisatie', ''),
            extra_instructies=kwargs.get('extra_instructies')
        )
        
        # Run orchestrator
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(
                orchestrator.create_definition(request)
            )
        finally:
            loop.close()
        
        # Converteer naar UnifiedResult
        if response.success and response.definition:
            result = UnifiedResult(
                success=True,
                processing_time=time.time() - start_time,
                processing_mode=ProcessingMode.AUTO,
                architecture_mode=ArchitectureMode.MODERN,
                definitie_origineel=response.definition.metadata.get('origineel', response.definition.definitie),
                definitie_gecorrigeerd=response.definition.definitie,
                marker=response.definition.metadata.get('marker', ''),
                voorbeelden={'voorbeelden': response.definition.voorbeelden} if response.definition.voorbeelden else {},
                metadata=response.definition.metadata or {}
            )
            
            if response.validation:
                result.toetsresultaten = response.validation.errors
                result.validation_score = response.validation.score
                result.validation_result = response.validation
            
            return result
        else:
            return UnifiedResult(
                success=False,
                processing_time=time.time() - start_time,
                processing_mode=ProcessingMode.AUTO,
                architecture_mode=ArchitectureMode.MODERN,
                error_message=response.message or 'Generatie mislukt'
            )
    
    def _convert_adapter_result(self, adapter_result: Dict[str, Any], start_time: float) -> UnifiedResult:
        """Converteer adapter result naar UnifiedResult."""
        result = UnifiedResult(
            success=adapter_result.get('success', False),
            processing_time=adapter_result.get('processing_time', time.time() - start_time),
            processing_mode=ProcessingMode.AUTO,
            architecture_mode=ArchitectureMode.MODERN,
            definitie_origineel=adapter_result.get('definitie_origineel', ''),
            definitie_gecorrigeerd=adapter_result.get('definitie_gecorrigeerd', ''),
            marker=adapter_result.get('marker', ''),
            toetsresultaten=adapter_result.get('toetsresultaten', []),
            validation_score=adapter_result.get('validation_score', 0.0),
            voorbeelden={'voorbeelden': adapter_result.get('voorbeelden', [])},
            error_message=adapter_result.get('error_message', '')
        )
        
        return result
    
    # Extra utility methods
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get informatie over de actieve service mode."""
        mode = self._get_service_mode()
        
        info = {
            'service_mode': mode.value,
            'architecture': 'clean' if mode == ServiceMode.NEW_SERVICES else 'legacy',
            'version': '2.0' if mode == ServiceMode.NEW_SERVICES else '1.0',
            'features': []
        }
        
        if mode == ServiceMode.NEW_SERVICES:
            info['features'] = [
                'dependency_injection',
                'clean_architecture',
                'enhanced_validation',
                'service_orchestration'
            ]
            info['container_stats'] = self._get_adapter().get_stats()
        else:
            info['features'] = [
                'unified_service',
                'adaptive_processing',
                'legacy_compatibility'
            ]
        
        return info
    
    @classmethod
    def get_instance(cls) -> 'UnifiedDefinitionService':
        """Get singleton instance (override voor V2)."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance