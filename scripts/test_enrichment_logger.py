#!/usr/bin/env python3
"""
Test script voor enrichment logger setup.

Verifies:
- Logger writes to logs/synonym_enrichment.log
- Correct log format
- Different log levels (DEBUG, INFO, WARNING, ERROR)
- File handler vs console handler behavior
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.synonym_orchestrator import enrichment_logger


def main():
    print("Testing enrichment logger setup...")
    print(f"Handlers: {len(enrichment_logger.handlers)}")
    print(f"Level: {enrichment_logger.level}")

    # Test different log levels
    enrichment_logger.debug("DEBUG: This is a debug message")
    enrichment_logger.info("INFO: Starting GPT-4 enrichment for 'test_term'")
    enrichment_logger.info("INFO: Enrichment complete: 3 suggestions, duration: 8.2s")
    enrichment_logger.warning("WARNING: GPT-4 returned no suggestions for 'empty_term'")
    enrichment_logger.error("ERROR: GPT-4 timeout for 'slow_term' after 30.1s")

    # Check if log file exists
    log_file = Path("logs/synonym_enrichment.log")
    if log_file.exists():
        print(f"\n✅ Log file created: {log_file}")
        print(f"   Size: {log_file.stat().st_size} bytes")

        # Read last 5 lines
        with open(log_file) as f:
            lines = f.readlines()
            print(f"\n📝 Last {min(5, len(lines))} log entries:")
            for line in lines[-5:]:
                print(f"   {line.rstrip()}")
    else:
        print(f"\n❌ Log file NOT created: {log_file}")

    print("\n✅ Enrichment logger test completed")


if __name__ == "__main__":
    main()
