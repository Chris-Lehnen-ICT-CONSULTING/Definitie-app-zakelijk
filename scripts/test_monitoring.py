#!/usr/bin/env python
"""
Test runner for monitoring tests with correct Python path setup.

This script ensures that the src/ directory is on the Python path
before running the monitoring tests.
"""
import sys
from pathlib import Path

# Add src to path before any other imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Now run pytest
import pytest

if __name__ == "__main__":
    # Run monitoring tests
    args = [
        "tests/monitoring/",
        "-xvs",
        "--tb=short",
    ]
    sys.exit(pytest.main(args))
