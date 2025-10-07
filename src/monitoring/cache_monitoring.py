"""Cache monitoring infrastructure."""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheOperation:
    """Single cache operation record."""

    cache_name: str
    operation: str  # get, set, delete, clear
    timestamp: float
    duration_ms: float
    result: str  # hit, miss, store, evict
    source: str | None = None  # disk, memory, fresh
    key: str | None = None
    size_bytes: int | None = None


@dataclass
class CacheSnapshot:
    """Point-in-time cache state."""

    timestamp: float
    cache_name: str
    total_entries: int
    memory_usage_bytes: int
    hit_rate: float
    avg_operation_ms: float
    hits: int = 0
    misses: int = 0
    evictions: int = 0


class CacheMonitor:
    """Base class for cache monitoring."""

    def __init__(self, cache_name: str, enabled: bool = True):
        self.cache_name = cache_name
        self.enabled = enabled
        self._operations: list[CacheOperation] = []

    @contextmanager
    def track_operation(self, operation: str, key: str = ""):
        """Context manager to track cache operation."""
        if not self.enabled:
            yield {}
            return

        start = time.perf_counter()
        result_data = {}

        try:
            yield result_data
        finally:
            duration_ms = (time.perf_counter() - start) * 1000

            op = CacheOperation(
                cache_name=self.cache_name,
                operation=operation,
                timestamp=time.time(),
                duration_ms=duration_ms,
                result=result_data.get("result", "unknown"),
                source=result_data.get("source"),
                key=key,
                size_bytes=result_data.get("size_bytes"),
            )

            self._operations.append(op)

            # Log if slow
            if duration_ms > 100:
                logger.warning(
                    f"Slow cache op: {self.cache_name}.{operation} took {duration_ms:.1f}ms"
                )

    def get_snapshot(self) -> CacheSnapshot:
        """Get current cache statistics."""
        if not self._operations:
            return CacheSnapshot(
                timestamp=time.time(),
                cache_name=self.cache_name,
                total_entries=0,
                memory_usage_bytes=0,
                hit_rate=0.0,
                avg_operation_ms=0.0,
            )

        hits = sum(1 for op in self._operations if op.result == "hit")
        misses = sum(1 for op in self._operations if op.result == "miss")
        total = hits + misses
        hit_rate = hits / total if total > 0 else 0.0

        avg_duration = sum(op.duration_ms for op in self._operations) / len(
            self._operations
        )

        evictions = sum(1 for op in self._operations if op.result == "evict")

        return CacheSnapshot(
            timestamp=time.time(),
            cache_name=self.cache_name,
            total_entries=len(self._operations),
            memory_usage_bytes=0,  # Memory tracking not yet implemented
            hit_rate=hit_rate,
            avg_operation_ms=avg_duration,
            hits=hits,
            misses=misses,
            evictions=evictions,
        )

    def get_operations(self, limit: int | None = None) -> list[CacheOperation]:
        """Get recorded operations, optionally limited to most recent."""
        if limit:
            return self._operations[-limit:]
        return self._operations.copy()

    def clear_operations(self):
        """Clear recorded operations history."""
        self._operations.clear()
        logger.info(f"Cleared operation history for {self.cache_name}")
