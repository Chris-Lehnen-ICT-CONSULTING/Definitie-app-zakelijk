import pytest

from services.validation.modular_validation_service import \
    ModularValidationService
from toetsregels.manager import get_toetsregel_manager


@pytest.mark.asyncio()
async def test_additional_patterns_con01_detects_context_wording():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = "registratie: het vastleggen van gegevens binnen de context van het strafrecht bij het OM"
    res = await svc.validate_definition(
        begrip="registratie",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "CON-01" for v in res.get("violations", [])), res


@pytest.mark.asyncio()
async def test_additional_patterns_ess01_detects_goal_phrases():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = "maatregel: is bedoeld om naleving af te dwingen"
    res = await svc.validate_definition(
        begrip="maatregel",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "ESS-01" for v in res.get("violations", [])), res


@pytest.mark.asyncio()
async def test_additional_patterns_int01_detects_multi_sentence():
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


@pytest.mark.asyncio()
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
