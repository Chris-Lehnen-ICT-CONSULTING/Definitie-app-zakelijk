"""
Dependency Injection Container voor de services.

Deze container beheert de instanties van alle services en hun dependencies.
Dit maakt het makkelijk om services te configureren, testen en swappen.
"""

import logging
import os
from typing import TYPE_CHECKING, Any

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
from services.orchestrators.definition_orchestrator_v2 import (
    DefinitionOrchestratorV2,
)

# UnifiedDefinitionGenerator vervangen door DefinitionOrchestrator
# from services.unified_definition_generator import UnifiedDefinitionGenerator
from services.workflow_service import WorkflowService

from config.config_manager import (
    get_component_config,
    get_default_model,
    get_default_temperature,
)

if TYPE_CHECKING:
    from services.data_aggregation_service import DataAggregationService
    from services.definition_ui_service import DefinitionUIService
    from services.export_service import ExportService

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
        self._load_configuration()
        logger.info("ServiceContainer geïnitialiseerd")

    def _load_configuration(self):
        """Laad configuratie uit environment en config dict."""
        # Basis configuratie
        self.db_path = self.config.get("db_path", "data/definities.db")
        self.openai_api_key = self.config.get(
            "openai_api_key", os.getenv("OPENAI_API_KEY")
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
            logger.info("DefinitionOrchestratorV2 instance aangemaakt als generator")
        return self._instances["generator"]

    # Legacy validator() method removed - validation now handled by V2 orchestrator

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

                # Inject duplicate service if enabled
                if self.config.get("use_new_duplicate_detection", True):
                    repository.set_duplicate_service(self.duplicate_detector())

                self._instances["repository"] = repository
                logger.info(
                    f"DefinitionRepository instance aangemaakt met db: {self.db_path}"
                )
            else:
                from services.null_repository import NullDefinitionRepository

                self._instances["repository"] = NullDefinitionRepository()
                logger.info(
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
            from services.interfaces import (
                OrchestratorConfig as V2OrchestratorConfig,
            )
            from services.prompts.prompt_service_v2 import PromptServiceV2
            from services.validation.config import ValidationConfig

            # Validation service: cutover to modular V2 implementation
            from services.validation.modular_validation_service import (
                ModularValidationService,
            )
            from toetsregels.manager import get_toetsregel_manager

            v2_config = V2OrchestratorConfig()

            # Create all required V2 services
            prompt_service = PromptServiceV2()
            ai_service = AIServiceV2(
                default_model=self.generator_config.gpt.model, use_cache=True
            )

            # Create ModularValidationService (V2)
            modular_validation_service = ModularValidationService(
                get_toetsregel_manager(),
                None,
                ValidationConfig.from_yaml("src/config/validation_rules.yaml"),
            )
            cleaning_service = CleaningServiceAdapterV1toV2(self.cleaning_service())

            # Create ValidationOrchestratorV2 wrapping ModularValidationService
            from services.orchestrators.validation_orchestrator_v2 import (
                ValidationOrchestratorV2,
            )

            validation_orchestrator = ValidationOrchestratorV2(
                validation_service=modular_validation_service,
                cleaning_service=cleaning_service,
            )

            self._instances["orchestrator"] = DefinitionOrchestratorV2(
                # Required V2 services
                prompt_service=prompt_service,
                ai_service=ai_service,
                validation_service=validation_orchestrator,
                cleaning_service=cleaning_service,
                repository=self.repository(),
                # Optional services
                enhancement_service=None,  # Not implemented yet
                security_service=None,  # Not implemented yet
                monitoring=None,  # Not implemented yet
                feedback_engine=None,  # Not implemented yet
                # Configuration
                config=v2_config,
            )
            logger.info("DefinitionOrchestratorV2 instance created")

        return self._instances["orchestrator"]

    def web_lookup(self) -> WebLookupServiceInterface:
        """
        Get of create ModernWebLookupService instance.

        Returns:
            Singleton instance van ModernWebLookupService
        """
        if "web_lookup" not in self._instances:
            self._instances["web_lookup"] = ModernWebLookupService()
            logger.info("ModernWebLookupService instance aangemaakt")
        return self._instances["web_lookup"]

    def duplicate_detector(self) -> DuplicateDetectionService:
        """
        Get of create DuplicateDetectionService instance.

        Returns:
            Singleton instance van DuplicateDetectionService
        """
        if "duplicate_detector" not in self._instances:
            similarity_threshold = self.config.get(
                "duplicate_similarity_threshold", 0.7
            )
            self._instances["duplicate_detector"] = DuplicateDetectionService(
                similarity_threshold=similarity_threshold
            )
            logger.info(
                f"DuplicateDetectionService instance aangemaakt met threshold {similarity_threshold}"
            )
        return self._instances["duplicate_detector"]

    def workflow(self) -> WorkflowService:
        """
        Get of create WorkflowService instance.

        Returns:
            Singleton instance van WorkflowService
        """
        if "workflow" not in self._instances:
            self._instances["workflow"] = WorkflowService()
            logger.info("WorkflowService instance aangemaakt")
        return self._instances["workflow"]

    def cleaning_service(self) -> CleaningServiceInterface:
        """
        Get of create CleaningService instance.

        Returns:
            Singleton instance van CleaningService
        """
        if "cleaning_service" not in self._instances:
            from services.cleaning_service import CleaningService

            self._instances["cleaning_service"] = CleaningService(self.cleaning_config)
            logger.info("CleaningService instance aangemaakt")
        return self._instances["cleaning_service"]

    def data_aggregation_service(self) -> "DataAggregationService":
        """
        Get of create DataAggregationService instance.

        Returns:
            Singleton instance van DataAggregationService
        """
        if "data_aggregation_service" not in self._instances:
            from services.data_aggregation_service import DataAggregationService

            # Use existing repository instance
            repo = self.repository()
            self._instances["data_aggregation_service"] = DataAggregationService(repo)
            logger.info("DataAggregationService instance aangemaakt")
        return self._instances["data_aggregation_service"]

    def export_service(self) -> "ExportService":
        """
        Get of create ExportService instance.

        Returns:
            Singleton instance van ExportService
        """
        if "export_service" not in self._instances:
            from services.export_service import ExportService

            # Use existing services
            repo = self.repository()
            data_agg_service = self.data_aggregation_service()

            # Get export directory from config
            export_dir = self.config.get("export_dir", "exports")

            self._instances["export_service"] = ExportService(
                repository=repo,
                data_aggregation_service=data_agg_service,
                export_dir=export_dir,
                validation_orchestrator=self.orchestrator(),
                enable_validation_gate=self.config.get(
                    "enable_export_validation_gate", False
                ),
            )
            logger.info("ExportService instance aangemaakt")
        return self._instances["export_service"]

    def definition_ui_service(self) -> "DefinitionUIService":
        """
        Get of create DefinitionUIService instance.

        Returns:
            Singleton instance van DefinitionUIService
        """
        if "definition_ui_service" not in self._instances:
            from ui.services.definition_ui_service import DefinitionUIService

            # Use existing services
            repo = self.repository()
            workflow_service = self.workflow()
            export_service = self.export_service()
            data_agg_service = self.data_aggregation_service()

            self._instances["definition_ui_service"] = DefinitionUIService(
                repository=repo,
                workflow_service=workflow_service,
                export_service=export_service,
                data_aggregation_service=data_agg_service,
            )
            logger.info("DefinitionUIService instance aangemaakt")
        return self._instances["definition_ui_service"]

    # Utility methods

    def reset(self):
        """Reset alle service instances."""
        self._instances.clear()
        logger.info("Alle service instances gereset")

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
            "validator": self.validator,
            "repository": self.repository,
            "orchestrator": self.orchestrator,
            "web_lookup": self.web_lookup,
            "duplicate_detector": self.duplicate_detector,
            "workflow": self.workflow,
            "cleaning_service": self.cleaning_service,
        }

        if name in service_map:
            return service_map[name]()
        return None

    def update_config(self, config: dict[str, Any]):
        """
        Update configuratie en reset services.

        Args:
            config: Nieuwe configuratie
        """
        self.config.update(config)
        self._load_configuration()
        self.reset()
        logger.info("Container configuratie geüpdatet")


# Globale container instance (optioneel)
_default_container: ServiceContainer | None = None


def get_container(config: dict[str, Any] | None = None) -> ServiceContainer:
    """
    Get de default container instance.

    Args:
        config: Optionele configuratie voor nieuwe container

    Returns:
        ServiceContainer instance
    """
    global _default_container

    if _default_container is None or config is not None:
        _default_container = ServiceContainer(config)

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
            "enable_auto_save": False,  # Geen auto-save in dev
            "enable_ontology": True,  # Test ontologie in dev
            "min_quality_score": 0.5,  # Lagere threshold voor dev
        }

    @staticmethod
    def testing() -> dict[str, Any]:
        """Test configuratie."""
        return {
            "db_path": ":memory:",  # In-memory database
            # Model wordt uit centrale config gehaald
            "enable_monitoring": False,
            "enable_auto_save": False,
            "enable_validation": True,
            "enable_enrichment": False,  # Skip enrichment in tests
            "enable_ontology": False,  # Skip ontologie in tests voor snelheid
        }

    @staticmethod
    def production() -> dict[str, Any]:
        """Production configuratie."""
        return {
            "db_path": "data/definities.db",
            # Model en temperature worden uit centrale config gehaald
            "enable_monitoring": True,
            "enable_auto_save": True,
            "enable_all_rules": True,
            "enable_ontology": True,  # Volledige ontologie in productie
            "min_quality_score": 0.7,  # Hogere kwaliteitseis
        }
