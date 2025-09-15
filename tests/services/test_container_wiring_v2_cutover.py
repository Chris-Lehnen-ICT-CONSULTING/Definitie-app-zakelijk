import inspect

import pytest


@pytest.mark.unit
def test_container_orchestrator_exists_and_is_validation_orchestrator_v2():
    from services.container import ServiceContainer, ContainerConfigs
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )

    container = ServiceContainer(ContainerConfigs.testing())
    orch = container.orchestrator()
    assert isinstance(orch, DefinitionOrchestratorV2)
    # And the embedded validation orchestrator is V2
    assert isinstance(orch.validation_service, ValidationOrchestratorV2)


@pytest.mark.unit
@pytest.mark.xfail(reason="Pending V2-only cutover: ModularValidationService not wired yet")
def test_container_uses_modular_validation_service_once_cutover_is_done():
    """
    This test documents the intended DI after Story 2.3 cutover.

    It should pass once the container wires ModularValidationService in place of
    the V1 adapter.
    """
    from services.container import ServiceContainer, ContainerConfigs
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )

    # Try to import the modular service; skip test early if the class/module is absent.
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    container = ServiceContainer(ContainerConfigs.testing())
    orch = container.orchestrator()
    assert isinstance(orch, ValidationOrchestratorV2)

    # Introspect the injected validation_service type if exposed (convention: attribute exists)
    injected = getattr(orch, "validation_service", None)
    assert injected is not None, "orchestrator should expose injected validation_service"
    assert isinstance(injected, m.ModularValidationService)
