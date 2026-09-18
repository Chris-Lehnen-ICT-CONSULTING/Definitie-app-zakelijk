"""ESS-02 (DEF-750): reviewplichtig zonder cijfer; signalen zijn geen oordeel.

Echte service, echte regelrecords, geen provider. De synthetische casussen
komen uit het ESS-02-onderzoeksdossier en zijn regressie-invoer, geen
deskundig gevalideerde goldset: deze tests bewijzen dat de app géén
automatisch inhoudelijk oordeel velt (geen marker-pass, geen pass op één
categoriehit, geen fail op nul of meerdere hits), niet dat een casus
inhoudelijk voldoet. De menselijke beoordeling en haar opslag volgen in C/D.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.validation.evaluators.base import EvaluationDeps
from services.validation.evaluators.judgment_review import JudgmentReviewEvaluator
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
    build_rule_records,
)
from ui.components import validation_view
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

REGELS_DIR = Path(__file__).resolve().parents[3] / "src" / "toetsregels" / "regels"


def _ruw(rule_id: str) -> dict:
    return json.loads((REGELS_DIR / f"{rule_id}.json").read_text(encoding="utf-8"))


ESS02 = build_rule_record("ESS-02", _ruw("ESS-02"))
ESS01 = build_rule_record("ESS-01", _ruw("ESS-01"))

#: Regex-artefacten die nooit als eindgebruikersverklaring mogen verschijnen.
REGEX_ARTEFACTEN = ("\\b", "\\s", "\\w", "(?", "^\\")

# (label, begrip, tekst, metadata, verwachte signaalpassage of None)
CASUSSEN = [
    (
        "E02-001 heldere kern zonder markerwoord",
        "dossierstuk",
        "document dat informatie over één behandeld onderwerp vastlegt",
        {},
        None,
    ),
    (
        "E02-004 activiteit met genoemde uitkomst (twee categoriewoorden)",
        "registratie",
        (
            "activiteit waarbij meetwaarden worden vastgelegd en die leidt tot een "
            "resultaat in een register"
        ),
        {},
        None,
    ),
    (
        "E02-005 gemengde kern zonder marker",
        "registratie",
        "activiteit of resultaat van het vastleggen van meetwaarden",
        {},
        "activiteit of resultaat",
    ),
    (
        "E02-006 gemengde kern met geldige marker",
        "registratie",
        "activiteit of resultaat van het vastleggen van meetwaarden",
        {"marker": "proces"},
        "activiteit of resultaat",
    ),
    (
        "E02-011 lege kern met marker",
        "lege-invoer",
        "",
        {"marker": "type"},
        None,
    ),
    (
        "fixture: precies één categoriehit (was automatische pass)",
        "waarde",
        "klasse van waarderingsvormen",
        {},
        "klasse van waarderingsvormen",
    ),
    (
        "E2-07 kick-off met 'soort' en opgegeven categorie",
        "toetsing",
        (
            "soort collegiale toetsing waarbij deelnemers samen een voorgestelde "
            "oplossing doorlopen"
        ),
        {"ontologische_categorie": "type"},
        "soort collegiale",
    ),
]


class TestRegelcontract:
    def test_ess02_is_scoreloos_reviewplichtig(self):
        assert ESS02.evaluator is EvaluatorType.JUDGMENT_REVIEW
        assert ESS02.required_inputs == (RequiredInput.DEFINITION_TEXT,)
        assert ESS02.executability is Executability.JUDGMENT
        assert ESS02.automation_status is AutomationStatus.REVIEW_REQUIRED
        assert ESS02.score_policy is ScorePolicy.NO_SCORE
        assert ESS02.counts_toward_score is False
        assert ESS02.is_automated is False

    def test_generiek_voorbeeldpaar_met_review_policy_en_eigenaar(self):
        # Alleen de generieke sleutels bereiken de promptformatter en
        # `has_example_pair`; de betekenisgrond staat bij het record.
        assert ESS02.has_example_pair
        assert ESS02.example_pair_policy is ExamplePairPolicy.REVIEW_POLICY
        assert (ESS02.example_pair_reason or "").strip()
        assert ESS02.example_pair_issue == "DEF-624"
        assert "goldset" in (ESS02.example_pair_reason or "").lower()

    def test_regelkaart_onderscheidt_niveau_en_aard_zonder_markerplicht(self):
        tekst = " ".join(
            str(ESS02.get(veld) or "") for veld in ("naam", "uitleg", "toelichting")
        ).lower()
        assert "algemeen begrip" in tekst
        assert "één bepaald ding" in tekst
        assert "markerwoorden zijn niet vereist" in tekst
        assert "welke van deze vier" not in tekst
        assert "is een categorie" not in tekst

    def test_normherkomst_astra_en_lokale_uitbreiding_gescheiden(self):
        relaties = ESS02.get("relatie") or []
        urls = [r.get("fullurl", "") for r in relaties]
        assert any("Type_of_instantie" in url for url in urls)
        assert any("DEF-625" in url for url in urls)
        assert not any("Polysemie_proces_vs_resultaat" in url for url in urls)

    def test_hulppatronen_zijn_reviewerhulp_geen_categoriedetectie(self):
        # De oude vier categorievelden dreven pass/fail; die route is dicht.
        assert ESS02.get("herkenbaar_patronen")
        for veld in (
            "herkenbaar_patronen_type",
            "herkenbaar_patronen_particulier",
            "herkenbaar_patronen_proces",
            "herkenbaar_patronen_resultaat",
        ):
            assert not ESS02.get(veld)

    def test_geen_record_routeert_nog_naar_de_categorie_evaluator(self):
        records = build_rule_records(
            {pad.stem: _ruw(pad.stem) for pad in REGELS_DIR.glob("*.json")}
        )
        nog = sorted(
            r.rule_id
            for r in records.values()
            if r.evaluator is EvaluatorType.ONTOLOGICAL_CATEGORY
        )
        assert nog == [], f"marker-/categoriehitroute nog actief voor {nog}"

    def test_ess01_contract_ongewijzigd(self):
        # DEF-746/747 blijven overeind: A raakt ESS-01 niet.
        assert ESS01.evaluator is EvaluatorType.JUDGMENT_REVIEW
        assert ESS01.automation_status is AutomationStatus.REVIEW_REQUIRED
        assert ESS01.score_policy is ScorePolicy.EXCLUDED_FROM_SCORE
        assert ESS01.example_pair_policy is ExamplePairPolicy.REVIEW_POLICY


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


class TestEvaluatorUitkomst:
    @pytest.mark.parametrize(
        ("label", "begrip", "tekst", "metadata", "passage"),
        CASUSSEN,
        ids=[c[0] for c in CASUSSEN],
    )
    def test_review_required_zonder_cijfer_of_violation(
        self, label, begrip, tekst, metadata, passage
    ):
        ctx = EvaluationContext(
            raw_text=tekst, cleaned_text=tekst, begrip=begrip, metadata=metadata
        )
        uitkomst = JudgmentReviewEvaluator().evaluate(ESS02, ctx, _deps())
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert uitkomst.score is None
        assert uitkomst.violation is None
        reden = uitkomst.reason or ""
        assert reden.startswith("ESS-02")
        assert "Nog te beoordelen" in reden
        for artefact in REGEX_ARTEFACTEN:
            assert artefact not in reden, f"regex als verklaring: {reden!r}"
        signalen = uitkomst.metadata.get("signals", [])
        if passage:
            assert f"Te beoordelen passage: {passage}." in reden
            assert "geen inhoudelijk oordeel" in reden
            assert signalen
        else:
            assert "Geen patroonsignaal gevonden" in reden
            assert not signalen

    def test_marker_en_label_geven_geen_positieve_uitkomst(self):
        tekst = "activiteit of resultaat van het vastleggen van meetwaarden"
        ctx = EvaluationContext(
            raw_text=tekst,
            cleaned_text=tekst,
            begrip="registratie",
            metadata={"marker": "proces", "ontologische_categorie": "proces"},
        )
        uitkomst = JudgmentReviewEvaluator().evaluate(ESS02, ctx, _deps())
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        reden = (uitkomst.reason or "").lower()
        assert "categorielabel" in reden
        assert "voldoet" not in reden.replace("voldoet niet", "")


class TestServiceRoute:
    @pytest.mark.parametrize(
        ("label", "begrip", "tekst", "metadata", "passage"),
        CASUSSEN,
        ids=[c[0] for c in CASUSSEN],
    )
    async def test_volledige_set_geeft_nooit_automatisch_ess02_oordeel(
        self, label, begrip, tekst, metadata, passage
    ):
        svc = ModularValidationService(get_toetsregel_manager(), None, None)
        result = await svc.validate_definition(
            begrip=begrip,
            text=tekst,
            context={"organisatorisch": ["uitvoering"], **metadata},
        )
        assert result["validation_status"] == "validated"
        assert result["rule_statuses"]["ESS-02"] == "review_required"
        assert "ESS-02" not in result["passed_rules"]
        assert not any(v.get("code") == "ESS-02" for v in result["violations"])
        item = next(r for r in result["review_required"] if r["rule_id"] == "ESS-02")
        assert item["reason"].startswith("ESS-02")
        if passage:
            assert f"Te beoordelen passage: {passage}." in item["reason"]
        else:
            assert "Geen patroonsignaal gevonden" in item["reason"]
        # Geen cijfer: geen totaalscore en geen vervangende deelscore voor de
        # categorie waarin ESS-02 valt.
        assert result["overall_score"] is None
        assert result["detailed_scores"]["juridisch"] is None

    async def test_beperkte_run_boekt_geen_ess02_score(self):
        """Eén regel, buiten de volledige set: nooit een cijfer, wel dekking."""
        svc = ModularValidationService(get_toetsregel_manager(), None, None)
        state = svc._ververs_state_indien_nodig()
        assert state.rule_records["ESS-02"].score_policy is ScorePolicy.NO_SCORE
        tekst = "activiteit of resultaat van het vastleggen van meetwaarden"
        ctx = EvaluationContext.from_params(
            text=tekst,
            cleaned=tekst,
            begrip="registratie",
            locale=None,
            profile=None,
            correlation_id="def750",
            tokens=(),
            metadata={"marker": "proces"},
        )
        uitkomst = svc._evaluate_rule("ESS-02", ctx, state)
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        rule_scores: dict = {}
        violations: list = []
        passed: list = []
        statuses: dict = {}
        review: list = []
        results: dict = {}
        svc._verwerk_uitkomst(
            "ESS-02",
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
        assert statuses == {"ESS-02": "review_required"}
        assert [r["rule_id"] for r in review] == ["ESS-02"]

    async def test_reden_wordt_letterlijk_getoond(self, monkeypatch):
        svc = ModularValidationService(get_toetsregel_manager(), None, None)
        result = await svc.validate_definition(
            begrip="registratie",
            text="activiteit of resultaat van het vastleggen van meetwaarden",
            context={"organisatorisch": ["uitvoering"]},
        )
        item = next(r for r in result["review_required"] if r["rule_id"] == "ESS-02")
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
        SessionStateManager.set_value("def750_show_validation_details", False)
        validation_view.render_validation_detailed_list(result, key_prefix="def750")
        assert item["reason"] in shown["text"]
        for api, values in shown.items():
            if api != "text":
                assert item["reason"] not in "\n".join(values)
        alles = "\n".join(v for vs in shown.values() for v in vs).lower()
        assert "marker aanwezig" not in alles
