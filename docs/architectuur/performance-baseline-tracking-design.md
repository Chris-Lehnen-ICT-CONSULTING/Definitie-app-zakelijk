# Performance Baseline Tracking System - Architectural Design

**Document Type:** Technical Design Document
**Date:** 2025-10-07
**Author:** Claude Code (Architecture Agent)
**Status:** DESIGN PHASE
**Related:** CLAUDE.md Performance Goals, Container Performance Issues (US-201, US-202)

---

## Executive Summary

**Problem:** Application startup takes ~400ms with known performance issues (double container init, prompt duplication), but there's no automated system to:
- Track performance baselines over time
- Detect regressions automatically
- Identify which operations are slowing down
- Compare performance across code changes

**Solution:** Implement a lightweight, automated performance baseline tracking system that:
- Records key metrics on every app start (<10ms overhead)
- Stores baselines in SQLite for historical trending
- Alerts on regressions (>10% slower than baseline)
- Integrates with existing monitoring infrastructure
- Provides visualization via UI dashboard

**Expected Impact:**
- ⚡ Catch performance regressions before they reach production
- 📊 Data-driven optimization decisions
- 🎯 Clear performance accountability per feature
- 💰 Reduced API costs through early detection of token bloat

---

## 1. Metrics to Track

### 1.1 Core Metrics (Priority: HIGH)

Based on CLAUDE.md performance goals and existing issues:

| Metric ID | Name | Target | Current | Source |
|-----------|------|--------|---------|--------|
| **APP-001** | Application Startup Time | <500ms | ~400ms | main.py → interface.render() |
| **SVC-001** | ServiceContainer Init | 1x only | 2-3x (KNOWN ISSUE) | container.py __init__ |
| **SVC-002** | Service Init Time | <200ms | ~300ms | All service __init__ |
| **VAL-001** | Single Validation Time | <1s | ~1s | ValidationOrchestrator.validate() |
| **VAL-002** | Rule Loading Time | <100ms | ~200ms | load_toetsregels() |
| **VAL-003** | Rule Cache Hit Rate | >90% | ~85% | RuleCache stats |
| **GEN-001** | Definition Generation Time | <5s | ~4s | DefinitionOrchestrator.generate() |
| **API-001** | API Call Duration | <3s | ~2-4s | AIServiceV2.call() |
| **API-002** | Prompt Token Count | <3000 | ~7250 (KNOWN ISSUE) | PromptServiceV2 output |
| **API-003** | API Cost per Request | <$0.01 | ~$0.02 | CostCalculator |
| **EXP-001** | Export Operation Time | <2s | ~1.5s | ExportService.export() |
| **MEM-001** | Peak Memory Usage | <500MB | ~350MB | psutil.Process |
| **MEM-002** | Memory Growth Rate | <10MB/hour | Unknown | psutil delta |

### 1.2 Secondary Metrics (Priority: MEDIUM)

| Metric ID | Name | Target | Source |
|-----------|------|--------|--------|
| **CACHE-001** | Container Cache Hit Rate | 100% | get_cached_container() |
| **CACHE-002** | Prompt Cache Hit Rate | >80% | PromptService cache stats |
| **CACHE-003** | Definition Cache Hit Rate | >70% | DefinitionCache stats |
| **DB-001** | Database Query Time | <50ms | Repository query timing |
| **DB-002** | Database Connection Pool | <10 active | Connection stats |
| **WEB-001** | Web Lookup Time | <2s | ModernWebLookupService |
| **UI-001** | Tab Switch Time | <100ms | UI state transitions |
| **UFO-001** | UFO Classification Time | <500ms | UFOClassifierService |

### 1.3 Derived Metrics (Calculated)

- **Throughput:** Definitions per hour = 3600 / AVG(GEN-001)
- **Cost Efficiency:** Cost per definition = API-003
- **Performance Index:** Composite score based on all metrics vs targets
- **Regression Score:** % deviation from baseline (negative = regression)

---

## 2. Data Model for Storing Metrics

### 2.1 Database Schema

**Table: `performance_baselines`**

```sql
CREATE TABLE performance_baselines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Metadata
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT NOT NULL,          -- Unique session identifier
    git_commit TEXT,                    -- Git SHA if available
    app_version TEXT,                   -- Application version
    environment TEXT DEFAULT 'local',   -- local/test/prod

    -- System Context
    python_version TEXT,
    platform TEXT,                      -- darwin/linux/windows
    cpu_count INTEGER,
    total_memory_mb INTEGER,

    -- Core Performance Metrics (milliseconds)
    startup_time_ms REAL,               -- APP-001
    container_init_count INTEGER,       -- SVC-001 (should be 1)
    container_init_time_ms REAL,        -- SVC-002
    service_init_time_ms REAL,          -- SVC-002
    validation_time_ms REAL,            -- VAL-001
    rule_loading_time_ms REAL,          -- VAL-002
    generation_time_ms REAL,            -- GEN-001
    api_call_time_ms REAL,              -- API-001
    export_time_ms REAL,                -- EXP-001

    -- API Metrics
    prompt_token_count INTEGER,         -- API-002
    api_cost_cents REAL,                -- API-003 (in cents)

    -- Memory Metrics (MB)
    peak_memory_mb REAL,                -- MEM-001
    memory_growth_mb REAL,              -- MEM-002

    -- Cache Metrics (percentages 0-1)
    container_cache_hit_rate REAL,      -- CACHE-001
    rule_cache_hit_rate REAL,           -- VAL-003
    prompt_cache_hit_rate REAL,         -- CACHE-002
    definition_cache_hit_rate REAL,     -- CACHE-003

    -- Derived Metrics
    performance_index REAL,             -- Composite score
    regression_score REAL,              -- % from baseline

    -- Issue Flags
    has_double_container BOOLEAN DEFAULT 0,
    has_prompt_duplication BOOLEAN DEFAULT 0,
    has_rule_reload_issue BOOLEAN DEFAULT 0,

    -- Additional Context (JSON)
    operation_breakdown TEXT,           -- JSON: detailed timing breakdown
    cache_stats TEXT,                   -- JSON: cache hit/miss details
    error_details TEXT,                 -- JSON: any errors during measurement
    notes TEXT                          -- Human notes
);

-- Indexes for common queries
CREATE INDEX idx_baselines_timestamp ON performance_baselines(timestamp);
CREATE INDEX idx_baselines_session ON performance_baselines(session_id);
CREATE INDEX idx_baselines_commit ON performance_baselines(git_commit);
CREATE INDEX idx_baselines_environment ON performance_baselines(environment);
CREATE INDEX idx_baselines_regression ON performance_baselines(regression_score);
```

**Table: `performance_alerts`**

```sql
CREATE TABLE performance_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Alert Metadata
    triggered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    baseline_id INTEGER REFERENCES performance_baselines(id),
    alert_type TEXT NOT NULL,           -- 'regression', 'threshold', 'anomaly'
    severity TEXT NOT NULL,             -- 'info', 'warning', 'error', 'critical'

    -- Alert Details
    metric_id TEXT NOT NULL,            -- e.g., 'APP-001', 'API-002'
    metric_name TEXT NOT NULL,
    current_value REAL NOT NULL,
    expected_value REAL NOT NULL,
    deviation_percent REAL NOT NULL,

    -- Context
    threshold_breached TEXT,            -- Description of threshold
    baseline_reference_id INTEGER REFERENCES performance_baselines(id),

    -- Resolution
    acknowledged BOOLEAN DEFAULT 0,
    acknowledged_by TEXT,
    acknowledged_at TIMESTAMP,
    resolution_notes TEXT,

    -- Additional Data
    context_json TEXT                   -- JSON: additional context
);

CREATE INDEX idx_alerts_triggered ON performance_alerts(triggered_at);
CREATE INDEX idx_alerts_severity ON performance_alerts(severity);
CREATE INDEX idx_alerts_acknowledged ON performance_alerts(acknowledged);
```

**Table: `performance_targets`**

```sql
CREATE TABLE performance_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Target Definition
    metric_id TEXT NOT NULL UNIQUE,     -- e.g., 'APP-001'
    metric_name TEXT NOT NULL,
    target_value REAL NOT NULL,
    unit TEXT NOT NULL,                 -- 'ms', 'tokens', 'MB', 'percent'

    -- Thresholds
    warning_threshold REAL,             -- Warn if exceeds this (e.g., +10%)
    error_threshold REAL,               -- Error if exceeds this (e.g., +20%)

    -- Metadata
    description TEXT,
    source TEXT,                        -- 'CLAUDE.md', 'manual', 'calculated'
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT,
    active BOOLEAN DEFAULT 1
);

-- Seed with targets from CLAUDE.md
INSERT INTO performance_targets (metric_id, metric_name, target_value, unit, warning_threshold, error_threshold, description, source) VALUES
('APP-001', 'Application Startup Time', 500, 'ms', 550, 600, 'Main app initialization', 'CLAUDE.md'),
('SVC-001', 'ServiceContainer Init Count', 1, 'count', 2, 3, 'Should be singleton', 'Known Issue'),
('VAL-001', 'Single Validation Time', 1000, 'ms', 1100, 1200, 'Definition validation', 'CLAUDE.md'),
('GEN-001', 'Definition Generation Time', 5000, 'ms', 5500, 6000, 'Full generation flow', 'CLAUDE.md'),
('API-002', 'Prompt Token Count', 3000, 'tokens', 3500, 4000, 'Prompt optimization', 'Known Issue'),
('EXP-001', 'Export Operation Time', 2000, 'ms', 2200, 2500, 'Export to file', 'CLAUDE.md'),
('MEM-001', 'Peak Memory Usage', 500, 'MB', 550, 600, 'Max memory usage', 'Estimated'),
('UI-001', 'UI Response Time', 200, 'ms', 250, 300, 'UI interaction lag', 'CLAUDE.md');
```

---

## 3. Baseline Calculation Strategy

### 3.1 Baseline Definition

**Baseline:** The "normal" expected performance, calculated as the **median** of the last N successful runs (N=20 by default).

**Why Median?**
- More robust to outliers than mean
- Reflects "typical" performance, not average
- Less sensitive to occasional slow runs (GC, background tasks)

**Alternatives Considered:**
- **Mean:** Too sensitive to outliers (rejected)
- **95th Percentile:** Too pessimistic for baseline (use for SLA instead)
- **Min:** Too optimistic, ignores real-world variance (rejected)

### 3.2 Baseline Update Strategy

**Rolling Window Approach:**

```python
def calculate_baseline(metric_id: str, window_size: int = 20) -> dict:
    """
    Calculate baseline from last N successful measurements.

    Returns:
        {
            'median': float,        # Baseline value
            'p5': float,           # 5th percentile (best case)
            'p95': float,          # 95th percentile (worst case)
            'std_dev': float,      # Standard deviation
            'sample_size': int,    # How many samples used
            'confidence': float    # Confidence in baseline (0-1)
        }
    """
    # Query last N measurements
    measurements = query_recent_measurements(metric_id, limit=window_size)

    # Remove outliers (>3 std dev from mean)
    cleaned = remove_outliers(measurements)

    # Calculate statistics
    return {
        'median': np.median(cleaned),
        'p5': np.percentile(cleaned, 5),
        'p95': np.percentile(cleaned, 95),
        'std_dev': np.std(cleaned),
        'sample_size': len(cleaned),
        'confidence': min(1.0, len(cleaned) / window_size)
    }
```

**Confidence Score:**
- 0.0-0.3: Low confidence (< 6 samples) - don't alert yet
- 0.3-0.7: Medium confidence (6-14 samples) - warn only
- 0.7-1.0: High confidence (14+ samples) - full alerting

**Baseline Recalculation:**
- **Trigger:** Every 10 new measurements
- **Window:** Last 20 measurements (configurable)
- **Exclusions:** Failed runs, incomplete data, known anomalies

### 3.3 Cold Start Handling

**Problem:** First 5-10 runs are slower (cache warming, JIT compilation, etc.)

**Solution:** Separate "cold start" and "warm" baselines:

```sql
-- Add column to baselines table
ALTER TABLE performance_baselines ADD COLUMN is_cold_start BOOLEAN DEFAULT 0;

-- Mark cold starts
UPDATE performance_baselines
SET is_cold_start = 1
WHERE session_id IN (
    SELECT DISTINCT session_id
    FROM performance_baselines
    WHERE timestamp > datetime('now', '-1 hour')
    LIMIT 3  -- First 3 sessions per hour
);
```

**Baseline Calculation:** Use only "warm" runs for baseline, track cold starts separately.

---

## 4. Regression Detection Algorithm

### 4.1 Three-Tier Detection

**Tier 1: Threshold-Based (Simple)**

```python
def check_threshold_breach(current: float, target: float, thresholds: dict) -> str:
    """
    Check if current value breaches warning/error thresholds.

    Returns: 'ok', 'warning', 'error', 'critical'
    """
    deviation_pct = ((current - target) / target) * 100

    if deviation_pct > thresholds['error']:
        return 'critical' if deviation_pct > thresholds['error'] * 1.5 else 'error'
    elif deviation_pct > thresholds['warning']:
        return 'warning'
    else:
        return 'ok'
```

**Tier 2: Statistical (Baseline Comparison)**

```python
def check_regression(current: float, baseline: dict) -> dict:
    """
    Compare current value against baseline statistics.

    Returns:
        {
            'is_regression': bool,
            'severity': str,
            'z_score': float,
            'percentile': float
        }
    """
    # Calculate z-score (how many std devs from median)
    z_score = (current - baseline['median']) / baseline['std_dev']

    # Classify severity
    if z_score > 3:  # > 3 std devs = very unusual
        severity = 'critical'
    elif z_score > 2:  # > 2 std devs = unusual
        severity = 'error'
    elif z_score > 1:  # > 1 std dev = notable
        severity = 'warning'
    else:
        severity = 'ok'

    return {
        'is_regression': z_score > 1,
        'severity': severity,
        'z_score': z_score,
        'percentile': calculate_percentile(current, baseline)
    }
```

**Tier 3: Trend Analysis (Historical)**

```python
def detect_trend_regression(metric_id: str, window_hours: int = 24) -> dict:
    """
    Detect if metric is trending worse over time.

    Uses linear regression to detect upward/downward trends.
    """
    # Get last N hours of data
    timeseries = query_metric_timeseries(metric_id, hours=window_hours)

    # Perform linear regression
    slope, intercept, r_value = linear_regression(timeseries)

    # Classify trend
    if slope > 0.05:  # Positive slope = getting worse
        if r_value > 0.8:  # Strong correlation
            severity = 'error'
        else:
            severity = 'warning'
    else:
        severity = 'ok'

    return {
        'has_trend_regression': slope > 0.05 and r_value > 0.6,
        'severity': severity,
        'slope': slope,
        'r_squared': r_value ** 2,
        'projected_24h': intercept + slope * 24
    }
```

### 4.2 Combined Decision Logic

```python
def evaluate_performance(current_metrics: dict) -> dict:
    """
    Combine all detection tiers into final decision.
    """
    alerts = []

    for metric_id, current_value in current_metrics.items():
        # Get target and baseline
        target = get_target(metric_id)
        baseline = calculate_baseline(metric_id)

        # Tier 1: Threshold check
        threshold_result = check_threshold_breach(current_value, target['value'], target)

        # Tier 2: Statistical check
        regression_result = check_regression(current_value, baseline)

        # Tier 3: Trend check (only if baseline exists)
        trend_result = detect_trend_regression(metric_id) if baseline['confidence'] > 0.5 else None

        # Combine results (worst severity wins)
        final_severity = max(
            threshold_result,
            regression_result['severity'],
            trend_result['severity'] if trend_result else 'ok',
            key=lambda s: ['ok', 'warning', 'error', 'critical'].index(s)
        )

        if final_severity != 'ok':
            alerts.append({
                'metric_id': metric_id,
                'severity': final_severity,
                'current': current_value,
                'baseline': baseline['median'],
                'target': target['value'],
                'threshold_status': threshold_result,
                'regression_status': regression_result,
                'trend_status': trend_result
            })

    return alerts
```

---

## 5. Code Instrumentation (Where to Measure)

### 5.1 Instrumentation Points

**A. Application Startup (main.py)**

```python
# src/main.py
from monitoring.performance_tracker import PerformanceTracker

def main():
    tracker = PerformanceTracker()
    tracker.start_operation('app_startup')

    try:
        # Existing startup code
        SessionStateManager.initialize_session_state()
        interface = TabbedInterface()
        interface.render()

        # Record startup success
        tracker.stop_operation('app_startup')
        tracker.record_baseline_snapshot()

    except Exception as e:
        tracker.stop_operation('app_startup', error=e)
        raise
```

**B. ServiceContainer (container.py)**

```python
# src/services/container.py
class ServiceContainer:
    _init_count = 0  # Class variable to track initialization count

    def __init__(self, config=None):
        # Track initialization
        ServiceContainer._init_count += 1

        tracker = PerformanceTracker.get_instance()
        tracker.record_metric('container_init_count', ServiceContainer._init_count)
        tracker.start_operation('container_init')

        try:
            # Existing initialization code
            self._initialize_services(config)

            tracker.stop_operation('container_init')
        except Exception as e:
            tracker.stop_operation('container_init', error=e)
            raise
```

**C. Validation Orchestrator**

```python
# src/services/validation/validation_orchestrator_v2.py
class ValidationOrchestratorV2:
    async def validate(self, definition: str) -> dict:
        tracker = PerformanceTracker.get_instance()
        tracker.start_operation('validation')

        try:
            result = await self._perform_validation(definition)
            tracker.stop_operation('validation')
            return result
        except Exception as e:
            tracker.stop_operation('validation', error=e)
            raise
```

**D. Definition Generator**

```python
# src/services/orchestrators/definition_orchestrator_v2.py
class DefinitionOrchestratorV2:
    async def generate_definition(self, term: str) -> dict:
        tracker = PerformanceTracker.get_instance()
        tracker.start_operation('generation')

        try:
            result = await self._generate(term)

            # Record API metrics
            tracker.record_metric('prompt_token_count', result['token_count'])
            tracker.record_metric('api_cost_cents', result['cost'] * 100)

            tracker.stop_operation('generation')
            return result
        except Exception as e:
            tracker.stop_operation('generation', error=e)
            raise
```

**E. Rule Cache**

```python
# src/toetsregels/rule_cache.py
class RuleCache:
    def get_cached_toetsregel_manager(self):
        tracker = PerformanceTracker.get_instance()
        tracker.start_operation('rule_loading')

        result = self._get_or_load()

        # Record cache stats
        stats = self.get_stats()
        tracker.record_metric('rule_cache_hit_rate', stats['hit_rate'])

        tracker.stop_operation('rule_loading')
        return result
```

### 5.2 Decorator-Based Instrumentation

**For clean, reusable instrumentation:**

```python
# src/monitoring/decorators.py
from functools import wraps
import asyncio

def measure_performance(operation_name: str, metric_id: str = None):
    """
    Decorator to automatically measure function performance.

    Usage:
        @measure_performance('validation', 'VAL-001')
        async def validate(self, definition):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracker = PerformanceTracker.get_instance()
            tracker.start_operation(operation_name)

            try:
                result = await func(*args, **kwargs)
                tracker.stop_operation(operation_name)
                return result
            except Exception as e:
                tracker.stop_operation(operation_name, error=e)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracker = PerformanceTracker.get_instance()
            tracker.start_operation(operation_name)

            try:
                result = func(*args, **kwargs)
                tracker.stop_operation(operation_name)
                return result
            except Exception as e:
                tracker.stop_operation(operation_name, error=e)
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
```

**Example Usage:**

```python
class ValidationService:
    @measure_performance('validation', 'VAL-001')
    async def validate_definition(self, text: str) -> dict:
        # Implementation
        pass
```

---

## 6. Storage Strategy

### 6.1 Database Integration

**Use existing SQLite database:** `/Users/chrislehnen/Projecten/Definitie-app/data/definities.db`

**Migration Script:**

```sql
-- Migration: Add performance tracking tables
-- File: src/database/migrations/010_add_performance_tracking.sql

-- Create tables (see section 2.1 for full schema)
CREATE TABLE IF NOT EXISTS performance_baselines (...);
CREATE TABLE IF NOT EXISTS performance_alerts (...);
CREATE TABLE IF NOT EXISTS performance_targets (...);

-- Seed targets from CLAUDE.md (see section 2.1)
INSERT INTO performance_targets (...) VALUES (...);
```

### 6.2 Data Retention Policy

**Retention Rules:**
- **Raw baselines:** Keep last 30 days (rolling window)
- **Daily aggregates:** Keep last 365 days (yearly history)
- **Alerts:** Keep all (for audit trail)
- **Cold start data:** Keep separate, 7 days

**Archival Strategy:**

```python
# Run daily via cron or on startup
def archive_old_baselines():
    """
    Archive baselines older than 30 days to daily aggregates.
    """
    # Calculate daily aggregates
    aggregates = db.execute("""
        SELECT
            DATE(timestamp) as date,
            AVG(startup_time_ms) as avg_startup,
            MIN(startup_time_ms) as min_startup,
            MAX(startup_time_ms) as max_startup,
            -- ... other metrics
        FROM performance_baselines
        WHERE timestamp < datetime('now', '-30 days')
        GROUP BY DATE(timestamp)
    """)

    # Insert into daily aggregates table
    db.insert_many('performance_daily_aggregates', aggregates)

    # Delete old raw data
    db.execute("""
        DELETE FROM performance_baselines
        WHERE timestamp < datetime('now', '-30 days')
    """)
```

### 6.3 File-Based Backup

**Export to JSON (for portability):**

```python
def export_baselines_to_json(output_path: str, days: int = 30):
    """
    Export last N days of baselines to JSON for backup/analysis.
    """
    baselines = db.query("""
        SELECT * FROM performance_baselines
        WHERE timestamp > datetime('now', '-{days} days')
        ORDER BY timestamp DESC
    """.format(days=days))

    with open(output_path, 'w') as f:
        json.dump([dict(row) for row in baselines], f, indent=2)
```

**Location:** `/Users/chrislehnen/Projecten/Definitie-app/data/performance_backups/`

---

## 7. Reporting and Visualization

### 7.1 Terminal Output (Immediate Feedback)

**On every startup:**

```
🚀 DefinitieAgent Startup Performance
────────────────────────────────────────────────────────────
⏱️  Startup Time:        387ms  ✅ (target: 500ms)
🔧 Container Init:       1x     ✅ (target: 1x)
📊 Validation Ready:     142ms  ✅ (target: 1000ms)
💾 Memory Usage:         328MB  ✅ (target: 500MB)
🎯 Performance Index:    94/100 ✅

⚠️  WARNINGS:
  • Prompt tokens: 4,123 (target: 3,000) ⚠️
  • Container cache miss detected (investigate)

📈 Trend: Performance improving (+3% vs 7-day avg)
────────────────────────────────────────────────────────────
```

### 7.2 Log File Output

**Structured logging:**

```python
# logs/performance_YYYYMMDD.log
{
    "timestamp": "2025-10-07T14:32:15Z",
    "session_id": "sess_abc123",
    "git_commit": "49848881",
    "metrics": {
        "startup_time_ms": 387,
        "container_init_count": 1,
        "validation_time_ms": 142,
        "prompt_token_count": 4123,
        "api_cost_cents": 1.23
    },
    "alerts": [
        {
            "metric_id": "API-002",
            "severity": "warning",
            "message": "Prompt tokens 37% above target",
            "deviation": 1123
        }
    ],
    "performance_index": 94,
    "baseline_confidence": 0.85
}
```

### 7.3 UI Dashboard (Streamlit Tab)

**New tab: "Performance" in TabbedInterface**

```python
# src/ui/tabs/performance_tab.py
class PerformanceTab:
    def render(self):
        st.header("📊 Performance Dashboard")

        # Time range selector
        time_range = st.selectbox("Time Range", ["Last 24 Hours", "Last 7 Days", "Last 30 Days"])

        # Metric cards (top row)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            self._render_metric_card("Startup Time", "APP-001", "ms")
        with col2:
            self._render_metric_card("API Cost", "API-003", "cents")
        with col3:
            self._render_metric_card("Memory Usage", "MEM-001", "MB")
        with col4:
            self._render_metric_card("Performance Index", "COMPOSITE", "score")

        # Trend charts (middle section)
        st.subheader("Performance Trends")
        self._render_trend_chart("APP-001", time_range)

        # Alert table (bottom section)
        st.subheader("Recent Alerts")
        self._render_alert_table()

        # Export button
        if st.button("📥 Export Performance Report"):
            self._export_report()
```

**Visualizations:**
- Line charts: Metric over time with baseline bands
- Bar charts: Current vs target comparison
- Heatmap: Performance index by hour of day
- Table: Alert history with severity indicators

### 7.4 CLI Commands

**Performance query commands:**

```bash
# Quick status
python -m scripts.monitoring.performance_cli status

# Detailed report
python -m scripts.monitoring.performance_cli report --days 7

# Compare two commits
python -m scripts.monitoring.performance_cli compare abc123 def456

# Export to CSV
python -m scripts.monitoring.performance_cli export --format csv --output performance.csv

# Alert summary
python -m scripts.monitoring.performance_cli alerts --severity warning --unacknowledged
```

### 7.5 CI/CD Integration

**GitHub Actions workflow:**

```yaml
# .github/workflows/performance-check.yml
name: Performance Regression Check

on:
  pull_request:
    branches: [main]

jobs:
  performance-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run performance benchmarks
        run: |
          python scripts/monitoring/run_performance_benchmarks.py --output results.json

      - name: Compare against baseline
        run: |
          python scripts/monitoring/compare_performance.py \
            --current results.json \
            --baseline main \
            --threshold 10

      - name: Post results to PR
        if: always()
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('results.json'));
            const comment = `## 📊 Performance Report\n\n${results.summary}`;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

**PR Comment Example:**

```markdown
## 📊 Performance Report

**Branch:** `feature/optimize-validation`
**Commit:** `abc1234`
**Baseline:** `main` (commit: `def5678`)

### Results
| Metric | Current | Baseline | Change | Status |
|--------|---------|----------|--------|--------|
| Startup Time | 412ms | 387ms | +6.5% | ⚠️ Warning |
| Container Init | 1x | 2x | -50% | ✅ Improved |
| Validation Time | 892ms | 1042ms | -14.4% | ✅ Improved |
| Prompt Tokens | 3,245 | 4,123 | -21.3% | ✅ Improved |

### Summary
✅ **3 metrics improved**
⚠️ **1 metric regressed** (within threshold)
❌ **0 critical regressions**

**Overall:** Performance looks good! Minor regression in startup time is acceptable given validation improvements.
```

---

## 8. Integration with Existing Monitoring

### 8.1 API Monitor Integration

**Leverage existing `api_monitor.py`:**

```python
# src/monitoring/performance_tracker.py
from monitoring.api_monitor import get_metrics_collector

class PerformanceTracker:
    def record_api_metrics(self):
        """Pull API metrics from existing monitor."""
        collector = get_metrics_collector()
        metrics = collector.get_realtime_metrics()

        self.record_metric('api_call_time_ms', metrics['avg_response_time'] * 1000)
        self.record_metric('api_cost_cents', metrics['total_cost'] * 100)
        self.record_metric('cache_hit_rate', metrics['cache_hit_rate'])
```

### 8.2 Cache Monitoring Integration

**Pull from RuleCache:**

```python
from toetsregels.rule_cache import RuleCache

class PerformanceTracker:
    def record_cache_metrics(self):
        """Pull cache stats from RuleCache."""
        cache = RuleCache.get_instance()
        stats = cache.get_stats()

        self.record_metric('rule_cache_hit_rate', stats['hit_rate'])
        self.record_metric('rule_cache_size', stats['entries'])
        self.record_metric('rule_loading_time_ms', stats['avg_load_time'] * 1000)
```

### 8.3 Existing PerformanceMonitor Integration

**Merge with `utils/performance_monitor.py`:**

```python
# Extend existing PerformanceMonitor
from utils.performance_monitor import get_performance_monitor

class PerformanceTracker:
    def __init__(self):
        # Use existing monitor for timing
        self.monitor = get_performance_monitor()

        # Add baseline tracking on top
        self.baseline_recorder = BaselineRecorder()

    def record_baseline_snapshot(self):
        """Convert PerformanceMonitor summary to baseline record."""
        summary = self.monitor.get_summary()

        baseline = {
            'startup_time_ms': summary.get('total_duration', 0) * 1000,
            'operation_breakdown': json.dumps(summary),
            # ... map other metrics
        }

        self.baseline_recorder.save(baseline)
```

---

## 9. Implementation Phases

### Phase 1: Foundation (Week 1) - SIMPLE
**Goal:** Basic tracking without alerts

**Tasks:**
- [ ] Create database tables (migration script)
- [ ] Implement `PerformanceTracker` class
- [ ] Add instrumentation to main.py (startup timing)
- [ ] Add instrumentation to container.py (init count)
- [ ] Record to database on every startup
- [ ] Add CLI command: `performance-cli status`

**Success Criteria:**
- Baselines recorded to database on every run
- Can query last 7 days of data via CLI

**Complexity:** SIMPLE (3-4 hours)

---

### Phase 2: Metrics & Baselines (Week 2) - MEDIUM
**Goal:** Track all core metrics with baseline calculation

**Tasks:**
- [ ] Add instrumentation to ValidationOrchestrator
- [ ] Add instrumentation to DefinitionOrchestrator
- [ ] Add instrumentation to RuleCache
- [ ] Implement baseline calculation logic
- [ ] Add `@measure_performance` decorator
- [ ] Implement cold start detection

**Success Criteria:**
- All 13 core metrics tracked (APP-001 through MEM-002)
- Baseline calculated from rolling window
- Cold starts separated from warm runs

**Complexity:** MEDIUM (1-2 days)

---

### Phase 3: Regression Detection (Week 3) - MEDIUM
**Goal:** Automated regression detection and alerting

**Tasks:**
- [ ] Implement threshold-based detection (Tier 1)
- [ ] Implement statistical regression detection (Tier 2)
- [ ] Implement trend analysis detection (Tier 3)
- [ ] Create alert logic and database records
- [ ] Add terminal output with warnings
- [ ] Add structured log output

**Success Criteria:**
- Regressions detected within 10% threshold
- Alerts visible in terminal on startup
- Alert history queryable via CLI

**Complexity:** MEDIUM (1-2 days)

---

### Phase 4: Visualization (Week 4) - COMPLEX
**Goal:** UI dashboard and reporting

**Tasks:**
- [ ] Create PerformanceTab in UI
- [ ] Implement metric cards
- [ ] Implement trend charts (matplotlib/plotly)
- [ ] Implement alert table
- [ ] Add export functionality
- [ ] Add time range filtering

**Success Criteria:**
- Performance tab visible in UI
- Charts render correctly
- Export works (CSV/JSON)

**Complexity:** COMPLEX (2-3 days)

---

### Phase 5: CI/CD Integration (Week 5) - MEDIUM
**Goal:** Automated performance testing in CI

**Tasks:**
- [ ] Create GitHub Actions workflow
- [ ] Implement performance benchmark script
- [ ] Implement baseline comparison script
- [ ] Add PR comment posting
- [ ] Document usage in CONTRIBUTING.md

**Success Criteria:**
- Performance checks run on every PR
- Results posted to PR as comment
- Fails CI if critical regression detected

**Complexity:** MEDIUM (1 day)

---

### Phase 6: Advanced Features (Future) - COMPLEX
**Goal:** Enhanced analytics and optimization

**Tasks:**
- [ ] Implement anomaly detection (ML-based)
- [ ] Add performance profiling integration
- [ ] Add flame graph generation
- [ ] Implement A/B test performance comparison
- [ ] Add Slack/email alerting

**Success Criteria:**
- Anomalies detected without explicit thresholds
- Profiling data linked to slow operations

**Complexity:** COMPLEX (1 week+)

---

## 10. Complexity Estimate

### Overall Complexity: **MEDIUM**

**Breakdown by Phase:**

| Phase | Complexity | Effort | Dependencies |
|-------|-----------|--------|--------------|
| Phase 1: Foundation | SIMPLE | 4 hours | None |
| Phase 2: Metrics | MEDIUM | 2 days | Phase 1 |
| Phase 3: Regression | MEDIUM | 2 days | Phase 2 |
| Phase 4: Visualization | COMPLEX | 3 days | Phase 3 |
| Phase 5: CI/CD | MEDIUM | 1 day | Phase 3 |
| **Total Core (P1-P3)** | **MEDIUM** | **4-5 days** | **Sequential** |
| **Total with UI (P1-P4)** | **COMPLEX** | **7-8 days** | **Sequential** |

**Risk Factors:**
- ⚠️ **Integration complexity:** Merging with existing monitors (mitigated by reuse)
- ⚠️ **Database schema changes:** Need careful migration (mitigated by SQLite flexibility)
- ⚠️ **UI rendering performance:** Charts may slow down UI (mitigated by lazy loading)
- ⚠️ **Test coverage:** Need comprehensive tests (add 20% time overhead)

**Recommendation:** Implement Phases 1-3 first (core functionality), then add Phase 4 (UI) if needed. Phase 5 (CI/CD) can be done independently.

---

## 11. Performance Overhead Estimate

### Instrumentation Overhead

**Per Operation:**
- Timer start/stop: ~0.01ms (negligible)
- Metric recording: ~0.05ms (negligible)
- Database write: ~5ms (batched)

**Per Session:**
- Baseline calculation: ~10ms (cached)
- Alert evaluation: ~15ms (only if baseline exists)
- Database commit: ~20ms (single transaction)

**Total Overhead:** <50ms per app start (1.25% of 400ms startup)

**Verification:**
```python
# Measure overhead
import time

start = time.perf_counter()
tracker = PerformanceTracker()
tracker.start_operation('test')
tracker.stop_operation('test')
tracker.record_baseline_snapshot()
overhead = (time.perf_counter() - start) * 1000

assert overhead < 50, f"Overhead too high: {overhead}ms"
```

### Database Size Growth

**Per Baseline Record:** ~1KB (JSON fields compressed)
**Per Day:** ~1KB × (10 app starts/day) = 10KB/day
**Per Month:** ~300KB/month
**Per Year:** ~3.6MB/year

**Mitigation:** Archive to daily aggregates after 30 days (see Section 6.2)

### Memory Footprint

**PerformanceTracker instance:** ~5KB
**In-memory cache:** ~50KB (20 baselines × 2.5KB each)
**Total:** <100KB (0.02% of 500MB target)

**Verdict:** Negligible impact on memory usage.

---

## 12. Security & Privacy Considerations

### Data Sanitization

**⚠️ NO PII in metrics:**
- ❌ Never log definition text (may contain sensitive terms)
- ❌ Never log API keys (use hash if needed)
- ❌ Never log user identifiers
- ✅ Only log timing, counts, sizes

**Implementation:**

```python
class PerformanceTracker:
    def record_operation(self, name: str, context: dict = None):
        # Sanitize context
        safe_context = {
            k: v for k, v in (context or {}).items()
            if k not in ['api_key', 'user_id', 'definition_text']
        }

        # Hash sensitive identifiers if needed
        if 'session_id' in safe_context:
            safe_context['session_id'] = hashlib.sha256(
                safe_context['session_id'].encode()
            ).hexdigest()[:16]

        self._record(name, safe_context)
```

### Access Control

**Database permissions:**
- Performance tables: READ/WRITE by app only
- No external access (SQLite is local only)

### Audit Trail

**All alerts are logged:**
- Who acknowledged alert
- When alert was resolved
- Resolution notes

**Compliance:** Aligns with AVG/GDPR (no personal data stored)

---

## 13. Success Metrics for Tracking System

### Adoption Metrics

**Target (after 30 days):**
- [ ] 100% of app starts record baselines
- [ ] 80% of core operations instrumented
- [ ] 50+ baselines collected per metric (high confidence)
- [ ] 10+ alerts triggered (system is working)
- [ ] 5+ alerts acknowledged (team is engaging)

### Effectiveness Metrics

**Target (after 60 days):**
- [ ] 3+ performance regressions caught before production
- [ ] 2+ optimizations driven by data (e.g., fix prompt duplication)
- [ ] 20% reduction in API costs (detected via tracking)
- [ ] 0 critical performance issues missed

### Developer Experience

**Survey (after 90 days):**
- [ ] 4+ stars: "Performance tracking is useful"
- [ ] 4+ stars: "Overhead is acceptable"
- [ ] 4+ stars: "UI dashboard is helpful"

---

## 14. Next Steps (Recommended)

### Immediate (This Week)

1. **Review & Approve Design:** Get stakeholder sign-off on this document
2. **Create User Story:** Add to backlog (e.g., US-203: Performance Baseline Tracking)
3. **Prototype Phase 1:** Implement basic tracking (4 hours)
4. **Validate Overhead:** Measure actual overhead vs estimate

### Short-Term (Next 2 Weeks)

5. **Implement Phase 2:** Add all core metrics
6. **Implement Phase 3:** Add regression detection
7. **Iterate on Thresholds:** Tune warning/error thresholds based on real data
8. **Document Usage:** Add to CLAUDE.md and README

### Medium-Term (Next Month)

9. **Implement Phase 4:** Build UI dashboard
10. **Implement Phase 5:** Add CI/CD integration
11. **Train Team:** Document how to use tracking system
12. **Retrospective:** Evaluate effectiveness, adjust as needed

---

## 15. Alternative Approaches Considered

### Alternative 1: Use External APM (e.g., New Relic, DataDog)

**Pros:**
- Professional-grade monitoring
- Advanced analytics out-of-box
- Cloud-based dashboards

**Cons:**
- ❌ Cost: $50-200/month
- ❌ Overkill for single-user app
- ❌ Adds external dependency
- ❌ Data leaves local environment

**Verdict:** Rejected (too complex, too expensive)

---

### Alternative 2: Use pytest-benchmark for All Tracking

**Pros:**
- Already have pytest-benchmark integration
- Good for unit test performance

**Cons:**
- ❌ Only works in test environment
- ❌ Doesn't track production performance
- ❌ No real-time alerting
- ❌ No historical trending

**Verdict:** Rejected (complementary, not replacement)

---

### Alternative 3: Manual Logging + Ad-Hoc Analysis

**Pros:**
- Zero implementation cost
- Maximum flexibility

**Cons:**
- ❌ No automation (manual = error-prone)
- ❌ No alerting (regressions go unnoticed)
- ❌ No historical data (can't track trends)
- ❌ High maintenance cost

**Verdict:** Rejected (current state, needs improvement)

---

### Alternative 4: File-Based Metrics (No Database)

**Pros:**
- Simpler than database
- Easier to version control

**Cons:**
- ❌ No efficient querying (can't calculate baselines fast)
- ❌ No relational data (can't join alerts to baselines)
- ❌ File locking issues (concurrent writes)
- ❌ No ACID guarantees

**Verdict:** Rejected (database is better fit)

---

## 16. References & Related Docs

### Internal Documentation
- **CLAUDE.md:** Performance goals and known issues
- **CONTAINER_ISSUE_SUMMARY.md:** Container duplication analysis
- **PERFORMANCE-ISSUES-DOCUMENTATION-REPORT.md:** Historical performance issues
- **US-201:** ServiceContainer caching optimization
- **US-202:** Rule cache performance fix (77% improvement)
- **EPIC-026:** UI Architecture refactoring

### Existing Code
- `/src/utils/performance_monitor.py` - Basic performance monitoring
- `/src/monitoring/api_monitor.py` - API call monitoring
- `/src/toetsregels/rule_cache.py` - Rule loading caching
- `/tests/services/test_validation_performance_baseline.py` - Performance tests

### External References
- **SQLite Performance Best Practices:** https://www.sqlite.org/optoverview.html
- **Python time.perf_counter():** https://docs.python.org/3/library/time.html#time.perf_counter
- **Statistical Process Control:** https://en.wikipedia.org/wiki/Statistical_process_control

---

## Appendix A: Sample Code

### PerformanceTracker Core Implementation

```python
# src/monitoring/performance_tracker.py
"""
Performance baseline tracking system for DefinitieAgent.
"""

import time
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Singleton class for tracking performance baselines and detecting regressions.

    Usage:
        tracker = PerformanceTracker.get_instance()
        tracker.start_operation('validation')
        # ... do work ...
        tracker.stop_operation('validation')
        tracker.record_baseline_snapshot()
    """

    _instance: Optional['PerformanceTracker'] = None

    def __init__(self):
        self.operations: Dict[str, float] = {}  # operation_name -> start_time
        self.metrics: Dict[str, Any] = {}  # metric_id -> value
        self.session_id = self._generate_session_id()
        self.start_time = time.perf_counter()

        # Initialize database connection
        from database.definitie_repository import get_database_connection
        self.db = get_database_connection()

        # Ensure tables exist
        self._ensure_tables()

    @classmethod
    def get_instance(cls) -> 'PerformanceTracker':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start_operation(self, operation_name: str):
        """Start timing an operation."""
        self.operations[operation_name] = time.perf_counter()
        logger.debug(f"Started timing: {operation_name}")

    def stop_operation(self, operation_name: str, error: Exception = None) -> float:
        """
        Stop timing an operation and return duration in milliseconds.

        Returns:
            Duration in milliseconds
        """
        if operation_name not in self.operations:
            logger.warning(f"Operation {operation_name} was not started")
            return 0.0

        start_time = self.operations.pop(operation_name)
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Store as metric
        metric_id = self._operation_to_metric_id(operation_name)
        self.metrics[metric_id] = duration_ms

        if error:
            logger.error(f"Operation {operation_name} failed after {duration_ms:.1f}ms: {error}")
        else:
            logger.debug(f"Operation {operation_name} completed in {duration_ms:.1f}ms")

        return duration_ms

    def record_metric(self, metric_id: str, value: Any):
        """Record a metric value."""
        self.metrics[metric_id] = value
        logger.debug(f"Recorded metric {metric_id}: {value}")

    def record_baseline_snapshot(self) -> int:
        """
        Save current metrics as a baseline snapshot to database.

        Returns:
            Baseline ID
        """
        # Calculate derived metrics
        self._calculate_derived_metrics()

        # Get system context
        import platform
        import psutil
        import sys

        process = psutil.Process()
        memory_info = process.memory_info()

        baseline = {
            'timestamp': datetime.now(timezone.utc),
            'session_id': self.session_id,
            'git_commit': self._get_git_commit(),
            'app_version': self._get_app_version(),
            'environment': 'local',

            # System context
            'python_version': sys.version.split()[0],
            'platform': platform.system(),
            'cpu_count': psutil.cpu_count(),
            'total_memory_mb': psutil.virtual_memory().total // (1024 * 1024),

            # Core metrics
            'startup_time_ms': self.metrics.get('startup_time_ms'),
            'container_init_count': self.metrics.get('container_init_count'),
            'container_init_time_ms': self.metrics.get('container_init_time_ms'),
            'validation_time_ms': self.metrics.get('validation_time_ms'),
            'rule_loading_time_ms': self.metrics.get('rule_loading_time_ms'),
            'generation_time_ms': self.metrics.get('generation_time_ms'),
            'api_call_time_ms': self.metrics.get('api_call_time_ms'),
            'export_time_ms': self.metrics.get('export_time_ms'),

            # API metrics
            'prompt_token_count': self.metrics.get('prompt_token_count'),
            'api_cost_cents': self.metrics.get('api_cost_cents'),

            # Memory metrics
            'peak_memory_mb': memory_info.rss // (1024 * 1024),
            'memory_growth_mb': self.metrics.get('memory_growth_mb', 0),

            # Cache metrics
            'container_cache_hit_rate': self.metrics.get('container_cache_hit_rate'),
            'rule_cache_hit_rate': self.metrics.get('rule_cache_hit_rate'),
            'prompt_cache_hit_rate': self.metrics.get('prompt_cache_hit_rate'),
            'definition_cache_hit_rate': self.metrics.get('definition_cache_hit_rate'),

            # Derived metrics
            'performance_index': self.metrics.get('performance_index', 0),
            'regression_score': self.metrics.get('regression_score', 0),

            # Issue flags
            'has_double_container': self.metrics.get('container_init_count', 1) > 1,
            'has_prompt_duplication': self.metrics.get('prompt_token_count', 0) > 5000,
            'has_rule_reload_issue': False,  # Detected elsewhere

            # JSON fields
            'operation_breakdown': json.dumps(self.metrics),
            'cache_stats': json.dumps(self._get_cache_stats()),
            'error_details': None,
            'notes': None
        }

        # Insert into database
        baseline_id = self._insert_baseline(baseline)

        # Check for regressions
        alerts = self._check_regressions(baseline_id)

        # Log summary
        self._log_summary(baseline, alerts)

        return baseline_id

    def _calculate_derived_metrics(self):
        """Calculate derived metrics from raw measurements."""
        # Performance index (0-100, higher is better)
        targets = self._get_targets()
        scores = []

        for metric_id, target in targets.items():
            current = self.metrics.get(metric_id)
            if current is not None:
                # Score: 100 if at target, 0 if 2x target
                score = max(0, min(100, 100 - (current - target['value']) / target['value'] * 100))
                scores.append(score)

        self.metrics['performance_index'] = sum(scores) / len(scores) if scores else 0

        # Regression score (calculated after baseline comparison)
        # Will be set by _check_regressions()

    def _check_regressions(self, baseline_id: int) -> list:
        """Check for performance regressions and create alerts."""
        alerts = []

        from monitoring.regression_detector import RegressionDetector
        detector = RegressionDetector(self.db)

        for metric_id, current_value in self.metrics.items():
            if current_value is None:
                continue

            # Run detection tiers
            result = detector.evaluate_metric(metric_id, current_value)

            if result['severity'] != 'ok':
                alert = {
                    'baseline_id': baseline_id,
                    'alert_type': 'regression',
                    'severity': result['severity'],
                    'metric_id': metric_id,
                    'metric_name': result['metric_name'],
                    'current_value': current_value,
                    'expected_value': result['expected_value'],
                    'deviation_percent': result['deviation_percent'],
                    'threshold_breached': result['threshold_breached'],
                    'context_json': json.dumps(result['details'])
                }

                alert_id = self._insert_alert(alert)
                alerts.append(alert)

        return alerts

    def _log_summary(self, baseline: dict, alerts: list):
        """Log performance summary to console."""
        print("\n🚀 DefinitieAgent Startup Performance")
        print("─" * 60)

        # Key metrics
        startup = baseline.get('startup_time_ms')
        if startup:
            status = "✅" if startup < 500 else "⚠️"
            print(f"⏱️  Startup Time:        {startup:.0f}ms  {status} (target: 500ms)")

        container_count = baseline.get('container_init_count', 1)
        status = "✅" if container_count == 1 else "⚠️"
        print(f"🔧 Container Init:       {container_count}x     {status} (target: 1x)")

        validation = baseline.get('validation_time_ms')
        if validation:
            status = "✅" if validation < 1000 else "⚠️"
            print(f"📊 Validation Ready:     {validation:.0f}ms  {status} (target: 1000ms)")

        memory = baseline.get('peak_memory_mb')
        if memory:
            status = "✅" if memory < 500 else "⚠️"
            print(f"💾 Memory Usage:         {memory:.0f}MB  {status} (target: 500MB)")

        perf_index = baseline.get('performance_index', 0)
        status = "✅" if perf_index >= 80 else "⚠️"
        print(f"🎯 Performance Index:    {perf_index:.0f}/100 {status}")

        # Warnings
        if alerts:
            print(f"\n⚠️  WARNINGS:")
            for alert in alerts[:3]:  # Show top 3
                print(f"  • {alert['metric_name']}: {alert['current_value']:.0f} (target: {alert['expected_value']:.0f}) {alert['severity'].upper()}")

        print("─" * 60)
        print()

    # Helper methods

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        import uuid
        return f"sess_{uuid.uuid4().hex[:8]}"

    def _get_git_commit(self) -> Optional[str]:
        """Get current git commit hash."""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=1
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def _get_app_version(self) -> str:
        """Get application version."""
        # Could read from __version__ or package metadata
        return "1.0.0"

    def _operation_to_metric_id(self, operation_name: str) -> str:
        """Map operation name to metric ID."""
        mapping = {
            'app_startup': 'startup_time_ms',
            'container_init': 'container_init_time_ms',
            'validation': 'validation_time_ms',
            'generation': 'generation_time_ms',
            'rule_loading': 'rule_loading_time_ms',
            'api_call': 'api_call_time_ms',
            'export': 'export_time_ms'
        }
        return mapping.get(operation_name, f"{operation_name}_time_ms")

    def _get_cache_stats(self) -> dict:
        """Collect cache statistics from various sources."""
        stats = {}

        # RuleCache stats
        try:
            from toetsregels.rule_cache import RuleCache
            cache = RuleCache.get_instance()
            stats['rule_cache'] = cache.get_stats()
        except Exception:
            pass

        # API Monitor stats
        try:
            from monitoring.api_monitor import get_metrics_collector
            collector = get_metrics_collector()
            stats['api_metrics'] = collector.get_realtime_metrics()
        except Exception:
            pass

        return stats

    def _get_targets(self) -> dict:
        """Load performance targets from database."""
        rows = self.db.execute("SELECT metric_id, metric_name, target_value, unit FROM performance_targets WHERE active = 1").fetchall()
        return {
            row['metric_id']: {
                'name': row['metric_name'],
                'value': row['target_value'],
                'unit': row['unit']
            }
            for row in rows
        }

    def _ensure_tables(self):
        """Ensure performance tracking tables exist."""
        # Run migration if needed
        try:
            self.db.execute("SELECT 1 FROM performance_baselines LIMIT 1")
        except Exception:
            logger.info("Creating performance tracking tables...")
            from database.migrate_database import run_migration
            run_migration('010_add_performance_tracking.sql')

    def _insert_baseline(self, baseline: dict) -> int:
        """Insert baseline record into database."""
        columns = ', '.join(baseline.keys())
        placeholders = ', '.join(['?' for _ in baseline])
        query = f"INSERT INTO performance_baselines ({columns}) VALUES ({placeholders})"

        cursor = self.db.execute(query, list(baseline.values()))
        self.db.commit()
        return cursor.lastrowid

    def _insert_alert(self, alert: dict) -> int:
        """Insert alert record into database."""
        columns = ', '.join(alert.keys())
        placeholders = ', '.join(['?' for _ in alert])
        query = f"INSERT INTO performance_alerts ({columns}) VALUES ({placeholders})"

        cursor = self.db.execute(query, list(alert.values()))
        self.db.commit()
        return cursor.lastrowid
```

---

## Appendix B: Example Usage

### Basic Usage (Startup Tracking)

```python
# src/main.py
from monitoring.performance_tracker import PerformanceTracker

def main():
    tracker = PerformanceTracker.get_instance()
    tracker.start_operation('app_startup')

    try:
        SessionStateManager.initialize_session_state()
        interface = TabbedInterface()
        interface.render()

        tracker.stop_operation('app_startup')
        tracker.record_baseline_snapshot()

    except Exception as e:
        tracker.stop_operation('app_startup', error=e)
        raise
```

### Decorator Usage (Service Methods)

```python
# src/services/validation/validation_orchestrator_v2.py
from monitoring.decorators import measure_performance

class ValidationOrchestratorV2:
    @measure_performance('validation', 'VAL-001')
    async def validate(self, definition: str) -> dict:
        # Implementation
        result = await self._perform_validation(definition)
        return result
```

### Manual Metric Recording

```python
# src/services/ai_service_v2.py
from monitoring.performance_tracker import PerformanceTracker

class AIServiceV2:
    async def call_api(self, prompt: str) -> dict:
        tracker = PerformanceTracker.get_instance()

        response = await self._call(prompt)

        # Record API metrics
        tracker.record_metric('prompt_token_count', response['usage']['total_tokens'])
        tracker.record_metric('api_cost_cents', response['cost'] * 100)

        return response
```

---

## Appendix C: CLI Command Reference

### performance-cli Commands

```bash
# Show current performance status
$ python -m scripts.monitoring.performance_cli status

# Generate detailed report
$ python -m scripts.monitoring.performance_cli report --days 7 --format text

# Export to CSV
$ python -m scripts.monitoring.performance_cli export --output performance.csv

# Compare two commits
$ python -m scripts.monitoring.performance_cli compare abc123 def456

# List active alerts
$ python -m scripts.monitoring.performance_cli alerts --unacknowledged

# Acknowledge alert
$ python -m scripts.monitoring.performance_cli alerts ack --id 42 --notes "Fixed by PR #123"

# Show baselines for metric
$ python -m scripts.monitoring.performance_cli baseline --metric APP-001 --days 30

# Calculate regression score
$ python -m scripts.monitoring.performance_cli regression --threshold 10

# Help
$ python -m scripts.monitoring.performance_cli --help
```

---

**END OF DOCUMENT**

This design document provides a complete blueprint for implementing a performance baseline tracking system for DefinitieAgent. All sections are fully specified and ready for implementation.
