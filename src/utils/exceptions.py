"""
Custom exceptions and error handling utilities for DefinitieAgent.
"""

import logging
from typing import Optional, Any
from functools import wraps


class DefinitieAgentError(Exception):
    """Base exception for DefinitieAgent application."""
    pass


class APIError(DefinitieAgentError):
    """Exception for API-related errors (OpenAI, web lookups)."""
    pass


class ValidationError(DefinitieAgentError):
    """Exception for validation and quality testing errors."""
    pass


class ConfigurationError(DefinitieAgentError):
    """Exception for configuration loading errors."""
    pass


class ExportError(DefinitieAgentError):
    """Exception for export functionality errors."""
    pass


def handle_api_error(func):
    """Decorator to handle API errors gracefully."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"API error in {func.__name__}: {str(e)}")
            raise APIError(f"API call failed: {str(e)}") from e
    return wrapper


def handle_validation_error(func):
    """Decorator to handle validation errors gracefully."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Validation error in {func.__name__}: {str(e)}")
            raise ValidationError(f"Validation failed: {str(e)}") from e
    return wrapper


def safe_execute(func, default_value: Any = None, error_message: str = ""):
    """
    Safely execute a function and return default value on error.
    
    Args:
        func: Function to execute
        default_value: Value to return on error
        error_message: Custom error message to log
        
    Returns:
        Function result or default_value on error
    """
    try:
        return func()
    except Exception as e:
        if error_message:
            logging.error(f"{error_message}: {str(e)}")
        else:
            logging.error(f"Error in {func.__name__}: {str(e)}")
        return default_value


def log_and_display_error(error: Exception, context: str = "", show_technical: bool = False):
    """
    Log error and return user-friendly message.
    
    Args:
        error: The exception that occurred
        context: Additional context about where the error occurred
        show_technical: Whether to show technical details to user
        
    Returns:
        User-friendly error message
    """
    error_msg = str(error)
    
    # Log technical details
    if context:
        logging.error(f"Error in {context}: {error_msg}")
    else:
        logging.error(f"Error: {error_msg}")
    
    # Return user-friendly message
    if isinstance(error, APIError):
        return "❌ Er is een probleem met de AI-service. Probeer het later opnieuw."
    elif isinstance(error, ValidationError):
        return "❌ Er is een probleem met de validatie. Controleer de invoer."
    elif isinstance(error, ConfigurationError):
        return "❌ Er is een configuratieprobleem. Neem contact op met support."
    elif isinstance(error, ExportError):
        return "❌ Er is een probleem met het exporteren. Probeer opnieuw."
    else:
        if show_technical:
            return f"❌ Onverwachte fout: {error_msg}"
        else:
            return "❌ Er is een onverwachte fout opgetreden. Probeer opnieuw."