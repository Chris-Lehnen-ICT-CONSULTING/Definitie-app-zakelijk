"""Tests for performance tracking and baseline management.

Test coverage:
- Basic metric tracking
- Baseline calculation (median)
- Confidence scoring
- Regression detection (WARNING/CRITICAL)
- Edge cases (insufficient data, negative values)
- Database persistence
"""

import os
import tempfile
import time

import pytest

from src.monitoring.performance_tracker import (PerformanceBaseline,
                                                PerformanceMetric,
                                                PerformanceTracker,
                                                get_tracker, reset_tracker)


@pytest.fixture()
def temp_db():
    """Fixture voor tijdelijke database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except Exception:
        pass


@pytest.fixture()
def tracker(temp_db):
    """Fixture voor performance tracker met tijdelijke database."""
    return PerformanceTracker(temp_db)


class TestPerformanceTracker:
    """Test suite voor PerformanceTracker."""

    def test_track_single_metric(self, tracker):
        """Test opslaan van enkele metric."""
        tracker.track_metric("test_metric", 100.0, metadata={"test": "value"})

        # Haal metric op
        metrics = tracker.get_recent_metrics("test_metric", limit=1)
        assert len(metrics) == 1
        assert metrics[0].metric_name == "test_metric"
        assert metrics[0].value == 100.0
        assert metrics[0].metadata == {"test": "value"}

    def test_track_multiple_metrics(self, tracker):
        """Test opslaan van meerdere metrics."""
        for i in range(10):
            tracker.track_metric("test_metric", 100.0 + i)

        metrics = tracker.get_recent_metrics("test_metric", limit=10)
        assert len(metrics) == 10

        # Check dat ze in omgekeerde chronologische volgorde zijn
        values = [m.value for m in metrics]
        assert values == [
            109.0,
            108.0,
            107.0,
            106.0,
            105.0,
            104.0,
            103.0,
            102.0,
            101.0,
            100.0,
        ]

    def test_baseline_calculation_median(self, tracker):
        """Test baseline berekening met median."""
        # Track 10 metrics: 100, 101, 102, ..., 109
        for i in range(10):
            tracker.track_metric("test_metric", 100.0 + i)

        baseline = tracker.get_baseline("test_metric")
        assert baseline is not None

        # Median van 100..109 = 104.5 (gemiddelde van 104 en 105)
        assert baseline.baseline_value == 104.5
        assert baseline.sample_count == 10
        assert baseline.confidence == 0.5  # 10/20

    def test_baseline_calculation_odd_samples(self, tracker):
        """Test baseline met oneven aantal samples."""
        # Track 11 metrics: 100, 101, ..., 110
        for i in range(11):
            tracker.track_metric("test_metric", 100.0 + i)

        baseline = tracker.get_baseline("test_metric")
        assert baseline is not None

        # Median van 100..110 = 105 (middelste waarde)
        assert baseline.baseline_value == 105.0

    def test_baseline_not_calculated_insufficient_data(self, tracker):
        """Test dat baseline niet berekend wordt met te weinig data."""
        # Track 4 metrics (minder dan MIN_SAMPLES=5)
        for _ in range(4):
            tracker.track_metric("test_metric", 100.0)

        baseline = tracker.get_baseline("test_metric")
        assert baseline is None

    def test_confidence_increases_with_samples(self, tracker):
        """Test dat confidence stijgt met aantal samples."""
        # 5 samples = 25% confidence
        for _ in range(5):
            tracker.track_metric("test_metric", 100.0)

        baseline = tracker.get_baseline("test_metric")
        assert baseline.confidence == 0.25  # 5/20

        # 10 samples = 50% confidence
        for i in range(5, 10):
            tracker.track_metric("test_metric", 100.0)

        baseline = tracker.get_baseline("test_metric")
        assert baseline.confidence == 0.5  # 10/20

        # 20 samples = 100% confidence
        for i in range(10, 20):
            tracker.track_metric("test_metric", 100.0)

        baseline = tracker.get_baseline("test_metric")
        assert baseline.confidence == 1.0  # 20/20

    def test_regression_detection_critical(self, tracker):
        """Test CRITICAL regression detection (>20% slechter)."""
        # Maak baseline van 100
        for i in range(10):
            tracker.track_metric("test_metric", 100.0)

        # Test waarde 25% slechter = CRITICAL
        alert = tracker.check_regression("test_metric", 125.0)
        assert alert == "CRITICAL"

    def test_regression_detection_warning(self, tracker):
        """Test WARNING regression detection (>10% slechter)."""
        # Maak baseline van 100
        for i in range(10):
            tracker.track_metric("test_metric", 100.0)

        # Test waarde 15% slechter = WARNING
        alert = tracker.check_regression("test_metric", 115.0)
        assert alert == "WARNING"

    def test_regression_detection_ok(self, tracker):
        """Test dat geen alert wordt gegeven bij acceptabele waarden."""
        # Maak baseline van 100
        for i in range(10):
            tracker.track_metric("test_metric", 100.0)

        # Test waarde 5% slechter = OK
        alert = tracker.check_regression("test_metric", 105.0)
        assert alert is None

        # Test waarde beter dan baseline = OK
        alert = tracker.check_regression("test_metric", 90.0)
        assert alert is None

    def test_regression_no_alert_low_confidence(self, tracker):
        """Test dat geen alert wordt gegeven bij lage confidence."""
        # Maak baseline met lage confidence (8 samples = 40%)
        for i in range(8):
            tracker.track_metric("test_metric", 100.0)

        # Test waarde 25% slechter, maar confidence < 50%
        alert = tracker.check_regression("test_metric", 125.0)
        assert alert is None

    def test_regression_no_baseline(self, tracker):
        """Test dat geen alert wordt gegeven zonder baseline."""
        alert = tracker.check_regression("nonexistent_metric", 100.0)
        assert alert is None

    def test_get_all_baselines(self, tracker):
        """Test ophalen van alle baselines."""
        # Maak baselines voor meerdere metrics
        for metric_name in ["metric_a", "metric_b", "metric_c"]:
            for i in range(10):
                tracker.track_metric(metric_name, 100.0 + i)

        baselines = tracker.get_all_baselines()
        assert len(baselines) == 3

        metric_names = {b.metric_name for b in baselines}
        assert metric_names == {"metric_a", "metric_b", "metric_c"}

    def test_baseline_sliding_window(self, tracker):
        """Test dat baseline gebruikt maakt van sliding window."""
        # Track 25 metrics (meer dan BASELINE_WINDOW=20)
        for i in range(25):
            tracker.track_metric("test_metric", 100.0 + i)

        baseline = tracker.get_baseline("test_metric")

        # Baseline zou gebaseerd moeten zijn op laatste 20: 105..124
        # Median van 105..124 = 114.5
        assert baseline.baseline_value == 114.5
        assert baseline.sample_count == 20
        assert baseline.confidence == 1.0

    def test_metadata_persistence(self, tracker):
        """Test dat metadata correct wordt opgeslagen en opgehaald."""
        metadata = {"version": "2.0", "platform": "darwin", "nested": {"key": "value"}}

        tracker.track_metric("test_metric", 100.0, metadata=metadata)

        metrics = tracker.get_recent_metrics("test_metric", limit=1)
        assert metrics[0].metadata == metadata

    def test_negative_value_rejected(self, tracker):
        """Test dat negatieve waarden worden afgewezen."""
        with pytest.raises(ValueError, match="non-negative"):
            tracker.track_metric("test_metric", -10.0)

    def test_zero_value_allowed(self, tracker):
        """Test dat nul als waarde is toegestaan."""
        tracker.track_metric("test_metric", 0.0)

        metrics = tracker.get_recent_metrics("test_metric", limit=1)
        assert metrics[0].value == 0.0

    def test_multiple_metrics_independent(self, tracker):
        """Test dat verschillende metrics onafhankelijk zijn."""
        # Track metric A
        for i in range(10):
            tracker.track_metric("metric_a", 100.0 + i)

        # Track metric B
        for i in range(10):
            tracker.track_metric("metric_b", 200.0 + i)

        baseline_a = tracker.get_baseline("metric_a")
        baseline_b = tracker.get_baseline("metric_b")

        assert baseline_a.baseline_value == 104.5  # median van 100..109
        assert baseline_b.baseline_value == 204.5  # median van 200..209

    def test_database_persistence(self, temp_db):
        """Test dat data persistent is over tracker instanties."""
        # Eerste tracker: opslaan
        tracker1 = PerformanceTracker(temp_db)
        for i in range(10):
            tracker1.track_metric("test_metric", 100.0 + i)

        # Tweede tracker: ophalen
        tracker2 = PerformanceTracker(temp_db)
        baseline = tracker2.get_baseline("test_metric")

        assert baseline is not None
        assert baseline.baseline_value == 104.5

        metrics = tracker2.get_recent_metrics("test_metric", limit=10)
        assert len(metrics) == 10


class TestGlobalTracker:
    """Test suite voor global tracker singleton."""

    def test_get_tracker_singleton(self):
        """Test dat get_tracker altijd dezelfde instance teruggeeft."""
        reset_tracker()  # Start clean

        tracker1 = get_tracker()
        tracker2 = get_tracker()

        assert tracker1 is tracker2

    def test_reset_tracker(self):
        """Test dat reset_tracker nieuwe instance maakt."""
        reset_tracker()

        tracker1 = get_tracker()
        reset_tracker()
        tracker2 = get_tracker()

        assert tracker1 is not tracker2


class TestRealWorldScenarios:
    """Test suite voor realistische scenario's."""

    def test_startup_time_tracking(self, tracker):
        """Test tracking van app startup tijd."""
        # Simuleer 20 app starts met variërende startup tijden
        startup_times = [
            210,
            205,
            215,
            208,
            212,  # Week 1: ~210ms
            220,
            225,
            218,
            222,
            223,  # Week 2: verslechtering
            400,
            410,
            405,
            398,
            407,  # Week 3: regressie!
            200,
            205,
            208,
            202,
            207,  # Week 4: fix
        ]

        for i, startup_ms in enumerate(startup_times):
            tracker.track_metric("app_startup_ms", startup_ms)

            # Check regression na elke meting
            if i >= 9:  # Na eerste 10 metingen hebben we baseline
                alert = tracker.check_regression("app_startup_ms", startup_ms)

                if i < 10:
                    # Week 1-2: geen regressie
                    assert alert is None or alert == "WARNING"
                elif 10 <= i < 15:
                    # Week 3: regressie gedetecteerd!
                    assert alert in ["WARNING", "CRITICAL"]
                else:
                    # Week 4: fix, geen regressie
                    pass  # Afhankelijk van sliding window

    def test_multiple_performance_metrics(self, tracker):
        """Test tracking van meerdere performance metrics."""
        metrics_config = {
            "app_startup_ms": (200, 300),
            "definition_generation_ms": (3000, 5000),
            "validation_ms": (800, 1200),
            "export_ms": (1500, 2000),
        }

        # Track alle metrics
        for metric_name, (min_val, max_val) in metrics_config.items():
            for i in range(15):
                # Variërende waarden
                value = min_val + (max_val - min_val) * i / 15
                tracker.track_metric(metric_name, value)

        # Verify alle baselines
        baselines = tracker.get_all_baselines()
        assert len(baselines) == 4

        for baseline in baselines:
            assert baseline.confidence >= 0.75  # 15/20
            assert baseline.sample_count == 15
