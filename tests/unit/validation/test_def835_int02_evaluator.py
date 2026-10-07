"""DEF-835 WP3: INT-02 O2-evaluator `decision_rule_assessment` (eerst rood).

Specificeert de pure, synchrone evaluator die een getypeerd WP1-
beoordelingsdocument (`domain.int02.contract.Beoordelingsdocument`) toepast op
de actuele invoer en de expliciete actuele configuratie. Geen modelaanroep:
de evaluator beslist niets zelf, maar gebruikt de bestaande WP1-controle
`toets_actualiteit` (NE → nog niet beoordeeld → fout/niet herleidbaar →
historisch → bewaard oordeel).

Metadata-interface (voorstel WP3, zie wp3-claude-rood-verslag-v1.md):

- `record_text` (str): de exacte kern; zonder `record_text` de aangeleverde
  tekst (`raw_text`), zoals INT-03;
- `organisatorische_context`, `juridische_context`, `wettelijke_basis`:
  lijst/tuple van teksten; afwezig of None = leeg;
- `int02_bedoeling`: tekst of None/afwezig (expliciet onbekend);
- `int02_bronnen`: lijst van `{"id", "tekst"}`; afwezig of None = geen;
- `int02_configuratie`: `domain.int02.contract.Configuratie` (actueel);
- `int02_document`: `domain.int02.contract.Beoordelingsdocument` of None.

Publieke deeluitkomst in `metadata["rule_result"]` (contract 2.3.0): score
null, `contract_version` = WP1-contractversie, precies één onderdeel met de
exacte WP1-melding, `assessment` (het document, alleen als `toets_actualiteit`
het als actueel of historisch heeft aanvaard; anders null), `signals`
(recordpatronen op de actuele kern; leeshulp) en `review.actuality`
(`current` / `historical` / `not_assessed`; null bij NE en fout).

Het actieve `INT-02.json` blijft O1 (`judgment_review`); de tests gebruiken
een tijdelijk record via de bestaande registry. Wat dit niet bewijst: de
volledige appketen (ModularValidationService-boekhouding, container, UI,
opslag; WP5) of enige semantische modelkwaliteit.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import importlib
import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from domain.int02.contract import (
    CONTRACTVERSIE,
    MELDING_E,
    MELDING_HISTORISCH,
    MELDING_NE,
    MELDING_NIET_BEOORDEELD,
    Beoordelingsdocument,
    Configuratie,
    Uitvoering,
    beoordeel,
    bereken_binding,
    maak_invoer,
    toets_actualiteit,
)
from services.validation.evaluators import build_default_registry
from services.validation.evaluators.base import EvaluationDeps, EvaluationOutcome
from services.validation.evaluators.judgment_review import JudgmentReviewEvaluator
from services.validation.evaluators.pronoun_reference_assessment import (
    ADVISORY_SEVERITY,
    ADVISORY_SEVERITY_LEVEL,
)
from services.validation.evaluators.registry import get_default_registry
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import (
    AutomationStatus,
    EvaluatorType,
    Executability,
    RequiredInput,
    ResultStatus,
    RuleContractError,
    ScorePolicy,
    build_rule_record,
    load_root_contract_policy,
)

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
RUW = json.loads((ROOT / "src/toetsregels/regels/INT-02.json").read_text("utf-8"))

MODULE = "services.validation.evaluators.decision_rule_assessment"
KLASSE = "DecisionRuleAssessmentEvaluator"
WAARDE = "decision_rule_assessment"


# ---------------------------------------------------------------------------
# Toegang tot het (nog) ontbrekende gedrag: een testfailure, geen collectiefout
# ---------------------------------------------------------------------------


def _module():
    try:
        return importlib.import_module(MODULE)
    except ModuleNotFoundError as exc:
        pytest.fail(f"evaluatormodule {MODULE} ontbreekt: {exc}")


def _soort() -> EvaluatorType:
    try:
        return EvaluatorType(WAARDE)
    except ValueError:
        pytest.fail(f"EvaluatorType kent {WAARDE!r} niet")


def _evaluator():
    klasse = getattr(_module(), KLASSE, None)
    assert klasse is not None, f"{MODULE} definieert {KLASSE} niet"
    return klasse()


def _o2_data(patronen: list[str] | None = None) -> dict:
    """Tijdelijk O2-record: kopie van het actieve record, nooit het bestand zelf."""
    data = copy.deepcopy(RUW)
    data["runtime_contract"].update(
        {"evaluator": WAARDE, "automation_status": "automated"}
    )
    if patronen is not None:
        data["herkenbaar_patronen"] = list(patronen)
    return data


def _o2_record(patronen: list[str] | None = None):
    try:
        return build_rule_record("INT-02", _o2_data(patronen))
    except RuleContractError as exc:
        pytest.fail(f"tijdelijk O2-record is niet te bouwen: {exc}")


class _StubSupport:
    def severity_for(self, rule):
        return "error"

    def severity_level_for(self, rule):
        return "critical"

    def build_suggestion(self, code, rule, text, ctx, *, reason, details=None):
        return "stub"


def _deps() -> EvaluationDeps:
    return EvaluationDeps(
        support=_StubSupport(),
        available_inputs=frozenset(RequiredInput),
        pattern_cache={},
    )


# ---------------------------------------------------------------------------
# Synthetische invoer en handmatig ingevulde beoordelaarsuitvoer (geen model)
# ---------------------------------------------------------------------------

TERM = "proefbegrip"
KERN_PASS = "Geheel getal dat zonder rest door twee deelbaar is."
KERN_PLICHT = "Verplichting die een partij moet nakomen."
KERN_VOORSCHRIFT = (
    "Aanvraag die de behandelaar moet afwijzen bij een ontbrekende bijlage."
)
KERN_DISCRETIE = (
    "Besluit waarmee de bevoegde autoriteit een aanvraag afwijst, tenzij zij van "
    "oordeel is dat de aanvrager daardoor onevenredig zou worden benadeeld."
)
KERN_C105 = "De medewerker laat de aanvrager toe."
KERN_OPEN = (
    "Besluit waarmee de bevoegde autoriteit een vergunning intrekt wanneer zij dat "
    "na afweging van de belangen van de houder evenredig acht."
)
KERN_NVT = "Zie artikel 3 van de Synthetische Wet."
CONTEXT = {
    "organisatorische_context": ["Synthetisch loket"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
BRONNEN = [{"id": "B1", "tekst": "Synthetische bronpassage."}]
BEDOELING = "Bevestigde synthetische bedoeling."


def _sha(tekst: str) -> str:
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


CONFIG = Configuratie(
    normhash=_sha("def835-wp3-testnorm"),
    promptversie="def835-int02-prompt/1",
    routeringshash=_sha("def835-wp3-routering"),
    provider="synthetisch",
    model="synthetisch-model",
)
VOLTOOID = Uitvoering(actor="ai", status="completed", tijdstip="2026-09-27T00:00:00Z")


def _passage(kern: str, citaat: str, functie: str) -> dict:
    # Contract /2: geen posities in de modeluitvoer; het citaat is uniek.
    assert kern.count(citaat) == 1
    return {
        "quote": citaat,
        "function": functie,
        "ground": {"field": "kern", "ref": None, "quote": None},
    }


def _respons(verdict: str, passages: list[dict], **over: Any) -> dict:
    return {
        "verdict": verdict,
        "passages": passages,
        "reason": over.pop("reason", "Synthetische onderbouwing."),
        "question": over.pop("question", None),
        "uncertainty": over.pop("uncertainty", "none"),
        "scope_reason": over.pop("scope_reason", None),
        "coverage": over.pop("coverage", "complete"),
    }


#: scenario -> (kern, beoordelaarsuitvoer, verwachte status)
SCENARIO = {
    "pass": (
        KERN_PASS,
        _respons(
            "pass", [_passage(KERN_PASS, "zonder rest door twee deelbaar", "criterion")]
        ),
        ResultStatus.PASS,
    ),
    "pass_plicht": (
        KERN_PLICHT,
        _respons(
            "pass", [_passage(KERN_PLICHT, "een partij moet nakomen", "criterion")]
        ),
        ResultStatus.PASS,
    ),
    "fail": (
        KERN_VOORSCHRIFT,
        _respons(
            "fail",
            [
                _passage(
                    KERN_VOORSCHRIFT,
                    "moet afwijzen bij een ontbrekende bijlage",
                    "actor_prescription",
                )
            ],
        ),
        ResultStatus.FAIL,
    ),
    "fail_discretie": (
        KERN_DISCRETIE,
        _respons(
            "fail",
            [
                _passage(
                    KERN_DISCRETIE,
                    "tenzij zij van oordeel is dat de aanvrager daardoor onevenredig "
                    "zou worden benadeeld",
                    "discretionary_decision_rule",
                )
            ],
        ),
        ResultStatus.FAIL,
    ),
    "fail_zonder_signaal": (
        KERN_C105,
        _respons(
            "fail",
            [_passage(KERN_C105, "laat de aanvrager toe", "actor_prescription")],
        ),
        ResultStatus.FAIL,
    ),
    "insufficient": (
        KERN_OPEN,
        _respons(
            "insufficient_information",
            [
                _passage(
                    KERN_OPEN,
                    "na afweging van de belangen van de houder evenredig acht",
                    "unclear",
                )
            ],
            reason="De bevestigde bedoeling ontbreekt.",
            question=(
                "Is de evenredigheidsafweging een kenmerk van het besluit of een "
                "voorschrift aan de autoriteit?"
            ),
            uncertainty="decisive",
            coverage="partial",
        ),
        ResultStatus.REVIEW_REQUIRED,
    ),
    "not_applicable": (
        KERN_NVT,
        _respons(
            "not_applicable",
            [],
            scope_reason="De tekst is een bronverwijzing zonder definitiekern",
            coverage="none",
        ),
        ResultStatus.NOT_APPLICABLE,
    ),
}


def _invoer(
    kern: str,
    *,
    begrip: str = TERM,
    context: dict | None = None,
    bedoeling: str | None = None,
    bronnen: list[dict] | tuple = (),
):
    context = CONTEXT if context is None else context
    return maak_invoer(
        begrip=begrip,
        kern=kern,
        bedoeling=bedoeling,
        organisatorische_context=list(context.get("organisatorische_context") or []),
        juridische_context=list(context.get("juridische_context") or []),
        wettelijke_basis=list(context.get("wettelijke_basis") or []),
        bronnen=list(bronnen),
    )


def _document(scenario: str, **invoer_over: Any) -> Beoordelingsdocument:
    kern, respons, _ = SCENARIO[scenario]
    invoer = _invoer(kern, **invoer_over)
    return beoordeel(invoer, CONFIG, copy.deepcopy(respons), VOLTOOID)


def _document_mislukt() -> Beoordelingsdocument:
    """WP1-foutdocument: transport faalde (timeout); geen oordeel."""
    uitvoering = Uitvoering(actor="ai", status="failed", foutcategorie="timeout")
    return beoordeel(_invoer(KERN_PASS), CONFIG, None, uitvoering)


def _document_niet_uitgevoerd() -> Beoordelingsdocument:
    """WP1: dienst blokkeerde vóór de aanroep; nog niet beoordeeld."""
    uitvoering = Uitvoering(actor="ai", status="not_executed")
    return beoordeel(_invoer(KERN_PASS), CONFIG, None, uitvoering)


_WEG = object()


def _metadata(kern: str, document: Any = _WEG, **over: Any) -> dict:
    md: dict[str, Any] = {
        **copy.deepcopy(CONTEXT),
        "record_text": kern,
        "int02_configuratie": CONFIG,
    }
    if document is not _WEG:
        md["int02_document"] = document
    for sleutel, waarde in over.items():
        if waarde is _WEG:
            md.pop(sleutel, None)
        else:
            md[sleutel] = waarde
    return md


def _ctx(
    md: dict,
    *,
    tekst: str | None = None,
    cleaned: str | None = None,
    begrip: str = TERM,
) -> EvaluationContext:
    ruw = md.get("record_text", "") if tekst is None else tekst
    return EvaluationContext(
        raw_text=ruw,
        cleaned_text=ruw if cleaned is None else cleaned,
        begrip=begrip,
        metadata=md,
    )


def _evalueer(md: dict, *, record=None, **ctx_over: Any) -> EvaluationOutcome:
    record = record if record is not None else _o2_record()
    return _evaluator().evaluate(record, _ctx(md, **ctx_over), _deps())


def _detail(uitkomst: EvaluationOutcome) -> dict:
    detail = uitkomst.metadata.get("rule_result")
    assert isinstance(detail, dict), "de evaluator levert geen metadata.rule_result"
    return detail


def _assert_scoreloos_met_melding(uitkomst, status: ResultStatus, melding: str):
    """Gemeenschappelijke vorm van elke O2-uitkomst (zes statussen)."""
    assert uitkomst.status is status
    assert uitkomst.score is None
    detail = _detail(uitkomst)
    assert detail["status"] == status.value
    assert detail["score"] is None
    assert detail["contract_version"] == CONTRACTVERSIE
    (onderdeel,) = detail["parts"]
    assert onderdeel["status"] == status.value
    assert onderdeel["reason"] == melding
    assert isinstance(detail["signals"], list)
    assert isinstance(detail["review"], dict)
    assert json.loads(json.dumps(detail)) == detail, "rule_result is geen JSON"
    return detail


def o2_uitkomsten() -> dict[str, EvaluationOutcome]:
    """Echte evaluatoruitkomsten voor alle zes statussen.

    Ook gebruikt door `tests/integration/contracts/test_validation_result_schema.py`,
    zodat het schema de werkelijke evaluatoruitvoer toetst en geen
    zelfbedachte losse dicts.
    """
    uitkomsten = {
        scenario: _evalueer(_metadata(SCENARIO[scenario][0], _document(scenario)))
        for scenario in ("pass", "fail", "fail_discretie", "insufficient")
    }
    uitkomsten["not_applicable"] = _evalueer(
        _metadata(KERN_NVT, _document("not_applicable"))
    )
    uitkomsten["niet_beoordeeld"] = _evalueer(_metadata(KERN_PASS))
    uitkomsten["historisch"] = _evalueer(
        _metadata(KERN_VOORSCHRIFT + " ", _document("fail"))
    )
    uitkomsten["niet_uitgevoerd"] = _evalueer(_metadata("", _document("pass")))
    uitkomsten["fout"] = _evalueer(_metadata(KERN_PASS, _document_mislukt()))
    return uitkomsten


# ---------------------------------------------------------------------------
# Registratie, root-SSOT en het actieve record
# ---------------------------------------------------------------------------


class TestRegistratie:
    def test_root_ssot_en_enum_kennen_de_nieuwe_evaluator(self):
        soort = _soort()
        policy = load_root_contract_policy()
        assert soort.value in policy.evaluators
        assert set(policy.evaluators) == {lid.value for lid in EvaluatorType}

    def test_register_lost_het_type_op_naar_de_o2_evaluator(self):
        soort = _soort()
        klasse = getattr(_module(), KLASSE, None)
        assert klasse is not None, f"{MODULE} definieert {KLASSE} niet"
        registry = build_default_registry()
        assert WAARDE in registry.registered_types()
        evaluator = registry.resolve(soort)
        assert isinstance(evaluator, klasse)
        assert evaluator.evaluator_type is soort
        assert isinstance(get_default_registry().resolve(WAARDE), klasse)

    def test_tijdelijk_record_is_geldig_scoreloos_en_via_de_registry_uitvoerbaar(
        self,
    ):
        record = _o2_record()
        assert record.evaluator is _soort()
        assert record.executability is Executability.JUDGMENT
        assert record.automation_status is AutomationStatus.AUTOMATED
        assert record.score_policy is ScorePolicy.EXCLUDED_FROM_SCORE
        assert record.counts_toward_score is False
        assert record.required_inputs == (
            RequiredInput.DEFINITION_TEXT,
            RequiredInput.CONTEXT_LISTS,
        )
        evaluator = get_default_registry().resolve(record.evaluator)
        ctx = _ctx(_metadata(KERN_PASS, _document("pass")))
        assert evaluator.evaluate(record, ctx, _deps()).status is ResultStatus.PASS

    def test_actief_int02_record_blijft_o1_en_ongewijzigd(self):
        record = build_rule_record("INT-02", RUW)
        assert record.evaluator is EvaluatorType.JUDGMENT_REVIEW
        assert record.automation_status is AutomationStatus.REVIEW_REQUIRED
        assert record.score_policy is ScorePolicy.EXCLUDED_FROM_SCORE
        assert isinstance(
            get_default_registry().resolve(record.evaluator), JudgmentReviewEvaluator
        )
        voor = copy.deepcopy(RUW)
        _o2_data()
        _o2_data(patronen=[])
        assert voor == RUW, "het tijdelijke record mag het bronrecord niet muteren"


# ---------------------------------------------------------------------------
# Puur en synchroon; WP1-controle in plaats van parallelle logica
# ---------------------------------------------------------------------------


class TestPuurEnSynchroon:
    def test_evaluate_is_synchroon_en_doet_geen_modelaanroep(self, monkeypatch):
        from services.validation import int02_assessment_service as dienst

        def verboden(*args, **kwargs):
            raise AssertionError("modelaanroep of promptopbouw in de evaluator")

        monkeypatch.setattr(dienst.Int02AssessmentService, "assess", verboden)
        monkeypatch.setattr(dienst, "bouw_int02_prompt", verboden)
        evaluator = _evaluator()
        assert not inspect.iscoroutinefunction(evaluator.evaluate)
        for md in (_metadata(KERN_PASS), _metadata(KERN_PASS, _document("pass"))):
            uitkomst = evaluator.evaluate(_o2_record(), _ctx(md), _deps())
            assert isinstance(uitkomst, EvaluationOutcome)
            assert not inspect.isawaitable(uitkomst)

    def test_wp1_toets_actualiteit_krijgt_exact_de_huidige_invoer(self, monkeypatch):
        module = _module()
        assert getattr(module, "toets_actualiteit", None) is toets_actualiteit, (
            "de evaluator hoort de bestaande WP1-controle toets_actualiteit te "
            "gebruiken, geen parallelle beoordelingslogica"
        )
        aanroepen = []

        def spion(document, invoer, configuratie):
            aanroepen.append((document, invoer, configuratie))
            return toets_actualiteit(document, invoer, configuratie)

        monkeypatch.setattr(module, "toets_actualiteit", spion)
        doc = _document("pass", bedoeling=BEDOELING, bronnen=BRONNEN)
        md = _metadata(KERN_PASS, doc, int02_bedoeling=BEDOELING, int02_bronnen=BRONNEN)
        uitkomst = _evalueer(md)
        assert uitkomst.status is ResultStatus.PASS
        [(document, invoer, configuratie)] = aanroepen
        assert document == doc
        assert invoer == _invoer(KERN_PASS, bedoeling=BEDOELING, bronnen=BRONNEN)
        assert configuratie == CONFIG

    def test_kern_is_de_exacte_recordtekst(self):
        md = _metadata(KERN_PASS, _document("pass"))
        uitkomst = _evalueer(md, tekst=f"{TERM}: {KERN_PASS}", cleaned="iets anders")
        assert uitkomst.status is ResultStatus.PASS

    def test_zonder_recordtekst_geldt_de_aangeleverde_tekst(self):
        md = _metadata(KERN_PASS, _document("pass"), record_text=_WEG)
        uitkomst = _evalueer(md, tekst=KERN_PASS, cleaned=KERN_PASS.upper())
        assert uitkomst.status is ResultStatus.PASS

    def test_afwezige_of_none_contextlijst_is_leeg(self):
        md = _metadata(
            KERN_PASS, _document("pass"), juridische_context=None, wettelijke_basis=_WEG
        )
        assert _evalueer(md).status is ResultStatus.PASS


# ---------------------------------------------------------------------------
# Actuele oordelen: pass / fail / review_required (O) / not_applicable
# ---------------------------------------------------------------------------


class TestActueelOordeel:
    @pytest.mark.parametrize(
        "scenario",
        [
            "pass",
            "pass_plicht",
            "fail",
            "fail_discretie",
            "fail_zonder_signaal",
            "insufficient",
            "not_applicable",
        ],
    )
    def test_actueel_oordeel_volgt_het_wp1_document(self, scenario):
        kern, _, status = SCENARIO[scenario]
        doc = _document(scenario)
        assert doc.status == status.value, "testopzet: WP1 moet dit oordeel aanvaarden"
        uitkomst = _evalueer(_metadata(kern, doc))
        detail = _assert_scoreloos_met_melding(uitkomst, status, doc.melding)
        assert detail["assessment"] == doc.als_dict()
        assert detail["review"]["actuality"] == "current"
        if status is ResultStatus.FAIL:
            return
        assert uitkomst.violation is None
        if status is not ResultStatus.PASS:
            assert uitkomst.reason == doc.melding

    @pytest.mark.parametrize("scenario", ["fail", "fail_discretie"])
    def test_fail_is_adviserend_zonder_cijfer_poort_of_herstel(self, scenario):
        kern, _, _ = SCENARIO[scenario]
        doc = _document(scenario)
        uitkomst = _evalueer(_metadata(kern, doc))
        assert uitkomst.status is ResultStatus.FAIL
        assert uitkomst.score is None
        violation = uitkomst.violation
        assert violation is not None
        assert violation["code"] == "INT-02"
        assert violation["message"] == doc.melding
        assert "De tekst is ongewijzigd." in violation["message"]
        assert violation["severity"] == ADVISORY_SEVERITY
        assert violation["severity_level"] == ADVISORY_SEVERITY_LEVEL
        assert violation["metadata"]["advisory"] is True
        assert "herschrijf" not in str(violation.get("suggestion") or "").lower()

    def test_onvoldoende_informatie_draagt_precies_de_ene_vraag(self):
        doc = _document("insufficient")
        uitkomst = _evalueer(_metadata(KERN_OPEN, doc))
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert doc.vraag and doc.vraag in (uitkomst.reason or "")
        assert _detail(uitkomst)["review"]["actuality"] == "current"


# ---------------------------------------------------------------------------
# Nog niet beoordeeld en historisch
# ---------------------------------------------------------------------------


class TestNietBeoordeeldEnHistorisch:
    @pytest.mark.parametrize("document", [_WEG, None], ids=["afwezig", "none"])
    def test_zonder_oordeel_open_en_nooit_pass(self, document):
        # Ook zonder enig signaalwoord in de kern: geen stil pass.
        uitkomst = _evalueer(_metadata(KERN_PASS, document))
        detail = _assert_scoreloos_met_melding(
            uitkomst, ResultStatus.REVIEW_REQUIRED, MELDING_NIET_BEOORDEELD
        )
        assert uitkomst.reason == MELDING_NIET_BEOORDEELD
        assert uitkomst.violation is None
        assert detail["assessment"] is None
        assert detail["review"]["actuality"] == "not_assessed"
        assert detail["signals"] == []

    def test_niet_uitgevoerd_wp1_document_is_nog_te_beoordelen(self):
        doc = _document_niet_uitgevoerd()
        uitkomst = _evalueer(_metadata(KERN_PASS, doc))
        detail = _assert_scoreloos_met_melding(
            uitkomst, ResultStatus.REVIEW_REQUIRED, MELDING_NIET_BEOORDEELD
        )
        assert detail["assessment"] == doc.als_dict()
        assert detail["review"]["actuality"] == "not_assessed"

    def test_zonder_actuele_configuratie_geen_actueel_oordeel(self):
        md = _metadata(KERN_PASS, _document("pass"), int02_configuratie=_WEG)
        uitkomst = _evalueer(md)
        detail = _assert_scoreloos_met_melding(
            uitkomst, ResultStatus.REVIEW_REQUIRED, MELDING_NIET_BEOORDEELD
        )
        assert detail["assessment"] is None
        assert detail["review"]["actuality"] == "not_assessed"

    HISTORISCH = [
        ("kern-witruimte", {"record_text": KERN_VOORSCHRIFT + " "}, {}),
        ("begrip", {}, {"begrip": "ander begrip"}),
        ("bedoeling", {"int02_bedoeling": BEDOELING}, {}),
        ("context", {"juridische_context": ["Bestuursrecht"]}, {}),
        ("bron", {"int02_bronnen": BRONNEN}, {}),
        (
            "normhash",
            {"int02_configuratie": dataclasses.replace(CONFIG, normhash=_sha("x"))},
            {},
        ),
        (
            "normversie",
            {
                "int02_configuratie": dataclasses.replace(
                    CONFIG, normversie="def771-int02/3"
                )
            },
            {},
        ),
        (
            "promptversie",
            {
                "int02_configuratie": dataclasses.replace(
                    CONFIG, promptversie="def835-int02-prompt/2"
                )
            },
            {},
        ),
        (
            "routeringshash",
            {
                "int02_configuratie": dataclasses.replace(
                    CONFIG, routeringshash=_sha("y")
                )
            },
            {},
        ),
        (
            "provider",
            {"int02_configuratie": dataclasses.replace(CONFIG, provider="ander")},
            {},
        ),
        (
            "model",
            {"int02_configuratie": dataclasses.replace(CONFIG, model="ander-model")},
            {},
        ),
    ]

    @pytest.mark.parametrize(
        ("veld", "metadata", "ctx"), HISTORISCH, ids=[h[0] for h in HISTORISCH]
    )
    def test_gewijzigd_bindingsveld_maakt_oordeel_historisch(self, veld, metadata, ctx):
        doc = _document("fail")
        uitkomst = _evalueer(_metadata(KERN_VOORSCHRIFT, doc, **metadata), **ctx)
        detail = _assert_scoreloos_met_melding(
            uitkomst, ResultStatus.REVIEW_REQUIRED, MELDING_HISTORISCH
        )
        # Een historische afkeur is geen actuele afkeur.
        assert uitkomst.violation is None
        assert uitkomst.reason == MELDING_HISTORISCH
        assert detail["review"]["actuality"] == "historical"
        # Het oude document blijft ongewijzigd controleerbaar.
        assert detail["assessment"] == doc.als_dict()


# ---------------------------------------------------------------------------
# Niet uitgevoerd (NE): exacte melding, oordeel genegeerd
# ---------------------------------------------------------------------------

LEGE_CONTEXT = {"organisatorische_context": [], "juridische_context": []}
NE_GEVALLEN = [
    ("lege-kern", "", CONTEXT, "kern"),
    ("witruimte", "   ", CONTEXT, "kern"),
    ("los-label", "Toegang:", CONTEXT, "kern"),
    ("geen-context", KERN_PASS, LEGE_CONTEXT, "context"),
    ("beide", "", {}, "kern en context"),
]


class TestNietUitgevoerd:
    @pytest.mark.parametrize(
        ("kern", "context", "grond"),
        [g[1:] for g in NE_GEVALLEN],
        ids=[g[0] for g in NE_GEVALLEN],
    )
    @pytest.mark.parametrize("voorbereid", [True, False], ids=["met-oordeel", "kaal"])
    def test_ontbrekende_invoer_geeft_exacte_ne(self, kern, context, grond, voorbereid):
        md: dict[str, Any] = {**copy.deepcopy(context), "record_text": kern}
        if voorbereid:
            md["int02_document"] = _document("pass")
            md["int02_configuratie"] = CONFIG
        melding = MELDING_NE.replace("{kern/context}", grond)
        uitkomst = _evalueer(md)
        detail = _assert_scoreloos_met_melding(
            uitkomst, ResultStatus.NOT_EVALUATED, melding
        )
        assert uitkomst.reason == melding
        assert uitkomst.violation is None
        assert detail["assessment"] is None
        assert detail["review"]["actuality"] is None


# ---------------------------------------------------------------------------
# Technische fout en ongeldig/gesaboteerd document: nooit pass of fail
# ---------------------------------------------------------------------------


def _assert_fout(uitkomst: EvaluationOutcome) -> dict:
    detail = _assert_scoreloos_met_melding(uitkomst, ResultStatus.ERROR, MELDING_E)
    assert uitkomst.reason == MELDING_E
    assert uitkomst.violation is None
    assert detail["assessment"] is None
    assert detail["review"]["actuality"] is None
    return detail


def _ongeldig_antwoord() -> Beoordelingsdocument:
    respons = copy.deepcopy(SCENARIO["pass"][1])
    respons["verdict"] = "ONGELDIG"
    return beoordeel(_invoer(KERN_PASS), CONFIG, respons, VOLTOOID)


def _verzonnen_citaat() -> Beoordelingsdocument:
    respons = copy.deepcopy(SCENARIO["fail"][1])
    respons["passages"][0]["quote"] = "zij vertrekt"
    return beoordeel(_invoer(KERN_PASS), CONFIG, respons, VOLTOOID)


def _direct_samengesteld() -> Beoordelingsdocument:
    invoer = _invoer(KERN_PASS)
    return Beoordelingsdocument(
        contractversie=CONTRACTVERSIE,
        invoer=invoer,
        binding=bereken_binding(invoer, CONFIG),
        uitvoering=VOLTOOID,
        status="pass",
        reden=None,
        melding="INT-02 — Voldoet. Verzonnen.",
        vraag=None,
        foutcategorie=None,
        oordeel_json=None,
    )


def _wp2_omhulsel():
    from services.validation.int02_assessment_service import Int02Beoordeling

    return Int02Beoordeling(
        document=_document("pass"),
        reden=None,
        gecachet=False,
        promptversie="def835-int02-prompt/1",
        prompt_sha256=None,
        profiel_id=None,
        task_type="validation",
        uitzonderingstype=None,
        stop_reason=None,
        antwoord_sha256=None,
    )


FOUTDOCUMENTEN = {
    "transport-mislukt": _document_mislukt,
    "ongeldig-antwoord": _ongeldig_antwoord,
    "verzonnen-citaat": _verzonnen_citaat,
}
ONGELDIGE_DOCUMENTEN = {
    "dict": lambda: _document("pass").als_dict(),
    "tekst": lambda: "pass",
    "lijst": lambda: ["pass"],
    "getal": lambda: 1,
    "wp2-omhulsel": _wp2_omhulsel,
}
GESABOTEERD = {
    "fout-als-pass": lambda: dataclasses.replace(
        _document_mislukt(), status="pass", melding=_document("pass").melding
    ),
    "pass-als-fail": lambda: dataclasses.replace(_document("pass"), status="fail"),
    "oordeel-vervangen": lambda: dataclasses.replace(
        _document("pass"),
        oordeel_json=json.dumps({**SCENARIO["pass"][1], "verdict": "fail"}),
    ),
    "oordeel-corrupt": lambda: dataclasses.replace(
        _document("pass"), oordeel_json="{niet-json"
    ),
    "direct-samengesteld": _direct_samengesteld,
}


class TestFoutEnOngeldig:
    @pytest.mark.parametrize("maak", FOUTDOCUMENTEN.values(), ids=FOUTDOCUMENTEN)
    def test_wp1_foutdocument_is_error_zonder_oordeel(self, maak):
        doc = maak()
        assert doc.status == "error", "testopzet: WP1 moet dit als fout vastleggen"
        detail = _assert_fout(_evalueer(_metadata(KERN_PASS, doc)))
        assert "zij vertrekt" not in json.dumps(detail, ensure_ascii=False)

    @pytest.mark.parametrize(
        "maak", ONGELDIGE_DOCUMENTEN.values(), ids=ONGELDIGE_DOCUMENTEN
    )
    def test_onbekend_documenttype_is_error(self, maak):
        _assert_fout(_evalueer(_metadata(KERN_PASS, maak())))

    @pytest.mark.parametrize("maak", GESABOTEERD.values(), ids=GESABOTEERD)
    def test_gesaboteerd_document_draagt_nooit_pass_of_fail(self, maak):
        detail = _assert_fout(_evalueer(_metadata(KERN_PASS, maak())))
        assert "Voldoet" not in json.dumps(detail, ensure_ascii=False)

    ONGELDIGE_METADATA = {
        "configuratie-als-dict": {
            "int02_configuratie": dataclasses.asdict(CONFIG),
        },
        "configuratie-als-tekst": {"int02_configuratie": "def835"},
        "context-als-tekst": {"organisatorische_context": "Synthetisch loket"},
        "context-met-getal": {"organisatorische_context": [1]},
        "bedoeling-als-getal": {"int02_bedoeling": 42},
        "bronnen-als-tekst": {"int02_bronnen": "B1"},
        "bron-zonder-tekst": {"int02_bronnen": [{"id": "B1"}]},
        "bron-dubbel-id": {
            "int02_bronnen": [{"id": "B1", "tekst": "a"}, {"id": "B1", "tekst": "b"}]
        },
    }

    @pytest.mark.parametrize(
        "waarde", [None, 42, [], {}], ids=["none", "getal", "lijst", "dict"]
    )
    @pytest.mark.parametrize("scenario", ["pass", "fail"])
    def test_aanwezige_ongeldige_recordtekst_valt_niet_terug_op_raw_text(
        self, scenario, waarde
    ):
        # WP3-R1 (Codex-review): terugval op raw_text alleen bij een ontbrekende
        # sleutel; een aanwezige niet-tekst is ongeldige metadata en mag het
        # meegegeven oordeel nooit actueel maken.
        kern = SCENARIO[scenario][0]
        md = _metadata(kern, _document(scenario), record_text=waarde)
        _assert_fout(_evalueer(md, tekst=kern))

    @pytest.mark.parametrize(
        "over", ONGELDIGE_METADATA.values(), ids=ONGELDIGE_METADATA
    )
    def test_ongeldige_metadata_wordt_netjes_een_fout(self, over):
        # Geen exceptie naar de aanroeper en nooit het meegegeven pass-oordeel.
        _assert_fout(_evalueer(_metadata(KERN_PASS, _document("pass"), **over)))


# ---------------------------------------------------------------------------
# Signalen: leeshulp uit het record en de actuele invoer
# ---------------------------------------------------------------------------


class TestSignalen:
    def test_signalen_veranderen_status_en_bewijs_niet(self):
        md = _metadata(KERN_PLICHT, _document("pass_plicht"))
        met = _evalueer(md)
        zonder = _evalueer(md, record=_o2_record(patronen=[]))
        assert met.status is zonder.status is ResultStatus.PASS
        assert met.violation is None and zonder.violation is None
        detail_met, detail_zonder = _detail(met), _detail(zonder)
        assert r"\bmoet\b" in detail_met["signals"]
        assert detail_zonder["signals"] == []
        assert {k: v for k, v in detail_met.items() if k != "signals"} == {
            k: v for k, v in detail_zonder.items() if k != "signals"
        }

    def test_signalen_komen_uit_de_actuele_kern_niet_uit_het_oordeel(self):
        # Oordeel over de discretiekern; actueel staat er een andere kern.
        md = _metadata(
            KERN_VOORSCHRIFT,
            _document("fail_discretie"),
            signals=[r"\bverzonnen\b"],
        )
        detail = _detail(_evalueer(md))
        patronen = set(RUW["herkenbaar_patronen"])
        assert r"\bmoet\b" in detail["signals"]
        assert r"\btenzij\b" not in detail["signals"]
        assert r"\bverzonnen\b" not in detail["signals"]
        assert set(detail["signals"]) <= patronen

    def test_zonder_signaalwoord_blijft_een_onderbouwde_afkeur_zichtbaar(self):
        uitkomst = _evalueer(_metadata(KERN_C105, _document("fail_zonder_signaal")))
        assert uitkomst.status is ResultStatus.FAIL
        assert _detail(uitkomst)["signals"] == []


# ---------------------------------------------------------------------------
# Geen verborgen mutatie; herhaalbaarheid
# ---------------------------------------------------------------------------


class TestGeenMutatie:
    def test_herhaalde_evaluatie_behoudt_invoer_en_oordeel(self):
        doc = _document("pass")
        doc_voor = doc.als_dict()
        oordeel_voor = doc.oordeel_json
        md = _metadata(KERN_PASS, doc)
        md_voor = {
            sleutel: (
                waarde
                if sleutel in ("int02_document", "int02_configuratie")
                else copy.deepcopy(waarde)
            )
            for sleutel, waarde in md.items()
        }
        een = _evalueer(md)
        twee = _evalueer(md)
        assert een.status is twee.status is ResultStatus.PASS
        assert (een.reason, een.violation, een.metadata) == (
            twee.reason,
            twee.violation,
            twee.metadata,
        )
        assert md == md_voor
        assert md["int02_document"] is doc
        assert md["int02_configuratie"] is CONFIG
        assert doc.als_dict() == doc_voor
        assert doc.oordeel_json == oordeel_voor
        # De publieke weergave is een kopie: muteren raakt het document niet.
        assessment = _detail(een)["assessment"]
        assessment["oordeel"]["verdict"] = "fail"
        assessment["invoer"]["kern"] = "gewijzigd"
        assert doc.oordeel["verdict"] == "pass"
        assert _detail(_evalueer(md))["assessment"] == doc_voor

    def test_alle_zes_statussen_zijn_gedekt(self):
        statussen = {u.status for u in o2_uitkomsten().values()}
        assert statussen == set(ResultStatus)
