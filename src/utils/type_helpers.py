"""
Type conversion and validation utilities.

This module provides centralized type handling functions to ensure
consistent type checking and conversion throughout the application.
"""

from typing import Any


def validate_type(
    value: Any,
    expected_type: type,
    error_message: str | None = None,
    raise_on_invalid: bool = True,
) -> bool:
    """
    Validate value type with consistent error handling.

    Args:
        value: Value to check
        expected_type: Expected type
        error_message: Custom error message
        raise_on_invalid: Whether to raise exception

    Returns:
        True if valid, False otherwise

    Raises:
        TypeError: If raise_on_invalid and type is invalid
    """
    if not isinstance(value, expected_type):
        if raise_on_invalid:
            msg = error_message or f"Expected {expected_type.__name__}, got {type(value).__name__}"
            raise TypeError(msg)
        return False
    return True


def ensure_list(value: Any, default: list | None = None) -> list:
    """
    Ensure value is a list.

    Args:
        value: Value to check
        default: Default list if value is invalid

    Returns:
        Valid list
    """
    if isinstance(value, list):
        return value
    return default if default is not None else []


def ensure_dict(value: Any, default: dict | None = None) -> dict:
    """
    Ensure value is a dictionary.

    Args:
        value: Value to check
        default: Default dict if value is invalid

    Returns:
        Valid dictionary
    """
    if isinstance(value, dict):
        return value
    return default if default is not None else {}


def ensure_string(value: Any, default: str = "") -> str:
    """
    Ensure value is a string.

    Args:
        value: Value to check
        default: Default string if value is invalid

    Returns:
        Valid string
    """
    if isinstance(value, str):
        return value
    if value is None:
        return default
    return str(value)