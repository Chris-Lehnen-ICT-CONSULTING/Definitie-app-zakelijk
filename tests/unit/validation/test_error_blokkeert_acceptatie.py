"""Een mislukte meting mag de uitkomst niet gunstiger maken (herreview PR 397).

`calculate_weighted_score` itereert over `rule_scores`. De ERROR-tak van
`_verwerk_uitkomst` boekt daar niets in, dus een geërrorde regel valt uit
**teller én noemer**. Zou die regel gefaald hebben (score 0,0), dan stijgt het
gemiddelde doordat hij wegvalt.

Gemeten met een repository die `RuntimeError` gooit, identieke invoer:

| | CON-01 | overall_score |
| --- | --- | --- |
| fout geslikt (vóór DEF-667) | `fail` | 0,74 |
| fail-closed (ná DEF-667) | `error` | 0,75 |

0,75 is `hard_min_score` in het vestigingsbeleid, dus een mislukte controle duwt
de definitie over de harde drempel. Dat is de kernclaim van deze PR omgekeerd:
een lagere dekking verschijnt als hogere kwaliteit.

Besluit: de score blijft puur over `pass`/`fail` (specificatiebesluit 6), maar
een `error` blokkeert de acceptatie. Een validatie die niet uitgevoerd kón
worden is geen goedgekeurde validatie.
"""

from __future__ import annotations

from typing import Any

import pytest

from services.validation.modular_validation_service import ModularValidationService
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

pytestmark = [pytest.mark.unit]

# De exacte invoer waarmee de regressie is gemeten.
BEGRIP = "besluit"
TEKST = (
    "type document dat op grond van de wet een publiekrechtelijke "
    "rechtshandeling bevat met uniek zaaknummer"
)
CONTEXT = {
    "organisatorische_context": ["DJI"],
    "juridische_context": ["strafrecht"],
    "wettelijke_basis": ["Awb"],
}
HARDE_DREMPEL = 0.75


class _KapotteRepository:
    """Een aanwezige repository die op de publieke capability stukloopt."""

    def find_duplicate_candidates(self, begrip: str) -> list[Any]:
        raise RuntimeError("SQLite: database is locked")


async def _met_kapotte_repository() -> dict:
    svc = ModularValidationService(
        get_toetsregel_manager(), None, None, repository=_KapotteRepository()
    )
    return await svc.validate_definition(
        begrip=BEGRIP, text=TEKST, ontologische_categorie=None, context=CONTEXT
    )


class TestErrorBlokkeertAcceptatie:
    @pytest.mark.asyncio
    async def test_repositorystoring_maakt_het_resultaat_onacceptabel(self):
        res = await _met_kapotte_repository()
        # DEF-674: de duplicaatcontrole is verhuisd naar DUP_01, de regel die
        # de database bevraagt. Een storing daar is dus een DUP_01-error.
        assert res["rule_statuses"]["DUP_01"] == ResultStatus.ERROR.value, res[
            "rule_statuses"
        ]
        assert res["evaluation_coverage"]["error"] >= 1, res["evaluation_coverage"]
        assert res["is_acceptable"] is False, (
            f"score {res['overall_score']} haalt de drempel, maar DUP_01 kon niet "
            f"worden beoordeeld — dat mag geen goedkeuring opleveren"
        )

    @pytest.mark.asyncio
    async def test_de_score_zelf_blijft_over_pass_en_fail(self):
        """Besluit 6 blijft intact: de ERROR gaat niet als 0,0 de score in.

        Deze test eiste eerder `overall_score >= 0,75`, omdat de geërrorde
        regel (toen CON-01) uit teller én noemer viel en het gemiddelde
        daardoor stéég — precies de omgekeerde-kernclaim die de blokkade
        rechtvaardigde.

        Sinds DEF-674 draagt DUP_01 de duplicaatcontrole, en die regel is
        `excluded_from_score`. Een storing daar kan het cijfer dus per
        constructie niet meer bewegen. Dat is sterker te bewijzen dan met een
        drempel: dezelfde tekst moet met en zonder kapotte repository exact
        hetzelfde cijfer opleveren. Zou de ERROR alsnog als 0,0 meetellen, dan
        zakt de score en valt deze test om.
        """
        met_storing = await _met_kapotte_repository()
        svc = ModularValidationService(get_toetsregel_manager(), None, None)
        zonder = await svc.validate_definition(
            begrip=BEGRIP, text=TEKST, ontologische_categorie=None, context=CONTEXT
        )
        assert met_storing["overall_score"] == zonder["overall_score"], (
            "een mislukte duplicaatcontrole beweegt de kwaliteitsscore: "
            f"{met_storing['overall_score']} met storing tegen "
            f"{zonder['overall_score']} zonder"
        )
        # En de blokkade zit dus écht op de acceptatie, niet op het cijfer.
        assert met_storing["is_acceptable"] is False, met_storing["overall_score"]
        assert zonder["is_acceptable"] is True, zonder["overall_score"]

    @pytest.mark.asyncio
    async def test_zonder_repository_blijft_het_resultaat_acceptabel(self):
        # De tegenhanger: de blokkade mag niet elke validatie afkeuren. De UI
        # valideert standaard zonder repository, en dan is er geen error.
        svc = ModularValidationService(get_toetsregel_manager(), None, None)
        res = await svc.validate_definition(
            begrip=BEGRIP, text=TEKST, ontologische_categorie=None, context=CONTEXT
        )
        assert res["evaluation_coverage"]["error"] == 0, res["evaluation_coverage"]
        assert res["is_acceptable"] is True, (
            f"zonder errors hoort dezelfde tekst gewoon acceptabel te zijn "
            f"(score {res['overall_score']})"
        )


def _record(rule_id: str, patronen: list[str]) -> RuleRecord:
    """Handgebouwd record met een onbruikbaar patroon: levert `error` op."""
    return RuleRecord(
        rule_id=rule_id,
        evaluator=EvaluatorType.GENERIC,
        required_inputs=(RequiredInput.DEFINITION_TEXT,),
        executability=Executability.DETERMINISTIC,
        automation_status=AutomationStatus.AUTOMATED,
        score_policy=ScorePolicy.SCORED,
        data={
            "id": rule_id,
            "naam": "x",
            "uitleg": "x",
            "prioriteit": "hoog",
            "aanbeveling": "verplicht",
            "herkenbaar_patronen": patronen,
        },
    )


class TestGeldtVoorElkeErrorbron:
    """Niet alleen de repository: elke ERROR-bron moet de acceptatie stoppen."""

    def _svc(self, *records: RuleRecord) -> ModularValidationService:
        svc = ModularValidationService(get_toetsregel_manager(), None, None)
        svc._rule_records = {record.rule_id: record for record in records}
        svc._internal_rules = sorted(svc._rule_records.keys())
        svc._json_rules = {rid: dict(r.data) for rid, r in svc._rule_records.items()}
        svc._default_weights = dict.fromkeys(svc._rule_records, 1.0)
        svc._pattern_cache = {}
        return svc

    @pytest.mark.asyncio
    async def test_een_geslaagde_regel_alleen_is_acceptabel(self):
        # De ijking. Zonder deze test bewijst de volgende niets: een resultaat
        # met alléén een errored regel heeft score 0,0 en zou ook zonder
        # errorblokkade al onacceptabel zijn.
        res = await self._svc(
            _record("SYN-OK", [r"\bkomtnietvoor\b"])
        ).validate_definition(
            begrip=BEGRIP, text=TEKST, ontologische_categorie=None, context={}
        )
        assert res["rule_statuses"]["SYN-OK"] == ResultStatus.PASS.value, res
        assert res["is_acceptable"] is True, res

    @pytest.mark.asyncio
    async def test_patroonfout_blokkeert_ook(self):
        # Zelfde geslaagde regel, plus één regel die op een onbruikbaar patroon
        # stukloopt. De score blijft hoog; alleen de error mag de acceptatie
        # tegenhouden.
        res = await self._svc(
            _record("SYN-OK", [r"\bkomtnietvoor\b"]),
            _record("SYN-ERROR", [r"([onafgesloten"]),
        ).validate_definition(
            begrip=BEGRIP, text=TEKST, ontologische_categorie=None, context={}
        )
        assert res["rule_statuses"]["SYN-ERROR"] == ResultStatus.ERROR.value, res
        assert res["overall_score"] >= HARDE_DREMPEL, (
            f"score zakte naar {res['overall_score']}; dan blokkeert de drempel "
            f"al en meet deze test de errorblokkade niet"
        )
        assert res["is_acceptable"] is False, res
