"""Repository layer voor database operations."""

from .synonym_repository import (
    SuggestionStatus,
    SynonymRepository,
    SynonymSuggestionRecord,
)

__all__ = [
    "SuggestionStatus",
    "SynonymRepository",
    "SynonymSuggestionRecord",
]
