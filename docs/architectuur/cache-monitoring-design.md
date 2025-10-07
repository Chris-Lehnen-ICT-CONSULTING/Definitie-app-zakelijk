---
title: Cache Monitoring System - Architectural Design
epic: EPIC-026
related_stories: [US-201, US-202, US-203]
status: design
created: 2025-10-07
last_verified: 2025-10-07
owner: development-team
applies_to: definitie-app@current
tags: [architecture, monitoring, performance, caching]
---

# Cache Monitoring System - Architectural Design

## Executive Summary

This document describes the architectural design for a comprehensive cache monitoring system that tracks RuleCache, ServiceContainer, and other caching mechanisms in the DefinitieAgent application. The system provides visibility into cache effectiveness, memory usage, and performance metrics with minimal overhead (<5ms).

## 1. Current Cache Implementations

### 1.1 RuleCache (`src/toetsregels/rule_cache.py`)
**Type**: Custom decorator-based cache with TTL
**Backend**: `utils.cache.cached` decorator (TTL: 3600s)
**Scope**: Process-local, singleton pattern
**Current Metrics**:
- Basic call counters (`get_all_calls`, `get_single_calls`)
- Total rules cached
- Cache directory info

**Strengths**:
- ✅ Already has singleton pattern
- ✅ Basic stats tracking in place
- ✅ Uses global cache facade

**Gaps**:
- ❌ No hit/miss tracking (always reports "cache hits")
- ❌ No disk vs memory distinction
- ❌ No timing metrics
- ❌ No memory usage tracking

### 1.2 ServiceContainer (`src/utils/container_manager.py`)
**Type**: Python `@lru_cache(maxsize=1)` decorator
**Scope**: Module-level singleton
**Current Metrics**:
- Built-in `cache_info()` available: hits, misses, maxsize, currsize
- `get_container_stats()`: service count, service names, config

**Strengths**:
- ✅ Uses standard library `lru_cache` with built-in metrics
- ✅ Already has stats function
- ✅ Initialization count tracking

**Gaps**:
- ❌ `cache_info()` not exposed to monitoring
- ❌ No timing for service initialization
- ❌ No memory usage per service

### 1.3 General Cache (`src/utils/cache.py`)
**Type**: Dual system
1. **FileCache**: File-based pickle cache with metadata
2. **CacheManager**: In-memory OrderedDict with LRU + file persistence
3. **@cached decorator**: Wrapper around both

**Current Metrics**:
- Global stats: hits, misses, hit_rate, evictions
- FileCache: entries, total_size_bytes, oldest/newest entry
- CacheManager: hits, misses, hit_rate, evictions, entries

**Strengths**:
- ✅ Comprehensive stats already tracked
- ✅ Thread-safe implementation
- ✅ Both memory and disk tracking

**Gaps**:
- ❌ No per-function breakdown
- ❌ No timing per operation
- ❌ Stats are global, hard to attribute

## 2. Proposed Monitoring Architecture

### 2.1 Design Principles

1. **Non-invasive**: <5ms overhead per cache operation
2. **Pluggable**: Can be disabled in production via config
3. **Structured**: Metrics follow consistent schema
4. **Actionable**: Expose data for decision-making
5. **Compatible**: Works with existing cache implementations

### 2.2 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Cache Monitoring Layer                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   RuleCache  │  │  Container   │  │   General    │      │
│  │   Monitor    │  │   Monitor    │  │   Cache      │      │
│  │              │  │              │  │   Monitor    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                    ┌───────▼────────┐                        │
│                    │  Metrics       │                        │
│                    │  Aggregator    │                        │
│                    └───────┬────────┘                        │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐             │
│         │                  │                  │             │
│  ┌──────▼──────┐  ┌────────▼───────┐  ┌──────▼──────┐     │
│  │   Logger    │  │   JSON File    │  │   API       │     │
│  │   Backend   │  │   Backend      │  │   Endpoint  │     │
│  └─────────────┘  └────────────────┘  └─────────────┘     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Core Components

#### 2.3.1 CacheMetrics (Data Model)
```python
@dataclass
class CacheOperation:
    """Single cache operation metrics."""
    cache_name: str           # "RuleCache", "ServiceContainer", "FileCache"
    operation: str            # "get", "set", "delete", "clear"
    timestamp: float          # Unix timestamp
    duration_ms: float        # Operation duration
    result: str               # "hit", "miss", "store", "evict"
    key: str | None = None   # Cache key (optional, for debugging)
    size_bytes: int | None = None  # Size of cached value
    source: str | None = None # "disk", "memory", "fresh"

@dataclass
class CacheSnapshot:
    """Point-in-time cache state."""
    cache_name: str
    timestamp: float
    total_entries: int
    memory_usage_bytes: int
    hit_rate: float
    avg_operation_ms: float
    hits: int
    misses: int
    evictions: int
    custom_metrics: Dict[str, Any]  # Cache-specific metrics
```

#### 2.3.2 CacheMonitor (Base Class)
```python
class CacheMonitor:
    """Base monitoring class for all cache types."""

    def __init__(self, cache_name: str, enabled: bool = True):
        self.cache_name = cache_name
        self.enabled = enabled
        self.operations: List[CacheOperation] = []
        self._lock = threading.Lock()

    @contextmanager
    def track_operation(
        self,
        operation: str,
        key: str | None = None
    ) -> Generator[Dict, None, None]:
        """Context manager to track cache operation timing."""
        if not self.enabled:
            yield {}
            return

        start = time.perf_counter()
        result_data = {}

        try:
            yield result_data
        finally:
            duration = (time.perf_counter() - start) * 1000

            with self._lock:
                self.operations.append(CacheOperation(
                    cache_name=self.cache_name,
                    operation=operation,
                    timestamp=time.time(),
                    duration_ms=duration,
                    result=result_data.get("result", "unknown"),
                    key=key,
                    size_bytes=result_data.get("size"),
                    source=result_data.get("source")
                ))

                # Keep last 10000 operations only (memory limit)
                if len(self.operations) > 10000:
                    self.operations = self.operations[-5000:]

    def get_snapshot(self) -> CacheSnapshot:
        """Get current cache statistics."""
        raise NotImplementedError

    def get_recent_operations(self, limit: int = 100) -> List[CacheOperation]:
        """Get recent operations for debugging."""
        with self._lock:
            return self.operations[-limit:]
```

#### 2.3.3 RuleCacheMonitor
```python
class RuleCacheMonitor(CacheMonitor):
    """Monitor for RuleCache operations."""

    def __init__(self, rule_cache: RuleCache, enabled: bool = True):
        super().__init__("RuleCache", enabled)
        self.cache = rule_cache

    def get_snapshot(self) -> CacheSnapshot:
        """Generate snapshot of RuleCache state."""
        stats = self.cache.get_stats()
        all_rules = self.cache.get_all_rules()

        # Calculate memory usage (approximate)
        memory_bytes = sum(
            len(json.dumps(rule, default=str).encode())
            for rule in all_rules.values()
        )

        # Calculate hit rate from operations
        recent_ops = self.get_recent_operations(limit=1000)
        hits = sum(1 for op in recent_ops if op.result == "hit")
        misses = sum(1 for op in recent_ops if op.result == "miss")
        total = hits + misses
        hit_rate = hits / total if total > 0 else 0.0

        # Average operation time
        avg_time = (
            sum(op.duration_ms for op in recent_ops) / len(recent_ops)
            if recent_ops else 0.0
        )

        return CacheSnapshot(
            cache_name="RuleCache",
            timestamp=time.time(),
            total_entries=len(all_rules),
            memory_usage_bytes=memory_bytes,
            hit_rate=hit_rate,
            avg_operation_ms=avg_time,
            hits=hits,
            misses=misses,
            evictions=0,  # RuleCache doesn't evict
            custom_metrics={
                "get_all_calls": stats["get_all_calls"],
                "get_single_calls": stats["get_single_calls"],
                "cache_dir": stats["cache_dir"]
            }
        )
```

#### 2.3.4 ContainerCacheMonitor
```python
class ContainerCacheMonitor(CacheMonitor):
    """Monitor for ServiceContainer caching."""

    def __init__(self, enabled: bool = True):
        super().__init__("ServiceContainer", enabled)

    def get_snapshot(self) -> CacheSnapshot:
        """Generate snapshot of container cache state."""
        # Get lru_cache stats
        cache_info = get_cached_container.cache_info()

        # Get container stats
        container_stats = get_container_stats()

        # Estimate memory usage (rough)
        service_count = container_stats.get("service_count", 0)
        memory_bytes = service_count * 50000  # ~50KB per service (estimate)

        # Calculate metrics
        total = cache_info.hits + cache_info.misses
        hit_rate = cache_info.hits / total if total > 0 else 0.0

        recent_ops = self.get_recent_operations(limit=100)
        avg_time = (
            sum(op.duration_ms for op in recent_ops) / len(recent_ops)
            if recent_ops else 0.0
        )

        return CacheSnapshot(
            cache_name="ServiceContainer",
            timestamp=time.time(),
            total_entries=cache_info.currsize,
            memory_usage_bytes=memory_bytes,
            hit_rate=hit_rate,
            avg_operation_ms=avg_time,
            hits=cache_info.hits,
            misses=cache_info.misses,
            evictions=0,  # maxsize=1, no evictions
            custom_metrics={
                "maxsize": cache_info.maxsize,
                "service_count": service_count,
                "services": container_stats.get("services", []),
                "initialization_count": getattr(
                    get_cached_container(),
                    "_initialization_count",
                    0
                )
            }
        )
```

#### 2.3.5 MetricsAggregator
```python
class MetricsAggregator:
    """Central aggregator for all cache metrics."""

    def __init__(self):
        self.monitors: Dict[str, CacheMonitor] = {}
        self._enabled = True

    def register_monitor(self, monitor: CacheMonitor):
        """Register a cache monitor."""
        self.monitors[monitor.cache_name] = monitor

    def get_all_snapshots(self) -> List[CacheSnapshot]:
        """Get snapshots from all monitors."""
        return [
            monitor.get_snapshot()
            for monitor in self.monitors.values()
        ]

    def get_summary(self) -> Dict[str, Any]:
        """Get aggregated summary of all caches."""
        snapshots = self.get_all_snapshots()

        total_memory = sum(s.memory_usage_bytes for s in snapshots)
        total_entries = sum(s.total_entries for s in snapshots)
        avg_hit_rate = (
            sum(s.hit_rate for s in snapshots) / len(snapshots)
            if snapshots else 0.0
        )

        return {
            "timestamp": time.time(),
            "total_caches": len(snapshots),
            "total_memory_bytes": total_memory,
            "total_memory_mb": total_memory / (1024 * 1024),
            "total_entries": total_entries,
            "average_hit_rate": round(avg_hit_rate, 2),
            "caches": {s.cache_name: s for s in snapshots}
        }
```

## 3. Integration Points

### 3.1 RuleCache Integration
**File**: `src/toetsregels/rule_cache.py`

```python
# Add to RuleCache.__init__
self.monitor = None  # Will be set by monitoring system

# Modify get_all_rules()
def get_all_rules(self) -> dict[str, dict[str, Any]]:
    if self.monitor and self.monitor.enabled:
        with self.monitor.track_operation("get_all", "all_rules") as result:
            cached_data = _load_all_rules_cached(str(self.regels_dir))
            result["result"] = "hit" if cached_data else "miss"
            result["size"] = len(cached_data)
            result["source"] = "cache" if cached_data else "disk"
            return cached_data
    else:
        # Original behavior
        self.stats["get_all_calls"] += 1
        return _load_all_rules_cached(str(self.regels_dir))
```

**Impact**: +2 lines per method, <1ms overhead

### 3.2 ServiceContainer Integration
**File**: `src/utils/container_manager.py`

```python
# Add module-level monitor
_container_monitor: ContainerCacheMonitor | None = None

def get_cached_container() -> ServiceContainer:
    global _container_monitor

    if _container_monitor and _container_monitor.enabled:
        with _container_monitor.track_operation("get", "singleton") as result:
            # Check if cached
            info = get_cached_container.cache_info()
            was_cached = info.currsize > 0

            # Original logic here (moved to inner function)
            container = _get_cached_container_impl()

            result["result"] = "hit" if was_cached else "miss"
            result["source"] = "memory" if was_cached else "fresh"
            return container
    else:
        # Original implementation
        return _get_cached_container_impl()
```

**Impact**: +5 lines, <1ms overhead

### 3.3 General Cache Integration
**File**: `src/utils/cache.py`

The `@cached` decorator already tracks hits/misses globally. Enhance it:

```python
# Add optional monitor parameter to cached decorator
def cached(
    ttl: int | None = None,
    cache_key_func: Callable | None = None,
    cache_manager: Optional["CacheManager"] = None,
    monitor: Optional[CacheMonitor] = None,  # NEW
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = # ... generate key

            # Track operation if monitor enabled
            if monitor and monitor.enabled:
                with monitor.track_operation("get", cache_key) as result:
                    cached_result = backend_get(cache_key)
                    if cached_result is not None:
                        result["result"] = "hit"
                        result["source"] = "cache"
                        _stats["hits"] += 1
                        return cached_result

                    # Cache miss
                    result["result"] = "miss"
                    _stats["misses"] += 1
                    value = func(*args, **kwargs)
                    backend_set(cache_key, value, ttl)
                    return value
            else:
                # Original behavior
                # ... existing code
```

**Impact**: +3 lines, <1ms overhead

## 4. Metrics Data Model

### 4.1 Core Metrics Schema

```yaml
cache_operation:
  cache_name: string          # "RuleCache", "ServiceContainer", etc.
  operation: enum             # get, set, delete, clear
  timestamp: float            # Unix timestamp
  duration_ms: float          # Operation duration
  result: enum                # hit, miss, store, evict
  key: string?                # Optional cache key
  size_bytes: int?            # Size of value
  source: enum?               # disk, memory, fresh

cache_snapshot:
  cache_name: string
  timestamp: float
  total_entries: int
  memory_usage_bytes: int
  hit_rate: float             # 0.0 - 1.0
  avg_operation_ms: float
  hits: int
  misses: int
  evictions: int
  custom_metrics: object      # Cache-specific data
```

### 4.2 Metrics Collection Points

| Cache | Get | Set | Delete | Clear | Snapshot |
|-------|-----|-----|--------|-------|----------|
| RuleCache | ✅ | ❌ | ❌ | ✅ | ✅ |
| ServiceContainer | ✅ | ❌ | ❌ | ✅ | ✅ |
| FileCache | ✅ | ✅ | ✅ | ✅ | ✅ |
| CacheManager | ✅ | ✅ | ✅ | ✅ | ✅ |

## 5. Metrics Exposure

### 5.1 Logging Backend
**File**: `src/monitoring/cache_logger.py`

```python
class CacheMetricsLogger:
    """Log cache metrics to structured logs."""

    def __init__(self, log_dir: Path = Path("logs")):
        self.log_dir = log_dir
        self.logger = logging.getLogger("cache_metrics")

        # Create rotating file handler
        handler = RotatingFileHandler(
            log_dir / "cache_metrics.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(message)s')
        )
        self.logger.addHandler(handler)

    def log_operation(self, operation: CacheOperation):
        """Log single cache operation."""
        self.logger.info(json.dumps(asdict(operation)))

    def log_snapshot(self, snapshot: CacheSnapshot):
        """Log cache snapshot."""
        self.logger.info(json.dumps(asdict(snapshot)))
```

**Output Format**:
```json
{"cache_name": "RuleCache", "operation": "get", "timestamp": 1696789200.123, "duration_ms": 0.45, "result": "hit", "source": "cache"}
{"cache_name": "ServiceContainer", "operation": "get", "timestamp": 1696789201.456, "duration_ms": 245.2, "result": "miss", "source": "fresh"}
```

### 5.2 JSON File Backend
**File**: `src/monitoring/cache_json_backend.py`

```python
class CacheMetricsJSONBackend:
    """Persist cache metrics to JSON files."""

    def __init__(self, data_dir: Path = Path("data/metrics")):
        self.data_dir = data_dir
        data_dir.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, snapshot: CacheSnapshot):
        """Save snapshot to JSON file."""
        filename = (
            f"cache_snapshot_{snapshot.cache_name}_"
            f"{int(snapshot.timestamp)}.json"
        )

        with open(self.data_dir / filename, 'w') as f:
            json.dump(asdict(snapshot), f, indent=2)

    def get_snapshots_since(
        self,
        cache_name: str,
        since: float
    ) -> List[CacheSnapshot]:
        """Load snapshots for analysis."""
        pattern = f"cache_snapshot_{cache_name}_*.json"
        snapshots = []

        for file in sorted(self.data_dir.glob(pattern)):
            timestamp = int(file.stem.split('_')[-1])
            if timestamp >= since:
                with open(file) as f:
                    data = json.load(f)
                    snapshots.append(CacheSnapshot(**data))

        return snapshots
```

### 5.3 API Endpoint
**File**: `src/api/cache_metrics_api.py` (new)

```python
# Simple Flask/FastAPI endpoint for metrics
@app.get("/api/metrics/cache/summary")
def get_cache_summary():
    """Get aggregated cache metrics."""
    aggregator = get_metrics_aggregator()
    return aggregator.get_summary()

@app.get("/api/metrics/cache/{cache_name}/snapshot")
def get_cache_snapshot(cache_name: str):
    """Get specific cache snapshot."""
    aggregator = get_metrics_aggregator()
    monitor = aggregator.monitors.get(cache_name)

    if not monitor:
        return {"error": "Cache not found"}, 404

    return monitor.get_snapshot()

@app.get("/api/metrics/cache/{cache_name}/operations")
def get_recent_operations(cache_name: str, limit: int = 100):
    """Get recent operations for debugging."""
    aggregator = get_metrics_aggregator()
    monitor = aggregator.monitors.get(cache_name)

    if not monitor:
        return {"error": "Cache not found"}, 404

    operations = monitor.get_recent_operations(limit)
    return [asdict(op) for op in operations]
```

**Note**: This requires adding a minimal API server. Can start with logging/JSON only.

### 5.4 Streamlit UI Dashboard (Optional)
**File**: `src/ui/components/cache_metrics_dashboard.py`

```python
def render_cache_dashboard():
    """Render cache metrics in Streamlit sidebar."""
    st.sidebar.markdown("### 📊 Cache Metrics")

    aggregator = get_metrics_aggregator()
    summary = aggregator.get_summary()

    # Overall stats
    st.sidebar.metric(
        "Total Memory",
        f"{summary['total_memory_mb']:.1f} MB"
    )
    st.sidebar.metric(
        "Avg Hit Rate",
        f"{summary['average_hit_rate']*100:.1f}%"
    )

    # Per-cache expander
    with st.sidebar.expander("Cache Details"):
        for cache_name, snapshot in summary['caches'].items():
            st.markdown(f"**{cache_name}**")
            cols = st.columns(2)
            cols[0].metric("Entries", snapshot.total_entries)
            cols[1].metric("Hit Rate", f"{snapshot.hit_rate*100:.0f}%")
            st.metric("Avg Time", f"{snapshot.avg_operation_ms:.2f}ms")
```

## 6. Configuration

### 6.1 Config File
**File**: `config/monitoring.yaml`

```yaml
cache_monitoring:
  enabled: true

  # Backends
  backends:
    - type: logger
      enabled: true
      log_level: INFO
      log_file: logs/cache_metrics.log

    - type: json
      enabled: false  # Disabled by default (large files)
      data_dir: data/metrics
      snapshot_interval_seconds: 300  # Every 5 minutes

    - type: api
      enabled: false  # Requires API server

  # Performance
  max_operations_history: 10000  # Keep last N operations
  track_keys: false  # Don't log cache keys (privacy)

  # Caches to monitor
  caches:
    RuleCache:
      enabled: true
      track_timing: true
      track_memory: true

    ServiceContainer:
      enabled: true
      track_timing: true
      track_memory: true

    FileCache:
      enabled: false  # Too noisy

    CacheManager:
      enabled: false
```

### 6.2 Environment Variables
```bash
CACHE_MONITORING_ENABLED=true
CACHE_MONITORING_LOG_LEVEL=INFO
CACHE_MONITORING_BACKENDS=logger,json
```

## 7. Performance Impact

### 7.1 Overhead Analysis

| Component | Operation | Overhead | Frequency | Total Impact |
|-----------|-----------|----------|-----------|--------------|
| Context Manager Setup | per operation | ~0.1ms | High | Low |
| Time Measurement | per operation | ~0.05ms | High | Low |
| Dict Creation | per operation | ~0.1ms | High | Low |
| List Append (locked) | per operation | ~0.2ms | High | Low |
| Snapshot Generation | per snapshot | ~5-10ms | Low (on-demand) | Negligible |
| **Total per operation** | | **~0.45ms** | | **<1ms** ✅ |

### 7.2 Memory Impact

| Component | Memory | Justification |
|-----------|--------|---------------|
| CacheOperation (10K) | ~5MB | Circular buffer, auto-trim |
| Monitors (3 instances) | ~100KB | Minimal overhead |
| Aggregator | ~50KB | Single instance |
| **Total** | **~5.2MB** | Acceptable ✅ |

### 7.3 Disable in Production
If needed, monitoring can be fully disabled:
- Set `CACHE_MONITORING_ENABLED=false`
- Overhead becomes zero (early return in context manager)
- No memory allocated for operations list

## 8. Implementation Phases

### Phase 1: Foundation (Week 1, 2-3 days)
**Complexity**: SIMPLE
- [ ] Create `src/monitoring/cache_monitoring.py` with base classes
- [ ] Define `CacheOperation` and `CacheSnapshot` dataclasses
- [ ] Implement `CacheMonitor` base class
- [ ] Add configuration loading
- [ ] Write unit tests

**Deliverables**:
- Base monitoring framework
- Configuration system
- 80% test coverage

### Phase 2: Integration (Week 1, 2 days)
**Complexity**: SIMPLE-MEDIUM
- [ ] Integrate with RuleCache
- [ ] Integrate with ServiceContainer
- [ ] Create `MetricsAggregator`
- [ ] Add logging backend
- [ ] Test end-to-end

**Deliverables**:
- Working monitoring for 2 main caches
- Structured logs with metrics
- Integration tests

### Phase 3: Exposure (Week 2, 2-3 days)
**Complexity**: MEDIUM
- [ ] JSON persistence backend
- [ ] Streamlit dashboard component
- [ ] Performance benchmarking
- [ ] Documentation

**Deliverables**:
- Multiple backends working
- UI dashboard (optional)
- Performance report
- User documentation

### Phase 4: Polish (Week 2, 1 day)
**Complexity**: SIMPLE
- [ ] Add remaining cache types (FileCache, CacheManager)
- [ ] Performance optimization
- [ ] Production testing
- [ ] Monitoring alerts (if needed)

**Deliverables**:
- Complete system
- Production-ready
- Monitoring documentation

**Total Estimate**: 8-10 days for full implementation

## 9. Files to Create/Modify

### New Files
```
src/
  monitoring/
    __init__.py
    cache_monitoring.py          # Core monitoring classes (300 lines)
    cache_logger.py              # Logging backend (100 lines)
    cache_json_backend.py        # JSON persistence (150 lines)
    metrics_aggregator.py        # Aggregation logic (100 lines)
  api/
    cache_metrics_api.py         # Optional API endpoints (100 lines)
  ui/
    components/
      cache_metrics_dashboard.py # Optional UI (50 lines)

config/
  monitoring.yaml                # Configuration (50 lines)

tests/
  monitoring/
    test_cache_monitoring.py     # Unit tests (300 lines)
    test_integration.py          # Integration tests (200 lines)
```

### Modified Files
```
src/toetsregels/rule_cache.py      # +20 lines (monitor integration)
src/utils/container_manager.py     # +30 lines (monitor integration)
src/utils/cache.py                  # +10 lines (monitor parameter)
src/services/container.py           # +5 lines (monitor init)
```

**Total**: ~1400 lines of new code, ~65 lines of modifications

## 10. Testing Strategy

### 10.1 Unit Tests
```python
def test_cache_monitor_tracks_operations():
    """Test that operations are tracked correctly."""
    monitor = CacheMonitor("TestCache")

    with monitor.track_operation("get", "key1") as result:
        result["result"] = "hit"
        result["size"] = 1024

    ops = monitor.get_recent_operations(limit=1)
    assert len(ops) == 1
    assert ops[0].operation == "get"
    assert ops[0].result == "hit"
    assert ops[0].duration_ms > 0

def test_monitor_respects_disabled_flag():
    """Test that disabled monitor has zero overhead."""
    monitor = CacheMonitor("TestCache", enabled=False)

    with monitor.track_operation("get", "key1") as result:
        result["result"] = "hit"

    # Should not track when disabled
    assert len(monitor.operations) == 0
```

### 10.2 Integration Tests
```python
def test_rule_cache_monitoring_end_to_end():
    """Test RuleCache monitoring integration."""
    # Setup
    cache = get_rule_cache()
    monitor = RuleCacheMonitor(cache, enabled=True)
    cache.monitor = monitor

    # Exercise
    rules = cache.get_all_rules()
    rule = cache.get_rule("CON-01")

    # Verify
    snapshot = monitor.get_snapshot()
    assert snapshot.total_entries > 0
    assert snapshot.hits >= 0

    ops = monitor.get_recent_operations(limit=10)
    assert len(ops) >= 2  # At least get_all and get_rule
```

### 10.3 Performance Tests
```python
def test_monitoring_overhead_under_5ms():
    """Verify monitoring overhead is <5ms per operation."""
    monitor = CacheMonitor("TestCache", enabled=True)

    # Measure without monitoring
    start = time.perf_counter()
    for _ in range(1000):
        cache.get("test_key")
    baseline = time.perf_counter() - start

    # Measure with monitoring
    start = time.perf_counter()
    for _ in range(1000):
        with monitor.track_operation("get", "test_key") as result:
            cache.get("test_key")
            result["result"] = "hit"
    monitored = time.perf_counter() - start

    overhead_per_op = (monitored - baseline) / 1000 * 1000  # ms
    assert overhead_per_op < 5.0, f"Overhead {overhead_per_op}ms exceeds 5ms"
```

## 11. Success Metrics

### 11.1 Functional Success
- ✅ Can track hit/miss rates for all caches
- ✅ Can distinguish disk vs memory access
- ✅ Can measure operation timing
- ✅ Can estimate memory usage
- ✅ Can export metrics for analysis

### 11.2 Performance Success
- ✅ Overhead <5ms per cache operation
- ✅ Memory footprint <10MB
- ✅ No impact on cache effectiveness
- ✅ Can be disabled in production with zero overhead

### 11.3 Usability Success
- ✅ Metrics accessible via logs
- ✅ Metrics accessible via API (optional)
- ✅ Metrics visible in UI (optional)
- ✅ Easy to understand and act on

## 12. Future Enhancements

### 12.1 Phase 2 Features (Post-MVP)
- **Alerting**: Send alerts when hit rate drops below threshold
- **Trends**: Track metrics over time, detect anomalies
- **Comparison**: Compare cache effectiveness across deployments
- **Optimization**: Suggest TTL/size adjustments based on metrics

### 12.2 Advanced Features
- **Distributed Tracing**: Track cache operations across services
- **Heatmaps**: Visualize cache access patterns
- **Cost Tracking**: Estimate cost savings from caching
- **A/B Testing**: Compare different cache configurations

## 13. Dependencies

### Required
- Python 3.11+ (already available)
- `threading` (stdlib)
- `time` (stdlib)
- `dataclasses` (stdlib)
- `json` (stdlib)

### Optional
- `tiktoken` (for token counting - not yet available, see US-203)
- Flask/FastAPI (for API endpoints - not required for MVP)
- Streamlit (already available for UI dashboard)

## 14. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Performance overhead >5ms | HIGH | LOW | Thorough benchmarking, ability to disable |
| Memory leak from history | MEDIUM | MEDIUM | Circular buffer with max size |
| Thread safety issues | HIGH | LOW | Use threading.Lock for shared state |
| Integration complexity | MEDIUM | LOW | Start with 1-2 caches, expand gradually |
| Config complexity | LOW | LOW | Sensible defaults, simple on/off flag |

## 15. Related Work

### 15.1 Existing Infrastructure
- `src/utils/cache.py`: Already has stats tracking
- `src/services/monitoring.py`: Minimal stub (can be extended)
- `logs/`: Directory exists for log output

### 15.2 Related Stories
- **US-201**: ServiceContainer optimization (completed)
- **US-202**: RuleCache optimization (completed)
- **US-203**: Prompt token optimization (open, needs monitoring)

## 16. Decision Log

### Why NOT use external monitoring tools (Prometheus, Grafana)?
**Decision**: Build custom monitoring
**Rationale**:
- Simple single-user application, not distributed system
- Want tight integration with existing code
- No operational overhead of running external services
- Faster to implement custom solution
- Can evolve as needs change

### Why track operations in memory instead of just aggregates?
**Decision**: Keep last 10K operations in memory
**Rationale**:
- Enables debugging of specific cache misses
- Allows calculation of windowed metrics (last hour, etc.)
- Memory impact is small (~5MB)
- Can be disabled if not needed
- Provides operational visibility

### Why use context manager for timing?
**Decision**: `with monitor.track_operation()` pattern
**Rationale**:
- Ensures timing even if exception occurs
- Clean syntax, readable
- Separates monitoring from business logic
- Easy to disable (early return)
- Standard Python pattern

## 17. Conclusion

This architectural design provides a comprehensive, low-overhead cache monitoring system that:

1. **Tracks all major caches**: RuleCache, ServiceContainer, FileCache, CacheManager
2. **Provides actionable metrics**: hit rates, timing, memory, source tracking
3. **Has minimal impact**: <5ms overhead, <10MB memory
4. **Is configurable**: Can disable entirely in production
5. **Is extensible**: Easy to add new caches or backends
6. **Is testable**: Clear interfaces for unit and integration tests

**Implementation Complexity**: MEDIUM (8-10 days)
**Performance Impact**: <5ms per operation, <10MB memory
**Maintenance Burden**: LOW (well-abstracted, simple interfaces)

**Recommendation**: Proceed with Phase 1 (foundation) to prove out the design, then iterate based on real-world usage patterns.

---

## Appendix A: Example Metrics Output

### Logging Output
```
2025-10-07 14:32:01 - {"cache_name": "RuleCache", "operation": "get_all", "timestamp": 1696689121.234, "duration_ms": 0.45, "result": "hit", "source": "cache"}
2025-10-07 14:32:01 - {"cache_name": "RuleCache", "operation": "get", "timestamp": 1696689121.567, "duration_ms": 0.12, "result": "hit", "key": "CON-01", "source": "cache"}
2025-10-07 14:32:05 - {"cache_name": "ServiceContainer", "operation": "get", "timestamp": 1696689125.890, "duration_ms": 245.3, "result": "miss", "source": "fresh"}
```

### JSON Snapshot
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
  "evictions": 0,
  "custom_metrics": {
    "get_all_calls": 12,
    "get_single_calls": 238,
    "cache_dir": "/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels"
  }
}
```

### API Response
```json
{
  "timestamp": 1696689300.0,
  "total_caches": 2,
  "total_memory_bytes": 2625000,
  "total_memory_mb": 2.5,
  "total_entries": 46,
  "average_hit_rate": 0.97,
  "caches": {
    "RuleCache": { /* snapshot */ },
    "ServiceContainer": { /* snapshot */ }
  }
}
```

## Appendix B: Quick Start Guide

### For Developers
```python
# 1. Enable monitoring in config
# config/monitoring.yaml
cache_monitoring:
  enabled: true
  backends: [logger]

# 2. Initialize monitoring in main.py
from monitoring.cache_monitoring import setup_monitoring
setup_monitoring()

# 3. View metrics in logs
tail -f logs/cache_metrics.log

# 4. Get programmatic access
from monitoring.metrics_aggregator import get_metrics_aggregator
aggregator = get_metrics_aggregator()
summary = aggregator.get_summary()
print(f"Total cache memory: {summary['total_memory_mb']:.1f} MB")
```

### For Operations
```bash
# Check current cache status
python scripts/check_cache_health.py

# View metrics dashboard (if UI enabled)
streamlit run src/main.py  # Check sidebar

# Export metrics for analysis
python scripts/export_cache_metrics.py --since 2025-10-01 --output metrics.json
```
