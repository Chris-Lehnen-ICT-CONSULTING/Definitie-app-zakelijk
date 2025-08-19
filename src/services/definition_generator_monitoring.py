"""
Definition Generator Monitoring Module.

Monitoring en metrics systeem voor de UnifiedDefinitionGenerator:
- API call tracking (van services implementatie)
- Performance monitoring (van definitie_generator implementatie)
- Quality metrics (van generation implementatie)
- Error tracking en alerting
"""

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from services.definition_generator_config import MonitoringConfig
from services.interfaces import Definition

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types van metrics die we tracken."""

    GENERATION_COUNT = "generation_count"
    GENERATION_DURATION = "generation_duration"
    SUCCESS_RATE = "success_rate"
    CACHE_HIT_RATE = "cache_hit_rate"
    CONTEXT_RICHNESS = "context_richness"
    PROMPT_LENGTH = "prompt_length"
    DEFINITION_LENGTH = "definition_length"
    ENHANCEMENT_RATE = "enhancement_rate"
    ERROR_RATE = "error_rate"


@dataclass
class MetricEntry:
    """Een individuele metric entry."""

    timestamp: datetime
    value: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationMetrics:
    """Metrics voor een specifieke definitie generatie."""

    begrip: str
    start_time: datetime
    end_time: datetime | None = None
    duration: float | None = None
    success: bool = True
    error: str | None = None

    # Context metrics
    context_sources: int = 0
    context_confidence: float = 0.0
    context_richness_score: float = 0.0

    # Prompt metrics
    prompt_length: int = 0
    prompt_strategy: str = "unknown"

    # Generation metrics
    definition_length: int = 0
    cache_hit: bool = False
    enhancement_applied: bool = False

    # Quality metrics
    quality_score: float | None = None
    validation_passed: bool = True

    def finish(self, success: bool = True, error: str | None = None):
        """Mark deze generatie als voltooid."""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.success = success
        self.error = error


class GenerationMonitor:
    """
    Monitor voor definitie generaties die metrics verzamelt.

    Combineert monitoring strategieën van alle drie implementaties:
    - API call tracking (van services)
    - Performance metrics (van definitie_generator)
    - Quality tracking (van generation)
    """

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.metrics: dict[MetricType, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.active_generations: dict[str, GenerationMetrics] = {}
        self.recent_errors: deque = deque(maxlen=100)

        # Performance tracking
        self._performance_window = timedelta(minutes=5)
        self._alert_threshold = 0.5  # 50% error rate

        logger.info("GenerationMonitor geïnitialiseerd")

    def start_generation(
        self, begrip: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """
        Start monitoring van een nieuwe generatie.

        Args:
            begrip: Het begrip dat gegenereerd wordt
            metadata: Extra metadata voor deze generatie

        Returns:
            Generation ID voor tracking
        """
        if not self.config.enable_monitoring:
            return ""

        generation_id = f"{begrip}_{int(time.time() * 1000)}"

        metrics = GenerationMetrics(begrip=begrip, start_time=datetime.now())

        if metadata:
            for key, value in metadata.items():
                if hasattr(metrics, key):
                    setattr(metrics, key, value)

        self.active_generations[generation_id] = metrics

        # Record generation start
        self._record_metric(MetricType.GENERATION_COUNT, 1, {"begrip": begrip})

        logger.debug(f"Started monitoring generation '{begrip}' (ID: {generation_id})")
        return generation_id

    def finish_generation(
        self,
        generation_id: str,
        success: bool = True,
        error: str | None = None,
        definition: Definition | None = None,
    ):
        """
        Beëindig monitoring van een generatie.

        Args:
            generation_id: Het generation ID van start_generation
            success: Of de generatie succesvol was
            error: Error message als van toepassing
            definition: De gegenereerde definitie (voor extra metrics)
        """
        if not self.config.enable_monitoring or not generation_id:
            return

        if generation_id not in self.active_generations:
            logger.warning(f"Onbekende generation ID: {generation_id}")
            return

        metrics = self.active_generations[generation_id]
        metrics.finish(success, error)

        # Record metrics
        if metrics.duration:
            self._record_metric(
                MetricType.GENERATION_DURATION,
                metrics.duration,
                {"begrip": metrics.begrip},
            )

        self._record_metric(
            MetricType.SUCCESS_RATE, 1 if success else 0, {"begrip": metrics.begrip}
        )

        if not success and error:
            self._record_error(metrics.begrip, error)

        # Definition-specific metrics
        if definition and success:
            self._record_definition_metrics(definition, metrics)

        # Cleanup
        del self.active_generations[generation_id]

        logger.debug(
            f"Finished monitoring generation '{metrics.begrip}' "
            f"(duration: {metrics.duration:.3f}s, success: {success})"
        )

    def record_context_metrics(
        self, generation_id: str, sources: int, confidence: float, richness_score: float
    ):
        """Record context-related metrics."""
        if not self.config.enable_monitoring or not generation_id:
            return

        if generation_id in self.active_generations:
            metrics = self.active_generations[generation_id]
            metrics.context_sources = sources
            metrics.context_confidence = confidence
            metrics.context_richness_score = richness_score

            self._record_metric(
                MetricType.CONTEXT_RICHNESS, richness_score, {"begrip": metrics.begrip}
            )

    def record_prompt_metrics(
        self, generation_id: str, prompt_length: int, strategy: str
    ):
        """Record prompt-related metrics."""
        if not self.config.enable_monitoring or not generation_id:
            return

        if generation_id in self.active_generations:
            metrics = self.active_generations[generation_id]
            metrics.prompt_length = prompt_length
            metrics.prompt_strategy = strategy

            self._record_metric(
                MetricType.PROMPT_LENGTH, prompt_length, {"strategy": strategy}
            )

    def record_cache_hit(self, generation_id: str, hit: bool):
        """Record cache hit/miss."""
        if not self.config.enable_monitoring or not generation_id:
            return

        if generation_id in self.active_generations:
            self.active_generations[generation_id].cache_hit = hit

        self._record_metric(MetricType.CACHE_HIT_RATE, 1 if hit else 0)

    def record_enhancement(self, generation_id: str, applied: bool):
        """Record enhancement application."""
        if not self.config.enable_monitoring or not generation_id:
            return

        if generation_id in self.active_generations:
            self.active_generations[generation_id].enhancement_applied = applied

        self._record_metric(MetricType.ENHANCEMENT_RATE, 1 if applied else 0)

    def _record_definition_metrics(
        self, definition: Definition, metrics: GenerationMetrics
    ):
        """Record metrics van de gegenereerde definitie."""
        definition_length = len(definition.definitie)
        metrics.definition_length = definition_length

        self._record_metric(
            MetricType.DEFINITION_LENGTH,
            definition_length,
            {"begrip": definition.begrip, "domein": definition.domein},
        )

        # Enhancement check
        enhanced = definition.metadata.get("enhanced", False)
        metrics.enhancement_applied = enhanced
        self._record_metric(MetricType.ENHANCEMENT_RATE, 1 if enhanced else 0)

    def _record_metric(
        self,
        metric_type: MetricType,
        value: float,
        metadata: dict[str, Any] | None = None,
    ):
        """Record een metric entry."""
        entry = MetricEntry(
            timestamp=datetime.now(), value=value, metadata=metadata or {}
        )

        self.metrics[metric_type].append(entry)

    def _record_error(self, begrip: str, error: str):
        """Record een error voor tracking."""
        error_entry = {"timestamp": datetime.now(), "begrip": begrip, "error": error}

        self.recent_errors.append(error_entry)

        # Check for alert conditions
        self._check_error_rate_alert()

    def _check_error_rate_alert(self):
        """Check of we een error rate alert moeten triggeren."""
        if not self.config.enable_alerts:
            return

        # Calculate error rate in last 5 minutes
        cutoff_time = datetime.now() - self._performance_window
        recent_errors = [e for e in self.recent_errors if e["timestamp"] > cutoff_time]

        # Get total generations in same period
        recent_generations = []
        for metric_list in self.metrics[MetricType.GENERATION_COUNT]:
            if metric_list.timestamp > cutoff_time:
                recent_generations.extend([metric_list])

        if len(recent_generations) == 0:
            return

        error_rate = len(recent_errors) / len(recent_generations)

        if error_rate > self._alert_threshold:
            self._trigger_alert(
                "high_error_rate",
                {
                    "error_rate": error_rate,
                    "recent_errors": len(recent_errors),
                    "total_generations": len(recent_generations),
                },
            )

    def _trigger_alert(self, alert_type: str, data: dict[str, Any]):
        """Trigger een monitoring alert."""
        logger.warning(f"MONITORING ALERT [{alert_type}]: {data}")

        # In een echte implementatie zou dit naar alerting systeem gaan
        # (email, Slack, PagerDuty, etc.)

    def get_metrics_summary(self, window_minutes: int = 60) -> dict[str, Any]:
        """
        Verkrijg een samenvatting van metrics over de gegeven periode.

        Args:
            window_minutes: Aantal minuten terug te kijken

        Returns:
            Dictionary met metric samenvattingen
        """
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        summary = {}

        for metric_type, entries in self.metrics.items():
            recent_entries = [e for e in entries if e.timestamp > cutoff_time]

            if recent_entries:
                values = [e.value for e in recent_entries]
                summary[metric_type.value] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "total": (
                        sum(values)
                        if metric_type == MetricType.GENERATION_COUNT
                        else None
                    ),
                }

        return summary

    def get_current_status(self) -> dict[str, Any]:
        """Verkrijg huidige monitoring status."""
        return {
            "active_generations": len(self.active_generations),
            "total_metrics_recorded": sum(
                len(entries) for entries in self.metrics.values()
            ),
            "recent_errors": len(self.recent_errors),
            "monitoring_enabled": self.config.enable_monitoring,
            "alerts_enabled": self.config.enable_alerts,
        }

    def reset_metrics(self):
        """Reset alle metrics (voor testing)."""
        self.metrics.clear()
        self.active_generations.clear()
        self.recent_errors.clear()
        logger.info("Alle monitoring metrics gereset")


# Global monitor instance
_monitor_instance: GenerationMonitor | None = None


def get_monitor(config: MonitoringConfig | None = None) -> GenerationMonitor:
    """
    Verkrijg de globale monitor instance.

    Args:
        config: MonitoringConfig, alleen gebruikt bij eerste call

    Returns:
        GenerationMonitor instance
    """
    global _monitor_instance

    if _monitor_instance is None:
        if config is None:
            from services.definition_generator_config import MonitoringConfig

            config = MonitoringConfig()
        _monitor_instance = GenerationMonitor(config)

    return _monitor_instance


def reset_monitor():
    """Reset de globale monitor instance."""
    global _monitor_instance
    if _monitor_instance:
        _monitor_instance.reset_metrics()
    _monitor_instance = None
