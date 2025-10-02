import pytest
import yaml


def _load_cases():
    with open("tests/fixtures/golden_definitions.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["cases"]


@pytest.mark.integration()
@pytest.mark.asyncio()
async def test_golden_definitions_via_orchestrator():
    from services.container import ContainerConfigs, ServiceContainer

    container = ServiceContainer(ContainerConfigs.testing())
    orch = container.orchestrator()
    # Gebruik de door DI geleverde ValidationOrchestratorV2 rechtstreeks
    val_orch = orch.validation_service

    mismatches = []
    for case in _load_cases():
        res = await val_orch.validate_text(
            begrip=case["begrip"],
            text=case["text"],
            ontologische_categorie=None,
            context=None,
        )

        assert isinstance(res, dict)
        exp = case["expected"]

        if res["is_acceptable"] is not exp["is_acceptable"]:
            mismatches.append(
                (case.get("id"), res["overall_score"], res.get("violations", []))
            )
            continue

        # violations: allow prefix matching for stability
        expected_codes = exp.get("violations", [])
        if expected_codes:
            actual_codes = [v.get("code", "") for v in res.get("violations", [])]

            def _prefix_present(prefix: str) -> bool:
                return any(c.startswith(prefix) for c in actual_codes)

            for code in expected_codes:
                if not _prefix_present(code):
                    mismatches.append(
                        (case.get("id"), actual_codes, f"missing prefix {code}")
                    )
                    break

    assert not mismatches, f"Golden mismatches: {mismatches}"
