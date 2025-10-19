"""
Dictionary operation utilities.

This module provides safe dictionary manipulation functions
with support for nested access and type validation.
"""

from typing import Any


def safe_dict_get(
    dictionary: dict[str, Any] | None,
    key: str,
    default: Any = None,
    expected_type: type | None = None,
) -> Any:
    """
    Safely get value from dictionary with type checking.

    Args:
        dictionary: Source dictionary
        key: Key to retrieve
        default: Default value
        expected_type: Expected type for validation

    Returns:
        Value from dictionary or default
    """
    if not dictionary or not isinstance(dictionary, dict):
        return default

    value = dictionary.get(key, default)

    if expected_type and value is not None and not isinstance(value, expected_type):
        return default

    return value


def get_nested_dict_value(
    dictionary: dict[str, Any] | None,
    *keys: str,
    default: Any = None,
) -> Any:
    """
    Get nested dictionary value safely.

    Args:
        dictionary: Source dictionary
        *keys: Sequence of keys to traverse
        default: Default value

    Returns:
        Nested value or default
    """
    if not dictionary:
        return default

    current = dictionary
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default

    return current if current is not None else default
