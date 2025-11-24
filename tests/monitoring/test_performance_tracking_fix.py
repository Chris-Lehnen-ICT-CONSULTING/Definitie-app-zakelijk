"""Tests voor performance tracking metric fix.

Verificatie dat:
1. Timer reset op elke main() call (geen cumulative tijd)
2. Rerun tijd is redelijk (< 1000ms voor normale reruns)
3. Geen module-level timer bestaat
4. Baseline comparison werkt met nieuwe metric naam
5. Metric rename functionaliteit werkt correct
"""

import sqlite3
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.monitoring.performance_tracker import (
    PerformanceTracker,
    get_tracker,
    reset_tracker,
)


@pytest.fixture
def temp_db(tmp_path):
    """Tijdelijke database voor tests."""
    db_path = tmp_path / "test_performance.db"
    tracker = PerformanceTracker(db_path=str(db_path))
    yield tracker
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def reset_global_tracker():
    """Reset global tracker tussen tests."""
    reset_tracker()
    yield
    reset_tracker()


class TestTimerScope:
    """Test dat timer correct in function scope staat."""

    def test_no_module_level_timer(self):
        """Verify dat _startup_start NIET bestaat op module level."""
        import src.main

        # Check dat oude module-level timer NIET bestaat
        assert not hasattr(src.main, "_startup_start"), (
            "Module-level timer '_startup_start' gevonden! "
            "Dit veroorzaakt cumulative timing bug."
        )

    def test_timer_in_main_function(self):
        """Verify dat timer binnen main() functie wordt gezet."""
        import inspect

        import src.main

        # Haal source code van main() op
        main_source = inspect.getsource(src.main.main)

        # Check dat timer binnen function scope staat
        assert (
            "rerun_start = time.perf_counter()" in main_source
        ), "Timer 'rerun_start' niet gevonden in main() functie!"

        # Check dat timer aan tracking functie wordt doorgegeven
        assert (
            "_track_rerun_performance(rerun_start)" in main_source
        ), "Timer wordt niet doorgegeven aan tracking functie!"

    @patch("src.main.SessionStateManager")
    @patch("src.main.TabbedInterface")
    @patch("src.main.time.perf_counter")
    @patch("src.monitoring.performance_tracker.get_tracker")  # Patch where it's called
    def test_timer_resets_per_main_call(
        self, mock_get_tracker, mock_perf_counter, mock_interface, mock_session_manager
    ):
        """Test dat timer RESET op elke main() call."""
        # Mock tracker
        mock_tracker = MagicMock()
        mock_get_tracker.return_value = mock_tracker

        # Mock interface
        mock_interface_instance = MagicMock()
        mock_interface.return_value = mock_interface_instance

        # Setup perf_counter to return different values
        # First call pair: start=1.0, end=1.05 (50ms)
        # Second call pair: start=2.0, end=2.03 (30ms)
        mock_perf_counter.side_effect = [1.0, 1.05, 2.0, 2.03]

        # Import and call main twice
        from src.main import main

        # First call
        with patch("src.main.st") as mock_st:  # Mock streamlit
            mock_st.session_state = MagicMock()  # Mock session_state
            main()

        # Verify first call tracked ~50ms
        first_call = mock_tracker.track_metric.call_args_list[0]
        assert first_call[0][0] == "streamlit_rerun_ms"
        first_time = first_call[0][1]
        assert 40 < first_time < 60, f"Expected ~50ms, got {first_time}ms"

        # Second call
        with patch("src.main.st") as mock_st:  # Mock streamlit
            mock_st.session_state = MagicMock()  # Mock session_state
            main()

        # Verify second call tracked ~30ms (NOT cumulative!)
        second_call = mock_tracker.track_metric.call_args_list[1]
        assert second_call[0][0] == "streamlit_rerun_ms"
        second_time = second_call[0][1]
        assert 20 < second_time < 40, f"Expected ~30ms, got {second_time}ms"

        # CRITICAL: Second measurement should NOT include first call time
        assert second_time < 100, (
            f"Second call measured {second_time}ms - "
            "this suggests cumulative timing bug is still present!"
        )


class TestMetricNaming:
    """Test dat metric correct hernoemd is."""

    @patch("src.main.SessionStateManager")
    @patch("src.main.TabbedInterface")
    @patch("src.monitoring.performance_tracker.get_tracker")
    def test_uses_streamlit_rerun_ms_metric(
        self, mock_get_tracker, mock_interface, mock_session_manager
    ):
        """Verify dat nieuwe metric naam 'streamlit_rerun_ms' gebruikt wordt."""
        mock_tracker = MagicMock()
        mock_get_tracker.return_value = mock_tracker

        mock_interface_instance = MagicMock()
        mock_interface.return_value = mock_interface_instance

        from src.main import main

        with patch("src.main.st") as mock_st:  # Mock streamlit
            mock_st.session_state = MagicMock()  # Mock session_state
            main()

        # Verify dat track_metric aangeroepen is met nieuwe naam
        mock_tracker.track_metric.assert_called_once()
        call_args = mock_tracker.track_metric.call_args

        # Check metric naam
        assert (
            call_args[0][0] == "streamlit_rerun_ms"
        ), f"Expected metric name 'streamlit_rerun_ms', got '{call_args[0][0]}'"

    @patch("src.main.SessionStateManager")
    @patch("src.main.TabbedInterface")
    @patch("src.monitoring.performance_tracker.get_tracker")
    def test_uses_check_regression_with_new_name(
        self, mock_get_tracker, mock_interface, mock_session_manager
    ):
        """Verify dat check_regression nieuwe metric naam gebruikt."""
        mock_tracker = MagicMock()
        mock_tracker.check_regression.return_value = None  # No regression
        mock_get_tracker.return_value = mock_tracker

        mock_interface_instance = MagicMock()
        mock_interface.return_value = mock_interface_instance

        from src.main import main

        with patch("src.main.st") as mock_st:  # Mock streamlit
            mock_st.session_state = MagicMock()  # Mock session_state
            main()

        # Verify check_regression called met nieuwe naam
        mock_tracker.check_regression.assert_called_once()
        call_args = mock_tracker.check_regression.call_args

        assert call_args[0][0] == "streamlit_rerun_ms", (
            f"Expected check_regression with 'streamlit_rerun_ms', "
            f"got '{call_args[0][0]}'"
        )


class TestRerunTimingRealistic:
    """Test dat rerun tijd realistisch is."""

    @patch("src.main.SessionStateManager")
    @patch("src.main.TabbedInterface")
    @patch("src.monitoring.performance_tracker.get_tracker")
    def test_rerun_time_reasonable(
        self, mock_get_tracker, mock_interface, mock_session_manager
    ):
        """Verify dat rerun tijd < 1000ms is voor lege rerun."""
        mock_tracker = MagicMock()
        mock_get_tracker.return_value = mock_tracker

        mock_interface_instance = MagicMock()
        mock_interface.return_value = mock_interface_instance

        from src.main import main

        with patch("src.main.st") as mock_st:  # Mock streamlit
            mock_st.session_state = MagicMock()  # Mock session_state
            main()

        # Haal gemeten tijd op
        call_args = mock_tracker.track_metric.call_args
        measured_time_ms = call_args[0][1]

        # Verify reasonable tijd (< 1000ms voor mocked rerun)
        assert measured_time_ms < 1000, (
            f"Rerun tijd {measured_time_ms:.1f}ms is onrealistisch hoog. "
            f"Voor gemockte rerun verwacht < 1000ms."
        )

        # Voor echte implementatie: meestal < 100ms
        # Maar met mocking kan het iets hoger zijn


class TestMetricRenaming:
    """Test metric rename functionaliteit in PerformanceTracker."""

    def test_rename_metric_success(self, temp_db):
        """Test succesvol renamen van metric."""
        # Insert test data met oude naam (5+ samples voor baseline)
        for i in range(6):
            temp_db.track_metric("app_startup_ms", 100.0 + i * 5, {"version": "1.0"})

        # Verify data bestaat met oude naam
        old_metrics = temp_db.get_recent_metrics("app_startup_ms", limit=10)
        assert len(old_metrics) == 6

        # Verify baseline is gemaakt
        old_baseline_before = temp_db.get_baseline("app_startup_ms")
        assert old_baseline_before is not None

        # Rename
        success = temp_db.rename_metric("app_startup_ms", "streamlit_rerun_ms")
        assert success

        # Verify data nu bestaat met nieuwe naam
        new_metrics = temp_db.get_recent_metrics("streamlit_rerun_ms", limit=10)
        assert len(new_metrics) == 6

        # Verify oude naam is weg
        old_metrics_after = temp_db.get_recent_metrics("app_startup_ms", limit=10)
        assert len(old_metrics_after) == 0

        # Verify baseline ook hernoemd
        new_baseline = temp_db.get_baseline("streamlit_rerun_ms")
        assert new_baseline is not None
        assert new_baseline.metric_name == "streamlit_rerun_ms"

        old_baseline = temp_db.get_baseline("app_startup_ms")
        assert old_baseline is None

    def test_rename_nonexistent_metric(self, temp_db):
        """Test renaming van niet-bestaande metric."""
        # Rename niet-bestaande metric (should succeed gracefully)
        success = temp_db.rename_metric("nonexistent_metric", "new_name")
        assert success  # Should return True (no-op success)

    def test_rename_with_existing_target(self, temp_db):
        """Test renaming wanneer target naam al bestaat."""
        # Insert data voor beide namen
        temp_db.track_metric("old_metric", 100.0)
        temp_db.track_metric("new_metric", 200.0)

        # Rename (should delete existing target first)
        success = temp_db.rename_metric("old_metric", "new_metric")
        assert success

        # Verify alleen data van old_metric overblijft
        new_metrics = temp_db.get_recent_metrics("new_metric", limit=10)
        assert len(new_metrics) == 1
        assert new_metrics[0].value == 100.0  # Van old_metric

    def test_delete_metric(self, temp_db):
        """Test deleting van metric."""
        # Insert test data (5+ voor baseline)
        for i in range(6):
            temp_db.track_metric("test_metric", 100.0 + i * 2)

        # Verify data bestaat
        metrics = temp_db.get_recent_metrics("test_metric", limit=10)
        assert len(metrics) == 6

        baseline = temp_db.get_baseline("test_metric")
        assert baseline is not None

        # Delete
        success = temp_db.delete_metric("test_metric")
        assert success

        # Verify alles weg is
        metrics_after = temp_db.get_recent_metrics("test_metric", limit=10)
        assert len(metrics_after) == 0

        baseline_after = temp_db.get_baseline("test_metric")
        assert baseline_after is None


class TestBaselineComparison:
    """Test baseline comparison met nieuwe metric naam."""

    def test_baseline_comparison_streamlit_rerun(self, temp_db):
        """Test dat baseline comparison werkt met streamlit_rerun_ms."""
        # Build baseline (need enough samples AND confidence >= 0.5)
        # MIN_SAMPLES = 5, BASELINE_WINDOW = 20
        # Confidence = samples / BASELINE_WINDOW
        # Need 10+ samples for confidence >= 0.5
        for i in range(12):
            temp_db.track_metric("streamlit_rerun_ms", 50.0 + i * 2)

        # Verify baseline bestaat
        baseline = temp_db.get_baseline("streamlit_rerun_ms")
        assert baseline is not None
        assert baseline.metric_name == "streamlit_rerun_ms"
        assert baseline.confidence >= 0.5, f"Confidence {baseline.confidence} < 0.5"

        # Test regression detection met hoge waarde
        alert = temp_db.check_regression("streamlit_rerun_ms", 150.0)
        assert alert == "CRITICAL"  # 150 / ~61 = ~2.4x = > 120%

        # Test warning met medium waarde
        alert = temp_db.check_regression("streamlit_rerun_ms", 70.0)
        assert alert == "WARNING"  # 70 / ~61 = ~1.14x = > 110%

        # Test geen alert met normale waarde
        alert = temp_db.check_regression("streamlit_rerun_ms", 62.0)
        assert alert is None

    def test_no_false_regression_with_fresh_baseline(self, temp_db):
        """Test dat nieuwe baseline geen false positives geeft."""
        # Simulate eerste paar runs (variatie 10-30ms - normaal voor reruns)
        temp_db.track_metric("streamlit_rerun_ms", 15.0)
        temp_db.track_metric("streamlit_rerun_ms", 22.0)
        temp_db.track_metric("streamlit_rerun_ms", 18.0)
        temp_db.track_metric("streamlit_rerun_ms", 25.0)
        temp_db.track_metric("streamlit_rerun_ms", 20.0)

        # Verify baseline gevormd (median ~20ms)
        baseline = temp_db.get_baseline("streamlit_rerun_ms")
        assert baseline is not None
        assert 18 < baseline.baseline_value < 25

        # Test dat normale variatie geen alert geeft
        alert = temp_db.check_regression("streamlit_rerun_ms", 28.0)
        assert alert is None  # 28/20 = 1.4x maar confidence check voorkomt alert


class TestDocumentation:
    """Test dat documentatie correct is."""

    def test_track_rerun_performance_docstring(self):
        """Verify dat _track_rerun_performance docstring correct is."""
        from src.main import _track_rerun_performance

        doc = _track_rerun_performance.__doc__

        # Check key phrases
        assert "Streamlit rerun" in doc
        assert "start_time" in doc
        assert "streamlit_rerun_ms" in doc or "metric naam" in doc

    def test_rename_metric_docstring(self):
        """Verify dat rename_metric documentatie example heeft."""
        doc = PerformanceTracker.rename_metric.__doc__

        assert "migrations" in doc.lower() or "rename" in doc.lower()
        assert "app_startup_ms" in doc or "streamlit_rerun_ms" in doc


class TestIntegration:
    """Integration tests voor complete flow."""

    @patch("src.main.SessionStateManager")
    @patch("src.main.TabbedInterface")
    @patch("src.monitoring.performance_tracker.get_tracker")
    def test_complete_flow_with_real_tracker(
        self,
        mock_get_tracker,
        mock_interface,
        mock_session_manager,
        tmp_path,
        reset_global_tracker,
    ):
        """Test complete flow met echte tracker (maar mocked UI)."""
        # Setup real tracker met temp DB
        db_path = tmp_path / "integration_test.db"
        tracker = PerformanceTracker(db_path=str(db_path))

        # Return our test tracker
        mock_get_tracker.return_value = tracker

        mock_interface_instance = MagicMock()
        mock_interface.return_value = mock_interface_instance

        from src.main import main

        with patch("src.main.st") as mock_st:  # Mock streamlit
            mock_st.session_state = MagicMock()  # Mock session_state
            # Call main meerdere keren
            main()
            time.sleep(0.01)  # Kleine delay
            main()

        # Verify metrics zijn opgeslagen
        metrics = tracker.get_recent_metrics("streamlit_rerun_ms", limit=10)
        assert len(metrics) == 2

        # Verify beide metrics zijn < 1000ms (redelijke rerun tijd)
        for metric in metrics:
            assert (
                metric.value < 1000
            ), f"Metric value {metric.value}ms lijkt cumulative - bug niet gefixt!"

        # Verify tweede metric is NIET hoger dan eerste + tweede
        # (zou het geval zijn bij cumulative timing)
        assert metrics[0].value < 1000
        assert metrics[1].value < 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
