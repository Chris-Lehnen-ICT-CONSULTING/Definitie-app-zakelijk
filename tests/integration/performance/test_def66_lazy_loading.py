"""
DEF-66: Tests for lazy loading optimization.

Tests verify that PromptServiceV2 and other heavy services
are NOT initialized until first use, reducing TabbedInterface
initialization from 509ms to <180ms.

DEF-519 — alleen de database- en containerfixture is gecorrigeerd. De
numerieke grenzen (`MAX_*_MS`) en de gemeten paden zijn ongewijzigd: elke
duurmeting hieronder omvat nog steeds de échte `ServiceContainer`- en
`TabbedInterface`-initialisatie, inclusief de echte `DefinitieRepository` met
schema-init. Alleen het *doelpad* van SQLite is verlegd naar `tmp_path`; de
containerfabriek en de repository-fabriek zelf draaien onveranderd door. Er
wordt dus geen tijd van een dubbel gemeten en geen prestatieverbetering
geclaimd — de meting is dezelfde, alleen niet meer op de
repository-database (`data/definities.db`), die de offline-gate terecht weigert.
"""

import time
from unittest.mock import MagicMock, Mock, patch

import pytest

pytestmark = [pytest.mark.performance]

# DEF-66 Performance targets
MAX_CONTAINER_INIT_MS = 200  # Maximum acceptable container initialization time


def _sluit_container_verbindingen(container) -> None:
    """Sluit de SQLite-verbindingen die deze container zelf opende.

    `DatabaseConnection` houdt één verbinding per thread in een
    `_ThreadConnectionState`; die klasse sluit haar eigen verbinding. Zonder
    deze stap blijft zij open tot de garbage collector toeslaat — zichtbaar als
    ResourceWarning.
    """
    from database.db_connection import DatabaseConnection

    gezien: set[int] = set()
    for instantie in list(getattr(container, "_instances", {}).values()):
        for houder in (instantie, getattr(instantie, "legacy_repo", None)):
            db = getattr(houder, "_db", None)
            if not isinstance(db, DatabaseConnection) or id(db) in gezien:
                continue
            gezien.add(id(db))
            toestand = getattr(db._thread_local, "state", None)
            if toestand is not None:
                toestand.close()


@pytest.fixture
def container_op_eigen_db(tmp_path, monkeypatch):
    """Laat de échte containerfabriek een eigen, tijdelijke database gebruiken.

    `get_cached_container()` blijft de gemeten functie: hij leest zijn config
    nog steeds uit `ContainerConfigs` en bouwt een echte `ServiceContainer`.
    Alleen `db_path` wordt overschreven, op de bestaande fabrieksgrens
    (`utils.container_manager.ServiceContainer`). Dat is geen dubbel: de echte
    klasse wordt aangeroepen met een ander pad.
    """
    from services.container import ServiceContainer
    from utils import container_manager

    db_path = tmp_path / "container-definities.db"
    gemaakt: list[ServiceContainer] = []

    def _container_met_eigen_db(config):
        container = ServiceContainer({**config, "db_path": str(db_path)})
        gemaakt.append(container)
        return container

    monkeypatch.setattr(container_manager, "ServiceContainer", _container_met_eigen_db)
    container_manager.get_cached_container.cache_clear()
    try:
        yield db_path
    finally:
        # Vanaf de eerste aanmaak bezit deze fixture de verbindingen van elke
        # container die zij liet bouwen; die worden hier gesloten.
        for container in gemaakt:
            _sluit_container_verbindingen(container)
        # Eigen cacheherstel: een container die naar deze tijdelijke database
        # wijst mag niet in de LRU-cache achterblijven voor een volgende test.
        container_manager.get_cached_container.cache_clear()


@pytest.fixture
def repository_op_eigen_db(tmp_path, monkeypatch):
    """Laat de échte repositoryfabriek een eigen, tijdelijke database gebruiken.

    `TabbedInterface.__init__` resolvet `get_definitie_repository` bij aanroep
    uit `database.definitie_repository`; die fabrieksgrens krijgt hier een
    expliciet `tmp_path`-pad mee. De fabriek zelf (inclusief schema-init) draait
    onveranderd binnen de meting.
    """
    from database import definitie_repository as repo_module

    db_path = tmp_path / "ui-definities.db"
    originele_fabriek = repo_module.get_definitie_repository

    def _fabriek_met_eigen_db(_db_path=None):
        return originele_fabriek(str(db_path))

    repo_module.clear_repository_singleton()
    monkeypatch.setattr(repo_module, "get_definitie_repository", _fabriek_met_eigen_db)
    try:
        yield db_path
    finally:
        singleton = repo_module._repository_singleton
        if singleton is not None:
            toestand = getattr(singleton._db._thread_local, "state", None)
            if toestand is not None:
                toestand.close()
        repo_module.clear_repository_singleton()


class TestPromptServiceLazyLoading:
    """Test that PromptServiceV2 is lazy-loaded in DefinitionOrchestratorV2."""

    def test_orchestrator_init_does_not_create_prompt_service(self):
        """
        CRITICAL: Orchestrator __init__ should NOT create PromptServiceV2.

        This is the core of DEF-66 fix - defer expensive initialization.
        """
        from services.orchestrators.definition_orchestrator_v2 import (
            DefinitionOrchestratorV2,
        )

        # Mock all required dependencies
        ai_service = Mock()
        validation_service = Mock()
        cleaning_service = Mock()
        repository = Mock()

        # Track if PromptServiceV2 was instantiated
        with patch(
            "services.prompts.prompt_service_v2.PromptServiceV2"
        ) as mock_prompt_class:
            # Create orchestrator WITHOUT passing prompt_service
            # (implementation should create it lazily)
            orchestrator = DefinitionOrchestratorV2(
                prompt_service=None,  # Key test: None should be accepted
                ai_service=ai_service,
                validation_service=validation_service,
                cleaning_service=cleaning_service,
                repository=repository,
            )

            # Verify PromptServiceV2 was NOT instantiated during __init__
            mock_prompt_class.assert_not_called()
            assert orchestrator is not None

    def test_prompt_service_created_on_first_use(self):
        """
        PromptServiceV2 should be created only when first needed.
        """
        from services.orchestrators.definition_orchestrator_v2 import (
            DefinitionOrchestratorV2,
        )

        # Mock all required dependencies
        ai_service = Mock()
        validation_service = Mock()
        cleaning_service = Mock()
        repository = Mock()

        # Create orchestrator with lazy prompt service
        orchestrator = DefinitionOrchestratorV2(
            prompt_service=None,
            ai_service=ai_service,
            validation_service=validation_service,
            cleaning_service=cleaning_service,
            repository=repository,
        )

        # Mock PromptServiceV2 to track instantiation
        with patch(
            "services.prompts.prompt_service_v2.PromptServiceV2"
        ) as mock_prompt_class:
            mock_prompt_instance = Mock()
            mock_prompt_class.return_value = mock_prompt_instance

            # Access prompt service property (should trigger creation)
            _ = orchestrator.prompt_service

            # Verify PromptServiceV2 was instantiated on first access
            mock_prompt_class.assert_called_once()

    def test_prompt_service_cached_after_first_access(self):
        """
        PromptServiceV2 should be created once and cached.
        """
        from services.orchestrators.definition_orchestrator_v2 import (
            DefinitionOrchestratorV2,
        )

        # Mock all required dependencies
        ai_service = Mock()
        validation_service = Mock()
        cleaning_service = Mock()
        repository = Mock()

        orchestrator = DefinitionOrchestratorV2(
            prompt_service=None,
            ai_service=ai_service,
            validation_service=validation_service,
            cleaning_service=cleaning_service,
            repository=repository,
        )

        with patch(
            "services.prompts.prompt_service_v2.PromptServiceV2"
        ) as mock_prompt_class:
            mock_prompt_instance = Mock()
            mock_prompt_class.return_value = mock_prompt_instance

            # Access multiple times
            service1 = orchestrator.prompt_service
            service2 = orchestrator.prompt_service
            service3 = orchestrator.prompt_service

            # Verify PromptServiceV2 was instantiated only ONCE
            mock_prompt_class.assert_called_once()

            # Verify same instance returned
            assert service1 is service2
            assert service2 is service3


class TestServiceContainerPerformance:
    """Test that ServiceContainer initialization is fast."""

    def test_service_container_init_under_200ms(self, container_op_eigen_db):
        """
        ServiceContainer initialization should be <200ms after lazy loading fix.

        Target: 509ms → <180ms (DEF-66 acceptance criteria)
        """
        from utils.container_manager import get_cached_container

        # Clear any existing cache
        get_cached_container.cache_clear()

        start = time.perf_counter()
        container = get_cached_container()
        duration_ms = (time.perf_counter() - start) * 1000

        # Verify initialization is reasonably fast
        # Note: First call may still take ~100-150ms for config loading
        # But should be <200ms (much better than 509ms)
        assert duration_ms < MAX_CONTAINER_INIT_MS, (
            f"Container init took {duration_ms:.1f}ms "
            f"(expected <{MAX_CONTAINER_INIT_MS}ms)"
        )

        # Verify container was created
        assert container is not None
        assert hasattr(container, "orchestrator")

    def test_orchestrator_creation_deferred_until_access(self, container_op_eigen_db):
        """
        Orchestrator (and its dependencies) should NOT be created during container init.
        """
        from utils.container_manager import get_cached_container

        get_cached_container.cache_clear()

        # Create container
        container = get_cached_container()

        # Verify orchestrator is NOT in instances yet (lazy loading)
        # Check internal state without triggering lazy load
        assert "orchestrator" not in container._instances

        # Now access it (should trigger lazy load)
        _ = container.orchestrator()

        # Verify now it's cached
        assert "orchestrator" in container._instances


class TestBackwardsCompatibility:
    """Ensure lazy loading doesn't break existing code."""

    def test_orchestrator_with_explicit_prompt_service_still_works(self):
        """
        Existing code that passes prompt_service explicitly should still work.

        Backwards compatibility requirement.
        """
        from services.orchestrators.definition_orchestrator_v2 import (
            DefinitionOrchestratorV2,
        )

        # Mock all dependencies
        prompt_service = Mock()
        ai_service = Mock()
        validation_service = Mock()
        cleaning_service = Mock()
        repository = Mock()

        # Old way: passing prompt_service explicitly
        orchestrator = DefinitionOrchestratorV2(
            prompt_service=prompt_service,  # Explicit (old way)
            ai_service=ai_service,
            validation_service=validation_service,
            cleaning_service=cleaning_service,
            repository=repository,
        )

        # Verify orchestrator was created
        assert orchestrator is not None

        # Verify prompt_service is available
        assert orchestrator.prompt_service is prompt_service


class TestPerformanceRegression:
    """Performance regression tests."""

    def test_tabbed_interface_reuses_prewarmed_container_and_repository(
        self,
        container_op_eigen_db,
        repository_op_eigen_db,
        request,
        record_testsuite_property,
    ):
        """TabbedInterface bouwt op de opgewarmde container en deelt die bedrading.

        Bewijst wat DEF-66 werkelijk oplevert: de UI maakt geen eigen container of
        repository aan, en herhaald construeren blijft op dezelfde objecten staan.
        DEF-563: de historische 200ms-eis uit DEF-66 is als testdrempel
        ingetrokken — actuele runnerkalibratie ontbreekt. De duur blijft
        informatief vastgelegd als record_testsuite_property, zonder drempel.

        Deze test rendert niets en doet geen providercall; de fixtures houden
        beide databases in tmp_path.
        """
        from ui.tabbed_interface import TabbedInterface
        from utils.container_manager import get_cached_container

        def _registreer_editrepo_sluiting(gebouwde_interface) -> None:
            """Sluit de verbinding die déze interface buiten de fixtures om opende.

            `DefinitionEditTab.__init__` krijgt van TabbedInterface geen
            repository mee en maakt er zelf één (definition_edit_tab.py:38);
            die `DefinitionEditRepository` bouwt via `DefinitionRepository`
            een eigen `legacy_repo` met eigen `DatabaseConnection`
            (definition_repository.py:63). Die valt buiten `_instances` van de
            container en buiten de repository-singleton, dus geen van beide
            fixtures ruimt hem op. Zonder deze finalizer blijft de
            thread-verbinding open tot de garbage collector toeslaat —
            zichtbaar als ResourceWarning.
            """
            db = gebouwde_interface.edit_tab.repository.legacy_repo._db
            toestand = getattr(db._thread_local, "state", None)
            if toestand is not None:
                request.addfinalizer(toestand.close)

        # Pre-create container (simulates app startup)
        get_cached_container.cache_clear()
        voorverwarmde_container = get_cached_container()

        start = time.perf_counter()
        interface = TabbedInterface()
        duration_ms = (time.perf_counter() - start) * 1000
        _registreer_editrepo_sluiting(interface)

        # De UI pakt de opgewarmde singleton in plaats van zelf te bouwen; een
        # tweede container zou hier een ander object opleveren.
        assert interface.container is voorverwarmde_container

        # De repository komt van de tijdelijke database van de fixture, dus niet
        # van de repository-database data/definities.db.
        assert interface.repository.db_path == str(repository_op_eigen_db)

        # Concrete componentkoppeling: checker en handler draaien op exact deze
        # repository en service, niet op eigen tweede instanties.
        assert interface.checker.repository is interface.repository
        assert interface.generation_handler.checker is interface.checker
        assert interface.generation_handler.repository is interface.repository
        assert (
            interface.generation_handler.definition_service
            is interface.definition_service
        )

        # De service is de echte ServiceAdapter uit de container, niet de
        # _DummyService waarop TabbedInterface.__init__ terugvalt als de
        # initialisatie faalt: die meldt "dummy" (service_factory.py:132).
        assert (
            interface.definition_service.get_service_info()["service_mode"]
            == "container_v2"
        )

        # Herhaald construeren hergebruikt container én repository, en koppelt de
        # nieuwe handler weer op diezelfde repository en een echte service.
        tweede_interface = TabbedInterface()
        _registreer_editrepo_sluiting(tweede_interface)
        assert tweede_interface.container is voorverwarmde_container
        assert tweede_interface.repository is interface.repository
        assert tweede_interface.generation_handler.repository is interface.repository
        assert (
            tweede_interface.definition_service.get_service_info()["service_mode"]
            == "container_v2"
        )

        # Informatief, geen drempel. Suite-breed; onder xdist niet geclaimd.
        record_testsuite_property(
            "def563_tabbed_interface_init_ms", round(duration_ms, 1)
        )
