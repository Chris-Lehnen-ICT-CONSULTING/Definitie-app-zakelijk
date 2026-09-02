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


class TestOnvolledigeSetLevertGeenOordeel:
    """Herfundering van bevinding 2 op de fail-closed guard (DEF-621).

    Deze klasse mat oorspronkelijk of de dekkingsnoemer klopte terwijl de
    validatie in fallback-modus gewoon doorliep: zeven baselineregels, dekking
    7/7 = 1,0. Het veiligheidsdoel was dat een lagere dekking nooit als hogere
    kwaliteit mag verschijnen.

    Sinds de guard wordt die toestand een stap eerder afgevangen: er wordt bij
    een onvolledige regelset helemaal niet meer geevalueerd. Het doel blijft
    identiek en wordt hier scherper bewezen - niet "de noemer klopt", maar
    "er is geen oordeel, en dat is zichtbaar".
    """

    @pytest.fixture(scope="class")
    def onvolledig(self) -> dict:
        import asyncio

        # Geen ToetsregelManager: nul van drieenvijftig regels geladen.
        # De zeven interne defaults zijn vangnetten in de uitvoervolgorde,
        # geen geladen contractregels - ze meetellen als lading zou precies
        # de gaten opvullen die de guard moet signaleren.
        return asyncio.run(_resultaat(ModularValidationService(None, None, None)))

    def test_er_wordt_geen_oordeel_geproduceerd(self, onvolledig):
        assert onvolledig["validation_status"] == "validation_unknown"
        assert onvolledig["unknown_reason"] == "ruleset_incomplete"

    def test_score_en_oordeel_zijn_slechts_placeholders(self, onvolledig):
        # 0.0 is hier geen kwaliteitsoordeel maar een fail-closed
        # compatibiliteitswaarde; False betekent "niet doorgaan", niet
        # "inhoudelijk afgekeurd".
        assert onvolledig["overall_score"] == 0.0
        assert onvolledig["is_acceptable"] is False

    def test_dekking_meldt_nul_gemeten_van_drieenvijftig(self, onvolledig):
        dekking = onvolledig["evaluation_coverage"]
        assert dekking["evaluated"] == 0
        assert dekking["total"] == len(CONTRACT_IDS) == 53
        assert dekking["not_evaluated"] == 53
        assert dekking["coverage_ratio"] == 0.0
        assert _som_van_de_statussen(dekking) == dekking["total"]

    def test_geen_enkele_regel_draagt_een_status(self, onvolledig):
        # De oude valkuil was een status per gedraaide regel plus een
        # opgetrokken noemer. Nu draait er niets, dus is er ook niets te
        # rapporteren - en dat mag niet als dekking verschijnen.
        assert onvolledig["rule_statuses"] == {}

    def test_de_kloof_is_zichtbaar_in_readiness(self, onvolledig):
        # Zonder manager is er niets geladen. De zeven interne vangnetten
        # telden hier eerder mee als lading, waardoor readiness 46 in plaats
        # van 53 ontbrekende regels meldde en een set van 52 als compleet kon
        # gelden. De hele kloof hoort zichtbaar te zijn, niet zes zevende.
        readiness = onvolledig["validation_readiness"]
        assert readiness["ready"] is False
        assert readiness["loaded_total"] == 0
        assert readiness["expected_total"] == len(CONTRACT_IDS) == 53
        ontbrekend = set(readiness["missing_rule_ids"])
        assert len(readiness["missing_rule_ids"]) == 53
        assert len(ontbrekend) == 53, sorted(ontbrekend)
        assert ontbrekend == set(CONTRACT_IDS)


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


class TestNoemerEnManifestVallenSamenInProductie:
    """DEF-673: `total` is de unie, dus die moet in productie het manifest zijn.

    `_vul_niet_uitgevoerde_regels` vult alleen contract-ID_s aan, dus
    `rule_statuses` is de unie van het manifest en de codes die werkelijk
    hebben gedraaid. Zolang die twee samenvallen is `coverage_ratio` een
    percentage van het contract. Vallen ze uiteen, dan verschuift de betekenis
    van dat getal — en dat mag niet stil gebeuren.
    """

    @pytest.mark.asyncio
    async def test_geladen_set_is_exact_het_manifest(self):
        res = await _resultaat(
            ModularValidationService(get_toetsregel_manager(), None, None)
        )
        statussen = set(res["rule_statuses"])
        manifest = set(CONTRACT_IDS)
        assert statussen == manifest, (
            f"buiten het manifest: {sorted(statussen - manifest)} · "
            f"manifest zonder status: {sorted(manifest - statussen)}"
        )
        assert res["evaluation_coverage"]["total"] == len(manifest)

    @pytest.mark.asyncio
    async def test_code_buiten_het_manifest_blokkeert_de_validatie(self):
        """Een onverwachte regel schuift de noemer niet meer op; hij blokkeert.

        Oorspronkelijk mat deze test of een code buiten het manifest de
        dekkingsnoemer naar 54 verschoof en of dat gemeld werd. Sinds de guard
        is een set met een onverwachte code per definitie geen dekkende set:
        de validatie stopt ervoor. Het veiligheidsdoel - de betekenis van
        `coverage_ratio` mag niet stil verschuiven - wordt daarmee harder
        gehaald dan met een waarschuwing.

        De regelset wordt hier via een manager aangeboden, niet via het
        muteren van verwijderde privevelden: het contract loopt door de
        echte laadweg.
        """
        echte = get_toetsregel_manager().get_all_regels()
        gekloond = dict(next(iter(echte.values())))
        gekloond["id"] = "SYN-99"

        class _ManagerMetExtraRegel:
            regels_dir = None

            def get_all_regels(self):
                return {**echte, "SYN-99": gekloond}

            def clear_cache(self):
                return None

        res = await _resultaat(
            ModularValidationService(_ManagerMetExtraRegel(), None, None)
        )

        assert res["validation_status"] == "validation_unknown", res
        assert res["unknown_reason"] == "ruleset_incomplete"
        readiness = res["validation_readiness"]
        assert "SYN-99" in readiness["unexpected_rule_ids"], readiness
        assert readiness["ready"] is False
        # Geen evaluatie, en de noemer is niet naar 54 opgerekt.
        assert res["rule_statuses"] == {}
        assert res["evaluation_coverage"]["evaluated"] == 0
        assert res["evaluation_coverage"]["total"] == len(CONTRACT_IDS)


class TestGeenMagischGetalAlsNoemer:
    """De root-SSOT is de enige bron; een kapotte config faalt zichtbaar.

    `_tel_regelbestanden` viel bij een onleesbare root-SSOT terug op het
    magische getal 45, terwijl elk ander pad bij diezelfde fout hard faalt.
    Een dekkingsnoemer die uit de lucht komt vallen is precies zo misleidend
    als een noemer die met de gedraaide set meebeweegt.
    """

    def test_kapotte_root_ssot_laat_de_directe_loader_hard_falen(self, monkeypatch):
        """De contractloader blijft fail-closed; alleen de service vangt hem op.

        Het oorspronkelijke doel blijft overeind: bij een onleesbare root-SSOT
        mag nergens een verzonnen verwacht aantal opduiken. De grens is alleen
        verlegd - de lader gooit nog steeds, en de runtime vertaalt dat naar
        een beschikbare maar onbepaalde validatie in plaats van een
        applicatie die niet start.
        """

        # DEF-621 commit 4: de service leest de policy vers uit `ROOT_SSOT_PAD`.
        # De naad staat daarom op `load_root_contract_policy`, dat een
        # optioneel pad aanneemt - vandaar de argumenten op de stub.
        def _kapot(*a, **kw):
            raise RuleContractError("root-SSOT niet leesbaar")

        monkeypatch.setattr(mvs, "load_root_contract_policy", _kapot)

        # a) de directe loader blijft hard falen
        with pytest.raises(RuleContractError):
            mvs.load_root_contract_policy()

        # b) de service construeert wel, en levert validation_unknown
        import asyncio

        svc = ModularValidationService(None, None, None)
        res = asyncio.run(_resultaat(svc))
        assert res["validation_status"] == "validation_unknown", res
        assert res["unknown_reason"] == "ruleset_incomplete"

        # c) geen magisch verwacht aantal zoals 45
        assert svc._snapshot.rules_expected_count == 0
        assert res["validation_readiness"]["expected_total"] == 0

    def test_verwachte_telling_komt_uit_het_manifest(self):
        svc = ModularValidationService(None, None, None)
        assert svc._snapshot.rules_expected_count == len(CONTRACT_IDS) == 53
