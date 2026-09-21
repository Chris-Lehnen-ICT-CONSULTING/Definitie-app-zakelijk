"""ESS-04 (DEF-767, W1-A): het regelrecord draagt besluit N2 — één normversie.

Echte regelrecords via beide laadpaden (ToetsregelManager en de
CachedToetsregelManager → RuleCache-keten, het productiepad), geen provider.
De teksten komen uit de besluitnotitie en instructievoorstellen-v5 van het
ESS-04-onderzoek (18 september 2026); het goede en de foute voorbeelden zijn
de registerfixtures ESS04-C03, ESS04-C05 en ESS04-C04.

Wat deze tests bewijzen: het record draagt de geharmoniseerde norm
(kwalitatieve criteria kunnen volstaan; cijfers bewijzen niets), beide
laadpaden leveren exact hetzelfde record (AC05), de vijftien signaalpatronen
zijn onaangeroerd en de automatische evaluatie velt voor het goede noch het
foute voorbeeld een pass of fail: altijd `review_required`, nooit een cijfer.

Wat ze niet bewijzen: een opgeslagen menselijk oordeel (DEF-624/626/627).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.validation.evaluators.base import EvaluationDeps
from services.validation.evaluators.judgment_review import JudgmentReviewEvaluator
from services.validation.modular_validation_service import ModularValidationService
from services.validation.types_internal import EvaluationContext
from toetsregels.cached_manager import get_cached_toetsregel_manager
from toetsregels.manager import get_toetsregel_manager
from toetsregels.rule_cache import _RECORD_DEFAULTS, get_rule_cache
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

pytestmark = [pytest.mark.unit]

REGELS_DIR = Path(__file__).resolve().parents[3] / "src" / "toetsregels" / "regels"


def _ruw(rule_id: str) -> dict:
    return json.loads((REGELS_DIR / f"{rule_id}.json").read_text(encoding="utf-8"))


ESS04 = build_rule_record("ESS-04", _ruw("ESS-04"))

#: De vijftien signaalpatronen op basis 2c9a6e3a1 — buiten scope van W1,
#: dus byte-gelijk te behouden.
PATRONEN_ONGEWIJZIGD = [
    r"\bbinnen\s+\d+\s+dagen?\b",
    r"\buiterlijk\s+na\s+\d+\s+(dagen?|weken?)\b",
    r"\btenminste\s+\d+%\b",
    r"\bminimaal\s+\d+%\b",
    r"\bmaximaal\s+\d+%\b",
    r"\b\d+\s+%\b",
    r"\baan de hand van\b",
    r"\bobjectieve criteria\b",
    r"\bbevat\b",
    r"\bomvat\b",
    r"\bheeft als eigenschap\b",
    r"\bwordt gekenmerkt door\b",
    r"\bcontrole op\b",
    r"\bwaarneembare\b",
    r"\btoetsbaar\b",
]

UITLEG_N2 = (
    "Ieder criterium in de definitie is binnen de bedoelde betekenis en context "
    "voldoende bepaald om navolgbaar te beoordelen of een geval eraan voldoet."
)
TOELICHTING_N2 = (
    "Kwalitatieve criteria kunnen volstaan. Cijfers, percentages en termijnen zijn "
    "alleen behulpzaam als duidelijk is waarop zij betrekking hebben en hoe zij "
    "moeten worden toegepast. Leg meet- of beoordelingscontext vast wanneer die de "
    "uitkomst bepaalt; denk dan aan populatie of noemer, grensinclusie, "
    "referentietijd, dagconventie en toepasselijke bronversie. Wat het begrip zelf "
    "begrenst hoort in de definitiekern; hoe je het vaststelt — methode, "
    "meetprocedure, rekenvoorbeeld — hoort in de toelichting. Verzin geen drempels "
    "of bewijs. Een onbekende uitkomst door ontbrekend gevalsbewijs is niet "
    "hetzelfde als een ontoetsbaar criterium. Een toepasbaar criterium kan nog "
    "steeds inhoudelijk onjuist of onvoldoende onderscheidend zijn; beoordeel die "
    "normdoelen afzonderlijk. Signalen en automatische controles vervangen geen "
    "inhoudelijke menselijke beoordeling."
)
TOETSVRAAG_N2 = (
    "Zijn de begripskenmerken in de bedoelde context voldoende bepaald om hun "
    "toepasselijkheid op gevallen navolgbaar te beoordelen, en welke criteria of "
    "betekenisgrond ontbreken nog om dat te beoordelen?"
)
EXAMPLE_PAIR_REASON_N2 = (
    "Het toepassen van dit criterium vraagt beoordeling van de bedoelde betekenis "
    "en de relevante grond. Woorden, getallen en signaalpatronen leveren geen "
    "bewijs van voldoen of niet voldoen; ook zonder treffer blijft menselijke "
    "beoordeling nodig."
)
GOED_VOORBEELD = "Veelhoek waarvan alle zijden even lang zijn."
FOUTE_VOORBEELDEN = [
    "Object dat minimaal 80% voldoet.",
    "Belangrijke aanvraag die binnen 3 dagen relevant wordt.",
]


class TestRegelkaartN2:
    def test_naam_uitleg_toelichting_en_toetsvraag_dragen_de_geharmoniseerde_norm(
        self,
    ):
        assert ESS04.get("naam") == "Toetsbaarheid"
        assert ESS04.get("uitleg") == UITLEG_N2
        assert ESS04.get("toelichting") == TOELICHTING_N2
        assert ESS04.get("toetsvraag") == TOETSVRAAG_N2
        assert "betekenisgrond" in str(ESS04.get("toetsvraag"))
        # De oude cijferplicht is weg: geen 'harde deadlines', geen 'tenminste 80%'.
        samen = " ".join(
            str(ESS04.get(veld) or "")
            for veld in ("uitleg", "toelichting", "toetsvraag")
        )
        assert "harde deadlines" not in samen
        assert "objectief toetsbare elementen" not in samen
        assert "tenminste 80%" not in samen

    def test_voorbeelden_zijn_het_semantische_paar_uit_het_casusregister(self):
        goed = ESS04.get("goede_voorbeelden") or []
        fout = ESS04.get("foute_voorbeelden") or []
        assert goed == [GOED_VOORBEELD]
        assert len(goed) == 1
        assert fout == FOUTE_VOORBEELDEN
        # Het oude paar (termijnfragment versus 'zo snel mogelijk') is weg: het
        # was een getalsbewijs, geen betekenisbewijs.
        assert not any("binnen 3 dagen nadat" in g for g in goed)
        assert not any("zo snel mogelijk" in f for f in fout)

    def test_thema_en_relaties(self):
        assert ESS04.get("thema") == "essentie van het begrip"
        relaties = ESS04.get("relatie") or []
        urls = [r.get("fullurl", "") for r in relaties]
        teksten = [r.get("fulltext", "") for r in relaties]
        assert "https://www.astraonline.nl/index.php/Toetsbaarheid" in urls
        assert (
            "https://www.astraonline.nl/index.php/Instanties_uniek_onderscheidbaar"
            in urls
        )
        assert "Toetsbaarheid" in teksten
        assert "Instanties uniek onderscheidbaar" in teksten
        assert len(relaties) == 2

    def test_ongewijzigde_velden_en_de_vijftien_patronen(self):
        assert ESS04.get("id") == "ESS_04"
        assert ESS04.get("herkenbaar_patronen") == PATRONEN_ONGEWIJZIGD
        assert len(ESS04.get("herkenbaar_patronen")) == 15
        assert ESS04.get("prioriteit") == "midden"
        assert ESS04.get("aanbeveling") == "verplicht"
        assert ESS04.get("geldigheid") == "alle"
        assert ESS04.get("status") == "definitief"
        assert ESS04.get("type") == "element in de definitie"
        assert ESS04.get("brondocument") == "ASTRA"

    def test_runtime_contract_blijft_reviewplichtig_zonder_score(self):
        assert ESS04.evaluator is EvaluatorType.JUDGMENT_REVIEW
        assert ESS04.required_inputs == (RequiredInput.DEFINITION_TEXT,)
        assert ESS04.executability is Executability.JUDGMENT
        assert ESS04.automation_status is AutomationStatus.REVIEW_REQUIRED
        assert ESS04.score_policy is ScorePolicy.EXCLUDED_FROM_SCORE
        assert ESS04.counts_toward_score is False
        assert ESS04.is_automated is False
        assert ESS04.example_pair_policy is ExamplePairPolicy.REVIEW_POLICY
        assert ESS04.example_pair_issue == "DEF-624"
        assert ESS04.example_pair_reason == EXAMPLE_PAIR_REASON_N2


class TestEenNormversieAC05:
    """Beide laadpaden leveren hetzelfde record: JSON-manager én RuleCache-keten."""

    @pytest.fixture(autouse=True)
    def _verse_cache(self):
        # Geen stale FileCache-entries (TTL 1u) uit een eerdere run met het
        # oude record; anders toont het productiepad een oude normversie.
        get_rule_cache().clear_cache()
        yield
        get_rule_cache().clear_cache()

    @staticmethod
    def _bronvelden(record: dict) -> dict:
        """Alle velden uit het JSON-bronrecord; het productiepad vult daarnaast
        alleen bekende default-containers (`_RECORD_DEFAULTS`) aan."""
        ruw = _ruw("ESS-04")
        extra = set(record) - set(ruw)
        assert extra <= set(_RECORD_DEFAULTS), extra
        return {veld: record[veld] for veld in ruw}

    def test_load_regel_is_gelijk_via_beide_paden(self):
        via_manager = get_toetsregel_manager().load_regel("ESS-04")
        via_cache = get_cached_toetsregel_manager().load_regel("ESS-04")
        assert via_manager is not None and via_cache is not None
        assert via_manager == _ruw("ESS-04")
        assert self._bronvelden(via_cache) == _ruw("ESS-04")
        assert via_cache["uitleg"] == UITLEG_N2
        assert via_cache["toetsvraag"] == TOETSVRAAG_N2
        assert via_cache["goede_voorbeelden"] == [GOED_VOORBEELD]
        assert via_cache["herkenbaar_patronen"] == PATRONEN_ONGEWIJZIGD

    def test_get_all_regels_is_gelijk_via_beide_paden(self):
        via_manager = get_toetsregel_manager().get_all_regels()["ESS-04"]
        via_cache = get_cached_toetsregel_manager().get_all_regels()["ESS-04"]
        assert via_manager == _ruw("ESS-04")
        assert self._bronvelden(via_cache) == _ruw("ESS-04")
        assert via_cache["runtime_contract"]["example_pair_reason"] == (
            EXAMPLE_PAIR_REASON_N2
        )


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


def _ctx(begrip: str, tekst: str) -> EvaluationContext:
    return EvaluationContext(raw_text=tekst, cleaned_text=tekst, begrip=begrip)


@pytest.fixture(
    scope="module", params=["toetsregel_manager", "cached_manager (productiepad)"]
)
def svc(request) -> ModularValidationService:
    if request.param.startswith("cached_manager"):
        get_rule_cache().clear_cache()
        manager = get_cached_toetsregel_manager()
    else:
        manager = get_toetsregel_manager()
    return ModularValidationService(manager, None, None)


class TestGeenAutomatischOordeel:
    """Het goede noch het foute recordvoorbeeld krijgt een automatische pass/fail."""

    @pytest.mark.parametrize(
        ("casus", "begrip", "tekst"),
        [
            ("ESS04-C05 fout voorbeeld", "object", FOUTE_VOORBEELDEN[0]),
            ("ESS04-C03 goed voorbeeld", "veelhoek", GOED_VOORBEELD),
        ],
    )
    def test_evaluator_blijft_review_required_zonder_score(self, casus, begrip, tekst):
        uitkomst = JudgmentReviewEvaluator().evaluate(
            ESS04, _ctx(begrip, tekst), _deps()
        )
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED, casus
        assert uitkomst.score is None
        assert uitkomst.violation is None

    @pytest.mark.parametrize(
        ("casus", "begrip", "tekst"),
        [
            ("ESS04-C05 fout voorbeeld", "object", FOUTE_VOORBEELDEN[0]),
            ("ESS04-C03 goed voorbeeld", "veelhoek", GOED_VOORBEELD),
        ],
    )
    async def test_volledige_set_geeft_nooit_automatisch_ess04_oordeel(
        self, svc, casus, begrip, tekst
    ):
        result = await svc.validate_definition(begrip=begrip, text=tekst, context={})
        assert result["validation_status"] == "validated"
        assert result["rule_statuses"]["ESS-04"] == "review_required", casus
        assert "ESS-04" not in result["passed_rules"]
        assert not any(v.get("code") == "ESS-04" for v in result["violations"])
        assert "ESS-04" not in (result.get("rule_scores") or {})
        item = next(r for r in result["review_required"] if r["rule_id"] == "ESS-04")
        assert item["reason"]
        assert result["overall_score"] is None
