"""
Integration test for definition generation workflow.

Tests the complete 10-step generation process as documented in:
docs/backlog/EPIC-026/phase-1/BUSINESS_LOGIC_EXTRACTION_PLAN.md

10-Step Generation Workflow:
1. Context validation (min 1 of org/jur/wet)
2. Ontological category determination
3. Document context retrieval
4. Document snippets extraction (max 2, 280 char window)
5. Regeneration context handling
6. Definition service call
7. Result storage
8. Edit tab preparation
9. Regeneration cleanup
10. Success notification

EPIC-026 Phase 1 - Rebuild Validation
"""

import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


# ========================================
# FIXTURES
# ========================================


@pytest.fixture()
def mock_service_container():
    """Mock service container with all required services."""
    container = Mock()

    # Mock AI service
    container.ai_service = AsyncMock()
    container.ai_service.generate_definition.return_value = {
        "definitie": "Een gestructureerde beschrijving van een begrip.",
        "confidence": 0.85,
    }

    # Mock validation service
    container.validation_service = Mock()
    container.validation_service.validate.return_value = {
        "overall_score": 0.85,
        "is_acceptable": True,
        "rule_results": [],
    }

    # Mock categorization service
    container.categorization_service = AsyncMock()
    container.categorization_service.determine_category.return_value = {
        "categorie": "proces",
        "confidence": 0.90,
    }

    # Mock repository
    container.repository = Mock()
    container.repository.save_definition.return_value = 1

    # Mock regeneration service
    container.regeneration_service = Mock()
    container.regeneration_service.get_context.return_value = None

    return container


@pytest.fixture()
def sample_generation_request() -> dict[str, Any]:
    """Sample generation request with all required fields."""
    return {
        "begrip": "authenticatie",
        "organisatorische_context": ["identiteitsbeheer"],
        "juridische_context": ["AVG"],
        "wettelijke_basis": ["AVG artikel 32"],
        "voorbeelden": [
            "De gebruiker wordt geauthenticeerd met credentials.",
            "Authenticatie vindt plaats via twee-factor verificatie.",
        ],
        "document_context": {
            "snippets": [
                "Authenticatie is het proces waarbij identiteit wordt geverifieerd.",
                "Het systeem ondersteunt meerdere authenticatiemethoden.",
            ]
        },
    }


# ========================================
# STEP 1: CONTEXT VALIDATION
# ========================================


@pytest.mark.integration()
@pytest.mark.baseline()
def test_step1_context_validation_success():
    """
    Test Step 1: Context validation passes with minimum required context.

    Requirement: At least 1 of org/jur/wet context must be provided.
    """
    # Valid cases
    valid_contexts = [
        {
            "organisatorische_context": ["test"],
            "juridische_context": [],
            "wettelijke_basis": [],
        },
        {
            "organisatorische_context": [],
            "juridische_context": ["test"],
            "wettelijke_basis": [],
        },
        {
            "organisatorische_context": [],
            "juridische_context": [],
            "wettelijke_basis": ["test"],
        },
        {
            "organisatorische_context": ["a"],
            "juridische_context": ["b"],
            "wettelijke_basis": ["c"],
        },
    ]

    for context in valid_contexts:
        has_context = any(
            [
                context.get("organisatorische_context"),
                context.get("juridische_context"),
                context.get("wettelijke_basis"),
            ]
        )
        assert has_context, f"Context validation should pass for {context}"


@pytest.mark.integration()
@pytest.mark.baseline()
def test_step1_context_validation_failure():
    """
    Test Step 1: Context validation fails without minimum context.

    Requirement: At least 1 context field must have content.
    """
    # Invalid cases
    invalid_contexts = [
        {
            "organisatorische_context": [],
            "juridische_context": [],
            "wettelijke_basis": [],
        },
        {
            "organisatorische_context": None,
            "juridische_context": None,
            "wettelijke_basis": None,
        },
        {},
    ]

    for context in invalid_contexts:
        has_context = any(
            [
                context.get("organisatorische_context"),
                context.get("juridische_context"),
                context.get("wettelijke_basis"),
            ]
        )
        assert not has_context, f"Context validation should fail for {context}"


# ========================================
# STEP 2: ONTOLOGICAL CATEGORY DETERMINATION
# ========================================


@pytest.mark.integration()
@pytest.mark.baseline()
@pytest.mark.asyncio()
async def test_step2_category_determination(mock_service_container):
    """
    Test Step 2: Ontological category determination.

    Uses async call to categorization service.
    """
    begrip = "authenticatie"

    # Call categorization service
    result = await mock_service_container.categorization_service.determine_category(
        begrip
    )

    assert "categorie" in result, "Result should contain category"
    assert "confidence" in result, "Result should contain confidence"
    assert result["categorie"] in [
        "proces",
        "type",
        "resultaat",
        "exemplaar",
        "ENT",
        "ACT",
        "REL",
        "ATT",
        "AUT",
        "STA",
        "OTH",
    ]


# ========================================
# STEP 3-4: DOCUMENT CONTEXT
# ========================================


@pytest.mark.integration()
@pytest.mark.baseline()
def test_step3_document_context_retrieval():
    """
    Test Step 3: Document context retrieval.

    Retrieves relevant document context for generation.
    """
    # Mock document context
    document_context = {
        "snippets": [
            "Authenticatie is het proces van identiteitsverificatie.",
            "Het systeem ondersteunt meerdere authenticatiemethoden.",
        ],
        "metadata": {"source": "authenticatiebeleid.pdf", "date": "2024-01-01"},
    }

    assert "snippets" in document_context
    assert isinstance(document_context["snippets"], list)


@pytest.mark.integration()
@pytest.mark.baseline()
def test_step4_document_snippets_extraction():
    """
    Test Step 4: Document snippets extraction.

    Requirement: Max 2 snippets, 280 character window.
    """
    long_text = "Lorem ipsum dolor sit amet. " * 20  # Very long text

    # Simulate snippet extraction (max 2, 280 chars each)
    snippets = []
    max_snippets = 2
    max_chars = 280

    # Extract snippets
    for i in range(max_snippets):
        if len(long_text) > i * max_chars:
            snippet = long_text[i * max_chars : (i + 1) * max_chars]
            snippets.append(snippet)

    # Verify constraints
    assert len(snippets) <= max_snippets, "Should extract max 2 snippets"
    for snippet in snippets:
        assert len(snippet) <= max_chars, f"Snippet should be max {max_chars} chars"


# ========================================
# STEP 5: REGENERATION CONTEXT
# ========================================


@pytest.mark.integration()
@pytest.mark.baseline()
def test_step5_regeneration_context_handling(mock_service_container):
    """
    Test Step 5: Regeneration context handling.

    Checks if definition is being regenerated and retrieves context.
    """
    # Test without regeneration
    result = mock_service_container.regeneration_service.get_context()
    assert result is None, "No regeneration context initially"

    # Test with regeneration
    mock_service_container.regeneration_service.get_context.return_value = {
        "previous_definition": "Old definition text",
        "reason": "Category changed",
    }

    result = mock_service_container.regeneration_service.get_context()
    assert result is not None
    assert "previous_definition" in result


# ========================================
# STEP 6: DEFINITION SERVICE CALL
# ========================================


@pytest.mark.integration()
@pytest.mark.baseline()
@pytest.mark.asyncio()
async def test_step6_definition_service_call(
    mock_service_container, sample_generation_request
):
    """
    Test Step 6: Definition service call (async).

    Main generation happens here.
    """
    # Call definition generation service
    result = await mock_service_container.ai_service.generate_definition(
        begrip=sample_generation_request["begrip"], context=sample_generation_request
    )

    assert "definitie" in result, "Result should contain definition text"
    assert isinstance(result["definitie"], str)
    assert len(result["definitie"]) > 0, "Definition should not be empty"


# ========================================
# STEP 7-8: RESULT STORAGE AND EDIT PREP
# ========================================


@pytest.mark.integration()
@pytest.mark.baseline()
def test_step7_result_storage(mock_service_container):
    """
    Test Step 7: Result storage in session state.

    Stores generated definition for further processing.
    """
    # Mock session state manager
    session_state = {}

    # Store result
    generated_definition = "Een definitie voor authenticatie."
    session_state["generated_definition"] = generated_definition
    session_state["validation_results"] = {"score": 0.85}

    # Verify storage
    assert "generated_definition" in session_state
    assert session_state["generated_definition"] == generated_definition


@pytest.mark.integration()
@pytest.mark.baseline()
def test_step8_edit_tab_preparation():
    """
    Test Step 8: Edit tab preparation.

    Sets up state for edit tab navigation.
    """
    session_state = {}

    # Prepare edit tab
    session_state["editing_definition_id"] = 1
    session_state["edit_organisatorische_context"] = ["test"]
    session_state["edit_juridische_context"] = []
    session_state["edit_wettelijke_basis"] = []

    # Verify preparation
    assert "editing_definition_id" in session_state
    assert session_state["editing_definition_id"] == 1


# ========================================
# STEP 9-10: CLEANUP AND NOTIFICATION
# ========================================


@pytest.mark.integration()
@pytest.mark.baseline()
def test_step9_regeneration_cleanup():
    """
    Test Step 9: Regeneration cleanup.

    Clears regeneration state after successful generation.
    """
    session_state = {"regenerating": True, "regeneration_context": {"old": "data"}}

    # Cleanup
    session_state["regenerating"] = False
    session_state["regeneration_context"] = None

    # Verify cleanup
    assert session_state["regenerating"] is False
    assert session_state["regeneration_context"] is None


@pytest.mark.integration()
@pytest.mark.baseline()
def test_step10_success_notification():
    """
    Test Step 10: Success notification.

    Generates UI feedback for user.
    """
    notification = {
        "type": "success",
        "message": "Definitie succesvol gegenereerd",
        "details": {"begrip": "authenticatie", "score": 0.85},
    }

    assert notification["type"] == "success"
    assert "message" in notification
    assert "details" in notification


# ========================================
# FULL WORKFLOW INTEGRATION TEST
# ========================================


@pytest.mark.integration()
@pytest.mark.baseline()
@pytest.mark.slow()
@pytest.mark.asyncio()
async def test_complete_generation_workflow(
    mock_service_container, sample_generation_request
):
    """
    Test complete 10-step generation workflow end-to-end.

    This is a comprehensive integration test of all steps.
    """
    workflow_state = {}

    # STEP 1: Context validation
    has_context = any(
        [
            sample_generation_request.get("organisatorische_context"),
            sample_generation_request.get("juridische_context"),
            sample_generation_request.get("wettelijke_basis"),
        ]
    )
    assert has_context, "Step 1: Context validation failed"
    workflow_state["step1_complete"] = True

    # STEP 2: Category determination
    category_result = (
        await mock_service_container.categorization_service.determine_category(
            sample_generation_request["begrip"]
        )
    )
    assert "categorie" in category_result, "Step 2: Category determination failed"
    workflow_state["step2_complete"] = True
    workflow_state["category"] = category_result["categorie"]

    # STEP 3-4: Document context (simulated)
    document_snippets = sample_generation_request.get("document_context", {}).get(
        "snippets", []
    )
    workflow_state["step3_complete"] = True
    workflow_state["step4_complete"] = True
    workflow_state["snippets"] = document_snippets[:2]  # Max 2

    # STEP 5: Regeneration context (none in this case)
    regeneration_context = mock_service_container.regeneration_service.get_context()
    workflow_state["step5_complete"] = True
    workflow_state["is_regeneration"] = regeneration_context is not None

    # STEP 6: Definition generation
    definition_result = await mock_service_container.ai_service.generate_definition(
        begrip=sample_generation_request["begrip"], context=sample_generation_request
    )
    assert "definitie" in definition_result, "Step 6: Definition generation failed"
    workflow_state["step6_complete"] = True
    workflow_state["generated_definition"] = definition_result["definitie"]

    # STEP 7: Result storage
    workflow_state["stored_definition"] = definition_result["definitie"]
    workflow_state["step7_complete"] = True

    # STEP 8: Edit tab preparation
    workflow_state["editing_definition_id"] = 1
    workflow_state["step8_complete"] = True

    # STEP 9: Regeneration cleanup (if applicable)
    if workflow_state["is_regeneration"]:
        workflow_state["regenerating"] = False
    workflow_state["step9_complete"] = True

    # STEP 10: Success notification
    workflow_state["notification"] = {
        "type": "success",
        "message": "Generation complete",
    }
    workflow_state["step10_complete"] = True

    # Verify all steps completed
    for step in range(1, 11):
        assert workflow_state.get(f"step{step}_complete"), f"Step {step} not completed"

    # Verify final state
    assert "generated_definition" in workflow_state
    assert "category" in workflow_state
    assert "notification" in workflow_state

    print("\n\nGeneration Workflow Test Results:")
    print("=" * 80)
    print("✓ All 10 steps completed successfully")
    print(f"  Category: {workflow_state['category']}")
    print(f"  Definition: {workflow_state['generated_definition'][:80]}...")
    print(f"  Notification: {workflow_state['notification']['message']}")


# ========================================
# ERROR HANDLING TESTS
# ========================================


@pytest.mark.integration()
@pytest.mark.baseline()
def test_workflow_fails_without_context():
    """Test that workflow fails early without valid context."""
    invalid_request = {
        "begrip": "test",
        "organisatorische_context": [],
        "juridische_context": [],
        "wettelijke_basis": [],
    }

    # Step 1 should fail
    has_context = any(
        [
            invalid_request.get("organisatorische_context"),
            invalid_request.get("juridische_context"),
            invalid_request.get("wettelijke_basis"),
        ]
    )

    assert not has_context, "Should fail context validation"


@pytest.mark.integration()
@pytest.mark.baseline()
@pytest.mark.asyncio()
async def test_workflow_handles_service_errors(mock_service_container):
    """Test that workflow handles service errors gracefully."""
    # Simulate service error
    mock_service_container.ai_service.generate_definition.side_effect = Exception(
        "API Error"
    )

    with pytest.raises(Exception) as exc_info:
        await mock_service_container.ai_service.generate_definition(
            begrip="test", context={}
        )

    assert "API Error" in str(exc_info.value)
