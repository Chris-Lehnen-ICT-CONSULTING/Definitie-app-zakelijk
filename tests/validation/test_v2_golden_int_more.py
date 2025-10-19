import pytest

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager


@pytest.mark.asyncio()
async def test_int02_no_decision_rules_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="toegang",
        text="Toegang: toestemming verleend door een bevoegde autoriteit, indien alle voorwaarden zijn vervuld.",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "INT-02" for v in res.get("violations", [])), res


@pytest.mark.asyncio()
async def test_int08_positive_formulation_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="bevoegd persoon",
        text="bevoegd persoon: iemand die niet onbevoegd is",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "INT-08" for v in res.get("violations", [])), res


@pytest.mark.asyncio()
async def test_int09_extension_definition_limitative_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="voertuig",
        text="voertuig: zoals auto, motorfiets of brommer",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "INT-09" for v in res.get("violations", [])), res


@pytest.mark.asyncio()
async def test_int10_no_hidden_background_knowledge_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="instantie",
        text="instantie: zie definitie in het beleidsdocument X",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "INT-10" for v in res.get("violations", [])), res
