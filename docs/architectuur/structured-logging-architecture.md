# Structured Logging Architecture Design

**Document Type:** Technical Architecture Design
**Created:** 2025-10-07
**Status:** Design Phase
**Author:** Claude (Architect Role)

## Executive Summary

This document proposes a structured logging architecture for DefinitieAgent that enables machine-readable logs for analytics, monitoring, and operational insights while maintaining backward compatibility with existing human-readable logs.

**Key Decision:** Use `python-json-logger` with gradual migration strategy.

---

## 1. Current Logging Infrastructure Analysis

### 1.1 Current State

**Logging Setup (src/main.py):**
```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

**Current Characteristics:**
- ✅ Basic Python `logging` module with simple string formatting
- ✅ PII redaction filter already implemented (`PIIRedactingFilter`)
- ✅ Logging configuration file exists (`config/logging_config.yaml`)
- ✅ JSON logging already used for specific purposes (security logs, API monitoring)
- ❌ No structured logging for application logs
- ❌ F-string interpolation throughout codebase (361 logging calls)
- ❌ Logs to console only (no file handlers configured in code)

**Logging Configuration (`config/logging_config.yaml`):**
- Comprehensive YAML config exists but **not currently loaded by application**
- Defines structured logging section (currently disabled)
- Includes module-specific levels, filters, performance tracking
- Environment-specific overrides (dev/prod/testing)

**Existing JSON Logging:**
- Security logs: `logs/security_log_*.json` (390 bytes each)
- API monitoring: `api_monitor.py` with JSON export capabilities
- NOT used for general application logging

### 1.2 Current Logging Patterns

**Most Common Pattern (361 files):**
```python
logger.info(f"ServiceContainer geïnitialiseerd (init count: {count})")
logger.error(f"Applicatie fout: {e!s}")
logger.warning(f"Search in {endpoint} failed: {e}")
```

**Observed Issues:**
1. **String interpolation happens before filtering** → Performance waste for disabled log levels
2. **No structured context** → Cannot query by `endpoint`, `count`, `error_type`
3. **Mixed languages** → Dutch business logic, English technical logs
4. **No correlation IDs** → Cannot trace requests across services

### 1.3 Performance Baseline

**Current Overhead:**
- String interpolation: Every log call evaluates f-strings immediately
- PIIRedactingFilter: Regex operations on every log message (acceptable overhead)
- No handlers configured → Only console output

**Bottlenecks:**
- ServiceContainer init: 2-3x initialization due to cache issues (logged extensively)
- PromptOrchestrator: 32x module registrations logged (2x orchestrators)
- Toetsregels loading: 53 rules × 2 = 106 log lines per startup

---

## 2. Library Comparison & Recommendation

### 2.1 Option Analysis

| Library | Pros | Cons | Verdict |
|---------|------|------|---------|
| **python-json-logger** | ✅ Drop-in replacement for Formatter<br>✅ Zero code changes for basic migration<br>✅ Works with existing handlers<br>✅ Lightweight (no dependencies) | ⚠️ Basic features only<br>⚠️ Manual context management | ✅ **RECOMMENDED** |
| **structlog** | ✅ Rich ecosystem<br>✅ Context binding<br>✅ Middleware/processors<br>✅ Best-in-class features | ❌ Requires code refactoring<br>❌ Learning curve<br>❌ Larger dependency | ❌ Overkill for current needs |
| **Custom Formatter** | ✅ Full control<br>✅ No dependencies | ❌ Maintenance burden<br>❌ Reinventing wheel | ❌ Not recommended |

### 2.2 Recommended Solution: python-json-logger

**Installation:**
```bash
pip install python-json-logger
```

**Justification:**
1. **Backward Compatible:** Works with existing `logging` infrastructure
2. **Minimal Changes:** No code refactoring required for basic JSON logging
3. **Proven:** Used in production by major organizations (4.5M+ downloads/month)
4. **Gradual Migration:** Can run alongside existing text logs
5. **No Lock-in:** Standard logging API, easy to switch later

---

## 3. Log Schema Design

### 3.1 Base Schema (Required Fields)

All structured logs will include these fields:

```json
{
  "timestamp": "2025-10-07T10:38:31.504Z",
  "level": "INFO",
  "logger": "services.container",
  "message": "ServiceContainer geïnitialiseerd",
  "module": "container",
  "function": "__init__",
  "line": 68,
  "thread": "MainThread",
  "process": 12345,
  "environment": "production"
}
```

**Field Definitions:**
- `timestamp`: ISO 8601 UTC timestamp
- `level`: Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- `logger`: Logger name (dot-separated namespace)
- `message`: Human-readable message (NO interpolation)
- `module`, `function`, `line`: Code location
- `thread`, `process`: Execution context
- `environment`: deployment environment (dev/prod/testing)

### 3.2 Context Fields (Optional)

Additional fields added via context managers or extra parameters:

```json
{
  "request_id": "req_abc123",
  "session_id": "sess_xyz789",
  "user_id": "user_123",
  "operation": "generate_definition",
  "component": "orchestrator",
  "duration_ms": 1234,
  "success": true
}
```

### 3.3 Service-Specific Fields

**ServiceContainer:**
```json
{
  "component": "service_container",
  "service_name": "orchestrator",
  "init_count": 1,
  "config_hash": "abc123"
}
```

**AI Service:**
```json
{
  "component": "ai_service",
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 500,
  "tokens_used": 234,
  "cost": 0.00234,
  "cached": false,
  "duration_ms": 1234
}
```

**Validation:**
```json
{
  "component": "validation",
  "rule_id": "ARAI-01",
  "rule_category": "ARAI",
  "validation_passed": true,
  "score": 0.85
}

**Web Lookup:**
```json
{
  "component": "web_lookup",
  "source": "wikipedia",
  "term": "burgerservicenummer",
  "results_count": 3,
  "api_type": "mediawiki",
  "cache_hit": false
}
```

**Performance Tracking:**
```json
{
  "component": "performance",
  "operation": "generate_definition",
  "duration_ms": 4567,
  "slow": true,
  "threshold_ms": 5000
}
```

### 3.4 Error Schema

```json
{
  "level": "ERROR",
  "message": "Applicatie fout",
  "error_type": "ValidationError",
  "error_message": "Definition too short",
  "stack_trace": "Traceback...",
  "component": "validation",
  "operation": "validate_definition",
  "request_id": "req_abc123"
}
```

---

## 4. Migration Strategy

### 4.1 Approach: Gradual Dual-Output

**Phase 1: Infrastructure (Week 1)**
- [ ] Add `python-json-logger` to `requirements.txt`
- [ ] Create structured logging module (`src/utils/structured_logging.py`)
- [ ] Update `config/logging_config.yaml` with JSON handlers
- [ ] Add environment detection (dev/prod/test)
- [ ] Test dual-output (console + JSON file)

**Phase 2: Core Services (Week 2-3)**
- [ ] Migrate `ServiceContainer` logging (highest value)
- [ ] Migrate `AIServiceV2` logging (cost tracking)
- [ ] Migrate `ValidationOrchestratorV2` logging (quality metrics)
- [ ] Add context managers for request tracking

**Phase 3: Supporting Services (Week 4-5)**
- [ ] Migrate web lookup services
- [ ] Migrate UI components
- [ ] Migrate utilities

**Phase 4: Optimization (Week 6)**
- [ ] Remove f-string interpolation (use lazy evaluation)
- [ ] Add correlation IDs
- [ ] Performance profiling
- [ ] Analytics dashboard

### 4.2 Backward Compatibility

**Human-Readable Console (Development):**
```
2025-10-07 10:38:31,504 - services.container - INFO - ServiceContainer geïnitialiseerd (init count: 1)
```

**JSON File (Production/Analytics):**
```json
{"timestamp": "2025-10-07T10:38:31.504Z", "level": "INFO", "logger": "services.container", "message": "ServiceContainer geïnitialiseerd", "init_count": 1}
```

**Configuration:**
```python
# Development: Human-readable console + JSON file
# Production: JSON only (both console and file)
# Testing: Minimal logging (JSON file only)
```

### 4.3 Code Migration Example

**Before:**
```python
logger.info(f"ServiceContainer geïnitialiseerd (init count: {self._initialization_count})")
```

**After (Lazy Evaluation):**
```python
# Option 1: Use extra parameter (RECOMMENDED)
logger.info("ServiceContainer geïnitialiseerd", extra={
    "init_count": self._initialization_count,
    "component": "service_container"
})

# Option 2: Use % formatting (lazy)
logger.info("ServiceContainer geïnitialiseerd (init count: %d)", self._initialization_count)
```

**Performance Benefit:**
- Before: F-string evaluated even if log level disabled
- After: Parameters only evaluated if log level enabled

---

## 5. Configuration Approach

### 5.1 Logging Configuration File

**Update `config/logging_config.yaml`:**

```yaml
structured:
  enabled: true  # Enable in production
  format: "json"
  file: "logs/definitie_agent_structured.jsonl"  # JSONL = newline-delimited JSON

  # Handlers
  handlers:
    console:
      enabled: true  # Human-readable in dev, JSON in prod
      format: "text"  # Override per environment

    file:
      enabled: true
      format: "json"
      rotation:
        max_bytes: 10485760  # 10 MB
        backup_count: 10

  # Base fields (always included)
  base_fields:
    - "timestamp"
    - "level"
    - "logger"
    - "message"
    - "module"
    - "function"
    - "line"
    - "thread"
    - "process"
    - "environment"

  # Context fields (opt-in per log call)
  context_fields:
    - "request_id"
    - "session_id"
    - "user_id"
    - "operation"
    - "component"
    - "duration_ms"

overrides:
  development:
    structured:
      enabled: true
      handlers:
        console:
          format: "text"  # Human-readable
        file:
          format: "json"  # Analytics

  production:
    structured:
      enabled: true
      handlers:
        console:
          format: "json"  # Machine-readable
        file:
          format: "json"

  testing:
    structured:
      enabled: true
      handlers:
        console:
          enabled: false
        file:
          format: "json"
```

### 5.2 Initialization Code

**Create `src/utils/structured_logging.py`:**

```python
"""
Structured logging setup for DefinitieAgent.

Provides JSON logging with context management and lazy evaluation.
"""

import logging
import os
from pathlib import Path
from typing import Any

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter with additional context.

    Adds environment, cleans up field names, and handles Dutch/English messages.
    """

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict):
        super().add_fields(log_record, record, message_dict)

        # Add environment
        log_record['environment'] = os.getenv('APP_ENV', 'development')

        # Rename fields for consistency
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['timestamp'] = self.formatTime(record, self.datefmt)

        # Add component if available (from extra)
        if hasattr(record, 'component'):
            log_record['component'] = record.component


def setup_structured_logging(config_path: str | None = None):
    """
    Setup structured logging based on configuration.

    Args:
        config_path: Path to logging_config.yaml (optional)
    """
    import yaml

    # Load configuration
    if config_path is None:
        config_path = "config/logging_config.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Get environment
    env = os.getenv('APP_ENV', 'development')
    overrides = config.get('overrides', {}).get(env, {})

    # Merge overrides
    structured_config = config.get('structured', {})
    structured_config.update(overrides.get('structured', {}))

    if not structured_config.get('enabled', False):
        return  # Structured logging disabled

    # Setup root logger
    root_logger = logging.getLogger()

    # Console handler
    console_config = structured_config.get('handlers', {}).get('console', {})
    if console_config.get('enabled', True):
        console_handler = logging.StreamHandler()

        if console_config.get('format') == 'json':
            formatter = CustomJsonFormatter(
                '%(timestamp)s %(level)s %(logger)s %(message)s'
            )
        else:
            # Human-readable format
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler (JSON)
    file_config = structured_config.get('handlers', {}).get('file', {})
    if file_config.get('enabled', True):
        from logging.handlers import RotatingFileHandler

        log_file = structured_config.get('file', 'logs/definitie_agent_structured.jsonl')
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=file_config.get('rotation', {}).get('max_bytes', 10485760),
            backupCount=file_config.get('rotation', {}).get('backup_count', 10),
            encoding='utf-8'
        )

        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(message)s'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


class LogContext:
    """
    Context manager for adding structured context to logs.

    Usage:
        with LogContext(request_id="req_123", operation="generate"):
            logger.info("Starting operation")
    """

    def __init__(self, **context: Any):
        self.context = context
        self.logger_class = logging.getLoggerClass()

    def __enter__(self):
        # Store original makeRecord
        self._original_makeRecord = self.logger_class.makeRecord

        # Patch makeRecord to add context
        def makeRecord_with_context(self_logger, *args, **kwargs):
            record = self._original_makeRecord(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        self.logger_class.makeRecord = makeRecord_with_context
        return self

    def __exit__(self, *args):
        # Restore original makeRecord
        self.logger_class.makeRecord = self._original_makeRecord


# Convenience functions
def log_with_context(logger: logging.Logger, level: str, message: str, **context):
    """
    Log a message with structured context.

    Args:
        logger: Logger instance
        level: Log level (info, debug, warning, error, critical)
        message: Log message
        **context: Additional context fields
    """
    log_func = getattr(logger, level.lower())
    log_func(message, extra=context)
```

### 5.3 Integration in main.py

**Update `src/main.py`:**

```python
import logging
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st

from ui.session_state import SessionStateManager
from ui.tabbed_interface import TabbedInterface
from utils.exceptions import log_and_display_error

# NEW: Setup structured logging
from utils.structured_logging import setup_structured_logging

# Setup structured logging BEFORE basicConfig
try:
    setup_structured_logging()
except Exception as e:
    # Fallback to basic logging if structured logging fails
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.warning(f"Failed to setup structured logging: {e}")

# Add PII filter (still needed)
try:
    from utils.logging_filters import PIIRedactingFilter
    _root = logging.getLogger()
    if not any(isinstance(f, PIIRedactingFilter) for f in _root.filters):
        _root.addFilter(PIIRedactingFilter())
except Exception:
    pass

logger = logging.getLogger(__name__)

# ... rest of main.py unchanged
```

---

## 6. Analytics Use Cases

### 6.1 Queries Enabled by Structured Logging

**Example 1: ServiceContainer Initialization Analysis**
```bash
# Query: How many times is ServiceContainer initialized per session?
jq 'select(.component == "service_container" and .message | contains("geïnitialiseerd")) | {timestamp, init_count}' \
  logs/definitie_agent_structured.jsonl
```

**Example 2: AI Service Cost Tracking**
```bash
# Query: Total API cost in last 24 hours
jq -s 'map(select(.component == "ai_service" and .cost)) | map(.cost) | add' \
  logs/definitie_agent_structured.jsonl
```

**Example 3: Slow Operations**
```bash
# Query: All operations slower than 5 seconds
jq 'select(.duration_ms > 5000) | {timestamp, operation, duration_ms, component}' \
  logs/definitie_agent_structured.jsonl
```

**Example 4: Validation Rule Failures**
```bash
# Query: Most common failing validation rules
jq -s 'map(select(.component == "validation" and .validation_passed == false)) |
  group_by(.rule_id) | map({rule: .[0].rule_id, count: length}) |
  sort_by(-.count)' \
  logs/definitie_agent_structured.jsonl
```

**Example 5: Error Rate by Component**
```bash
# Query: Error rate per component
jq -s 'map(select(.level == "ERROR")) | group_by(.component) |
  map({component: .[0].component, errors: length})' \
  logs/definitie_agent_structured.jsonl
```

### 6.2 Integration with Analytics Tools

**Option 1: Local Analysis (jq + Python)**
- Use `jq` for quick CLI queries
- Python scripts for complex analytics
- Generate reports with pandas/matplotlib

**Option 2: Elasticsearch/Kibana (Future)**
- Ship logs to Elasticsearch
- Visualize in Kibana dashboards
- Set up alerts for critical metrics

**Option 3: Grafana Loki (Lightweight)**
- Log aggregation without full ELK stack
- Time-series queries
- Cost-effective for small deployments

---

## 7. Implementation Complexity Estimate

### 7.1 Effort Breakdown

| Phase | Tasks | Estimated Effort | Complexity |
|-------|-------|------------------|------------|
| **Phase 1: Infrastructure** | - Add dependency<br>- Create structured_logging.py<br>- Update config<br>- Test dual-output | 4-6 hours | Low |
| **Phase 2: Core Services** | - Migrate 3 core services<br>- Add context managers<br>- Update tests | 12-16 hours | Medium |
| **Phase 3: Supporting Services** | - Migrate 10+ services<br>- Update UI components | 16-24 hours | Medium |
| **Phase 4: Optimization** | - Remove f-strings<br>- Add correlation IDs<br>- Performance profiling | 8-12 hours | Low-Medium |
| **Total** | | **40-58 hours** | **Medium** |

### 7.2 Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Performance degradation | High | Low | Benchmark before/after, optimize if needed |
| Log volume explosion | Medium | Medium | Enable sampling in production, monitor disk usage |
| Breaking existing log parsing | Low | Low | Gradual migration, test thoroughly |
| Missing context in logs | Medium | Medium | Add context incrementally, document patterns |

### 7.3 Success Criteria

- [ ] Zero performance degradation (< 5% overhead)
- [ ] 100% backward compatibility (existing logs still work)
- [ ] Core services (Container, AI, Validation) migrated
- [ ] Analytics queries functional (5+ example queries work)
- [ ] Documentation complete (migration guide + examples)

---

## 8. Performance Impact Analysis

### 8.1 Expected Overhead

**JSON Serialization:**
- Overhead: ~10-50 microseconds per log call
- Acceptable for INFO+ levels
- Use lazy evaluation for DEBUG level

**File I/O:**
- Async handlers can buffer writes
- Rotating file handler is efficient
- Compression reduces disk usage by ~5-10x

**Memory:**
- JSON formatter: Negligible (< 1 MB)
- Log buffers: Configurable (default 100 records)

### 8.2 Optimization Strategies

**1. Lazy Evaluation**
```python
# Bad (always evaluates f-string)
logger.debug(f"Processing {len(items)} items: {items}")

# Good (only evaluates if DEBUG enabled)
logger.debug("Processing %d items: %s", len(items), items)
```

**2. Sampling**
```yaml
sampling:
  enabled: true
  levels:
    DEBUG: 0.01  # Log 1% of DEBUG messages
    INFO: 0.1    # Log 10% of INFO messages
    WARNING: 1.0  # Log 100% of WARNING+ messages
```

**3. Async Handlers**
```python
from logging.handlers import QueueHandler, QueueListener

# Offload logging to background thread
queue_handler = QueueHandler(queue)
queue_listener = QueueListener(queue, file_handler)
```

### 8.3 Benchmark Results (Estimated)

| Operation | Before (f-string) | After (lazy %) | After (JSON extra) |
|-----------|-------------------|----------------|---------------------|
| Log call (disabled) | ~1 µs | ~0.1 µs | ~0.1 µs |
| Log call (enabled) | ~50 µs | ~60 µs | ~100 µs |
| Throughput | 20k logs/s | 18k logs/s | 10k logs/s |

**Conclusion:** JSON structured logging adds ~2x overhead, but this is acceptable for INFO+ levels. Use sampling for high-frequency DEBUG logs.

---

## 9. Integration with Existing Monitoring

### 9.1 Current Monitoring (api_monitor.py)

**Already Implemented:**
- API call tracking with JSON export
- Cost calculation
- Performance metrics (response time, throughput)
- Alert system (MetricSnapshot, AlertSeverity)

**Integration Points:**
1. **Unified Logging:** api_monitor logs should use structured logging
2. **Correlation:** Add `request_id` to link API calls with application logs
3. **Aggregation:** Combine API metrics with service logs for full picture

### 9.2 Monitoring Dashboard (Future)

**Metrics to Track:**
1. **Service Health:**
   - Container initialization count (should be 1x)
   - Service creation rate
   - Error rate per component

2. **Performance:**
   - Operation duration (p50, p95, p99)
   - Slow operations (> threshold)
   - Cache hit rate

3. **Cost:**
   - API cost per hour/day
   - Token usage per operation
   - Cost per definition generated

4. **Quality:**
   - Validation rule pass/fail rates
   - Definition quality scores
   - Manual intervention rate

**Visualization:**
- Grafana dashboards (if Loki integrated)
- Python scripts with matplotlib
- Simple web UI with Flask/Streamlit

---

## 10. Example Before/After Logs

### 10.1 ServiceContainer Initialization

**Before (Current):**
```
2025-10-07 10:38:31,504 - services.container - INFO - ServiceContainer geïnitialiseerd (init count: 1)
```

**After (Structured):**
```json
{
  "timestamp": "2025-10-07T10:38:31.504Z",
  "level": "INFO",
  "logger": "services.container",
  "message": "ServiceContainer geïnitialiseerd",
  "component": "service_container",
  "init_count": 1,
  "config_hash": "abc123def456",
  "environment": "production",
  "module": "container",
  "function": "__init__",
  "line": 68
}
```

### 10.2 AI Service Call

**Before:**
```
2025-10-07 10:40:15,234 - services.ai_service_v2 - DEBUG - Cache hit for prompt: Generate a definition for...
```

**After:**
```json
{
  "timestamp": "2025-10-07T10:40:15.234Z",
  "level": "DEBUG",
  "logger": "services.ai_service_v2",
  "message": "Cache hit for prompt",
  "component": "ai_service",
  "operation": "generate_definition",
  "model": "gpt-4o-mini",
  "prompt_length": 1234,
  "cached": true,
  "cache_key": "prompt_abc123",
  "duration_ms": 5,
  "request_id": "req_xyz789"
}
```

### 10.3 Validation Error

**Before:**
```
2025-10-07 10:42:30,567 - services.validation - WARNING - Validation rule ARAI-01 failed for definition
```

**After:**
```json
{
  "timestamp": "2025-10-07T10:42:30.567Z",
  "level": "WARNING",
  "logger": "services.validation",
  "message": "Validation rule failed",
  "component": "validation",
  "operation": "validate_definition",
  "rule_id": "ARAI-01",
  "rule_category": "ARAI",
  "rule_name": "Afgebakend begrip",
  "validation_passed": false,
  "score": 0.45,
  "threshold": 0.7,
  "definition_id": 123,
  "term": "burgerservicenummer",
  "request_id": "req_xyz789"
}
```

### 10.4 Web Lookup Operation

**Before:**
```
2025-10-07 10:45:12,890 - services.modern_web_lookup_service - INFO - Starting lookup for term: burgerservicenummer
2025-10-07 10:45:13,234 - services.web_lookup.wikipedia_service - INFO - Wikipedia lookup voor term: burgerservicenummer
2025-10-07 10:45:14,123 - services.modern_web_lookup_service - WARNING - Source lookup failed: {'source': 'sru', 'error': 'timeout'}
```

**After:**
```json
{
  "timestamp": "2025-10-07T10:45:12.890Z",
  "level": "INFO",
  "logger": "services.modern_web_lookup_service",
  "message": "Starting web lookup",
  "component": "web_lookup",
  "operation": "lookup_term",
  "term": "burgerservicenummer",
  "sources": ["wikipedia", "sru"],
  "request_id": "req_abc123"
}
{
  "timestamp": "2025-10-07T10:45:13.234Z",
  "level": "INFO",
  "logger": "services.web_lookup.wikipedia_service",
  "message": "Wikipedia lookup started",
  "component": "web_lookup",
  "operation": "wikipedia_lookup",
  "source": "wikipedia",
  "api_type": "mediawiki",
  "term": "burgerservicenummer",
  "request_id": "req_abc123"
}
{
  "timestamp": "2025-10-07T10:45:14.123Z",
  "level": "WARNING",
  "logger": "services.modern_web_lookup_service",
  "message": "Source lookup failed",
  "component": "web_lookup",
  "operation": "lookup_term",
  "source": "sru",
  "error_type": "TimeoutError",
  "error_message": "Request timeout after 5s",
  "duration_ms": 5000,
  "request_id": "req_abc123"
}
```

---

## 11. Migration Checklist

### Phase 1: Infrastructure Setup
- [ ] Add `python-json-logger==2.0.7` to `requirements.txt`
- [ ] Create `src/utils/structured_logging.py`
- [ ] Update `src/main.py` to call `setup_structured_logging()`
- [ ] Test console output (dev environment)
- [ ] Test JSON file output (`logs/definitie_agent_structured.jsonl`)
- [ ] Verify PII redaction still works
- [ ] Document configuration options

### Phase 2: Core Services Migration
- [ ] **ServiceContainer** (`src/services/container.py`)
  - [ ] Migrate `__init__` logging
  - [ ] Add `component="service_container"` to all logs
  - [ ] Add `service_name` to service factory logs
  - [ ] Add `config_hash` to initialization logs
- [ ] **AIServiceV2** (`src/services/ai_service_v2.py`)
  - [ ] Migrate `generate_definition` logging
  - [ ] Add structured fields: `model`, `temperature`, `tokens_used`, `cost`, `cached`
  - [ ] Add `request_id` context manager
  - [ ] Track cache hit/miss rates
- [ ] **ValidationOrchestratorV2** (`src/services/orchestrators/validation_orchestrator_v2.py`)
  - [ ] Migrate validation result logging
  - [ ] Add structured fields: `rule_id`, `rule_category`, `score`, `passed`
  - [ ] Track validation metrics

### Phase 3: Supporting Services
- [ ] **ModernWebLookupService** (`src/services/modern_web_lookup_service.py`)
- [ ] **DefinitionRepository** (`src/services/definition_repository.py`)
- [ ] **CleaningService** (`src/services/cleaning_service.py`)
- [ ] **WorkflowService** (`src/services/workflow_service.py`)
- [ ] **UI Components** (`src/ui/components/`)

### Phase 4: Optimization
- [ ] Replace f-strings with lazy evaluation (priority: hot paths)
- [ ] Add correlation ID middleware
- [ ] Performance profiling (before/after comparison)
- [ ] Create analytics queries documentation
- [ ] Set up log rotation and archival
- [ ] Create monitoring dashboard (optional)

### Phase 5: Documentation
- [ ] Update `CLAUDE.md` with structured logging guidelines
- [ ] Create migration guide for developers
- [ ] Document log schema and fields
- [ ] Create analytics query examples
- [ ] Update troubleshooting guide

---

## 12. Recommendations

### 12.1 Immediate Actions (Week 1)
1. **Install python-json-logger:** Add to requirements and test
2. **Create infrastructure:** Implement `structured_logging.py`
3. **Test dual output:** Verify console + JSON file work together
4. **Migrate ServiceContainer:** Highest value, easy win

### 12.2 Short-Term (Weeks 2-4)
1. **Migrate AI Service:** Critical for cost tracking
2. **Migrate Validation:** Important for quality metrics
3. **Add correlation IDs:** Essential for request tracing
4. **Create analytics queries:** Demonstrate value

### 12.3 Long-Term (Months 1-3)
1. **Complete migration:** All services use structured logging
2. **Optimize performance:** Remove f-strings, add sampling
3. **Build dashboard:** Visualize key metrics
4. **Integrate with monitoring:** Elasticsearch/Loki/Grafana (optional)

### 12.4 Best Practices

**DO:**
- ✅ Use `extra` parameter for structured context
- ✅ Add `component` field to all logs
- ✅ Use ISO 8601 timestamps (UTC)
- ✅ Include `request_id` for tracing
- ✅ Log durations in milliseconds
- ✅ Use lazy evaluation (`%s` formatting)

**DON'T:**
- ❌ Use f-strings for logging
- ❌ Log sensitive data (PII, API keys)
- ❌ Log at DEBUG level in production (without sampling)
- ❌ Create deeply nested JSON (keep flat)
- ❌ Mix Dutch and English in same log message
- ❌ Log raw exception objects (serialize first)

---

## 13. Conclusion

### Summary

This architecture provides a **pragmatic, low-risk path** to structured logging for DefinitieAgent:

1. **Library:** `python-json-logger` (drop-in replacement, zero refactoring)
2. **Strategy:** Gradual migration with dual output (console + JSON)
3. **Schema:** Standardized fields with component-specific extensions
4. **Migration:** 4 phases over 6 weeks, ~40-58 hours effort
5. **Value:** Enables analytics, monitoring, and operational insights

### Next Steps

1. **Review this design** with stakeholders
2. **Approve Phase 1** infrastructure changes
3. **Create Epic/User Stories** for implementation
4. **Start with ServiceContainer** migration (quick win)
5. **Iterate based on feedback** and metrics

### Success Metrics

- **Performance:** < 5% overhead
- **Coverage:** 80%+ of logs structured within 6 weeks
- **Analytics:** 5+ working queries demonstrating value
- **Quality:** Zero regressions in existing functionality

---

## Appendices

### A. Dependencies

```txt
# requirements.txt
python-json-logger==2.0.7  # BSD License, 4.5M+ downloads/month
PyYAML==6.0.1  # Already in requirements
```

### B. Configuration Files

**Location:** `config/logging_config.yaml`
**Status:** Exists but not loaded
**Action:** Update structured logging section, load in main.py

### C. Related Documents

- `config/logging_config.yaml` - Logging configuration (exists)
- `src/utils/logging_filters.py` - PII redaction filter (exists)
- `src/monitoring/api_monitor.py` - API monitoring (exists)
- `CLAUDE.md` - Project guidelines (update with logging standards)

### D. External Resources

- [python-json-logger Documentation](https://github.com/madzak/python-json-logger)
- [Python logging best practices](https://docs.python.org/3/howto/logging.html)
- [Structured logging guidelines](https://www.structlog.org/en/stable/why.html)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-07
**Next Review:** After Phase 1 completion
