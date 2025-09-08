# Validation Orchestrator V2 - Rollout Runbook

---
document: Validation Orchestrator Rollout Runbook
version: 1.0
status: DRAFT
type: Runbook
parent: # validation_orchestrator_v2.md (gearchiveerd)
related:
  - validation_result_contract.md
  - error_catalog_validation.md
  - golden-dataset-validation.md
see-also:
  - validation_observability_privacy.md
  - ../architectuur/SOLUTION_ARCHITECTURE.md
owner: DevOps Lead
created: 2024-12-29
updated: 2024-12-29
tags: [validation, rollout, deployment, feature-flag, shadow-mode]
---

## Executive Summary

Dit runbook beschrijft de veilige, gefaseerde rollout van ValidationOrchestratorV2 via feature flags, shadow mode comparison, en automated rollback procedures.

## Prerequisites

### Technical Requirements
- [ ] Feature flag `VALIDATION_ORCHESTRATOR_V2` geconfigureerd
- [ ] Monitoring dashboards live (Grafana/Datadog)
- [ ] Alerting rules actief
- [ ] Golden dataset beschikbaar
- [ ] Contract tests passing
- [ ] Re-entrancy verificatie compleet
- [ ] Rollback scripts getest

### Organizational Requirements
- [ ] Change Advisory Board (CAB) approval
- [ ] Stakeholder communication sent
- [ ] On-call schedule confirmed
- [ ] Rollback owner assigned
- [ ] Success criteria agreed

## Rollout Phases

### Phase 0: Shadow Mode (Production)

**Duration**: 48-72 hours
**Traffic**: 100% old path, 100% shadow new path
**Purpose**: Baseline comparison zonder user impact

#### Configuration
```yaml
feature_flags:
  VALIDATION_ORCHESTRATOR_V2:
    enabled: false
    shadow_mode: true
    shadow_sample_rate: 1.0  # 100% shadow
    correlation_enabled: true
```

#### Metrics to Monitor
| Metric | Threshold | Alert Level | Action |
|--------|-----------|-------------|--------|
| diff_rate | ≤2% | - | Continue |
| diff_rate | 2-5% | Warning | Investigate differences |
| diff_rate | >5% | Critical | Stop rollout, investigate |
| p95_latency_delta | ≤+10% | - | Continue |
| p95_latency_delta | >+10% | Warning | Check performance |
| error_rate_delta | ≤+0.2pp | - | Continue |
| error_rate_delta | >+0.2pp | Critical | Stop rollout |

#### Shadow Comparison Logic
```python
async def shadow_compare(request: ValidationRequest) -> ShadowResult:
    # Run both paths
    old_result = await old_validator.validate(request)
    new_result = await new_validator.validate(request)

    # Compare results
    diff = compare_results(old_result, new_result)

    # Log differences
    if diff.has_differences:
        await log_shadow_diff(
            correlation_id=request.correlation_id,
            diff=diff,
            old_result=sanitize(old_result),
            new_result=sanitize(new_result)
        )

    # Emit metrics
    metrics.increment("shadow.total")
    if diff.has_differences:
        metrics.increment("shadow.differences")
        metrics.histogram("shadow.score_delta", diff.score_delta)

    # Always return old result to user
    return old_result
```

### Phase 1: Canary Deployment (10%)

**Duration**: 24-48 hours
**Traffic**: 10% new path, 90% old path
**Purpose**: Limited production exposure

#### Configuration
```yaml
feature_flags:
  VALIDATION_ORCHESTRATOR_V2:
    enabled: true
    rollout_percentage: 10
    shadow_mode: false
    sticky_sessions: true  # Consistent per user
```

#### Canary Selection
```python
def should_use_v2(user_id: str, percentage: float) -> bool:
    """Deterministic canary selection."""
    hash_value = hashlib.md5(user_id.encode()).hexdigest()
    user_bucket = int(hash_value[:8], 16) % 100
    return user_bucket < percentage
```

#### Success Criteria
- [ ] Error rate delta <0.5pp
- [ ] P95 latency delta <20%
- [ ] No critical alerts
- [ ] User complaint rate normal
- [ ] All contract tests passing

### Phase 2: Progressive Rollout (50%)

**Duration**: 24 hours
**Traffic**: 50% new path
**Purpose**: Broader validation

#### Configuration
```yaml
feature_flags:
  VALIDATION_ORCHESTRATOR_V2:
    enabled: true
    rollout_percentage: 50
```

#### Additional Monitoring
- User feedback channels
- Support ticket volume
- Business metrics impact

### Phase 3: Full Rollout (100%)

**Duration**: 48 hours observation
**Traffic**: 100% new path
**Purpose**: Complete migration

#### Configuration
```yaml
feature_flags:
  VALIDATION_ORCHESTRATOR_V2:
    enabled: true
    rollout_percentage: 100
    legacy_endpoint_enabled: true  # Keep for emergency
```

### Phase 4: Cleanup

**After**: 1 sprint (2 weeks)
**Actions**:
- [ ] Remove feature flag
- [ ] Delete legacy code paths
- [ ] Archive shadow comparison logs
- [ ] Update documentation
- [ ] Close rollout ticket

## Telemetry & Metrics

### Key Metrics

```prometheus
# Request rate
rate(validation_requests_total[5m])

# Error rate
rate(validation_errors_total[5m]) / rate(validation_requests_total[5m])

# Latency percentiles
histogram_quantile(0.50, validation_duration_seconds)
histogram_quantile(0.95, validation_duration_seconds)
histogram_quantile(0.99, validation_duration_seconds)

# Shadow mode differences
rate(shadow_differences_total[5m]) / rate(shadow_comparisons_total[5m])

# Score divergence
histogram_quantile(0.95, shadow_score_delta)

# Rule coverage
validation_rules_evaluated / validation_rules_total
```

### Dashboard Queries

#### Grafana Dashboard
```json
{
  "panels": [
    {
      "title": "Validation Error Rate",
      "targets": [{
        "expr": "rate(validation_errors_total[5m])"
      }]
    },
    {
      "title": "P95 Latency Comparison",
      "targets": [
        {"expr": "histogram_quantile(0.95, validation_v1_duration)", "legend": "V1"},
        {"expr": "histogram_quantile(0.95, validation_v2_duration)", "legend": "V2"}
      ]
    },
    {
      "title": "Shadow Diff Rate",
      "targets": [{
        "expr": "rate(shadow_differences_total[5m]) / rate(shadow_comparisons_total[5m])"
      }]
    }
  ]
}
```

### Alert Configuration

```yaml
alerts:
  - name: ValidationHighErrorRate
    expr: rate(validation_errors_total[5m]) > 0.05
    for: 5m
    severity: warning
    annotations:
      summary: "Validation error rate above 5%"

  - name: ValidationHighDiffRate
    expr: rate(shadow_differences_total[5m]) / rate(shadow_comparisons_total[5m]) > 0.05
    for: 10m
    severity: critical
    annotations:
      summary: "Shadow comparison diff rate above 5%"

  - name: ValidationHighLatency
    expr: histogram_quantile(0.95, validation_duration_seconds) > 1.0
    for: 5m
    severity: warning
    annotations:
      summary: "P95 validation latency above 1s"
```

## Rollback Procedures

### Immediate Rollback (Emergency)

**Time to Rollback**: <1 minute

```bash
# 1. Disable feature flag immediately
curl -X POST https://config-service/flags/VALIDATION_ORCHESTRATOR_V2 \
  -d '{"enabled": false, "rollout_percentage": 0}'

# 2. Verify traffic routing
watch 'curl -s https://metrics/api/v1/query?query=validation_orchestrator_active'

# 3. Clear caches if needed
redis-cli FLUSHDB

# 4. Notify stakeholders
./scripts/notify_rollback.sh "Emergency rollback executed"
```

### Gradual Rollback (Controlled)

**Time to Rollback**: 5-10 minutes

```bash
# 1. Reduce percentage gradually
for pct in 50 25 10 0; do
  curl -X POST https://config-service/flags/VALIDATION_ORCHESTRATOR_V2 \
    -d "{\"rollout_percentage\": $pct}"
  sleep 120  # Wait 2 minutes between steps
  ./scripts/check_metrics.sh || break
done

# 2. Monitor metrics during rollback
watch -n 5 './scripts/rollback_metrics.sh'
```

### Post-Rollback Actions

1. **Immediate** (within 1 hour):
   - [ ] Confirm metrics stabilized
   - [ ] Collect error logs
   - [ ] Document timeline
   - [ ] Notify stakeholders

2. **Short-term** (within 24 hours):
   - [ ] Root cause analysis
   - [ ] Create bug tickets
   - [ ] Update runbook
   - [ ] Schedule retrospective

3. **Long-term** (within 1 week):
   - [ ] Fix identified issues
   - [ ] Update tests
   - [ ] Plan re-rollout
   - [ ] Share learnings

## Safety & Privacy

### Correlation IDs
Every request MOET een correlation ID hebben:
```python
correlation_id = request.headers.get('X-Correlation-ID') or str(uuid.uuid4())
```

### PII Masking
```python
def mask_validation_logs(log_entry: dict) -> dict:
    """Mask PII in validation logs."""
    if 'definition_text' in log_entry:
        # Only log first 100 chars
        log_entry['definition_text'] = log_entry['definition_text'][:100] + '...[TRUNCATED]'
    if 'user_id' in log_entry:
        # Hash user ID
        log_entry['user_id'] = hashlib.sha256(log_entry['user_id'].encode()).hexdigest()[:8]
    return log_entry
```

### Log Retention
| Environment | Retention | Purpose |
|-------------|-----------|---------|
| Development | 30 days | Debugging |
| Staging | 60 days | Testing |
| Production | 90 days | Compliance (AVG/BIO) |
| Archives | 1 year | Audit trail |

## Communication Plan

### Stakeholder Matrix

| Stakeholder | When | Channel | Message |
|-------------|------|---------|---------|
| Dev Team | T-1 week | Slack | Rollout schedule |
| Product | T-3 days | Email | Feature flag timeline |
| Support | T-1 day | Training | What to expect |
| Users | T-0 | In-app | Maintenance notice |
| Leadership | T+1 day | Report | Success metrics |

### Status Page Updates

```markdown
## Validation Service Upgrade
**Status**: In Progress
**Impact**: None expected
**Started**: 2024-12-29 10:00 CET

We're upgrading our validation service to improve performance
and accuracy. No user impact expected.

Updates:
- 10:00 - Shadow mode enabled
- 10:30 - Metrics nominal
- 11:00 - Starting canary rollout (10%)
```

## Ownership & Escalation

### RACI Matrix

| Task | Responsible | Accountable | Consulted | Informed |
|------|------------|-------------|-----------|----------|
| Flag toggle | DevOps | Tech Lead | Dev Team | Product |
| Monitoring | DevOps | DevOps Lead | SRE | Tech Lead |
| Rollback decision | Tech Lead | CTO | DevOps, Product | All |
| Communication | Product | Product Lead | Tech Lead | Users |

### Escalation Path

1. **L1**: On-call engineer (0-15 min)
2. **L2**: Tech Lead (15-30 min)
3. **L3**: Platform Team (30-60 min)
4. **L4**: CTO (>60 min)

## Related Documents
<!-- Validation Orchestrator V2 document gearchiveerd - functionaliteit gedocumenteerd in TECHNICAL_ARCHITECTURE.md -->
- **Contract**: [ValidationResult Contract](../architectuur/contracts/validation_result_contract.md)
- **Errors**: [Error Catalog](../technisch/error_catalog_validation.md)
- **Testing**: [Golden Dataset](../testing/golden-dataset-validation.md)
- **Monitoring**: [Observability Guide](../technisch/validation_observability_privacy.md)

## Appendix: Scripts

### check_metrics.sh
```bash
#!/bin/bash
# Check if metrics are within acceptable range

ERROR_RATE=$(curl -s https://metrics/api/v1/query?query=validation_error_rate | jq '.data.result[0].value[1]')
LATENCY_P95=$(curl -s https://metrics/api/v1/query?query=validation_p95_latency | jq '.data.result[0].value[1]')

if (( $(echo "$ERROR_RATE > 0.05" | bc -l) )); then
  echo "ERROR: Error rate too high: $ERROR_RATE"
  exit 1
fi

if (( $(echo "$LATENCY_P95 > 1.0" | bc -l) )); then
  echo "WARNING: P95 latency high: $LATENCY_P95"
fi

echo "Metrics OK - Error: $ERROR_RATE, P95: $LATENCY_P95"
```

## Change Log
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2024-12-29 | Initial runbook | DevOps Lead |

---
*This runbook must be reviewed before each rollout and updated based on lessons learned.*
