import pytest

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager


@pytest.mark.asyncio()
async def test_arai01_flags_verb_core():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = "begrip: is een systeem dat gegevens verwerkt"
    res = await svc.validate_definition(
        begrip="begrip",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "ARAI-01" for v in res.get("violations", [])), res


@pytest.mark.asyncio()
async def test_arai02_container_without_specificity_fails_and_with_specificity_passes():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)

    bad = "proces ter ondersteuning"
    res_bad = await svc.validate_definition(
        begrip="proces",
        text=bad,
        ontologische_categorie=None,
        context={},
    )
    assert any(
        v.get("code") == "ARAI-02" for v in res_bad.get("violations", [])
    ), res_bad

    ok = "proces dat gegevens verzamelt voor analyse"
    res_ok = await svc.validate_definition(
        begrip="proces",
        text=ok,
        ontologische_categorie=None,
        context={},
    )
    assert not any(
        v.get("code") == "ARAI-02" for v in res_ok.get("violations", [])
    ), res_ok


@pytest.mark.asyncio()
async def test_arai03_subjective_adjectives_flagged():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = "maatregel: adequaat en relevant systeem voor gegevensuitwisseling"
    res = await svc.validate_definition(
        begrip="maatregel",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    assert any(v.get("code") == "ARAI-03" for v in res.get("violations", [])), res


@pytest.mark.asyncio()
async def test_str01_body_start_detects_verb_via_arai01():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    # FOUT: start met hulpwoord na ':' (valt onder ARAI-01 verb-kern detectie)
    bad = "term: is een proces"
    res_bad = await svc.validate_definition(
        begrip="term",
        text=bad,
        ontologische_categorie=None,
        context={},
    )
    assert any(
        v.get("code") == "ARAI-01" for v in res_bad.get("violations", [])
    ), res_bad

    # GOED: start met zelfstandig naamwoord na ':'
    ok = "term: proces waarmee gegevens worden verwerkt"
    res_ok = await svc.validate_definition(
        begrip="term",
        text=ok,
        ontologische_categorie=None,
        context={},
    )
    assert not any(
        v.get("code") == "ARAI-01" for v in res_ok.get("violations", [])
    ), res_ok
