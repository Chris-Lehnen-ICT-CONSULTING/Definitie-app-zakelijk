"""DEF-622 vervolgcriteria — de definitiegeneratiegrens (echte orchestrator).

Bewijs op `DefinitionOrchestratorV2.create_definition` met echte services
(cleaning, validatie met de echte regelset, repository op een synthetische
DB) en één bevroren providergrens met per casus vaste modeluitvoer:

* **Context vóór generatie** (CON-GT-001 / CW-GEN-05): zonder inhoudelijke
  waarde in de drie contextlijsten start geen modelaanroep; de aanroeper
  krijgt een duidelijke vraag om context. Niet alleen "Genereer Nieuw": de
  grens geldt voor elke ingang die op `create_definition` uitkomt.
* **Nul herstelcalls** (CON-GT-012 / CW-GEN-10): ook met een expliciet
  ingeschakelde enhancement-configuratie en een aanwezige enhancement-service
  leidt een CON-01-uitkomst (fail / open / technische fout) of een gesloten
  gate door ontbrekende totaalscore niet tot een automatische hersteloproep.
  Andere regelverantwoordelijkheden blijven: alleen overtredingen van andere
  regels kunnen de bestaande enhancement nog triggeren.
* **Getoetst = getoond = opgeslagen** (CON-GT-013/014-grens): de validatie
  muteert de kandidaat niet zonder hertoetsing; de opgeslagen tekst is exact
  de getoetste tekst.

De tekstvergelijking na generatie (kern vóór nabewerking, wijzigingsvlag,
UI-melding) staat in `test_def622_tekstwijziging_bewijs.py`.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from services.cleaning_service import CleaningConfig, CleaningService
from services.definition_repository import DefinitionRepository
from services.interfaces import GenerationRequest, OrchestratorConfig, PromptResult
from services.null_repository import NullDefinitionRepository
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

ZILVER = "Kwaliteitskeurmerk dat uitsluitend door Stichting Zilver wordt verleend"
KOPER = "controle die binnen Team Koper wordt uitgevoerd op dossiers"
NEUTRAAL = "Controle waarbij wordt vastgesteld of alle vereiste velden zijn ingevuld"


class BevrorenProvider:
    """De enige bevroren grens: vaste modeluitvoer per proef, met oproepteller."""

    def __init__(self, tekst: str) -> None:
        self.tekst = tekst
        self.oproepen: list[str] = []

    async def generate_definition(self, prompt: str, **kwargs: Any) -> Any:
        self.oproepen.append(prompt)
        return SimpleNamespace(
            text=self.tekst, model="bevroren", tokens_used=7, metadata={}
        )


class VastePrompt:
    async def build_generation_prompt(self, request, **kwargs: Any) -> PromptResult:
        return PromptResult(
            text=f"Definieer {request.begrip}",
            token_count=3,
            components_used=("bevroren",),
            feedback_integrated=False,
            optimization_applied=False,
            metadata={},
        )


def _alleen_con01(service: ModularValidationService) -> ModularValidationService:
    """Bewijsgrens: de echte CON-01-evaluator, met de overige regels expliciet
    buiten de set (dus 'positief'). Zo is een herstelcall alleen aan CON-01 of
    aan de gesloten gate (totaalscore niet beschikbaar) toe te schrijven.
    Geen productgedrag: uitsluitend isolatie van de proef."""
    from dataclasses import replace
    from types import MappingProxyType

    from services.validation.readiness import bepaal_readiness

    echt = service._ververs_state_indien_nodig()
    behouden = ("CON-01",)
    service._snapshot = replace(
        echt,
        readiness=bepaal_readiness(behouden, behouden),
        contract_rule_ids=behouden,
        internal_rules=behouden,
        rule_records=MappingProxyType({c: echt.rule_records[c] for c in behouden}),
        json_rules=MappingProxyType({c: echt.json_rules[c] for c in behouden}),
        default_weights=MappingProxyType(
            {c: g for c, g in echt.default_weights.items() if c in behouden}
        ),
        pattern_cache={},
        rules_loaded_count=len(behouden),
        rules_expected_count=len(behouden),
    )
    return service


def _orchestrator(
    tmp_path,
    tekst: str,
    *,
    enhancement: Any = None,
    alleen_con01: bool = False,
    validatie_cleaning: Any = None,
) -> tuple[DefinitionOrchestratorV2, BevrorenProvider, DefinitionRepository]:
    provider = BevrorenProvider(tekst)
    cleaning = CleaningService(CleaningConfig())
    service = ModularValidationService(
        toetsregel_manager=get_toetsregel_manager(),
        repository=NullDefinitionRepository(),
    )
    if alleen_con01:
        service = _alleen_con01(service)
    validatie = ValidationOrchestratorV2(
        service, cleaning_service=validatie_cleaning or cleaning
    )
    repo = DefinitionRepository(str(tmp_path / "generatie.db"))
    orch = DefinitionOrchestratorV2(
        prompt_service=VastePrompt(),
        ai_service=provider,
        validation_service=validatie,
        cleaning_service=cleaning,
        repository=repo,
        enhancement_service=enhancement,
        config=OrchestratorConfig(
            enable_feedback_loop=False,
            enable_enhancement=enhancement is not None,
        ),
    )
    return orch, provider, repo


def _request(begrip: str = "keurmerk", **context: Any) -> GenerationRequest:
    return GenerationRequest(
        id=str(uuid.uuid4()),
        begrip=begrip,
        ontologische_categorie="type",
        organisatorische_context=context.get("org"),
        juridische_context=context.get("jur"),
        wettelijke_basis=context.get("wet"),
    )


@pytest.fixture(autouse=True)
def _geen_voorbeelden(monkeypatch):
    """De voorbeeldengenerator is een eigen providergrens en valt buiten deze proef."""
    from voorbeelden import unified_voorbeelden

    async def _leeg(*_a: Any, **_k: Any) -> dict[str, Any]:
        return {}

    monkeypatch.setattr(unified_voorbeelden, "genereer_alle_voorbeelden_async", _leeg)


# ------------------------------------------------------- context vóór generatie


@pytest.mark.parametrize(
    "context",
    [
        {},
        {"org": [], "jur": [], "wet": []},
        {"org": [" ", ""], "jur": [None], "wet": ["   "]},
    ],
    ids=["ontbreekt", "leeg", "alleen-witruimte"],
)
async def test_zonder_context_geen_modelaanroep(tmp_path, context):
    """CON-GT-001 / CW-GEN-05: context is generatie-invoer; ontbreekt zij,
    dan vraagt de app om context en roept zij het model niet aan."""
    orch, provider, repo = _orchestrator(tmp_path, ZILVER)
    # schema.sql zaait zelf voorbeeldrijen: vergelijk vóór/na, verwijder niets.
    ids_voor = sorted(r.id for r in repo.legacy_repo.get_all())

    antwoord = await orch.create_definition(_request(**context))

    assert antwoord.success is False
    # Onafhankelijk tekstbewijs: een begrijpelijke vraag om context, geen
    # technische foutmelding.
    melding = (antwoord.error or "").lower()
    assert "minimaal één contextwaarde" in melding
    assert "organisatorisch" in melding and "wettelijke basis" in melding
    assert "generation failed" not in melding
    assert antwoord.metadata.get("error_type") == "context_required"
    assert provider.oproepen == []
    assert sorted(r.id for r in repo.legacy_repo.get_all()) == ids_voor


async def test_met_een_inhoudelijke_contextwaarde_loopt_de_generatie(tmp_path):
    """Eén inhoudelijke waarde in één van de drie lijsten volstaat (B-01)."""
    orch, provider, repo = _orchestrator(tmp_path, NEUTRAAL)

    antwoord = await orch.create_definition(_request(wet=["Regeling Z"]))

    assert antwoord.success is True, antwoord.error
    assert len(provider.oproepen) == 1
    assert antwoord.definition is not None and antwoord.definition.id


# ------------------------------------------------------------ nul herstelcalls


@pytest.mark.parametrize(
    ("begrip", "tekst", "context", "verwachte_con01"),
    [
        ("keurmerk", KOPER, {"org": ["Team Koper"]}, "review_required"),
        # Het echte casusbegrip (CON-GT-004): 'Zilverkeurmerk' staat niet
        # letterlijk in de uitvoer, zodat de generieke circulariteits-
        # heuristiek (geen CON-01) deze proef niet vertroebelt.
        ("Zilverkeurmerk", ZILVER, {"org": ["Stichting Zilver"]}, "review_required"),
        ("keurmerk", NEUTRAAL, {"org": ["Team Koper"]}, "pass"),
    ],
    ids=["open-naam-koper", "open-naam-zilver", "voldoet-zonder-naam"],
)
async def test_geen_herstelcall_bij_con01_uitkomst_ook_met_enhancement_aan(
    tmp_path, begrip, tekst, context, verwachte_con01
):
    """CON-GT-012 / CW-GEN-10: enhancement expliciet aan én service aanwezig;
    een CON-01-uitkomst of een gesloten gate door de ontbrekende totaalscore
    is geen herstelgrond. Nul hersteloproepen; de kandidaat blijft concept.

    Bewijsgrens: de echte CON-01-evaluator met de overige regels expliciet
    buiten de set (`_alleen_con01`) en een proefgrond zonder generieke
    baseline-bevindingen (circulariteit/inhoud), zodat geen echte overtreding
    van een andere regel de — bewust behouden — andere-regelroute kan
    activeren. Die route wordt apart bewezen in
    `test_andere_regelovertredingen_blijven_de_enhancement_triggeren`."""
    enhancement = SimpleNamespace(enhance_definition=AsyncMock(return_value="x"))
    orch, provider, repo = _orchestrator(
        tmp_path, tekst, enhancement=enhancement, alleen_con01=True
    )

    antwoord = await orch.create_definition(_request(begrip=begrip, **context))

    assert antwoord.success is True, antwoord.error
    assert len(provider.oproepen) == 1
    enhancement.enhance_definition.assert_not_called()
    assert antwoord.metadata["enhanced"] is False
    validatie = antwoord.validation_result
    assert validatie["overall_score"] is None
    assert validatie["is_acceptable"] is False
    assert validatie["rule_statuses"]["CON-01"] == verwachte_con01
    assert not any(v.get("code") != "CON-01" for v in validatie["violations"])
    rij = repo.legacy_repo.get_definitie(antwoord.definition.id)
    assert rij is not None and rij.status == "draft"


async def test_geen_herstelcall_bij_technische_con01_fout(tmp_path):
    """CON-GT-012: een technische fout in de CON-01-controle is geen
    overtreding en geen herstelgrond; zij blijft zichtbaar als 'error'.
    Zelfde bewijsgrens: alleen de (echte, hier falende) CON-01-evaluator."""
    enhancement = SimpleNamespace(enhance_definition=AsyncMock(return_value="x"))
    orch, provider, repo = _orchestrator(
        tmp_path, NEUTRAAL, enhancement=enhancement, alleen_con01=True
    )

    with patch(
        "services.validation.evaluators.context_metadata."
        "ContextMetadataEvaluator.evaluate",
        side_effect=RuntimeError("synthetische storing"),
    ):
        antwoord = await orch.create_definition(_request(org=["Team Koper"]))

    assert antwoord.success is True, antwoord.error
    enhancement.enhance_definition.assert_not_called()
    assert antwoord.validation_result["rule_statuses"]["CON-01"] == "error"
    assert antwoord.definition is not None and antwoord.definition.id


async def test_con01_uitkomst_bereikt_de_enhancement_niet_naast_andere_regels(
    tmp_path,
):
    """Volle regelset: echte andere overtredingen activeren de behouden
    route, maar de open CON-01-uitkomst gaat niet mee als herstelgrond en
    de hertoetste kandidaat behoudt de noodzakelijke naam."""
    enhancement = SimpleNamespace(enhance_definition=AsyncMock(return_value=ZILVER))
    orch, provider, repo = _orchestrator(
        tmp_path,
        "Dit is een ding dat Stichting Zilver moet verlenen",
        enhancement=enhancement,
    )

    antwoord = await orch.create_definition(_request(org=["Stichting Zilver"]))

    assert antwoord.success is True, antwoord.error
    enhancement.enhance_definition.assert_called_once()
    doorgegeven = enhancement.enhance_definition.call_args.args[1]
    assert doorgegeven and not any(v.get("code") == "CON-01" for v in doorgegeven)
    assert antwoord.validation_result["rule_statuses"]["CON-01"] == "review_required"
    assert "Stichting Zilver" in antwoord.definition.definitie


async def test_andere_regelovertredingen_blijven_de_enhancement_triggeren(tmp_path):
    """Behoud van andere regelverantwoordelijkheden: overtredingen van andere
    regels kunnen de bestaande enhancement nog triggeren, met hertoetsing van
    de daadwerkelijk bewaarde kandidaat; CON-01-uitkomsten gaan er niet in."""
    enhancement = SimpleNamespace(enhance_definition=AsyncMock(return_value=NEUTRAAL))
    # 'is', 'een' en 'moet' leveren echte overtredingen van andere regels.
    orch, provider, repo = _orchestrator(
        tmp_path, "Dit is een ding dat moet controleren", enhancement=enhancement
    )

    antwoord = await orch.create_definition(_request(org=["Team Koper"]))

    assert antwoord.success is True, antwoord.error
    enhancement.enhance_definition.assert_called_once()
    doorgegeven = enhancement.enhance_definition.call_args.args[1]
    assert doorgegeven, "andere overtredingen horen de enhancement te bereiken"
    assert not any(v.get("code") == "CON-01" for v in doorgegeven)
    assert antwoord.metadata["enhanced"] is True
    # Hertoetsing: het opgeslagen resultaat is de getoetste, verbeterde tekst.
    rij = repo.legacy_repo.get_definitie(antwoord.definition.id)
    assert rij.definitie == antwoord.definition.definitie


# ---------------------------------------------- getoetst = getoond = opgeslagen


class NietIdempotenteCleaning:
    """Adversariële nabewerking voor de validatie: de eerste `mutaties`
    aanroepen voegen een markering toe en schrijven die in het
    Definition-object terug. Zo is de hertoetsingsbranch bewijsbaar; de gewone
    opschoning is idempotent en zou hem nooit raken."""

    def __init__(self, mutaties: int) -> None:
        self.mutaties = mutaties
        self.oproepen = 0

    async def clean_definition(self, definition):
        from services.interfaces import CleaningResult

        self.oproepen += 1
        origineel = definition.definitie
        if self.oproepen <= self.mutaties:
            definition.definitie = f"{origineel} [v{self.oproepen}]"
        return CleaningResult(
            original_text=origineel,
            cleaned_text=definition.definitie,
            was_cleaned=definition.definitie != origineel,
            applied_rules=("adversarieel",),
        )

    async def clean_text(self, text, term):
        from services.interfaces import CleaningResult

        return CleaningResult(
            original_text=text, cleaned_text=text, was_cleaned=False, applied_rules=()
        )


async def test_een_mutatie_wordt_hertoetst_en_exact_opgeslagen(tmp_path):
    """Wijzigt de validatie de tekst één keer (in-place cleaning), dan wordt
    de gewijzigde tekst de kandidaat en opnieuw getoetst; de tweede toetsing
    is stabiel en de opgeslagen tekst is exact de getoetste tekst
    (CON-01-vingerafdruk op precies die tekst)."""
    from domain.context.contract import bereken_vingerafdruk

    adversarieel = NietIdempotenteCleaning(mutaties=1)
    orch, provider, repo = _orchestrator(
        tmp_path, "Kwaliteitsmerk voor producten.", validatie_cleaning=adversarieel
    )

    antwoord = await orch.create_definition(_request(org=["Team Koper"]))

    assert antwoord.success is True, antwoord.error
    # Twee toetsingen: de eerste wijzigde de tekst, de tweede toetste de
    # gewijzigde kandidaat stabiel (de branch is daadwerkelijk doorlopen).
    assert adversarieel.oproepen == 2
    opgeslagen = repo.legacy_repo.get_definitie(antwoord.definition.id).definitie
    assert opgeslagen == antwoord.definition.definitie
    assert opgeslagen == "Kwaliteitsmerk voor producten. [v1]"
    con01 = antwoord.validation_result["rule_results"]["CON-01"]
    assert con01["fingerprint"] == bereken_vingerafdruk(
        "keurmerk", opgeslagen, {"organisatorische_context": ["Team Koper"]}
    )


async def test_blijvende_mutatie_koppelt_geen_oordeel_aan_een_andere_tekst(
    tmp_path,
):
    """Blijft de validatie de tekst wijzigen, dan hoort elk oordeel bij een
    andere tekst dan de kandidaat: fail-closed — geen resultaat, geen opslag,
    en een duidelijke reden; het model is één keer aangeroepen."""
    adversarieel = NietIdempotenteCleaning(mutaties=99)
    orch, provider, repo = _orchestrator(
        tmp_path, "Kwaliteitsmerk voor producten.", validatie_cleaning=adversarieel
    )
    ids_voor = sorted(r.id for r in repo.legacy_repo.get_all())

    antwoord = await orch.create_definition(_request(org=["Team Koper"]))

    assert antwoord.success is False
    assert antwoord.definition is None
    assert "niet stabiel" in (antwoord.error or "")
    assert antwoord.metadata.get("error_type") == "KandidaatNietStabielError"
    assert len(provider.oproepen) == 1
    assert adversarieel.oproepen == 2
    assert sorted(r.id for r in repo.legacy_repo.get_all()) == ids_voor


async def test_idempotente_opschoning_toetst_een_keer_en_slaat_dezelfde_tekst_op(
    tmp_path,
):
    """Standaardpad: de echte opschoning is idempotent, dus één toetsing en
    dezelfde tekst getoetst, getoond en opgeslagen."""
    from domain.context.contract import bereken_vingerafdruk

    orch, provider, repo = _orchestrator(tmp_path, "kwaliteitsmerk voor producten")
    toetsingen: list[str] = []
    echte = orch.validation_service.validate_definition

    async def _spion(definition, context=None):
        toetsingen.append(definition.definitie)
        return await echte(definition, context)

    orch.validation_service.validate_definition = _spion  # type: ignore[method-assign]

    antwoord = await orch.create_definition(_request(org=["Team Koper"]))

    assert antwoord.success is True, antwoord.error
    assert toetsingen == ["Kwaliteitsmerk voor producten."]
    opgeslagen = repo.legacy_repo.get_definitie(antwoord.definition.id).definitie
    assert opgeslagen == antwoord.definition.definitie == toetsingen[0]
    con01 = antwoord.validation_result["rule_results"]["CON-01"]
    assert con01["fingerprint"] == bereken_vingerafdruk(
        "keurmerk", opgeslagen, {"organisatorische_context": ["Team Koper"]}
    )
