"""DEF-770 vervolg (contract /6): T20 en T24 uit de verse T24-herproef.

Bron: effectproeven-herstel-20260924-v1/t24-herproef-v1 (adjudicatie-v1,
bevindingstoets-v1). Die set is nu ontwikkelregressie; de historische labels
hieronder zijn overgenomen, niet aangepast:

- T20 historisch normatief pass, automatisch pass. Titelbeleid
  (herstel-20260924-v1/titel-en-budgetbesluit-v1.md, 25 september 2026,
  “akkoord op beide”): een voortzetting na een titel of citaat waarvan de
  woordrollen niet automatisch bewezen zijn, krijgt inhoudelijke beoordeling.
  De automatische verwachting voor T20 is daarom review_required; de
  normatieve interpretatie mag één formulering blijven. De positieve
  'waar'-bijzinherkenning uit contract /5 is vervallen (astra-review-v1..v3).
- T24 normatief en automatisch review_required: de afkorting 'v.qr.' wordt in
  de tekst zelf verklaard, dus haar punten zijn intern. De twijfel zit in de
  onduidelijke aansluiting na het haakje ('quicksortering) v.qr. bepaalt het
  sorteervak'), niet in een afkortingspunt.

Kleine-letterbeleid, T17/T18/T23 en eerdere regressies blijven in de andere
testbestanden bewaakt. Nooit een volledige INT-01-pass.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)
from domain.int01.zinsgrenzen import CONTRACTVERSIE, regeluitkomst, segmenteer
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

#: T20 herproef — historisch normatief pass; automatisch review_required
#: onder het titelbeleid (titel-en-budgetbesluit-v1).
H_T20 = (
    "Spelkaart met de titel ‘Wie woont hier?’ waarop aanwijzingen voor een "
    "fictief dierverblijf staan."
)
#: T24 herproef — normatief review_required, automatisch review_required.
H_T24 = (
    "Bak voor onderdelen met een vakcode (v.qr. = vakcodering voor "
    "quicksortering) v.qr. bepaalt het sorteervak"
)
H_T24_PASSAGE = "quicksortering) v.qr. bepaalt het sorteervak"

#: Automatische verwachting die volgens een expliciet besluit afwijkt van het
#: historische geadjudiceerde label. Het historische label in HERPROEF blijft
#: ongewijzigd staan.
BESLUIT_AUTOMATISCH = {
    # titel-en-budgetbesluit-v1: titelvoortzetting met onbewezen woordrollen
    # → inhoudelijke beoordeling (historisch label: pass).
    "T20": "review_required",
}


# (id, tekst, zekere grenzen, onzekere grenzen)
GEVALLEN = [
    # ── Titelbeleid (titel-en-budgetbesluit-v1): na een citaatslot bewijst een
    # 'waar'-bijzin de woordrollen niet; geen automatische pass, onzeker met
    # passage en reden. Tot en met contract /5 waren de gemarkeerde varianten
    # 0/0; dat is vervallen. ──
    ("h-T20", H_T20, 0, 1),
    ("t20-waarin", "kaart met de titel ‘Klaar?’ waarin de spelregels staan", 0, 1),
    ("t20-waarbij", "bord met de tekst ‘Stop!’ waarbij de route eindigt", 0, 1),
    (
        "t20-waarvan-punt",
        "map met het opschrift “Gereed.” waarvan de inhoud vastligt",
        0,
        1,
    ),
    # Astra-review-v3 R1: voornaamwoord + persoonsvorm gevolgd door een
    # zelfstandige mededeling; blijft onzeker.
    (
        "c4-r1-het-werkt",
        "kaart met de titel ‘Klaar?’ waarop het werkt de deelnemers wachten",
        0,
        1,
    ),
    (
        "c4-r1-dit-werkt",
        "kaart met de titel ‘Klaar?’ waarop dit werkt de deelnemers wachten",
        0,
        1,
    ),
    # Negatief: na de bijzin volgt een tweede persoonsvorm (hoofdzin).
    (
        "t20-bijzin-dan-hoofdzin",
        (
            "kaart met de titel ‘Wie woont hier?’ waarop aanwijzingen staan is de "
            "controle vereist"
        ),
        0,
        1,
    ),
    (
        "t20-bijzin-komma-hoofdzin",
        (
            "kaart met de titel ‘Wie woont hier?’ waarop aanwijzingen staan, "
            "volgt de controle"
        ),
        0,
        1,
    ),
    # Negatief: vraagzin na het citaat.
    ("t20-vraagzin", "kaart met de titel ‘Wie woont hier?’ waarop wacht je?", 0, 1),
    # Negatief: echte zelfstandige zin na de bijzin, met hoofdletter. Onder het
    # titelbeleid is ook het citaatslot onzeker (was 1/0 t/m contract /5).
    (
        "t20-zin-na-bijzin",
        (
            "kaart met de titel ‘Wie woont hier?’ waarop de aanwijzingen staan. De "
            "kaart ligt klaar."
        ),
        1,
        1,
    ),
    # Astra-review-v2 R1: met kaal onderwerp is ook het citaatslot onzeker
    # (was 1/0 in v2; de zekere fail is ongewijzigd).
    (
        "t20-zin-na-kale-bijzin",
        (
            "kaart met de titel ‘Wie woont hier?’ waarop aanwijzingen staan. De "
            "kaart ligt klaar."
        ),
        1,
        1,
    ),
    # Negatief: geen ondubbelzinnige bijzinmarkering ('die' kan aanwijzend).
    (
        "t20-die-aanwijzend",
        "kaart met de titel ‘Wie woont hier?’ die aanwijzingen staan klaar",
        0,
        1,
    ),
    (
        "t20-zelfstandig",
        "kaart met de titel ‘Wie woont hier?’ de kaart ligt klaar",
        0,
        1,
    ),
    # Conservatieve grens: een herkende persoonsvorm midden in de bijzin
    # ('is samengevat') is zonder woordsoortkennis niet van een hoofdzin te
    # onderscheiden; blijft onzeker.
    (
        "t20-grens-pv-midden",
        "boek met de titel ‘Wat nu?’ waarvan de inhoud is samengevat",
        0,
        1,
    ),
    # ── Astra-review-v1 R1: afwezigheid van een herkend werkwoord bewijst
    # geen bijzin. Exacte review-repro's: blijven onzeker. ──
    (
        "c2-r1-repro-vraagvolgorde",
        "kaart met de titel ‘Wie woont hier?’ waarop wacht je.",
        0,
        1,
    ),
    (
        "c2-r1-repro-extra-hoofdzin",
        (
            "kaart met de titel ‘Wie woont hier?’ waarop aanwijzingen staan daarna "
            "volgt de controle."
        ),
        0,
        1,
    ),
    # Titelbeleid: ook met naamwoord-/voorzetselgroepen en werkwoordsvorm
    # achteraan zijn de woordrollen niet bewezen; onzeker (was 0/0 t/m /5).
    (
        "c2-r1-twee-groepen",
        "kaart met de titel ‘Klaar?’ waarmee de speler een route kiest",
        0,
        1,
    ),
    (
        "c2-r1-voorzetselgroep",
        "kaart met de titel ‘Klaar?’ waarin de regels voor de ronde staan",
        0,
        1,
    ),
    # Negatief: extra woord zonder groepsopening (verborgen tweede zin).
    (
        "c2-r1-lidwoordgroep-dan-pv",
        "kaart met de titel ‘Klaar?’ waarop de aanwijzingen staan volgt",
        0,
        1,
    ),
    (
        "c2-r1-pv-in-voorzetselgroep",
        "kaart met de titel ‘Klaar?’ waarop aanwijzingen voor een dier staan volgt",
        0,
        1,
    ),
    (
        "c2-r1-tweede-zin-na-groep",
        "kaart met de titel ‘Klaar?’ waarop de speler wacht de controle volgt",
        0,
        1,
    ),
    # Negatief: laatste woord heeft geen persoonsvormuitgang.
    (
        "c2-r1-voornaamwoord-slot",
        "kaart met de titel ‘Klaar?’ waarop staat je naam",
        0,
        1,
    ),
    # Bewijsgrens: sterke verledentijdsvorm zonder herkenbare uitgang blijft
    # onzeker (conservatief dekkingsverlies, geen fout).
    (
        "c2-r1-grens-sterk-verleden",
        "kaart met de titel ‘Klaar?’ waarop de naam stond",
        0,
        1,
    ),
    # ── Astra-review-v2 R1: rollen moeten onderscheidend ondersteund zijn.
    # Exacte repro en verwisselde woordvolgorde: onzeker. ──
    (
        "c3-r1-repro-verwisseld",
        "kaart met de titel ‘Wie woont hier?’ waarop staan aanwijzingen",
        0,
        1,
    ),
    (
        "c3-r1-verwisseld-punt",
        "kaart met de titel ‘Wie woont hier?’ waarop staan aanwijzingen.",
        0,
        1,
    ),
    (
        "c3-r1-verwisseld-lidwoord",
        "kaart met de titel ‘Wie woont hier?’ waarop staan de aanwijzingen",
        0,
        1,
    ),
    (
        "c3-r1-waarin-verwisseld",
        "kaart met de titel ‘Klaar?’ waarin staan de namen",
        0,
        1,
    ),
    (
        "c3-r1-waarmee-verwisseld",
        "kaart met de titel ‘Klaar?’ waarmee betaalt een speler",
        0,
        1,
    ),
    (
        "c3-r1-waarvoor-verwisseld",
        "kaart met de titel ‘Klaar?’ waarvoor gelden de regels",
        0,
        1,
    ),
    # Titelbeleid: een lidwoordmarkering bewijst de rollen niet (astra-review-v3
    # R1, 'het werkt'); onzeker met en zonder slotpunt (was 0/0 t/m /5).
    (
        "c3-r1-gemarkeerd",
        "kaart met de titel ‘Wie woont hier?’ waarop de aanwijzingen staan",
        0,
        1,
    ),
    (
        "c3-r1-gemarkeerd-punt",
        "kaart met de titel ‘Wie woont hier?’ waarop de aanwijzingen staan.",
        0,
        1,
    ),
    (
        "c3-r1-waarin-gemarkeerd",
        "kaart met de titel ‘Klaar?’ waarin de namen staan",
        0,
        1,
    ),
    (
        "c3-r1-waarmee-gemarkeerd",
        "kaart met de titel ‘Klaar?’ waarmee een speler betaalt",
        0,
        1,
    ),
    (
        "c3-r1-waarvoor-gemarkeerd",
        "kaart met de titel ‘Klaar?’ waarvoor de regels gelden",
        0,
        1,
    ),
    # Kaal (ongemarkeerd) onderwerp: rol niet te onderscheiden van een
    # verwisselde volgorde; onzeker (dit is ook de vorm van de T20-herproeftekst).
    ("c3-r1-kaal-onderwerp", "kaart met de titel ‘Klaar?’ waarin namen staan", 0, 1),
    # ── T24: lokaal verklaarde afkorting ──
    ("h-T24", H_T24, 0, 1),
    # Andere verklaringsvormen en afkortingen (geen corpusnaam).
    (
        "t24-hierna",
        (
            "kast volgens de dossierkast standaard (hierna: dk.st.) dk.st. regelt "
            "de plaatsing"
        ),
        0,
        1,
    ),
    # Astra-review-v1 R2: de verklaring bewijst de afkortingsfunctie, niet dat
    # de slotpunt van een latere vermelding geen zinseinde is (was 0/0 in v1).
    (
        "t24-afkorting-tussen-haakjes-met-aansluiting",
        (
            "kast volgens de dossierkast standaard (dk.st.) waarin dk.st. de "
            "plaatsing regelt"
        ),
        0,
        1,
    ),
    # Review-repro R2: latere vermelding met kleine letter erna blijft onzeker.
    (
        "c2-r2-repro-slotpunt-later",
        (
            "Bak met vakcode (v.qr. = vakcodering) ingedeeld volgens v.qr. daarna "
            "volgt controle"
        ),
        0,
        1,
    ),
    (
        "c2-r2-hierna-later",
        (
            "kast volgens de standaard (hierna: dk.st.) ingericht volgens dk.st. de "
            "plaatsing volgt"
        ),
        0,
        1,
    ),
    # Punten in de verklaring zelf (vóór '=' of het sluitende haakje) zijn intern.
    ("c2-r2-alleen-verklaring", "Bak met vakcode (v.qr. = vakcodering)", 0, 0),
    ("c2-r2-verklaring-haakjes", "kast volgens de standaard (dk.st.)", 0, 0),
    # Astra-review-v2 R2: onderdrukking alleen waar dezelfde overgang door de
    # aansluitingsmelding gedekt wordt; 0, 1, meer spaties, tab en regelomloop.
    (
        "c3-r2-repro-zonder-spatie",
        (
            "Bak voor onderdelen met een vakcode (v.qr. = vakcodering voor "
            "quicksortering)v.qr. bepaalt het sorteervak"
        ),
        0,
        1,
    ),
    (
        "c3-r2-meer-spaties",
        "Bak met vakcode (v.qr. = vakcodering)   v.qr. bepaalt het vak",
        0,
        1,
    ),
    ("c3-r2-tab", "Bak met vakcode (v.qr. = vakcodering)\tv.qr. bepaalt het vak", 0, 1),
    (
        "c3-r2-regelomloop",
        "Bak met vakcode (v.qr. = vakcodering)\nv.qr. bepaalt het vak",
        0,
        1,
    ),
    (
        "c3-r2-dubbele-haakjes",
        "Bak met vakcode (v.qr. = vakcodering (intern))v.qr. bepaalt het vak",
        0,
        1,
    ),
    # Aansluiting na het haakje én een latere slotpunt: twee overgangen.
    (
        "c3-r2-aansluiting-en-later",
        (
            "Bak met vakcode (v.qr. = vakcodering) v.qr. bepaalt het vak volgens "
            "v.qr. daarna volgt controle"
        ),
        0,
        2,
    ),
    # Niet-verklaarde afkorting na een haakje: gewone kleine-letteronzekerheid.
    (
        "c3-r2-onverklaard-na-haakje",
        "Bak met code (zie bijlage)x.qr. bepaalt het vak",
        0,
        1,
    ),
    # Verklaard én duidelijk aangesloten: geen twijfel.
    (
        "t24-verklaard-aangesloten",
        (
            "Bak voor onderdelen met een vakcode (v.qr. = vakcodering) volgens "
            "het sorteervak"
        ),
        0,
        0,
    ),
    # Negatief: niet verklaard — punt + kleine letter blijft onzeker.
    ("t24-onverklaard", "Bak voor onderdelen met code v.qr. bepaalt het vak", 0, 1),
    # Negatief: duidelijke grens na het haakje blijft zekere fail. Astra-review-
    # v1 R2: de slotpunt van de latere vermelding ('De v.qr. bepaalt') is
    # daarnaast onzeker (was 1/0 in v1; de zekere fail is ongewijzigd).
    (
        "t24-verklaard-dan-nieuwe-zin",
        "Bak met een vakcode (v.qr. = vakcodering). De v.qr. bepaalt het vak.",
        1,
        1,
    ),
    # Negatief: verklaarde afkorting gevolgd door een hoofdletter blijft onzeker.
    (
        "t24-verklaard-hoofdletter",
        "Bak met een vakcode (v.qr. = vakcodering) volgens v.qr. Het vak ligt vast",
        0,
        1,
    ),
]


#: Volledige bekende herproefset (t24-herproef-v1/gevallen-v1.json) met het
#: geadjudiceerde automatische label (adjudicatie-v1.json, sentence_status).
#: Ontwikkelregressie; labels overgenomen, niet aangepast.
HERPROEF = [
    ("T01", "Voorziening voor de tijdelijke opslag van regenwater", "pass"),
    (
        "T02",
        "Transportbak die na aflevering van de inhoud naar de verzender terugkeert.",
        "pass",
    ),
    (
        "T03",
        "Opslag van warmte en koude in een ondergronds reservoir voor later gebruik",
        "pass",
    ),
    (
        "T04",
        (
            "Kast waarin bezoekers zaden achterlaten en waaruit zij zaden meenemen. "
            "Elk vak bevat één plantensoort."
        ),
        "fail",
    ),
    ("T05", "Lade voor maximaal 12 buisjes met elk 2,5 ml vloeistof.", "pass"),
    (
        "T06",
        (
            "Geordend overzicht van de ontwerpen van ir. Maanlijn. Elke schets heeft "
            "een volgnummer."
        ),
        "fail",
    ),
    (
        "T07",
        "Verzameling materialen voor handwerk, zoals papier, draad, kralen enz.",
        "pass",
    ),
    (
        "T08",
        (
            "Controle van een installatie volgens schema nr. 4, bijv. vóór "
            "ingebruikname. De controleur registreert de meetwaarden."
        ),
        "fail",
    ),
    (
        "T09",
        "Een stiltecabine is een afgesloten werkplek die omgevingsgeluid dempt.",
        "pass",
    ),
    (
        "T10",
        (
            "Een wisselvak is een gemarkeerde ruimte waar estafettelopers een stok "
            "overdragen. De markering begrenst de overdrachtsruimte."
        ),
        "fail",
    ),
    (
        "T11",
        (
            "Een controlevraag is een vraag waarmee een spreker nagaat of een uitleg "
            "is begrepen. Kan de toehoorder de beschreven stap navertellen?"
        ),
        "fail",
    ),
    (
        "T12",
        (
            "Een stoproep is een luide mondelinge opdracht om een handeling "
            "onmiddellijk te onderbreken. Leg het gereedschap neer!"
        ),
        "fail",
    ),
    (
        "T13",
        "Strook begroeide grond\nlangs een waterloop\ndie afstromend water vertraagt.",
        "pass",
    ),
    (
        "T14",
        (
            "Een reparatielogboek is een chronologisch overzicht van uitgevoerde "
            "herstelwerkzaamheden.\n\nElke vermelding beschrijft de storing en de "
            "toegepaste ingreep."
        ),
        "fail",
    ),
    (
        "T15",
        (
            "Draagbare uitrusting voor terreinmetingen, bestaande uit:\n- een "
            "afstandsmeter;\n- een peilstok;\n- een notitiekaart."
        ),
        "pass",
    ),
    (
        "T16",
        (
            "Nachtventilatie is het verversen van binnenlucht tijdens de nacht; de "
            "luchtstroom voert opgehoopte warmte af."
        ),
        "pass",
    ),
    (
        "T17",
        "Bord dat met de tekst ‘Pas op!’ de aandacht vestigt op een gevaarlijke plek.",
        "review_required",
    ),
    (
        "T18",
        (
            "Een kiemhoes is een doorlatende omhulling rond een zaaibak. (De "
            "omhulling houdt insecten buiten.)"
        ),
        "fail",
    ),
    (
        "T19",
        "“Afgebakende ruimte waar bezoekers een geluidsopname beluisteren.”",
        "pass",
    ),
    ("T20", H_T20, "pass"),
    ("T21", "", "not_evaluated"),
    ("T22", "Reservevak:", "review_required"),
    (
        "T23",
        (
            "Een droogrek is een frame waaraan nat textiel wordt opgehangen. de open "
            "ruimte tussen de stangen laat lucht door."
        ),
        "review_required",
    ),
    ("T24", H_T24, "review_required"),
]


@pytest.mark.parametrize(
    ("tekst", "label"),
    [pytest.param(t, BESLUIT_AUTOMATISCH.get(i, lab), id=i) for i, t, lab in HERPROEF],
)
def test_bekende_herproefset_automatisch_label(tekst, label):
    seg = segmenteer(tekst)
    if label == "not_evaluated":
        assert seg is None
        return
    assert seg is not None
    if label == "fail":
        assert seg.zekere_grenzen, seg
    elif label == "review_required":
        assert not seg.zekere_grenzen and seg.onzekere_grenzen, seg
    else:
        assert not seg.zekere_grenzen and not seg.onzekere_grenzen, seg


@pytest.mark.parametrize(
    ("tekst", "zeker", "onzeker"),
    [pytest.param(t, z, o, id=i) for i, t, z, o in GEVALLEN],
)
def test_segmentatie(tekst, zeker, onzeker):
    seg = segmenteer(tekst)
    assert seg is not None
    assert len(seg.zekere_grenzen) == zeker, seg
    assert len(seg.onzekere_grenzen) == onzeker, seg


def test_t20_titelvoortzetting_is_inhoudelijke_beoordeling():
    """Titelbeleid (titel-en-budgetbesluit-v1): geen automatische zinspass;
    één onzekere grens op het citaatslot, met passage en reden."""
    seg = segmenteer(H_T20)
    assert not seg.zekere_grenzen
    [grens] = seg.onzekere_grenzen
    assert grens.positie == H_T20.index("?’")
    assert "hier?’" in grens.passage
    assert "aanhalingsteken" in grens.grond
    detail = regeluitkomst(seg)
    assert detail["status"] == "review_required"
    delen = {p["id"]: p["status"] for p in detail["parts"]}
    assert "zinsstructuur" not in delen
    assert delen["zinsgrens_onzeker_1"] == "review_required"


def test_t24_twijfel_op_aansluiting_niet_op_afkortingspunten():
    seg = segmenteer(H_T24)
    assert not seg.zekere_grenzen
    [grens] = seg.onzekere_grenzen
    assert grens.passage == H_T24_PASSAGE
    assert grens.positie == H_T24.index(")")
    assert "aansluiting" in grens.grond
    assert "kleine letter" not in grens.grond
    assert "afkorting gevolgd" not in grens.grond


# ── Service (beide laadpaden) en opslag ─────────────────────────────────


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
SERVICEGEVALLEN = [
    # Titelbeleid (titel-en-budgetbesluit-v1): was zinsstructuur pass t/m /5.
    ("h-T20", H_T20, {"zinsgrens_onzeker_1": "review_required", **OPEN}),
    ("h-T24", H_T24, {"zinsgrens_onzeker_1": "review_required", **OPEN}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tekst", "delen"),
    [pytest.param(t, d, id=i) for i, t, d in SERVICEGEVALLEN],
)
async def test_service_uitkomst_beide_laadpaden(svc, tekst, delen):
    res = await svc.validate_definition(
        begrip="object", text=tekst, ontologische_categorie=None, context={}
    )
    assert res["rule_statuses"]["INT-01"] == "review_required"
    assert "INT-01" not in res["passed_rules"]
    detail = res["rule_results"]["INT-01"]
    assert detail["contract_version"] == CONTRACTVERSIE
    assert {p["id"]: p["status"] for p in detail["parts"]} == delen


@pytest.mark.parametrize("tekst", [H_T20, H_T24], ids=["h-T20", "h-T24"])
def test_opslag_en_teruglezen(tmp_path: Path, tekst):
    pad = tmp_path / "vervolg.db"
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
    assert uit["status"] == "review_required"
    assert uit["contract_version"] == CONTRACTVERSIE
    verwacht = regeluitkomst(segmenteer(tekst))["parts"]
    assert [p["id"] for p in uit["parts"]] == [p["id"] for p in verwacht]
