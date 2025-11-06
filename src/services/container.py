"""
Dependency Injection Container voor de services.

Deze container beheert de instanties van alle services en hun dependencies.
Dit maakt het makkelijk om services te configureren, testen en swappen.
"""

import logging
import os
from typing import TYPE_CHECKING, Any

from config.config_manager import (
    get_component_config,
    get_default_model,
    get_default_temperature,
)
from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_repository import DefinitionRepository

# Legacy DefinitionValidator removed - using V2 orchestrator for validation
from services.duplicate_detection_service import DuplicateDetectionService
from services.interfaces import (
    CleaningServiceInterface,
    DefinitionGeneratorInterface,
    DefinitionOrchestratorInterface,
    DefinitionRepositoryInterface,
    WebLookupServiceInterface,
)
from services.modern_web_lookup_service import ModernWebLookupService

# V2 Architecture imports
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2

# UnifiedDefinitionGenerator vervangen door DefinitionOrchestrator
# from services.unified_definition_generator import UnifiedDefinitionGenerator
from services.workflow_service import WorkflowService

if TYPE_CHECKING:
    from repositories.synonym_registry import SynonymRegistry
    from services.data_aggregation_service import DataAggregationService
    from services.export_service import ExportService
    from services.gpt4_synonym_suggester import GPT4SynonymSuggester
    from services.synonym_orchestrator import SynonymOrchestrator
    from services.web_lookup.synonym_service_refactored import JuridischeSynoniemService

logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Simpele Dependency Injection container voor service management.

    Deze container:
    - Beheert singleton instances van services
    - Configureert dependencies
    - Biedt een centrale plek voor service configuratie
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialiseer de container met optionele configuratie.

        Args:
            config: Dictionary met configuratie opties
        """
        self.config = config or {}
        self._instances = {}
        self._lazy_instances = {}  # Cache for lazy-loaded services
        self._initialization_count = 0  # Track init count voor debugging
        self._load_configuration()
        self._initialization_count += 1

        # US-202: Add unique container ID for tracking multiple instances
        import uuid

        self._container_id = str(uuid.uuid4())[:8]

        # Use structured logging with extra fields (backward compatible)
        logger.info(
            "ServiceContainer instance initialized (lazy service loading will occur on first access)",
            extra={
                "component": "service_container",
                "container_id": self._container_id,
                "init_count": self._initialization_count,
                "environment": self.config.get("environment", "unknown"),
                "db_path": self.db_path,
            },
        )

    def _load_configuration(self):
        """Laad configuratie uit environment en config dict."""
        # Basis configuratie
        self.db_path = self.config.get("db_path", "data/definities.db")
        self.openai_api_key = self.config.get(
            "openai_api_key",
            (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_PROD")),
        )

        # Service specifieke configuratie - Use default and override via sub-configs
        from services.definition_generator_config import (
            GPTConfig,
            MonitoringConfig,
            QualityConfig,
        )

        # Gebruik centrale configuratie voor definition generator
        definition_config = get_component_config("definition_generator")

        gpt_config = GPTConfig(
            model=self.config.get(
                "generator_model", definition_config.get("model", get_default_model())
            ),
            temperature=self.config.get(
                "generator_temperature",
                definition_config.get("temperature", get_default_temperature()),
            ),
            api_key=self.openai_api_key,  # Pass the API key
        )

        quality_config = QualityConfig(
            enable_cleaning=self.config.get("enable_cleaning", True),
            enable_ontology=self.config.get("enable_ontology", True),
        )

        monitoring_config = MonitoringConfig(
            enable_monitoring=self.config.get("enable_monitoring", False)
        )

        self.generator_config = UnifiedGeneratorConfig(
            gpt=gpt_config, quality=quality_config, monitoring=monitoring_config
        )

        # Legacy validator config removed - V2 orchestrator handles validation
        # Feature toggles
        self.use_json_rules = bool(self.config.get("use_json_rules", True))

        # Cleaning service configuratie
        from services.cleaning_service import CleaningConfig

        self.cleaning_config = CleaningConfig(
            enable_cleaning=self.config.get("enable_cleaning", True),
            track_changes=self.config.get("cleaning_track_changes", True),
            preserve_original=self.config.get("cleaning_preserve_original", True),
            log_operations=self.config.get("cleaning_log_operations", True),
        )

    # Service factory methods

    def generator(self) -> DefinitionGeneratorInterface:
        """
        Get of create DefinitionGenerator instance.

        V2 orchestrator is nu de enige implementatie.

        Returns:
            Singleton instance van DefinitionGeneratorInterface (via V2 Orchestrator)
        """
        if "generator" not in self._instances:
            # V2 orchestrator is de enige generator implementatie
            orchestrator_instance = self.orchestrator()
            self._instances["generator"] = orchestrator_instance
            logger.debug("DefinitionOrchestratorV2 instance aangemaakt als generator")
        return self._instances["generator"]

    # Legacy validator() method removed - validation now handled by V2 orchestrator
    @property
    def validator(self):  # pragma: no cover - compatibility shim for tests' specs
        """Legacy attribute intentionally unavailable.

        Exposed as a property raising AttributeError so:
        - hasattr(instance, 'validator') returns False (as expected by tests)
        - Mock(spec=ServiceContainer) may still reference 'validator' in its spec
        """
        msg = "validator attribute removed; use V2 orchestrator"
        raise AttributeError(msg)

    def repository(self) -> DefinitionRepositoryInterface:
        """
        Get of create DefinitionRepository instance.

        Returns:
            Singleton instance van DefinitionRepository
        """
        if "repository" not in self._instances:
            # Check if database should be used
            use_database = self.config.get("use_database", True)

            if use_database:
                repository = DefinitionRepository(self.db_path)

                # NOTE: Duplicate service is NOT injected here during init to keep repository eager-loaded
                # It will be injected lazily when edit functionality is accessed via UI
                # See duplicate_detector() for lazy loading implementation

                self._instances["repository"] = repository
                logger.debug(
                    f"DefinitionRepository instance aangemaakt met db: {self.db_path}"
                )
            else:
                from services.null_repository import NullDefinitionRepository

                self._instances["repository"] = NullDefinitionRepository()
                logger.debug(
                    "NullDefinitionRepository instance aangemaakt (no database)"
                )

        return self._instances["repository"]

    def orchestrator(self) -> DefinitionOrchestratorInterface:
        """
        Get of create DefinitionOrchestrator instance.

        Returns:
            Singleton instance van DefinitionOrchestratorV2
        """
        if "orchestrator" not in self._instances:
            # V2 is now the only orchestrator
            from services.adapters.cleaning_service_adapter import (
                CleaningServiceAdapterV1toV2,
            )
            from services.ai_service_v2 import AIServiceV2
            from services.interfaces import OrchestratorConfig as V2OrchestratorConfig

            # DEF-66: PromptServiceV2 import removed - lazy loaded by orchestrator
            # DEF-90: ValidationOrchestratorV2 creation removed - lazy loaded by orchestrator
            # Create config with use_json_rules for lazy validation loading
            v2_config = V2OrchestratorConfig(
                use_json_rules=self.use_json_rules  # DEF-90: Pass for lazy validation
            )

            # DEF-66: PromptServiceV2 is now lazy-loaded by orchestrator (saves 435ms on init)
            # prompt_service = PromptServiceV2()  # REMOVED - lazy loaded

            # DEF-90: ValidationOrchestratorV2 is now lazy-loaded by orchestrator (saves 345ms on init)
            # modular_validation_service = ...  # REMOVED - lazy loaded
            # validation_orchestrator = ...  # REMOVED - lazy loaded

            # Create AI service (still eager - needed for orchestrator init check)
            ai_service = AIServiceV2(
                default_model=self.generator_config.gpt.model, use_cache=True
            )

            # Get cleaning service (needed for orchestrator init)
            cleaning_service = CleaningServiceAdapterV1toV2(self.cleaning_service())

            # Architecture v3.1: Get synonym orchestrator for enrichment
            try:
                synonym_orch = self.synonym_orchestrator()
            except Exception:
                # If synonym orchestrator fails, log warning and continue without
                logger.warning(
                    "Synonym orchestrator initialization failed - "
                    "definition generation will proceed without synonym enrichment"
                )
                synonym_orch = None

            self._instances["orchestrator"] = DefinitionOrchestratorV2(
                # DEF-66: prompt_service=None triggers lazy loading (saves 435ms)
                prompt_service=None,  # Will be lazy-loaded on first access
                ai_service=ai_service,
                # DEF-90: validation_service=None triggers lazy loading (saves 345ms, 56%!)
                validation_service=None,  # Will be lazy-loaded on first access
                cleaning_service=cleaning_service,
                repository=self.repository(),
                # Optional services
                enhancement_service=None,  # Not implemented yet
                security_service=None,  # Not implemented yet
                monitoring=None,  # Not implemented yet
                feedback_engine=None,  # Not implemented yet
                # Configuration
                config=v2_config,
                # Epic 3: inject ModernWebLookupService so enrichment and provenance work
                web_lookup_service=self.web_lookup(),
                # Architecture v3.1: inject SynonymOrchestrator for synonym enrichment
                synonym_orchestrator=synonym_orch,
            )
            logger.debug("DefinitionOrchestratorV2 instance created")

        return self._instances["orchestrator"]

    def validation_orchestrator(self):
        """
        Get ValidationOrchestratorV2 instance (DEF-90: lazy-loaded via orchestrator).

        Returns:
            ValidationOrchestratorV2 instance (lazy-loaded from orchestrator property)
        """
        # DEF-90: Validation is now lazy-loaded via orchestrator property
        # Access orchestrator.validation_service to trigger lazy load if needed
        orchestrator = self.orchestrator()
        return orchestrator.validation_service

    def ontological_classifier(self):
        """
        Get of create OntologicalClassifier instance (U/F/O classifier).

        Dit is de classifier die VOOR definitie generatie wordt gebruikt om
        begrippen te classificeren als Universals, Functionals, of Objects.

        Returns:
            Singleton instance van OntologicalClassifier

        Usage:
            # In UI
            classifier = container.ontological_classifier()
            result = classifier.classify(begrip, org_ctx, jur_ctx)
            request.ontologische_categorie = result.to_string_level()

            # Batch processing
            results = classifier.classify_batch(begrippen_list)
        """
        if "ontological_classifier" not in self._instances:
            from services.ai_service_v2 import AIServiceV2
            from services.classification.ontological_classifier import (
                OntologicalClassifier,
            )

            # Reuse AI service with same config as generator
            ai_service = AIServiceV2(
                default_model=self.generator_config.gpt.model, use_cache=True
            )

            self._instances["ontological_classifier"] = OntologicalClassifier(
                ai_service
            )
            logger.info("OntologicalClassifier (standalone) initialized")

        return self._instances["ontological_classifier"]

    def term_based_classifier(self):
        """
        Get of create ImprovedOntologyClassifier instance (term-based classifier).

        DEF-35: Term-based classifier met YAML configuratie voor pattern matching.
        Dit is een snellere, config-driven alternatief voor AI-based classificatie.

        Returns:
            Singleton instance van ImprovedOntologyClassifier

        Usage:
            # In UI of service
            classifier = container.term_based_classifier()
            result = classifier.classify(begrip, org_ctx, jur_ctx, wet_ctx)

            # Result bevat:
            # - result.categorie: OntologischeCategorie enum
            # - result.confidence: 0.0-1.0 score
            # - result.confidence_label: "HIGH"/"MEDIUM"/"LOW"
            # - result.all_scores: Dict met alle category scores
            # - result.reasoning: Menselijke uitleg
        """
        if "term_based_classifier" not in self._instances:
            from ontologie.improved_classifier import ImprovedOntologyClassifier

            # Initialize met default config (loaded from YAML, cached)
            self._instances["term_based_classifier"] = ImprovedOntologyClassifier()
            logger.info(
                "ImprovedOntologyClassifier (term-based) initialized with YAML config"
            )

        return self._instances["term_based_classifier"]

    def web_lookup(self) -> WebLookupServiceInterface:
        """
        Get of create ModernWebLookupService instance.

        Returns:
            Singleton instance van ModernWebLookupService
        """
        if "web_lookup" not in self._instances:
            try:
                self._instances["web_lookup"] = ModernWebLookupService()
                logger.info(
                    "✅ ModernWebLookupService initialized successfully - external context enrichment AVAILABLE"
                )
            except Exception as e:
                logger.error(
                    f"⚠️ ModernWebLookupService initialization FAILED: {type(e).__name__}: {e}\n"
                    f"Definitions will be generated WITHOUT external context enrichment!"
                )
                self._instances["web_lookup"] = None
        return self._instances["web_lookup"]

    def synonym_registry(self) -> "SynonymRegistry":
        """
        Get or create SynonymRegistry instance.

        Returns:
            Singleton instance van SynonymRegistry
        """
        if "synonym_registry" not in self._instances:
            from repositories.synonym_registry import SynonymRegistry

            self._instances["synonym_registry"] = SynonymRegistry(self.db_path)
            logger.info(f"SynonymRegistry initialized with db: {self.db_path}")

        return self._instances["synonym_registry"]

    def gpt4_synonym_suggester(self) -> "GPT4SynonymSuggester":
        """
        Get or create GPT4SynonymSuggester instance.

        Returns:
            Singleton instance van GPT4SynonymSuggester (placeholder mode)
        """
        if "gpt4_synonym_suggester" not in self._instances:
            from services.gpt4_synonym_suggester import GPT4SynonymSuggester

            try:
                # Initialize suggester (placeholder implementation)
                # API key validation will be added when GPT-4 integration is implemented
                self._instances["gpt4_synonym_suggester"] = GPT4SynonymSuggester()
                logger.info(
                    "GPT4SynonymSuggester initialized (placeholder mode - no actual API calls)"
                )
            except Exception as e:
                logger.warning(
                    f"GPT4SynonymSuggester initialization warning: {e}. "
                    "Synonym enrichment will not be available."
                )
                # Don't fail hard - allow app to start without enrichment
                self._instances["gpt4_synonym_suggester"] = None

        return self._instances["gpt4_synonym_suggester"]

    def synonym_orchestrator(self) -> "SynonymOrchestrator":
        """
        Get or create SynonymOrchestrator instance.

        Wires registry + GPT-4 suggester + cache invalidation callbacks.

        Returns:
            Singleton instance van SynonymOrchestrator
        """
        if "synonym_orchestrator" not in self._instances:
            from services.synonym_orchestrator import SynonymOrchestrator

            # Get dependencies
            registry = self.synonym_registry()
            gpt4_suggester = self.gpt4_synonym_suggester()

            # Handle case where suggester failed to initialize
            if gpt4_suggester is None:
                logger.warning(
                    "GPT4SynonymSuggester not available - "
                    "creating dummy suggester for orchestrator"
                )
                # Create a dummy suggester that always returns empty results
                from services.gpt4_synonym_suggester import GPT4SynonymSuggester

                gpt4_suggester = GPT4SynonymSuggester()

            # Create orchestrator
            orchestrator = SynonymOrchestrator(
                registry=registry, gpt4_suggester=gpt4_suggester
            )

            # Wire cache invalidation callbacks
            # When registry data changes, orchestrator cache must be invalidated
            registry.register_invalidation_callback(orchestrator.invalidate_cache)

            self._instances["synonym_orchestrator"] = orchestrator
            logger.info(
                "SynonymOrchestrator initialized with TTL cache and invalidation callbacks wired"
            )

        return self._instances["synonym_orchestrator"]

    def synonym_service(self) -> "JuridischeSynoniemService":
        """
        Get or create JuridischeSynoniemService instance (façade).

        Provides backward compatible API over SynonymOrchestrator.

        Returns:
            Singleton instance van JuridischeSynoniemService
        """
        if "synonym_service" not in self._instances:
            from services.web_lookup.synonym_service_refactored import (
                JuridischeSynoniemService,
            )

            # Get orchestrator dependency
            orchestrator = self.synonym_orchestrator()

            self._instances["synonym_service"] = JuridischeSynoniemService(orchestrator)
            logger.info("JuridischeSynoniemService initialized as orchestrator façade")

        return self._instances["synonym_service"]

    def duplicate_detector(self) -> DuplicateDetectionService:
        """
        Get of create DuplicateDetectionService instance (LAZY-LOADED).

        Only loaded when edit functionality is accessed.
        Automatically injects into repository on first access.

        Returns:
            Singleton instance van DuplicateDetectionService
        """
        if "duplicate_detector" not in self._lazy_instances:
            similarity_threshold = self.config.get(
                "duplicate_similarity_threshold", 0.7
            )
            self._lazy_instances["duplicate_detector"] = DuplicateDetectionService(
                similarity_threshold=similarity_threshold
            )
            logger.info(
                f"⚡ DuplicateDetectionService lazy-loaded (threshold={similarity_threshold})"
            )

            # Inject into repository if enabled
            if self.config.get("use_new_duplicate_detection", True):
                repo = self.repository()
                repo.set_duplicate_service(self._lazy_instances["duplicate_detector"])
                logger.info("⚡ DuplicateDetectionService injected into repository")

        return self._lazy_instances["duplicate_detector"]

    # ===== Approval Gate Policy (US-160) =====
    def gate_policy(self):
        """
        Get or create GatePolicyService instance (LAZY-LOADED).

        Only loaded when validation gates or workflow transitions are accessed.
        Loads approval gate policy (YAML) with lazy TTL caching.

        Returns:
            Singleton instance van GatePolicyService
        """
        if "gate_policy" not in self._lazy_instances:
            from services.policies.approval_gate_policy import GatePolicyService

            base_path = self.config.get(
                "approval_gate_config_path", "config/approval_gate.yaml"
            )
            self._lazy_instances["gate_policy"] = GatePolicyService(base_path)
            logger.info("⚡ GatePolicyService lazy-loaded (config: %s)", base_path)
        return self._lazy_instances["gate_policy"]

    def workflow(self) -> WorkflowService:
        """
        Get of create WorkflowService instance.

        Returns:
            Singleton instance van WorkflowService
        """
        if "workflow" not in self._instances:
            self._instances["workflow"] = WorkflowService()
            logger.debug("WorkflowService instance aangemaakt")
        return self._instances["workflow"]

    def definition_workflow_service(self):
        """
        Get of create DefinitionWorkflowService instance (LAZY-LOADED).

        US-072: Deze service combineert workflow en repository acties
        zodat UI geen losse services hoeft te coördineren.

        Only loaded when Expert Review tab or workflow actions are accessed.

        Returns:
            Singleton instance van DefinitionWorkflowService
        """
        if "definition_workflow_service" not in self._lazy_instances:
            from services.definition_workflow_service import DefinitionWorkflowService

            # Use existing services
            workflow_service = self.workflow()
            repository = self.repository()

            # Optional services (None for now, can be added later)
            event_bus = None  # Pending: integrate Event Bus when US-060 is delivered
            audit_logger = (
                None  # Pending: integrate Audit Trail when US-068 is delivered
            )
            gate_policy_service = self.gate_policy()  # Lazy - will trigger lazy load

            self._lazy_instances["definition_workflow_service"] = (
                DefinitionWorkflowService(
                    workflow_service=workflow_service,
                    repository=repository,
                    event_bus=event_bus,
                    audit_logger=audit_logger,
                    gate_policy_service=gate_policy_service,
                )
            )
            logger.info("⚡ DefinitionWorkflowService lazy-loaded (US-072)")
        return self._lazy_instances["definition_workflow_service"]

    def cleaning_service(self) -> CleaningServiceInterface:
        """
        Get of create CleaningService instance.

        Returns:
            Singleton instance van CleaningService
        """
        if "cleaning_service" not in self._instances:
            from services.cleaning_service import CleaningService

            self._instances["cleaning_service"] = CleaningService(self.cleaning_config)
            logger.debug("CleaningService instance aangemaakt")
        return self._instances["cleaning_service"]

    def data_aggregation_service(self) -> "DataAggregationService":
        """
        Get of create DataAggregationService instance (LAZY-LOADED).

        Only loaded when export actions are triggered.

        Returns:
            Singleton instance van DataAggregationService
        """
        if "data_aggregation_service" not in self._lazy_instances:
            from services.data_aggregation_service import DataAggregationService

            # Use existing repository instance
            repo = self.repository()
            self._lazy_instances["data_aggregation_service"] = DataAggregationService(
                repo
            )
            logger.info("⚡ DataAggregationService lazy-loaded")
        return self._lazy_instances["data_aggregation_service"]

    def export_service(self) -> "ExportService":
        """
        Get of create ExportService instance (LAZY-LOADED).

        Only loaded when export actions are triggered.
        Lazy-loads data_aggregation_service as dependency.

        Returns:
            Singleton instance van ExportService
        """
        if "export_service" not in self._lazy_instances:
            from services.export_service import ExportService

            # Use existing services
            repo = self.repository()
            data_agg_service = (
                self.data_aggregation_service()
            )  # Lazy - will trigger lazy load

            # Get export directory from config
            export_dir = self.config.get("export_dir", "exports")

            self._lazy_instances["export_service"] = ExportService(
                repository=repo,
                data_aggregation_service=data_agg_service,
                export_dir=export_dir,
                validation_orchestrator=self.orchestrator(),
                enable_validation_gate=self.config.get(
                    "enable_export_validation_gate", False
                ),
            )
            logger.info("⚡ ExportService lazy-loaded")
        return self._lazy_instances["export_service"]

    def import_service(self):
        """
        Get or create DefinitionImportService instance (CSV batch helper) (LAZY-LOADED).

        Only loaded when import actions are triggered.

        Returns:
            Singleton instance van DefinitionImportService
        """
        if "import_service" not in self._lazy_instances:
            from services.definition_import_service import DefinitionImportService

            repo = self.repository()
            validator = self.validation_orchestrator()
            self._lazy_instances["import_service"] = DefinitionImportService(
                repository=repo, validation_orchestrator=validator
            )
            logger.info("⚡ DefinitionImportService lazy-loaded (CSV helper)")
        return self._lazy_instances["import_service"]

    # UI-services worden niet in de servicescontainer opgebouwd. Gebruik UI-container.

    # Utility methods

    def reset(self):
        """Reset alle service instances (eager and lazy)."""
        self._instances.clear()
        self._lazy_instances.clear()
        logger.debug("Alle service instances gereset (eager + lazy)")

    def get_service(self, name: str):
        """
        Get een service op naam.

        Args:
            name: Naam van de service (generator, validator, repository, orchestrator, web_lookup)

        Returns:
            Service instance of None
        """
        service_map = {
            "generator": self.generator,
            # Legacy validator verwijderd; geen mapping meer beschikbaar
            "repository": self.repository,
            "orchestrator": self.orchestrator,
            "web_lookup": self.web_lookup,
            "duplicate_detector": self.duplicate_detector,
            "workflow": self.workflow,
            "cleaning_service": self.cleaning_service,
            "gate_policy": self.gate_policy,
            "definition_workflow_service": self.definition_workflow_service,
            "import_service": self.import_service,
            "synonym_registry": self.synonym_registry,
            "gpt4_synonym_suggester": self.gpt4_synonym_suggester,
            "synonym_orchestrator": self.synonym_orchestrator,
            "synonym_service": self.synonym_service,
            "ontological_classifier": self.ontological_classifier,
            "term_based_classifier": self.term_based_classifier,
        }

        if name in service_map:
            return service_map[name]()
        return None

    def get_initialization_count(self) -> int:
        """
        Get het aantal keer dat deze container is geïnitialiseerd.

        Returns:
            Aantal initialisaties (voor debugging van caching issues)
        """
        return getattr(self, "_initialization_count", 1)

    def get_container_id(self) -> str:
        """
        Get het unieke ID van deze container instance.

        Returns:
            Container ID (8-char UUID voor debugging van duplicate containers)
        """
        return getattr(self, "_container_id", "UNKNOWN")

    def update_config(self, config: dict[str, Any]):
        """
        Update configuratie en reset services.

        Args:
            config: Nieuwe configuratie
        """
        self.config.update(config)
        self._load_configuration()
        self.reset()
        logger.debug("Container configuratie geüpdatet")


# Globale container instance (optioneel)
_default_container: ServiceContainer | None = None


def get_container() -> ServiceContainer:
    """
    Get de singleton container instance.

    No config parameter allowed - container is initialized once with
    default configuration. This prevents duplicate initialization.

    Returns:
        ServiceContainer instance (singleton)
    """
    global _default_container

    if _default_container is None:
        # Initialize with None to use sensible defaults from _load_configuration()
        # which pulls from environment variables and ConfigManager
        _default_container = ServiceContainer(None)

    return _default_container


def reset_container():
    """Reset de globale container."""
    global _default_container
    if _default_container:
        _default_container.reset()
    _default_container = None


# Test configuraties voor verschillende environments
class ContainerConfigs:
    """Voorgedefinieerde configuraties voor verschillende environments."""

    @staticmethod
    def development() -> dict[str, Any]:
        """Development configuratie."""
        # Laat generator_model en generator_temperature weg zodat centrale config gebruikt wordt
        return {
            "db_path": "data/definities.db",
            # Model en temperature worden uit centrale config gehaald
            "enable_monitoring": True,
            "enable_ontology": True,  # Test ontologie in dev
            # Dead code verwijderd: enable_auto_save, min_quality_score (never used)
        }

    @staticmethod
    def testing() -> dict[str, Any]:
        """Test configuratie."""
        return {
            "db_path": ":memory:",  # In-memory database
            # Model wordt uit centrale config gehaald
            "enable_monitoring": False,
            "enable_ontology": False,  # Skip ontologie in tests voor snelheid
            "use_json_rules": False,  # Gebruik interne regels voor voorspelbare golden-acceptatie
            # Dead code verwijderd: enable_auto_save, enable_validation, enable_enrichment (never used)
        }

    @staticmethod
    def production() -> dict[str, Any]:
        """Production configuratie."""
        return {
            "db_path": "data/definities.db",
            # Model en temperature worden uit centrale config gehaald
            "enable_monitoring": True,
            "enable_ontology": True,  # Volledige ontologie in productie
            # Dead code verwijderd: enable_auto_save, enable_all_rules, min_quality_score (never used)
        }
