import pytest

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager


@pytest.mark.asyncio()
async def test_ver02_definition_in_singular_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="gegevens",
        text="gegevens zijn feiten en getallen die zijn verzameld voor analyse",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "VER-02" for v in res.get("violations", [])), res


@pytest.mark.asyncio()
async def test_ver03_infinitive_for_verb_term_pass_and_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)

    # FAIL: vervoegde vorm in term/tekst
    res_bad = await svc.validate_definition(
        begrip="beoordeelt",
        text="beoordeelt: handeling waarbij de kwalificatie plaatsvindt",
        ontologische_categorie=None,
        context={},
    )
    assert any(
        v.get("code") == "VER-03" for v in res_bad.get("violations", [])
    ), res_bad

    # PASS: infinitief
    res_ok = await svc.validate_definition(
        begrip="beoordelen",
        text="beoordelen: proces van een oordeel vormen",
        ontologische_categorie=None,
        context={},
    )
    assert not any(
        v.get("code") == "VER-03" for v in res_ok.get("violations", [])
    ), res_ok
