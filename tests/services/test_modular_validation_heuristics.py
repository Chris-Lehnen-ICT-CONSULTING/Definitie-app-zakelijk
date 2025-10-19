import pytest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_informal_language_violation_blocks_acceptance():
    from services.validation.modular_validation_service import ModularValidationService

    svc = ModularValidationService()
    begrip = "computer"
    text = "Zo'n ding waar je van alles mee kunt, zoals internetten en spelletjes spelen enzo."

    res = await svc.validate_definition(begrip, text)
    codes = [v.get("code") for v in res.get("violations", [])]
    assert "LANG-INF-001" in codes
    assert res["is_acceptable"] is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mixed_language_violation_blocks_acceptance():
    from services.validation.modular_validation_service import ModularValidationService

    svc = ModularValidationService()
    begrip = "framework"
    text = "Een software framework dat developers gebruiken volgens best practices om applicaties te builden."

    res = await svc.validate_definition(begrip, text)
    codes = [v.get("code") for v in res.get("violations", [])]
    assert "LANG-MIX-001" in codes
    assert res["is_acceptable"] is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_too_minimal_structure_violation_blocks_acceptance():
    from services.validation.modular_validation_service import ModularValidationService

    svc = ModularValidationService()
    begrip = "test"
    text = "Een test definitie."

    res = await svc.validate_definition(begrip, text)
    codes = [v.get("code") for v in res.get("violations", [])]
    assert "STR-FORM-001" in codes
    assert res["is_acceptable"] is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_soft_accept_minimal_ok_without_blocking_errors():
    from services.validation.modular_validation_service import ModularValidationService

    svc = ModularValidationService()
    begrip = "databank"
    text = "Een gestructureerde verzameling van gegevens die elektronisch worden opgeslagen."

    res = await svc.validate_definition(begrip, text)
    # Geen blocking errors (LANG-/CON-CIRC-/VAL-EMP-/VAL-LEN-002-/STR-FORM)
    codes = [v.get("code") for v in res.get("violations", [])]
    assert not any(
        c
        and (
            c.startswith(("LANG-", "CON-CIRC", "VAL-EMP", "VAL-LEN-002")) or c == "STR-FORM-001"
        )
        for c in codes
    )
    # Overall kan onder 0.75 liggen, maar boven soft-floor => acceptabel
    assert res["is_acceptable"] is True
