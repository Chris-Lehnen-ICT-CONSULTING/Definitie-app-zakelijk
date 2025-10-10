import pytest

from services.validation.modular_validation_service import \
    ModularValidationService
from toetsregels.manager import get_toetsregel_manager


@pytest.mark.asyncio()
async def test_con01_flags_context_wording_more_generic():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = "maatregel: actie binnen het strafrecht"
    res = await svc.validate_definition(
        begrip="maatregel",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "CON-01" for v in res.get("violations", [])), res


@pytest.mark.asyncio()
async def test_sam01_qualification_word_detected():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = "proces: institutioneel proces binnen de organisatie"
    res = await svc.validate_definition(
        begrip="proces",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "SAM-01" for v in res.get("violations", [])), res


@pytest.mark.asyncio()
async def test_sam03_nested_definition_phrases():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = "procesmodel: zoals gedefinieerd in het proceshandboek"
    res = await svc.validate_definition(
        begrip="procesmodel",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "SAM-03" for v in res.get("violations", [])), res


@pytest.mark.asyncio()
async def test_ver03_infinite_verb_term_required():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = "beoordeelt: handeling waarbij een beoordeling wordt uitgevoerd"
    res = await svc.validate_definition(
        begrip="beoordeelt",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "VER-03" for v in res.get("violations", [])), res
