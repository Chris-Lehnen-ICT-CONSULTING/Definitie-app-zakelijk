import pytest


@pytest.mark.integration()
@pytest.mark.asyncio()
async def test_orchestrator_validate_text_minimal_shape():
    """
    Integration: orchestrator.validate_text returns a schema-like result.

    This test asserts the current wiring works end-to-end regardless of the
    underlying validation path (V1 adapter today; Modular V2 after cutover).
    """
    from services.container import ContainerConfigs, ServiceContainer
    from services.validation.interfaces import CONTRACT_VERSION

    container = ServiceContainer(ContainerConfigs.testing())
    orch = container.orchestrator()

    res = await orch.validate_text(
        begrip="belastingplichtige",
        text="Een natuurlijk persoon of rechtspersoon die belasting verschuldigd is.",
        ontologische_categorie=None,
        context=None,
    )

    assert isinstance(res, dict)
    for key in (
        "version",
        "overall_score",
        "is_acceptable",
        "violations",
        "passed_rules",
        "detailed_scores",
        "system",
    ):
        assert key in res, f"Missing required key: {key}"

    assert res["version"] == CONTRACT_VERSION
    assert "correlation_id" in res["system"]
