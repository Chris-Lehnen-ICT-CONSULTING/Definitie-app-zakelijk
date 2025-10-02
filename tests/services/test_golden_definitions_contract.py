import pytest
import yaml


def _load_cases():
    with open("tests/fixtures/golden_definitions.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["cases"]


@pytest.mark.contract()
@pytest.mark.asyncio()
async def test_golden_definitions_against_modular_service():
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService  # type: ignore[attr-defined]
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)  # type: ignore[arg-type]
    except TypeError:
        service = svc()  # type: ignore[call-arg]

    for case in _load_cases():
        res = await service.validate_definition(
            begrip=case["begrip"],
            text=case["text"],
            ontologische_categorie=None,
            context={"correlation_id": "00000000-0000-0000-0000-000000000000"},
        )

        assert isinstance(res, dict)
        exp = case["expected"]

        assert res["is_acceptable"] is exp["is_acceptable"]

        if "min_overall_score" in exp:
            assert res["overall_score"] >= exp["min_overall_score"] - 0.001
        if "max_overall_score" in exp:
            assert res["overall_score"] <= exp["max_overall_score"] + 0.001

        # violations: allow prefix matching for stability
        expected_codes = exp.get("violations", [])
        if expected_codes:
            actual_codes = [v.get("code", "") for v in res.get("violations", [])]

            # Accept either exact code or prefix match (e.g., "ESS-")
            def _prefix_present(prefix: str) -> bool:
                return any(c.startswith(prefix) for c in actual_codes)

            for code in expected_codes:
                assert _prefix_present(
                    code
                ), f"Expected violation code/prefix '{code}' not found in {actual_codes}"
