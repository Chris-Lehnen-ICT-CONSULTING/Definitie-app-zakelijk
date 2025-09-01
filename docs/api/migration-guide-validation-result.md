# Migration Guide: ValidationResult Changes

## Overview
As part of Story 2.3, the `ModularValidationService` now returns plain dictionaries instead of `ValidationResult` objects. This guide helps you migrate existing code to work with the new format.

## Key Changes

### 1. ValidationResult is now a Dict

**Before (Object):**
```python
result = await validator.validate(definition)
if result.is_valid:
    print(f"Score: {result.score}")
    for error in result.errors:
        print(error)
```

**After (Dict):**
```python
result = await validator.validate_definition(begrip, text)
if result["is_acceptable"]:
    print(f"Score: {result['overall_score']}")
    for violation in result["violations"]:
        print(violation["message"])
```

### 2. Property Mappings

| Old Property | New Dict Key | Notes |
|--------------|--------------|-------|
| `result.is_valid` | `result["is_acceptable"]` | Boolean validation status |
| `result.score` | `result["overall_score"]` | Float 0.0-1.0 |
| `result.errors` | `result["violations"]` | List of violation dicts |
| `result.warnings` | `result["violations"]` | Filtered by severity |
| `result.metadata` | `result["system"]` | System metadata |

### 3. Violation Structure Changes

**Before:**
```python
error = ValidationError(
    message="Definition too short",
    severity="error",
    code="LENGTH_ERROR"
)
```

**After:**
```python
violation = {
    "code": "VAL-LEN-001",
    "severity": "error",
    "message": "Definition is shorter than minimum length",
    "rule_id": "VAL-LEN-001",
    "category": "juridisch"
}
```

## Migration Strategies

### Strategy 1: Direct Dict Access (Recommended)

Update your code to use dictionary access:

```python
# Before
if validation_result.is_valid:
    score = validation_result.score
    
# After
if validation_result.get("is_acceptable", False):
    score = validation_result.get("overall_score", 0.0)
```

### Strategy 2: Wrapper Class (For Gradual Migration)

Create a wrapper to maintain object-style access:

```python
class ValidationResultAdapter:
    def __init__(self, result_dict):
        self._data = result_dict
    
    @property
    def is_valid(self):
        return self._data.get("is_acceptable", False)
    
    @property
    def score(self):
        return self._data.get("overall_score", 0.0)
    
    @property
    def errors(self):
        return self._data.get("violations", [])
    
    def __getitem__(self, key):
        return self._data[key]

# Usage
result_dict = await validator.validate_definition(begrip, text)
result = ValidationResultAdapter(result_dict)

# Now you can use both styles
if result.is_valid:  # Object style
    print(result["overall_score"])  # Dict style
```

### Strategy 3: Compatibility Layer (Already Implemented)

The `service_factory.py` already includes backwards compatibility:

```python
# Automatically handles both formats
"validation_score": (
    response.validation_result.get("overall_score", 0.0)
    if isinstance(response.validation_result, dict)
    else response.validation_result.score
    if hasattr(response.validation_result, "score")
    else 0.0
)
```

## Common Migration Patterns

### Pattern 1: Validation Checks

```python
# Before
if not validator.validate(definition).is_valid:
    raise ValidationError("Invalid definition")

# After
result = await validator.validate_definition(begrip, text)
if not result.get("is_acceptable", False):
    raise ValidationError("Invalid definition")
```

### Pattern 2: Error Collection

```python
# Before
errors = []
for error in validation_result.errors:
    errors.append(error.message)

# After
errors = []
for violation in validation_result.get("violations", []):
    errors.append(violation["message"])
```

### Pattern 3: Score Thresholds

```python
# Before
if validation_result.score < 0.75:
    log.warning(f"Low score: {validation_result.score}")

# After
score = validation_result.get("overall_score", 0.0)
if score < 0.75:
    log.warning(f"Low score: {score}")
```

### Pattern 4: Filtering by Severity

```python
# Before
errors = [e for e in result.errors if e.severity == "error"]
warnings = [e for e in result.errors if e.severity == "warning"]

# After
violations = result.get("violations", [])
errors = [v for v in violations if v["severity"] == "error"]
warnings = [v for v in violations if v["severity"] == "warning"]
```

## Testing Your Migration

### Unit Test Updates

```python
# Before
def test_validation():
    result = Mock()
    result.is_valid = True
    result.score = 0.85
    
# After
def test_validation():
    result = {
        "is_acceptable": True,
        "overall_score": 0.85,
        "violations": []
    }
```

### Integration Test Updates

```python
# Before
@patch('validator.validate')
def test_integration(mock_validate):
    mock_validate.return_value.is_valid = True
    
# After
@patch('validator.validate_definition')
async def test_integration(mock_validate):
    mock_validate.return_value = {
        "is_acceptable": True,
        "overall_score": 0.9
    }
```

## Deprecation Timeline

- **Current**: Both object and dict formats supported
- **Next Release**: Dict format is default, object format deprecated
- **Future**: Object format removed

## Need Help?

If you encounter issues during migration:

1. Check if `service_factory.py` compatibility layer handles your case
2. Use the `ValidationResultAdapter` wrapper for gradual migration
3. Run tests with both formats to ensure compatibility

## Benefits of the New Format

1. **JSON Serializable**: Direct database storage without custom serializers
2. **Type Safety**: TypedDict provides better IDE support
3. **Performance**: No object instantiation overhead
4. **Consistency**: Same format across all services
5. **Schema Validation**: Can validate against JSON Schema