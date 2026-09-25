"""DEF-770 citaatbeleid (contract /8): citaatvervolgen naar inhoudelijke beoordeling.

Besluit: herstel-20260924-v1/algemeen-citaatbesluit-v1.md (Chris: “ja”). Bij
een titel of citaat met interne zinseindpunctuatie en een voortzetting
waarvoor de samenhang of woordrollen grammaticale interpretatie vereist, is
de automatische uitkomst review_required. Normatief kan de tekst één correcte
formulering zijn. Geen woorduitgang, veronderstelde grammaticale correctheid
of afwezigheid van een herkende hoofdzin levert automatisch positief bewijs.

Tot en met /7 gaven twee positieve paden na een citaatslot toch een pass:
voorzetselgroepen erna en een vóór het citaat geopende bijzin. Beide leiden
de samenhang af uit veronderstelde woordrollen (‘met het regent’: ‘het’ als
lidwoord; ‘die de melding “Gereed.” klaar’: ‘klaar’ als slotwerkwoord). Onder
/8 is elke kleine-lettervoortzetting na een citaatslot onzeker, zoals een punt
met kleine letter sinds /3.

Behouden (geen algemene onzekerverklaring voor citaten): interne leestekens
van een citaat die niet direct vóór het sluitende teken staan, een citaat
zonder slotteken, en zekere buitenste grenzen.

T17 uit de restherstelproef (effectproeven-restherstel-20260925-v1) is
ontwikkelbewijs; de labels zijn overgenomen uit astra-t24-acceptatie-v1.md
(normatief en historisch automatisch pass), niet aangepast. De afzonderlijke
besluitverwachting is review_required. Nooit een volledige INT-01-pass.
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

#: T17 uit de restherstelproef; ontwikkelbewijs.
R_T17 = (
    "bord met de tekst ‘Ga verder!’ dat tijdens een oefening een vrije doorgang "
    "markeert"
)
#: Labels van die proef (astra-t24-acceptatie-v1.md): zichtbaar, ongewijzigd.
REFERENTIE_NORMATIEF = {"T17": "pass"}
HISTORISCH_AUTOMATISCH = {"T17": "pass"}
#: Besluitverwachting volgens algemeen-citaatbesluit-v1.
BESLUIT_AUTOMATISCH = {"T17": "review_required"}


# (id, tekst, zekere grenzen, onzekere grenzen)
ONZEKER = [
    ("r-T17", R_T17, 0, 1),
    # dat/die-bijzin na het citaat: zelfde vorm, andere lezing mogelijk.
    (
        "dat-hoofdzinvolgorde",
        (
            "bord met de tekst ‘Ga verder!’ dat markeert tijdens een oefening een "
            "vrije doorgang"
        ),
        0,
        1,
    ),
    ("die-bijzin", "kaart met de titel ‘Klaar?’ die de speler bewaart", 0, 1),
    # Tot en met /7 pass via voorzetselgroepen: veronderstelde woordrollen.
    ("pp-het-regent", "kaart met de titel ‘Klaar?’ met het regent", 0, 1),
    ("pp-scherm", "code met de melding “Gereed.” op het scherm", 0, 1),
    ("pp-commissie", "vraag ‘Wie betaalt?’ van de commissie", 0, 1),
    # Tot en met /7 pass via een vóór het citaat geopende bijzin.
    ("bijzin-toont", "code die de melding “Gereed.” toont", 0, 1),
    ("bijzin-klaar", "code die de melding “Gereed.” klaar", 0, 1),
    (
        "bijzin-pp",
        "code waarmee een bediener de melding “Gereed.” op het scherm zet",
        0,
        1,
    ),
]

# Afbakening: het besluit is geen algemene onzekerverklaring voor citaten.
BEHOUDEN = [
    # Interne punctuatie niet direct vóór het sluitende teken.
    ("intern-punt", "melding “Klaar. Ga door” op het scherm", 0, 0),
    ("intern-vraag", "formulier met de kop “Wie? Wanneer” boven de velden", 0, 0),
    # Citaat zonder slotteken: geen kandidaat.
    (
        "zonder-slotteken",
        "bord met de tekst ‘Ga verder’ dat een doorgang markeert",
        0,
        0,
    ),
    # Zekere buitenste grens blijft zeker, naast de onzekere citaatgrens.
    (
        "zekere-grens",
        "bord met de tekst ‘Ga verder!’ op de muur. Het bord hangt vast.",
        1,
        1,
    ),
    # Nominale kern zonder citaat: geen persoonsvormplicht.
    ("geen-citaat", "bord dat tijdens een oefening een vrije doorgang markeert", 0, 0),
]


@pytest.mark.parametrize(
    ("tekst", "zeker", "onzeker"),
    [pytest.param(t, z, o, id=i) for i, t, z, o in ONZEKER + BEHOUDEN],
)
def test_segmentatie(tekst, zeker, onzeker):
    seg = segmenteer(tekst)
    assert seg is not None
    assert len(seg.zekere_grenzen) == zeker, seg
    assert len(seg.onzekere_grenzen) == onzeker, seg


@pytest.mark.parametrize(
    "tekst", [t for _, t, _, _ in ONZEKER], ids=[i for i, *_ in ONZEKER]
)
def test_citaatvervolg_houdt_passage_en_reden(tekst):
    seg = segmenteer(tekst)
    [grens] = seg.onzekere_grenzen
    assert grens.passage and tekst[grens.positie] in "?!."
    assert "aanhalingsteken" in grens.grond
    delen = {p["id"]: p["status"] for p in regeluitkomst(seg)["parts"]}
    assert "zinsstructuur" not in delen


def test_geheel_geciteerde_kern_ongewijzigd():
    seg = segmenteer("“Een luisterpunt vangt zachte tiksignalen op.”")
    assert not seg.zekere_grenzen and not seg.onzekere_grenzen
    delen = {p["id"]: p["status"] for p in regeluitkomst(seg)["parts"]}
    assert delen["zinsstructuur"] == "pass"
    assert delen["broncitaat"] == "review_required"


def test_r_t17_besluitverwachting_naast_referentie():
    """Normatief en historisch pass blijven zichtbaar; automatisch geldt het
    besluit (review_required)."""
    assert REFERENTIE_NORMATIEF["T17"] == HISTORISCH_AUTOMATISCH["T17"] == "pass"
    detail = regeluitkomst(segmenteer(R_T17))
    assert detail["status"] == BESLUIT_AUTOMATISCH["T17"]
    delen = {p["id"]: p["status"] for p in detail["parts"]}
    assert delen["zinsgrens_onzeker_1"] == BESLUIT_AUTOMATISCH["T17"]


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tekst",
    [R_T17, "code met de melding “Gereed.” op het scherm"],
    ids=["r-T17", "pp-scherm"],
)
async def test_service_beide_laadpaden(svc, tekst):
    res = await svc.validate_definition(
        begrip="object", text=tekst, ontologische_categorie=None, context={}
    )
    assert res["rule_statuses"]["INT-01"] == "review_required"
    assert "INT-01" not in res["passed_rules"]
    detail = res["rule_results"]["INT-01"]
    assert detail["contract_version"] == CONTRACTVERSIE
    assert {p["id"]: p["status"] for p in detail["parts"]} == {
        "zinsgrens_onzeker_1": "review_required",
        **OPEN,
    }


def test_opslag_en_teruglezen(tmp_path: Path):
    pad = tmp_path / "citaatbeleid.db"
    did = DefinitieRepository(str(pad)).create_definitie(
        DefinitieRecord(
            begrip="object",
            definitie=R_T17,
            categorie="type",
            organisatorische_context='["Synthetische Proefdienst"]',
            juridische_context="[]",
            wettelijke_basis="[]",
            status=DefinitieStatus.DRAFT.value,
        )
    )
    uit = DefinitieRepository(str(pad)).get_definitie(did).get_int01_beoordeling()
    assert uit["applied"] is True
    assert uit["status"] == "review_required"
    assert uit["contract_version"] == CONTRACTVERSIE
    assert uit["parts"] == regeluitkomst(segmenteer(R_T17))["parts"]


def test_contractversie_na_citaatbeleid_en_citaatcorrectie():
    """/7 (restherstel) is proefbron geweest; het citaatbeleid verandert de
    runtime-interpretatie (geen positief citaatvervolg meer), dus /7 → /8. De
    citaatcorrectie (astra-acceptatie-v1) daarna: /8 → /9
    (test_def770_citaatcorrectie_zinsgrenzen.py)."""
    assert CONTRACTVERSIE == "def770-int01/9"
