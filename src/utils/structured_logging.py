"""Structured logging setup for JSON output.

This module provides structured logging capabilities using python-json-logger.
It enables JSON-formatted logs for analytics and monitoring while maintaining
backward compatibility with existing text-based logs.

Usage:
    from utils.structured_logging import setup_structured_logging

    # Enable JSON logging via environment variable
    setup_structured_logging(enable_json=True, log_file='logs/app.json.log')
"""

import logging
import os
from pathlib import Path

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context.

    Adds environment information and standardizes field names for consistency.
    """

    def add_fields(
        self, log_record: dict, record: logging.LogRecord, message_dict: dict
    ):
        """Add custom fields to the log record.

        Args:
            log_record: The dictionary that will be serialized to JSON
            record: The logging.LogRecord instance
            message_dict: Additional message context
        """
        super().add_fields(log_record, record, message_dict)

        # Add environment context
        log_record["environment"] = os.getenv("APP_ENV", "development")

        # Standardize field names (rename after parent processing)
        if "levelname" in log_record:
            log_record["level"] = log_record.pop("levelname")
        if "name" in log_record:
            log_record["logger"] = log_record.pop("name")
        if "asctime" in log_record:
            log_record["timestamp"] = log_record.pop("asctime")

        # Add component if available from extra parameter
        if hasattr(record, "component"):
            log_record["component"] = record.component


def setup_structured_logging(enable_json: bool = False, log_file: str | None = None):
    """Configure structured logging.

    This function sets up JSON-formatted logging when enabled. It maintains
    backward compatibility by only adding JSON logging when explicitly enabled.

    Args:
        enable_json: If True, output JSON format. If False, keep existing text logging.
        log_file: Optional file path for JSON logs. If None, logs to console.

    Example:
        # Enable JSON logging to file
        setup_structured_logging(enable_json=True, log_file='logs/app.json.log')

        # Use structured logging with extra fields
        logger.info("ServiceContainer initialized", extra={
            "component": "service_container",
            "init_count": 1
        })
    """
    if not enable_json:
        return  # Keep existing text logging

    # Create handler (file or console)
    if log_file:
        # Ensure log directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_file, encoding="utf-8")
    else:
        handler = logging.StreamHandler()

    # Create JSON formatter
    formatter = CustomJsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)

    # Add handler to root logger
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def log_with_context(logger: logging.Logger, level: str, message: str, **context):
    """Log a message with structured context fields.

    This is a convenience function for adding structured context to log messages.

    Args:
        logger: Logger instance
        level: Log level ('info', 'debug', 'warning', 'error', 'critical')
        message: Log message (human-readable)
        **context: Additional structured context fields

    Example:
        log_with_context(
            logger, 'info',
            'ServiceContainer initialized',
            component='service_container',
            init_count=1,
            config_hash='abc123'
        )
    """
    log_func = getattr(logger, level.lower())
    log_func(message, extra=context)
