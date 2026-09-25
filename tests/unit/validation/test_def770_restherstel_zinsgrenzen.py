"""DEF-770 restherstel (contract /7): nominale titelvoortzetting en los label.

Bron: herstel-20260924-v1/astra-acceptatiebevindingen-v1.md. De verzegelde
T24-acceptatie (effectproeven-vervolg-20260924-v1) is nu ontwikkelbewijs; haar
labels zijn overgenomen, niet aangepast.

- T20 (nieuw): ‘fiche bij het fictieve oefenboek ‘Wie opent het luik?’ met de
  kleurcode van de bijbehorende opdracht’. Referentie pass; de app geeft
  review_required. Oorzaak: `_voorzetselgroepen` staat na het lidwoord één
  woord toe, dus ‘van de bijbehorende opdracht’ strandt. De eerste kandidaat
  (/7, één extra woord onder structurele voorwaarden) is afgekeurd
  (astra-review-v1): ‘met het regent hard’ en ‘tijdens de proef wacht’ werden
  onterecht pass, omdat het structuurargument grammaticale correctheid
  veronderstelde. Correctiepoging 2 verwijdert die uitbreiding: zonder bewijs
  van woordrollen is exacte T20 niet veilig positief te herkennen.
  Beleid (herstel-20260924-v1/restherstel-titelbesluit-v1.md, Chris: “Ja,
  deze twijfelgevallen inhoudelijk beoordelen (advies)”): een nominale
  voortzetting na een titel of citaat waarvan de samenhang woordrollen in een
  uitgebreide voorzetselgroep vraagt (lidwoord plus extra woord vóór de kern),
  krijgt automatisch review_required. De normatieve referentie blijft pass;
  het historische label en de oude 23/24-uitslag blijven ongewijzigd. De
  eerdere strikte xfails zijn vervangen door deze besluitverwachting.
- T22: ‘schakelblad’. Referentie review_required. Tot en met /6 gaf het
  ontbreken van grenzen automatisch `zinsstructuur: pass`. Eén inhoudswoord
  (eventueel met lidwoord) is geen definitieformulering: /7 geeft een open
  onderdeel `formulering` met passage en reden in plaats van die pass.

Citaatbeleid (algemeen-citaatbesluit-v1, contract /8): elke
kleine-lettervoortzetting na een citaatslot is onzeker; het basisgedrag
‘één woord na het lidwoord’ (a-T20-zonder-extra-woord) geeft daarom geen
0/0 meer.

Nooit een volledige INT-01-pass.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)
from domain.int01.zinsgrenzen import (
    CONTRACTVERSIE,
    open_melding,
    regeluitkomst,
    segmenteer,
)
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

#: T20 uit de verzegelde T24-acceptatie (t24-gevallen-v1.json); referentie pass.
A_T20 = (
    "fiche bij het fictieve oefenboek ‘Wie opent het luik?’ met de kleurcode van "
    "de bijbehorende opdracht"
)
#: T22 uit dezelfde set; referentie review_required.
A_T22 = "schakelblad"

TITEL = "kaart met de titel ‘Klaar?’ "


# ── T20: voorzetselgroep; restherstel-titelbesluit-v1 ──────────────────

#: Verzegelde T24-adjudicatie (vervolgproef); alleen gelezen, nooit gewijzigd.
T24_ADJUDICATIE = (
    Path(__file__).resolve().parents[3]
    / "docs/analyses/def606-regeldossiers/INT-01-implementatie"
    / "effectproeven-vervolg-20260924-v1/t24-adjudicatie-v1.json"
)
#: Historische normatieve referentie (t24-adjudicatie-v1.json): blijft zichtbaar.
REFERENTIE_NORMATIEF = {"T20": "pass"}
#: Automatische verwachting volgens restherstel-titelbesluit-v1 (25 september
#: 2026): uitgebreide voorzetselgroep na een titel of citaat → inhoudelijke
#: beoordeling. Geen relabel van de referentie; een dekkingsbeperking.
BESLUIT_AUTOMATISCH = {"T20": "review_required"}

# (id, tekst, zekere grenzen, onzekere grenzen)
NOMINAAL = [
    # Basisgedrag t/m /7: één woord na het lidwoord in elke groep gaf 0/0.
    # Citaatbeleid (algemeen-citaatbesluit-v1, contract /8): een
    # kleine-lettervoortzetting na een citaatslot is altijd onzeker, dus 0/1.
    pytest.param(
        (
            "fiche bij het fictieve oefenboek ‘Wie opent het luik?’ met de "
            "kleurcode van de opdracht"
        ),
        0,
        1,
        id="a-T20-zonder-extra-woord",
    ),
]

# Onzeker: een extra woord in een voorzetselgroep bewijst geen rollen.
ONZEKER = [
    # Astra-review-v1 R1: exacte regressies van de eerste kandidaat.
    ("r1-het-regent-hard", TITEL + "met het regent hard", 0, 1),
    ("r1-tijdens-wacht", TITEL + "tijdens de proef wacht", 0, 1),
    # restherstel-titelbesluit-v1: exacte T20 onzeker (automatisch
    # review_required), met passage en reden.
    ("a-T20-besluit", A_T20, 0, 1),
    # Eerdere uitbreidingsgevallen: terug naar basisgedrag.
    ("van-het", TITEL + "met de kleur van het grote vak", 0, 1),
    ("volgens-de", TITEL + "volgens de vaste volgorde", 0, 1),
    ("extra-woord-midden", TITEL + "met de rode rand van de kaart", 0, 1),
    ("onbekend", TITEL + "met de blorse vek", 0, 1),
    ("a-T20-met-tweede-zin", A_T20 + ". De speler wacht.", 1, 1),
    # Eerdere tegenvoorbeelden blijven onzeker.
    ("drie-woorden", TITEL + "met de kaart speelt men", 0, 1),
    ("twee-bijvoeglijk", TITEL + "met de kleine rode kaart", 0, 1),
    ("infinitief", TITEL + "met de pen schrijven", 0, 1),
    ("partikel-op", TITEL + "op het grote scherm", 0, 1),
    ("partikel-uit", TITEL + "uit de speler wacht", 0, 1),
    ("voegwoord-voor", TITEL + "voor de speler wacht", 0, 1),
    ("voornaamwoord-deze", TITEL + "met deze speelde hij", 0, 1),
    ("voornaamwoord-een", TITEL + "met een speelde hij", 0, 1),
    ("bijzinwoord", TITEL + "met de kaart die", 0, 1),
    ("persoonsvorm", A_T20 + " is", 0, 1),
    ("woord-buiten-groep", A_T20 + " wacht de speler", 0, 1),
    # Titelbeleid ongewijzigd: 'waar' + voorzetsel blijft onzeker.
    ("waar-bijzin", TITEL + "waarop het werkt de deelnemers wachten", 0, 1),
    ("waar-bijzin-lidwoord", TITEL + "waarin de namen staan", 0, 1),
]


@pytest.mark.parametrize(
    ("tekst", "zeker", "onzeker"),
    NOMINAAL + [pytest.param(t, z, o, id=i) for i, t, z, o in ONZEKER],
)
def test_segmentatie(tekst, zeker, onzeker):
    seg = segmenteer(tekst)
    assert seg is not None
    assert len(seg.zekere_grenzen) == zeker, seg
    assert len(seg.onzekere_grenzen) == onzeker, seg


@pytest.mark.parametrize(
    "tekst",
    [A_T20, TITEL + "met het regent hard", TITEL + "tijdens de proef wacht"],
    ids=["a-T20", "r1-het-regent-hard", "r1-tijdens-wacht"],
)
def test_onzekere_titelvoortzetting_houdt_passage_en_reden(tekst):
    seg = segmenteer(tekst)
    [grens] = seg.onzekere_grenzen
    assert "?’" in grens.passage
    assert "aanhalingsteken" in grens.grond
    delen = {p["id"]: p["status"] for p in regeluitkomst(seg)["parts"]}
    assert "zinsstructuur" not in delen
    assert delen["zinsgrens_onzeker_1"] == "review_required"


def test_a_t20_besluitverwachting_en_normatieve_referentie():
    """restherstel-titelbesluit-v1: automatisch review_required; de verzegelde
    normatieve referentie blijft pass en is hier zichtbaar, niet aangepast."""
    adjudicatie = json.loads(T24_ADJUDICATIE.read_text(encoding="utf-8"))
    [geval] = [c for c in adjudicatie["cases"] if c["id"] == "T20"]
    # Normatieve as (astra-review-v3): de referentie blijft pass.
    assert geval["normative_sentence_status"] == REFERENTIE_NORMATIEF["T20"]
    # Historisch automatisch label van die proef, apart en onveranderd.
    assert geval["sentence_status"] == "pass"
    detail = regeluitkomst(segmenteer(A_T20))
    delen = {p["id"]: p["status"] for p in detail["parts"]}
    assert detail["status"] == BESLUIT_AUTOMATISCH["T20"]
    assert "zinsstructuur" not in delen
    assert delen["zinsgrens_onzeker_1"] == BESLUIT_AUTOMATISCH["T20"]


# ── T22: los label ───────────────────────────────────────────────────────

LOS_LABEL = [
    ("a-T22", A_T22),
    ("hoofdletter-punt", "Schakelblad."),
    ("witruimte", "  schakelblad \n"),
    ("aanhalingstekens", "“schakelblad”"),
    ("koppelteken", "schakel-blad"),
    ("met-lidwoord", "het schakelblad"),
    ("ander-woord", "Reservevak"),
    ("uitroep", "Opgelet!"),
]


@pytest.mark.parametrize("tekst", [pytest.param(t, id=i) for i, t in LOS_LABEL])
def test_los_label_geen_zinsstructuur_pass(tekst):
    seg = segmenteer(tekst)
    assert seg is not None and not seg.zekere_grenzen
    detail = regeluitkomst(seg)
    assert detail["status"] == "review_required"
    delen = {p["id"]: p for p in detail["parts"]}
    assert "zinsstructuur" not in delen
    formulering = delen["formulering"]
    assert formulering["status"] == "review_required"
    assert formulering["evidence"] == " ".join(tekst.split())
    assert formulering["position"] == len(tekst) - len(tekst.lstrip())
    assert "definitieformulering" in formulering["reason"]
    assert "Eén definitieformulering vastgesteld" not in open_melding(seg)
    assert "Geen definitieformulering vastgesteld" in open_melding(seg)


def test_label_met_dubbele_punt_blijft_grens_zonder_dubbele_melding():
    """Het bestaande label-met-dubbele-puntpatroon (T22 in de herproef,
    'Reservevak:') blijft één onzekere grens; geen tweede melding."""
    seg = segmenteer("Reservevak:")
    assert len(seg.onzekere_grenzen) == 1
    delen = [p["id"] for p in regeluitkomst(seg)["parts"]]
    assert delen == ["zinsgrens_onzeker_1", "compactheid", "begrijpelijkheid"]


def test_lege_tekst_blijft_niet_beoordeeld():
    assert segmenteer("") is None
    assert segmenteer("   \n") is None


# Geldige nominale definities zonder persoonsvorm houden hun zinsstructuur-pass.
NOMINALE_DEFINITIES = [
    "Voorziening voor de tijdelijke opslag van regenwater",
    "tijdelijke opslag",
    "schakelblad voor de reserveset",
    "Schakelblad (SB)",
]


@pytest.mark.parametrize("tekst", NOMINALE_DEFINITIES)
def test_nominale_definitie_houdt_zinsstructuur_pass(tekst):
    delen = {p["id"]: p["status"] for p in regeluitkomst(segmenteer(tekst))["parts"]}
    assert delen["zinsstructuur"] == "pass"
    assert "formulering" not in delen


# ── Service (beide laadpaden), opslag en actualiteit ────────────────────


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
    # restherstel-titelbesluit-v1: automatisch review_required (BESLUIT_AUTOMATISCH).
    ("a-T20", "omslagfiche", A_T20, {"zinsgrens_onzeker_1": "review_required", **OPEN}),
    ("a-T22", "schakelblad", A_T22, {"formulering": "review_required", **OPEN}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("begrip", "tekst", "delen"),
    [pytest.param(b, t, d, id=i) for i, b, t, d in SERVICEGEVALLEN],
)
async def test_service_uitkomst_beide_laadpaden(svc, begrip, tekst, delen):
    res = await svc.validate_definition(
        begrip=begrip, text=tekst, ontologische_categorie=None, context={}
    )
    assert res["rule_statuses"]["INT-01"] == "review_required"
    assert "INT-01" not in res["passed_rules"]
    detail = res["rule_results"]["INT-01"]
    assert detail["contract_version"] == CONTRACTVERSIE
    assert {p["id"]: p["status"] for p in detail["parts"]} == delen


@pytest.mark.parametrize("tekst", [A_T20, A_T22], ids=["a-T20", "a-T22"])
def test_opslag_en_teruglezen(tmp_path: Path, tekst):
    pad = tmp_path / "restherstel.db"
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
    assert uit["parts"] == verwacht


def test_contractversie_na_restherstel_en_citaatbeleid():
    """/6 (titelbeleid) is proefbron van de verzegelde T24-acceptatie. Het
    restherstel verandert de interpretatie (los label geen zinsstructuur-pass),
    dus /6 → /7. De afgekeurde voorzetselgroepuitbreiding is geen deel van /7.
    Het citaatbeleid (algemeen-citaatbesluit-v1) verandert haar opnieuw:
    /7 → /8 (test_def770_citaatbeleid_zinsgrenzen.py), en de citaatcorrectie
    (astra-acceptatie-v1): /8 → /9 (test_def770_citaatcorrectie_zinsgrenzen.py). Het voorbeeldgetal (astra-acceptatie-v2, T08) daarna: /9 → /10
    (test_def770_voorbeeldgetal_zinsgrenzen.py)."""
    assert CONTRACTVERSIE == "def770-int01/10"
