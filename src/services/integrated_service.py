"""
Geïntegreerde Service Laag - Uniform interface voor alle definitie verwerkingsdiensten.

Verbindt legacy en moderne architecturen met een consistente API.
Biedt centrale toegang tot alle definitie generatie en validatie functionaliteiten.
"""

import asyncio  # Asynchrone programmering voor niet-blokkerende operaties
import logging  # Logging faciliteiten voor debug en monitoring
from typing import Dict, List, Any, Optional, Tuple, Union  # Type hints voor betere code documentatie
from dataclasses import dataclass, field  # Dataklassen voor gestructureerde data
from datetime import datetime  # Datum en tijd functionaliteit
from enum import Enum  # Enumeraties voor constante waarden

# Moderne architectuur imports - nieuwe modulaire systeem componenten
from database.definitie_repository import DefinitieRepository, DefinitieRecord, DefinitieStatus, get_definitie_repository  # Database toegang
from generation.definitie_generator import DefinitieGenerator, GenerationContext, OntologischeCategorie  # Definitie generatie
from validation.definitie_validator import DefinitieValidator, validate_definitie, ValidationResult  # Definitie validatie
from integration.definitie_checker import DefinitieChecker  # Definitie integratie controle

# Legacy imports - bestaande service implementaties voor achterwaartse compatibiliteit
from services.definition_service import DefinitionService  # Synchrone legacy service
from services.async_definition_service import AsyncDefinitionService  # Asynchrone legacy service

# Opschoning module import - voor het opschonen van gegenereerde definities
try:
    from opschoning.opschoning import opschonen  # Importeer opschoning functie
    OPSCHONING_AVAILABLE = True  # Module succesvol geladen
except ImportError:
    print("Opschoning module niet beschikbaar")  # Log waarschuwing
    OPSCHONING_AVAILABLE = False  # Module niet beschikbaar

# Web lookup imports
try:
    from web_lookup.bron_lookup import zoek_bronnen_voor_begrip, valideer_definitie_bronnen
    from web_lookup.definitie_lookup import zoek_definitie, detecteer_duplicaten
    WEB_LOOKUP_AVAILABLE = True
except (ImportError, UnicodeDecodeError) as e:
    print(f"Web lookup modules not available: {e}")
    WEB_LOOKUP_AVAILABLE = False

# Monitoring imports
try:
    from monitoring.api_monitor import record_api_call
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False  # Monitoring niet beschikbaar

logger = logging.getLogger(__name__)  # Logger instantie voor deze module


class ServiceMode(Enum):
    """Service operatie modi voor verschillende architectuur integraties."""
    LEGACY = "legacy"  # Gebruik alleen legacy systeem componenten
    MODERN = "modern"  # Gebruik alleen moderne modulaire componenten
    HYBRID = "hybrid"  # Combineer legacy en moderne componenten
    AUTO = "auto"      # Automatisch kiezen op basis van beschikbaarheid


@dataclass
class ServiceConfig:
    """Configuratie voor geïntegreerde service met standaard instellingen."""
    mode: ServiceMode = ServiceMode.AUTO      # Service modus (auto-detectie standaard)
    enable_caching: bool = True               # Cache resultaten voor snellere responses
    enable_monitoring: bool = True            # Monitor API gebruik en prestaties
    enable_web_lookup: bool = True            # Zoek in externe web bronnen
    enable_validation: bool = True            # Valideer gegenereerde definities
    default_timeout: float = 30.0             # Standaard timeout in seconden
    max_retries: int = 3                      # Maximum aantal herhaalpogingen bij fouten
    parallel_processing: bool = True


@dataclass
class IntegratedResult:
    """Unified result container for all service operations."""
    success: bool
    operation: str
    processing_time: float
    service_mode: ServiceMode
    
    # Core definition data
    definitie_record: Optional[DefinitieRecord] = None
    validation_result: Optional[ValidationResult] = None
    
    # Legacy compatibility
    definitie_origineel: str = ""
    definitie_gecorrigeerd: str = ""
    marker: str = ""
    toetsresultaten: List[str] = field(default_factory=list)
    
    # Extended data
    bronnen: List[Any] = field(default_factory=list)
    web_lookup_results: Dict[str, Any] = field(default_factory=dict)
    duplicate_analysis: Dict[str, Any] = field(default_factory=dict)
    examples: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    cache_hits: int = 0
    total_requests: int = 0
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)


class IntegratedDefinitionService:
    """Unified service layer for all definition processing operations."""
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        """Initialize integrated service."""
        self.config = config or ServiceConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize services based on availability and config
        self._init_services()
        
        # Performance tracking
        self.operation_stats = {}
    
    def _init_services(self):
        """Initialize available services."""
        # Core services (always available)
        self.repository = get_definitie_repository()
        self.checker = DefinitieChecker(self.repository)
        
        # Modern services
        try:
            self.modern_generator = DefinitieGenerator()
            self.modern_validator = DefinitieValidator()
            self.modern_available = True
        except Exception as e:
            self.logger.warning(f"Modern services not available: {e}")
            self.modern_available = False
        
        # Legacy services
        try:
            self.legacy_service = DefinitionService()
            self.async_service = AsyncDefinitionService()
            self.legacy_available = True
        except Exception as e:
            self.logger.warning(f"Legacy services not available: {e}")
            self.legacy_available = False
        
        # Determine best available mode
        if self.config.mode == ServiceMode.AUTO:
            if self.modern_available:
                self.active_mode = ServiceMode.MODERN
            elif self.legacy_available:
                self.active_mode = ServiceMode.LEGACY
            else:
                self.active_mode = ServiceMode.HYBRID
        else:
            self.active_mode = self.config.mode
        
        self.logger.info(f"Integrated service initialized in {self.active_mode.value} mode")
    
    async def generate_definition(
        self,
        begrip: str,
        context: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> IntegratedResult:
        """
        Generate definition using best available service.
        
        Args:
            begrip: Term to define
            context: Context information
            options: Generation options
            
        Returns:
            IntegratedResult with generation results
        """
        start_time = datetime.now()
        operation = "generate_definition"
        
        try:
            # Record operation start
            if MONITORING_AVAILABLE and self.config.enable_monitoring:
                await record_api_call(
                    endpoint="integrated_service",
                    function_name=operation,
                    duration=0.0,
                    success=True,
                    tokens_used=0
                )
            
            # Choose generation strategy
            if self.active_mode == ServiceMode.MODERN and self.modern_available:
                result = await self._generate_modern(begrip, context, options)
            elif self.active_mode == ServiceMode.LEGACY and self.legacy_available:
                result = await self._generate_legacy(begrip, context, options)
            else:
                result = await self._generate_hybrid(begrip, context, options)
            
            # Add web lookup if enabled
            if self.config.enable_web_lookup and WEB_LOOKUP_AVAILABLE:
                await self._add_web_lookup_data(result, begrip, context)
            
            # Performance tracking
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            result.operation = operation
            result.service_mode = self.active_mode
            
            # Update stats
            self._update_operation_stats(operation, processing_time, result.success)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Definition generation failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return IntegratedResult(
                success=False,
                operation=operation,
                processing_time=processing_time,
                service_mode=self.active_mode,
                error_message=str(e)
            )
    
    async def _generate_modern(
        self, 
        begrip: str, 
        context: Dict[str, Any], 
        options: Optional[Dict[str, Any]]
    ) -> IntegratedResult:
        """Generate using modern architecture."""
        try:
            # Convert context to GenerationContext
            generation_context = self._convert_to_generation_context(begrip, context)
            
            # Use modern generator
            generation_result = self.modern_generator.generate(generation_context)
            
            # Apply opschoning if available
            definitie_origineel = generation_result.definitie
            definitie_gecorrigeerd = definitie_origineel
            if OPSCHONING_AVAILABLE:
                definitie_gecorrigeerd = opschonen(definitie_origineel, begrip)
            
            # Validate result
            validation_result = None
            if self.config.enable_validation:
                validation_result = self.modern_validator.validate(
                    generation_result.definitie,
                    generation_context.categorie
                )
            
            # Create database record
            definitie_record = DefinitieRecord(
                begrip=begrip,
                definitie=definitie_gecorrigeerd,
                categorie=generation_context.categorie.value,
                organisatorische_context=generation_context.organisatorische_context,
                juridische_context=generation_context.juridische_context,
                status=DefinitieStatus.DRAFT.value,
                validation_score=validation_result.overall_score if validation_result else None,
                metadata={
                    "generation_method": "modern",
                    "used_instructions": [instr.rule_id for instr in generation_result.gebruikte_instructies],
                    "confidence_score": generation_result.confidence_score
                }
            )
            
            return IntegratedResult(
                success=True,
                operation="generate_modern",
                processing_time=0.0,  # Will be set by caller
                service_mode=ServiceMode.MODERN,
                definitie_record=definitie_record,
                validation_result=validation_result,
                definitie_origineel=definitie_origineel,
                definitie_gecorrigeerd=definitie_gecorrigeerd,
                metadata={
                    "generation_strategy": "modern_ai",
                    "used_rules": [instr.rule_id for instr in generation_result.gebruikte_instructies],
                    "opschoning_applied": OPSCHONING_AVAILABLE,
                    "opschoning_changed": definitie_origineel != definitie_gecorrigeerd if OPSCHONING_AVAILABLE else False
                }
            )
            
        except Exception as e:
            raise Exception(f"Modern generation failed: {e}")
    
    async def _generate_legacy(
        self, 
        begrip: str, 
        context: Dict[str, Any], 
        options: Optional[Dict[str, Any]]
    ) -> IntegratedResult:
        """Generate using legacy architecture."""
        try:
            # Convert context for legacy service
            context_dict = self._convert_to_legacy_context(context)
            
            # Use async service if parallel processing enabled
            if self.config.parallel_processing:
                async_result = await self.async_service.async_generate_definition(
                    begrip, context_dict
                )
                
                # Apply opschoning to legacy result
                definitie_gecorrigeerd = async_result.definitie_gecorrigeerd
                if OPSCHONING_AVAILABLE and definitie_gecorrigeerd:
                    definitie_gecorrigeerd = opschonen(definitie_gecorrigeerd, begrip)
                
                return IntegratedResult(
                    success=async_result.success,
                    operation="generate_legacy_async",
                    processing_time=async_result.processing_time,
                    service_mode=ServiceMode.LEGACY,
                    definitie_origineel=async_result.definitie_origineel,
                    definitie_gecorrigeerd=definitie_gecorrigeerd,
                    marker=async_result.marker,
                    toetsresultaten=async_result.toetsresultaten or [],
                    examples=async_result.additional_content or {},
                    cache_hits=async_result.cache_hits,
                    total_requests=async_result.total_requests,
                    error_message=async_result.error_message
                )
            else:
                # Use synchronous legacy service
                definitie_orig, definitie_clean, marker = self.legacy_service.generate_definition(
                    begrip, context_dict
                )
                
                # Apply opschoning to sync legacy result
                if OPSCHONING_AVAILABLE and definitie_clean:
                    definitie_clean = opschonen(definitie_clean, begrip)
                
                return IntegratedResult(
                    success=True,
                    operation="generate_legacy_sync",
                    processing_time=0.0,
                    service_mode=ServiceMode.LEGACY,
                    definitie_origineel=definitie_orig,
                    definitie_gecorrigeerd=definitie_clean,
                    marker=marker
                )
                
        except Exception as e:
            raise Exception(f"Legacy generation failed: {e}")
    
    async def _generate_hybrid(
        self, 
        begrip: str, 
        context: Dict[str, Any], 
        options: Optional[Dict[str, Any]]
    ) -> IntegratedResult:
        """Generate using hybrid approach."""
        try:
            # Try modern first, fallback to legacy
            if self.modern_available:
                try:
                    return await self._generate_modern(begrip, context, options)
                except Exception as e:
                    self.logger.warning(f"Modern generation failed, falling back to legacy: {e}")
            
            if self.legacy_available:
                return await self._generate_legacy(begrip, context, options)
            
            raise Exception("No generation services available")
            
        except Exception as e:
            raise Exception(f"Hybrid generation failed: {e}")
    
    async def validate_definition(
        self,
        definitie: str,
        categorie: str,
        context: Optional[Dict[str, Any]] = None
    ) -> IntegratedResult:
        """
        Validate definition using best available validator.
        
        Args:
            definitie: Definition to validate
            categorie: Ontological category
            context: Optional context
            
        Returns:
            IntegratedResult with validation results
        """
        start_time = datetime.now()
        operation = "validate_definition"
        
        try:
            # Use modern validator if available
            if self.modern_available:
                validation_result = validate_definitie(definitie, categorie, context)
                
                return IntegratedResult(
                    success=True,
                    operation=operation,
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    service_mode=self.active_mode,
                    validation_result=validation_result,
                    definitie_gecorrigeerd=definitie,
                    toetsresultaten=[v.description for v in validation_result.violations],
                    metadata={
                        "overall_score": validation_result.overall_score,
                        "is_acceptable": validation_result.is_acceptable,
                        "violations_count": len(validation_result.violations)
                    }
                )
            else:
                # Fallback to legacy validation
                from ai_toetser import toets_definitie
                legacy_context = self._convert_to_legacy_context(context or {})
                toetsresultaten = toets_definitie(definitie, legacy_context)
                
                return IntegratedResult(
                    success=True,
                    operation=operation,
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    service_mode=ServiceMode.LEGACY,
                    definitie_gecorrigeerd=definitie,
                    toetsresultaten=toetsresultaten,
                    metadata={"legacy_validation": True}
                )
                
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return IntegratedResult(
                success=False,
                operation=operation,
                processing_time=(datetime.now() - start_time).total_seconds(),
                service_mode=self.active_mode,
                error_message=str(e)
            )
    
    async def check_duplicates(
        self,
        begrip: str,
        definitie: str,
        threshold: float = 0.8
    ) -> IntegratedResult:
        """
        Check for duplicate definitions.
        
        Args:
            begrip: Term to check
            definitie: Definition to check
            threshold: Similarity threshold
            
        Returns:
            IntegratedResult with duplicate analysis
        """
        start_time = datetime.now()
        operation = "check_duplicates"
        
        try:
            duplicate_analysis = {}
            
            # Use web lookup if available
            if WEB_LOOKUP_AVAILABLE and self.config.enable_web_lookup:
                duplicate_analysis = await detecteer_duplicaten(begrip, definitie, threshold)
            else:
                # Fallback to repository search
                existing = self.repository.search_definities(query=begrip, limit=10)
                duplicate_analysis = {
                    "duplicaat_gevonden": len(existing) > 0,
                    "mogelijke_duplicaten": [
                        {
                            "begrip": def_rec.begrip,
                            "definitie": def_rec.definitie,
                            "bron": f"Internal DB (ID: {def_rec.id})",
                            "gelijkenis": 0.5  # Placeholder
                        }
                        for def_rec in existing
                    ]
                }
            
            return IntegratedResult(
                success=True,
                operation=operation,
                processing_time=(datetime.now() - start_time).total_seconds(),
                service_mode=self.active_mode,
                duplicate_analysis=duplicate_analysis,
                metadata={
                    "threshold": threshold,
                    "found_duplicates": duplicate_analysis.get("duplicaat_gevonden", False)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Duplicate check failed: {e}")
            return IntegratedResult(
                success=False,
                operation=operation,
                processing_time=(datetime.now() - start_time).total_seconds(),
                service_mode=self.active_mode,
                error_message=str(e)
            )
    
    async def lookup_sources(
        self,
        begrip: str,
        context: Optional[Dict[str, Any]] = None
    ) -> IntegratedResult:
        """
        Look up sources for a term.
        
        Args:
            begrip: Term to look up sources for
            context: Optional context
            
        Returns:
            IntegratedResult with source information
        """
        start_time = datetime.now()
        operation = "lookup_sources"
        
        try:
            bronnen = []
            web_lookup_results = {}
            
            if WEB_LOOKUP_AVAILABLE and self.config.enable_web_lookup:
                bron_resultaat = await zoek_bronnen_voor_begrip(begrip, context, max_resultaten=10)
                bronnen = bron_resultaat.gevonden_bronnen
                web_lookup_results["bron_lookup"] = {
                    "query": bron_resultaat.query,
                    "zoek_tijd": bron_resultaat.zoek_tijd,
                    "totaal_gevonden": bron_resultaat.totaal_gevonden,
                    "aanbevelingen": bron_resultaat.aanbevelingen
                }
            
            return IntegratedResult(
                success=True,
                operation=operation,
                processing_time=(datetime.now() - start_time).total_seconds(),
                service_mode=self.active_mode,
                bronnen=bronnen,
                web_lookup_results=web_lookup_results,
                metadata={
                    "sources_found": len(bronnen),
                    "web_lookup_enabled": WEB_LOOKUP_AVAILABLE and self.config.enable_web_lookup
                }
            )
            
        except Exception as e:
            self.logger.error(f"Source lookup failed: {e}")
            return IntegratedResult(
                success=False,
                operation=operation,
                processing_time=(datetime.now() - start_time).total_seconds(),
                service_mode=self.active_mode,
                error_message=str(e)
            )
    
    async def _add_web_lookup_data(
        self, 
        result: IntegratedResult, 
        begrip: str, 
        context: Dict[str, Any]
    ):
        """Add web lookup data to result."""
        try:
            # Look up related definitions
            definitie_lookup = await zoek_definitie(begrip, context, max_resultaten=5)
            result.web_lookup_results["definitie_lookup"] = {
                "gevonden": len(definitie_lookup.gevonden_definities),
                "exacte_matches": len(definitie_lookup.exacte_matches),
                "gerelateerde": definitie_lookup.gerelateerde_begrippen[:5]
            }
            
            # Look up sources
            source_lookup = await self.lookup_sources(begrip, context)
            if source_lookup.success:
                result.web_lookup_results.update(source_lookup.web_lookup_results)
                result.bronnen.extend(source_lookup.bronnen)
            
        except Exception as e:
            self.logger.warning(f"Web lookup enhancement failed: {e}")
            result.warnings.append(f"Web lookup failed: {str(e)}")
    
    def _convert_to_generation_context(
        self, 
        begrip: str, 
        context: Dict[str, Any]
    ) -> GenerationContext:
        """Convert context dict to GenerationContext."""
        # Extract context information
        org_context = context.get("organisatorische_context", [])
        jur_context = context.get("juridische_context", [])
        
        # Determine category
        categorie_str = context.get("categorie", "type")
        categorie_map = {
            "type": OntologischeCategorie.TYPE,
            "proces": OntologischeCategorie.PROCES,
            "resultaat": OntologischeCategorie.RESULTAAT,
            "exemplaar": OntologischeCategorie.EXEMPLAAR
        }
        categorie = categorie_map.get(categorie_str.lower(), OntologischeCategorie.TYPE)
        
        return GenerationContext(
            begrip=begrip,
            organisatorische_context=org_context[0] if org_context else "",
            juridische_context=jur_context[0] if jur_context else "",
            categorie=categorie
        )
    
    def _convert_to_legacy_context(self, context: Dict[str, Any]) -> Dict[str, List[str]]:
        """Convert context dict to legacy format."""
        return {
            "organisatorische_context": context.get("organisatorische_context", []),
            "juridische_context": context.get("juridische_context", []),
            "wettelijke_basis": context.get("wettelijke_basis", [])
        }
    
    def _update_operation_stats(self, operation: str, duration: float, success: bool):
        """Update operation statistics."""
        if operation not in self.operation_stats:
            self.operation_stats[operation] = {
                "total_calls": 0,
                "successful_calls": 0,
                "total_duration": 0.0,
                "avg_duration": 0.0
            }
        
        stats = self.operation_stats[operation]
        stats["total_calls"] += 1
        if success:
            stats["successful_calls"] += 1
        stats["total_duration"] += duration
        stats["avg_duration"] = stats["total_duration"] / stats["total_calls"]
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information and statistics."""
        return {
            "active_mode": self.active_mode.value,
            "config": {
                "enable_caching": self.config.enable_caching,
                "enable_monitoring": self.config.enable_monitoring,
                "enable_web_lookup": self.config.enable_web_lookup,
                "enable_validation": self.config.enable_validation,
                "parallel_processing": self.config.parallel_processing
            },
            "availability": {
                "modern_services": self.modern_available,
                "legacy_services": self.legacy_available,
                "web_lookup": WEB_LOOKUP_AVAILABLE,
                "monitoring": MONITORING_AVAILABLE
            },
            "operation_stats": self.operation_stats
        }


# Global service instance
_integrated_service: Optional[IntegratedDefinitionService] = None


def get_integrated_service(config: Optional[ServiceConfig] = None) -> IntegratedDefinitionService:
    """Get or create global integrated service instance."""
    global _integrated_service
    if _integrated_service is None:
        _integrated_service = IntegratedDefinitionService(config)
    return _integrated_service


# Convenience functions
async def integrated_generate_definition(
    begrip: str,
    context: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None
) -> IntegratedResult:
    """Convenience function for definition generation."""
    service = get_integrated_service()
    return await service.generate_definition(begrip, context, options)


async def integrated_validate_definition(
    definitie: str,
    categorie: str,
    context: Optional[Dict[str, Any]] = None
) -> IntegratedResult:
    """Convenience function for definition validation."""
    service = get_integrated_service()
    return await service.validate_definition(definitie, categorie, context)


async def integrated_check_duplicates(
    begrip: str,
    definitie: str,
    threshold: float = 0.8
) -> IntegratedResult:
    """Convenience function for duplicate checking."""
    service = get_integrated_service()
    return await service.check_duplicates(begrip, definitie, threshold)


if __name__ == "__main__":
    # Test integrated service
    import asyncio
    
    async def test_integrated_service():
        print("🔧 Testing Integrated Service")
        print("=" * 30)
        
        # Initialize service
        config = ServiceConfig(
            mode=ServiceMode.AUTO,
            enable_web_lookup=True,
            enable_monitoring=True
        )
        
        service = IntegratedDefinitionService(config)
        
        # Test generation
        context = {
            "organisatorische_context": ["DJI"],
            "juridische_context": ["Strafrecht"],
            "categorie": "proces"
        }
        
        result = await service.generate_definition("authenticatie", context)
        
        print(f"📊 Generation result:")
        print(f"   Success: {result.success}")
        print(f"   Mode: {result.service_mode.value}")
        print(f"   Time: {result.processing_time:.3f}s")
        if result.definitie_gecorrigeerd:
            print(f"   Definitie: {result.definitie_gecorrigeerd[:100]}...")
        
        # Test validation
        if result.success and result.definitie_gecorrigeerd:
            val_result = await service.validate_definition(
                result.definitie_gecorrigeerd, "proces"
            )
            print(f"✅ Validation: {val_result.success}")
            if val_result.validation_result:
                print(f"   Score: {val_result.validation_result.overall_score:.2f}")
        
        # Service info
        info = service.get_service_info()
        print(f"🔧 Service info:")
        print(f"   Mode: {info['active_mode']}")
        print(f"   Modern available: {info['availability']['modern_services']}")
        print(f"   Legacy available: {info['availability']['legacy_services']}")
        print(f"   Web lookup: {info['availability']['web_lookup']}")
    
    # Run test
    asyncio.run(test_integrated_service())