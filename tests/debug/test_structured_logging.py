#!/usr/bin/env python3
"""Quick test script to verify structured logging functionality."""

import logging
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Enable structured logging
os.environ['STRUCTURED_LOGGING'] = 'true'

from utils.structured_logging import setup_structured_logging

# Setup structured logging
setup_structured_logging(enable_json=True, log_file='logs/test_structured.json.log')

# Get a logger
logger = logging.getLogger('test')

# Test basic logging
logger.info("Test message without structured context")

# Test structured logging with extra fields
logger.info("ServiceContainer initialized", extra={
    "component": "service_container",
    "init_count": 1,
    "environment": "testing"
})

# Test with multiple fields
logger.info("Operation completed", extra={
    "component": "test_service",
    "operation": "test_operation",
    "duration_ms": 123,
    "success": True
})

# Test error logging
logger.error("Test error occurred", extra={
    "component": "test_service",
    "error_type": "TestError",
    "operation": "test_operation"
})

print("\n✅ Structured logging test completed!")
print(f"📄 Check log file: logs/test_structured.json.log")
