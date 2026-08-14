import pytest

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]


@pytest.mark.asyncio
async def test_str04_kickoff_requires_narrowing_pass_and_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)

    # PASS: kick-off followed by narrowing
    res_ok = await svc.validate_definition(
        begrip="proces",
        text="proces dat gegevens verzamelt voor analyse",
        ontologische_categorie=None,
        context={},
    )
    assert not any(
        v.get("code") == "STR-04" for v in res_ok.get("violations", [])
    ), res_ok

    # FAIL: too generic kickoff
    res_bad = await svc.validate_definition(
        begrip="proces",
        text="proces.",
        ontologische_categorie=None,
        context={},
    )
    assert any(
        v.get("code") == "STR-04" for v in res_bad.get("violations", [])
    ), res_bad


@pytest.mark.asyncio
async def test_str05_definition_not_construction_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="motorvoertuig",
        text="motorvoertuig: bestaat uit een chassis, vier wielen en een motor",
        ontologische_categorie=None,
        context={},
    )
    review = {r["rule_id"]: r for r in res.get("review_required", [])}
    assert "STR-05" in review, res
    # Het patroon blijft een signaal voor de reviewer; valt dat weg, dan is de
    # detectie stilletjes kapot en moet deze test dat merken.
    assert review["STR-05"]["signals"], review
    assert "STR-05" not in res.get("passed_rules", []), res
    assert not any(v.get("code") == "STR-05" for v in res.get("violations", [])), res


@pytest.mark.asyncio
async def test_str06_essence_not_goal_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="beveiligingsmaatregel",
        text="beveiligingsmaatregel: voorziening om te voorkomen dat ongeautoriseerde toegang optreedt",
        ontologische_categorie=None,
        context={},
    )
    # STR-06 is sinds DEF-624 een oordeelregel; de doelmarkers zijn een
    # reviewersignaal en delen hun patronen met ESS-01.
    review = {r["rule_id"]: r for r in res.get("review_required", [])}
    assert "STR-06" in review, res
    assert review["STR-06"]["signals"], review
    assert "STR-06" not in res.get("passed_rules", []), res
    assert not any(v.get("code") == "STR-06" for v in res.get("violations", [])), res


@pytest.mark.asyncio
async def test_str07_double_negation_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="beveiliging",
        text="Beveiliging: maatregelen die niet zonder toezicht kunnen werken",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "STR-07" for v in res.get("violations", [])), res


@pytest.mark.asyncio
async def test_str08_ambiguous_and_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="toegang",
        text="Het systeem vereist login en verificatie",
        ontologische_categorie=None,
        context={},
    )
    review = {r["rule_id"]: r for r in res.get("review_required", [])}
    assert "STR-08" in review, res
    # Het patroon blijft een signaal voor de reviewer; valt dat weg, dan is de
    # detectie stilletjes kapot en moet deze test dat merken.
    assert review["STR-08"]["signals"], review
    assert "STR-08" not in res.get("passed_rules", []), res
    assert not any(v.get("code") == "STR-08" for v in res.get("violations", [])), res


@pytest.mark.asyncio
async def test_str09_ambiguous_or_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="identificatie",
        text="Een persoon met een paspoort of identiteitskaart",
        ontologische_categorie=None,
        context={},
    )
    review = {r["rule_id"]: r for r in res.get("review_required", [])}
    assert "STR-09" in review, res
    # Het patroon blijft een signaal voor de reviewer; valt dat weg, dan is de
    # detectie stilletjes kapot en moet deze test dat merken.
    assert review["STR-09"]["signals"], review
    assert "STR-09" not in res.get("passed_rules", []), res
    assert not any(v.get("code") == "STR-09" for v in res.get("violations", [])), res
