# Error Catalog - Validation Services

---
document: Error Catalog Validation
version: 1.0
status: DRAFT
type: Reference
parent: validation_orchestrator_v2.md
related:
  - validation_result_contract.md
  - validation_orchestrator_rollout.md
  - validation_observability_privacy.md
see-also:
  - ADR-006-validation-orchestrator-separation.md
owner: Dev Lead
created: 2024-12-29
updated: 2024-12-29
tags: [validation, errors, taxonomy, retry, monitoring]
---

## Executive Summary

Dit document definieert de complete error taxonomie voor ValidationOrchestratorV2. Het specificeert error codes, retry policies, severity levels, en remediation strategies.

## Error Taxonomie

### Categorieën

| Category | Code Range | Type | Retryable | Description |
|----------|------------|------|-----------|-------------|
| **Validation Rule Violations** | VAL-xxx-xxx | Functional | No | Business rule violations |
| **Input Errors** | INP-xxx-xxx | Client | No | Invalid input data |
| **Policy Errors** | POL-xxx-xxx | Authorization | No | Policy/permission violations |
| **Rate Limits** | LIM-xxx-xxx | Throttling | Yes* | Rate limit exceeded |
| **Timeouts** | TMO-xxx-xxx | Temporal | Yes | Operation timeout |
| **Upstream Errors** | UPS-xxx-xxx | External | Yes* | External service errors |
| **Internal Errors** | INT-xxx-xxx | System | No** | Internal system errors |

*Retryable met backoff
**Mogelijk retryable na investigation

## Standard Error Fields

Elke error MOET deze velden bevatten:

```typescript
interface ValidationError {
  // Identification
  code: string;           // Unique error code
  title: string;          // Short description
  message: string;        // User-friendly message (no PII!)

  // Classification
  category: string;       // Error category
  severity: 'info' | 'warning' | 'error' | 'critical';
  retryable: boolean;     // Can retry solve this?

  // HTTP mapping
  http_status: number;    // HTTP status code equivalent

  // Remediation
  remediation: string;    // How to fix this
  documentation_url?: string;  // Link to detailed docs

  // Operational
  source: 'rule_engine' | 'ai' | 'schema' | 'legal' | 'system';
  telemetry_tags: string[];  // For monitoring/alerting
}
```

## Validation Rule Violations (VAL)

### Structure Violations (VAL-STR)

| Code | Title | Message | Severity | Remediation |
|------|-------|---------|----------|-------------|
| VAL-STR-001 | Long Sentence | Zin bevat meer dan 20 woorden | warning | Splits lange zinnen op voor betere leesbaarheid |
| VAL-STR-002 | Missing Structure | Definitie mist duidelijke structuur | error | Gebruik de standaard definitiestructuur: term + 'is' + uitleg |
| VAL-STR-003 | Nested Complexity | Te veel geneste bijzinnen | warning | Vereenvoudig de zinsstructuur |

### Language Violations (VAL-LNG)

| Code | Title | Message | Severity | Remediation |
|------|-------|---------|----------|-------------|
| VAL-LNG-001 | Spelling Error | Spellingsfout gedetecteerd | warning | Controleer spelling van gemarkeerde woorden |
| VAL-LNG-002 | Jargon Detected | Onnodig jargon gebruikt | info | Vervang vaktermen door begrijpelijke alternatieven |
| VAL-LNG-003 | B1 Level Exceeded | Taalniveau te complex (boven B1) | warning | Vereenvoudig woordkeuze voor B1 niveau |

### Legal Violations (VAL-JUR)

| Code | Title | Message | Severity | Remediation |
|------|-------|---------|----------|-------------|
| VAL-JUR-001 | Circular Reference | Circulaire verwijzing gedetecteerd | error | Verwijder zelfreferentie uit definitie |
| VAL-JUR-002 | Ambiguous Terms | Juridisch ambigue formulering | error | Gebruik eenduidige juridische termen |
| VAL-JUR-003 | Missing Legal Basis | Wettelijke grondslag ontbreekt | warning | Voeg verwijzing naar relevante wetgeving toe |

### Coherence Violations (VAL-SAM)

| Code | Title | Message | Severity | Remediation |
|------|-------|---------|----------|-------------|
| VAL-SAM-001 | Inconsistent Terms | Inconsistent gebruik van termen | warning | Gebruik termen consistent door hele definitie |
| VAL-SAM-002 | Context Missing | Context informatie ontbreekt | info | Voeg context toe voor duidelijkheid |
| VAL-SAM-003 | Contradiction | Tegenstrijdige informatie | error | Los tegenstrijdigheden in definitie op |

## System Errors

### Timeout Errors (TMO)

| Code | Title | HTTP | Retryable | Remediation |
|------|-------|------|-----------|-------------|
| TMO-001 | Validation Timeout | 504 | Yes | Retry met kleinere batch of verhoog timeout |
| TMO-002 | Cleaning Timeout | 504 | Yes | Vereenvoudig input text |
| TMO-003 | Enhancement Timeout | 504 | Yes | Skip enhancement of probeer later |

### Upstream Errors (UPS)

| Code | Title | HTTP | Retryable | Remediation |
|------|-------|------|-----------|-------------|
| UPS-001 | AI Service Unavailable | 503 | Yes | Wacht 30s en probeer opnieuw |
| UPS-002 | Database Unavailable | 503 | Yes | Check database connection |
| UPS-003 | External API Error | 502 | Yes | Contact external service provider |

### Internal Errors (INT)

| Code | Title | HTTP | Retryable | Remediation |
|------|-------|------|-----------|-------------|
| INT-001 | Validation Engine Error | 500 | No | Check logs, contact support |
| INT-002 | Configuration Error | 500 | No | Verify configuration settings |
| INT-003 | Memory Exhausted | 500 | Maybe | Reduce batch size, restart service |

## Retry Policies

### Exponential Backoff
```python
def get_retry_delay(attempt: int, base_delay: float = 1.0) -> float:
    """Calculate retry delay with exponential backoff + jitter."""
    delay = min(base_delay * (2 ** attempt), 60.0)  # Cap at 60s
    jitter = random.uniform(0, delay * 0.1)  # 10% jitter
    return delay + jitter
```

### Retry Matrix

| Error Category | Max Attempts | Base Delay | Strategy |
|----------------|-------------|------------|----------|
| Rate Limits | 3 | 5s | Exponential backoff |
| Timeouts | 2 | 2s | Linear backoff |
| Upstream | 3 | 1s | Exponential + jitter |
| Internal | 0 | - | No retry (investigate) |

## Error Response Format

### Standard Error Response
```json
{
  "error": {
    "code": "VAL-STR-001",
    "title": "Long Sentence",
    "message": "Zin bevat meer dan 20 woorden",
    "severity": "warning",
    "category": "validation",
    "retryable": false,
    "http_status": 422,
    "remediation": "Splits lange zinnen op voor betere leesbaarheid",
    "documentation_url": "https://docs.../errors/VAL-STR-001",
    "source": "rule_engine",
    "telemetry_tags": ["validation", "structure", "warning"],
    "details": {
      "location": {"start": 45, "end": 123},
      "rule_id": "ARAI04",
      "threshold": 20,
      "actual": 35
    }
  },
  "correlation_id": "req-123e4567-e89b",
  "timestamp": "2024-12-29T10:30:00Z"
}
```

### Batch Error Response
```json
{
  "errors": [
    {"code": "VAL-STR-001", "message": "..."},
    {"code": "VAL-JUR-002", "message": "..."}
  ],
  "partial_results": [...],
  "correlation_id": "req-123e4567-e89b"
}
```

## UI Mapping Guidelines

### Severity to UI

| Severity | Color | Icon | User Action |
|----------|-------|------|-------------|
| info | Blue | ℹ️ | Optional improvement |
| warning | Orange | ⚠️ | Should fix |
| error | Red | ❌ | Must fix |
| critical | Dark Red | 🚨 | Blocks operation |

### i18n Support

Error messages worden vertaald via code lookup:
```typescript
const errorMessages = {
  "VAL-STR-001": {
    "nl": "Zin bevat meer dan 20 woorden",
    "en": "Sentence contains more than 20 words",
    "de": "Satz enthält mehr als 20 Wörter"
  }
};
```

## Monitoring & Alerting

### Metrics to Track

```prometheus
# Error rate by code
validation_errors_total{code="VAL-STR-001", severity="warning"} 142

# Error rate by category
validation_errors_total{category="structure", severity="error"} 23

# Retry success rate
validation_retries_total{code="TMO-001", success="true"} 45
validation_retries_total{code="TMO-001", success="false"} 5
```

### Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Error rate | >5% | >10% | Check specific error codes |
| Timeout rate | >2% | >5% | Scale up or optimize |
| Retry failure | >20% | >50% | Check upstream services |
| 5xx errors | >0.1% | >1% | Page on-call engineer |

## Privacy & Security

### PII Prevention
- GEEN persoonsgegevens in error messages
- GEEN gevoelige data in logs
- Gebruik correlation IDs voor tracing
- Mask/redact waar nodig

### Log Sanitization
```python
def sanitize_error_log(error: dict) -> dict:
    """Remove PII from error before logging."""
    sanitized = error.copy()
    if 'user_input' in sanitized:
        sanitized['user_input'] = '[REDACTED]'
    if 'definition_text' in sanitized:
        sanitized['definition_text'] = sanitized['definition_text'][:50] + '...'
    return sanitized
```

## Related Documents
- **Parent**: [Validation Orchestrator V2](../architecture/validation_orchestrator_v2.md)
- **Contract**: [ValidationResult Contract](../architecture/contracts/validation_result_contract.md)
- **Implementation**: [Rollout Runbook](../workflows/validation_orchestrator_rollout.md)
- **Monitoring**: [Observability Guide](./validation_observability_privacy.md)

## Change Log
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2024-12-29 | Initial error catalog | Dev Lead |

---
*Error codes are immutable once assigned. New codes only, no reuse.*
