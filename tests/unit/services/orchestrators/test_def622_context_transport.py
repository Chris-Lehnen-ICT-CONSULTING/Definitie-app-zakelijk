"""DEF-622: context blijft gestructureerd aanwezig op de V2-servicegrens.

Vóór DEF-622 bouwde `ValidationOrchestratorV2` een context-dict met alleen
`profile`, `correlation_id`, `locale` en `feature_flags`; `context.metadata`
en de drie contextlijsten van een `Definition` bereikten de service nooit.
CON-01 (contextcontract) en DUP_01 (duplicaatidentiteit) hebben die lijsten
nodig, dus dit transport is een harde eis en geen best-effort verrijking.
"""

from copy import deepcopy
from unittest.mock import AsyncMock

import pytest

from services.interfaces import Definition
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.interfaces import CONTRACT_VERSION, ValidationContext

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _service() -> AsyncMock:
    """Servicedubbel met een schema-herkenbaar antwoord.

    `{}` als antwoord laat `ensure_schema_compliance` naar een degraded result
    vallen en logt daarbij een mapperfout; dat is ruis die niets met het
    transport te maken heeft. `version` + `system` volstaan voor de mapper.
    """
    service = AsyncMock()
    service.validate_definition.return_value = {
        "version": CONTRACT_VERSION,
        "system": {},
    }
    return service


async def test_text_transports_context_metadata_without_mutating_input():
    service = _service()
    metadata = {
        "organisatorische_context": ["Stichting Zilver"],
        "juridische_context": ["privaatrecht"],
        "wettelijke_basis": ["Regeling Z"],
        "options": {"force_duplicate": True},
    }
    before = deepcopy(metadata)
    await ValidationOrchestratorV2(service).validate_text(
        "keurmerk", "kwaliteitsmerk", context=ValidationContext(metadata=metadata)
    )
    supplied = service.validate_definition.call_args.kwargs["context"]
    assert supplied == metadata
    assert metadata == before
    assert supplied is not metadata


async def test_definition_context_is_authoritative_including_empty_lists():
    service = _service()
    definition = Definition(
        id=42,
        begrip="keurmerk",
        definitie="kwaliteitsmerk",
        organisatorische_context=[" Zilver ", "zilver", ""],
        categorie="type",
    )
    await ValidationOrchestratorV2(service).validate_definition(
        definition,
        ValidationContext(metadata={"juridische_context": ["verouderde invoer"]}),
    )
    supplied = service.validate_definition.call_args.kwargs["context"]
    assert supplied["organisatorische_context"] == ["Zilver"]
    assert supplied["juridische_context"] == []
    assert supplied["wettelijke_basis"] == []
    assert supplied["definition_id"] == 42
    assert supplied["categorie"] == "type"
    assert definition.organisatorische_context == [" Zilver ", "zilver", ""]


async def test_definition_context_travels_without_validation_context():
    """Ook zonder `ValidationContext` reizen de recordlijsten mee.

    De UI en de importservice valideren een `Definition` doorgaans zonder
    aparte `ValidationContext`. Zou het transport aan dat object hangen, dan
    zou CON-01 voor zo'n record 'geen context' melden terwijl het record wél
    context draagt.
    """
    service = _service()
    definition = Definition(
        begrip="keurmerk",
        definitie="kwaliteitsmerk",
        wettelijke_basis=["Regeling Z", "regeling z"],
    )
    await ValidationOrchestratorV2(service).validate_definition(definition)
    supplied = service.validate_definition.call_args.kwargs["context"]
    assert supplied["wettelijke_basis"] == ["Regeling Z"]
    assert supplied["organisatorische_context"] == []
    assert supplied["juridische_context"] == []
    assert "definition_id" not in supplied
