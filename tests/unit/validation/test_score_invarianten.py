"""DEF-670: de kerninvariant van DEF-624 heeft een runtime-test nodig.

De review op PR #397 stelde vast dat géén enkele test `overall_score`
asserteert ná een run met `review_required`, `not_evaluated` of `error`, en
dat de ERROR-tak volledig ongedekt was. Het contract dwingt de combinatie
"niet automatisch én scored" af (`_eis_consistente_klasse`), dus zolang de
records geldig zijn kán zo'n regel de score niet raken. Precies daarom
bewijzen deze tests de tweede lijn: ook een regel die zichzélf `scored`
noemt en tóch geen pass/fail oplevert, mag de score niet bewegen.

De records hieronder worden daarom rechtstreeks via de dataclass gebouwd —
`build_rule_record` zou ze weigeren. Dat is het punt: de scoreplumbing mag
niet op de contractvalidatie leunen om deze invariant te halen.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any

import pytest

from services.validation.modular_validation_service import ModularValidationService
from services.validation.readiness import (
    RuntimeSnapshot,
    bepaal_readiness,
    bereken_fingerprint,
)
from toetsregels.runtime_contract import (
    AutomationStatus,
    EvaluatorType,
    Executability,
    RequiredInput,
    ResultStatus,
    RuleRecord,
    ScorePolicy,
)


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

TEKST = (
    "besluit: een schriftelijke beslissing van een bestuursorgaan inzake een aanvraag"
)
RAAKT = r"\bbeslissing\b"
KAPOT = r"([onafgesloten"


def _record(
    rule_id: str,
    evaluator: EvaluatorType,
    *,
    patronen: list[str] | None = None,
) -> RuleRecord:
    """Een record dat zich `automated` + `scored` noemt, wat de evaluator ook doet.

    Bewust buiten `build_rule_record` om: die zou een niet-automatische status
    met `scored` afwijzen. Deze test moet juist bewijzen dat de scoreplumbing
    zelfstandig sluit.
    """
    data: dict[str, Any] = {
        "id": rule_id,
        "naam": f"Invariantregel {rule_id}",
        "uitleg": "Alleen voor de score-invariant.",
        "prioriteit": "hoog",
        "aanbeveling": "verplicht",
    }
    if patronen is not None:
        data["herkenbaar_patronen"] = patronen
    return RuleRecord(
        rule_id=rule_id,
        evaluator=evaluator,
        required_inputs=(RequiredInput.DEFINITION_TEXT,),
        executability=Executability.DETERMINISTIC,
        automation_status=AutomationStatus.AUTOMATED,
        score_policy=ScorePolicy.SCORED,
        data=data,
    )


# Twee ijkregels met een bekende uitkomst: SYN-FAIL vuurt op de tekst,
# SYN-PASS niet. Samen leveren zij een score die noch 0 noch 1 is, zodat een
# derde regel die onterecht meetelt zichtbaar verschuift.
FAALREGEL = _record("SYN-FAIL", EvaluatorType.GENERIC, patronen=[RAAKT])
SLAAGREGEL = _record("SYN-PASS", EvaluatorType.GENERIC, patronen=[r"\bkomtnietvoor\b"])

# De drie statussen die nooit als pass mogen meetellen.
NIET_GEMETEN: list[Any] = [
    pytest.param(
        _record("SYN-REVIEW", EvaluatorType.JUDGMENT_REVIEW),
        ResultStatus.REVIEW_REQUIRED,
        id="review_required",
    ),
    pytest.param(
        _record("SYN-DEFER", EvaluatorType.DEFINITION_GRAPH),
        ResultStatus.NOT_EVALUATED,
        id="not_evaluated",
    ),
    pytest.param(
        _record("SYN-ERROR", EvaluatorType.GENERIC, patronen=[KAPOT]),
        ResultStatus.ERROR,
        id="error",
    ),
]


def _svc(*records: RuleRecord) -> ModularValidationService:
    svc = ModularValidationService(None, None, None)
    _publiceer_snapshot(svc, {record.rule_id: record for record in records})
    return svc


async def _run(*records: RuleRecord) -> dict:
    return await _svc(*records).validate_definition(
        begrip="besluit", text=TEKST, ontologische_categorie=None, context={}
    )


class TestIjkregelsMetenIets:
    """Zonder deze twee asserties zou de invariant-test niets kunnen aantonen."""

    @pytest.mark.asyncio
    async def test_de_faalregel_faalt_en_de_slaagregel_slaagt(self):
        res = await _run(FAALREGEL, SLAAGREGEL)
        assert res["rule_statuses"]["SYN-FAIL"] == ResultStatus.FAIL.value, res
        assert res["rule_statuses"]["SYN-PASS"] == ResultStatus.PASS.value, res

    @pytest.mark.asyncio
    async def test_een_extra_geslaagde_regel_beweegt_de_score_wel(self):
        # De controle op de controle: beweegt de score hier niet, dan bewijst
        # "de score beweegt niet" bij de andere statussen ook niets.
        basis = await _run(FAALREGEL, SLAAGREGEL)
        extra = _record(
            "SYN-PASS2", EvaluatorType.GENERIC, patronen=[r"\bnietaanwezig\b"]
        )
        met_extra = await _run(FAALREGEL, SLAAGREGEL, extra)
        assert met_extra["overall_score"] > basis["overall_score"], (
            f"score beweegt niet mee met een extra pass "
            f"({basis['overall_score']} → {met_extra['overall_score']})"
        )


class TestAlleenPassEnFailRakenDeScore:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(("record", "verwachte_status"), NIET_GEMETEN)
    async def test_status_is_wat_hij_hoort_te_zijn(self, record, verwachte_status):
        res = await _run(FAALREGEL, SLAAGREGEL, record)
        assert res["rule_statuses"][record.rule_id] == verwachte_status.value, res[
            "rule_statuses"
        ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("record", "verwachte_status"), NIET_GEMETEN)
    async def test_score_beweegt_niet(self, record, verwachte_status):
        basis = await _run(FAALREGEL, SLAAGREGEL)
        met = await _run(FAALREGEL, SLAAGREGEL, record)
        assert met["overall_score"] == basis["overall_score"], (
            f"{verwachte_status.value} telt mee in de score: "
            f"{basis['overall_score']} → {met['overall_score']}"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("record", "verwachte_status"), NIET_GEMETEN)
    async def test_geldt_niet_als_geslaagde_regel(self, record, verwachte_status):
        res = await _run(FAALREGEL, SLAAGREGEL, record)
        assert record.rule_id not in res["passed_rules"], res["passed_rules"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("record", "verwachte_status"), NIET_GEMETEN)
    async def test_valt_buiten_de_gemeten_dekking(self, record, verwachte_status):
        res = await _run(FAALREGEL, SLAAGREGEL, record)
        dekking = res["evaluation_coverage"]
        sleutel = {
            ResultStatus.REVIEW_REQUIRED: "review_required",
            ResultStatus.NOT_EVALUATED: "not_evaluated",
            ResultStatus.ERROR: "error",
        }[verwachte_status]
        assert dekking[sleutel] >= 1, dekking
        # De twee ijkregels zijn de énige gemeten regels.
        assert dekking["evaluated"] == 2, dekking
        assert dekking["passed"] == 1 and dekking["failed"] == 1, dekking


class TestErrorTakIsGedekt:
    """De ERROR-tak was volledig ongedekt (review, bevinding 6)."""

    @pytest.mark.asyncio
    async def test_error_levert_geen_violation_en_geen_pass(self):
        record = _record("SYN-ERROR", EvaluatorType.GENERIC, patronen=[KAPOT])
        res = await _run(FAALREGEL, SLAAGREGEL, record)
        assert res["rule_statuses"]["SYN-ERROR"] == ResultStatus.ERROR.value, res
        assert "SYN-ERROR" not in res["passed_rules"], res
        assert not any(
            v.get("code") == "SYN-ERROR" for v in res["violations"]
        ), "een evaluatorfout is geen inhoudelijke violation"

    @pytest.mark.asyncio
    async def test_error_wordt_gelogd(self, caplog):
        import logging

        record = _record("SYN-ERROR", EvaluatorType.GENERIC, patronen=[KAPOT])
        with caplog.at_level(logging.WARNING):
            await _run(FAALREGEL, SLAAGREGEL, record)
        assert any(
            "SYN-ERROR" in bericht.getMessage() for bericht in caplog.records
        ), "een evaluatorfout mag niet stil blijven"
