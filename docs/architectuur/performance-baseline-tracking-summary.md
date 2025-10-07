# Performance Baseline Tracking System - Quick Reference

**Full Design:** [performance-baseline-tracking-design.md](./performance-baseline-tracking-design.md)
**Date:** 2025-10-07
**Status:** DESIGN APPROVED

---

## TL;DR

**What:** Automated system to track performance baselines, detect regressions, and alert on slowdowns.

**Why:** Catch performance issues early (e.g., double container init, prompt token bloat) before they impact users.

**How:** Lightweight instrumentation (<50ms overhead) + SQLite storage + Statistical regression detection + UI dashboard

**When:** Implement in 5 phases over 4-5 weeks (core functionality in 4-5 days)

---

## Quick Stats

| Metric | Value |
|--------|-------|
| **Implementation Effort** | 4-5 days (core), 7-8 days (with UI) |
| **Performance Overhead** | <50ms (<1.25% of startup time) |
| **Database Size Growth** | ~300KB/month (compressed) |
| **Memory Footprint** | <100KB (negligible) |
| **Metrics Tracked** | 13 core + 8 secondary = 21 total |
| **Complexity** | MEDIUM (manageable) |

---

## Core Metrics (13)

1. **APP-001:** Application Startup Time (target: <500ms)
2. **SVC-001:** ServiceContainer Init Count (target: 1x only)
3. **SVC-002:** Service Init Time (target: <200ms)
4. **VAL-001:** Single Validation Time (target: <1s)
5. **VAL-002:** Rule Loading Time (target: <100ms)
6. **VAL-003:** Rule Cache Hit Rate (target: >90%)
7. **GEN-001:** Definition Generation Time (target: <5s)
8. **API-001:** API Call Duration (target: <3s)
9. **API-002:** Prompt Token Count (target: <3000)
10. **API-003:** API Cost per Request (target: <$0.01)
11. **EXP-001:** Export Operation Time (target: <2s)
12. **MEM-001:** Peak Memory Usage (target: <500MB)
13. **MEM-002:** Memory Growth Rate (target: <10MB/hour)

---

## Key Features

### 1. Baseline Calculation
- **Method:** Rolling median of last 20 successful runs
- **Confidence:** Low (0-0.3), Medium (0.3-0.7), High (0.7-1.0)
- **Update:** Every 10 new measurements

### 2. Regression Detection (3 Tiers)
- **Tier 1:** Threshold-based (simple: >target?)
- **Tier 2:** Statistical (z-score: >1 std dev?)
- **Tier 3:** Trend analysis (getting worse over time?)

### 3. Alerting
- **Severity:** info, warning, error, critical
- **Thresholds:** Warning at +10%, Error at +20%
- **Output:** Terminal, logs, database, UI dashboard

### 4. Storage
- **Database:** SQLite (existing `data/definities.db`)
- **Tables:** `performance_baselines`, `performance_alerts`, `performance_targets`
- **Retention:** 30 days raw, 365 days aggregated

---

## Implementation Phases

### Phase 1: Foundation (4 hours) - SIMPLE ✅
- Create database tables
- Implement `PerformanceTracker` class
- Add startup timing
- Record to database

**Deliverable:** Basic tracking without alerts

---

### Phase 2: Metrics (2 days) - MEDIUM
- Instrument all core operations
- Implement baseline calculation
- Add `@measure_performance` decorator
- Handle cold starts

**Deliverable:** All metrics tracked with baselines

---

### Phase 3: Regression Detection (2 days) - MEDIUM
- Implement 3-tier detection
- Create alert logic
- Add terminal/log output
- CLI commands

**Deliverable:** Automated regression alerts

---

### Phase 4: Visualization (3 days) - COMPLEX
- Build Streamlit dashboard
- Metric cards + trend charts
- Alert table
- Export functionality

**Deliverable:** UI for performance monitoring

---

### Phase 5: CI/CD Integration (1 day) - MEDIUM
- GitHub Actions workflow
- PR comment with results
- Fail CI on critical regression

**Deliverable:** Automated performance testing

---

## Instrumentation Points

| Location | What to Measure | Metric ID |
|----------|----------------|-----------|
| `main.py` | Startup time | APP-001 |
| `container.py` | Init count + time | SVC-001, SVC-002 |
| `validation_orchestrator_v2.py` | Validation time | VAL-001 |
| `definition_orchestrator_v2.py` | Generation time | GEN-001 |
| `rule_cache.py` | Loading time + hit rate | VAL-002, VAL-003 |
| `ai_service_v2.py` | API time + tokens + cost | API-001/002/003 |
| `export_service.py` | Export time | EXP-001 |
| `psutil.Process` | Memory usage | MEM-001/002 |

---

## Example Output

### Terminal (on every startup)

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

### CLI Commands

```bash
# Quick status
python -m scripts.monitoring.performance_cli status

# Detailed report
python -m scripts.monitoring.performance_cli report --days 7

# Compare commits
python -m scripts.monitoring.performance_cli compare abc123 def456

# Export data
python -m scripts.monitoring.performance_cli export --format csv
```

### GitHub PR Comment

```markdown
## 📊 Performance Report

**Branch:** `feature/optimize-validation`
**Baseline:** `main`

| Metric | Current | Baseline | Change | Status |
|--------|---------|----------|--------|--------|
| Startup Time | 412ms | 387ms | +6.5% | ⚠️ Warning |
| Container Init | 1x | 2x | -50% | ✅ Improved |
| Validation Time | 892ms | 1042ms | -14.4% | ✅ Improved |
| Prompt Tokens | 3,245 | 4,123 | -21.3% | ✅ Improved |

**Summary:** ✅ 3 improved, ⚠️ 1 regressed (acceptable)
```

---

## Code Examples

### Basic Usage

```python
from monitoring.performance_tracker import PerformanceTracker

def main():
    tracker = PerformanceTracker.get_instance()
    tracker.start_operation('app_startup')

    # ... do work ...

    tracker.stop_operation('app_startup')
    tracker.record_baseline_snapshot()
```

### Decorator Usage

```python
from monitoring.decorators import measure_performance

class ValidationService:
    @measure_performance('validation', 'VAL-001')
    async def validate(self, text: str) -> dict:
        # Implementation
        pass
```

### Manual Metrics

```python
tracker = PerformanceTracker.get_instance()
tracker.record_metric('prompt_token_count', 4123)
tracker.record_metric('api_cost_cents', 1.23)
```

---

## Database Schema (Simplified)

### performance_baselines

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | TIMESTAMP | When measured |
| session_id | TEXT | Unique session |
| git_commit | TEXT | Git SHA |
| startup_time_ms | REAL | APP-001 |
| container_init_count | INTEGER | SVC-001 |
| validation_time_ms | REAL | VAL-001 |
| ... | ... | 20+ other metrics |

### performance_alerts

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| triggered_at | TIMESTAMP | When alerted |
| severity | TEXT | info/warning/error/critical |
| metric_id | TEXT | e.g., 'APP-001' |
| current_value | REAL | Measured value |
| expected_value | REAL | Baseline/target |
| deviation_percent | REAL | How much off |

### performance_targets

| Column | Type | Description |
|--------|------|-------------|
| metric_id | TEXT | e.g., 'APP-001' |
| target_value | REAL | Target (500 for APP-001) |
| warning_threshold | REAL | Warn at +10% |
| error_threshold | REAL | Error at +20% |

---

## Decision Tree: Should I Alert?

```
Current Value vs Target
    │
    ├─ Within 10% → ✅ OK
    │
    ├─ 10-20% over → ⚠️ WARNING
    │   │
    │   ├─ Within 1 std dev → Info only
    │   │
    │   └─ >1 std dev → Warning alert
    │
    └─ >20% over → ❌ ERROR
        │
        ├─ >2 std devs → Error alert
        │
        └─ >3 std devs → 🚨 Critical alert
```

---

## Success Criteria

### After 30 Days
- [ ] 100% of starts record baselines
- [ ] 80% of operations instrumented
- [ ] 50+ baselines per metric (high confidence)
- [ ] 10+ alerts triggered (system working)

### After 60 Days
- [ ] 3+ regressions caught early
- [ ] 2+ optimizations driven by data
- [ ] 20% API cost reduction
- [ ] 0 critical issues missed

---

## Known Issues Detected

Based on existing analysis:

| Issue | Metric | Current | Target | Status |
|-------|--------|---------|--------|--------|
| Double Container | SVC-001 | 2-3x | 1x | 🔴 Active |
| Prompt Duplication | API-002 | 7,250 | 3,000 | 🔴 Active |
| Rule Loading | VAL-002 | 200ms | 100ms | 🟡 Improving |

**This system will track fixes for these issues!**

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Overhead too high | Performance regression | Low | Batch writes, measure first |
| False positives | Alert fatigue | Medium | Tune thresholds, confidence levels |
| Database bloat | Storage issues | Low | Archive to aggregates after 30d |
| Test isolation | Flaky tests | Medium | Clear cache in test setup |

---

## Integration Points

### Existing Systems to Leverage

1. **api_monitor.py:** Pull API metrics (cost, tokens, timing)
2. **performance_monitor.py:** Use for basic timing
3. **rule_cache.py:** Pull cache hit rates
4. **definitie_repository.py:** Use existing DB connection

### New Dependencies

- ✅ None! (Pure stdlib: time, json, sqlite3, logging)
- Optional: `numpy` for statistics (already in requirements.txt)
- Optional: `matplotlib`/`plotly` for charts (Phase 4)

---

## Next Steps

### Immediate Actions
1. ✅ Review this design document
2. ⏳ Create user story (US-203: Performance Baseline Tracking)
3. ⏳ Prototype Phase 1 (4 hours)
4. ⏳ Measure actual overhead vs estimate

### This Week
5. ⏳ Implement Phase 2 (all core metrics)
6. ⏳ Implement Phase 3 (regression detection)
7. ⏳ Iterate on thresholds based on real data

### Next Month
8. ⏳ Implement Phase 4 (UI dashboard)
9. ⏳ Implement Phase 5 (CI/CD integration)
10. ⏳ Retrospective + adjust

---

## Related Documents

- **Full Design:** [performance-baseline-tracking-design.md](./performance-baseline-tracking-design.md)
- **Performance Goals:** [CLAUDE.md](../../CLAUDE.md) (Section: Performance Goals)
- **Container Issue:** [CONTAINER_ISSUE_SUMMARY.md](../analyses/CONTAINER_ISSUE_SUMMARY.md)
- **Historical Issues:** [PERFORMANCE-ISSUES-DOCUMENTATION-REPORT.md](../reports/PERFORMANCE-ISSUES-DOCUMENTATION-REPORT.md)
- **US-202:** [toetsregels-caching-fix.md](../reports/toetsregels-caching-fix.md) (77% faster!)

---

## FAQ

### Q: Why not use external APM (DataDog, New Relic)?
**A:** Overkill + cost ($50-200/month) for single-user app. This is simpler and free.

### Q: Will this slow down my app?
**A:** No! Overhead <50ms (<1.25% of startup). Negligible impact.

### Q: Can I disable tracking?
**A:** Yes! Set `DISABLE_PERFORMANCE_TRACKING=1` env var. (But why?)

### Q: How do I acknowledge an alert?
**A:** `python -m scripts.monitoring.performance_cli alerts ack --id 42 --notes "Fixed"`

### Q: Where is data stored?
**A:** SQLite database: `data/definities.db` (same as definitions)

### Q: Can I export data for analysis?
**A:** Yes! CSV/JSON export via CLI or UI dashboard

### Q: What if I want to track custom metrics?
**A:** Use `tracker.record_metric('my_metric_id', value)` - it's flexible!

---

**Ready to implement?** Start with Phase 1 (4 hours) and iterate from there!

**Questions?** See full design document or ask in #performance Slack channel.
