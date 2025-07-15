"""
Performance monitoring utilities voor DefinitieAgent.

Dit module biedt tools voor het monitoren en loggen van performance metrics
om trage operaties te identificeren en optimaliseren.
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor voor het bijhouden van performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
        self.active_timers: Dict[str, float] = {}
    
    def start_timer(self, operation: str) -> None:
        """Start een timer voor een operatie."""
        self.active_timers[operation] = time.time()
        logger.debug(f"⏱️ Started timer for: {operation}")
    
    def stop_timer(self, operation: str) -> float:
        """Stop een timer en return de duration."""
        if operation not in self.active_timers:
            logger.warning(f"Timer for {operation} was not started")
            return 0.0
        
        start_time = self.active_timers.pop(operation)
        duration = time.time() - start_time
        
        # Store metric
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)
        
        # Log if slow
        if duration > 5.0:  # Meer dan 5 seconden
            logger.warning(f"⚠️ SLOW OPERATION: {operation} took {duration:.2f}s")
        else:
            logger.info(f"✅ {operation} completed in {duration:.2f}s")
        
        return duration
    
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary statistics voor alle operations."""
        summary = {}
        
        for operation, durations in self.metrics.items():
            if durations:
                summary[operation] = {
                    'count': len(durations),
                    'total': sum(durations),
                    'average': sum(durations) / len(durations),
                    'min': min(durations),
                    'max': max(durations)
                }
        
        return summary
    
    def log_summary(self):
        """Log een performance summary."""
        summary = self.get_summary()
        
        logger.info("📊 Performance Summary:")
        for operation, stats in summary.items():
            logger.info(
                f"  {operation}: "
                f"avg={stats['average']:.2f}s, "
                f"min={stats['min']:.2f}s, "
                f"max={stats['max']:.2f}s, "
                f"total={stats['total']:.2f}s ({stats['count']} calls)"
            )


# Global performance monitor
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get de globale performance monitor."""
    return _performance_monitor


def measure_performance(operation_name: str = None):
    """
    Decorator voor het meten van functie performance.
    
    Args:
        operation_name: Naam voor de operatie (default: functie naam)
        
    Example:
        @measure_performance("definitie_generatie")
        async def generate_definition():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            name = operation_name or func.__name__
            monitor = get_performance_monitor()
            
            monitor.start_timer(name)
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                monitor.stop_timer(name)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            name = operation_name or func.__name__
            monitor = get_performance_monitor()
            
            monitor.start_timer(name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                monitor.stop_timer(name)
        
        # Return async of sync wrapper based op functie type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


import asyncio  # Import hier voor circular import te vermijden


# Utility functies voor manual timing
def start_timing(operation: str):
    """Start timing voor een operatie."""
    monitor = get_performance_monitor()
    monitor.start_timer(operation)


def stop_timing(operation: str) -> float:
    """Stop timing en return duration."""
    monitor = get_performance_monitor()
    return monitor.stop_timer(operation)


def log_performance_summary():
    """Log de performance summary."""
    monitor = get_performance_monitor()
    monitor.log_summary()