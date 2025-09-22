import pytest
import yaml


def _load_cases():
    with open("tests/fixtures/golden_definitions.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["cases"]


@pytest.mark.integration
@pytest.mark.xfail(reason="Golden acceptability mapping via DI service not aligned yet")
@pytest.mark.asyncio
async def test_golden_definitions_via_orchestrator():
    from services.container import ServiceContainer, ContainerConfigs

    container = ServiceContainer(ContainerConfigs.testing())
    orch = container.orchestrator()

    # Bouw een ValidationOrchestratorV2 bovenop de DI-geïnjecteerde validation_service
    from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
    val_orch = ValidationOrchestratorV2(validation_service=getattr(orch, "validation_service"))

    for case in _load_cases():
        res = await val_orch.validate_text(
            begrip=case["begrip"],
            text=case["text"],
            ontologische_categorie=None,
            context=None,
        )

        assert isinstance(res, dict)
        exp = case["expected"]

        assert res["is_acceptable"] is exp["is_acceptable"]

        # Minimale runner: focus op acceptability + violation-prefixen; score-bands worden elders getest

        # violations: allow prefix matching for stability
        expected_codes = exp.get("violations", [])
        if expected_codes:
            actual_codes = [v.get("code", "") for v in res.get("violations", [])]

            def _prefix_present(prefix: str) -> bool:
                return any(c.startswith(prefix) for c in actual_codes)

            for code in expected_codes:
                assert _prefix_present(code), f"Expected prefix '{code}' not in {actual_codes}"
