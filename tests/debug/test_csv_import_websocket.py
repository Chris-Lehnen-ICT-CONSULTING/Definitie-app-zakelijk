"""
Test script voor WebSocket timeout issues tijdens CSV import.
Dit script simuleert verschillende CSV import scenario's om WebSocket timeouts te detecteren.
"""

import csv
import io
import time
from pathlib import Path


def create_test_csv(num_rows: int) -> bytes:
    """Create a test CSV with specified number of rows."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    # Header
    writer.writerow(
        [
            "begrip",
            "definitie",
            "categorie",
            "organisatorische_context",
            "juridische_context",
            "wettelijke_basis",
        ]
    )

    # Data rows
    for i in range(num_rows):
        writer.writerow(
            [
                f"TestBegrip_{i}",
                f"Dit is een test definitie voor begrip {i} met voldoende tekst om realistisch te zijn.",
                "proces",
                "DJI, OM",
                "Strafrecht",
                "Sv, WvSr",
            ]
        )

    return output.getvalue().encode("utf-8-sig")


def test_websocket_timeout_scenarios():
    """Test different CSV sizes for WebSocket timeout issues."""

    test_scenarios = [
        (10, "Small batch - should complete quickly"),
        (50, "Medium batch - potential timeout risk"),
        (100, "Large batch - high timeout risk"),
        (200, "Extra large - likely to timeout without fix"),
    ]

    for num_rows, description in test_scenarios:
        print(f"\n{'='*60}")
        print(f"Testing: {description}")
        print(f"Rows: {num_rows}")
        print("=" * 60)

        csv_data = create_test_csv(num_rows)
        csv_size = len(csv_data) / 1024  # KB

        print(f"CSV size: {csv_size:.1f} KB")

        # Simulate processing time (0.5s per row is realistic for API calls)
        estimated_time = num_rows * 0.5
        print(f"Estimated processing time: {estimated_time:.1f}s")

        if estimated_time > 30:
            print("⚠️  WARNING: High risk of WebSocket timeout!")
            print("    Default Streamlit timeout is ~30s")
            print("    Solution: Yield control every 5 rows")
        elif estimated_time > 15:
            print("⚠️  CAUTION: Moderate risk of timeout")
            print("    Consider batch processing")
        else:
            print("✅ Should complete without timeout")

        # Save test CSV for manual testing
        test_file = Path(f"test_import_{num_rows}_rows.csv")
        test_file.write_bytes(csv_data)
        print(f"Test file saved: {test_file}")


def simulate_import_with_yielding(num_rows: int, yield_interval: int = 5):
    """Simulate import with periodic yielding to prevent timeout."""

    print(
        f"\nSimulating import of {num_rows} rows with yielding every {yield_interval} rows..."
    )

    start_time = time.time()

    for i in range(num_rows):
        # Simulate row processing
        time.sleep(0.1)  # Faster simulation

        # Yield control periodically
        if i > 0 and i % yield_interval == 0:
            print(
                f"  Yielding control at row {i} (elapsed: {time.time() - start_time:.1f}s)"
            )
            time.sleep(0.01)  # Simulate yield

    total_time = time.time() - start_time
    print(f"Completed in {total_time:.1f}s")

    if total_time > 30:
        print(
            "⚠️  Even with yielding, this would risk timeout. Consider smaller batches."
        )
    else:
        print("✅ Import completed within safe timeout window")


if __name__ == "__main__":
    print("WebSocket Timeout Test Suite")
    print("=" * 60)

    # Test different scenarios
    test_websocket_timeout_scenarios()

    print("\n" + "=" * 60)
    print("Testing yielding strategy...")
    print("=" * 60)

    # Test yielding strategy
    simulate_import_with_yielding(50, yield_interval=5)
    simulate_import_with_yielding(100, yield_interval=5)
    simulate_import_with_yielding(100, yield_interval=10)

    print("\n✅ Test complete. Check generated CSV files for manual testing.")
