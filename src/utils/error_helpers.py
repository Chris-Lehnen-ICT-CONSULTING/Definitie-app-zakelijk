"""
Error handling utilities.

This module provides centralized error handling patterns including
safe execution, error decorators, and service error management.
"""

import logging
from functools import wraps
from typing import Any, Callable, TypeVar, cast

import streamlit as st

# Type variables for generic functions
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def safe_execute(
    func: Callable[[], T],
    default: T,
    error_message: str | None = None,
    logger: logging.Logger | None = None,
    raise_on_error: bool = False,
) -> T:
    """
    Execute a function with standardized error handling.

    Args:
        func: Function to execute
        default: Default value to return on error
        error_message: Optional error message to log
        logger: Optional logger instance
        raise_on_error: Whether to re-raise exceptions

    Returns:
        Function result or default value on error
    """
    try:
        return func()
    except Exception as e:
        if logger and error_message:
            logger.error(f"{error_message}: {e}")
        elif logger:
            logger.error(f"Error in {func.__name__ if hasattr(func, '__name__') else 'operation'}: {e}")

        if raise_on_error:
            raise
        return default


def error_handler(
    error_message: str | None = None,
    default_return: Any = None,
    logger_name: str | None = None,
    show_st_error: bool = False,
) -> Callable[[F], F]:
    """
    Decorator for consistent error handling.

    Args:
        error_message: Custom error message
        default_return: Value to return on error
        logger_name: Logger name to use
        show_st_error: Whether to show Streamlit error

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if logger_name:
                    logger = logging.getLogger(logger_name)
                    msg = error_message or f"Error in {func.__name__}"
                    logger.error(f"{msg}: {e}")

                if show_st_error:
                    st.error(f"{error_message or 'An error occurred'}: {e!s}")

                return default_return
        return cast(F, wrapper)
    return decorator


def handle_service_error(
    operation: str,
    error: Exception,
    logger: logging.Logger | None = None,
    show_ui: bool = False,
    default_return: Any = None,
) -> Any:
    """
    Handle service layer errors with consistent logging and UI feedback.

    Args:
        operation: Description of the operation that failed
        error: The exception that occurred
        logger: Optional logger for recording
        show_ui: Whether to show error in UI
        default_return: Value to return

    Returns:
        The default return value
    """
    error_msg = f"Error in {operation}: {error!s}"

    if logger:
        logger.error(error_msg, exc_info=True)

    if show_ui:
        st.error(error_msg)

    return default_return