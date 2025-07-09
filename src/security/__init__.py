"""
Security package for DefinitieAgent.
Provides comprehensive security middleware, threat detection, and request validation.
"""

from .security_middleware import (
    SecurityMiddleware,
    SecurityEvent,
    SecurityLevel,
    ThreatType,
    ValidationRequest,
    ValidationResponse,
    get_security_middleware,
    security_middleware_decorator
)

__all__ = [
    "SecurityMiddleware",
    "SecurityEvent",
    "SecurityLevel",
    "ThreatType",
    "ValidationRequest",
    "ValidationResponse",
    "get_security_middleware",
    "security_middleware_decorator"
]

# Version info
__version__ = "1.0.0"
__author__ = "DefinitieAgent Development Team"
__description__ = "Security middleware and threat detection system for Dutch government applications"
