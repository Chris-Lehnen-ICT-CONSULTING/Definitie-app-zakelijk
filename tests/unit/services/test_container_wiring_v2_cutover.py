"""Actieve DI-keten van de ServiceContainer (DEF-519).

De oude xfail in dit bestand documenteerde een architectuur die nooit gebouwd
is: `container.orchestrator()` zou zélf een `ValidationOrchestratorV2` worden en
de cutover naar `ModularValidationService` moest nog komen. Het werkelijke
contract is anders — de container levert een `DefinitionOrchestratorV2`, die
lazy een `ValidationOrchestratorV2` opbouwt met daarin de echte
`ModularValidationService`. Deze tests toetsen die keten op
instantie-identiteit én op een werkelijk uitgevoerde validatie, zodat een
teruggedraaide of gemockte validatielaag hier omvalt.
"""

from typing import Any

import pytest

pytestmark = [pytest.mark.unit]


def _sluit_eigen_verbindingen(container: Any) -> None:
    """Sluit de SQLite-verbinding die deze test zelf liet openen."""
    repository = container._instances.get("repository")
    verbinding = getattr(getattr(repository, "legacy_repo", None), "_db", None)
    staat = getattr(getattr(verbinding, "_thread_local", None), "state", None)
    if staat is not None:
        staat.close()


@pytest.fixture
def container(tmp_path):
    """Echte container op een verse tijdelijke database, met echte regelset."""
    from services.container import ContainerConfigs, ServiceContainer

    instantie = ServiceContainer(
        {
            **ContainerConfigs.testing(),
            "db_path": str(tmp_path / "def519-di-contract.db"),
            # De echte regelset, zodat de validatielaag ook werkelijk evalueert.
            # Met `False` laadt hij 0/53 regels en valt hij fail-closed terug op
            # `validation_unknown` — precies het verschil dat
            # `test_wired_validation_service_evaluates_the_real_ruleset` meet.
            "use_json_rules": True,
        }
    )
    try:
        yield instantie
    finally:
        _sluit_eigen_verbindingen(instantie)
        instantie.reset()


@pytest.mark.unit
def test_container_orchestrator_exists_and_is_validation_orchestrator_v2(container):
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )

    orch = container.orchestrator()
    assert isinstance(orch, DefinitionOrchestratorV2)
    # And the embedded validation orchestrator is V2
    assert isinstance(orch.validation_service, ValidationOrchestratorV2)


@pytest.mark.unit
def test_container_wires_modular_validation_service_in_validation_orchestrator(
    container,
):
    """De keten container → definitie-orchestrator → validatie-orchestrator → service.

    Elke schakel wordt op concrete instantie-identiteit getoetst, niet op
    aanwezigheid van een attribuut.
    """
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )

    orch = container.orchestrator()

    assert isinstance(orch, DefinitionOrchestratorV2)
    # De oude xfail verwachtte de validatie-orchestrator hier zélf. Die stand
    # bestaat niet: de definitie-orchestrator bevat hem.
    assert not isinstance(orch, ValidationOrchestratorV2)

    validatie_orchestrator = orch.validation_service
    assert isinstance(validatie_orchestrator, ValidationOrchestratorV2)

    modulair = validatie_orchestrator.validation_service
    assert isinstance(modulair, ModularValidationService)

    # Dezelfde instanties, geen tweede keten naast de gebruikte.
    assert container.orchestrator() is orch
    assert container.validation_orchestrator() is validatie_orchestrator


@pytest.mark.unit
async def test_wired_validation_service_evaluates_the_real_ruleset(container):
    """De bedrade validatielaag voert echte regels uit op echte tekst."""
    validatie_orchestrator = container.validation_orchestrator()

    resultaat = await validatie_orchestrator.validate_text(
        "koopovereenkomst",
        "overeenkomst waarbij de verkoper zich verbindt een zaak te leveren en "
        "de koper zich verbindt daarvoor een prijs in geld te betalen",
    )

    assert resultaat["validation_status"] == "validated"

    dekking = resultaat["evaluation_coverage"]
    assert dekking["total"] == 53
    assert dekking["evaluated"] > 0
    assert dekking["evaluated"] == dekking["passed"] + dekking["failed"]
    assert dekking["coverage_ratio"] > 0

    statussen = resultaat["rule_statuses"]
    assert len(statussen) == dekking["total"]
    assert set(statussen.values()) <= {
        "pass",
        "fail",
        "review_required",
        "not_evaluated",
        "error",
    }

    # Elke gemelde overtreding komt uit een regel die ook echt op `fail` staat.
    assert resultaat["violations"]
    for overtreding in resultaat["violations"]:
        assert statussen[overtreding["rule_id"]] == "fail"
