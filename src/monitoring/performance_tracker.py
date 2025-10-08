"""Performance baseline tracking.

Auto-detecteert performance regressies door metrics te tracken en baselines te berekenen.
Gebruikt sliding window van laatste 20 samples voor baseline berekening.
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individuele performance metric."""

    metric_name: str
    value: float
    timestamp: float
    metadata: dict[str, Any]


@dataclass
class PerformanceBaseline:
    """Baseline voor een metric."""

    metric_name: str
    baseline_value: float
    confidence: float
    sample_count: int
    last_updated: float


class PerformanceTracker:
    """Track performance metrics en baselines.

    Features:
    - Automatische baseline berekening (median van laatste 20 samples)
    - Regression detection met WARNING/CRITICAL alerts
    - Confidence scoring op basis van sample count
    - Metadata support voor context tracking
    """

    # Thresholds voor regression detection
    CRITICAL_THRESHOLD = 1.20  # 20% slechter dan baseline
    WARNING_THRESHOLD = 1.10  # 10% slechter dan baseline

    # Baseline calculation settings
    BASELINE_WINDOW = 20  # Aantal samples voor baseline
    MIN_SAMPLES = 5  # Minimum samples voordat baseline berekend wordt

    def __init__(self, db_path: str = "data/definities.db"):
        """Initialize performance tracker.

        Args:
            db_path: Pad naar SQLite database
        """
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self):
        """Create performance tables als deze niet bestaan."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Performance metrics table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        value REAL NOT NULL,
                        timestamp REAL NOT NULL,
                        metadata TEXT,
                        CONSTRAINT chk_value_positive CHECK (value >= 0)
                    )
                """
                )

                # Index voor snelle queries
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_performance_metrics_name_timestamp
                    ON performance_metrics(metric_name, timestamp DESC)
                """
                )

                # Performance baselines table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS performance_baselines (
                        metric_name TEXT PRIMARY KEY,
                        baseline_value REAL NOT NULL,
                        confidence REAL NOT NULL,
                        sample_count INTEGER NOT NULL,
                        last_updated REAL NOT NULL,
                        CONSTRAINT chk_baseline_positive CHECK (baseline_value >= 0),
                        CONSTRAINT chk_confidence_range CHECK (confidence >= 0 AND confidence <= 1),
                        CONSTRAINT chk_sample_count CHECK (sample_count > 0)
                    )
                """
                )

                conn.commit()
                logger.info("Performance tracking schema geïnitialiseerd")
        except sqlite3.Error as e:
            logger.error(f"Fout bij schema initialisatie: {e}")
            raise

    def track_metric(
        self, metric_name: str, value: float, metadata: dict[str, Any] | None = None
    ) -> None:
        """Store performance metric en update baseline.

        Args:
            metric_name: Naam van de metric (bijv. "app_startup_ms")
            value: Gemeten waarde
            metadata: Optionele context (bijv. {"version": "2.0"})
        """
        if value < 0:
            raise ValueError(f"Value must be non-negative, got {value}")

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Store metric
                conn.execute(
                    """INSERT INTO performance_metrics
                       (metric_name, value, timestamp, metadata)
                       VALUES (?, ?, ?, ?)""",
                    (metric_name, value, time.time(), json.dumps(metadata or {})),
                )
                conn.commit()

            logger.debug(f"Tracked metric: {metric_name}={value}")

            # Update baseline na opslaan
            self._update_baseline(metric_name)

        except sqlite3.Error as e:
            logger.error(f"Fout bij opslaan metric {metric_name}: {e}")
            raise

    def _update_baseline(self, metric_name: str) -> None:
        """Bereken nieuwe baseline uit recente samples.

        Gebruikt median van laatste BASELINE_WINDOW samples.
        Confidence wordt berekend als: sample_count / BASELINE_WINDOW.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Haal laatste samples op
                cursor = conn.execute(
                    """SELECT value FROM performance_metrics
                       WHERE metric_name = ?
                       ORDER BY timestamp DESC
                       LIMIT ?""",
                    (metric_name, self.BASELINE_WINDOW),
                )
                values = [row[0] for row in cursor.fetchall()]

                if len(values) < self.MIN_SAMPLES:
                    logger.debug(
                        f"Niet genoeg samples voor {metric_name}: "
                        f"{len(values)}/{self.MIN_SAMPLES}"
                    )
                    return

                # Bereken median als baseline
                sorted_values = sorted(values)
                median_idx = len(sorted_values) // 2

                if len(sorted_values) % 2 == 0:
                    # Even aantal: gemiddelde van middelste twee
                    median = (
                        sorted_values[median_idx - 1] + sorted_values[median_idx]
                    ) / 2
                else:
                    # Oneven aantal: middelste waarde
                    median = sorted_values[median_idx]

                # Confidence: hoeveel van window is gevuld
                confidence = min(len(values) / self.BASELINE_WINDOW, 1.0)

                # Update baseline
                conn.execute(
                    """
                    INSERT OR REPLACE INTO performance_baselines
                    (metric_name, baseline_value, confidence, sample_count, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (metric_name, median, confidence, len(values), time.time()),
                )
                conn.commit()

                logger.debug(
                    f"Baseline updated: {metric_name}={median:.1f} "
                    f"(confidence={confidence:.2f}, n={len(values)})"
                )

        except sqlite3.Error as e:
            logger.error(f"Fout bij baseline update voor {metric_name}: {e}")
            # Don't raise - baseline update is non-critical

    def check_regression(self, metric_name: str, current_value: float) -> str | None:
        """Check of huidige waarde een regressie is vs baseline.

        Args:
            metric_name: Naam van metric
            current_value: Huidige gemeten waarde

        Returns:
            "CRITICAL" als > 20% slechter
            "WARNING" als > 10% slechter
            None als binnen acceptable range of geen baseline
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """SELECT baseline_value, confidence
                       FROM performance_baselines
                       WHERE metric_name = ?""",
                    (metric_name,),
                )
                row = cursor.fetchone()

                if not row:
                    logger.debug(f"Geen baseline voor {metric_name}")
                    return None

                baseline, confidence = row

                # Alleen alert geven bij voldoende confidence
                if confidence < 0.5:
                    logger.debug(
                        f"Te weinig confidence voor {metric_name}: {confidence:.2f}"
                    )
                    return None

                # Check thresholds
                ratio = current_value / baseline

                if ratio >= self.CRITICAL_THRESHOLD:
                    logger.warning(
                        f"CRITICAL regression voor {metric_name}: "
                        f"{current_value:.1f} vs baseline {baseline:.1f} "
                        f"({ratio:.1%})"
                    )
                    return "CRITICAL"
                elif ratio >= self.WARNING_THRESHOLD:
                    logger.warning(
                        f"WARNING regression voor {metric_name}: "
                        f"{current_value:.1f} vs baseline {baseline:.1f} "
                        f"({ratio:.1%})"
                    )
                    return "WARNING"

                return None

        except sqlite3.Error as e:
            logger.error(f"Fout bij regression check voor {metric_name}: {e}")
            return None

    def get_baseline(self, metric_name: str) -> PerformanceBaseline | None:
        """Haal baseline op voor metric.

        Args:
            metric_name: Naam van metric

        Returns:
            PerformanceBaseline of None als geen baseline beschikbaar
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """SELECT metric_name, baseline_value, confidence,
                              sample_count, last_updated
                       FROM performance_baselines
                       WHERE metric_name = ?""",
                    (metric_name,),
                )
                row = cursor.fetchone()

                if not row:
                    return None

                return PerformanceBaseline(
                    metric_name=row[0],
                    baseline_value=row[1],
                    confidence=row[2],
                    sample_count=row[3],
                    last_updated=row[4],
                )
        except sqlite3.Error as e:
            logger.error(f"Fout bij ophalen baseline voor {metric_name}: {e}")
            return None

    def get_all_baselines(self) -> list[PerformanceBaseline]:
        """Haal alle baselines op.

        Returns:
            List van PerformanceBaseline objecten
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """SELECT metric_name, baseline_value, confidence,
                              sample_count, last_updated
                       FROM performance_baselines
                       ORDER BY metric_name"""
                )

                return [
                    PerformanceBaseline(
                        metric_name=row[0],
                        baseline_value=row[1],
                        confidence=row[2],
                        sample_count=row[3],
                        last_updated=row[4],
                    )
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            logger.error(f"Fout bij ophalen alle baselines: {e}")
            return []

    def get_recent_metrics(
        self, metric_name: str, limit: int = 10
    ) -> list[PerformanceMetric]:
        """Haal recente metrics op voor een metric.

        Args:
            metric_name: Naam van metric
            limit: Maximum aantal metrics

        Returns:
            List van PerformanceMetric objecten
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """SELECT metric_name, value, timestamp, metadata
                       FROM performance_metrics
                       WHERE metric_name = ?
                       ORDER BY timestamp DESC
                       LIMIT ?""",
                    (metric_name, limit),
                )

                return [
                    PerformanceMetric(
                        metric_name=row[0],
                        value=row[1],
                        timestamp=row[2],
                        metadata=json.loads(row[3] or "{}"),
                    )
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            logger.error(f"Fout bij ophalen recente metrics voor {metric_name}: {e}")
            return []

    def rename_metric(self, old_name: str, new_name: str) -> bool:
        """Rename een metric (voor migrations).

        Deze functie hernoemt een metric in BOTH de metrics table EN de baselines table.
        Gebruikt transactie om consistentie te garanderen.

        Args:
            old_name: Oude metric naam
            new_name: Nieuwe metric naam

        Returns:
            True als succesvol, False bij fout

        Example:
            tracker.rename_metric("app_startup_ms", "streamlit_rerun_ms")
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check of oude metric bestaat
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM performance_metrics WHERE metric_name = ?",
                    (old_name,),
                )
                old_count = cursor.fetchone()[0]

                if old_count == 0:
                    logger.info(
                        f"Geen data gevonden voor metric '{old_name}', skip rename"
                    )
                    return True

                # Check of nieuwe naam al bestaat
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM performance_metrics WHERE metric_name = ?",
                    (new_name,),
                )
                new_count = cursor.fetchone()[0]

                if new_count > 0:
                    logger.warning(
                        f"Metric '{new_name}' bestaat al met {new_count} records, "
                        f"oude data wordt verwijderd"
                    )
                    # Verwijder oude data met nieuwe naam om duplicaten te voorkomen
                    conn.execute(
                        "DELETE FROM performance_metrics WHERE metric_name = ?",
                        (new_name,),
                    )
                    conn.execute(
                        "DELETE FROM performance_baselines WHERE metric_name = ?",
                        (new_name,),
                    )

                # Rename in beide tables (transactie garandeert atomicity)
                conn.execute(
                    "UPDATE performance_metrics SET metric_name = ? WHERE metric_name = ?",
                    (new_name, old_name),
                )

                conn.execute(
                    "UPDATE performance_baselines SET metric_name = ? WHERE metric_name = ?",
                    (new_name, old_name),
                )

                conn.commit()

                logger.info(
                    f"Metric renamed: '{old_name}' -> '{new_name}' ({old_count} records)"
                )
                return True

        except sqlite3.Error as e:
            logger.error(f"Fout bij renaming metric '{old_name}' -> '{new_name}': {e}")
            return False

    def delete_metric(self, metric_name: str) -> bool:
        """Verwijder alle data voor een metric.

        Args:
            metric_name: Naam van metric om te verwijderen

        Returns:
            True als succesvol, False bij fout
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Verwijder uit beide tables
                conn.execute(
                    "DELETE FROM performance_metrics WHERE metric_name = ?",
                    (metric_name,),
                )
                conn.execute(
                    "DELETE FROM performance_baselines WHERE metric_name = ?",
                    (metric_name,),
                )
                conn.commit()

                logger.info(f"Metric data verwijderd: '{metric_name}'")
                return True

        except sqlite3.Error as e:
            logger.error(f"Fout bij verwijderen metric '{metric_name}': {e}")
            return False


# Global tracker instance (singleton pattern)
_tracker: PerformanceTracker | None = None


def get_tracker() -> PerformanceTracker:
    """Get global performance tracker (singleton).

    Returns:
        PerformanceTracker instance
    """
    global _tracker
    if _tracker is None:
        _tracker = PerformanceTracker()
    return _tracker


def reset_tracker() -> None:
    """Reset global tracker (vooral voor tests)."""
    global _tracker
    _tracker = None
