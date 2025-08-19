"""
API monitoring en analytics voor DefinitieAgent.

Biedt real-time prestatie monitoring, fout analyse, en kosten optimalisatie
voor alle API calls en systeem operaties.
"""

import asyncio  # Asynchrone programmering voor real-time monitoring
import csv  # CSV export functionaliteit voor rapportage
import json  # JSON verwerking voor data serialisatie
import logging  # Logging faciliteiten voor debug en monitoring
import time  # Tijd functies voor prestatie metingen
from collections import defaultdict, deque  # Efficiënte data structuren voor metrics
from dataclasses import (  # Dataklassen voor gestructureerde monitoring data
    asdict,
    dataclass,
)
from datetime import (  # Datum en tijd functionaliteit voor timestamps
    datetime,
    timedelta,
)
from enum import Enum  # Enumeraties voor monitoring types en severity levels
from pathlib import Path  # Object-georiënteerde pad manipulatie
from typing import Any  # Type hints voor betere code documentatie

logger = logging.getLogger(__name__)  # Logger instantie voor API monitor module


class AlertSeverity(Enum):
    """Alert ernst niveaus voor monitoring meldingen."""

    INFO = "info"  # Informatieve meldingen
    WARNING = "warning"  # Waarschuwingen, aandacht vereist
    ERROR = "error"  # Fouten die actie vereisen
    CRITICAL = "critical"  # Kritieke situaties, directe actie nodig


class MetricType(Enum):
    """Types van metrics die getrackt worden voor performance monitoring."""

    RESPONSE_TIME = "response_time"  # API response tijden
    ERROR_RATE = "error_rate"  # Fout percentages
    THROUGHPUT = "throughput"  # Aantal requests per seconde
    COST = "cost"  # API kosten tracking
    CACHE_HIT_RATE = "cache_hit_rate"  # Cache hit ratio
    QUEUE_LENGTH = "queue_length"  # Lengte van request queues


@dataclass
class Alert:
    """Alert configuration and state."""

    name: str
    metric_type: MetricType
    threshold_value: float
    comparison: str  # 'gt', 'lt', 'eq'
    severity: AlertSeverity
    window_minutes: int = 5
    cooldown_minutes: int = 15
    last_triggered: datetime | None = None
    trigger_count: int = 0
    enabled: bool = True


@dataclass
class APICall:
    """Individual API call record."""

    timestamp: datetime
    endpoint: str
    function_name: str
    request_id: str
    duration: float
    success: bool
    error_type: str | None = None
    tokens_used: int = 0
    cost: float = 0.0
    cache_hit: bool = False
    priority: str = "normal"
    retry_count: int = 0


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time."""

    timestamp: datetime
    endpoint: str
    response_time_avg: float
    response_time_p95: float
    error_rate: float
    throughput: float
    cost_per_hour: float
    cache_hit_rate: float
    active_requests: int


class CostCalculator:
    """Calculate API costs based on usage."""

    # OpenAI pricing (as of 2025, subject to change)
    PRICING = {
        "gpt-4": {
            "input": 0.00003,  # per token
            "output": 0.00006,  # per token
        },
        "gpt-3.5-turbo": {
            "input": 0.0000015,
            "output": 0.000002,
        },
    }

    @classmethod
    def calculate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for API call."""
        pricing = cls.PRICING.get(model, cls.PRICING["gpt-4"])
        return input_tokens * pricing["input"] + output_tokens * pricing["output"]

    @classmethod
    def estimate_monthly_cost(cls, daily_requests: int, avg_tokens: int) -> float:
        """Estimate monthly cost based on usage patterns."""
        # Assume 70% input, 30% output tokens
        input_tokens = int(avg_tokens * 0.7)
        output_tokens = int(avg_tokens * 0.3)

        daily_cost = daily_requests * cls.calculate_cost(
            "gpt-4", input_tokens, output_tokens
        )
        return daily_cost * 30


class MetricsCollector:
    """Collects and aggregates API metrics."""

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.api_calls: deque = deque()
        self.metrics_history: dict[str, deque] = defaultdict(lambda: deque())
        self.alerts: list[Alert] = []
        self._lock = asyncio.Lock()

        # Load historical data
        self._load_historical_data()

        # Set up default alerts
        self._setup_default_alerts()

    def _setup_default_alerts(self):
        """Set up default alert conditions."""
        self.alerts = [
            Alert(
                name="High Error Rate",
                metric_type=MetricType.ERROR_RATE,
                threshold_value=0.1,  # 10%
                comparison="gt",
                severity=AlertSeverity.ERROR,
                window_minutes=5,
            ),
            Alert(
                name="Slow Response Time",
                metric_type=MetricType.RESPONSE_TIME,
                threshold_value=10.0,  # 10 seconds
                comparison="gt",
                severity=AlertSeverity.WARNING,
                window_minutes=10,
            ),
            Alert(
                name="High Cost Rate",
                metric_type=MetricType.COST,
                threshold_value=1.0,  # $1 per hour
                comparison="gt",
                severity=AlertSeverity.WARNING,
                window_minutes=60,
            ),
            Alert(
                name="Low Cache Hit Rate",
                metric_type=MetricType.CACHE_HIT_RATE,
                threshold_value=0.3,  # 30%
                comparison="lt",
                severity=AlertSeverity.INFO,
                window_minutes=30,
            ),
        ]

    def _load_historical_data(self):
        """Load historical metrics data."""
        try:
            history_file = Path("cache/api_metrics.json")
            if history_file.exists():
                with open(history_file) as f:
                    data = json.load(f)

                    # Load recent API calls
                    calls_data = data.get("recent_calls", [])
                    for call_data in calls_data[-1000:]:  # Keep last 1000 calls
                        call = APICall(
                            timestamp=datetime.fromisoformat(call_data["timestamp"]),
                            **{k: v for k, v in call_data.items() if k != "timestamp"},
                        )
                        self.api_calls.append(call)

                    logger.info(f"Loaded {len(self.api_calls)} historical API calls")
        except Exception as e:
            logger.warning(f"Could not load historical metrics: {e}")

    def _save_historical_data(self):
        """Save historical data to disk."""
        try:
            history_file = Path("cache/api_metrics.json")
            history_file.parent.mkdir(exist_ok=True)

            # Convert recent calls to serializable format
            recent_calls = []
            for call in list(self.api_calls)[-1000:]:  # Save last 1000 calls
                call_dict = asdict(call)
                call_dict["timestamp"] = call.timestamp.isoformat()
                recent_calls.append(call_dict)

            data = {
                "recent_calls": recent_calls,
                "last_updated": datetime.now().isoformat(),
            }

            with open(history_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save metrics history: {e}")

    async def record_api_call(self, api_call: APICall):
        """Record an API call for metrics."""
        async with self._lock:
            self.api_calls.append(api_call)

            # Clean up old data
            cutoff = datetime.now() - timedelta(hours=self.retention_hours)
            while self.api_calls and self.api_calls[0].timestamp < cutoff:
                self.api_calls.popleft()

            # Generate snapshot
            await self._generate_snapshot(api_call.endpoint)

            # Check alerts
            await self._check_alerts()

    async def _generate_snapshot(self, endpoint: str):
        """Generate metrics snapshot for an endpoint."""
        now = datetime.now()
        recent_calls = [
            call
            for call in self.api_calls
            if (
                call.endpoint == endpoint
                and (now - call.timestamp).total_seconds() < 300
            )  # Last 5 minutes
        ]

        if not recent_calls:
            return

        # Calculate metrics
        response_times = [call.duration for call in recent_calls if call.success]
        errors = [call for call in recent_calls if not call.success]
        cache_hits = [call for call in recent_calls if call.cache_hit]

        response_time_avg = (
            sum(response_times) / len(response_times) if response_times else 0
        )

        # Calculate 95th percentile
        if response_times:
            sorted_times = sorted(response_times)
            p95_index = int(0.95 * len(sorted_times))
            response_time_p95 = (
                sorted_times[p95_index]
                if p95_index < len(sorted_times)
                else sorted_times[-1]
            )
        else:
            response_time_p95 = 0

        error_rate = len(errors) / len(recent_calls) if recent_calls else 0
        throughput = len(recent_calls) / 5.0  # Requests per minute over 5 minutes

        # Calculate hourly cost
        hourly_cost = (
            sum(call.cost for call in recent_calls) * 12
        )  # 5-min window * 12 = hourly

        cache_hit_rate = len(cache_hits) / len(recent_calls) if recent_calls else 0

        # Active requests (this is an approximation)
        active_requests = len(
            [
                call
                for call in recent_calls
                if (now - call.timestamp).total_seconds() < 30
            ]
        )

        snapshot = MetricSnapshot(
            timestamp=now,
            endpoint=endpoint,
            response_time_avg=response_time_avg,
            response_time_p95=response_time_p95,
            error_rate=error_rate,
            throughput=throughput,
            cost_per_hour=hourly_cost,
            cache_hit_rate=cache_hit_rate,
            active_requests=active_requests,
        )

        # Store snapshot
        self.metrics_history[endpoint].append(snapshot)

        # Keep only recent snapshots
        cutoff = now - timedelta(hours=self.retention_hours)
        while (
            self.metrics_history[endpoint]
            and self.metrics_history[endpoint][0].timestamp < cutoff
        ):
            self.metrics_history[endpoint].popleft()

    async def _check_alerts(self):
        """Check alert conditions."""
        now = datetime.now()

        for alert in self.alerts:
            if not alert.enabled:
                continue

            # Check cooldown
            if (
                alert.last_triggered
                and (now - alert.last_triggered).total_seconds()
                < alert.cooldown_minutes * 60
            ):
                continue

            # Get recent data for alert window
            window_start = now - timedelta(minutes=alert.window_minutes)

            # Calculate metric value based on type
            metric_value = await self._calculate_metric_value(
                alert.metric_type, window_start
            )

            # Check threshold
            triggered = False
            if (
                (alert.comparison == "gt" and metric_value > alert.threshold_value)
                or (alert.comparison == "lt" and metric_value < alert.threshold_value)
                or (
                    alert.comparison == "eq"
                    and abs(metric_value - alert.threshold_value) < 0.001
                )
            ):
                triggered = True

            if triggered:
                alert.last_triggered = now
                alert.trigger_count += 1

                logger.warning(
                    f"🚨 ALERT: {alert.name} - {metric_value:.3f} {alert.comparison} {alert.threshold_value} "
                    f"(Severity: {alert.severity.value})"
                )

    async def _calculate_metric_value(
        self, metric_type: MetricType, window_start: datetime
    ) -> float:
        """Calculate metric value for alert checking."""
        recent_calls = [
            call for call in self.api_calls if call.timestamp >= window_start
        ]

        if not recent_calls:
            return 0.0

        if metric_type == MetricType.RESPONSE_TIME:
            response_times = [call.duration for call in recent_calls if call.success]
            return sum(response_times) / len(response_times) if response_times else 0.0

        if metric_type == MetricType.ERROR_RATE:
            errors = [call for call in recent_calls if not call.success]
            return len(errors) / len(recent_calls)

        if metric_type == MetricType.THROUGHPUT:
            window_minutes = (datetime.now() - window_start).total_seconds() / 60
            return len(recent_calls) / window_minutes if window_minutes > 0 else 0.0

        if metric_type == MetricType.COST:
            window_hours = (datetime.now() - window_start).total_seconds() / 3600
            total_cost = sum(call.cost for call in recent_calls)
            return total_cost / window_hours if window_hours > 0 else 0.0

        if metric_type == MetricType.CACHE_HIT_RATE:
            cache_hits = [call for call in recent_calls if call.cache_hit]
            return len(cache_hits) / len(recent_calls)

        return 0.0

    def get_realtime_metrics(self, endpoint: str | None = None) -> dict[str, Any]:
        """Get real-time metrics dashboard data."""
        now = datetime.now()
        recent_cutoff = now - timedelta(minutes=5)

        if endpoint:
            recent_calls = [
                call
                for call in self.api_calls
                if call.endpoint == endpoint and call.timestamp >= recent_cutoff
            ]
            endpoints = [endpoint]
        else:
            recent_calls = [
                call for call in self.api_calls if call.timestamp >= recent_cutoff
            ]
            endpoints = list({call.endpoint for call in self.api_calls})

        # Overall metrics
        total_calls = len(recent_calls)
        successful_calls = [call for call in recent_calls if call.success]
        failed_calls = [call for call in recent_calls if not call.success]
        cached_calls = [call for call in recent_calls if call.cache_hit]

        response_times = [call.duration for call in successful_calls]
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )

        total_cost = sum(call.cost for call in recent_calls)
        total_tokens = sum(call.tokens_used for call in recent_calls)

        # Per-endpoint breakdown
        endpoint_metrics = {}
        for ep in endpoints:
            ep_calls = [call for call in recent_calls if call.endpoint == ep]
            if ep_calls:
                ep_successful = [call for call in ep_calls if call.success]
                ep_response_times = [call.duration for call in ep_successful]

                endpoint_metrics[ep] = {
                    "total_calls": len(ep_calls),
                    "success_rate": len(ep_successful) / len(ep_calls),
                    "avg_response_time": (
                        sum(ep_response_times) / len(ep_response_times)
                        if ep_response_times
                        else 0
                    ),
                    "error_count": len(ep_calls) - len(ep_successful),
                    "cache_hit_rate": len([call for call in ep_calls if call.cache_hit])
                    / len(ep_calls),
                    "total_cost": sum(call.cost for call in ep_calls),
                }

        return {
            "timestamp": now.isoformat(),
            "window_minutes": 5,
            "total_calls": total_calls,
            "success_rate": (
                len(successful_calls) / total_calls if total_calls > 0 else 0
            ),
            "error_count": len(failed_calls),
            "avg_response_time": avg_response_time,
            "cache_hit_rate": len(cached_calls) / total_calls if total_calls > 0 else 0,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "estimated_hourly_cost": total_cost * 12,  # 5-minute window * 12
            "endpoint_metrics": endpoint_metrics,
            "active_alerts": [
                {
                    "name": alert.name,
                    "severity": alert.severity.value,
                    "last_triggered": (
                        alert.last_triggered.isoformat()
                        if alert.last_triggered
                        else None
                    ),
                    "trigger_count": alert.trigger_count,
                }
                for alert in self.alerts
                if alert.last_triggered
                and (now - alert.last_triggered).total_seconds() < 3600  # Last hour
            ],
        }

    def generate_cost_optimization_report(self) -> dict[str, Any]:
        """Generate cost optimization recommendations."""
        now = datetime.now()
        day_ago = now - timedelta(days=1)

        recent_calls = [call for call in self.api_calls if call.timestamp >= day_ago]
        if not recent_calls:
            return {"error": "No recent data available"}

        # Cost analysis
        total_cost = sum(call.cost for call in recent_calls)
        cached_calls = [call for call in recent_calls if call.cache_hit]
        cache_savings = len(cached_calls) * 0.001  # Estimated savings per cached call

        # Token analysis
        total_tokens = sum(call.tokens_used for call in recent_calls)
        avg_tokens_per_call = total_tokens / len(recent_calls)

        # Error analysis
        failed_calls = [call for call in recent_calls if not call.success]
        wasted_cost = sum(call.cost for call in failed_calls)

        # Recommendations
        recommendations = []

        if len(cached_calls) / len(recent_calls) < 0.3:
            recommendations.append(
                {
                    "type": "caching",
                    "priority": "high",
                    "description": "Low cache hit rate detected. Increase cache TTL or improve cache key generation.",
                    "potential_savings": f"${cache_savings * 3:.2f}/day",
                }
            )

        if wasted_cost > total_cost * 0.1:
            recommendations.append(
                {
                    "type": "error_reduction",
                    "priority": "high",
                    "description": "High error rate is wasting API costs. Implement better retry logic.",
                    "potential_savings": f"${wasted_cost:.2f}/day",
                }
            )

        if avg_tokens_per_call > 1000:
            recommendations.append(
                {
                    "type": "prompt_optimization",
                    "priority": "medium",
                    "description": "High token usage detected. Consider shorter prompts or response limits.",
                    "potential_savings": f"${total_cost * 0.2:.2f}/day",
                }
            )

        return {
            "period": "24 hours",
            "total_calls": len(recent_calls),
            "total_cost": total_cost,
            "estimated_monthly_cost": total_cost * 30,
            "cache_hit_rate": len(cached_calls) / len(recent_calls),
            "error_rate": len(failed_calls) / len(recent_calls),
            "avg_tokens_per_call": avg_tokens_per_call,
            "wasted_cost": wasted_cost,
            "recommendations": recommendations,
        }

    def export_metrics_csv(self, filename: str | None = None) -> str:
        """Export metrics to CSV file."""
        if filename is None:
            filename = f"api_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = Path("exports") / filename
        filepath.parent.mkdir(exist_ok=True)

        with open(filepath, "w", newline="") as csvfile:
            fieldnames = [
                "timestamp",
                "endpoint",
                "function_name",
                "duration",
                "success",
                "error_type",
                "tokens_used",
                "cost",
                "cache_hit",
                "priority",
                "retry_count",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for call in self.api_calls:
                row = asdict(call)
                row["timestamp"] = call.timestamp.isoformat()
                writer.writerow(row)

        return str(filepath)


# Global metrics collector
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


async def record_api_call(
    endpoint: str,
    function_name: str,
    duration: float,
    success: bool,
    error_type: str | None = None,
    tokens_used: int = 0,
    model: str = "gpt-4",
    cache_hit: bool = False,
    priority: str = "normal",
    retry_count: int = 0,
):
    """Convenience function to record an API call."""
    collector = get_metrics_collector()

    # Calculate cost
    cost = 0.0
    if tokens_used > 0:
        # Estimate input/output split
        input_tokens = int(tokens_used * 0.7)
        output_tokens = int(tokens_used * 0.3)
        cost = CostCalculator.calculate_cost(model, input_tokens, output_tokens)

    api_call = APICall(
        timestamp=datetime.now(),
        endpoint=endpoint,
        function_name=function_name,
        request_id=f"{function_name}_{int(time.time() * 1000)}",
        duration=duration,
        success=success,
        error_type=error_type,
        tokens_used=tokens_used,
        cost=cost,
        cache_hit=cache_hit,
        priority=priority,
        retry_count=retry_count,
    )

    await collector.record_api_call(api_call)


async def test_api_monitor():
    """Test the API monitoring system."""
    print("🧪 Testing API Monitor")
    print("=" * 30)

    collector = get_metrics_collector()

    # Simulate API calls
    for _i in range(20):
        await record_api_call(
            endpoint="test_api",
            function_name="test_function",
            duration=random.uniform(0.5, 3.0),
            success=random.choice([True, True, True, False]),  # 25% error rate
            tokens_used=random.randint(100, 500),
            cache_hit=random.choice([True, False]),
            retry_count=random.randint(0, 2),
        )

    # Get metrics
    metrics = collector.get_realtime_metrics()
    print(f"📊 Total calls: {metrics['total_calls']}")
    print(f"📊 Success rate: {metrics['success_rate']:.1%}")
    print(f"📊 Cache hit rate: {metrics['cache_hit_rate']:.1%}")
    print(f"📊 Total cost: ${metrics['total_cost']:.4f}")

    # Generate cost optimization report
    report = collector.generate_cost_optimization_report()
    print(f"💰 Estimated monthly cost: ${report.get('estimated_monthly_cost', 0):.2f}")
    print(f"💰 Recommendations: {len(report.get('recommendations', []))}")

    # Export CSV
    csv_file = collector.export_metrics_csv()
    print(f"📁 Exported metrics to: {csv_file}")


if __name__ == "__main__":
    import random

    asyncio.run(test_api_monitor())
