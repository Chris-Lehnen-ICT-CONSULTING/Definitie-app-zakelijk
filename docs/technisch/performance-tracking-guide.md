# Performance Tracking Quick Reference Guide

## Overview

DefinitieAgent includes automatic performance baseline tracking to detect performance regressions early. The system tracks metrics, calculates baselines, and alerts on degradations.

## Quick Start

### View Performance Status

```bash
python -m src.cli.performance_cli status
```

Output:
```
=== Performance Status ===

🟢 app_startup_ms
   Huidig:   220.5
   Baseline: 224.5
   Afwijking: -1.8%
   Status:   OK
   Confidence: 100% (20 samples)
```

### View All Baselines

```bash
python -m src.cli.performance_cli baselines
```

### View Metric History

```bash
python -m src.cli.performance_cli history app_startup_ms --limit 10
```

## Understanding Alerts

### Alert Levels

| Level | Threshold | Meaning | Action |
|-------|-----------|---------|--------|
| 🟢 OK | <10% slower | Performance within acceptable range | No action needed |
| 🟡 WARNING | 10-20% slower | Noticeable degradation | Investigate cause |
| 🔴 CRITICAL | >20% slower | Significant regression | Fix immediately |

### Example Log Output

```python
# OK - no alert
INFO: Startup tijd: 220.5ms

# WARNING
WARNING: WARNING startup regressie: 258.1ms (>10% slechter dan baseline)

# CRITICAL
WARNING: CRITICAL startup regressie: 280.6ms (>20% slechter dan baseline)
```

## How It Works

### 1. Automatic Tracking

Every time the app starts, it automatically:
1. Measures startup time
2. Stores the measurement in the database
3. Updates the baseline (if enough data)
4. Checks for regression vs baseline
5. Logs a warning if regression detected

### 2. Baseline Calculation

**Algorithm**: Median of last 20 samples

**Why median?**
- More robust against outliers
- Performance spikes (GC, disk I/O) don't skew baseline
- More stable than mean

**Example**:
```
Samples: [200, 205, 210, 215, 220, 225, 230, 235, 240, 245, ...]
Baseline: 222.5ms (median)
```

### 3. Confidence Scoring

**Formula**: `confidence = sample_count / 20`

| Samples | Confidence | Alert Threshold |
|---------|-----------|-----------------|
| 1-4 | 0-20% | No alerts (insufficient data) |
| 5-9 | 25-45% | No alerts (low confidence) |
| 10-19 | 50-95% | ✅ Alerts enabled |
| 20+ | 100% | ✅ Full confidence |

**Note**: Alerts only trigger when confidence >= 50% (10+ samples)

### 4. Sliding Window

The system uses a **sliding window** of 20 samples:
- Always uses the **last 20 measurements**
- Automatically adapts to gradual changes
- Old measurements are archived but not used for baseline

**Example**:
```
Sample 1-20:  Used for baseline (avg ~225ms)
Sample 21:    Replaces sample 1, new baseline calculated
Sample 22:    Replaces sample 2, new baseline calculated
...
```

## Adding Custom Metrics

### In Code

```python
from src.monitoring.performance_tracker import get_tracker

# Track a metric
tracker = get_tracker()
tracker.track_metric(
    "definition_generation_ms",
    elapsed_ms,
    metadata={"model": "gpt-4", "length": 150}
)

# Check for regression
alert = tracker.check_regression("definition_generation_ms", elapsed_ms)
if alert:
    logger.warning(f"Performance alert: {alert}")
```

### Best Practices

1. **Metric naming**: Use descriptive names with `_ms` suffix for time metrics
   - ✅ `app_startup_ms`, `definition_generation_ms`
   - ❌ `time`, `perf`, `metric1`

2. **Metadata**: Include relevant context
   - ✅ `{"model": "gpt-4", "version": "2.0"}`
   - ❌ `{}`

3. **Error handling**: Always wrap in try/except
   ```python
   try:
       tracker.track_metric(...)
   except Exception as e:
       logger.debug(f"Tracking error (non-critical): {e}")
   ```

4. **Don't track**:
   - User input processing time (too variable)
   - Network latency (out of our control)
   - Cold start scenarios (first run ever)

## Troubleshooting

### "Geen baseline beschikbaar"

**Cause**: Fewer than 5 measurements recorded.

**Solution**: Run the app 5+ times to generate baseline.

```bash
# Quick way to generate baseline
for i in {1..10}; do
    python -m streamlit run src/main.py --server.headless true &
    sleep 5
    pkill -f streamlit
done
```

### "Te weinig confidence"

**Cause**: Less than 10 samples, confidence < 50%.

**Solution**: Run the app more times or wait for more data.

### "Performance tracking fout"

**Cause**: Database issue or corrupted data.

**Solution**: Reset performance data:
```bash
python -m src.cli.performance_cli reset-all
```

**Warning**: This deletes all performance history!

### False Alerts

**Problem**: Alert triggered but performance seems fine.

**Causes**:
1. **System load**: Other apps consuming resources
2. **Cold cache**: First run after reboot
3. **Background updates**: OS updates, backups

**Solution**:
1. Check system load: `top` or Activity Monitor
2. Restart app a few times to warm up caches
3. If persistent, investigate code changes

## Maintenance

### Clean Old Data

```bash
# Remove baseline for specific metric
python -m src.cli.performance_cli delete-baseline app_startup_ms

# Reset all data (careful!)
python -m src.cli.performance_cli reset-all
```

### Database Location

Performance data is stored in:
```
data/definities.db
  ├── performance_metrics      (individual measurements)
  └── performance_baselines    (calculated baselines)
```

### Backup

```bash
# Backup performance data
cp data/definities.db data/definities.db.backup

# Restore
cp data/definities.db.backup data/definities.db
```

## Advanced Usage

### Custom Thresholds

Edit `src/monitoring/performance_tracker.py`:

```python
class PerformanceTracker:
    CRITICAL_THRESHOLD = 1.30  # 30% worse (more lenient)
    WARNING_THRESHOLD = 1.15   # 15% worse
```

### Different Window Size

```python
class PerformanceTracker:
    BASELINE_WINDOW = 50  # Use last 50 samples
    MIN_SAMPLES = 10      # Need 10 samples minimum
```

### Custom Database Location

```python
tracker = PerformanceTracker(db_path="/custom/path/metrics.db")
```

## Metrics Currently Tracked

| Metric | Description | Target | Critical |
|--------|-------------|--------|----------|
| `app_startup_ms` | App startup time | <250ms | >400ms |

**More metrics coming in Phase 2-4!**

## Performance Overhead

| Operation | Overhead | Impact |
|-----------|----------|--------|
| Track metric | ~1-2ms | Negligible |
| Update baseline | ~3-5ms | Negligible |
| Check regression | ~1ms | Negligible |
| **Total per startup** | **~5-10ms** | **<4% of 250ms startup** |

## Frequently Asked Questions

### Q: How long until I get alerts?

**A**: After 10 app starts (to reach 50% confidence).

### Q: Can I disable performance tracking?

**A**: Not currently, but overhead is <10ms per startup. You can ignore alerts in logs.

### Q: What if baseline keeps changing?

**A**: This is normal if your performance is gradually improving/degrading. The sliding window adapts automatically.

### Q: How do I track custom metrics?

**A**: See "Adding Custom Metrics" section above.

### Q: Can I export performance data?

**A**: Use SQL to export from database:
```bash
sqlite3 data/definities.db "SELECT * FROM performance_metrics" > metrics.csv
```

### Q: What's the difference between baseline and average?

**A**: Baseline uses **median** (middle value), average uses **mean** (sum/count). Median is more robust against outliers.

## Support

For issues or questions:
1. Check logs: `logs/app.log`
2. View full report: `docs/reports/performance-baseline-tracking-implementation.md`
3. Source code: `src/monitoring/performance_tracker.py`

---

**Last updated**: 2025-10-07
**Version**: Phase 1 (Basic Tracking)
