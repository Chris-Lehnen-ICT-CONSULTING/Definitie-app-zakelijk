# ModularValidationService API Documentation

## Overview
The `ModularValidationService` is a lightweight, async-first validation service that provides deterministic validation results for Dutch definitions. It supports both individual and batch validation operations.

## Class: ModularValidationService

### Constructor

```python
ModularValidationService(
    toetsregel_manager: Optional[ToetsregelManager] = None,
    cleaning_service: Optional[CleaningService] = None,
    config: Optional[Config] = None
)
```

**Parameters:**
- `toetsregel_manager`: Optional manager for loading validation rules from external sources
- `cleaning_service`: Optional service for text cleaning/normalization
- `config`: Optional configuration object for weights and thresholds

### Methods

#### `async validate_definition()`

Validates a single definition text against configured rules.

```python
async def validate_definition(
    begrip: str,
    text: str,
    ontologische_categorie: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

**Parameters:**
- `begrip`: The concept/term being defined
- `text`: The definition text to validate
- `ontologische_categorie`: Optional ontological category for context-aware validation
- `context`: Optional context dictionary with metadata

**Returns:**
A dictionary conforming to the ValidationResult schema:

```python
{
    "version": "1.0.0",
    "overall_score": 0.85,  # Float between 0.0-1.0
    "is_acceptable": True,   # Boolean indicating if definition passes threshold
    "violations": [
        {
            "code": "VAL-LEN-001",
            "severity": "warning",
            "message": "Definition is too short",
            "rule_id": "VAL-LEN-001",
            "category": "structuur"
        }
    ],
    "passed_rules": ["ESS-CONT-001", "CON-CIRC-001"],
    "detailed_scores": {
        "taal": 0.90,
        "juridisch": 0.85,
        "structuur": 0.80,
        "samenhang": 0.88
    },
    "system": {
        "correlation_id": "uuid-string"
    }
}
```

**Example:**

```python
service = ModularValidationService()
result = await service.validate_definition(
    begrip="proces",
    text="Een proces is een reeks van samenhangende activiteiten."
)

if result["is_acceptable"]:
    print(f"Valid! Score: {result['overall_score']}")
else:
    for violation in result["violations"]:
        print(f"Issue: {violation['code']} - {violation['message']}")
```

#### `async batch_validate()`

Validates multiple definitions in batch with optional concurrency control.

```python
async def batch_validate(
    items: List[Union[ValidationRequest, Tuple[str, str], Dict]],
    max_concurrency: int = 1
) -> List[Dict[str, Any]]
```

**Parameters:**
- `items`: List of items to validate. Can be:
  - `ValidationRequest` objects
  - Tuples of `(begrip, text)`
  - Dictionaries with `begrip` and `text` keys
- `max_concurrency`: Maximum number of parallel validations (default: 1 for sequential)

**Returns:**
List of ValidationResult dictionaries in the same order as input items.

**Example:**

```python
# Using ValidationRequest objects
from services.validation.interfaces import ValidationRequest

items = [
    ValidationRequest(begrip="proces", text="Een proces is..."),
    ValidationRequest(begrip="systeem", text="Een systeem is...")
]

# Sequential processing
results = await service.batch_validate(items, max_concurrency=1)

# Parallel processing (up to 5 concurrent)
results = await service.batch_validate(items, max_concurrency=5)

# Using tuples (backwards compatibility)
simple_items = [
    ("begrip1", "Definitie tekst 1"),
    ("begrip2", "Definitie tekst 2")
]
results = await service.batch_validate(simple_items)
```

## Validation Rules

### Default Rules

Wanneer no `ToetsregelManager` is provided, the service uses these default rules:

| Rule Code | Description | Weight | Category |
|-----------|-------------|--------|----------|
| VAL-EMP-001 | Empty text validation | 1.0 | juridisch |
| VAL-LEN-001 | Minimum length (20 chars) | 0.9 | juridisch |
| VAL-LEN-002 | Maximum length (500 chars) | 0.6 | juridisch |
| ESS-CONT-001 | Essential content check | 1.0 | juridisch |
| CON-CIRC-001 | Circular definition check | 0.8 | samenhang |
| STR-TERM-001 | Terminology structure | 0.5 | structuur |
| STR-ORG-001 | Organization structure | 0.7 | structuur |

### Dynamic Rule Loading

Wanneer a `ToetsregelManager` is provided, rules are loaded dynamically:

```python
from toetsregels.manager import ToetsregelManager

manager = ToetsregelManager()
service = ModularValidationService(toetsregel_manager=manager)

# Service now uses rules from manager (typically 40+ rules)
```

## Configuration

### Weights Configuration

Customize rule weights via config:

```python
config = Config(
    weights={
        "VAL-EMP-001": 1.0,
        "VAL-LEN-001": 0.8,
        "ESS-CONT-001": 0.9
    }
)
service = ModularValidationService(config=config)
```

### Threshold Configuration

Set acceptance threshold:

```python
config = Config(
    thresholds={
        "overall_accept": 0.75  # Definitions with score >= 0.75 are acceptable
    }
)
```

## Error Handling

The service uses degraded error handling - validation always returns a result:

- If a rule fails, it's marked as a violation but doesn't stop validation
- If cleaning fails, original text is used
- If ToetsregelManager fails, default rules are used
- System errors are captured in the `system.error` field

## Prestaties Considerations

- **Sequential validation** (`max_concurrency=1`): Predictable, lower resource usage
- **Parallel validation** (`max_concurrency>1`): Faster for large batches, higher memory usage
- **Rule evaluation**: All rules are evaluated independently for isolation
- **Deterministic output**: Same input always produces same output (given same rules/config)

## Migration from Legacy ValidationService

See the [Migration Guide](./migration-guide-validation-result.md) for details on migrating from the legacy ValidationService to ModularValidationService.
