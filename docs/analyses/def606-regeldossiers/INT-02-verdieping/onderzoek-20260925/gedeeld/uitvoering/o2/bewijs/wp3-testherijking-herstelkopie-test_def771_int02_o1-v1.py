"""DEF-771 WP3: INT-02-passagehulp (O1), S1-leeshulp en niet-uitgevoerd.

Besluiten B2/B3 (25 september 2026): INT-02 blijft een menselijke
beoordeling (`review_required`, geen cijfer). De reden draagt de toetsvraag,
per passage de exacte neutrale O1-vraag met citaat en positie, en zonder
signaal de exacte waarschuwing. Lege kern, los termlabel of ontbrekende
context geeft `not_evaluated` met de exacte NE-melding. De verwachte teksten
worden rechtstreeks uit synthese v5 §4 gelezen.

Casusteksten: A-P1 `p1-invoer.json` (C04, C13, C23), B-P1 `proeven-b-v1.py`
(C50, C54, C56), C1 `proef-c1-verwachtingen.json` (C83), register v5 (C02,
C59, C105) en drie synthetische gevallen uit het goedgekeurde WP3-voorstel.
Wat dit niet bewijst: een juist inhoudelijk oordeel of bruikbaarheid van de
signalen voor een reviewer.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.evaluators.base import EvaluationDeps
from services.validation.evaluators.judgment_review import JudgmentReviewEvaluator
from services.validation.interfaces import CONTRACT_VERSION, ValidationContext
from services.validation.modular_validation_service import ModularValidationService
from services.validation.result_contract import neem_contractvelden_over
from services.validation.types_internal import EvaluationContext
from tests.fixtures.def772_fakes import FakeInt03Assessor
from toetsregels.manager import get_toetsregel_manager
from toetsregels.runtime_contract import RequiredInput, ResultStatus, build_rule_record

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
_SYN = (
    ROOT / "docs/analyses/def606-regeldossiers/INT-02-verdieping"
    "/onderzoek-20260925/gedeeld/gezamenlijke-synthese-v5.md"
).read_text(encoding="utf-8")
HULP, ZONDER_SIGNAAL = re.findall(
    r'"(INT-02 — Nog te beoordelen\.[^"]+)"',
    next(r for r in _SYN.splitlines() if r.startswith("**Reviewerhulp (O1")),
)
NE = next(m for m in re.findall(r'"(INT-02 — [^"]+)"', _SYN) if "Niet uitg" in m)
RUW = json.loads((ROOT / "src/toetsregels/regels/INT-02.json").read_text("utf-8"))
INT02 = build_rule_record("INT-02", RUW)
CONTEXT = {"organisatorische_context": ["Synthetisch loket"]}

C02 = "transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken."
C04 = "Getal dat even is indien het zonder rest door twee deelbaar is."
C13 = "besluit waarmee de bevoegde autoriteit een vergunning intrekt wanneer zij dat na afweging van de belangen van de houder evenredig acht."
C50 = "Persoon die als stelselmatige dader geldt indien hij in de vijf jaar voorafgaand aan het laatste feit drie maal wegens een misdrijf onherroepelijk is veroordeeld."
C54 = "Lid dat stemgerechtigd is alleen als het vóór 1 januari is ingeschreven."
C59 = "beslisregel: Algoritme waarvoor oordeelsvorming nodig is."
C83 = "passende maatregel: maatregel die de rechter naar eigen inzicht oplegt wanneer hij dat redelijk acht"
C105 = "De medewerker laat de aanvrager toe."
BEVOEGDHEID = "Bevoegdheid waarbij de bevoegde instantie naar eigen inzicht kan besluiten welke maatregel passend is."
PLICHT = "Verplichting die een partij moet nakomen."
FUNCTIE = "Voorwerp dat dient als ondersteuning."
# R1 (review WP5): een tussenzin, opsomming of ingebed criterium mag de
# dragende zin niet afkappen.
TUSSENZIN = "Handeling die moet, na toestemming van de rechter, worden verricht."
OPSOMMING = (
    "Aanvraag die moet worden beoordeeld op: volledigheid, juistheid en tijdigheid."
)
INGEBED = (
    "Persoon die, indien het inkomen lager is dan de grens, recht heeft op een toeslag."
)

S1 = [
    r"\bvan\s+oordeel\s+is\b",
    r"\bnaar\s+eigen\s+inzicht\b",
    r"\bredelijk\s+acht\b",
    r"\bkan\b[^.!?;\n]*\bbesluiten\b",
    r"\bmoet\b",
    r"\bdient\s+te\b",
]
PASSAGE = re.compile(r"Beschrijft de passage '(.+?)' een kenmerk", re.DOTALL)
POSITIE = re.compile(r"Positie in de getoetste kern: (\d+)–(\d+) ")


def _evalueer(tekst, *, context=True, raw=None):
    ctx = EvaluationContext.from_params(text=raw or tekst, cleaned=tekst)
    inputs = {RequiredInput.DEFINITION_TEXT}
    if context:
        inputs.add(RequiredInput.CONTEXT_LISTS)
    deps = EvaluationDeps(support=None, available_inputs=frozenset(inputs))
    return JudgmentReviewEvaluator().evaluate(INT02, ctx, deps)


def _signalen(uitkomst):
    return list(uitkomst.metadata.get("signals", []))


def _passages(uitkomst, kern):
    reden = uitkomst.reason or ""
    paren = list(zip(PASSAGE.findall(reden), POSITIE.findall(reden), strict=True))
    for passage, (start, einde) in paren:
        assert kern[int(start) : int(einde)] == passage
    return [(p, int(s), int(e)) for p, (s, e) in paren]


def test_record_s1_en_leeshulp():
    assert RUW["herkenbaar_patronen"][:7] == [
        r"\bindien\b",
        r"\bmits\b",
        r"\balleen als\b",
        r"\btenzij\b",
        r"\bvoor zover\b",
        r"\bop voorwaarde dat\b",
        r"\bin geval dat\b",
    ]
    assert RUW["herkenbaar_patronen"][7:] == S1
    assert "niet normatief" in RUW["signaalbeleid"]
    assert RUW["runtime_contract"]["required_inputs"] == [
        "definition_text",
        "context_lists",
    ]


@pytest.mark.parametrize(
    ("tekst", "signalen", "passage"),
    [
        (C04, [r"\bindien\b"], C04[:-1]),
        (C50, [r"\bindien\b"], C50[:-1]),
        (C54, [r"\balleen als\b"], C54[:-1]),
        # Het termlabel hoort bij de dragende zin (R1: geen ':'-grens).
        (C02, [r"\bmoet\b"], C02[:-1]),
        (C83, S1[1:3], C83),
        (BEVOEGDHEID, S1[1:2] + S1[3:4], BEVOEGDHEID[:-1]),
        (PLICHT, [r"\bmoet\b"], PLICHT[:-1]),
        (TUSSENZIN, [r"\bmoet\b"], TUSSENZIN[:-1]),
        (OPSOMMING, [r"\bmoet\b"], OPSOMMING[:-1]),
        (INGEBED, [r"\bindien\b"], INGEBED[:-1]),
    ],
)
def test_signaal_geeft_neutrale_vraag_met_passage_en_positie(tekst, signalen, passage):
    uitkomst = _evalueer(tekst)
    assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
    assert uitkomst.score is None
    assert sorted(_signalen(uitkomst)) == sorted(signalen)
    reden = uitkomst.reason or ""
    assert reden.startswith(f"INT-02 — Toetsvraag: {INT02.get('toetsvraag')} ")
    assert HULP.replace("{zinsdeel}", passage) in reden
    assert [p for p, _, _ in _passages(uitkomst, tekst)] == [passage]
    assert "nulgebaseerd, einde exclusief" in reden
    assert ZONDER_SIGNAAL not in reden


@pytest.mark.parametrize("tekst", [C13, C59, C105, FUNCTIE])
def test_zonder_signaal_exacte_waarschuwing(tekst):
    uitkomst = _evalueer(tekst)
    assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
    assert _signalen(uitkomst) == []
    assert uitkomst.reason == (
        f"INT-02 — Toetsvraag: {INT02.get('toetsvraag')} {ZONDER_SIGNAAL}"
    )


def test_markergrenzen_kan_besluiten_en_dient_te():
    assert (
        _signalen(_evalueer("Orgaan dat kan optreden. Het college mag besluiten."))
        == []
    )
    assert _signalen(_evalueer("Taak die de ambtenaar dient te verrichten.")) == [
        r"\bdient\s+te\b"
    ]


def test_herhaalde_passage_blijft_onderscheidbaar():
    # Binnen één volledige zin delen de markers één vraag (R1).
    tekst = "handeling die moet volgen, handeling die moet volgen"
    assert _passages(_evalueer(tekst), tekst) == [(tekst, 0, 52)]
    # In verschillende zekere zinnen houdt elke passage een eigen positie.
    tekst = "Handeling die moet volgen. Handeling die moet volgen."
    assert _passages(_evalueer(tekst), tekst) == [
        ("Handeling die moet volgen", 0, 25),
        ("Handeling die moet volgen", 27, 52),
    ]


def test_onzekere_grens_citeert_de_volledige_kern():
    tekst = "Handeling die moet volgen\nen verder gaat."
    assert [p for p, _, _ in _passages(_evalueer(tekst), tekst)] == [tekst[:-1]]


def test_posities_in_getoetste_kern_zonder_broncitaat():
    uitkomst = _evalueer(C04, raw=f"Definitie: {C04}")
    assert _passages(uitkomst, C04) == [(C04[:-1], 0, len(C04) - 1)]
    assert "Definitie:" not in (uitkomst.reason or "")
    assert "afwijkt van de aangeleverde tekst" in (uitkomst.reason or "")


@pytest.mark.parametrize(
    ("tekst", "context", "grond"),
    [
        ("", True, "kern"),
        ("Toegang:", True, "kern"),
        (C50, False, "context"),
        ("", False, "kern en context"),
    ],
)
def test_evaluator_niet_uitgevoerd(tekst, context, grond):
    uitkomst = _evalueer(tekst, context=context)
    assert uitkomst.status is ResultStatus.NOT_EVALUATED
    assert uitkomst.reason == NE.replace("{kern/context}", grond)


async def _service(tekst, context):
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    resultaat = await svc.validate_definition(
        begrip="proef", text=tekst, context=context
    )
    review = {r["rule_id"]: r for r in resultaat["review_required"]}
    ctx = EvaluationContext.from_params(text=tekst, cleaned=tekst, metadata=context)
    uitkomst = svc._evaluate_rule("INT-02", ctx, svc._snapshot)
    return resultaat["rule_statuses"]["INT-02"], review.get("INT-02"), uitkomst


async def _publiek(tekst, context):
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    return await svc.validate_definition(begrip="proef", text=tekst, context=context)


@pytest.mark.parametrize(
    ("casus", "tekst", "context", "grond"),
    [
        ("C06", "", CONTEXT, "kern"),
        ("C23", "Toegang:", CONTEXT, "kern"),
        ("C56", C50, {}, "context"),
    ],
)
async def test_service_niet_uitgevoerd(casus, tekst, context, grond):
    status, item, uitkomst = await _service(tekst, context)
    assert status == ResultStatus.NOT_EVALUATED.value, casus
    assert item is None
    assert uitkomst.reason == NE.replace("{kern/context}", grond)


async def test_service_met_context_geeft_passagehulp_zonder_oordeel():
    status, item, _ = await _service(C50, CONTEXT)
    assert status == ResultStatus.REVIEW_REQUIRED.value
    assert HULP.replace("{zinsdeel}", C50[:-1]) in item["reason"]
    assert item["signals"] == [r"\bindien\b"]


NE_GEVALLEN = [
    ("C06", "", CONTEXT, "kern"),
    ("C23", "Toegang:", CONTEXT, "kern"),
    ("C56", C50, {}, "context"),
]
SCHEMA = json.loads(
    (
        ROOT / "docs/architectuur/contracts/schemas/validation_result.schema.json"
    ).read_text(encoding="utf-8")
)


def _valideer_rule_results(resultaat):
    # Gericht op het contractdeel: het volledige resultaat valideert op main al
    # niet (violation-codes zoals 'ESS-05' passen niet op het codepatroon).
    Draft202012Validator(SCHEMA["properties"]["rule_results"]).validate(
        json.loads(json.dumps(resultaat["rule_results"]))
    )


@pytest.mark.parametrize(("casus", "tekst", "context", "grond"), NE_GEVALLEN)
async def test_ne_reist_publiek_mee_in_rule_results(casus, tekst, context, grond):
    resultaat = await _publiek(tekst, context)
    detail = resultaat["rule_results"]["INT-02"]
    assert detail["status"] == ResultStatus.NOT_EVALUATED.value, casus
    assert detail["score"] is None and detail["fingerprint"] is None
    assert detail["contract_version"] == RUW["contractversie"]
    (onderdeel,) = detail["parts"]
    assert onderdeel["status"] == ResultStatus.NOT_EVALUATED.value
    assert onderdeel["reason"] == NE.replace("{kern/context}", grond)
    # Geen oordeel, score of reviewvraag uit een niet-uitgevoerde INT-02.
    assert "INT-02" not in resultaat["passed_rules"]
    assert all(v.get("code") != "INT-02" for v in resultaat["violations"])
    assert all(r["rule_id"] != "INT-02" for r in resultaat["review_required"])
    assert "INT-02" not in json.dumps(resultaat["acceptance_gate"])


@pytest.mark.parametrize(("casus", "tekst", "context", "grond"), NE_GEVALLEN)
async def test_ne_resultaat_past_in_schema_en_conversie(casus, tekst, context, grond):
    resultaat = await _publiek(tekst, context)
    assert CONTRACT_VERSION == "2.2.0"
    assert resultaat["version"] == CONTRACT_VERSION
    _valideer_rule_results(resultaat)
    omgezet: dict = {}
    neem_contractvelden_over(omgezet, resultaat)
    assert omgezet["rule_results"]["INT-02"] == resultaat["rule_results"]["INT-02"]


async def test_rr_boekt_geen_int02_deeluitkomst_en_andere_regels_blijven():
    met = await _publiek(C50, CONTEXT)
    zonder = await _publiek(C50, {})
    assert "INT-02" not in met["rule_results"]
    assert set(zonder["rule_results"]) - {"INT-02"} == set(met["rule_results"])
    _valideer_rule_results(met)
    _valideer_rule_results(zonder)


# Contract 2.2.0 beschrijft ook de bestaande INT-03-runtimevelden `assessment`
# (beoordelingsdocument of null) en `signals` (patroonlijst) in
# rule_results['INT-03']; andere regels krijgen die velden niet en onbekende
# velden blijven overal afgewezen (DEF-771/DEF-772, integratie met main).
RULE_RESULTS = Draft202012Validator(SCHEMA["properties"]["rule_results"])


async def _met_int03_beoordeling(scenario):
    orch = ValidationOrchestratorV2(
        ModularValidationService(get_toetsregel_manager(), None, None),
        int03_assessment_service=FakeInt03Assessor(scenario=scenario),
    )
    return await orch.validate_text(
        "proef", C50, context=ValidationContext(metadata=CONTEXT)
    )


def _fouten(rule_results):
    return list(RULE_RESULTS.iter_errors(json.loads(json.dumps(rule_results))))


@pytest.mark.parametrize("bron", ["zonder_dienst", "pass", "fail"])
async def test_int03_uitkomst_met_en_zonder_beoordeling_past_in_schema(bron):
    if bron == "zonder_dienst":
        resultaat = await _publiek(C50, CONTEXT)
        assert resultaat["rule_results"]["INT-03"]["assessment"] is None
    else:
        resultaat = await _met_int03_beoordeling(bron)
        assessment = resultaat["rule_results"]["INT-03"]["assessment"]
        assert assessment["status"] == "assessed"
    assert resultaat["rule_results"]["INT-03"]["signals"]
    assert _fouten(resultaat["rule_results"]) == []
    # INT-02 blijft een open beoordeling met passagehulp, zonder deeluitkomst.
    item = next(r for r in resultaat["review_required"] if r["rule_id"] == "INT-02")
    assert HULP.replace("{zinsdeel}", C50[:-1]) in item["reason"]
    assert "INT-02" not in resultaat["rule_results"]


@pytest.mark.parametrize(
    ("veld", "waarde"),
    [
        ("signals", "\\bdie\\b"),
        ("signals", [1]),
        ("signals", None),
        ("assessment", "beoordeeld"),
        ("assessment", ["assessed"]),
    ],
)
async def test_int03_velden_hebben_expliciete_typen(veld, waarde):
    resultaat = await _met_int03_beoordeling("pass")
    rule_results = resultaat["rule_results"]
    assert _fouten(rule_results) == []
    rule_results["INT-03"][veld] = waarde
    assert _fouten(rule_results)


async def test_onbekende_velden_en_int03_velden_elders_blijven_afgewezen():
    met = await _met_int03_beoordeling("pass")
    ne = await _publiek(C50, {})
    assert _fouten(met["rule_results"]) == []
    assert _fouten(ne["rule_results"]) == []
    for rule_results, regel, veld, waarde in (
        (met["rule_results"], "INT-03", "onbekend", 1),
        (ne["rule_results"], "INT-02", "signals", []),
        (ne["rule_results"], "INT-02", "assessment", None),
    ):
        kopie = json.loads(json.dumps(rule_results))
        kopie[regel][veld] = waarde
        assert _fouten(kopie), (regel, veld)
    # De INT-02-NE-uitkomst zelf is ongewijzigd.
    (onderdeel,) = ne["rule_results"]["INT-02"]["parts"]
    assert onderdeel["reason"] == NE.replace("{kern/context}", "context")
