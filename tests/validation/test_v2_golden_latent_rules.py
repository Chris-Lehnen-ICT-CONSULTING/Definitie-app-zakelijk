import pytest

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager


@pytest.mark.asyncio()
async def test_sam02_qualification_no_repetition_should_flag_conflict():
    """Golden (latent): SAM-02 should flag repetition/conflict, not yet enforced in V2."""
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = (
        "delict: delict dat binnen de grenzen van een wettelijke strafbepaling valt en "
        "waarvoor de politie voldoende bewijs heeft voor veroordeling"
    )
    res = await svc.validate_definition(
        begrip="opgehelderd delict",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "SAM-02" for v in res.get("violations", []))


@pytest.mark.asyncio()
async def test_sam04_compound_head_mismatch_should_fail():
    """Golden (latent): SAM-04 composition must start with specialising component."""
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = "procesmodel: weergave, meestal als diagram, van een proces"
    res = await svc.validate_definition(
        begrip="procesmodel",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "SAM-04" for v in res.get("violations", []))
