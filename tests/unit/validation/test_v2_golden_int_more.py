import pytest

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]


@pytest.mark.asyncio
async def test_int02_decision_rule_signal_is_review_required():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="toegang",
        text="Toegang: toestemming verleend door een bevoegde autoriteit, indien alle voorwaarden zijn vervuld.",
        ontologische_categorie=None,
        # DEF-771: zonder context is INT-02 niet uitgevoerd; synthetische
        # context laat de open menselijke beoordeling werkelijk draaien.
        context={"organisatorische_context": ["Synthetische Organisatie"]},
    )
    # INT-02 is sinds DEF-624 een oordeelregel; het voorwaardelijke patroon
    # is een reviewersignaal, geen bewijs van een beslisregel. Of "indien"
    # een criterium of een voorschrift is, hangt af van de functie (C24).
    assert res["rule_statuses"]["INT-02"] == "review_required", res
    review = {r["rule_id"]: r for r in res.get("review_required", [])}
    assert "INT-02" in review, res
    assert review["INT-02"]["signals"], review
    assert "INT-02" not in res.get("passed_rules", []), res
    assert not any(v.get("code") == "INT-02" for v in res.get("violations", [])), res


@pytest.mark.asyncio
async def test_int08_positive_formulation_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="bevoegd persoon",
        text="bevoegd persoon: iemand die niet onbevoegd is",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "INT-08" for v in res.get("violations", [])), res


@pytest.mark.asyncio
async def test_int09_extension_definition_limitative_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="voertuig",
        text="voertuig: zoals auto, motorfiets of brommer",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "INT-09" for v in res.get("violations", [])), res


@pytest.mark.asyncio
async def test_int10_no_hidden_background_knowledge_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="instantie",
        text="instantie: zie definitie in het beleidsdocument X",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "INT-10" for v in res.get("violations", [])), res
