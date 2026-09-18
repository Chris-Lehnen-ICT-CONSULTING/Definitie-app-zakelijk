"""ESS-03 (DEF-766): telbaarheid is een menselijk oordeel; geen woordbewijs.

Echte service, echte regelrecords, beide laadpaden (ToetsregelManager en de
CachedToetsregelManager → RuleCache-keten), geen provider. De casussen komen
uit het ESS-03-casusregister v4 (onderzoek 18 september 2026) en zijn
synthetische regressie-invoer, geen deskundig gevalideerde goldset.

Wat deze tests bewijzen: de app velt géén automatisch semantisch ESS-03-
oordeel meer. De oude `positive_indicator` liet "Object met een nummer", een
ontkende uniciteitsclaim en een ISBN-exemplaar slagen en keurde een
natuurlijke grens, een stoflezing en "registratienummer" af — puur op
woorden. Nu: open oordeel → `review_required`, ontbrekende term of lege
tekst → `not_evaluated`, technische fout → `error`; nooit een cijfer, nooit
een violation, nooit een nummergerichte herstelopdracht.

Wat ze niet bewijzen: een opgeslagen menselijk oordeel, stale-detectie of
een vaststel-/exportroute (zie contract-gap-v1.md; DEF-624/626/627/630).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.validation.evaluators.base import EvaluationDeps
from services.validation.evaluators.judgment_review import JudgmentReviewEvaluator
from services.validation.evaluators.positive_indicator import _INDICATOREN
from services.validation.modular_validation_service import ModularValidationService
from services.validation.types_internal import EvaluationContext
from toetsregels.manager import get_toetsregel_manager
from toetsregels.runtime_contract import (
    AutomationStatus,
    EvaluatorType,
    ExamplePairPolicy,
    Executability,
    RequiredInput,
    ResultStatus,
    ScorePolicy,
    build_rule_record,
)
from ui.components import validation_view
from ui.components.validation_renderer import ValidationRenderer
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

REGELS_DIR = Path(__file__).resolve().parents[3] / "src" / "toetsregels" / "regels"


def _ruw(rule_id: str) -> dict:
    return json.loads((REGELS_DIR / f"{rule_id}.json").read_text(encoding="utf-8"))


ESS03 = build_rule_record("ESS-03", _ruw("ESS-03"))

#: Regex-artefacten die nooit als eindgebruikersverklaring mogen verschijnen.
REGEX_ARTEFACTEN = ("\\b", "\\s", "\\w", "(?", "^\\")

#: Woorden waarmee de oude indicator/suggestie een nummerplicht uitdrukte.
NUMMERPLICHT = (
    "uniek identificatiecriterium",
    "nummer/code/registratie",
    "serienummer, kenteken, ID",
)

# (casus-ID, oude runtime-uitkomst, begrip, tekst)
# Oude uitkomst = gemeten in proefuitkomsten-v1.json (13×2, exit 0).
CASUSSEN = [
    (
        "H-good",
        "pass",
        "auto",
        (
            "Een auto is een vierwielig motorvoertuig met een uniek chassisnummer "
            "(VIN) en kenteken."
        ),
    ),
    (
        "H-bad",
        "fail",
        "auto",
        "Een auto is een vervoermiddel op vier wielen met een motor.",
    ),
    ("H-empty_identifier", "pass", "object", "Object met een nummer."),
    ("H-keyword_specific", "pass", "object", "Object met specifiek belang."),
    (
        "H-natural_boundary",
        "fail",
        "eiland",
        ("Landmassa die bij hoogwater volledig door water is omgeven."),
    ),
    ("H-mass_noun", "fail", "water", "Vloeistof bestaande uit H2O."),
    (
        "N01-negated",
        "pass",
        "object",
        ("Object waarvan de code niet uniek is en naar meerdere objecten verwijst."),
    ),
    (
        "N02-scope",
        "pass",
        "meetobject",
        (
            "Meetobject dat binnen register R door een blijvend uniek nummer wordt "
            "onderscheiden."
        ),
    ),
    (
        "N03-compound",
        "fail",
        "meetobject",
        ("Meetobject herkenbaar aan zijn registratienummer."),
    ),
    ("N04-isbn", "pass", "boekexemplaar", "Boekexemplaar met een ISBN."),
    (
        "N05-natural",
        "fail",
        "landoppervlak",
        (
            "Afzonderlijk aaneengesloten landoppervlak dat op het afgesproken "
            "peilmoment volledig door water is omgeven."
        ),
    ),
]
CASUS_IDS = [c[0] for c in CASUSSEN]

#: N06-metadata: dezelfde tekst als N02 met botsende onderzoeksmetadata. Die
#: metadata is geen appfunctie; de uitkomst mag er niet van afhangen.
N06_METADATA = {
    "identity_evidence": {
        "namespace": "R",
        "objects": [{"object": "a", "number": "17"}, {"object": "b", "number": "17"}],
    }
}


class TestRegelcontract:
    def test_ess03_is_scoreloos_reviewplichtig_met_term_als_vereiste_invoer(self):
        assert ESS03.evaluator is EvaluatorType.JUDGMENT_REVIEW
        assert ESS03.required_inputs == (
            RequiredInput.DEFINITION_TEXT,
            RequiredInput.TERM,
        )
        assert ESS03.executability is Executability.JUDGMENT
        assert ESS03.automation_status is AutomationStatus.REVIEW_REQUIRED
        assert ESS03.score_policy is ScorePolicy.NO_SCORE
        assert ESS03.counts_toward_score is False
        assert ESS03.is_automated is False

    def test_voorbeeldpaar_is_reviewpolicy_met_reden_en_eigenaar_def766(self):
        assert ESS03.has_example_pair
        assert ESS03.example_pair_policy is ExamplePairPolicy.REVIEW_POLICY
        assert ESS03.example_pair_issue == "DEF-766"
        reden = (ESS03.example_pair_reason or "").lower()
        assert "inhoudelijk oordeel" in reden
        assert "samenstellingen" in reden

    def test_voorbeelden_zijn_het_semantische_paar_uit_tekstvoorstellen_v3(self):
        goed = ESS03.get("goede_voorbeelden") or []
        fout = ESS03.get("foute_voorbeelden") or []
        assert goed == [
            (
                "Afzonderlijk aaneengesloten landoppervlak dat op het afgesproken "
                "peilmoment volledig door water is omgeven."
            )
        ]
        assert fout == [
            (
                "Boekexemplaar dat uitsluitend door zijn ISBN van andere fysieke "
                "exemplaren wordt onderscheiden."
            )
        ]
        # Het oude paar (VIN/kenteken versus vier wielen) is een woordbewijs.
        assert not any("chassisnummer" in g for g in goed)

    def test_regelkaart_stelt_geen_nummerplicht_en_noemt_de_uitzondering(self):
        naam = str(ESS03.get("naam") or "")
        assert naam == "Instanties uniek onderscheidbaar (telbaarheid)"
        uitleg = str(ESS03.get("uitleg") or "")
        toelichting = str(ESS03.get("toelichting") or "")
        toetsvraag = str(ESS03.get("toetsvraag") or "")
        geldigheid = str(ESS03.get("geldigheid") or "")
        assert "administratieve identifier is niet verplicht" in uitleg
        assert "eenduidige telling" in toelichting
        assert "bewijst op zichzelf geen identiteit" in toelichting
        assert "niet-telbare lezing" in toelichting.lower()
        assert "zand" in toelichting and "recidive" in toelichting
        assert "één, dezelfde of een andere instantie" in toetsvraag
        assert "niet op een woord" in geldigheid
        # De oude formuleringen (identifierlijst, "in elke situatie") zijn weg.
        samen = " ".join((uitleg, toelichting, toetsvraag, geldigheid))
        assert "in elke situatie" not in samen
        assert "bijv. serienummer" not in samen
        assert geldigheid != "telbare zelfstandige naamwoorden"

    def test_relatie_behoudt_astra_bron_en_voegt_contextrelatie_toe(self):
        urls = [r.get("fullurl", "") for r in (ESS03.get("relatie") or [])]
        assert any(url.endswith("/Instanties_uniek_onderscheidbaar") for url in urls)
        assert any(url.endswith("/Eigen_definitie_voor_elke_context") for url in urls)

    def test_positive_indicator_kent_ess03_niet_meer(self):
        # Ook het alternatieve levende pad (de hardgecodeerde indicator) is
        # dicht: er is geen ESS-03-patroon meer dat een pass of fail draagt.
        assert "ESS-03" not in _INDICATOREN
        assert "ESS-05" in _INDICATOREN  # ESS-05 blijft ongewijzigd


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


def _ctx(begrip: str, tekst: str, metadata: dict | None = None) -> EvaluationContext:
    return EvaluationContext(
        raw_text=tekst, cleaned_text=tekst, begrip=begrip, metadata=metadata or {}
    )


class TestEvaluatorUitkomst:
    @pytest.mark.parametrize(
        ("casus", "oud", "begrip", "tekst"), CASUSSEN, ids=CASUS_IDS
    )
    def test_open_oordeel_zonder_cijfer_of_violation(self, casus, oud, begrip, tekst):
        uitkomst = JudgmentReviewEvaluator().evaluate(
            ESS03, _ctx(begrip, tekst), _deps()
        )
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED, casus
        assert uitkomst.score is None
        assert uitkomst.violation is None
        reden = uitkomst.reason or ""
        assert reden.startswith("ESS-03")
        assert (
            "Nog te beoordelen: is voldoende duidelijk wat hier als één instantie geldt?"
            in reden
        )
        for artefact in REGEX_ARTEFACTEN:
            assert artefact not in reden, f"regex als verklaring: {reden!r}"
        # De reden velt zelf geen oordeel: geen 'voldoet' of 'voldoet niet'.
        assert "voldoet" not in reden.lower()
        for oud_woord in NUMMERPLICHT:
            assert oud_woord not in reden

    def test_signalen_wijzen_een_code_of_naamclaim_aan_zonder_oordeel(self):
        # N03: 'registratienummer' werd door de oude indicator gemist (fail);
        # nu is het een te beoordelen passage — en uitdrukkelijk geen bewijs.
        uitkomst = JudgmentReviewEvaluator().evaluate(
            ESS03,
            _ctx("meetobject", "Meetobject herkenbaar aan zijn registratienummer."),
            _deps(),
        )
        reden = uitkomst.reason or ""
        assert "Te beoordelen passage: registratienummer." in reden
        assert "bewijst op zichzelf geen identiteit" in reden
        assert uitkomst.metadata.get("signals")

    def test_natuurlijke_grens_zonder_code_is_geen_afkeur(self):
        # N05/H-natural_boundary: geen trefwoord → oude fail. Nu: open, en de
        # reden vraagt niet om een nummer.
        uitkomst = JudgmentReviewEvaluator().evaluate(
            ESS03,
            _ctx(
                "eiland", "Landmassa die bij hoogwater volledig door water is omgeven."
            ),
            _deps(),
        )
        reden = uitkomst.reason or ""
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert "Geen patroonsignaal gevonden" in reden
        # Geen herstelopdracht: de reden vraagt nergens om iets toe te voegen.
        assert "voeg" not in reden.lower()
        for oud in NUMMERPLICHT:
            assert oud not in reden
        assert not uitkomst.metadata.get("signals")

    def test_categorielabel_is_registratie_geen_vrijstelling(self):
        # H-mass_noun met een opgegeven categorie: het label bepaalt de
        # toepasselijkheid niet; het wordt genoemd als te controleren claim.
        uitkomst = JudgmentReviewEvaluator().evaluate(
            ESS03,
            _ctx(
                "water",
                "Vloeistof bestaande uit H2O.",
                {"ontologische_categorie": "type"},
            ),
            _deps(),
        )
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        reden = uitkomst.reason or ""
        assert "categorie 'type'" in reden
        assert "bepaalt de toepasselijkheid niet" in reden

    def test_lege_tekst_is_niet_geevalueerd_geen_open_oordeel_over_niets(self):
        # H-empty: geen toetsobject → niet uitgevoerd, geen inhoudelijke
        # afkeur en geen review-vraag over een lege kern.
        uitkomst = JudgmentReviewEvaluator().evaluate(
            ESS03, _ctx("object", "   "), _deps()
        )
        assert uitkomst.status is ResultStatus.NOT_EVALUATED
        assert uitkomst.score is None
        assert uitkomst.violation is None
        assert "definitietekst" in (uitkomst.reason or "").lower()

    def test_botsende_onderzoeksmetadata_verandert_de_uitkomst_niet(self):
        tekst = (
            "Meetobject dat binnen register R door een blijvend uniek nummer wordt "
            "onderscheiden."
        )
        zonder = JudgmentReviewEvaluator().evaluate(
            ESS03, _ctx("meetobject", tekst), _deps()
        )
        met = JudgmentReviewEvaluator().evaluate(
            ESS03, _ctx("meetobject", tekst, N06_METADATA), _deps()
        )
        assert zonder.status is met.status is ResultStatus.REVIEW_REQUIRED
        assert zonder.reason == met.reason


@pytest.fixture(
    scope="module", params=["toetsregel_manager", "cached_manager (productiepad)"]
)
def svc(request) -> ModularValidationService:
    # Beide regelbronnen: de DEF-606-bug zat in de divergentie tussen de
    # volledige manager en de RuleCache-keten (productiepad).
    if request.param.startswith("cached_manager"):
        from toetsregels.cached_manager import get_cached_toetsregel_manager
        from toetsregels.rule_cache import get_rule_cache

        get_rule_cache().clear_cache()  # geen stale FileCache-entries
        manager = get_cached_toetsregel_manager()
    else:
        manager = get_toetsregel_manager()
    return ModularValidationService(manager, None, None)


def _ess03_violations(result: dict) -> list[dict]:
    return [v for v in result.get("violations", []) if v.get("code") == "ESS-03"]


class TestServiceRoute:
    @pytest.mark.parametrize(
        ("casus", "oud", "begrip", "tekst"), CASUSSEN, ids=CASUS_IDS
    )
    async def test_volledige_set_geeft_nooit_automatisch_ess03_oordeel(
        self, svc, casus, oud, begrip, tekst
    ):
        result = await svc.validate_definition(begrip=begrip, text=tekst, context={})
        assert result["validation_status"] == "validated"
        assert result["rule_statuses"]["ESS-03"] == "review_required", (casus, oud)
        assert "ESS-03" not in result["passed_rules"]
        assert _ess03_violations(result) == []
        item = next(r for r in result["review_required"] if r["rule_id"] == "ESS-03")
        assert item["reason"].startswith("ESS-03")
        assert "Nog te beoordelen" in item["reason"]
        # Geen cijfer: geen totaalscore, geen categoriecijfer voor 'juridisch',
        # en ESS-03 wordt als regel zonder cijfer benoemd.
        assert result["overall_score"] is None
        assert result["detailed_scores"]["juridisch"] is None
        redenen = " ".join(result["acceptance_gate"].get("reasons") or [])
        assert "ESS-03" in redenen

    async def test_zonder_term_is_ess03_niet_geevalueerd_nooit_pass(self, svc):
        result = await svc.validate_definition(
            begrip="", text="Object met een nummer.", context={}
        )
        assert result["rule_statuses"]["ESS-03"] == "not_evaluated"
        assert "ESS-03" not in result["passed_rules"]
        assert _ess03_violations(result) == []
        assert not any(r["rule_id"] == "ESS-03" for r in result["review_required"])

    async def test_lege_tekst_met_term_is_niet_geevalueerd(self, svc):
        result = await svc.validate_definition(begrip="object", text="", context={})
        assert result["rule_statuses"]["ESS-03"] == "not_evaluated"
        assert _ess03_violations(result) == []
        assert not any(r["rule_id"] == "ESS-03" for r in result["review_required"])
        # De basisfout blijft bij VAL-EMP-001, niet bij ESS-03.
        assert result["rule_statuses"]["VAL-EMP-001"] == "fail"

    async def test_botsende_metadata_geeft_zelfde_open_uitkomst(self, svc):
        tekst = (
            "Meetobject dat binnen register R door een blijvend uniek nummer wordt "
            "onderscheiden."
        )
        zonder = await svc.validate_definition(
            begrip="meetobject", text=tekst, context={}
        )
        met = await svc.validate_definition(
            begrip="meetobject", text=tekst, context=dict(N06_METADATA)
        )
        assert zonder["rule_statuses"]["ESS-03"] == met["rule_statuses"]["ESS-03"]
        assert zonder["rule_statuses"]["ESS-03"] == "review_required"

    async def test_technische_fout_is_error_zonder_cijfer_of_violation(
        self, svc, monkeypatch
    ):
        def kapot(self, record, ctx, deps):
            if record.rule_id.upper() == "ESS-03":
                raise RuntimeError("synthetische storing")
            return _origineel(self, record, ctx, deps)

        _origineel = JudgmentReviewEvaluator.evaluate
        monkeypatch.setattr(JudgmentReviewEvaluator, "evaluate", kapot)
        result = await svc.validate_definition(
            begrip="object", text="Object met een nummer.", context={}
        )
        assert result["rule_statuses"]["ESS-03"] == "error"
        assert _ess03_violations(result) == []
        assert "ESS-03" not in result["passed_rules"]
        assert not any(r["rule_id"] == "ESS-03" for r in result["review_required"])
        # Apart herkenbaar foutonderdeel, zonder interne details als uitleg.
        detail = result["rule_results"]["ESS-03"]
        assert detail["status"] == "error"
        assert detail["score"] is None
        assert "synthetische storing" not in json.dumps(detail, ensure_ascii=False)
        assert result["evaluation_coverage"]["error"] >= 1
        assert result["is_acceptable"] is False

    async def test_beperkte_run_boekt_geen_ess03_score(self, svc):
        """Eén regel, buiten de volledige set: nooit een cijfer, wel dekking."""
        state = svc._ververs_state_indien_nodig()
        assert state.rule_records["ESS-03"].score_policy is ScorePolicy.NO_SCORE
        tekst = "Object met een nummer."
        ctx = EvaluationContext.from_params(
            text=tekst,
            cleaned=tekst,
            begrip="object",
            locale=None,
            profile=None,
            correlation_id="def766",
            tokens=(),
            metadata={},
        )
        uitkomst = svc._evaluate_rule("ESS-03", ctx, state)
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        rule_scores: dict = {}
        violations: list = []
        passed: list = []
        statuses: dict = {}
        review: list = []
        results: dict = {}
        svc._verwerk_uitkomst(
            "ESS-03",
            ctx,
            uitkomst,
            state,
            rule_scores=rule_scores,
            violations=violations,
            passed_rules=passed,
            rule_statuses=statuses,
            review_items=review,
            rule_results=results,
            geen_cijfer=True,
        )
        assert rule_scores == {}
        assert violations == []
        assert passed == []
        assert statuses == {"ESS-03": "review_required"}
        assert [r["rule_id"] for r in review] == ["ESS-03"]


class TestGeenAutomatischHerstel:
    def test_suggestieopbouw_geeft_geen_nummeropdracht_meer(self):
        svc = ModularValidationService(get_toetsregel_manager(), None, None)
        tekst = "Landmassa die bij hoogwater volledig door water is omgeven."
        suggestie = svc.build_suggestion(
            "ESS-03", _ruw("ESS-03"), tekst, _ctx("eiland", tekst), reason="unique_id"
        )
        for oud in NUMMERPLICHT:
            assert oud not in suggestie
        assert "identificatiecriterium" not in suggestie

    async def test_geen_ess03_suggestie_in_het_resultaat(self):
        svc = ModularValidationService(get_toetsregel_manager(), None, None)
        result = await svc.validate_definition(
            begrip="eiland",
            text="Landmassa die bij hoogwater volledig door water is omgeven.",
            context={},
        )
        suggesties = [v.get("suggestion") or "" for v in result["violations"]]
        assert not any("identificatiecriterium" in s for s in suggesties)
        assert _ess03_violations(result) == []

    def test_renderer_verzint_geen_heuristische_passreden_voor_ess03(self):
        # ESS-03 komt nooit meer als geslaagde regel binnen; de UI mag dan
        # ook geen "vereist element herkend" meer voor ESS-03 uitspreken.
        renderer = ValidationRenderer()
        reden = renderer._build_pass_reason(
            "ESS-03", "Object met een nummer.", "object"
        )
        assert "Vereist element herkend" not in reden
        # ESS-05 houdt zijn bestaande heuristiek.
        assert "Vereist element herkend" in renderer._build_pass_reason(
            "ESS-05", "eigenschap die een entiteit onderscheidt", "kenmerk"
        )


class TestWeergave:
    async def test_open_reden_wordt_letterlijk_getoond(self, monkeypatch):
        svc = ModularValidationService(get_toetsregel_manager(), None, None)
        result = await svc.validate_definition(
            begrip="meetobject",
            text="Meetobject herkenbaar aan zijn registratienummer.",
            context={},
        )
        item = next(r for r in result["review_required"] if r["rule_id"] == "ESS-03")
        shown = {
            api: []
            for api in (
                "markdown",
                "info",
                "warning",
                "success",
                "error",
                "write",
                "text",
            )
        }
        for api in shown:
            monkeypatch.setattr(
                validation_view.st,
                api,
                lambda t, *a, _api=api, **kw: shown[_api].append(str(t)),
                raising=False,
            )
        monkeypatch.setattr(validation_view.st, "button", lambda *a, **kw: False)
        SessionStateManager.set_value("def766_show_validation_details", False)
        validation_view.render_validation_detailed_list(result, key_prefix="def766")
        # Passages zijn gebruikersinvoer: letterlijk via st.text, niet als markdown.
        assert item["reason"] in shown["text"]
        for api, values in shown.items():
            if api != "text":
                assert item["reason"] not in "\n".join(values)
