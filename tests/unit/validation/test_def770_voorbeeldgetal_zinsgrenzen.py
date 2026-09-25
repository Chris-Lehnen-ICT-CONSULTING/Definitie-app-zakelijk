"""DEF-770 T08-correctie (contract /10): aangekondigd numeriek voorbeeld.

Bron: logs/def770-citaatbeleid/astra-acceptatie-v2.md, bevinding 3 (LOW). In
effectproeven-citaatbeleid-20260925-v2 (nu ontwikkelbewijs; alleen gelezen)
meldt de app bij ‘…, bijv. 12. De achterkant …’ naast de echte grens na ‘12.’
ook een onzekere grens na ‘bijv.’. Beide referenties en de adjudicatie
onderbouwen die afkortingspunt als intern.

Oorzaak: de cijferroute in `_classificeer_afkorting` kwam vóór de
voorbeeldvrijstelling uit /9 (‘bijv. R7.’), die alleen voor een code met
hoofdletter gold. Herstel: dezelfde, positief ondersteunde voorbeeldcontext
(alleen ‘bijv.’, gevolgd door één voorbeeld dat direct met een slotteken of
het tekstenende afsluit) geldt ook voor een getal. Geen algemene vrijstelling
voor afkorting plus getal: onbekende afkortingen, andere aankondigers en een
getal met vervolgwoorden blijven onzeker, zoals in het bestaande contract. De
echte grens na het getal blijft beoordeeld. T17/T24 vallen hier buiten.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from domain.int01.opslag import bouw_beoordeling, lees_beoordeling
from domain.int01.zinsgrenzen import CONTRACTVERSIE, segmenteer
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

PROEF = (
    Path(__file__).resolve().parents[3]
    / "docs/analyses/def606-regeldossiers/INT-01-implementatie"
    / "effectproeven-citaatbeleid-20260925-v2"
)
#: T08 uit t24-gevallen-v1.json van de v2-proef (gecontroleerd hieronder).
P2_T08 = (
    "Kaart waarop elke proefronde een nummer krijgt, bijv. 12. De achterkant biedt "
    "ruimte voor opmerkingen."
)

REDEN_GETAL = "afkorting gevolgd door een getal"
REDEN_GRENS = "getal aan zinseinde gevolgd door een nieuw zinsbegin"

# (id, tekst, [(soort, teken op positie, deel van de passage, deel van de
# reden)]) — elke verwachte grens; geen andere.
GEVALLEN = [
    # Positief aangekondigd numeriek voorbeeld: alleen de echte grens.
    ("p2-T08", P2_T08, [("zeker", ".", "bijv. 12. De achterkant", REDEN_GRENS)]),
    ("getal-slot", "kaart met een nummer, bijv. 12.", []),
    ("getal-einde", "kaart met een nummer, bijv. 12", []),
    ("getal-decimaal-slot", "kaart met een maat, bijv. 12.5.", []),
    # Code uit /9 ongewijzigd.
    ("code-slot", "kaart met een code, bijv. R7.", []),
    # Negatieve tegenhangers: onzeker zoals in het bestaande contract.
    (
        "getal-met-vervolg",
        "kaart met een nummer, bijv. 12 velden liggen klaar",
        [("onzeker", ".", "bijv. 12 velden", REDEN_GETAL)],
    ),
    (
        "getal-met-komma",
        "kaart met een nummer, bijv. 12, 13 en 14",
        [("onzeker", ".", "bijv. 12, 13", REDEN_GETAL)],
    ),
    (
        "andere-aankondiger",
        "kaart met een nummer, bv. 12.",
        [("onzeker", ".", "bv. 12.", REDEN_GETAL)],
    ),
    (
        "onbekende-afkorting",
        "kaart met een nummer volgens q.z. 12.",
        [("onzeker", ".", "q.z. 12.", REDEN_GETAL)],
    ),
    (
        "mogelijk-zinslot",
        "kaarten, borden enz. 12 stuks liggen klaar",
        [("onzeker", ".", "enz. 12 stuks", REDEN_GETAL)],
    ),
    (
        "mogelijk-zinslot-afsluitend",
        "kaarten, borden enz. 12.",
        [("onzeker", ".", "enz. 12.", REDEN_GETAL)],
    ),
]


@pytest.mark.parametrize(
    ("tekst", "verwacht"), [pytest.param(t, v, id=i) for i, t, v in GEVALLEN]
)
def test_grenzen_met_positie_passage_en_reden(tekst, verwacht):
    seg = segmenteer(tekst)
    assert seg is not None
    gevonden = [("zeker", g) for g in seg.zekere_grenzen] + [
        ("onzeker", g) for g in seg.onzekere_grenzen
    ]
    assert len(gevonden) == len(verwacht), seg
    for soort, teken, passage, reden in verwacht:
        assert any(
            s == soort
            and tekst[g.positie] == teken
            and passage in g.passage
            and reden in g.grond
            for s, g in gevonden
        ), (soort, teken, passage, reden, seg)


# ── Binding aan de v2-proef (alleen lezen) ──────────────────────────────


def _proefcases(naam: str) -> dict[str, dict]:
    data = json.loads((PROEF / naam).read_text(encoding="utf-8"))
    cases = data["cases"] if isinstance(data, dict) else data
    return {case["id"]: case for case in cases}


def test_proefbinding_tekst_ongewijzigd():
    assert _proefcases("t24-gevallen-v1.json")["T08"]["tekst"] == P2_T08


def test_ontwikkelregressie_volgt_adjudicatie():
    """Zinsstatus fail met de grenspassage uit de adjudicatie, en geen andere
    grens; het label wordt gelezen, niet overschreven."""
    case = _proefcases("t24-adjudicatie-v1.json")["T08"]
    seg = segmenteer(P2_T08)
    assert case["sentence_status"] == "fail"
    assert [g.passage for g in seg.onzekere_grenzen] == []
    [grens] = seg.zekere_grenzen
    assert case["boundary_passage"] in grens.passage


# ── Service (beide laadpaden), actualiteit en contract ──────────────────


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


@pytest.mark.asyncio
async def test_service_beide_laadpaden(svc):
    res = await svc.validate_definition(
        begrip="Rondekaart", text=P2_T08, ontologische_categorie=None, context={}
    )
    assert res["rule_statuses"]["INT-01"] == "fail"
    detail = res["rule_results"]["INT-01"]
    assert detail["contract_version"] == CONTRACTVERSIE
    assert {p["id"]: p["status"] for p in detail["parts"]} == {
        "zinsgrens_1": "fail",
        "compactheid": "review_required",
        "begrijpelijkheid": "review_required",
    }


def test_uitkomst_onder_contract_9_geldt_niet_als_actueel():
    oud = dict(bouw_beoordeling(P2_T08, 1), contract_version="def770-int01/9")
    gelezen = lees_beoordeling(oud, P2_T08)
    assert gelezen["applied"] is False
    assert "contractversie" in gelezen["applied_reason"]


def test_contractversie_is_10_na_voorbeeldgetal():
    """/9 is proefbron van effectproeven-citaatbeleid-20260925-v2. Deze
    correctie verandert de runtime-interpretatie (numeriek voorbeeld na
    ‘bijv.’), dus /9 → /10."""
    assert CONTRACTVERSIE == "def770-int01/10"
