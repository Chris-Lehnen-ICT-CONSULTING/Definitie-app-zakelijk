#!/usr/bin/env python3
"""Test if streamlit runs in async context."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_async_context():
    """Check if we're in an async context."""
    try:
        loop = asyncio.get_event_loop()
        print(f"Event loop found: {loop}")
        print(f"Loop is running: {loop.is_running()}")
        return loop.is_running()
    except RuntimeError as e:
        print(f"No event loop: {e}")
        return False


if __name__ == "__main__":
    print("Testing async context...")
    is_async = check_async_context()
    print(f"In async context: {is_async}")

    # Try to run a simple async function
    async def simple_test():
        return "Test completed"

    try:
        result = asyncio.run(simple_test())
        print(f"asyncio.run worked: {result}")
    except Exception as e:
        print(f"asyncio.run failed: {e}")
