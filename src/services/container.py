"""
Dependency Injection Container voor de services.

Deze container beheert de instanties van alle services en hun dependencies.
Dit maakt het makkelijk om services te configureren, testen en swappen.
"""

import logging
import os
from typing import Any

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_orchestrator import DefinitionOrchestrator, OrchestratorConfig
from services.definition_repository import DefinitionRepository
from services.definition_validator import DefinitionValidator, ValidatorConfig
from services.duplicate_detection_service import DuplicateDetectionService
from services.interfaces import (
    DefinitionGeneratorInterface,
    DefinitionOrchestratorInterface,
    DefinitionRepositoryInterface,
    DefinitionValidatorInterface,
    WebLookupServiceInterface,
)
from services.modern_web_lookup_service import ModernWebLookupService
from services.unified_definition_generator import UnifiedDefinitionGenerator
from services.workflow_service import WorkflowService

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

        gpt_config = GPTConfig(
            model=self.config.get("generator_model", "gpt-4"),
            temperature=self.config.get("generator_temperature", 0.4),
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

        self.validator_config = ValidatorConfig(
            enable_all_rules=self.config.get("enable_all_rules", True),
            min_score_threshold=self.config.get("min_score_threshold", 0.6),
            enable_suggestions=self.config.get("enable_suggestions", True),
        )

        self.orchestrator_config = OrchestratorConfig(
            enable_validation=self.config.get("enable_validation", True),
            enable_enrichment=self.config.get("enable_enrichment", True),
            enable_auto_save=self.config.get("enable_auto_save", True),
            min_quality_score=self.config.get("min_quality_score", 0.6),
        )

    # Service factory methods

    def generator(self) -> DefinitionGeneratorInterface:
        """
        Get of create DefinitionGenerator instance.

        Returns:
            Singleton instance van DefinitionGenerator
        """
        if "generator" not in self._instances:
            self._instances["generator"] = UnifiedDefinitionGenerator(
                self.generator_config
            )
            logger.info("UnifiedDefinitionGenerator instance aangemaakt")
        return self._instances["generator"]

    def validator(self) -> DefinitionValidatorInterface:
        """
        Get of create DefinitionValidator instance.

        Returns:
            Singleton instance van DefinitionValidator
        """
        if "validator" not in self._instances:
            self._instances["validator"] = DefinitionValidator(self.validator_config)
            logger.info("DefinitionValidator instance aangemaakt")
        return self._instances["validator"]

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
            Singleton instance van DefinitionOrchestrator
        """
        if "orchestrator" not in self._instances:
            self._instances["orchestrator"] = DefinitionOrchestrator(
                generator=self.generator(),
                validator=self.validator(),
                repository=self.repository(),
                config=self.orchestrator_config,
            )
            logger.info("DefinitionOrchestrator instance aangemaakt")
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
        return {
            "db_path": "data/dev_definities.db",
            "generator_model": "gpt-3.5-turbo",  # Goedkoper voor dev
            "generator_temperature": 0.5,
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
            "generator_model": "gpt-3.5-turbo",
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
            "db_path": "data/production_definities.db",
            "generator_model": "gpt-4",
            "generator_temperature": 0.4,
            "enable_monitoring": True,
            "enable_auto_save": True,
            "enable_all_rules": True,
            "enable_ontology": True,  # Volledige ontologie in productie
            "min_quality_score": 0.7,  # Hogere kwaliteitseis
        }
