"""DEF-768: de ESS-05-beoordeling door de hele generatieketen (offline, echte validatie).

`DefinitionOrchestratorV2.create_definition` met gemockte AI/prompt/cleaning/
repository, maar met de echte `ValidationOrchestratorV2` →
`ModularValidationService` (echte regelset) en een deterministische fake
`Ess05AssessmentService`. Bewijst dat de gegenereerde kandidaat de
onderscheidsbeoordeling bereikt, dat die vóór opslag op de definitie staat,
dat een negatieve uitkomst (K-8) zichtbaar maar niet blokkerend is en geen
herstelroute activeert, en dat er nooit een cijfer ontstaat. Geen echt model,
geen productiedatabase.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.ess03.contract import Intentie
from domain.ess05.contract import bereken_ess05_vingerafdruk
from services.interfaces import (
    AIGenerationResult,
    CleaningResult,
    GenerationRequest,
    OrchestratorConfig,
    PromptResult,
)
from services.null_repository import NullDefinitionRepository
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.modular_validation_service import ModularValidationService
from tests.fixtures.def768_fakes import FakeEss05Assessor
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

BEGRIP = "lener"
DEFINITIE = "Persoon met een actuele lening bij de instelling."
ORG = ["Synthetische Uitleendienst"]


@pytest.fixture
def generate(monkeypatch):
    from voorbeelden import unified_voorbeelden

    monkeypatch.setattr(
        unified_voorbeelden,
        "genereer_alle_voorbeelden_async",
        AsyncMock(return_value={}),
    )

    async def run(*, scenario="pass", enhancement=None):
        assessor = FakeEss05Assessor(scenario=scenario)
        prompt = AsyncMock()
        prompt.build_generation_prompt.return_value = PromptResult(
            text="Offline",
            token_count=1,
            components_used=(),
            feedback_integrated=False,
            optimization_applied=False,
            metadata={},
        )
        ai = AsyncMock()
        ai.generate_definition.return_value = AIGenerationResult(
            text=DEFINITIE, model="offline", tokens_used=1, generation_time=0.0
        )
        cleaning = AsyncMock()
        cleaning.clean_text.return_value = CleaningResult(
            original_text=DEFINITIE, cleaned_text=DEFINITIE, was_cleaned=False
        )
        validation = ValidationOrchestratorV2(
            ModularValidationService(
                get_toetsregel_manager(), repository=NullDefinitionRepository()
            ),
            ess05_assessment_service=assessor,
        )
        repo = MagicMock()
        repo.save.return_value = 42
        orch = DefinitionOrchestratorV2(
            prompt_service=prompt,
            ai_service=ai,
            validation_service=validation,
            cleaning_service=cleaning,
            repository=repo,
            enhancement_service=enhancement,
            config=OrchestratorConfig(
                enable_feedback_loop=False, enable_enhancement=enhancement is not None
            ),
        )
        response = await orch.create_definition(
            GenerationRequest(
                id="ess05-offline",
                begrip=BEGRIP,
                ontologische_categorie="type",
                organisatorische_context=list(ORG),
            ),
            context={},
        )
        assert response.success, response.error
        return SimpleNamespace(
            response=response,
            assessor=assessor,
            definition=repo.save.call_args.args[0],
        )

    return run


async def test_generatie_bereikt_de_beoordeling_en_bewaart_haar(generate):
    result = await generate()
    (call,) = result.assessor.calls
    assert (call["begrip"], call["tekst"]) == (BEGRIP, DEFINITIE)
    beoordeling = result.definition.metadata["ess05_assessment"]
    assert beoordeling["status"] == "assessed"
    assert beoordeling["fingerprint"] == bereken_ess05_vingerafdruk(
        BEGRIP,
        DEFINITIE,
        {"organisatorische_context": ORG},
        [],
        intentie=Intentie(categorie="type"),
        buren=(),
    )
    raw = result.response.validation_result
    assert raw["ess05_assessment"] == beoordeling
    # Geen bevestigde buur: precies één vraag, nooit een stille pass (K-2).
    assert raw["rule_statuses"]["ESS-05"] == "review_required"
    assert "ESS-05" not in raw["passed_rules"]
    assert raw["rule_results"]["ESS-05"]["review"]["question"]
    assert raw["overall_score"] is None


async def test_k8_is_zichtbaar_niet_blokkerend_en_zonder_herstel(generate):
    enhancement = AsyncMock()
    enhancement.enhance_definition.return_value = "HERSCHREVEN"
    result = await generate(scenario="lacks", enhancement=enhancement)
    raw = result.response.validation_result
    assert raw["rule_statuses"]["ESS-05"] == "fail"
    [violation] = [v for v in raw["violations"] if v.get("code") == "ESS-05"]
    assert violation["severity"] == "warning"
    assert "zonder toespitsing" in violation["description"]
    # Andere overtredingen kunnen herstel vragen, ESS-05 zelf nooit (geen
    # automatische herschrijving op een onderscheidsoordeel).
    for call in enhancement.enhance_definition.await_args_list:
        assert all(v.get("code") != "ESS-05" for v in call.args[1])


async def test_technische_fout_reist_mee_als_error(generate):
    result = await generate(scenario="error")
    raw = result.response.validation_result
    assert raw["rule_statuses"]["ESS-05"] == "error"
    assert result.definition.metadata["ess05_assessment"]["status"] == "error"
