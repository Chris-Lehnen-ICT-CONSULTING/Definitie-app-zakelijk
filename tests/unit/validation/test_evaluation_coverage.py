"""DEF-668: dekking meet tegen het rulecontract, niet tegen de gedraaide set.

`_bereken_dekking` gebruikte `totaal = len(rule_statuses)`. In fallback-modus
draaien zeven baselineregels, en de dekking meldde dan `total=7` met
`coverage_ratio=1.0` — volledige dekking, op het moment dat 46 van de 53
contractregels nooit hebben gedraaid. Uit de eigen docstring van die functie:
*"Een lagere dekking mag nooit als hogere kwaliteit verschijnen."*

De noemer komt daarom uit het `rule_ids`-manifest in de root-SSOT, en de
niet-uitgevoerde regels staan expliciet als `not_evaluated` in
`rule_statuses`. Alleen de noemer optrekken zou niet volstaan: dan telt de
som van de statussen niet meer op tot `total` en is het dekkingsblok intern
tegenstrijdig.
"""

from __future__ import annotations

import pytest

from services.validation import modular_validation_service as mvs
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager
from toetsregels.runtime_contract import (
    ResultStatus,
    RuleContractError,
    root_contract_policy,
)

pytestmark = [pytest.mark.unit]

CONTRACT_IDS = tuple(root_contract_policy().rule_ids)
BASELINE = (
    "VAL-EMP-001",
    "VAL-LEN-001",
    "VAL-LEN-002",
    "ESS-CONT-001",
    "CON-CIRC-001",
    "STR-TERM-001",
    "STR-ORG-001",
)
TEKST = "besluit: een schriftelijke beslissing van een bestuursorgaan"


async def _resultaat(svc: ModularValidationService) -> dict:
    return await svc.validate_definition(
        begrip="besluit", text=TEKST, ontologische_categorie=None, context={}
    )


def _som_van_de_statussen(dekking: dict) -> int:
    return (
        dekking["passed"]
        + dekking["failed"]
        + dekking["review_required"]
        + dekking["not_evaluated"]
        + dekking["error"]
    )


class TestFallbackMeldtGeenVolledigeDekking:
    """De gemeten kern van bevinding 2, op het pad waar zij zichtbaar was."""

    @pytest.fixture(scope="class")
    def fallback(self) -> dict:
        import asyncio

        # Geen ToetsregelManager: de service valt terug op de zeven
        # ingebouwde baselineregels. Dat is exact de degraded-modus waarin de
        # oude dekking 7/7 = 1,0 meldde.
        return asyncio.run(_resultaat(ModularValidationService(None, None, None)))

    def test_noemer_is_de_contractset(self, fallback):
        assert fallback["evaluation_coverage"]["total"] == len(CONTRACT_IDS) == 53

    def test_dekking_is_zeven_van_drieenvijftig(self, fallback):
        dekking = fallback["evaluation_coverage"]
        assert dekking["evaluated"] == len(BASELINE) == 7
        assert dekking["coverage_ratio"] == pytest.approx(7 / 53, abs=1e-4)
        assert dekking["coverage_ratio"] < 1.0, (
            "fallback-modus meldt nog steeds volledige dekking terwijl 46 "
            "regels niet hebben gedraaid"
        )

    def test_de_niet_gedraaide_regels_zijn_zichtbaar(self, fallback):
        statussen = fallback["rule_statuses"]
        niet_gedraaid = sorted(set(CONTRACT_IDS) - set(BASELINE))
        assert len(niet_gedraaid) == 46
        ontbreekt = [rid for rid in niet_gedraaid if rid not in statussen]
        assert not ontbreekt, f"onzichtbare regels in rule_statuses: {ontbreekt}"
        verkeerd = {
            rid: statussen[rid]
            for rid in niet_gedraaid
            if statussen[rid] != ResultStatus.NOT_EVALUATED.value
        }
        assert not verkeerd, f"niet-gedraaide regels met andere status: {verkeerd}"

    def test_tellingen_sluiten_op_de_noemer(self, fallback):
        # De valkuil die de opdracht expliciet benoemt: alleen de noemer op 53
        # zetten terwijl de statusaantallen tot 7 optellen.
        dekking = fallback["evaluation_coverage"]
        assert _som_van_de_statussen(dekking) == dekking["total"]
        assert len(fallback["rule_statuses"]) == dekking["total"]

    def test_lagere_dekking_verschijnt_niet_als_hogere_kwaliteit(self, fallback):
        # Score en dekking zijn twee getallen. De score mag hoog zijn; de
        # dekking moet dan nog steeds laag rapporteren.
        dekking = fallback["evaluation_coverage"]
        assert dekking["coverage_ratio"] < 0.2, dekking
        assert 0.0 <= fallback["overall_score"] <= 1.0


class TestVolledigeSetDektDeNoemer:
    @pytest.fixture(scope="class")
    def volledig(self) -> dict:
        import asyncio

        return asyncio.run(
            _resultaat(ModularValidationService(get_toetsregel_manager(), None, None))
        )

    def test_alle_contractregels_hebben_een_status(self, volledig):
        ontbreekt = sorted(set(CONTRACT_IDS) - set(volledig["rule_statuses"]))
        assert not ontbreekt, f"contractregels zonder status: {ontbreekt}"

    def test_noemer_blijft_de_contractset(self, volledig):
        dekking = volledig["evaluation_coverage"]
        assert dekking["total"] == len(CONTRACT_IDS)
        assert _som_van_de_statussen(dekking) == dekking["total"]

    def test_dekking_is_niet_volledig_zolang_regels_zijn_uitgesteld(self, volledig):
        # 12 oordeelregels + 5 uitgestelde regels kunnen per contract niet
        # automatisch worden beoordeeld. Zou de dekking hier 1,0 melden, dan
        # zou zij die zeventien regels stil als gemeten presenteren.
        dekking = volledig["evaluation_coverage"]
        assert dekking["coverage_ratio"] < 1.0, dekking
        assert dekking["review_required"] + dekking["not_evaluated"] > 0, dekking


class TestGeenMagischGetalAlsNoemer:
    """De root-SSOT is de enige bron; een kapotte config faalt zichtbaar.

    `_tel_regelbestanden` viel bij een onleesbare root-SSOT terug op het
    magische getal 45, terwijl elk ander pad bij diezelfde fout hard faalt.
    Een dekkingsnoemer die uit de lucht komt vallen is precies zo misleidend
    als een noemer die met de gedraaide set meebeweegt.
    """

    def test_kapotte_root_ssot_laat_de_service_niet_starten(self, monkeypatch):
        def _kapot():
            raise RuleContractError("root-SSOT niet leesbaar")

        monkeypatch.setattr(mvs, "root_contract_policy", _kapot)
        with pytest.raises(RuleContractError):
            ModularValidationService(None, None, None)

    def test_verwachte_telling_komt_uit_het_manifest(self):
        svc = ModularValidationService(None, None, None)
        assert svc._rules_expected_count == len(CONTRACT_IDS) == 53
