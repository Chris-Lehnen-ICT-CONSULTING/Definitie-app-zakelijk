# ValidationResult Contract

---
document: ValidationResult Contract
version: 1.0
status: CONCEPT
type: Contract
parent: validation_orchestrator_v2.md
related:
  - error_catalog_validation.md
  - validation_result.schema.json
  - validation_orchestrator_rollout.md
see-also:
  - golden-dataset-validation.md
  - ADR-006-validation-orchestrator-v2.md
owner: Dev Lead
created: 29-12-2024
updated: 29-12-2024
tags: [validation, contract, v2, async, schema]
---

## Executive Summary

Dit document definieert het bindende contract voor `ValidationResult` objecten in de ValidationOrchestratorV2. Het specificeert data structuur, versie beleid, en compatibility garanties.

## Scope & Status

- **Scope**: Alle validation responses van ValidationOrchestratorV2
- **Versie**: 2.2.0 (SemVer)
- **Backward Compatibility**: Gegarandeerd binnen major version. De overgang 1.x → 2.0.0 is een betekenisverandering (zie tabel); legacy-invoer blijft leesbaar via de normalisatie in `services.validation.result_contract`, maar levert nooit een oordeel.

### Wijzigingen

| Versie | Wijziging |
| --- | --- |
| 2.2.0 | DEF-771 (26-09-2026): een deeluitkomst in `rule_results` (`parts[].status`) mag `not_evaluated` zijn. INT-02 boekt bij ontbrekende kern of context `rule_results['INT-02']` met status `not_evaluated`, `score` en `fingerprint` `null`, `contract_version` uit het regelrecord en één onderdeel `invoer` met de exacte melding "INT-02 — Niet uitgevoerd: {kern/context} ontbreekt. Er is geen inhoudelijk oordeel." Geen oordeel, score, reviewpunt of poort; `rule_statuses` en de dekking blijven zoals ze waren. Additief; geen nieuw veld. |
| 2.0.0 | DEF-624 (deellevering 1, 16-09-2026): `validation_status` is verplicht in de canonieke uitvoervorm en heeft geen `default: validated` meer. Een afwezige, null of ongeldige status betekent niet langer "uitgevoerde run" maar wordt aan de invoergrens (dict, legacy object, fabriek, adapter) `validation_unknown` met reden `contract_status_missing` / `contract_status_invalid`; een degraded result is `validation_unknown` met `validation_error`. `validation_readiness` is alleen bij `ruleset_incomplete` verplicht (alleen dan gemeten). Bij `validation_unknown` is `is_acceptable` altijd `false` en `overall_score` 0 of null. Conversies verzinnen geen geslaagde regels (de oude `BASIC-00x`-default vervalt) en maken van een `None`-score geen 0.0 (ook niet via de legacy-sleutel `score`). In de TypedDict-binding zijn de schemaverplichte velden `Required[...]` (`ValidationResult.__required_keys__` == `required`); een expliciet `source_assessment: null` reist bij conversie mee en een aanwezige ongeldige status wordt als `contract_status_invalid` (niet als ontbrekend) gemeld. `services.validation.types` voert geen eigen versie meer maar herexporteert dit contract; de fabriek normaliseert een afwezige/ongeldige status via de centrale statusbepaling (AC 1) en weigert alleen tegenstrijdige expliciete metadata (reden bij validated, expliciete unknown zonder contractuele reden, `ruleset_incomplete` zonder volledige readiness, readiness buiten de schemavorm); `is_valid_result` volgt de conditionele schema-eisen incl. de unknown-placeholders en de readinessvorm. Vorige versie gepind als `schemas/validation_result_v1.4.0.schema.json`. |
| 1.4.0 | DEF-743: `source_assessment` (volledige AI-bronbeoordeling CON-02, of null) toegevoegd. Additief. |
| 1.3.0 | DEF-622: `rule_results` toegevoegd; `overall_score` en categoriescores mogen `null` zijn (geen noemer zonder CON-01). Additief. |
| 1.2.0 | DEF-621: `validation_status`, `unknown_reason` (`ruleset_incomplete`) en `validation_readiness` toegevoegd. Additief. |
| 1.1.0 | DEF-624: `rule_statuses`, `evaluation_coverage` en `review_required` toegevoegd. Additief; geen veld verdwenen of van betekenis veranderd. `additionalProperties` blijft bewust `false` — een nieuw veld mag niet stil binnenglippen. |
| 1.0.0 | Initieel contract. Gepind als `schemas/validation_result_v1.0.0.schema.json`. |

### Runstatus (2.0.0)

`validation_status` zegt uitsluitend of een producent werkelijk een run
uitvoerde; het is niet de kwaliteitsuitkomst. Een fail, een open review
(`review_required`) of een technische regelfout (`rule_statuses[...] = error`)
blijft `validated`. Alleen `validated` opent een gate, bewaart een score of
laat een hertoetsing als bewijs gelden; een `validation_unknown` draagt zijn
regel- en bronuitkomsten uitsluitend ter uitleg mee.

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

  // Evaluatiedekking naast de score (1.1.0, optioneel)
  rule_statuses?: Record<string, RuleResultStatus>;
  evaluation_coverage?: EvaluationCoverage;
  review_required?: ReviewRequirement[];
}
```

### Score versus evaluatiedekking (1.1.0)

`overall_score` wordt uitsluitend berekend over regels met status `pass` of
`fail`. `review_required`, `not_evaluated` en `error` vallen uit de noemer:
zij tellen nooit als 1,0 mee. Zonder die scheiding zou een lagere dekking als
hogere kwaliteit verschijnen — een regel die niet draait, kan immers ook niet
falen.

Consumers die kwaliteit tonen, horen beide getallen te tonen.

```typescript
type RuleResultStatus =
  | "pass"              // uitgevoerd, voldoet
  | "fail"              // uitgevoerd, voldoet niet
  | "review_required"   // vraagt menselijk oordeel
  | "not_evaluated"     // vereiste invoer ontbrak
  | "error";            // evaluator faalde

interface EvaluationCoverage {
  evaluated: number;        // pass + fail
  passed: number;
  failed: number;
  review_required: number;
  not_evaluated: number;
  error: number;
  total: number;
  coverage_ratio: number;   // evaluated / total, 0.0 - 1.0
}

interface ReviewRequirement {
  rule_id: string;
  category: string;
  reason: string;
  signals: string[];        // patroontreffers als aanwijzing, geen bewijs
}
```

`review_required` is bewust géén `violations`-entry: reviewplicht is geen
geconstateerd kwaliteitsprobleem. De `signals` wijzen de beoordelaar waar te
kijken en mogen niet als bewijs worden gepresenteerd.

### ValidationViolation Structure

```typescript
interface ValidationViolation {
  // Identification
  code: string;              // Error code (zie Error Catalog)
  rule_id: string;           // Specific rule (e.g., "ARAI04SUB1")
  category: string;          // Category (taal|juridisch|structuur|samenhang|system)

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

## Compatibility Testen

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

## Backward Compatibility Mapping (v1.0.0 → latest)

- Pinned schema `validation_result_v1.0.0.schema.json` hanteert andere veldnamen/structuur dan de “latest” variant.
- Belangrijkste verschillen en mapping voor consumers:
  - `metadata` (v1) → `system` (latest)
    - `metadata.correlation_id` → `system.correlation_id`
    - `metadata.processing_time_ms` → `system.duration_ms`
    - `metadata.validator_version` → `system.engine_version`
  - `warnings` (v1 optioneel array) → geen direct equivalent; opnemen als `violations` met `severity="info"` indien gewenst.
- Richtlijn:
  - Producers: lever “latest” (`system`) uit.
  - Consumers: ondersteun v1 via een lichte adapter die bovenstaande mapping toepast.

## Related Documents
- **Parent**: Validation Orchestrator V2 Architecture (see Solution Architecture)
- **Schema**: [JSON Schema Definition](./schemas/validation_result.schema.json)
- **Errors**: [Error Catalog](../../technisch/error_catalog_validation.md)
- **Usage**: Rollout Runbook (documentation in planning)
- **Testen**: [Golden Dataset](../../testing/golden-dataset-validation.md)

## Change Log
| Versie | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 29-12-2024 | Initial contract definition | Dev Lead |

---
*Contract governance: Changes require approval from Dev Lead + Architect*
