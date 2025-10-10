import pytest

from services.validation.modular_validation_service import \
    ModularValidationService
from toetsregels.manager import get_toetsregel_manager


@pytest.mark.asyncio()
async def test_str01_starts_with_forbidden_word():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="maatregel",
        text="is een corrigerende actie opgelegd …",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "STR-01" for v in res.get("violations", []))


@pytest.mark.asyncio()
async def test_int06_no_explanations_in_definition():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="model",
        text="model: representatie, bijvoorbeeld UML …",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "INT-06" for v in res.get("violations", []))


@pytest.mark.asyncio()
async def test_arai04_modals_forbidden():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="proces",
        text="… moet uitgevoerd worden door …",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "ARAI-04" for v in res.get("violations", []))


@pytest.mark.asyncio()
async def test_sam01_misleading_qualifier():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="proces",
        text="juridisch proces: …",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "SAM-01" for v in res.get("violations", []))


@pytest.mark.asyncio()
async def test_str03_not_just_synonym():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="evaluatie",
        text="beoordeling",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "STR-03" for v in res.get("violations", []))


@pytest.mark.asyncio()
async def test_ver01_lemma_plural_triggers():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    # 'gegevens' is meervoud → VER-01 should trigger (not plurale tantum whitelist)
    res = await svc.validate_definition(
        begrip="gegevens",
        text="gegevens: …",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "VER-01" for v in res.get("violations", []))


@pytest.mark.asyncio()
async def test_con02_authentic_source_required():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="maatregel",
        text="maatregel: corrigerende actie …",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "CON-02" for v in res.get("violations", []))

    res_ok = await svc.validate_definition(
        begrip="maatregel",
        text="maatregel: corrigerende actie volgens het Wetboek …",
        ontologische_categorie=None,
        context={},
    )
    assert not any(v.get("code") == "CON-02" for v in res_ok.get("violations", []))
