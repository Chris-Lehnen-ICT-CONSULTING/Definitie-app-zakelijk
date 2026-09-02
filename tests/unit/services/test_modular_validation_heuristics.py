import pytest

from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

# DEF-621: de service wordt nu met de echte contractmanager gebouwd.
# Zonder manager laadt zij zeven van drieenvijftig regels; sinds de
# fail-closed guard levert dat `validation_unknown` in plaats van een
# score over die zeven. Deze tests gaan over heuristiekgedrag, niet over
# de guard, dus draaien ze op de volledige regelset.


@pytest.mark.unit
@pytest.mark.asyncio
async def test_informal_language_violation_blocks_acceptance():
    from services.validation.modular_validation_service import ModularValidationService

    svc = ModularValidationService(get_toetsregel_manager(), None, None)
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

    svc = ModularValidationService(get_toetsregel_manager(), None, None)
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

    svc = ModularValidationService(get_toetsregel_manager(), None, None)
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

    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    # DEF-621: de oude databanktekst scoort met de echte 53-regelmanager 0,55
    # en is dan niet acceptabel - die invoer toetst de soft floor dus niet
    # meer. Deze invoer is gemeten op 0,64: onder de drempel van 0,75, zonder
    # blocking error, en juist daardoor via de soft floor acceptabel.
    begrip = "besluit"
    text = "type document met uniek zaaknummer volgens de wet"

    res = await svc.validate_definition(begrip, text)
    # Geen blocking errors (LANG-/CON-CIRC-/VAL-EMP-/VAL-LEN-002-/STR-FORM)
    codes = [v.get("code") for v in res.get("violations", [])]
    assert not any(
        c
        and (
            c.startswith(("LANG-", "CON-CIRC", "VAL-EMP", "VAL-LEN-002"))
            or c == "STR-FORM-001"
        )
        for c in codes
    )
    # De score ligt onder de normale drempel van 0,75; zou hij daarboven
    # liggen, dan bewees de test niets over de soft floor.
    assert 0.60 <= res["overall_score"] < 0.75, res["overall_score"]
    # Overall onder 0.75, maar boven soft-floor => acceptabel
    assert res["is_acceptable"] is True
