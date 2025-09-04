---
canonical: true
status: active
owner: architecture
last_verified: 2025-09-04
applies_to: definitie-app@v2-cfr
---

# Context Flow Refactoring - Migration Strategy

## Executive Summary

This document provides the detailed migration strategy from the current broken multi-path context system to the new single-path architecture. The migration is designed to be performed in phases with feature flags to minimize risk.

## Current State Analysis

### Identified Legacy Paths

1. **Path 1: Direct String Context** (DEPRECATED)
   - Location: `service_factory.py:229`
   - Issue: Concatenates lists into strings
   - Usage: ~60% of requests

2. **Path 2: Domain Field** (DEPRECATED)
   - Location: Multiple files use `domein` field
   - Issue: Separate from context fields
   - Usage: ~30% of requests

3. **Path 3: Session State** (ACTIVE)
   - Location: `ui/session_state.py`
   - Issue: Inconsistent storage
   - Usage: ~10% of requests

### Critical Bugs to Fix

| Bug ID | Location | Current Code | Fixed Code |
|--------|----------|--------------|------------|
| CFR-BUG-001 | `service_factory.py:229` | `context=", ".join(context_dict.get("organisatorisch", []))` | `organisatorische_context=context_dict.get("organisatorisch", [])` |
| CFR-BUG-001 | `prompt_service_v2.py:158-176` | Empty context extraction | Proper field mapping |
| CFR-BUG-002 | `context_selector.py:137-183` | "Anders..." in options list | Checkbox approach |

## Migration Phases

### Phase 1: Foundation (Days 1-3)

#### Day 1: Critical Bug Fixes
```python
# 1. Fix service_factory.py
# File: src/services/service_factory.py
# Line: 229
# Action: Replace string concatenation with list assignment

def generate_definition(self, begrip: str, context_dict: dict, **kwargs):
    request = GenerationRequest(
        id=str(uuid.uuid4()),
        begrip=begrip,
        # FIX: Direct list mapping
        organisatorische_context=context_dict.get("organisatorisch", []),
        juridische_context=context_dict.get("juridisch", []),
        wettelijke_basis=context_dict.get("wettelijk", []),
        # Remove deprecated string context
        context=None,  # DEPRECATED
        domein=None,   # DEPRECATED
    )
```

#### Day 2: Fix Prompt Service
```python
# 2. Fix prompt_service_v2.py
# File: src/services/prompts/prompt_service_v2.py
# Lines: 158-176
# Action: Properly extract context fields

def _convert_request_to_context(self, request: GenerationRequest, extra_context=None):
    base_context = {
        "organisatorisch": request.organisatorische_context or [],
        "juridisch": request.juridische_context or [],
        "wettelijk": request.wettelijke_basis or [],
        "domein": []  # Keep for compatibility, but empty
    }

    # No string concatenation, keep as lists
    enriched = EnrichedContext(
        base_context=base_context,
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={
            "organisatorische_context": base_context["organisatorisch"],
            "juridische_context": base_context["juridisch"],
            "wettelijke_basis": base_context["wettelijk"],
        }
    )
    return enriched
```

#### Day 3: Fix UI Component
```python
# 3. Fix context_selector.py
# File: src/ui/components/context_selector.py
# Action: Implement checkbox approach for "Anders..."

def _render_context_field(self, field_name: str, label: str, options: List[str]):
    # Checkbox for custom entry instead of in-list
    use_custom = st.checkbox(
        f"🔧 Anders... toevoegen",
        key=f"custom_check_{field_name}"
    )

    # Regular multiselect WITHOUT "Anders..." in options
    selected = st.multiselect(
        label=label,
        options=options,  # Clean list
        key=f"select_{field_name}"
    )

    # Custom input if checkbox is checked
    custom_value = None
    if use_custom:
        custom_value = st.text_input(
            f"Aangepaste {label.lower()}",
            key=f"custom_input_{field_name}",
            max_chars=100
        )
        if custom_value:
            selected.append(custom_value)

    return selected
```

### Phase 2: Type Safety (Days 4-7)

#### Day 4: Implement Context Validator
```python
# Create new file: src/services/validation/context_validator.py
class ContextValidator:
    def validate(self, data: Dict[str, Any]) -> ValidatedContext:
        # Ensure list types
        org = self._ensure_list(data.get("organisatorische_context"))
        jur = self._ensure_list(data.get("juridische_context"))
        wet = self._ensure_list(data.get("wettelijke_basis"))

        # Validate and sanitize
        return ValidatedContext(
            organisatorische_context=self._sanitize_list(org),
            juridische_context=self._sanitize_list(jur),
            wettelijke_basis=self._sanitize_list(wet),
            validation_metadata={
                "validated_at": datetime.utcnow(),
                "rules_applied": ["type_check", "sanitization"]
            }
        )
```

#### Day 5: Update Interfaces
```python
# Update: src/services/interfaces.py
@dataclass
class GenerationRequest:
    # ... existing fields ...

    # Add new context fields (lists only)
    organisatorische_context: List[str] = field(default_factory=list)
    juridische_context: List[str] = field(default_factory=list)
    wettelijke_basis: List[str] = field(default_factory=list)

    # Mark old fields as deprecated
    context: Optional[str] = field(default=None, metadata={"deprecated": True})
    domein: Optional[str] = field(default=None, metadata={"deprecated": True})
```

#### Day 6-7: Add Comprehensive Tests
```python
# Create: tests/unit/test_context_flow.py
class TestContextFlow:
    def test_context_list_types(self):
        """Ensure all context fields are lists"""

    def test_anders_option_no_crash(self):
        """Test that Anders... doesn't crash"""

    def test_context_passes_to_prompt(self):
        """Verify context reaches prompt"""
```

### Phase 3: Feature Flag Rollout (Days 8-10)

#### Day 8: Implement Feature Flags
```python
# src/config/feature_flags.py
class FeatureFlags:
    USE_NEW_CONTEXT_FLOW = "use_new_context_flow"

    @staticmethod
    def is_enabled(flag: str) -> bool:
        # Check environment variable first
        env_value = os.getenv(f"FF_{flag.upper()}", "")
        if env_value:
            return env_value.lower() == "true"

        # Check Streamlit session state
        if "feature_flags" in st.session_state:
            return st.session_state.feature_flags.get(flag, False)

        # Default values
        defaults = {
            FeatureFlags.USE_NEW_CONTEXT_FLOW: False  # Start disabled
        }
        return defaults.get(flag, False)
```

#### Day 9: Dual Path Support
```python
# src/services/context_processor.py
def process_context(data: Dict[str, Any]) -> Dict[str, List[str]]:
    if FeatureFlags.is_enabled(FeatureFlags.USE_NEW_CONTEXT_FLOW):
        # New path: direct list handling
        validator = ContextValidator()
        validated = validator.validate(data)
        return validated.to_dict()
    else:
        # Legacy path: string concatenation (log warning)
        logger.warning("Using deprecated context flow")
        return legacy_process_context(data)
```

#### Day 10: Gradual Rollout
```yaml
# deployment/feature-flags.yaml
rollout_stages:
  - stage: canary
    percentage: 10
    users: ["test_user_1", "test_user_2"]

  - stage: beta
    percentage: 25
    organizations: ["OM_TEST"]

  - stage: production
    percentage: 100
    enabled: true
```

### Phase 4: Audit & Compliance (Days 11-14)

#### Day 11: Database Migration
```sql
-- migrations/002_add_context_audit.sql
CREATE TABLE context_audit_trail (
    id BIGSERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    context_data JSONB NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    definition_id BIGINT,
    checksum VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_request ON context_audit_trail(request_id);
CREATE INDEX idx_audit_timestamp ON context_audit_trail(timestamp);
```

#### Day 12: Implement Audit Service
```python
# src/services/audit/audit_service.py
class AuditService:
    async def log_context_usage(
        self,
        request_id: str,
        context_data: ValidatedContext,
        user_id: str
    ):
        await self.db.execute(
            """
            INSERT INTO context_audit_trail
            (request_id, timestamp, context_data, user_id, checksum)
            VALUES ($1, $2, $3, $4, $5)
            """,
            request_id,
            datetime.utcnow(),
            json.dumps(context_data.to_dict()),
            user_id,
            self._calculate_checksum(context_data)
        )
```

#### Day 13-14: Compliance Reporting
```python
# src/services/compliance/astra_reporter.py
class AstraComplianceReporter:
    def generate_context_report(self, start_date, end_date):
        """Generate ASTRA compliance report for context usage"""
        return {
            "period": {"start": start_date, "end": end_date},
            "context_coverage": self._calculate_coverage(),
            "traceability_score": self._calculate_traceability(),
            "vocabulary_compliance": self._check_vocabulary(),
            "audit_completeness": self._verify_audit_trail()
        }
```

### Phase 5: Cleanup (Days 15-21)

#### Day 15-16: Remove Legacy Code
```python
# Mark deprecated code for removal
# Add deprecation warnings
import warnings

def legacy_context_handler(context: str):
    warnings.warn(
        "legacy_context_handler is deprecated, use new context flow",
        DeprecationWarning,
        stacklevel=2
    )
    # Legacy code here
```

#### Day 17-18: Update Documentation
- Update API documentation
- Create migration guide
- Update user manual
- Record architecture decisions

#### Day 19-20: Performance Optimization
```python
# Add caching for validated context
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_validated_context(context_hash: str) -> ValidatedContext:
    """Cache validated context for performance"""
    return _validate_context_internal(context_hash)
```

#### Day 21: Final Validation
- Run E2E tests
- Performance benchmarks
- Compliance validation
- User acceptance testing

## Rollback Plan

### Automatic Rollback Triggers
1. Error rate > 5% in 5 minutes
2. P95 latency > 500ms
3. Context validation failures > 10%

### Manual Rollback Procedure
```bash
# 1. Disable feature flag
export FF_USE_NEW_CONTEXT_FLOW=false

# 2. Restart services
docker-compose restart app

# 3. Verify rollback
curl http://localhost:8000/health/context-flow
# Should return: {"flow": "legacy", "status": "active"}
```

## Monitoring & Alerting

### Key Metrics
```python
# src/monitoring/context_metrics.py
from prometheus_client import Counter, Histogram

context_flow_requests = Counter(
    'context_flow_requests_total',
    'Total context flow requests',
    ['flow_type', 'status']
)

context_validation_duration = Histogram(
    'context_validation_duration_seconds',
    'Time to validate context'
)

anders_option_usage = Counter(
    'anders_option_usage_total',
    'Usage of Anders... option',
    ['field_type']
)
```

### Alert Rules
```yaml
# monitoring/alerts.yaml
groups:
  - name: context_flow
    rules:
      - alert: HighContextValidationFailureRate
        expr: rate(context_flow_requests_total{status="failure"}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High context validation failure rate"

      - alert: AndersOptionCrash
        expr: rate(anders_option_errors_total[1m]) > 0
        for: 1m
        annotations:
          summary: "Anders... option causing crashes"
```

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Context pass-through | 100% | Audit logs |
| Anders... stability | 0 crashes | Error monitoring |
| Migration time | <21 days | Project tracking |
| User disruption | <1% | Support tickets |
| Performance impact | <100ms | P95 latency |

## Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Data loss during migration | Low | High | Backup before each phase |
| User confusion | Medium | Medium | Training and documentation |
| Performance degradation | Low | Medium | Load testing and monitoring |
| Rollback failure | Low | High | Tested rollback procedures |
| Legacy integration breaks | Medium | High | Feature flags and dual paths |

## Communication Plan

### Stakeholder Updates
- **Day 0**: Announce migration plan
- **Day 3**: Phase 1 complete (bug fixes)
- **Day 7**: Phase 2 complete (type safety)
- **Day 10**: Beta rollout begins
- **Day 14**: Compliance features active
- **Day 21**: Migration complete

### User Communication
```
Subject: Belangrijke Update: Context Selectie Verbeteringen

Beste gebruiker,

We zijn bezig met het verbeteren van de context selectie in de Definitie-app.

Wat verandert er:
- Stabielere "Anders..." optie
- Betere context doorgifte naar definities
- Volledige ASTRA compliance

Wanneer:
- Start: [Date]
- Verwachte afronding: [Date + 21 days]

Actie vereist: Geen

Bij vragen: support@definitie-app.nl
```

## References

- [Epic CFR Stories](../stories/MASTER-EPICS-USER-STORIES.md#epic-cfr-context-flow-refactoring)
- [Architecture Documents](./EA-CFR.md)
- [Technical Specifications](./TA-CFR.md)
- [ADR-015](./beslissingen/ADR-015-context-flow-refactoring.md)
