#!/usr/bin/env python3
"""
WebSocket Health Monitor voor Streamlit applicatie.
Monitort de WebSocket verbinding tijdens langdurige operaties.
"""

import logging
import time

import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketMonitor:
    """Monitor WebSocket health during long operations."""

    def __init__(self, timeout_threshold: float = 25.0):
        """Initialize monitor with timeout threshold (seconds)."""
        self.timeout_threshold = timeout_threshold
        self.last_heartbeat = time.time()
        self.operation_start = None
        self.warnings_issued = 0

    def start_operation(self, operation_name: str):
        """Mark start of a long operation."""
        self.operation_start = time.time()
        self.last_heartbeat = time.time()
        logger.info(f"Started monitoring: {operation_name}")

    def heartbeat(self):
        """Record a heartbeat (UI update)."""
        self.last_heartbeat = time.time()

    def check_health(self) -> tuple[bool, str | None]:
        """Check WebSocket health.

        Returns:
            (is_healthy, warning_message)
        """
        if not self.operation_start:
            return True, None

        elapsed = time.time() - self.last_heartbeat

        if elapsed > self.timeout_threshold:
            self.warnings_issued += 1
            return False, f"⚠️ WebSocket timeout risk! No update for {elapsed:.1f}s"
        elif elapsed > self.timeout_threshold * 0.7:
            return True, f"⚠️ WebSocket warning: {elapsed:.1f}s since last update"

        return True, None

    def get_stats(self) -> dict:
        """Get monitoring statistics."""
        if not self.operation_start:
            return {}

        total_time = time.time() - self.operation_start
        time_since_heartbeat = time.time() - self.last_heartbeat

        return {
            "operation_duration": f"{total_time:.1f}s",
            "last_heartbeat": f"{time_since_heartbeat:.1f}s ago",
            "warnings_issued": self.warnings_issued,
            "health_status": (
                "🟢 Healthy" if time_since_heartbeat < 10 else "🟡 At Risk"
            ),
        }


def monitor_csv_import(df_size: int) -> WebSocketMonitor:
    """Create and configure monitor for CSV import."""
    monitor = WebSocketMonitor()

    # Estimate timeout risk based on size
    estimated_time = df_size * 0.5  # 0.5s per row estimate

    if estimated_time > 30:
        st.warning(
            f"⚠️ Large import detected ({df_size} rows). "
            f"Estimated time: {estimated_time:.0f}s. "
            "WebSocket monitoring enabled."
        )

    return monitor


def safe_import_with_monitoring(rows, process_func, monitor: WebSocketMonitor):
    """Safely import rows with WebSocket monitoring.

    Args:
        rows: Iterable of rows to process
        process_func: Function to process each row
        monitor: WebSocketMonitor instance

    Returns:
        List of results
    """
    results = []
    batch_size = 5  # Yield every 5 rows

    monitor.start_operation(f"Import {len(rows)} rows")

    for i, row in enumerate(rows):
        try:
            # Process row
            result = process_func(row)
            results.append(result)

            # Update progress and heartbeat
            if i % batch_size == 0:
                monitor.heartbeat()
                is_healthy, warning = monitor.check_health()

                if not is_healthy:
                    logger.error(warning)
                    st.error(warning)
                    # Force reconnect attempt
                    st.empty()
                    time.sleep(0.1)
                elif warning:
                    logger.warning(warning)

        except Exception as e:
            logger.error(f"Error processing row {i}: {e}")
            results.append({"error": str(e)})

    # Final stats
    stats = monitor.get_stats()
    logger.info(f"Import completed: {stats}")

    return results


if __name__ == "__main__":
    # Demo monitoring
    print("WebSocket Monitor Demo")
    print("-" * 40)

    monitor = WebSocketMonitor(timeout_threshold=5.0)  # Short timeout for demo

    monitor.start_operation("Demo Import")

    for i in range(20):
        time.sleep(0.5)

        if i % 3 == 0:
            monitor.heartbeat()
            print(f"✓ Heartbeat at {i}")

        is_healthy, warning = monitor.check_health()
        if warning:
            print(warning)

    stats = monitor.get_stats()
    print("\nFinal Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
