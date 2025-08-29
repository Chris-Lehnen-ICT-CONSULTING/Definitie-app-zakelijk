# Validation Observability & Privacy Guide

**Status**: ACTIVE  
**Version**: 1.0.0  
**Last Updated**: 2025-08-29  
**Compliance**: AVG/GDPR Compliant

## Overzicht

Deze guide beschrijft observability practices voor ValidationOrchestratorV2 met focus op privacy, monitoring, en compliance. Alle logging en metrics zijn ontworpen met privacy-by-design principes.

## Metric Naming Convention

### Standaard Metrics
```
validation.request.count          # Aantal validation requests
validation.request.duration       # Request duration in ms
validation.request.error          # Error count per error type
validation.score.distribution     # Score distributie histogram
validation.cache.hit_ratio        # Cache hit percentage
validation.batch.size             # Batch grootte distributie
```

### Naming Pattern
```
<service>.<component>.<metric>
```

Voorbeeld:
```
validation.orchestrator.latency_p95
validation.validator.timeout_count
validation.cache.memory_usage_mb
```

## Logging Strategy

### Log Levels & Content

#### DEBUG (Development Only)
```python
logger.debug(
    "Validation started",
    extra={
        "correlation_id": "uuid-here",
        "method": "validate_definition",
        "flags": {"feature_x": True}
    }
)
# NOOIT in productie, kan gevoelige data bevatten
```

#### INFO (Operational)
```python
logger.info(
    "Validation completed",
    extra={
        "correlation_id": "uuid-here",
        "duration_ms": 234,
        "score_bucket": "high",  # Niet exact score
        "cache_hit": True
    }
)
```

#### WARNING (Degraded Performance)
```python
logger.warning(
    "Validation slow",
    extra={
        "correlation_id": "uuid-here",
        "duration_ms": 5234,
        "threshold_ms": 2000
    }
)
```

#### ERROR (Failures)
```python
logger.error(
    "Validation failed",
    extra={
        "correlation_id": "uuid-here",
        "error_code": "VAL-SVC-001",
        "error_category": "service_unavailable"
        # GEEN user input of definitie content!
    }
)
```

## Privacy & PII Protection

### Data Classification
| Data Type | Classification | Logging | Metrics | Retention |
|-----------|---------------|---------|---------|-----------|
| Definitie content | CONFIDENTIAL | ❌ Never | ❌ Never | - |
| User identifiers | PERSONAL | ❌ Never | ❌ Never | - |
| Correlation IDs | INTERNAL | ✅ Yes | ✅ Yes | 30 days |
| Scores (exact) | SENSITIVE | ❌ No | ✅ Aggregated | 90 days |
| Error messages | INTERNAL | ✅ Sanitized | ✅ Count only | 30 days |
| Performance data | OPERATIONAL | ✅ Yes | ✅ Yes | 90 days |

### PII Masking Rules

```python
def sanitize_for_logging(data: dict) -> dict:
    """Remove/mask PII before logging."""
    SENSITIVE_KEYS = {
        'definition', 'content', 'text', 
        'user_id', 'email', 'name'
    }
    
    sanitized = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_KEYS:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, str) and len(value) > 100:
            sanitized[key] = f"[STRING_{len(value)}_CHARS]"
        else:
            sanitized[key] = value
    
    return sanitized
```

### Aggregation Before Storage
```python
# WRONG - Logs exact score
logger.info(f"Score: {score}")

# CORRECT - Logs score bucket
score_bucket = "high" if score > 0.8 else "medium" if score > 0.5 else "low"
logger.info(f"Score bucket: {score_bucket}")
```

## Retention Policies

### Per Environment

| Environment | Logs | Metrics | Traces | Backup |
|-------------|------|---------|--------|---------|
| Development | 7 days | 7 days | 3 days | None |
| Test | 14 days | 30 days | 7 days | None |
| Staging | 30 days | 90 days | 14 days | 7 days |
| Production | 30 days | 90 days | 30 days | 90 days |

### Automated Cleanup
```yaml
# cronjob for log rotation
0 2 * * * /usr/bin/find /var/log/validation -name "*.log" -mtime +30 -delete
0 3 * * * /usr/bin/find /var/metrics/validation -name "*.db" -mtime +90 -delete
```

## Distributed Tracing

### Correlation ID Flow
```python
class ValidationContext:
    def __init__(self, correlation_id: str = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.start_time = time.time()
        self.spans = []
    
    def create_span(self, operation: str):
        return Span(
            correlation_id=self.correlation_id,
            operation=operation,
            start_time=time.time()
        )
```

### Trace Headers
```python
TRACE_HEADERS = {
    "X-Correlation-ID": "uuid",
    "X-Request-ID": "uuid", 
    "X-Trace-Parent": "trace-id",
    "X-Trace-State": "vendor-specific"
}
```

## Dashboard Definitions

### Validation Performance Dashboard
```yaml
panels:
  - title: "Request Rate"
    query: "rate(validation.request.count[5m])"
    
  - title: "Latency P95"
    query: "histogram_quantile(0.95, validation.request.duration)"
    
  - title: "Error Rate"
    query: "rate(validation.request.error[5m]) / rate(validation.request.count[5m])"
    
  - title: "Score Distribution"
    query: "validation.score.distribution"
    type: "heatmap"
```

### Alert Definitions
```yaml
alerts:
  - name: "HighErrorRate"
    expr: "rate(validation.request.error[5m]) > 0.05"
    severity: "warning"
    
  - name: "SlowValidation"
    expr: "validation.request.duration > 2000"
    severity: "warning"
    
  - name: "ServiceDown"
    expr: "up{job='validation'} == 0"
    severity: "critical"
```

## Monitoring Implementation

### Metrics Collection
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
validation_counter = Counter(
    'validation_request_total',
    'Total validation requests',
    ['method', 'status']
)

validation_duration = Histogram(
    'validation_duration_seconds',
    'Validation duration',
    ['method'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

cache_hit_ratio = Gauge(
    'validation_cache_hit_ratio',
    'Cache hit ratio'
)

# Use in code
@validation_duration.time()
async def validate_definition(self, definition: str):
    validation_counter.labels(method='definition', status='started').inc()
    # ... validation logic ...
```

### Health Checks
```python
async def health_check():
    """Health check endpoint voor monitoring."""
    checks = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": await check_database(),
            "cache": await check_cache(),
            "validator": await check_validator_service()
        }
    }
    
    # Determine overall health
    if all(check["status"] == "healthy" for check in checks["checks"].values()):
        return JSONResponse(checks, status_code=200)
    else:
        checks["status"] = "degraded"
        return JSONResponse(checks, status_code=503)
```

## Security Considerations

### Log Injection Prevention
```python
def safe_log_value(value: str) -> str:
    """Prevent log injection attacks."""
    # Remove newlines and control characters
    safe = value.replace('\n', '\\n').replace('\r', '\\r')
    # Limit length
    if len(safe) > 200:
        safe = safe[:200] + '...'
    return safe
```

### Metric Cardinality Control
```python
# WRONG - Unbounded cardinality
metrics.labels(user_id=user_id, definition_id=def_id)

# CORRECT - Bounded cardinality
metrics.labels(
    user_type="internal" if is_internal else "external",
    score_bucket=get_score_bucket(score)
)
```

## Compliance Checklist

### AVG/GDPR Compliance
- [ ] Geen PII in logs of metrics
- [ ] Data minimalisatie toegepast
- [ ] Retention policies gedocumenteerd
- [ ] Right to erasure implementatie mogelijk
- [ ] Privacy impact assessment uitgevoerd

### Security Compliance
- [ ] Logs encrypted at rest
- [ ] Metrics encrypted in transit
- [ ] Access control op dashboards
- [ ] Audit logging voor dashboard access
- [ ] Regular security reviews

## Operational Procedures

### Incident Response
1. Check correlation ID in error logs
2. Trace request flow via distributed tracing
3. Check metrics for anomalies
4. Review health check status
5. Check upstream/downstream services

### Performance Troubleshooting
1. Check P95 latency trends
2. Review cache hit ratios
3. Check batch size distributions
4. Review error rates per endpoint
5. Check resource utilization

## Tools & Endpoints

### Monitoring Endpoints
```
GET /health          # Health check
GET /metrics         # Prometheus metrics
GET /ready          # Readiness probe
GET /live           # Liveness probe
```

### Debugging Endpoints (Dev Only)
```
GET /debug/config    # Current configuration
GET /debug/flags     # Feature flag status
POST /debug/trace    # Enable trace logging
```

---

*Voor vragen over observability of privacy, contact het Security Team of Platform Team.*