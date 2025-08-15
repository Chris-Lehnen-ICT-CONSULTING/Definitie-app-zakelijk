"""
Aangepaste uitzonderingen en foutafhandeling utilities voor DefinitieAgent.

Deze module definieert alle aangepaste exception types en utilities
voor elegante foutafhandeling in de hele applicatie.
"""

import logging
from typing import Any
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
    Voer een functie veilig uit en geef standaardwaarde terug bij fout.

    Args:
        func: Functie om uit te voeren
        default_value: Waarde om terug te geven bij fout
        error_message: Aangepast foutbericht voor logging

    Returns:
        Functie resultaat of default_value bij fout
    """
    try:
        # Probeer de functie uit te voeren
        return func()
    except Exception as e:
        # Log de fout met aangepast of standaard bericht
        if error_message:
            logging.error(f"{error_message}: {str(e)}")
        else:
            logging.error(f"Fout in {func.__name__}: {str(e)}")
        # Geef standaardwaarde terug bij fout
        return default_value


def log_and_display_error(
    error: Exception, context: str = "", show_technical: bool = False
):
    """
    Log fout en geef gebruikersvriendelijk bericht terug.

    Args:
        error: De uitzondering die opgetreden is
        context: Aanvullende context over waar de fout optrad
        show_technical: Of technische details getoond moeten worden aan gebruiker

    Returns:
        Gebruikersvriendelijk foutbericht
    """
    # Converteer fout naar string voor logging
    error_msg = str(error)

    # Log technische details voor debugging
    if context:
        logging.error(f"Fout in {context}: {error_msg}")
    else:
        logging.error(f"Fout: {error_msg}")

    # Geef gebruikersvriendelijk bericht terug op basis van fout type
    if isinstance(error, APIError):
        return "❌ Er is een probleem met de AI-service. Probeer het later opnieuw."
    elif isinstance(error, ValidationError):
        return "❌ Er is een probleem met de validatie. Controleer de invoer."
    elif isinstance(error, ConfigurationError):
        return "❌ Er is een configuratieprobleem. Neem contact op met support."
    elif isinstance(error, ExportError):
        return "❌ Er is een probleem met het exporteren. Probeer opnieuw."
    else:
        # Voor onbekende fouten, toon technische details indien gevraagd
        if show_technical:
            return f"❌ Onverwachte fout: {error_msg}"
        else:
            return "❌ Er is een onverwachte fout opgetreden. Probeer opnieuw."
