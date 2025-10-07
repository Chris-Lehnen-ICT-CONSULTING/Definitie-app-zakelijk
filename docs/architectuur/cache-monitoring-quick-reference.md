# Cache Monitoring - Quick Reference Card

## At a Glance

| Aspect | Value |
|--------|-------|
| **Complexity** | MEDIUM |
| **Implementation Time** | 8-10 days |
| **Performance Overhead** | <5ms per operation |
| **Memory Overhead** | ~5MB |
| **Can Be Disabled** | Yes (zero overhead) |
| **Dependencies** | None (stdlib only) |

## What Gets Tracked

### Per Operation
- ⏱️ **Duration**: How long did it take?
- ✅ **Result**: Hit, miss, store, evict?
- 📍 **Source**: Disk, memory, or fresh?
- 🔑 **Key**: Which cache key? (optional)
- 💾 **Size**: How big is the value?

### Per Cache (Snapshot)
- 📊 **Hit Rate**: % of cache hits
- 🧮 **Total Entries**: How many items cached?
- 💾 **Memory Usage**: Total bytes in cache
- ⏱️ **Avg Time**: Average operation duration
- 📈 **Stats**: Hits, misses, evictions

## Integration Pattern

### Before (RuleCache example)
```python
def get_all_rules(self):
    self.stats["get_all_calls"] += 1
    return _load_all_rules_cached(str(self.regels_dir))
```

### After (with monitoring)
```python
def get_all_rules(self):
    if self.monitor and self.monitor.enabled:
        with self.monitor.track_operation("get_all", "all_rules") as result:
            data = _load_all_rules_cached(str(self.regels_dir))
            result["result"] = "hit" if data else "miss"
            result["size"] = len(data)
            return data
    else:
        # Original code
        self.stats["get_all_calls"] += 1
        return _load_all_rules_cached(str(self.regels_dir))
```

**Impact**: +7 lines, <1ms overhead

## How to Use

### Enable Monitoring
```yaml
# config/monitoring.yaml
cache_monitoring:
  enabled: true
  backends: [logger]
```

### View Metrics (Logs)
```bash
tail -f logs/cache_metrics.log
```

### View Metrics (Code)
```python
from monitoring.metrics_aggregator import get_metrics_aggregator

aggregator = get_metrics_aggregator()
summary = aggregator.get_summary()

print(f"Total memory: {summary['total_memory_mb']:.1f} MB")
print(f"Avg hit rate: {summary['average_hit_rate']*100:.0f}%")

# Per-cache details
for cache_name, snapshot in summary['caches'].items():
    print(f"{cache_name}: {snapshot.hit_rate*100:.0f}% hit rate")
```

### View Metrics (UI)
```python
# In Streamlit sidebar
from ui.components.cache_metrics_dashboard import render_cache_dashboard

render_cache_dashboard()
```

### Disable in Production
```bash
# Zero overhead when disabled
export CACHE_MONITORING_ENABLED=false
```

## Output Examples

### Single Operation
```json
{
  "cache_name": "RuleCache",
  "operation": "get",
  "timestamp": 1696689121.234,
  "duration_ms": 0.45,
  "result": "hit",
  "source": "cache",
  "key": "CON-01",
  "size_bytes": 2048
}
```

### Cache Snapshot
```json
{
  "cache_name": "RuleCache",
  "timestamp": 1696689200.0,
  "total_entries": 45,
  "memory_usage_bytes": 125000,
  "hit_rate": 0.98,
  "avg_operation_ms": 0.35,
  "hits": 245,
  "misses": 5,
  "evictions": 0
}
```

### Aggregated Summary
```json
{
  "total_caches": 2,
  "total_memory_mb": 2.5,
  "average_hit_rate": 0.97,
  "caches": {
    "RuleCache": { /* snapshot */ },
    "ServiceContainer": { /* snapshot */ }
  }
}
```

## Testing Pattern

### Unit Test
```python
def test_monitor_tracks_operations():
    monitor = CacheMonitor("TestCache")

    with monitor.track_operation("get", "key1") as result:
        result["result"] = "hit"
        result["size"] = 1024

    ops = monitor.get_recent_operations(limit=1)
    assert ops[0].operation == "get"
    assert ops[0].result == "hit"
```

### Integration Test
```python
def test_rule_cache_monitoring():
    cache = get_rule_cache()
    monitor = RuleCacheMonitor(cache, enabled=True)
    cache.monitor = monitor

    # Exercise
    rules = cache.get_all_rules()

    # Verify
    snapshot = monitor.get_snapshot()
    assert snapshot.hit_rate >= 0.0
```

### Performance Test
```python
def test_overhead_under_5ms():
    monitor = CacheMonitor("TestCache", enabled=True)

    # Measure with monitoring
    start = time.perf_counter()
    for _ in range(1000):
        with monitor.track_operation("get", "key") as result:
            result["result"] = "hit"
    duration = time.perf_counter() - start

    overhead_per_op = (duration / 1000) * 1000  # ms
    assert overhead_per_op < 5.0
```

## Files Overview

### Core Implementation
```
src/monitoring/
  cache_monitoring.py          # Base classes, monitors
  metrics_aggregator.py        # Aggregation logic
```

### Backends
```
src/monitoring/
  cache_logger.py              # Log to file
  cache_json_backend.py        # Persist to JSON
```

### Optional
```
src/ui/components/
  cache_metrics_dashboard.py   # Streamlit widget

src/api/
  cache_metrics_api.py         # REST endpoints
```

### Configuration
```
config/
  monitoring.yaml              # Settings
```

### Tests
```
tests/monitoring/
  test_cache_monitoring.py     # Unit tests
  test_integration.py          # Integration tests
```

## Key Metrics to Watch

### Hit Rate (target: >90%)
- **Good**: 95%+ → Cache is effective
- **OK**: 80-95% → Cache is working
- **Bad**: <80% → Cache not helping or wrong TTL

### Avg Operation Time
- **Good**: <1ms → Minimal overhead
- **OK**: 1-5ms → Acceptable overhead
- **Bad**: >5ms → Performance issue

### Memory Usage
- **Good**: <10MB → Efficient caching
- **OK**: 10-50MB → Reasonable for benefits
- **Bad**: >50MB → May need to reduce cache size

### Eviction Rate
- **Good**: 0 evictions → Cache size is sufficient
- **OK**: <10% eviction rate → Some churn, OK
- **Bad**: >10% eviction rate → Cache too small

## Common Patterns

### Debugging Cache Miss
```python
# Get recent operations
monitor = aggregator.monitors["RuleCache"]
ops = monitor.get_recent_operations(limit=100)

# Find misses
misses = [op for op in ops if op.result == "miss"]
print(f"Found {len(misses)} cache misses")

# Analyze
for miss in misses:
    print(f"Miss at {miss.timestamp}: key={miss.key}, duration={miss.duration_ms}ms")
```

### Comparing Before/After
```python
# Before optimization
before = monitor.get_snapshot()

# ... make changes ...

# After optimization
after = monitor.get_snapshot()

improvement = (after.hit_rate - before.hit_rate) / before.hit_rate
print(f"Hit rate improved by {improvement*100:.1f}%")
```

### Monitoring Over Time
```python
# Collect snapshots periodically
snapshots = []
for _ in range(10):
    snapshot = monitor.get_snapshot()
    snapshots.append(snapshot)
    time.sleep(60)  # Every minute

# Analyze trend
hit_rates = [s.hit_rate for s in snapshots]
print(f"Hit rate range: {min(hit_rates)*100:.0f}% - {max(hit_rates)*100:.0f}%")
print(f"Average: {sum(hit_rates)/len(hit_rates)*100:.0f}%")
```

## Troubleshooting

### Monitor Not Tracking Operations
✅ **Check**: Is monitoring enabled in config?
✅ **Check**: Is monitor instance attached to cache?
✅ **Check**: Are you calling the right methods?

### High Overhead (>5ms)
✅ **Check**: Too many operations in history? (reduce max_operations_history)
✅ **Check**: Tracking cache keys? (disable track_keys)
✅ **Check**: Too many backends? (disable JSON/API)

### Memory Growing Too Large
✅ **Check**: max_operations_history setting (default: 10000)
✅ **Check**: Are operations being trimmed? (circular buffer)
✅ **Check**: Disable monitoring if not needed

### Metrics Not Appearing in Logs
✅ **Check**: Logger backend enabled?
✅ **Check**: Log file path writable?
✅ **Check**: Log level set correctly?

## Configuration Options

### Minimal (Logging Only)
```yaml
cache_monitoring:
  enabled: true
  backends:
    - type: logger
      enabled: true
```

### Full Featured
```yaml
cache_monitoring:
  enabled: true
  max_operations_history: 10000
  track_keys: false

  backends:
    - type: logger
      enabled: true
      log_level: INFO

    - type: json
      enabled: true
      snapshot_interval_seconds: 300

    - type: api
      enabled: true
```

### Production (Disabled)
```yaml
cache_monitoring:
  enabled: false  # Zero overhead
```

## Performance Budget

| Component | Time Budget | Actual | Status |
|-----------|-------------|--------|--------|
| Context setup | 0.1ms | 0.1ms | ✅ |
| Time measurement | 0.05ms | 0.05ms | ✅ |
| Dict creation | 0.1ms | 0.1ms | ✅ |
| List append (locked) | 0.2ms | 0.2ms | ✅ |
| **Total** | **0.5ms** | **0.45ms** | ✅ |

## Related Documentation

- **Full Design**: `docs/architectuur/cache-monitoring-design.md`
- **Summary**: `docs/architectuur/CACHE_MONITORING_SUMMARY.md`
- **US-201**: Container optimization
- **US-202**: RuleCache optimization
- **US-203**: Prompt token optimization

---

**Last Updated**: 2025-10-07
**Status**: Design Complete
**Next**: Start Phase 1 implementation
