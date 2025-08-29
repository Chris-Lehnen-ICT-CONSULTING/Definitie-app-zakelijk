# ValidationResult Contract

---
document: ValidationResult Contract
version: 1.0
status: DRAFT
type: Contract
parent: validation_orchestrator_v2.md
related:
  - error_catalog_validation.md
  - validation_result.schema.json
  - validation_orchestrator_rollout.md
see-also:
  - golden-dataset-validation.md
  - ADR-006-validation-orchestrator-separation.md
owner: Dev Lead
created: 2024-12-29
updated: 2024-12-29
tags: [validation, contract, v2, async, schema]
---

## Executive Summary

Dit document definieert het bindende contract voor `ValidationResult` objecten in de ValidationOrchestratorV2. Het specificeert data structuur, versie beleid, en compatibility garanties.

## Scope & Status

- **Scope**: Alle validation responses van ValidationOrchestratorV2
- **Versie**: 1.0.0 (SemVer)
- **Backward Compatibility**: Gegarandeerd binnen major version

## Versie Beheer

### Semantic Versioning
- **Major** (1.x.x): Breaking changes - veld verwijdering, type changes, semantiek breuk
- **Minor** (x.1.x): Non-breaking additions - nieuwe optionele velden
- **Patch** (x.x.1): Bug fixes, documentatie updates

### Compatibility Rules
- Consumers MOETEN unknown fields ignoreren (forward compatibility)
- Producers MOGEN NIET required fields weglaten (backward compatibility)
- Schema validatie via JSON Schema draft 2020-12

## Data Model

### Core Fields

```typescript
interface ValidationResult {
  // Contract metadata
  version: string;           // Contract versie (e.g., "1.0.0")

  // Validation outcome
  overall_score: number;     // 0.0 - 1.0
  is_acceptable: boolean;    // Pass/fail decision

  // Violations detail
  violations: ValidationViolation[];
  passed_rules: string[];    // Rule IDs that passed

  // Scoring breakdown
  detailed_scores: Record<string, number>;

  // Improvements (optional)
  improvement_suggestions?: Suggestion[];

  // System metadata (optional)
  system?: SystemMetadata;
}
```

### ValidationViolation Structure

```typescript
interface ValidationViolation {
  // Identification
  code: string;              // Error code (zie Error Catalog)
  rule_id: string;           // Specific rule (e.g., "ARAI04SUB1")
  category: string;          // Category (taal|juridisch|structuur|samenhang)

  // Details
  severity: 'info' | 'warning' | 'error';
  message: string;           // User-friendly message (i18n ready)

  // Location (optional)
  location?: {
    text_span?: { start: number; end: number };
    indices?: number[];
    line?: number;
    column?: number;
  };

  // Remediation
  suggestions?: string[];    // Possible fixes
  metadata?: Record<string, any>;  // Additional context
}
```

### SystemMetadata Structure

```typescript
interface SystemMetadata {
  correlation_id: string;    // Request tracing ID
  engine_version?: string;   // Validator version
  profile_used?: string;     // Validation profile
  timestamp?: string;        // ISO 8601
  duration_ms?: number;      // Processing time

  timings?: {
    cleaning_ms?: number;
    validation_ms?: number;
    enhancement_ms?: number;
  };
}
```

## JSON Schema

Volledig schema: [validation_result.schema.json](./schemas/validation_result.schema.json)

### Validatie
```bash
# Validate response
ajv validate -s validation_result.schema.json -d response.json

# TypeScript types generation
json2ts validation_result.schema.json > ValidationResult.d.ts
```

## Mapping Strategy

### Modern Validator → Services Interface

```python
# src/services/validation/mappers.py
def map_to_interface(modern_result: ModernValidationResult) -> ValidationResult:
    return ValidationResult(
        version="1.0.0",
        overall_score=modern_result.overall_score,
        is_acceptable=modern_result.is_acceptable,
        violations=[map_violation(v) for v in modern_result.violations],
        passed_rules=modern_result.passed_rules,
        detailed_scores=modern_result.detailed_scores,
        improvement_suggestions=modern_result.suggestions,
        system={
            "correlation_id": context.correlation_id,
            "engine_version": modern_result.engine_version,
            "profile_used": modern_result.profile_name
        }
    )
```

## Error Handling

Validation results zijn ALTIJD functioneel - exceptions worden opgevangen:

```python
try:
    result = await validator.validate(...)
except Exception as e:
    # Return degraded result, not exception
    return ValidationResult(
        version="1.0.0",
        overall_score=0.0,
        is_acceptable=False,
        violations=[{
            "code": "SYS-INT-001",
            "severity": "error",
            "message": "Validation service unavailable",
            "rule_id": "SYSTEM",
            "category": "system"
        }],
        passed_rules=[],
        detailed_scores={},
        system={"error": str(e)}
    )
```

## Example Payloads

### Success Response
```json
{
  "version": "1.0.0",
  "overall_score": 0.86,
  "is_acceptable": true,
  "violations": [
    {
      "code": "VAL-STR-001",
      "severity": "warning",
      "message": "Zin bevat meer dan 20 woorden",
      "rule_id": "ARAI04",
      "category": "structuur",
      "location": {
        "text_span": {"start": 12, "end": 47}
      },
      "suggestions": ["Splits de zin op bij 'waarbij'"]
    }
  ],
  "passed_rules": ["VAL-LNG-001", "VAL-JUR-002", "VAL-SAM-001"],
  "detailed_scores": {
    "taal": 0.9,
    "juridisch": 0.8,
    "structuur": 0.85,
    "samenhang": 0.88
  },
  "system": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
    "engine_version": "2.1.0",
    "profile_used": "default",
    "duration_ms": 145
  }
}
```

### Validation Failure
```json
{
  "version": "1.0.0",
  "overall_score": 0.42,
  "is_acceptable": false,
  "violations": [
    {
      "code": "VAL-JUR-003",
      "severity": "error",
      "message": "Definitie bevat circulaire verwijzing",
      "rule_id": "ARAI02",
      "category": "juridisch"
    }
  ],
  "passed_rules": [],
  "detailed_scores": {
    "taal": 0.7,
    "juridisch": 0.2,
    "structuur": 0.5,
    "samenhang": 0.3
  }
}
```

## Compatibility Testing

### Golden Snapshots
- Maintain bij: `tests/fixtures/golden/validation_results/`
- Update alleen met explicit changelog entry
- Automated regression via: `pytest tests/contracts/test_validation_contract.py`

### Contract Tests
```python
def test_contract_compatibility():
    # Load all golden snapshots
    for snapshot in golden_snapshots:
        # Validate against schema
        assert validate_schema(snapshot, "validation_result.schema.json")
        # Check backward compatibility
        assert can_deserialize_v1(snapshot)
```

## Related Documents
- **Parent**: [Validation Orchestrator V2 Architecture](../validation_orchestrator_v2.md)
- **Schema**: [JSON Schema Definition](./schemas/validation_result.schema.json)
- **Errors**: [Error Catalog](../../technisch/error_catalog_validation.md)
- **Usage**: [Rollout Runbook](../../workflows/validation_orchestrator_rollout.md)
- **Testing**: [Golden Dataset](../../testing/golden-dataset-validation.md)

## Change Log
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2024-12-29 | Initial contract definition | Dev Lead |

---
*Contract governance: Changes require approval from Dev Lead + Architect*
