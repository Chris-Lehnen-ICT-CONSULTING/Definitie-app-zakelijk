"""
Integration test for US-041: Context flow from UI to prompt service.

This test ensures that the context mapping from UI through service_factory
to prompt_service_v2 works correctly, particularly that list fields are
properly populated instead of using string fallback.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from services.service_factory import ServiceAdapter
from services.interfaces import GenerationRequest
from services.container import ServiceContainer


@pytest.mark.integration
def test_context_flows_from_ui_to_prompt_service():
    """
    CRITICAL TEST: Verifies US-041 context flow actually works.
    
    This test ensures that context from UI (via service_factory) properly
    populates the list fields in GenerationRequest and flows through to
    PromptServiceV2 without falling back to string-based context.
    """
    # Setup mock container with necessary services
    container = MagicMock(spec=ServiceContainer)
    
    # Mock orchestrator that captures the request
    captured_request = None
    async def capture_request(request):
        nonlocal captured_request
        captured_request = request
        # Return a mock response
        from services.interfaces import DefinitionResponseV2, Definition
        # Note: Using V2 response which the orchestrator returns
        response = DefinitionResponseV2()
        response.success = True
        response.definition = Definition(
            id="test-id",
            begrip="test",
            definitie="Test definitie",
            metadata={}
        )
        response.validation_result = {"overall_score": 0.9, "violations": []}
        response.metadata = {"voorbeelden": {}}
        return response
    
    mock_orchestrator = MagicMock()
    mock_orchestrator.create_definition = AsyncMock(side_effect=capture_request)
    mock_orchestrator.get_stats = MagicMock(return_value={})
    
    # Setup other required mocks
    container.orchestrator = MagicMock(return_value=mock_orchestrator)
    container.web_lookup = MagicMock(return_value=MagicMock())
    container.definition_ui_service = MagicMock(return_value=MagicMock())
    container.generator = MagicMock(return_value=MagicMock(get_stats=MagicMock(return_value={})))
    container.repository = MagicMock(return_value=MagicMock(get_stats=MagicMock(return_value={})))
    
    # Create adapter (this is what UI uses)
    adapter = ServiceAdapter(container)
    
    # Simulate UI calling generate_definition with context_dict
    context_dict = {
        "organisatorisch": ["DJI", "OM", "Rechtspraak"],
        "juridisch": ["Strafrecht", "Bestuursrecht"],
        "wettelijk": ["Wetboek van Strafrecht", "Wetboek van Strafvordering"],
        "domein": ["Detentie", "Sanctietoepassing"]
    }
    
    # Call the method that UI would call
    result = adapter.generate_definition(
        begrip="gevangenisstraf",
        context_dict=context_dict,
        organisatie="DJI",
        extra_instructies="Focus op Nederlandse context"
    )
    
    # Verify the request was captured
    assert captured_request is not None, "Request should have been captured"
    
    # CRITICAL ASSERTIONS: Verify list fields are populated, not string field
    assert captured_request.organisatorische_context == ["DJI", "OM", "Rechtspraak"], \
        f"organisatorische_context should be populated as list, got: {captured_request.organisatorische_context}"
    
    assert captured_request.juridische_context == ["Strafrecht", "Bestuursrecht"], \
        f"juridische_context should be populated as list, got: {captured_request.juridische_context}"
    
    assert captured_request.wettelijke_basis == ["Wetboek van Strafrecht", "Wetboek van Strafvordering"], \
        f"wettelijke_basis should be populated as list, got: {captured_request.wettelijke_basis}"
    
    # Verify old string field is NOT used for organisatorische context
    assert captured_request.context is None, \
        f"Context field should be None when using list fields, got: {captured_request.context}"
    
    # Verify domein is still handled correctly
    assert captured_request.domein == "Detentie, Sanctietoepassing", \
        f"Domein should be concatenated string, got: {captured_request.domein}"
    
    print("✅ Context flow test PASSED - List fields are properly populated!")


@pytest.mark.integration
def test_empty_context_lists_handled_correctly():
    """Test that empty context lists don't cause errors."""
    container = MagicMock(spec=ServiceContainer)
    
    captured_request = None
    async def capture_request(request):
        nonlocal captured_request
        captured_request = request
        from services.interfaces import DefinitionResponseV2, Definition
        # Note: Using V2 response which the orchestrator returns
        response = DefinitionResponseV2()
        response.success = True
        response.definition = Definition(
            id="test-id",
            begrip="test",
            definitie="Test definitie",
            metadata={}
        )
        response.validation_result = {"overall_score": 0.9, "violations": []}
        response.metadata = {"voorbeelden": {}}
        return response
    
    mock_orchestrator = MagicMock()
    mock_orchestrator.create_definition = AsyncMock(side_effect=capture_request)
    mock_orchestrator.get_stats = MagicMock(return_value={})
    
    container.orchestrator = MagicMock(return_value=mock_orchestrator)
    container.web_lookup = MagicMock(return_value=MagicMock())
    container.definition_ui_service = MagicMock(return_value=MagicMock())
    container.generator = MagicMock(return_value=MagicMock(get_stats=MagicMock(return_value={})))
    container.repository = MagicMock(return_value=MagicMock(get_stats=MagicMock(return_value={})))
    
    adapter = ServiceAdapter(container)
    
    # Call with empty context
    context_dict = {}
    
    result = adapter.generate_definition(
        begrip="test",
        context_dict=context_dict
    )
    
    # Verify empty lists are handled gracefully
    assert captured_request is not None
    assert captured_request.organisatorische_context == [], \
        "Empty context should result in empty list, not None"
    assert captured_request.juridische_context == [], \
        "Empty context should result in empty list, not None"
    assert captured_request.wettelijke_basis == [], \
        "Empty context should result in empty list, not None"


@pytest.mark.integration 
def test_backwards_compatibility_with_string_context():
    """Test that old string-based context still works for backward compatibility."""
    container = MagicMock(spec=ServiceContainer)
    
    captured_request = None
    async def capture_request(request):
        nonlocal captured_request
        captured_request = request
        from services.interfaces import DefinitionResponseV2, Definition
        # Note: Using V2 response which the orchestrator returns
        response = DefinitionResponseV2()
        response.success = True
        response.definition = Definition(
            id="test-id",
            begrip="test", 
            definitie="Test definitie",
            metadata={}
        )
        response.validation_result = {"overall_score": 0.9, "violations": []}
        response.metadata = {"voorbeelden": {}}
        return response
    
    mock_orchestrator = MagicMock()
    mock_orchestrator.create_definition = AsyncMock(side_effect=capture_request)
    mock_orchestrator.get_stats = MagicMock(return_value={})
    
    container.orchestrator = MagicMock(return_value=mock_orchestrator)
    container.web_lookup = MagicMock(return_value=MagicMock())
    container.definition_ui_service = MagicMock(return_value=MagicMock())
    container.generator = MagicMock(return_value=MagicMock(get_stats=MagicMock(return_value={})))
    container.repository = MagicMock(return_value=MagicMock(get_stats=MagicMock(return_value={})))
    
    adapter = ServiceAdapter(container)
    
    # Call with mixed context (some lists, some strings for backward compat)
    context_dict = {
        "organisatorisch": ["DJI"],  # List
        "context": "Some old string context",  # Old string field
    }
    
    result = adapter.generate_definition(
        begrip="test",
        context_dict=context_dict
    )
    
    assert captured_request is not None
    assert captured_request.organisatorische_context == ["DJI"], \
        "List context should be preserved"
    # The string context field should be None when using new list fields
    assert captured_request.context is None, \
        "Old context field should be None when using new list fields"


if __name__ == "__main__":
    # Run all tests synchronously
    test_context_flows_from_ui_to_prompt_service()
    test_empty_context_lists_handled_correctly()
    test_backwards_compatibility_with_string_context()
    
    print("\n✅ All integration tests passed!")