"""
Custom exceptions voor DefinitieAgent services.

Provides specific exception types voor betere error handling en debugging.
"""


class DefinitionServiceError(Exception):
    """Base exception voor definition services."""


class DuplicateDefinitionError(DefinitionServiceError):
    """Raised when attempting to save a duplicate definition."""

    def __init__(self, begrip: str, message: str = ""):
        self.begrip = begrip
        super().__init__(
            message or f"Definition for '{begrip}' already exists in the database"
        )


class DatabaseConstraintError(DefinitionServiceError):
    """Raised when database constraint is violated."""

    def __init__(self, field: str, begrip: str, message: str = ""):
        self.field = field
        self.begrip = begrip
        super().__init__(
            message
            or f"Database constraint violated for field '{field}' in definition '{begrip}'"
        )


class DatabaseConnectionError(DefinitionServiceError):
    """Raised when database connection fails."""

    def __init__(self, db_path: str, message: str = ""):
        self.db_path = db_path
        super().__init__(message or f"Cannot connect to database at '{db_path}'")


class ValidationError(DefinitionServiceError):
    """Raised when definition validation fails."""

    def __init__(self, begrip: str, violations: list[str], message: str = ""):
        self.begrip = begrip
        self.violations = violations
        super().__init__(
            message
            or f"Validation failed for '{begrip}': {len(violations)} violation(s)"
        )


class RepositoryError(DefinitionServiceError):
    """Raised when repository operation fails."""

    def __init__(self, operation: str, begrip: str = "", message: str = ""):
        self.operation = operation
        self.begrip = begrip
        super().__init__(
            message or f"Repository operation '{operation}' failed for '{begrip}'"
        )
