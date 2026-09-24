"""DEF-770 herstel na T24: zes afwijkingen en hun nabije tegenhangers.

Bron: effectproeven-20260924-v1 (T24-adjudicatie, vaste AI-referenties, nu
ontwikkelmateriaal) en herstelanalyse-v1. De verwachtingen volgen uit die
referenties en de daar vastgelegde generalisaties, niet uit het gedrag van de
implementatie:

- T15 opsomming binnen één kern (na ':' of ';') is geen grens;
- T17 leestekens binnen een ingesloten citaat vormen geen buitenste grens
  (haakjes blijven onzeker);
- T19 een geheel geciteerde kern krijgt altijd het open onderdeel broncitaat;
- T22 een los label met dubbele punt zonder vervolg is onzeker;
- T23 een beletselteken met vervolg is onzeker;
- T24 een punt na een aantoonbaar volledig woord (productief achtervoegsel),
  gevolgd door een zelfstandige zin met kleine beginletter, is alleen een
  zekere grens (fail) als het onderwerp positief herkend is (lidwoordgroep).
  Contract def770-int01/3 (conservatieve-beoordeling-besluit-v1, punt 3): een
  kaal woord plus voorzetselgroep bewijst geen onderwerp. De oude T24-tekst
  houdt haar normatieve fail-label in het historische corpus, maar haar
  automatische dispositie onder /3 is onzeker (review_required). Zonder
  bewijs — onbekende afkorting ('voorz.'), persoonsvorm direct na de punt,
  geen persoonsvorm — blijft het onzeker; een vals fail is geen herstel.

Nooit een volledige INT-01-pass; compactheid en begrijpelijkheid blijven
apart open; oude opgeslagen uitkomsten gelden na de semantische wijziging
niet meer als actueel (contractversie).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)
from domain.int01.opslag import (
    bouw_beoordeling,
    lees_beoordeling,
    met_nieuwe_beoordeling,
    weergavedetail,
)
from domain.int01.zinsgrenzen import CONTRACTVERSIE, regeluitkomst, segmenteer
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

T15 = "pakket met uitsluitend:\n- een routeblad;\n- een telkaart;\n- een blanco verslagvel."
T17 = "code die de melding 'Gereed. Neem de bak mee.' op het oefenscherm laat verschijnen."
T19 = "“strook langs een proefwand die tijdens de meting onbelicht blijft.”"
T22 = "Oefenstatus:"
T23 = "onderbreking van de geluidsproef... daarna opnieuw luisteren"
T24 = "strook voor tijdelijke bundeling. controle volgens zqv. blijft vereist"
#: Gewone duidelijke grens (punt + hoofdletter): blijft zekere fail onder /3.
ZEKER_FAIL = "strook voor tijdelijke bundeling. De controle blijft vereist."

# (id, tekst, zekere grenzen, onzekere grenzen)
GEVALLEN = [
    # T15 en tegenhangers
    ("T15-opsomming-na-dubbele-punt", T15, 0, 0),
    ("lijst-hoofdletters", "pakket met:\n- Een routeblad;\n- Een telkaart.", 0, 0),
    ("opsomming-na-komma", "pakket met een routeblad,\n- een telkaart", 0, 0),
    ("lijst-zonder-inleidend-teken", "pakket\n- een routeblad\n- een telkaart", 0, 2),
    ("lijst-tweede-zin", "regels:\n- De houder meldt dit. De dienst beslist.", 1, 0),
    # T17 en tegenhangers
    ("T17-ingesloten-citaat", T17, 0, 0),
    ("citaat-recht", 'code die de melding "Stop. Ga." op het scherm toont.', 0, 0),
    ("citaat-krul", "nota met de titel “Beleid. Uitvoering” van de minister.", 0, 0),
    ("zin-na-citaat", "code die de melding 'Gereed.' toont. Neem de bak mee.", 1, 0),
    ("punt-binnen-haakjes", "code (Gereed. Neem mee) op het scherm.", 0, 1),
    # T19 en tegenhanger
    ("T19-geheel-geciteerd", T19, 0, 0),
    ("deels-geciteerd", "strook “langs een wand” die onbelicht blijft.", 0, 0),
    # T22 en tegenhangers
    ("T22-los-label", T22, 0, 1),
    ("label-met-inhoud", "Oefenstatus: actief", 0, 0),
    ("inleiding-zonder-vervolg", "pakket met uitsluitend:", 0, 1),
    # T23 en tegenhangers
    ("T23-beletselteken-vervolg", T23, 0, 1),
    ("beletselteken-aan-einde", "onderbreking van de geluidsproef...", 0, 0),
    ("beletselteken-hoofdletter", "onderbreking... Daarna opnieuw luisteren", 0, 1),
    ("beletselteken-in-citaat", "melding 'wacht ... daarna' op het scherm.", 0, 0),
    # T24 en tegenhangers. Zeker alleen na een aantoonbaar volledig woord
    # (productief achtervoegsel, geen lengte-/klinkerheuristiek) én een vervolg
    # met positief herkend onderwerp; anders blijft twijfel zichtbaar.
    # Besluit /3 punt 3: T24 automatisch onzeker (normatief label blijft fail).
    ("T24-automatisch-onzeker-onder-3", T24, 0, 2),
    # Uitwerking-v2 (conservatief /3): punt + kleine letter nooit automatisch
    # zeker, ook niet na volledig woord en lidwoordgroep. Was zeker onder /2.
    ("ingen-meervoud", "strook voor bundelingen. de controle blijft vereist", 0, 1),
    ("heid-woord", "zorg voor de veiligheid. het toezicht is vereist", 0, 1),
    # Onbekende afkorting binnen één formulering: persoonsvorm direct na de punt.
    ("voorz-persoonsvorm", "bericht dat door de voorz. wordt ondertekend", 0, 1),
    # Zelfde afkorting, vervolg met eigen onderwerp: lexicaal niet te scheiden
    # van T24 zonder woordenboek, dus onzeker (geen vals fail).
    ("voorz-met-onderwerp", "strook voor de voorz. controle blijft vereist", 0, 1),
    ("ing-pv-vooraan", "bericht dat door de vergadering. wordt ondertekend", 0, 1),
    # Volledig woord zonder herkenbaar achtervoegsel: conservatief onzeker.
    ("kleine-letter-met-persoonsvorm", "Afgebakend object. heeft vaste vorm.", 0, 1),
    ("zonder-suffix", "strook langs een proefwand. controle blijft vereist", 0, 1),
    ("zonder-persoonsvorm", "strook voor bundeling. controle volgens protocol", 0, 1),
    ("afd-met-onderwerp", "strook voor de afd. controle blijft vereist", 0, 1),
    ("gebiedende-wijs", "onderdeel van de regeling. zie ook de bijlage", 0, 1),
    ("bekende-afkorting", "maatregel zoals bijv. een boete die geldt.", 0, 0),
    ("gestippelde-afkorting", "register met o.a. gegevens die worden bewaard.", 0, 0),
    # Review R1: een werkwoordtoken bewijst geen zelfstandige zin. Infinitief-
    # constructie, bijzin en voorzetselvervolg blijven onzeker; alleen een
    # vervolg dat met een onderwerp begint, draagt de zekere grens.
    ("r1-om-te-infinitief", "regeling. om te worden toegepast", 0, 1),
    ("r1-bijzin-die", "regeling. die kan worden toegepast", 0, 1),
    ("r1-voorzetsel", "regeling. zonder de verplichting die blijft gelden", 0, 1),
    ("r1-relatief-voor-pv", "regeling. controle die blijft vereist", 0, 1),
    ("r1-onderwerp-lidwoord", "regeling. de controle blijft vereist", 0, 1),
    # Review R2: een slotteken direct vóór het sluitende aanhalingsteken kan
    # ook de buitenste zin afsluiten; zonder duidelijke voortzetting onzeker.
    ("r2-zelfstandig", "code met de melding “Gereed.” controle blijft vereist", 0, 1),
    ("r2-hoofdletter", "code met de melding “Gereed.” Controle blijft vereist", 0, 1),
    ("r2-onbeslist", "code met de melding “Gereed.” controle volgens protocol", 0, 1),
    ("r2-citaat-voortzetting", "code die de melding “Gereed.” toont", 0, 0),
    ("r2-citaat-voorzetsel", "code met de melding “Gereed.” op het scherm", 0, 0),
    ("r2-intern-citaatteken", "code met de melding “Stop. Ga” op het scherm", 0, 0),
    # Correctiereview R1: zeker alleen met een ondubbelzinnige persoonsvorm
    # (geen infinitief-homograaf), met een aanvulling erna en zonder
    # werkwoordelijke vorm ervoor. Anders onzeker.
    ("r3-deelwoord-worden", "regeling. toegepast worden", 0, 1),
    ("r3-bijwoord-worden", "regeling. uitsluitend worden toegepast", 0, 1),
    ("r3-meervoud-ambigu", "regeling. controles kunnen volgen", 0, 1),
    ("r3-deelwoord-wordt", "regeling. uitsluitend wordt toegepast", 0, 1),
    ("r3-pv-achteraan", "regeling. controle nodig is", 0, 1),
    ("r3-verleden-meervoud", "regeling. de controles werden uitgevoerd", 0, 1),
    # r4: een kaal woord direct vóór de persoonsvorm is geen bewezen onderwerp
    # (was in r3 nog zeker); zie herstelanalyse-v5.
    ("r4-kaal-woord-voor-pv", "regeling. toezicht is vereist", 0, 1),
    # Correctiereview R2: een citaatafsluiting is alleen één formulering bij een
    # aantoonbare voortzetting; onbekende syntaxis blijft onzeker.
    (
        "r3-citaat-inversie",
        "code met de melding “Gereed.” voor gebruik is controle vereist",
        0,
        1,
    ),
    (
        "r3-bijzin-al-met-werkwoord",
        "code die eindigt met de melding “Gereed.” de controle volgt later",
        0,
        1,
    ),
    (
        "r3-open-bijzin-nieuwe-woordgroep",
        "code die de melding “Gereed.” de controle volgt later",
        0,
        1,
    ),
    (
        "r3-open-bijzin-met-persoonsvorm",
        "code die de melding “Gereed.” voor gebruik is controle vereist",
        0,
        1,
    ),
    ("r3-citaat-lange-pp", "code met de melding “Gereed.” op het grote scherm", 0, 1),
    ("r3-citaat-korte-pp", "melding “Gereed.” van de dienst", 0, 0),
    # Correctiereview v2, R1: het onderwerp moet positief herkend zijn — onder
    # /3 alleen een lidwoordgroep. Een bijwoord, ander kaal woord of kaal woord
    # plus voorzetselgroep vóór de persoonsvorm bewijst dat niet (besluit punt 3).
    ("r4-bijwoord-opnieuw", "regeling. opnieuw wordt toegepast", 0, 1),
    ("r4-bijwoord-nog", "regeling. nog wordt toegepast", 0, 1),
    ("r4-bijwoord-daarna", "regeling. daarna wordt controle uitgevoerd", 0, 1),
    ("r4-lidwoordgroep", "regeling. de controle blijft vereist", 0, 1),
    # Astra-conservatief-review-v1 R1: lidwoordgroep kan tijdsbepaling zijn.
    ("c4-tijdsbepaling-de", "regeling. de hele dag wordt toegepast", 0, 1),
    ("c4-tijdsbepaling-elke", "regeling. elke dag wordt toegepast", 0, 1),
    ("c4-tijdsbepaling-deze", "regeling. deze week wordt toegepast", 0, 1),
    # Duidelijke hoofdlettergrens blijft zekere fail; ononderbroken blijft één.
    ("c4-hoofdletter-fail", "regeling. De controle blijft vereist.", 1, 0),
    ("c4-ononderbroken", "regeling die elke dag wordt toegepast", 0, 0),
    ("c3-woord-met-pp", "regeling. toezicht op naleving is vereist", 0, 1),
    ("c3-bijwoord-met-pp", "regeling. opnieuw volgens protocol wordt toegepast", 0, 1),
    ("c3-lidwoord-met-pp", "regeling. de controle volgens zqv. blijft vereist", 0, 2),
    ("r4-pp-zonder-object", "regeling. toezicht op is vereist", 0, 1),
    # Correctiereview v2, R2: een open bijzin vóór het citaat is alleen bewezen
    # met markering, lidwoord 'de'/'een' en één woord ('die de melding').
    (
        "r4-bijzin-met-werkwoord",
        "code die meldt “Gereed.” na gebruik volgt controle",
        0,
        1,
    ),
    ("r4-bijzin-voornaamwoord", "code die het meldt “Gereed.” op het scherm", 0, 0),
    ("r4-bijzin-het-vervolg", "code die het meldt “Gereed.” na gebruik volgt", 0, 1),
    ("r4-open-bijzin-pp", "code die de melding “Gereed.” na gebruik toont", 0, 0),
    ("r4-open-bijzin-een", "code die een melding “Gereed.” toont", 0, 0),
    # Correctiereview v2, R3: onvolledige voortzetting na het citaat.
    ("r4-alleen-voorzetsel", "code met de melding “Gereed.” op", 0, 1),
    ("r4-voorzetsel-lidwoord", "code met de melding “Gereed.” op de", 0, 1),
    ("r4-voorzetsel-het", "code met de melding “Gereed.” op het", 0, 1),
    ("r4-geen-woord", "code met de melding “Gereed.” –", 0, 1),
    # Ongewijzigd gedrag rond initialen en afkortingen
    ("initiaal-zonder-naamcontext", "rapport van J. Jansen over detentie.", 0, 1),
    ("titel-initiaal", "rapport van dr. J. Jansen over detentie.", 0, 0),
    ("enz-hoofdletter", "Object met gegevens enz. Het wordt geregistreerd.", 0, 1),
]


@pytest.mark.parametrize(
    ("tekst", "zeker", "onzeker"),
    [pytest.param(t, z, o, id=i) for i, t, z, o in GEVALLEN],
)
def test_segmentatie(tekst, zeker, onzeker):
    seg = segmenteer(tekst)
    assert seg is not None
    assert len(seg.zekere_grenzen) == zeker, seg
    assert len(seg.onzekere_grenzen) == onzeker, seg


def test_t24_onder_contract_3_onzeker_met_passage_en_positie():
    """Besluit /3 punt 3: de normatieve fail blijft in het historische corpus;
    de automatische dispositie is doorverwijzing, met vindbare grens."""
    seg = segmenteer(T24)
    assert not seg.zekere_grenzen
    grens, afkorting = seg.onzekere_grenzen
    assert "bundeling." in grens.passage and "controle" in grens.passage
    assert grens.positie == T24.index("bundeling.") + len("bundeling")
    assert "kleine letter" in grens.grond
    assert "zqv." in afkorting.passage
    uitkomst = regeluitkomst(seg)
    assert uitkomst["status"] == "review_required"
    assert "zinsstructuur" not in _delen(uitkomst)


@pytest.mark.parametrize(
    "tekst",
    [
        "strook voor tijdelijke bundeling. de controle blijft vereist",
        "regeling. de hele dag wordt toegepast",
    ],
)
def test_kleine_letter_na_punt_altijd_onzeker_met_passage_en_positie(tekst):
    """Uitwerking-v2: punt + kleine beginletter krijgt onder /3 nooit een
    automatische zekere uitkomst; de mogelijke grens blijft vindbaar."""
    seg = segmenteer(tekst)
    assert not seg.zekere_grenzen
    [grens] = seg.onzekere_grenzen
    assert tekst[grens.positie] == "."
    assert tekst[grens.positie + 2].islower()
    assert "kleine letter" in grens.grond
    assert regeluitkomst(seg)["status"] == "review_required"


def test_hoofdlettergrens_blijft_zekere_fail():
    seg = segmenteer(ZEKER_FAIL)
    [grens] = seg.zekere_grenzen
    assert grens.positie == ZEKER_FAIL.index("bundeling.") + len("bundeling")
    assert regeluitkomst(seg)["status"] == "fail"


def test_r2_citaatafsluiting_onzeker_met_passage_en_reden():
    seg = segmenteer("code met de melding “Gereed.” controle blijft vereist")
    [grens] = seg.onzekere_grenzen
    assert "Gereed." in grens.passage and "controle" in grens.passage
    assert "citaat" in grens.grond
    assert "zinsstructuur" not in _delen(regeluitkomst(seg))


def test_r3_onbekende_citaatvoortzetting_toont_grens_met_positie():
    tekst = "code met de melding “Gereed.” voor gebruik is controle vereist"
    seg = segmenteer(tekst)
    [grens] = seg.onzekere_grenzen
    assert grens.positie == tekst.index(".”")
    assert "Gereed." in grens.passage and "voor" in grens.passage
    assert "zinsstructuur" not in _delen(regeluitkomst(seg))


@pytest.mark.parametrize(
    "tekst",
    [
        "code met de melding “Gereed.” op",
        "code met de melding “Gereed.” op de",
        "code die meldt “Gereed.” na gebruik volgt controle",
    ],
)
def test_r4_onvolledige_of_onbewezen_voortzetting_met_positie(tekst):
    seg = segmenteer(tekst)
    [grens] = seg.onzekere_grenzen
    assert grens.positie == tekst.index(".”")
    assert "Gereed." in grens.passage


def test_t22_en_t23_passage_en_reden():
    [label] = segmenteer(T22).onzekere_grenzen
    assert "Oefenstatus:" in label.passage
    assert "dubbele punt" in label.grond
    [weglating] = segmenteer(T23).onzekere_grenzen
    assert "geluidsproef..." in weglating.passage and "daarna" in weglating.passage
    assert "beletselteken" in weglating.grond


def _delen(detail: dict) -> dict[str, str]:
    return {p["id"]: p["status"] for p in detail["parts"]}


def test_t19_geheel_citaat_krijgt_broncitaat_ook_bij_een_zin():
    detail = regeluitkomst(segmenteer(T19))
    assert detail["status"] == "review_required"
    assert _delen(detail) == {
        "zinsstructuur": "pass",
        "broncitaat": "review_required",
        "compactheid": "review_required",
        "begrijpelijkheid": "review_required",
    }
    citaat = next(p for p in detail["parts"] if p["id"] == "broncitaat")
    assert "parafrase" in citaat["action"]
    # Deels geciteerd: geen broncitaatonderdeel.
    deels = regeluitkomst(segmenteer("strook “langs een wand” die onbelicht blijft."))
    assert "broncitaat" not in _delen(deels)


# ── Service: beide laadpaden ────────────────────────────────────────────


@pytest.fixture(
    scope="module", params=["toetsregel_manager", "cached_manager (productiepad)"]
)
def svc(request) -> ModularValidationService:
    if request.param.startswith("cached_manager"):
        from toetsregels.cached_manager import get_cached_toetsregel_manager
        from toetsregels.rule_cache import get_rule_cache

        get_rule_cache().clear_cache()
        manager = get_cached_toetsregel_manager()
    else:
        manager = get_toetsregel_manager()
    return ModularValidationService(manager, None, None)


OPEN = {"compactheid": "review_required", "begrijpelijkheid": "review_required"}

# (id, tekst, regelstatus, verwachte onderdelen)
SERVICEGEVALLEN = [
    ("T15", T15, "review_required", {"zinsstructuur": "pass", **OPEN}),
    ("T17", T17, "review_required", {"zinsstructuur": "pass", **OPEN}),
    (
        "T19",
        T19,
        "review_required",
        {"zinsstructuur": "pass", "broncitaat": "review_required", **OPEN},
    ),
    ("T22", T22, "review_required", {"zinsgrens_onzeker_1": "review_required", **OPEN}),
    ("T23", T23, "review_required", {"zinsgrens_onzeker_1": "review_required", **OPEN}),
    # Besluit /3 punt 3: automatische dispositie onzeker; normatief label fail.
    (
        "T24",
        T24,
        "review_required",
        {
            "zinsgrens_onzeker_1": "review_required",
            "zinsgrens_onzeker_2": "review_required",
            **OPEN,
        },
    ),
    (
        "zeker-fail",
        ZEKER_FAIL,
        "fail",
        {"zinsgrens_1": "fail", **OPEN},
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tekst", "status", "delen"),
    [pytest.param(t, s, d, id=i) for i, t, s, d in SERVICEGEVALLEN],
)
async def test_service_uitkomst_beide_laadpaden(svc, tekst, status, delen):
    res = await svc.validate_definition(
        begrip="object", text=tekst, ontologische_categorie=None, context={}
    )
    assert res["rule_statuses"]["INT-01"] == status
    assert "INT-01" not in res["passed_rules"]
    detail = res["rule_results"]["INT-01"]
    assert detail["contract_version"] == CONTRACTVERSIE
    assert _delen(detail) == delen
    redenen = {p["id"]: p["reason"] for p in detail["parts"]}
    assert redenen["compactheid"] != redenen["begrijpelijkheid"]


# ── Contractversie, opslag en weergave ──────────────────────────────────


def test_contractversie_is_3_na_conservatief_besluit():
    """Besluit punt 5: de beslisbetekenis wijzigt, dus /2 → /3."""
    assert CONTRACTVERSIE == "def770-int01/3"


@pytest.mark.parametrize("oude_versie", ["def770-int01/1", "def770-int01/2"])
@pytest.mark.parametrize(
    ("tekst", "nieuw"),
    [(T24, "review_required"), (ZEKER_FAIL, "fail")],
    ids=["T24", "zeker-fail"],
)
def test_uitkomst_onder_oude_contractversie_geldt_niet_als_actueel(
    oude_versie, tekst, nieuw
):
    # T24 was onder /2 'fail'; die oude uitkomst mag niet als /3 gelden.
    oud = dict(bouw_beoordeling(tekst, 1), status="fail", contract_version=oude_versie)
    gelezen = lees_beoordeling(oud, tekst)
    assert gelezen["applied"] is False
    assert "contractversie" in gelezen["applied_reason"]
    # UI-weergave bij dezelfde tekst: niet toepasbaar, geen oude onderdelen.
    weergave = weergavedetail(oud, tekst)
    assert [p["id"] for p in weergave["parts"]] == ["tekstbinding"]
    assert weergave["status"] == "review_required"
    # Een volgende schrijfactie levert een verse /3-uitkomst met historie.
    registratie = met_nieuwe_beoordeling({"int01_beoordeling": oud}, tekst, 2)
    assert registratie["int01_beoordeling"]["contract_version"] == CONTRACTVERSIE
    assert registratie["int01_beoordeling"]["status"] == nieuw
    assert len(registratie["int01_beoordeling_history"]) == 1


@pytest.mark.parametrize(
    ("tekst", "status"),
    [
        (T15, "review_required"),
        (T19, "review_required"),
        (T24, "review_required"),
        (ZEKER_FAIL, "fail"),
    ],
    ids=["T15", "T19", "T24", "zeker-fail"],
)
def test_opslag_en_teruglezen(tmp_path: Path, tekst, status):
    pad = tmp_path / "herstel.db"
    did = DefinitieRepository(str(pad)).create_definitie(
        DefinitieRecord(
            begrip="object",
            definitie=tekst,
            categorie="type",
            organisatorische_context='["Synthetische Proefdienst"]',
            juridische_context="[]",
            wettelijke_basis="[]",
            status=DefinitieStatus.DRAFT.value,
        )
    )
    record = DefinitieRepository(str(pad)).get_definitie(did)
    assert record is not None and record.definitie == tekst
    uit = record.get_int01_beoordeling()
    assert uit["applied"] is True
    assert uit["status"] == status
    assert uit["contract_version"] == CONTRACTVERSIE
    assert _delen(uit) == _delen(regeluitkomst(segmenteer(tekst)))
