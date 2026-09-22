import pytest

from services.validation.modular_validation_service import ModularValidationService
from tests.fixtures.def766_fakes import BINDING, bouw_ess03_beoordeling
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]


@pytest.mark.asyncio
async def test_ess03_woordtreffer_geeft_geen_automatische_pass_of_fail():
    """ESS-03 oordeelt sinds DEF-766 op de AI-beoordeling, nooit op woorden.

    Vóór DEF-766 was 'VIN: unieke code …' een automatische pass en
    'aanduiding van een ding' een automatische fail — puur op woorden. Nu
    is ESS-03 zonder voorbereide beoordeling voor béide teksten expliciet
    niet beoordeeld (`review_required`, geen violation, geen pass, met de
    reden "niet uitgevoerd"), en verandert alleen een aan de kandidaat
    gebonden beoordeling de uitkomst — niet de aanwezigheid van een code- of
    uniciteitswoord. Zonder dat verschil zou deze test invoer-onafhankelijk
    zijn (DEF-670-les): daarom keurt de gebonden beoordeling de claimtekst
    juist áf terwijl de tekst zonder claim open blijft.
    """
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    tekst_claim = "VIN: unieke code die een voertuig identificeert"

    res_claim = await svc.validate_definition(
        begrip="voertuigidentificatie",
        text=tekst_claim,
        ontologische_categorie=None,
        context={},
    )
    assert res_claim["rule_statuses"]["ESS-03"] == "review_required", res_claim
    assert "ESS-03" not in res_claim.get("passed_rules", []), res_claim
    assert not any(
        v.get("code") == "ESS-03" for v in res_claim.get("violations", [])
    ), res_claim
    detail_claim = res_claim["rule_results"]["ESS-03"]
    assert "niet uitgevoerd" in detail_claim["parts"][0]["reason"].lower()

    res_zonder = await svc.validate_definition(
        begrip="identificatie",
        text="identificatie: aanduiding van een ding",
        ontologische_categorie=None,
        context={},
    )
    assert res_zonder["rule_statuses"]["ESS-03"] == "review_required", res_zonder
    assert "ESS-03" not in res_zonder.get("passed_rules", []), res_zonder
    assert not any(
        v.get("code") == "ESS-03" for v in res_zonder.get("violations", [])
    ), res_zonder

    # De kern: alleen een aan exact deze kandidaat gebonden beoordeling
    # verandert de uitkomst — hier een afkeur van de codeclaim (het woord
    # 'unieke' bewijst niets), zichtbaar maar niet blokkerend.
    beoordeling = bouw_ess03_beoordeling(
        "voertuigidentificatie",
        tekst_claim,
        {},
        None,
        scenario="fail",
        reden="De code wordt genoemd, maar populatie en geldigheid zijn niet onderbouwd.",
    )
    # Correctieronde 1 (R1): zonder actuele beoordelingsbinding (prompt, norm,
    # provider, model — door de wrapper meegegeven) geldt een meegegeven
    # beoordeling niet als actueel: expliciet niet beoordeeld, geen fail.
    res_zonder_binding = await svc.validate_definition(
        begrip="voertuigidentificatie",
        text=tekst_claim,
        ontologische_categorie=None,
        context={"ess03_assessment": beoordeling},
    )
    assert res_zonder_binding["rule_statuses"]["ESS-03"] == "review_required"
    assert not any(
        v.get("code") == "ESS-03" for v in res_zonder_binding.get("violations", [])
    )
    res_beoordeeld = await svc.validate_definition(
        begrip="voertuigidentificatie",
        text=tekst_claim,
        ontologische_categorie=None,
        context={"ess03_assessment": beoordeling, "ess03_binding": BINDING.als_dict()},
    )
    assert res_beoordeeld["rule_statuses"]["ESS-03"] == "fail"
    [violation] = [v for v in res_beoordeeld["violations"] if v.get("code") == "ESS-03"]
    assert violation["severity"] == "warning"
    assert (
        res_beoordeeld["rule_statuses"]["ESS-03"]
        != res_zonder["rule_statuses"]["ESS-03"]
    )


@pytest.mark.asyncio
async def test_ess04_testable_element_pass_and_fail():
    """ESS-04 is een oordeelregel, maar de signalen moeten wél onderscheiden.

    DEF-670 (review PR #397, bevinding 7): deze test was invoer-onafhankelijk
    geworden. Hij asserteerde voor beide teksten alleen "geen violation" en
    "niet in passed_rules" — beide waar voor élke invoer, ook met de teksten
    verwisseld. Wat de reviewer moet zien is het verschil: bij een toetsbaar
    element vuurt een signaal, bij een vage tekst niet. Dát is wat ESS-04
    vandaag daadwerkelijk oplevert, en het faalt zodra de signaalopbouw stukgaat.
    """
    svc = ModularValidationService(get_toetsregel_manager(), None, None)

    res_ok = await svc.validate_definition(
        begrip="termijn",
        text="termijn: periode binnen 7 dagen waarbinnen een handeling moet plaatsvinden",
        ontologische_categorie=None,
        context={},
    )
    review_ok = {r["rule_id"]: r for r in res_ok.get("review_required", [])}
    assert "ESS-04" in review_ok, res_ok
    assert "ESS-04" not in res_ok.get("passed_rules", []), res_ok
    assert not any(
        v.get("code") == "ESS-04" for v in res_ok.get("violations", [])
    ), res_ok
    assert review_ok["ESS-04"]["signals"], (
        "een toetsbaar element (binnen 7 dagen) levert geen enkel signaal op — "
        "de reviewer krijgt dan geen aanwijzing waar te kijken"
    )

    res_bad = await svc.validate_definition(
        begrip="termijn",
        text="termijn: periode waarin iets gebeurt",
        ontologische_categorie=None,
        context={},
    )
    review_bad = {r["rule_id"]: r for r in res_bad.get("review_required", [])}
    assert "ESS-04" in review_bad, res_bad
    assert "ESS-04" not in res_bad.get("passed_rules", []), res_bad
    assert not any(
        v.get("code") == "ESS-04" for v in res_bad.get("violations", [])
    ), res_bad
    assert not review_bad["ESS-04"]["signals"], (
        f"een tekst zonder toetsbaar element levert tóch signalen: "
        f"{review_bad['ESS-04']['signals']}"
    )

    # De kern: de twee teksten leveren verschillende uitkomsten op. Zou deze
    # assert wegvallen, dan kon de test opnieuw invoer-onafhankelijk worden.
    assert review_ok["ESS-04"]["signals"] != review_bad["ESS-04"]["signals"]


@pytest.mark.asyncio
async def test_ess05_distinguishing_feature_pass_and_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)

    res_ok = await svc.validate_definition(
        begrip="speciaal kenmerk",
        text="eigenschap die een entiteit onderscheidt van andere entiteiten",
        ontologische_categorie=None,
        context={},
    )
    assert not any(
        v.get("code") == "ESS-05" for v in res_ok.get("violations", [])
    ), res_ok

    res_bad = await svc.validate_definition(
        begrip="kenmerk",
        text="een entiteit die in situaties voorkomt",
        ontologische_categorie=None,
        context={},
    )
    assert any(
        v.get("code") == "ESS-05" for v in res_bad.get("violations", [])
    ), res_bad
