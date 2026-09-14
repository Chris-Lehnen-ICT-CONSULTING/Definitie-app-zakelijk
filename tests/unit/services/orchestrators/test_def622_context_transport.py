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

    De dubbel bewaart eerst een snapshot van wat hij ontving
    (`service.received`) en muteert daarna de ontvangen context in de diepte
    (een geneste lijst én de `options`-dict): een oppervlakkige kopie zou die
    mutatie naar de aanroeper laten doorlekken, en dan slaagt de
    invoer-onveranderd-assertie niet meer.
    """
    service = AsyncMock()

    async def _muteer(*_args, **kwargs):
        context = kwargs.get("context") or {}
        service.received = deepcopy(context)
        for veld in ("organisatorische_context", "wettelijke_basis"):
            if isinstance(context.get(veld), list):
                context[veld].append("gemuteerd door service")
        if isinstance(context.get("options"), dict):
            context["options"]["force_duplicate"] = "gemuteerd"
        return {"version": CONTRACT_VERSION, "system": {}}

    service.validate_definition.side_effect = _muteer
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
    assert service.received == metadata
    # De dubbel heeft `supplied` in de diepte gemuteerd; de aanroeper mag
    # daar niets van merken.
    assert supplied["organisatorische_context"][-1] == "gemuteerd door service"
    assert supplied["options"]["force_duplicate"] == "gemuteerd"
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
    supplied = service.received
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
    supplied = service.received
    assert supplied["wettelijke_basis"] == ["Regeling Z"]
    assert supplied["organisatorische_context"] == []
    assert supplied["juridische_context"] == []
    assert supplied["definition_id"] is None


async def test_empty_record_category_and_id_override_caller_values():
    """Recordautoriteit geldt ook voor een record zónder categorie of id.

    Zou een ontbrekende recordwaarde de aanroeperwaarde laten staan, dan zoekt
    DUP_01 op categorie 'proces' terwijl het record geen categorie draagt, en
    mist het een gelijk-contextkandidaat met categorie 'type'
    (reviewbevinding op de transportcommit).
    """
    service = _service()
    definition = Definition(
        begrip="keurmerk",
        definitie="kwaliteitsmerk",
        organisatorische_context=["Stichting Zilver"],
    )
    await ValidationOrchestratorV2(service).validate_definition(
        definition,
        ValidationContext(
            metadata={
                "categorie": "proces",
                "ontologische_categorie": "proces",
                "definition_id": 7,
            }
        ),
    )
    supplied = service.validate_definition.call_args.kwargs["context"]
    assert supplied["categorie"] is None
    assert supplied["ontologische_categorie"] is None
    assert supplied["definition_id"] is None
