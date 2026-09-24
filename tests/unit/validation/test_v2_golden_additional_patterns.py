import pytest

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]


@pytest.mark.asyncio
async def test_con01_has_no_meta_phrase_heuristic_anymore():
    """DEF-622 (B-04): geen automatische afkeur op meta-contextfrasen.

    Vóór DEF-622 vuurde CON-01 op `binnen de context van`, `strafrecht` en
    `OM` uit een vaste lijst. Nu tellen alleen de werkelijk geselecteerde
    contextwaarden: met een context die geen van deze woorden bevat, voldoet
    de definitie — ook al staat die frase erin.
    """
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = "registratie: het vastleggen van gegevens binnen de context van het strafrecht bij het OM"
    res = await svc.validate_definition(
        begrip="registratie",
        text=text,
        ontologische_categorie=None,
        context={"organisatorische_context": ["Stichting Zilver"]},
    )
    assert res["rule_statuses"]["CON-01"] == "pass", res["rule_statuses"]
    assert not any(v.get("code") == "CON-01" for v in res.get("violations", [])), res


@pytest.mark.asyncio
async def test_additional_patterns_ess01_detects_goal_phrases():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = "maatregel: is bedoeld om naleving af te dwingen"
    res = await svc.validate_definition(
        begrip="maatregel",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    # ESS-01 is sinds DEF-624 een oordeelregel: de doelfrase is een signaal
    # voor de reviewer, geen bewijs. Valt het signaal weg, dan faalt deze
    # test alsnog — de assertie is verschoven, niet verzwakt.
    review = {r["rule_id"]: r for r in res.get("review_required", [])}
    assert "ESS-01" in review, res
    assert review["ESS-01"]["signals"], review
    assert "ESS-01" not in res.get("passed_rules", []), res
    assert not any(v.get("code") == "ESS-01" for v in res.get("violations", [])), res


@pytest.mark.asyncio
async def test_additional_patterns_int01_detects_multi_sentence():
    # DEF-770: INT-01 staat niet meer in additional_patterns; de tweede zin
    # wordt nu door de sentence_boundary-evaluator gevonden. De naam van deze
    # test is historisch, de verwachting (tweede zin faalt) blijft.
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = (
        "transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken. "
        "In tegenstelling tot andere eisen vertegenwoordigen transitie-eisen tijdelijke behoeften."
    )
    res = await svc.validate_definition(
        begrip="transitie-eis",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "INT-01" for v in res.get("violations", [])), res


@pytest.mark.asyncio
async def test_additional_patterns_str02_detects_vague_terms():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = "termijn: proces."
    res = await svc.validate_definition(
        begrip="termijn",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "STR-02" for v in res.get("violations", [])), res
