"""DEF-667: geen enkele evaluator mag een fout in een pass laten eindigen.

Drie fail-open resten uit de review van PR #397:

1. `generic._gecompileerde_patronen` ving `re.error` af met een lege lijst en
   cachete die. Eén onbruikbaar patroon zette daarmee álle patronen van de
   regel uit, procesbreed. Zelfde constructie in `judgment_review` en
   `ontological_category`; `redundancy_patterns` deed hetzelfde met een stil
   `continue`.
2. `context_metadata.evaluate` negeerde de uitkomst van
   `_signaleer_duplicaat`, dat elke uitzondering met een warning slikte. Bij
   een repositorystoring kon een duplicaat ongemerkt worden vastgesteld.
3. De hardgecodeerde `additional_patterns` gaan langs de contractvalidatie
   heen; zij hebben hun eigen guard nodig.

De contractvalidatie bij het laden (zie `test_rule_loader_failclosed.py`)
houdt kapotte patronen nu buiten de deur. Deze suite dekt de tweede lijn af:
komt een ongeldig patroon tóch tot de runtime — een handgebouwd record, een
lader die wordt omzeild — dan is de uitkomst `error`, nooit `pass`.
"""

from __future__ import annotations

import re
from types import MappingProxyType
from typing import Any

import pytest

from services.validation.evaluators.base import EvaluationDeps
from services.validation.evaluators.duplicate_detection import (
    DUPLICATE_LOOKUP_METHODE,
)
from services.validation.evaluators.generic import GenericEvaluator
from services.validation.evaluators.judgment_review import JudgmentReviewEvaluator
from services.validation.evaluators.ontological_category import (
    OntologicalCategoryEvaluator,
)
from services.validation.modular_validation_service import ModularValidationService
from services.validation.readiness import (
    RuntimeSnapshot,
    bepaal_readiness,
    bereken_fingerprint,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.manager import get_toetsregel_manager
from toetsregels.runtime_contract import (
    AutomationStatus,
    EvaluatorType,
    Executability,
    RequiredInput,
    ResultStatus,
    RuleRecord,
    ScorePolicy,
)
from validation.additional_patterns import all_additional_patterns


def _publiceer_snapshot(
    svc,
    records=None,
    *,
    internal=None,
    weights=None,
    json_rules=None,
):
    """DEF-621: publiceer een volledige generatie i.p.v. losse privevelden.

    De guard vergelijkt de geladen ID-verzameling met de contractuele set.
    Een synthetische regelset is per definitie niet de echte 53, dus
    `contract_rule_ids` is hier gelijk aan de synthetische set - anders zou
    elke synthetische test op `validation_unknown` stranden en niets meer
    over de evaluator bewijzen.

    De fingerprint komt uit de service zelf, zodat de eerstvolgende
    verversing niets ziet wijzigen en deze snapshot laat staan.
    """
    records = dict(records or {})
    ids = tuple(sorted(internal if internal is not None else records))
    svc._snapshot = RuntimeSnapshot(
        fingerprint=bereken_fingerprint(svc._fingerprintbronnen()),
        readiness=bepaal_readiness(ids, ids),
        contract_rule_ids=ids,
        internal_rules=ids,
        rule_records=MappingProxyType(records),
        json_rules=MappingProxyType(
            dict(json_rules)
            if json_rules is not None
            else {rid: dict(r.data) for rid, r in records.items()}
        ),
        default_weights=MappingProxyType(dict(weights or dict.fromkeys(ids, 1.0))),
        pattern_cache={},
        rules_loaded_count=len(ids),
        rules_expected_count=len(ids),
        is_degraded_mode=False,
        degradation_reason=None,
    )
    return svc


pytestmark = [pytest.mark.unit]

KAPOT_PATROON = r"([onafgesloten"
RAKEND_PATROON = r"\bverboden\b"
TEKST = "besluit: een schriftelijke beslissing die verboden gedrag benoemt"


def _record(rule_id: str, data: dict[str, Any], evaluator: EvaluatorType) -> RuleRecord:
    """Bouw een record buiten `build_rule_record` om.

    Bewust rechtstreeks via de dataclass: de contractvalidatie zou dit
    record juist weigeren. Precies dat maakt het geschikt om te bewijzen dat
    de tweede lijn — de ERROR-grens in de service — óók sluit.
    """
    return RuleRecord(
        rule_id=rule_id,
        evaluator=evaluator,
        required_inputs=(RequiredInput.DEFINITION_TEXT,),
        executability=Executability.DETERMINISTIC,
        automation_status=AutomationStatus.AUTOMATED,
        score_policy=ScorePolicy.SCORED,
        data={"id": rule_id, "naam": "x", "uitleg": "x", "prioriteit": "hoog", **data},
    )


def _ctx() -> EvaluationContext:
    return EvaluationContext(raw_text=TEKST, cleaned_text=TEKST, begrip="besluit")


class _StubSupport:
    def severity_for(self, rule: dict[str, Any]) -> str:
        return "error"

    def severity_level_for(self, rule: dict[str, Any]) -> str:
        return "high"

    def build_suggestion(self, code, rule, text, ctx, *, reason, details=None) -> str:
        return "suggestie"


def _deps(**extra: Any) -> EvaluationDeps:
    return EvaluationDeps(
        support=_StubSupport(),
        available_inputs=frozenset(RequiredInput),
        pattern_cache={},
        **extra,
    )


class TestEvaluatorsSlikkenGeenPatroonfout:
    """Een onbruikbaar patroon mag nooit "geen patronen" gaan betekenen."""

    @pytest.mark.parametrize(
        ("evaluator", "velden", "type_"),
        [
            pytest.param(
                GenericEvaluator(),
                {"herkenbaar_patronen": [RAKEND_PATROON, KAPOT_PATROON]},
                EvaluatorType.GENERIC,
                id="generic/herkenbaar_patronen",
            ),
            pytest.param(
                GenericEvaluator(),
                {"required_patterns": [KAPOT_PATROON]},
                EvaluatorType.GENERIC,
                id="generic/required_patterns",
            ),
            pytest.param(
                GenericEvaluator(),
                {"redundancy_patterns": [KAPOT_PATROON]},
                EvaluatorType.GENERIC,
                id="generic/redundancy_patterns",
            ),
            pytest.param(
                JudgmentReviewEvaluator(),
                {"herkenbaar_patronen": [RAKEND_PATROON, KAPOT_PATROON]},
                EvaluatorType.JUDGMENT_REVIEW,
                id="judgment_review/herkenbaar_patronen",
            ),
            pytest.param(
                OntologicalCategoryEvaluator(),
                {"herkenbaar_patronen_type": [KAPOT_PATROON]},
                EvaluatorType.ONTOLOGICAL_CATEGORY,
                id="ontological_category/herkenbaar_patronen_type",
            ),
        ],
    )
    def test_kapot_patroon_werpt_door(self, evaluator, velden, type_):
        record = _record("SYN-01", velden, type_)
        with pytest.raises(re.error):
            evaluator.evaluate(record, _ctx(), _deps())

    def test_geen_lege_patroonlijst_in_de_cache(self):
        """De lege lijst was het gevaarlijkste deel: hij gold procesbreed.

        Na de eerste mislukte compilatie stond `pattern_cache[code] = []`
        vast; elke volgende evaluatie van die regel sloeg de patronen over,
        ook wanneer het record intussen was hersteld.
        """
        cache: dict[str, Any] = {}
        deps = EvaluationDeps(
            support=_StubSupport(),
            available_inputs=frozenset(RequiredInput),
            pattern_cache=cache,
        )
        record = _record(
            "SYN-01", {"herkenbaar_patronen": [KAPOT_PATROON]}, EvaluatorType.GENERIC
        )
        with pytest.raises(re.error):
            GenericEvaluator().evaluate(record, _ctx(), deps)
        assert not any(
            waarde == [] for waarde in cache.values()
        ), f"lege patroonlijst gecachet: {cache}"


class TestErrorGrensBoektGeenPass:
    """Bereikt een patroonfout de service, dan is de status `error`."""

    @pytest.mark.asyncio
    async def test_patroonfout_levert_error_en_geen_score(self):
        svc = ModularValidationService(get_toetsregel_manager(), None, None)
        # Injecteer ná het laden, zodat de contractvalidatie niet in de weg
        # zit maar de evaluatielus wél het echte pad draait.
        _publiceer_snapshot(
            svc,
            {
                "SYN-01": _record(
                    "SYN-01",
                    {"herkenbaar_patronen": [RAKEND_PATROON, KAPOT_PATROON]},
                    EvaluatorType.GENERIC,
                )
            },
        )

        res = await svc.validate_definition(
            begrip="besluit", text=TEKST, ontologische_categorie=None, context={}
        )

        assert res["rule_statuses"]["SYN-01"] == ResultStatus.ERROR.value, res
        assert "SYN-01" not in res["passed_rules"], res
        assert res["evaluation_coverage"]["error"] == 1, res["evaluation_coverage"]


class TestHardgecodeerdePatronen:
    """`additional_patterns` gaat langs de contractvalidatie heen.

    Die patronen staan in Python, niet in de JSON-records, dus
    `build_rule_record` ziet ze nooit. Zonder deze guard zou een typefout
    daar dezelfde stille bypass opleveren als de records vóór DEF-667.
    """

    def test_alle_aanvullende_patronen_compileren(self):
        kapot: list[str] = []
        for code, patronen in all_additional_patterns().items():
            for index, patroon in enumerate(patronen):
                try:
                    re.compile(patroon, re.IGNORECASE)
                except (re.error, TypeError) as exc:
                    kapot.append(f"{code}[{index}] {patroon!r}: {exc}")
        assert not kapot, "niet-compileerbare aanvullende patronen:\n- " + "\n- ".join(
            kapot
        )

    def test_mapping_is_niet_leeg(self):
        # Zonder deze assert zou een lege of verhuisde mapping de guard
        # hierboven stil laten slagen.
        assert all_additional_patterns(), "additional_patterns is leeg"


class _KapotteRepository:
    """Een aanwezige repository die tijdens de duplicaatcontrole faalt."""

    def find_duplicate_candidates(self, begrip: str) -> list[Any]:
        raise RuntimeError("database niet bereikbaar")


class TestRepositoryfoutIsGeenPass:
    """Een storing in de duplicaatcontrole is geen geslaagde CON-01.

    Gemeten op de oude HEAD: bij een falende repository logde CON-01 een
    warning en eindigde daarna op `pass`. Een duplicaat kon zo ongemerkt
    worden vastgesteld — de uitkomst zei dat er gecontroleerd was.
    """

    CONTEXT = {"organisatorische_context": ["DJI"]}
    TEKST = "besluit: een schriftelijke beslissing van een bestuursorgaan"

    @pytest.mark.asyncio
    async def test_repositorystoring_levert_error(self):
        svc = ModularValidationService(
            get_toetsregel_manager(), None, None, repository=_KapotteRepository()
        )
        res = await svc.validate_definition(
            begrip="besluit",
            text=self.TEKST,
            ontologische_categorie=None,
            context=self.CONTEXT,
        )
        # DEF-674: de duplicaatcontrole — en dus de repositorystoring — hoort
        # bij DUP_01, de regel die de database bevraagt.
        assert res["rule_statuses"]["DUP_01"] == ResultStatus.ERROR.value, res[
            "rule_statuses"
        ]
        assert "DUP_01" not in res["passed_rules"], res

    @pytest.mark.asyncio
    async def test_afwezige_repository_blijft_bestaand_gedrag(self):
        """Geen repository is geen storing.

        De duplicaatcontrole is optioneel; ontbreekt zij, dan blijft CON-01
        gewoon zijn patroontoets doen. Zonder deze test zou de fix hierboven
        de hele regel op `error` kunnen zetten voor elke aanroep zonder
        repository — de UI valideert standaard zonder.
        """
        svc = ModularValidationService(get_toetsregel_manager(), None, None)
        res = await svc.validate_definition(
            begrip="besluit",
            text=self.TEKST,
            ontologische_categorie=None,
            context=self.CONTEXT,
        )
        assert res["rule_statuses"]["CON-01"] in (
            ResultStatus.PASS.value,
            ResultStatus.FAIL.value,
        ), res["rule_statuses"]


class _RepositoryZonderDuplicaatzoeker:
    """De productievorm: repository aanwezig, capability afwezig.

    `DefinitionRepository` — het object dat de orchestrator werkelijk
    injecteert — heeft geen `_get_all_definitions`; die is in DEF-176 als dode
    code verwijderd. Gemeten: `hasattr(...) is False`, en geen `__getattr__`.
    """

    def save(self) -> None: ...


class TestOnbereikbareDuplicaatcontroleIsNietStil:
    """DEF-672: een bedradingsdefect mag niet als geslaagde controle passeren.

    De capability-guard nam elke productie-aanroep en returnde stil, waarna
    CON-01 een gemeten `pass` meldde. De controle is daarmee nooit gelopen.
    De echte bedrading vraagt een genormaliseerde duplicaatquery over de
    persistentiegrens (specificatiebesluit 2) en is belegd bij DEF-672; tot dan
    moet de fout minstens zichtbaar zijn.
    """

    @pytest.mark.asyncio
    async def test_ontbrekende_capability_wordt_gemeld(self, caplog):
        import logging

        svc = ModularValidationService(
            get_toetsregel_manager(),
            None,
            None,
            repository=_RepositoryZonderDuplicaatzoeker(),
        )
        with caplog.at_level(logging.ERROR):
            res = await svc.validate_definition(
                begrip="besluit",
                text="besluit: een schriftelijke beslissing van een bestuursorgaan",
                ontologische_categorie=None,
                context={"organisatorische_context": ["DJI"]},
            )

        meldingen = [
            bericht.getMessage()
            for bericht in caplog.records
            if bericht.levelno >= logging.ERROR
        ]
        assert any(
            "DEF-672" in melding and "Duplicaatcontrole" in melding
            for melding in meldingen
        ), f"bedradingsdefect bleef stil; gelogd: {meldingen}"
        # Bewust géén error-status: dat zou met de errorblokkade elke
        # productievalidatie afkeuren. De patroontoets van CON-01 loopt door.
        assert res["rule_statuses"]["CON-01"] in (
            ResultStatus.PASS.value,
            ResultStatus.FAIL.value,
        ), res["rule_statuses"]

    def test_de_echte_repository_biedt_de_capability(self):
        """De aanleiding van DEF-672 is weg: de bedrading klopt nu.

        De guard hierboven blijft staan voor repositories die de capability
        niet bieden — een test- of integratie-implementatie die achterloopt
        mag niet stilzwijgend een gemeten `pass` opleveren. Maar de
        productieketen mag hem nooit meer raken.
        """
        from services.definition_repository import DefinitionRepository

        assert hasattr(DefinitionRepository, DUPLICATE_LOOKUP_METHODE), (
            f"DefinitionRepository biedt {DUPLICATE_LOOKUP_METHODE!r} niet meer — "
            f"de duplicaatcontrole is opnieuw onbereikbaar (DEF-672)"
        )
