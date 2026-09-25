"""DEF-770 correctie na de citaatbeleidproef (contract /9).

Bron: logs/def770-citaatbeleid/astra-acceptatie-v1.md (drie bevestigde
bevindingen). De afgeronde proef effectproeven-citaatbeleid-20260925-v1 is nu
ontwikkelbewijs: T15, T17, T20 en T08 zijn ontwikkelregressies. Hun teksten en
automatische labels worden hier alleen gelezen, nooit aangepast.

1. T15 — een expliciete lijstinleiding met dubbele punt geldt voor het hele
   aaneengesloten opsommingsblok, niet alleen voor het eerste lid. Werkelijke
   zinseindtekens blijven beoordeeld; een niet-ingeleide lijst, een
   blokonderbreking en tekst na het blok worden niet vrijgesteld (tekst na het
   blok was tot en met /8 alleen gemaskeerd door de grens tussen de leden).
2. T17/T20 — een citaatslot gevolgd door een scheidingsteken (‘kom terug!’,
   dat …) verloor de kandidaat en gaf zinsstructuur-pass. Voor komma,
   puntkomma en dubbele punt is dat verlies aangetoond (voorprobe-v2.log); de
   overgang bereikt nu de bestaande onzekerheidsroute, met de positie van het
   slotteken. Interne citaatpunctuatie, een citaat zonder slotteken en een
   latere zekere grens blijven zoals ze waren. Geen grammaticale pass.
3. T08 — ‘bijv. R7. De …’: na ‘bijv.’, dat zelf een voorbeeld aankondigt, is
   een alfanumerieke code die direct met een slotteken of het tekstenende
   afsluit geen zinsbegin; een zin die alleen uit ‘R7.’ bestaat, is geen zin.
   De werkelijke grens na ‘R7.’ blijft zeker. Geen algemene vrijstelling voor
   afkortingen vóór een hoofdletter; andere en onbekende afkortingen (‘ca.’,
   ‘bv.’, ‘q.z.’) blijven onzeker (astra-correctiereview-v2, R3).

Correctiereview v2 (R2): een citaatslot met komma, puntkomma of dubbele punt
zonder spatie erna volgt dezelfde route als met spatie.

Nooit een volledige INT-01-pass.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from domain.int01.opslag import bouw_beoordeling, lees_beoordeling
from domain.int01.zinsgrenzen import CONTRACTVERSIE, regeluitkomst, segmenteer
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

PROEF = (
    Path(__file__).resolve().parents[3]
    / "docs/analyses/def606-regeldossiers/INT-01-implementatie"
    / "effectproeven-citaatbeleid-20260925-v1"
)

#: Teksten uit t24-gevallen-v1.json (gecontroleerd in test_proefbinding).
P_T08 = (
    "tekenreeks voor een terugkerende proefzending, bijv. R7. De laatste positie "
    "bevat een cijfer van 0 t/m 9."
)
P_T15 = (
    "samenstel van drie losneembare lagen:\n- een poreuze bovenlaag\n"
    "- een gekleurde tussenlaag\n- een gladde onderlaag"
)
P_T17 = (
    "Een terugroepteken is een lichtsignaal met de betekenis ‘kom terug!’, dat "
    "verschijnt zodra een oefenwagen zijn keerpunt passeert."
)
P_T20 = (
    "Een luisterkaart is een kaart uit de oefenreeks ‘Wie luistert?’, waarop een "
    "geluid door een abstract patroon wordt weergegeven. De achterzijde toont de "
    "bijbehorende beweging."
)
PROEFTEKSTEN = {"T08": P_T08, "T15": P_T15, "T17": P_T17, "T20": P_T20}

REDEN_CITAAT = "sluitend aanhalingsteken"
REDEN_CITAAT_HOOFD = "binnen een ingesloten citaat"
REDEN_LIJSTVERVOLG = "na een opsomming"


# (id, tekst, [(soort, teken op positie, deel van de passage, deel van de
# reden)]) — elke verwachte grens met positie, passage en reden; geen andere.
GEVALLEN = [
    # ── 1. Lijstcontext ─────────────────────────────────────────────────
    ("T15", P_T15, []),
    ("lijst-minimaal", "lagen:\n- bovenlaag\n- onderlaag", []),
    ("lijst-drie-leden", "lagen:\n- bovenlaag\n- tussenlaag\n- onderlaag", []),
    # Behoud: puntkomma na het lid was al één formulering.
    ("lijst-puntkomma", "lagen:\n- bovenlaag;\n- onderlaag", []),
    # Behoud: geen inleidende dubbele punt, geen vrijstelling.
    (
        "lijst-oningeleid",
        "lagen\n- bovenlaag\n- onderlaag",
        [
            ("onzeker", "\n", "lagen ↵ - bovenlaag", "opsommingsteken"),
            ("onzeker", "\n", "bovenlaag ↵ - onderlaag", "opsommingsteken"),
        ],
    ),
    # Behoud: een lege regel onderbreekt het blok.
    (
        "lijst-lege-regel",
        "lagen:\n- bovenlaag\n\n- onderlaag",
        [
            ("onzeker", "\n", "bovenlaag ↵ - onderlaag", "alinea-overgang"),
            ("onzeker", "\n", "bovenlaag ↵ - onderlaag", "opsommingsteken"),
        ],
    ),
    # Tekst tussen de leden onderbreekt het blok: zij zelf en het lid daarna
    # blijven onzeker.
    (
        "lijst-tussentekst",
        "lagen:\n- bovenlaag\ntussentekst\n- onderlaag",
        [
            ("onzeker", "\n", "bovenlaag ↵ tussentekst", REDEN_LIJSTVERVOLG),
            ("onzeker", "\n", "tussentekst ↵ - onderlaag", "opsommingsteken"),
        ],
    ),
    # Zelfstandige vervolgtekst na het blok: niet vrijgesteld.
    (
        "lijst-vervolgtekst",
        "lagen:\n- bovenlaag\n- onderlaag\nDe kaart ligt klaar",
        [("onzeker", "\n", "onderlaag ↵ De kaart", REDEN_LIJSTVERVOLG)],
    ),
    (
        "lijst-een-lid-vervolgtekst",
        "lagen:\n- bovenlaag\nDe kaart ligt klaar",
        [("onzeker", "\n", "bovenlaag ↵ De kaart", REDEN_LIJSTVERVOLG)],
    ),
    (
        "lijst-alinea-na-blok",
        "lagen:\n- bovenlaag\n- onderlaag\n\nDe kaart ligt klaar",
        [("onzeker", "\n", "onderlaag ↵ De kaart", "alinea-overgang")],
    ),
    # Behoud: een werkelijk zinseindteken in een lid blijft beoordeeld.
    (
        "lijst-zinseindteken",
        "lagen:\n- bovenlaag.\n- onderlaag",
        [("onzeker", ".", "bovenlaag. - onderlaag", "geen zinsbegin")],
    ),
    (
        "lijst-zinseindteken-hoofdletter",
        "lagen:\n- De bovenlaag is ruw. Hij slijt.\n- onderlaag",
        [
            ("zeker", ".", "ruw. Hij slijt", "nieuw zinsbegin"),
            ("onzeker", ".", "slijt. - onderlaag", "geen zinsbegin"),
        ],
    ),
    # ── 2. Citaatslot gevolgd door een scheidingsteken ──────────────────
    (
        "T17",
        P_T17,
        [("onzeker", "!", "‘kom terug!’, dat verschijnt", REDEN_CITAAT)],
    ),
    (
        "T20",
        P_T20,
        [
            ("onzeker", "?", "‘Wie luistert?’, waarop een geluid", REDEN_CITAAT),
            ("zeker", ".", "weergegeven. De achterzijde", "nieuw zinsbegin"),
        ],
    ),
    (
        "citaat-komma",
        "bord met de tekst ‘kom terug!’, dat verschijnt",
        [("onzeker", "!", "terug!’, dat verschijnt", REDEN_CITAAT)],
    ),
    (
        "citaat-puntkomma",
        "bord met de tekst ‘kom terug!’; de lamp brandt",
        [("onzeker", "!", "terug!’; de lamp", REDEN_CITAAT)],
    ),
    (
        "citaat-dubbelepunt",
        "bord met de tekst ‘kom terug!’: de lamp brandt",
        [("onzeker", "!", "terug!’: de lamp", REDEN_CITAAT)],
    ),
    (
        "citaat-punt-komma",
        "bord met de tekst “Gereed.”, dat verschijnt",
        [("onzeker", ".", "“Gereed.”, dat verschijnt", REDEN_CITAAT)],
    ),
    # Hoofdletter na de komma: de bestaande route voor een teken binnen een
    # citaat, zoals zonder komma; nooit zeker.
    (
        "citaat-komma-hoofdletter",
        "bord met de tekst ‘kom terug!’, Dat verschijnt",
        [("onzeker", "!", "terug!’, Dat verschijnt", REDEN_CITAAT_HOOFD)],
    ),
    # Correctiereview v2 (R2): zonder spatie na het scheidingsteken dezelfde
    # overgang; een ontbrekende spatie bewijst geen samenhang. Passage zonder
    # ingevoegde spatie, positie op het slotteken.
    (
        "citaat-komma-zonder-spatie",
        "bord met de tekst ‘kom terug!’,dat verschijnt",
        [("onzeker", "!", "terug!’,dat verschijnt", REDEN_CITAAT)],
    ),
    (
        "citaat-puntkomma-zonder-spatie",
        "bord met de tekst ‘kom terug!’;de lamp brandt",
        [("onzeker", "!", "terug!’;de lamp", REDEN_CITAAT)],
    ),
    (
        "citaat-dubbelepunt-zonder-spatie",
        "bord met de tekst ‘kom terug!’:de lamp brandt",
        [("onzeker", "!", "terug!’:de lamp", REDEN_CITAAT)],
    ),
    (
        "citaat-punt-komma-zonder-spatie",
        "bord met de tekst “Gereed.”,dat verschijnt",
        [("onzeker", ".", "“Gereed.”,dat verschijnt", REDEN_CITAAT)],
    ),
    (
        "citaat-komma-hoofdletter-zonder-spatie",
        "bord met de tekst ‘kom terug!’,Dat verschijnt",
        [("onzeker", "!", "terug!’,Dat verschijnt", REDEN_CITAAT_HOOFD)],
    ),
    (
        "T20-zonder-spatie",
        P_T20.replace("’, waarop", "’,waarop"),
        [
            ("onzeker", "?", "‘Wie luistert?’,waarop een geluid", REDEN_CITAAT),
            ("zeker", ".", "weergegeven. De achterzijde", "nieuw zinsbegin"),
        ],
    ),
    # Behoud: zonder slotteken, interne punctuatie, haakjes.
    ("citaat-zonder-slotteken", "bord met de tekst ‘kom terug’, dat verschijnt", []),
    ("citaat-zonder-slotteken-zonder-spatie", "bord met de tekst ‘kom terug’,dat", []),
    ("citaat-intern", "bord met de tekst ‘Klaar. Ga door’, dat verschijnt", []),
    ("citaat-intern-zonder-spatie", "bord met de tekst ‘Klaar. Ga door’,dat", []),
    ("haakjes-afkorting-komma", "bord (zie hfst. 3), dat verschijnt", []),
    (
        "haakjes-slot-komma",
        "bord (Stop!), dat verschijnt",
        [("onzeker", "!", "(Stop!)", "haakjesdeel")],
    ),
    # ── 3. Afkorting vóór een voorbeeldcode ─────────────────────────────
    ("T08", P_T08, [("zeker", ".", "R7. De laatste positie", "nieuw zinsbegin")]),
    ("code-slot", "tekenreeks, bijv. R7.", []),
    ("code-einde", "tekenreeks, bijv. R7", []),
    # Correctiereview v2 (R3): alleen 'bijv.' (= bijvoorbeeld) kondigt zelf een
    # voorbeeld aan. Een onbekende gestippelde afkorting of een andere
    # afkorting bewijst geen voorbeeldcontext: onzeker, zoals op /8.
    (
        "onbekende-afkorting-code",
        "houder volgens q.z. AB-12.",
        [
            (
                "onzeker",
                ".",
                "volgens q.z. AB-12.",
                "afkorting gevolgd door een hoofdletter",
            )
        ],
    ),
    (
        "onbekende-afkorting-code-einde",
        "houder volgens q.z. AB-12",
        [
            (
                "onzeker",
                ".",
                "volgens q.z. AB-12",
                "afkorting gevolgd door een hoofdletter",
            )
        ],
    ),
    (
        "andere-afkorting-code",
        "houder, ca. R7.",
        [("onzeker", ".", "ca. R7.", "afkorting gevolgd door een hoofdletter")],
    ),
    (
        "bv-code",
        "houder, bv. R7.",
        [("onzeker", ".", "bv. R7.", "afkorting gevolgd door een hoofdletter")],
    ),
    # Negatieve tegenhangers: blijven onzeker.
    (
        "code-met-vervolg",
        "tekenreeks, bijv. R7 bevat een cijfer",
        [("onzeker", ".", "bijv. R7 bevat", "afkorting gevolgd door een hoofdletter")],
    ),
    (
        "code-met-komma",
        "tekenreeks, bijv. R7, R8 en R9",
        [("onzeker", ".", "bijv. R7, R8", "afkorting gevolgd door een hoofdletter")],
    ),
    (
        "hoofdletterwoord",
        "tekenreeks, bijv. De kaart ligt klaar",
        [("onzeker", ".", "bijv. De kaart", "afkorting gevolgd door een hoofdletter")],
    ),
    (
        "code-zonder-cijfer",
        "tekenreeks, bijv. NVR.",
        [("onzeker", ".", "bijv. NVR.", "afkorting gevolgd door een hoofdletter")],
    ),
    (
        "code-met-kleine-letter",
        "tekenreeks, bijv. Rood7.",
        [("onzeker", ".", "bijv. Rood7.", "afkorting gevolgd door een hoofdletter")],
    ),
    (
        "mogelijk-zinslot-code",
        "tekenreeks, enz. R7.",
        [("onzeker", ".", "enz. R7.", "ook een zin kan afsluiten")],
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


def test_zonder_grenzen_geeft_zinsstructuur_pass():
    delen = {p["id"]: p["status"] for p in regeluitkomst(segmenteer(P_T15))["parts"]}
    assert delen == {
        "zinsstructuur": "pass",
        "compactheid": "review_required",
        "begrijpelijkheid": "review_required",
    }


# ── Binding aan de afgeronde proef (alleen lezen) ───────────────────────


def _proefcases(naam: str) -> dict[str, dict]:
    data = json.loads((PROEF / naam).read_text(encoding="utf-8"))
    cases = data["cases"] if isinstance(data, dict) else data
    return {case["id"]: case for case in cases}


def test_proefbinding_teksten_ongewijzigd():
    gevallen = _proefcases("t24-gevallen-v1.json")
    for gid, tekst in PROEFTEKSTEN.items():
        assert gevallen[gid]["tekst"] == tekst


def _zinsstatus(seg) -> str:
    if seg.zekere_grenzen:
        return "fail"
    if seg.onzekere_grenzen or seg.zonder_formulering is not None:
        return "review_required"
    return "pass"


@pytest.mark.parametrize("gid", sorted(PROEFTEKSTEN))
def test_ontwikkelregressie_volgt_adjudicatie(gid):
    """Automatische zinsstatus en grenspassages volgen de verzegelde
    adjudicatie; de labels worden gelezen, niet overschreven."""
    case = _proefcases("t24-adjudicatie-v1.json")[gid]
    seg = segmenteer(PROEFTEKSTEN[gid])
    assert _zinsstatus(seg) == case["sentence_status"]
    zeker = [g.passage for g in seg.zekere_grenzen]
    onzeker = [g.passage for g in seg.onzekere_grenzen]
    for grens in case["boundaries"]:
        passages = zeker if grens["expected"] == "zeker" else onzeker
        assert any(grens["passage"] in p for p in passages), (grens, seg)
    if case["boundary_passage"]:
        assert any(case["boundary_passage"] in p for p in zeker + onzeker), seg


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


OPEN = {"compactheid": "review_required", "begrijpelijkheid": "review_required"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tekst", "status", "delen"),
    [
        pytest.param(P_T15, "review_required", {"zinsstructuur": "pass"}, id="T15"),
        pytest.param(
            P_T17,
            "review_required",
            {"zinsgrens_onzeker_1": "review_required"},
            id="T17",
        ),
        pytest.param(
            P_T20,
            "fail",
            {"zinsgrens_1": "fail", "zinsgrens_onzeker_1": "review_required"},
            id="T20",
        ),
        pytest.param(P_T08, "fail", {"zinsgrens_1": "fail"}, id="T08"),
    ],
)
async def test_service_beide_laadpaden(svc, tekst, status, delen):
    res = await svc.validate_definition(
        begrip="object", text=tekst, ontologische_categorie=None, context={}
    )
    assert res["rule_statuses"]["INT-01"] == status
    assert "INT-01" not in res["passed_rules"]
    detail = res["rule_results"]["INT-01"]
    assert detail["contract_version"] == CONTRACTVERSIE
    assert {p["id"]: p["status"] for p in detail["parts"]} == {**delen, **OPEN}


@pytest.mark.parametrize("gid", sorted(PROEFTEKSTEN))
def test_uitkomst_onder_contract_8_geldt_niet_als_actueel(gid):
    tekst = PROEFTEKSTEN[gid]
    oud = dict(bouw_beoordeling(tekst, 1), contract_version="def770-int01/8")
    gelezen = lees_beoordeling(oud, tekst)
    assert gelezen["applied"] is False
    assert "contractversie" in gelezen["applied_reason"]


def test_contractversie_is_9_na_citaatcorrectie():
    """/8 (citaatbeleid) is proefbron van effectproeven-citaatbeleid-20260925-v1.
    Deze correctie verandert de runtime-interpretatie (lijstblok, citaatslot met
    scheidingsteken, voorbeeldcode na afkorting), dus /8 → /9."""
    assert CONTRACTVERSIE == "def770-int01/9"
