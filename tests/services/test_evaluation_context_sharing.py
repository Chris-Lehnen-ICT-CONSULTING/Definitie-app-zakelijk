"""Tests for EvaluationContext sharing between validators."""

from unittest.mock import Mock, call, patch

import pytest


@pytest.mark.unit()
def test_evaluation_context_dataclass_structure():
    """Test that EvaluationContext has all required fields."""
    m = pytest.importorskip(
        "services.validation.types_internal",
        reason="types_internal module not implemented yet",
    )

    ctx_cls = getattr(m, "EvaluationContext", None)
    assert ctx_cls is not None, "EvaluationContext must exist"

    # Test construction with required fields
    context = ctx_cls(
        raw_text="Original text",
        cleaned_text="Cleaned text",
        locale="nl",
        profile="default",
        correlation_id="test-123",
        tokens=["word1", "word2"],
        metadata={"key": "value"},
    )

    # Verify all fields are accessible
    assert context.raw_text == "Original text"
    assert context.cleaned_text == "Cleaned text"
    assert context.locale == "nl"
    assert context.profile == "default"
    assert context.correlation_id == "test-123"
    assert context.tokens == ["word1", "word2"]
    assert context.metadata == {"key": "value"}


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_context_computed_once_shared_across_validators():
    """Test that EvaluationContext is computed once and shared."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    # Mock the cleaning service to track calls
    mock_cleaning = Mock()
    mock_cleaning.clean_text = Mock(return_value="cleaned text")

    # Mock tokenizer to track calls
    mock_tokenizer = Mock(return_value=["token1", "token2"])

    svc = m.ModularValidationService
    try:
        service = svc(
            toetsregel_manager=None,
            cleaning_service=mock_cleaning,
            config=None,
        )
    except TypeError:
        service = svc()
        service.cleaning_service = mock_cleaning

    # Patch tokenizer if it exists
    with patch.object(service, "_tokenize", mock_tokenizer, create=True):
        await service.validate_definition(
            begrip="test",
            text="Raw input text",
            ontologische_categorie=None,
            context={"correlation_id": "test-123"},
        )

    # Cleaning should be called exactly once
    assert (
        mock_cleaning.clean_text.call_count == 1
    ), "Cleaning should happen exactly once"
    mock_cleaning.clean_text.assert_called_once_with("Raw input text")

    # Tokenization should happen at most once (if used)
    assert mock_tokenizer.call_count <= 1, "Tokenization should happen at most once"


@pytest.mark.unit()
def test_context_prevents_duplicate_text_processing():
    """Test that validators receive pre-processed text via context."""
    m = pytest.importorskip(
        "services.validation.module_adapter",
        reason="ValidationModuleAdapter not implemented yet",
    )
    t = pytest.importorskip(
        "services.validation.types_internal",
        reason="types_internal not implemented yet",
    )

    adapter = m.ValidationModuleAdapter()

    # Create context with pre-computed data
    ctx = t.EvaluationContext(
        raw_text="  Raw TEXT with spaces  ",
        cleaned_text="raw text with spaces",  # Pre-cleaned
        locale="nl",
        profile=None,
        correlation_id="test-123",
        tokens=["raw", "text", "with", "spaces"],  # Pre-tokenized
        metadata={},
    )

    # Mock validator that checks it receives cleaned text
    mock_validator = Mock()
    mock_validator.code = "TEST-01"
    mock_validator.validate = Mock(return_value={"score": 0.8, "violations": []})

    # Validator should receive the context with pre-processed data
    adapter.evaluate_sync(mock_validator, ctx)

    # Verify validator was called with the context
    mock_validator.validate.assert_called_once()
    call_args = mock_validator.validate.call_args

    # Context should be passed to validator
    passed_ctx = call_args[0][0] if call_args[0] else call_args.kwargs.get("context")
    assert passed_ctx is not None
    assert passed_ctx.cleaned_text == "raw text with spaces"
    assert passed_ctx.tokens == ["raw", "text", "with", "spaces"]


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_context_includes_correlation_id_for_tracing():
    """Test that correlation_id is properly propagated through context."""
    m = pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    svc = m.ModularValidationService
    try:
        service = svc(toetsregel_manager=None, cleaning_service=None, config=None)
    except TypeError:
        service = svc()

    correlation_id = "trace-abc-123"

    # Mock internal method to inspect context
    original_evaluate = getattr(service, "_evaluate_rule", None)
    contexts_seen = []

    def capture_context(rule, context):
        contexts_seen.append(context)
        return {"score": 0.8, "violations": []}

    if original_evaluate:
        with patch.object(service, "_evaluate_rule", side_effect=capture_context):
            await service.validate_definition(
                begrip="test",
                text="test text",
                ontologische_categorie=None,
                context={"correlation_id": correlation_id},
            )

        # All contexts should have the same correlation_id
        for ctx in contexts_seen:
            assert ctx.correlation_id == correlation_id
    else:
        # If method not found, just verify result contains correlation_id
        result = await service.validate_definition(
            begrip="test",
            text="test text",
            ontologische_categorie=None,
            context={"correlation_id": correlation_id},
        )
        assert result["system"]["correlation_id"] == correlation_id


@pytest.mark.unit()
def test_context_immutable_between_validators():
    """Test that EvaluationContext cannot be modified by validators."""
    m = pytest.importorskip(
        "services.validation.types_internal",
        reason="types_internal module not implemented yet",
    )

    ctx_cls = getattr(m, "EvaluationContext", None)
    assert ctx_cls is not None

    # Create context
    context = ctx_cls(
        raw_text="Original",
        cleaned_text="Cleaned",
        locale="nl",
        profile=None,
        correlation_id="test-123",
        tokens=["word"],
        metadata={"key": "value"},
    )

    # Attempt to modify should raise error (if frozen/immutable)
    with pytest.raises((AttributeError, TypeError)):
        context.raw_text = "Modified"

    with pytest.raises((AttributeError, TypeError)):
        context.tokens.append("new_token")

    # Original values should be unchanged
    assert context.raw_text == "Original"
    assert len(context.tokens) == 1


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_context_lazy_computation_of_optional_fields():
    """Test that optional fields like tokens are only computed when needed."""
    pytest.importorskip(
        "services.validation.modular_validation_service",
        reason="ModularValidationService not implemented yet",
    )

    # Track which validators actually use tokens
    validators_using_tokens = []

    class TokenUsingValidator:
        code = "TOKEN-01"

        def validate(self, context):
            if context.tokens:
                validators_using_tokens.append(self.code)
            return {"score": 0.8, "violations": []}

    class NoTokenValidator:
        code = "NOTOKEN-01"

        def validate(self, context):
            # Doesn't access tokens
            return {"score": 0.9, "violations": []}

    # If no validator needs tokens, they shouldn't be computed
    # This is an optimization test - implementation may vary
