import pytest

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]


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
    """ESS-04 is een oordeelregel, maar de signalen moeten wél onderscheiden.

    DEF-670 (review PR #397, bevinding 7): deze test was invoer-onafhankelijk
    geworden. Hij asserteerde voor beide teksten alleen "geen violation" en
    "niet in passed_rules" — beide waar voor élke invoer, ook met de teksten
    verwisseld. Wat de reviewer moet zien is het verschil: bij een toetsbaar
    element vuurt een signaal, bij een vage tekst niet. Dát is wat ESS-04
    vandaag daadwerkelijk oplevert, en het faalt zodra de signaalopbouw stukgaat.
    """
    svc = ModularValidationService(get_toetsregel_manager(), None, None)

    res_ok = await svc.validate_definition(
        begrip="termijn",
        text="termijn: periode binnen 7 dagen waarbinnen een handeling moet plaatsvinden",
        ontologische_categorie=None,
        context={},
    )
    review_ok = {r["rule_id"]: r for r in res_ok.get("review_required", [])}
    assert "ESS-04" in review_ok, res_ok
    assert "ESS-04" not in res_ok.get("passed_rules", []), res_ok
    assert not any(
        v.get("code") == "ESS-04" for v in res_ok.get("violations", [])
    ), res_ok
    assert review_ok["ESS-04"]["signals"], (
        "een toetsbaar element (binnen 7 dagen) levert geen enkel signaal op — "
        "de reviewer krijgt dan geen aanwijzing waar te kijken"
    )

    res_bad = await svc.validate_definition(
        begrip="termijn",
        text="termijn: periode waarin iets gebeurt",
        ontologische_categorie=None,
        context={},
    )
    review_bad = {r["rule_id"]: r for r in res_bad.get("review_required", [])}
    assert "ESS-04" in review_bad, res_bad
    assert "ESS-04" not in res_bad.get("passed_rules", []), res_bad
    assert not any(
        v.get("code") == "ESS-04" for v in res_bad.get("violations", [])
    ), res_bad
    assert not review_bad["ESS-04"]["signals"], (
        f"een tekst zonder toetsbaar element levert tóch signalen: "
        f"{review_bad['ESS-04']['signals']}"
    )

    # De kern: de twee teksten leveren verschillende uitkomsten op. Zou deze
    # assert wegvallen, dan kon de test opnieuw invoer-onafhankelijk worden.
    assert review_ok["ESS-04"]["signals"] != review_bad["ESS-04"]["signals"]


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
