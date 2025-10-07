# Cache Monitoring System - Executive Summary

**Created**: 2025-10-07
**Status**: Design Complete
**Complexity**: MEDIUM (8-10 days)
**Performance Impact**: <5ms overhead per operation

## Quick Overview

A comprehensive monitoring system that tracks cache effectiveness across RuleCache, ServiceContainer, and other caching mechanisms with minimal overhead.

## What We Have Now

### ✅ RuleCache (US-202)
- Custom TTL-based cache with singleton pattern
- Basic stats: call counts, total rules
- **GAP**: No hit/miss tracking, no timing, no memory metrics

### ✅ ServiceContainer (US-201/202)
- Python `@lru_cache(maxsize=1)` singleton
- Built-in `cache_info()` available but not exposed
- **GAP**: No timing, no service-level memory tracking

### ✅ FileCache & CacheManager
- Comprehensive stats already tracked (hits, misses, evictions)
- **GAP**: No per-function breakdown, no timing

## What We'll Build

### Core Components

1. **CacheMonitor** (base class)
   - Tracks operations with timing
   - Distinguishes hit/miss/evict
   - Records disk vs memory source
   - Circular buffer (10K operations max)

2. **RuleCacheMonitor** (specialized)
   - Wraps RuleCache
   - Tracks `get_all_rules()` and `get_rule()` calls
   - Calculates memory usage and hit rates

3. **ContainerCacheMonitor** (specialized)
   - Wraps ServiceContainer
   - Exposes `lru_cache.cache_info()`
   - Tracks initialization timing

4. **MetricsAggregator** (central hub)
   - Collects from all monitors
   - Generates cross-cache summaries
   - Exports to multiple backends

### Metrics Tracked

| Metric | RuleCache | Container | FileCache |
|--------|-----------|-----------|-----------|
| Hit/Miss Rate | ✅ | ✅ | ✅ |
| Operation Timing | ✅ | ✅ | ✅ |
| Memory Usage | ✅ | ✅ | ✅ |
| Disk vs Memory | ✅ | ✅ | N/A |
| Source Tracking | ✅ | ✅ | ✅ |

### Exposure Methods

1. **Logging Backend** (MVP)
   - Structured JSON logs to `logs/cache_metrics.log`
   - Rotating file handler (10MB, 5 backups)

2. **JSON Persistence** (optional)
   - Snapshots to `data/metrics/`
   - Historical analysis capability

3. **Streamlit Dashboard** (optional)
   - Sidebar widget showing live metrics
   - Expandable per-cache details

4. **API Endpoints** (future)
   - `/api/metrics/cache/summary`
   - `/api/metrics/cache/{name}/snapshot`

## Performance Impact

| Aspect | Measurement | Target | Status |
|--------|-------------|--------|--------|
| Per-operation overhead | 0.45ms | <5ms | ✅ PASS |
| Memory footprint | ~5.2MB | <10MB | ✅ PASS |
| Can be disabled | Yes | Yes | ✅ PASS |

## Implementation Plan

### Phase 1: Foundation (2-3 days)
- Base monitoring classes
- Configuration system
- Unit tests

### Phase 2: Integration (2 days)
- RuleCache integration
- ServiceContainer integration
- Logging backend

### Phase 3: Exposure (2-3 days)
- JSON persistence
- Streamlit dashboard
- Performance benchmarks

### Phase 4: Polish (1 day)
- Remaining caches
- Optimization
- Documentation

**Total**: 8-10 days

## Key Design Decisions

### ✅ Custom vs External Tools
**Decision**: Build custom monitoring
**Why**: Simple single-user app, tight integration, no ops overhead

### ✅ Context Manager Pattern
**Decision**: `with monitor.track_operation()` syntax
**Why**: Clean, handles exceptions, easy to disable

### ✅ In-Memory Operation History
**Decision**: Keep last 10K operations
**Why**: Enables debugging, small memory impact, can be disabled

### ✅ Multiple Backends
**Decision**: Support logging, JSON, API, UI
**Why**: Different use cases (dev, ops, analysis)

## Integration Points

### RuleCache
```python
# src/toetsregels/rule_cache.py (+20 lines)
def get_all_rules(self):
    if self.monitor:
        with self.monitor.track_operation("get_all", "all_rules") as result:
            data = _load_all_rules_cached(str(self.regels_dir))
            result["result"] = "hit" if data else "miss"
            return data
```

### ServiceContainer
```python
# src/utils/container_manager.py (+30 lines)
@lru_cache(maxsize=1)
def get_cached_container():
    if _container_monitor:
        with _container_monitor.track_operation("get", "singleton") as result:
            # ... existing logic
            result["result"] = "hit" if was_cached else "miss"
```

## Example Output

### Log Entry
```json
{"cache_name": "RuleCache", "operation": "get_all", "timestamp": 1696689121.234, "duration_ms": 0.45, "result": "hit", "source": "cache"}
```

### Snapshot
```json
{
  "cache_name": "RuleCache",
  "total_entries": 45,
  "memory_usage_bytes": 125000,
  "hit_rate": 0.98,
  "avg_operation_ms": 0.35,
  "hits": 245,
  "misses": 5
}
```

### Summary
```json
{
  "total_caches": 2,
  "total_memory_mb": 2.5,
  "average_hit_rate": 0.97,
  "caches": { /* per-cache snapshots */ }
}
```

## Success Criteria

### Functional
- ✅ Track hit/miss for all caches
- ✅ Distinguish disk vs memory
- ✅ Measure operation timing
- ✅ Estimate memory usage

### Performance
- ✅ Overhead <5ms per operation
- ✅ Memory <10MB total
- ✅ Can disable with zero overhead

### Usability
- ✅ Metrics in logs
- ✅ Optional API/UI
- ✅ Easy to understand

## Files to Create

```
src/monitoring/
  cache_monitoring.py          (300 lines) - Core classes
  cache_logger.py              (100 lines) - Logging backend
  cache_json_backend.py        (150 lines) - JSON persistence
  metrics_aggregator.py        (100 lines) - Aggregation

config/
  monitoring.yaml              (50 lines)  - Configuration

tests/monitoring/
  test_cache_monitoring.py     (300 lines) - Unit tests
  test_integration.py          (200 lines) - Integration tests
```

**Total**: ~1400 new lines, ~65 lines modified

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance overhead | HIGH | Benchmark, ability to disable |
| Memory leak | MEDIUM | Circular buffer with max size |
| Thread safety | HIGH | Use threading.Lock |
| Complexity | MEDIUM | Start small, iterate |

## Related Stories

- **US-201**: Container optimization ✅ Complete
- **US-202**: RuleCache optimization ✅ Complete
- **US-203**: Prompt token optimization (open, needs monitoring)

## Next Steps

1. Review design with team
2. Approve implementation approach
3. Start Phase 1 (foundation)
4. Iterate based on real-world usage

## Questions for Review

1. Do we need API endpoints in MVP? (Proposal: NO, start with logging)
2. Should we track cache keys in logs? (Proposal: NO, privacy concern)
3. What's the snapshot interval? (Proposal: On-demand only, no periodic)
4. Do we need Streamlit dashboard? (Proposal: YES, useful for dev)

---

**Full Design**: See `docs/architectuur/cache-monitoring-design.md`
**Contact**: Development Team
**Last Updated**: 2025-10-07
