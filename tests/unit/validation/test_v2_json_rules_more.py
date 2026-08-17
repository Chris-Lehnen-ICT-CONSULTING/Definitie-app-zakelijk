import pytest

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]


@pytest.mark.asyncio
async def test_str01_starts_with_forbidden_word():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="maatregel",
        text="is een corrigerende actie opgelegd …",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "STR-01" for v in res.get("violations", []))


@pytest.mark.asyncio
async def test_int06_no_explanations_in_definition():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="model",
        text="model: representatie, bijvoorbeeld UML …",
        ontologische_categorie=None,
        context={},
    )
    # INT-06 is sinds DEF-624 een oordeelregel; de toelichtingsmarker is een
    # reviewersignaal, geen bewijs dat definitie en toelichting vermengd zijn.
    review = {r["rule_id"]: r for r in res.get("review_required", [])}
    assert "INT-06" in review, res
    assert review["INT-06"]["signals"], review
    assert "INT-06" not in res.get("passed_rules", []), res
    assert not any(v.get("code") == "INT-06" for v in res.get("violations", [])), res


@pytest.mark.asyncio
async def test_arai04_modals_forbidden():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="proces",
        text="… moet uitgevoerd worden door …",
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "ARAI-04" for v in res.get("violations", []))


@pytest.mark.asyncio
async def test_sam01_misleading_qualifier():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="proces",
        text="juridisch proces: …",
        ontologische_categorie=None,
        context={},
    )
    # SAM-01 vergt de begrippenverzameling: zonder repository valt er niets
    # te beoordelen, dus not_evaluated in plaats van een stille pass. Dat
    # gedrag is voor alle repositoryregels gedekt in
    # tests/unit/validation/test_rule_runtime_matrix.py::TestRepositoryregelsZonderRepository.
    # Het reviewgedrag mét repository is in `main` nog niet gedekt; die
    # dekking komt met Batch 2 via DEF-623.
    assert res.get("rule_statuses", {}).get("SAM-01") == "not_evaluated", res
    assert "SAM-01" not in res.get("passed_rules", []), res


@pytest.mark.asyncio
async def test_str03_not_just_synonym():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="evaluatie",
        text="beoordeling",
        ontologische_categorie=None,
        context={},
    )
    # STR-03 is sinds DEF-624 een oordeelregel: of een definitie meer is dan
    # een synoniem vergt een semantisch oordeel.
    review = {r["rule_id"]: r for r in res.get("review_required", [])}
    assert "STR-03" in review, res
    assert "STR-03" not in res.get("passed_rules", []), res
    assert not any(v.get("code") == "STR-03" for v in res.get("violations", [])), res
    # DEF-670 (bevinding 7): deze test miste als enige van zijn zusters de
    # signals-assertie. Zonder haar toetst hij alleen dat STR-03 op review
    # staat, niet dat de reviewer een aanwijzing krijgt — hier: dat de
    # definitie uit één enkel woord bestaat.
    assert review["STR-03"]["signals"], review


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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
