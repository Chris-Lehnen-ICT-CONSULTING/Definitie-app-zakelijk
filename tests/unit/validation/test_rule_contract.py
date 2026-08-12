"""DEF-606 / DEF-624 Task 1 — contracttests voor het JSON-rulecontract.

Deze suite is de uitvoerbare specificatie van ADR-001. Zij toetst drie
lagen die vandaag geen van alle afdwingbaar zijn:

1. **Recordcontract** — ieder van de 53 JSON-regelrecords declareert precies
   één bekende evaluatorstrategie, expliciete vereiste invoer, een
   uitvoerbaarheidsklasse, een automatiseringsstatus en een scorepolicy.
2. **Registercontract** — evaluators worden expliciet geregistreerd; een
   onbekend type of een dubbele registratie faalt zichtbaar, en ontbrekende
   vereiste invoer levert nooit een pass.
3. **Semantisch contract** — de gedocumenteerde goed/fout-paren in de
   records zijn normatieve regressiecases: een automatisch geclassificeerde
   regel moet het eigen foute voorbeeld slechter beoordelen dan het goede.

Geen skips, geen xfails, geen faaltolerantie: een regel die zijn eigen
tegenvoorbeeld niet herkent moet hier rood worden.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

REGELS_DIR = Path(__file__).resolve().parents[3] / "src" / "toetsregels" / "regels"
RULE_IDS: list[str] = sorted(p.stem for p in REGELS_DIR.glob("*.json"))
RAW: dict[str, dict[str, Any]] = {
    rid: json.loads((REGELS_DIR / f"{rid}.json").read_text(encoding="utf-8"))
    for rid in RULE_IDS
}

# De 44 records die zowel een goed als een fout voorbeeld dragen. Dat is de
# door de bron zelf meegeleverde specificatie; zie
# docs/analyses/2026-08-11-DEF-606-inhoudelijk-antwoord.md §3.
VOORBEELDPAREN: list[str] = sorted(
    rid
    for rid in RULE_IDS
    if RAW[rid].get("goede_voorbeelden") and RAW[rid].get("foute_voorbeelden")
)


def _begrip_en_tekst(voorbeeld: str) -> tuple[str, str]:
    """Splits een voorbeeld in (begrip, volledige tekst).

    De records noteren voorbeelden als ``begrip: definitietekst``; enkele
    lemmagerichte regels (VER-01/VER-03) noteren alleen het lemma. De
    volledige string blijft de te valideren tekst — precies zoals
    ``runtime_cases.yaml`` het doet.
    """
    tekst = str(voorbeeld).strip()
    begrip = tekst.split(":", 1)[0].strip() if ":" in tekst else tekst
    return begrip, tekst


@pytest.fixture(scope="module")
def svc() -> ModularValidationService:
    return ModularValidationService(get_toetsregel_manager(), None, None)


async def _violations_voor(
    svc: ModularValidationService,
    rule_id: str,
    begrip: str,
    tekst: str,
    context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    res = await svc.validate_definition(
        begrip=begrip,
        text=tekst,
        ontologische_categorie=None,
        context=context or {},
    )
    return [
        v
        for v in res.get("violations", [])
        if str(v.get("code", "")).upper().replace("_", "-")
        == rule_id.upper().replace("_", "-")
    ]


class TestRecordContract:
    """Ieder record declareert zijn eigen uitvoerbaarheid."""

    def test_alle_53_records_aanwezig(self):
        assert len(RULE_IDS) == 53, f"verwacht 53 regelrecords, gevonden {RULE_IDS}"

    @pytest.mark.parametrize("rule_id", RULE_IDS, ids=str)
    def test_record_declareert_runtime_contract(self, rule_id):
        contract = RAW[rule_id].get("runtime_contract")
        assert isinstance(contract, dict) and contract, (
            f"{rule_id}: blok 'runtime_contract' ontbreekt — zonder contract "
            f"kan de runtime niet bewijzen welke evaluator deze regel draait"
        )

    @pytest.mark.parametrize("rule_id", RULE_IDS, ids=str)
    def test_evaluator_en_scorevelden_zijn_gesloten_waarden(self, rule_id):
        from toetsregels.runtime_contract import (
            AutomationStatus,
            EvaluatorType,
            Executability,
            RequiredInput,
            ScorePolicy,
        )

        contract = RAW[rule_id].get("runtime_contract") or {}
        assert contract.get("evaluator") in set(
            EvaluatorType
        ), f"{rule_id}: onbekende evaluator {contract.get('evaluator')!r}"
        assert contract.get("executability") in set(Executability), (
            f"{rule_id}: onbekende uitvoerbaarheidsklasse "
            f"{contract.get('executability')!r}"
        )
        assert contract.get("automation_status") in set(AutomationStatus), (
            f"{rule_id}: onbekende automatiseringsstatus "
            f"{contract.get('automation_status')!r}"
        )
        assert contract.get("score_policy") in set(
            ScorePolicy
        ), f"{rule_id}: onbekende scorepolicy {contract.get('score_policy')!r}"
        vereist = contract.get("required_inputs")
        assert isinstance(vereist, list), (
            f"{rule_id}: 'required_inputs' moet een lijst zijn (mag leeg), "
            f"gevonden {vereist!r}"
        )
        onbekend = sorted(set(vereist) - set(RequiredInput))
        assert not onbekend, f"{rule_id}: onbekende required inputs {onbekend}"

    @pytest.mark.parametrize("rule_id", RULE_IDS, ids=str)
    def test_record_id_matcht_bestandsnaam_canoniek(self, rule_id):
        from toetsregels.runtime_contract import canonical_rule_id

        assert canonical_rule_id(RAW[rule_id]["id"]) == canonical_rule_id(rule_id), (
            f"{rule_id}: veld 'id' is {RAW[rule_id]['id']!r} — ID/bestandsnaam-"
            f"drift mag niet stil blijven bestaan"
        )

    def test_records_bouwen_zonder_contractfout(self):
        from toetsregels.runtime_contract import build_rule_record

        for rule_id in RULE_IDS:
            build_rule_record(rule_id, RAW[rule_id])

    def test_onbekende_evaluator_faalt_zichtbaar(self):
        from toetsregels.runtime_contract import RuleContractError, build_rule_record

        kapot = dict(RAW["CON-01"])
        kapot["runtime_contract"] = {
            **(kapot.get("runtime_contract") or {}),
            "evaluator": "verzonnen_evaluator",
        }
        with pytest.raises(RuleContractError):
            build_rule_record("CON-01", kapot)

    def test_ontbrekend_contractblok_faalt_zichtbaar(self):
        from toetsregels.runtime_contract import RuleContractError, build_rule_record

        kaal = {k: v for k, v in RAW["CON-01"].items() if k != "runtime_contract"}
        with pytest.raises(RuleContractError):
            build_rule_record("CON-01", kaal)


class TestOordeelregels:
    """De oordeelregels zijn een besluit, geen bijproduct van de records.

    De lijsten hieronder staan bewust hárd in de test en worden niet uit de
    JSON afgeleid. Zou je ze afleiden, dan bevestigt de test elke wijziging
    die iemand in een record maakt — inclusief het per ongeluk terugzetten
    van een regel naar `automated`. Nu faalt de test in beide richtingen.
    """

    # Besluit DEF-624 (Cowork-onderzoek 2026-08-11, bevestigd door Chris).
    GOEDGEKEURD = frozenset(
        {
            "ARAI-03",
            "ESS-01",
            "ESS-04",
            "INT-02",
            "INT-06",
            "STR-03",
            "STR-05",
            "STR-06",
        }
    )
    # Oordeelregel mét repositorybehoefte: zonder begrippenverzameling kan
    # SAM-01 niet eens tot een oordeel komen.
    REPOSITORY_OORDEEL = frozenset({"SAM-01"})
    # Projectuitbreiding bovenop het besluit; vastgelegd bij DEF-624 omdat
    # hun patronen aantoonbaar ook op het eigen goede voorbeeld vuren.
    PROJECTUITBREIDING = frozenset({"INT-03", "STR-08", "STR-09"})

    @property
    def bedoeld(self) -> frozenset[str]:
        return self.GOEDGEKEURD | self.REPOSITORY_OORDEEL | self.PROJECTUITBREIDING

    def test_precies_de_bedoelde_regels_zijn_oordeelregels(self):
        feitelijk = {
            rule_id
            for rule_id in RULE_IDS
            if (RAW[rule_id].get("runtime_contract") or {}).get("evaluator")
            == "judgment_review"
        }
        assert feitelijk == self.bedoeld, (
            f"te veel: {sorted(feitelijk - self.bedoeld)} · "
            f"te weinig: {sorted(self.bedoeld - feitelijk)}"
        )

    @pytest.mark.parametrize(
        "rule_id",
        sorted(GOEDGEKEURD | REPOSITORY_OORDEEL | PROJECTUITBREIDING),
        ids=str,
    )
    def test_oordeelregel_draagt_de_volledige_klasse(self, rule_id):
        contract = RAW[rule_id].get("runtime_contract") or {}
        assert contract.get("executability") == "judgment", rule_id
        assert contract.get("automation_status") == "review_required", rule_id
        assert contract.get("score_policy") == "excluded_from_score", rule_id

    def test_sam01_vereist_de_begrippenverzameling(self):
        contract = RAW["SAM-01"]["runtime_contract"]
        assert "definition_repository" in contract["required_inputs"], (
            "SAM-01 toetst betekenisafwijking t.o.v. het algemeen aanvaarde "
            "begrip; zonder begrippenverzameling is dat niet te beoordelen"
        )

    @pytest.mark.asyncio
    async def test_sam01_zonder_repository_is_niet_geevalueerd(self, svc):
        status = await _status_voor(
            svc, "SAM-01", "koppeling", "koppeling: technisch verband tussen delen"
        )
        assert (
            status == "not_evaluated"
        ), f"SAM-01 zonder repository moet not_evaluated geven, niet {status!r}"

    @pytest.mark.asyncio
    async def test_sam01_met_repository_vraagt_review(self):
        svc = _svc_met_repository(
            [("proces", "proces: reeks activiteiten met een gemeenschappelijk doel")]
        )
        res = await svc.validate_definition(
            begrip="koppeling",
            text="koppeling: technisch verband tussen delen",
            ontologische_categorie=None,
            context={},
        )
        assert (res.get("rule_statuses") or {}).get("SAM-01") == "review_required", res
        review = {item["rule_id"]: item for item in res.get("review_required", [])}
        assert "SAM-01" in review, res
        # Patronen zijn een aanwijzing voor de reviewer, geen bewijs: ze
        # verschijnen als signaal en nooit als violation.
        assert review["SAM-01"]["signals"], review
        assert not any(
            v.get("code") == "SAM-01" for v in res.get("violations", [])
        ), res
        assert "SAM-01" not in res.get("passed_rules", []), res


class TestEvaluatorRegister:
    """Evaluators zijn expliciet geregistreerd; niets valt stil terug op pass."""

    def test_alle_gedeclareerde_evaluatortypen_zijn_geregistreerd(self):
        from services.validation.evaluators.registry import get_default_registry

        registry = get_default_registry()
        gedeclareerd = {
            (RAW[rid].get("runtime_contract") or {}).get("evaluator")
            for rid in RULE_IDS
        }
        ontbreekt = sorted(
            t for t in gedeclareerd if t not in registry.registered_types()
        )
        assert not ontbreekt, f"evaluatortypen zonder registratie: {ontbreekt}"

    def test_onbekend_type_resolven_faalt(self):
        from services.validation.evaluators.registry import (
            UnknownEvaluatorError,
            get_default_registry,
        )

        with pytest.raises(UnknownEvaluatorError):
            get_default_registry().resolve("verzonnen_evaluator")

    def test_dubbele_registratie_faalt(self):
        from services.validation.evaluators.generic import GenericEvaluator
        from services.validation.evaluators.registry import (
            DuplicateEvaluatorError,
            EvaluatorRegistry,
        )

        registry = EvaluatorRegistry()
        registry.register(GenericEvaluator())
        with pytest.raises(DuplicateEvaluatorError):
            registry.register(GenericEvaluator())

    def test_ontbrekende_required_input_levert_geen_pass(self):
        from toetsregels.runtime_contract import (
            RequiredInput,
            ResultStatus,
            build_rule_record,
            missing_inputs,
            status_for_missing_inputs,
        )

        record = build_rule_record("SAM-05", RAW["SAM-05"])
        ontbreekt = missing_inputs(record, beschikbaar=frozenset())
        assert (
            RequiredInput.DEFINITION_REPOSITORY in ontbreekt
        ), "SAM-05 moet de begrippenverzameling als vereiste invoer declareren"
        assert status_for_missing_inputs(ontbreekt) is not ResultStatus.PASS


class TestScoreEnDekking:
    """Niet-uitgevoerde regels tellen nooit als pass/1,0 mee in de score."""

    @pytest.mark.asyncio
    async def test_resultaat_rapporteert_evaluatiedekking(self, svc):
        res = await svc.validate_definition(
            begrip="toezicht",
            text="toezicht: systematisch volgen van handelingen om vast te stellen of zij aan normen voldoen",
            ontologische_categorie=None,
            context={"organisatorische_context": ["DJI"]},
        )
        dekking = res.get("evaluation_coverage")
        assert isinstance(dekking, dict), (
            "resultaat bevat geen 'evaluation_coverage' — score en dekking "
            "moeten afzonderlijk zichtbaar zijn"
        )
        for sleutel in (
            "evaluated",
            "review_required",
            "not_evaluated",
            "error",
            "total",
            "coverage_ratio",
        ):
            assert sleutel in dekking, f"dekkingsblok mist '{sleutel}'"
        assert dekking["total"] == 53

    @pytest.mark.asyncio
    async def test_review_required_telt_niet_als_pass(self, svc):
        res = await svc.validate_definition(
            begrip="toezicht",
            text="toezicht: systematisch volgen van handelingen om vast te stellen of zij aan normen voldoen",
            ontologische_categorie=None,
            context={"organisatorische_context": ["DJI"]},
        )
        statussen = res.get("rule_statuses") or {}
        assert statussen, "resultaat bevat geen per-regel resultaatstatus"
        review = {r for r, s in statussen.items() if s == "review_required"}
        assert review, (
            "geen enkele regel is review_required — de oordeelregels moeten "
            "expliciet reviewplichtig zijn in plaats van stil te passeren"
        )
        assert not (review & set(res.get("passed_rules", []))), (
            "review_required-regels staan in passed_rules; dat is precies de "
            "default-pass die het contract verbiedt"
        )


class TestSemantischeGaten:
    """De expliciete RED-cases uit het implementatieplan (Task 1 stap 2)."""

    @pytest.mark.asyncio
    async def test_sam06_zonder_voorkeursterm_passeert_niet_stil(self, svc):
        vios = await _violations_voor(
            svc,
            "SAM-06",
            "vonnis",
            "vonnis: rechterlijke beslissing, ook wel uitspraak genoemd",
            context={"synoniemen": ["uitspraak"], "voorkeursterm": None},
        )
        assert vios, (
            "SAM-06 blijft inert: zonder geselecteerde voorkeursterm hoort de "
            "regel te falen of reviewplichtig te zijn (DEF-621 defect 3)"
        )

    @pytest.mark.asyncio
    async def test_sam05_detecteert_cyclus_diepte_2(self):
        svc = _svc_met_repository(
            [
                ("beslissing", "beslissing: uitkomst van een oordeel"),
                ("oordeel", "oordeel: grond voor een beslissing"),
            ]
        )
        vios = await _violations_voor(
            svc, "SAM-05", "beslissing", "beslissing: uitkomst van een oordeel"
        )
        assert vios, "SAM-05 detecteert geen cyclus A→B→A"

    @pytest.mark.asyncio
    async def test_sam05_detecteert_cyclus_diepte_3(self):
        svc = _svc_met_repository(
            [
                ("aangifte", "aangifte: melding die leidt tot een onderzoek"),
                ("onderzoek", "onderzoek: handeling die leidt tot een rapport"),
                ("rapport", "rapport: vastlegging van een aangifte"),
            ]
        )
        vios = await _violations_voor(
            svc, "SAM-05", "aangifte", "aangifte: melding die leidt tot een onderzoek"
        )
        assert vios, "SAM-05 detecteert geen cyclus A→B→C→A"

    @pytest.mark.asyncio
    async def test_ver03_keurt_zelfstandig_naamwoord_op_t_niet_af(self, svc):
        vios = await _violations_voor(
            svc, "VER-03", "besluit", "besluit: vastgestelde keuze na afweging"
        )
        assert not vios, (
            f"VER-03 keurt het zelfstandig naamwoord 'besluit' af als vervoegd "
            f"werkwoord: {[v.get('message') for v in vios]}"
        )

    @pytest.mark.asyncio
    async def test_con01_zonder_contextmetadata_faalt(self, svc):
        vios = await _violations_voor(
            svc,
            "CON-01",
            "toezicht",
            "toezicht: systematisch volgen van handelingen aan de hand van normen",
            context={},
        )
        assert vios, (
            "CON-01 accepteert een definitie zonder enige gestructureerde "
            "context; minimaal één contextwaarde is verplicht"
        )

    @pytest.mark.asyncio
    async def test_con01_accepteert_contextspecifieke_tekst_zonder_label(self, svc):
        vios = await _violations_voor(
            svc,
            "CON-01",
            "toezicht",
            "toezicht: systematisch volgen van handelingen aan de hand van normen",
            context={"organisatorische_context": ["DJI"]},
        )
        assert not vios, (
            f"CON-01 keurt een correcte contextspecifieke definitie af: "
            f"{[v.get('message') for v in vios]}"
        )

    @pytest.mark.asyncio
    async def test_con01_verbiedt_contextwaarde_in_definitietekst(self, svc):
        vios = await _violations_voor(
            svc,
            "CON-01",
            "toezicht",
            "toezicht: controle uitgevoerd door DJI aan de hand van normen",
            context={"organisatorische_context": ["DJI"]},
        )
        assert vios, "CON-01 laat de geselecteerde contextwaarde in de tekst staan"


async def _status_voor(
    svc: ModularValidationService, rule_id: str, begrip: str, tekst: str
) -> str:
    res = await svc.validate_definition(
        begrip=begrip, text=tekst, ontologische_categorie=None, context={}
    )
    return str((res.get("rule_statuses") or {}).get(rule_id, ""))


class TestVoorbeeldparen:
    """De 44 gedocumenteerde goed/fout-paren als directe regressielaag.

    Het record bepaalt zélf hoe zijn paar meetelt (`example_pair_policy`).
    Afwijken van ``normative`` mag, maar alleen mét reden en tracker-ID — dat
    dwingt `build_rule_record` af. Er wordt nergens gexfaild of geskipt: elke
    policy krijgt hier een eigen, even harde assertie.
    """

    def test_er_zijn_44_voorbeeldparen(self):
        assert len(VOORBEELDPAREN) == 44, (
            f"verwacht 44 records met goed én fout voorbeeld, gevonden "
            f"{len(VOORBEELDPAREN)}: {VOORBEELDPAREN}"
        )

    @staticmethod
    def _policy(rule_id: str) -> str:
        return str(
            (RAW[rule_id].get("runtime_contract") or {}).get("example_pair_policy", "")
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("rule_id", VOORBEELDPAREN, ids=str)
    async def test_goed_voorbeeld_wordt_niet_afgekeurd(self, svc, rule_id):
        """Een correct voorbeeld mag onder geen enkele policy falen."""
        begrip, tekst = _begrip_en_tekst(RAW[rule_id]["goede_voorbeelden"][0])
        vios = await _violations_voor(svc, rule_id, begrip, tekst)
        assert not vios, (
            f"{rule_id}: het eigen GOEDE voorbeeld levert een violation: "
            f"{[v.get('message') for v in vios]}"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("rule_id", VOORBEELDPAREN, ids=str)
    async def test_fout_voorbeeld_volgens_beleid(self, svc, rule_id):
        policy = self._policy(rule_id)
        begrip, tekst = _begrip_en_tekst(RAW[rule_id]["foute_voorbeelden"][0])

        if policy == "normative":
            vios = await _violations_voor(svc, rule_id, begrip, tekst)
            assert vios, (
                f"{rule_id}: het eigen FOUTE voorbeeld passeert — de regel "
                f"herkent zijn gedocumenteerde tegenvoorbeeld niet"
            )
            return

        # Niet-normatieve policies: de regel mag het foute voorbeeld niet
        # zomaar goedkeuren. De uitkomst moet expliciet zichtbaar zijn.
        status = await _status_voor(svc, rule_id, begrip, tekst)
        verwacht = {
            "requires_repository": {"not_evaluated", "error"},
            "review_policy": {"review_required"},
            "source_defect": {"pass", "fail"},
        }[policy]
        assert status in verwacht, (
            f"{rule_id}: policy {policy!r} verwacht status in {sorted(verwacht)}, "
            f"gevonden {status!r}"
        )
        assert (
            status != "pass" or policy == "source_defect"
        ), f"{rule_id}: policy {policy!r} mag nooit als pass eindigen"


class _StubDefinitie:
    """Minimaal repository-record voor de graaf-/overlapevaluators."""

    def __init__(self, begrip: str, definitie: str, definitie_id: int) -> None:
        self.id = definitie_id
        self.begrip = begrip
        self.definitie = definitie
        self.categorie = ""
        self.status = "vastgesteld"
        self.organisatorische_context = []
        self.juridische_context = []
        self.wettelijke_basis = []
        self.voorkeursterm = None


class _StubRepository:
    def __init__(self, paren: list[tuple[str, str]]) -> None:
        self._defs = [
            _StubDefinitie(begrip, definitie, index + 1)
            for index, (begrip, definitie) in enumerate(paren)
        ]

    def _get_all_definitions(self) -> list[_StubDefinitie]:
        return list(self._defs)


def _svc_met_repository(paren: list[tuple[str, str]]) -> ModularValidationService:
    return ModularValidationService(
        get_toetsregel_manager(), None, None, _StubRepository(paren)
    )
