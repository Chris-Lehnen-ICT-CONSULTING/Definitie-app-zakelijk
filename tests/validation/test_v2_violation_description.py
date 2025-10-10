import pytest

from services.validation.modular_validation_service import \
    ModularValidationService
from toetsregels.manager import get_toetsregel_manager


@pytest.mark.asyncio()
async def test_violations_include_description_field():
    """V2 violations should mirror 'message' into 'description' for UI."""
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="maatregel",
        text="is een corrigerende actie opgelegd …",  # triggers STR-01
        ontologische_categorie=None,
        context={},
    )
    vlist = res.get("violations", [])
    assert vlist, "Expected at least one violation"
    # Find any violation with a message
    with_msg = next((v for v in vlist if v.get("message")), None)
    assert with_msg is not None, f"Expected a violation with message, got: {vlist}"
    assert "description" in with_msg, "description field missing in violation"
    assert (
        with_msg["description"] == with_msg["message"]
    ), "description should mirror message"
