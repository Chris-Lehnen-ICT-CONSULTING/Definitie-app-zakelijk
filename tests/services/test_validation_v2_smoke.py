import asyncio

from services.container import get_container


def test_validation_v2_smoke():
    container = get_container({"enable_ontology": False})
    orchestrator = container.orchestrator()
    validation = getattr(orchestrator, "validation_service", None)
    assert validation is not None, "Validation orchestrator should be available"

    async def run():
        return await validation.validate_text(
            begrip="", text="test definitie", ontologische_categorie=None, context=None
        )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(run())
    finally:
        loop.close()

    assert isinstance(result, dict)
    assert "overall_score" in result
    assert "is_acceptable" in result
    assert "violations" in result
