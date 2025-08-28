# V2 Orchestrator Async Bug Documentation

## Issue: Missing await for async clean_text method

### Location
File: `src/services/orchestrators/definition_orchestrator_v2.py`
Line: 231

### Current Code (BUG)
```python
# V2 cleaning service interface
cleaning_result = self.cleaning_service.clean_text(
    (
        generation_result.text
        if hasattr(generation_result, "text")
        else str(generation_result)
    ),
    sanitized_request.begrip,
)
```

### Required Fix
```python
# V2 cleaning service interface
cleaning_result = await self.cleaning_service.clean_text(
    (
        generation_result.text
        if hasattr(generation_result, "text")
        else str(generation_result)
    ),
    sanitized_request.begrip,
)
```

### Problem
The `clean_text` method in `CleaningServiceInterface` is defined as async, but the V2 orchestrator calls it without `await`. This will result in:
- Runtime warning: "coroutine was never awaited"
- The cleaning operation will not execute
- `cleaning_result` will be a coroutine object instead of a `CleaningResult`

### Impact
- The V2 flow will fail when it tries to access `cleaning_result.cleaned_text`
- AttributeError: 'coroutine' object has no attribute 'cleaned_text'

### Additional Notes
The legacy fallback path (line 243) correctly uses `await` for `clean_definition`, so this is likely an oversight during the V2 implementation.
