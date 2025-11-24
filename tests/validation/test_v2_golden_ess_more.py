import pytest

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager


@pytest.mark.asyncio
async def test_ess03_unique_identification_pass_and_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)

    res_ok = await svc.validate_definition(
        begrip="voertuigidentificatie",
        text="VIN: unieke code die een voertuig identificeert",
        ontologische_categorie=None,
        context={},
    )
    assert not any(
        v.get("code") == "ESS-03" for v in res_ok.get("violations", [])
    ), res_ok

    res_bad = await svc.validate_definition(
        begrip="identificatie",
        text="identificatie: aanduiding van een ding",
        ontologische_categorie=None,
        context={},
    )
    assert any(
        v.get("code") == "ESS-03" for v in res_bad.get("violations", [])
    ), res_bad


@pytest.mark.asyncio
async def test_ess04_testable_element_pass_and_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)

    res_ok = await svc.validate_definition(
        begrip="termijn",
        text="termijn: periode binnen 7 dagen waarbinnen een handeling moet plaatsvinden",
        ontologische_categorie=None,
        context={},
    )
    assert not any(
        v.get("code") == "ESS-04" for v in res_ok.get("violations", [])
    ), res_ok

    res_bad = await svc.validate_definition(
        begrip="termijn",
        text="termijn: periode waarin iets gebeurt",
        ontologische_categorie=None,
        context={},
    )
    assert any(
        v.get("code") == "ESS-04" for v in res_bad.get("violations", [])
    ), res_bad


@pytest.mark.asyncio
async def test_ess05_distinguishing_feature_pass_and_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)

    res_ok = await svc.validate_definition(
        begrip="speciaal kenmerk",
        text="eigenschap die een entiteit onderscheidt van andere entiteiten",
        ontologische_categorie=None,
        context={},
    )
    assert not any(
        v.get("code") == "ESS-05" for v in res_ok.get("violations", [])
    ), res_ok

    res_bad = await svc.validate_definition(
        begrip="kenmerk",
        text="een entiteit die in situaties voorkomt",
        ontologische_categorie=None,
        context={},
    )
    assert any(
        v.get("code") == "ESS-05" for v in res_bad.get("violations", [])
    ), res_bad
