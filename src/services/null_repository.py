"""
Null Repository implementation voor development zonder database.

Deze implementatie doet niets maar voorkomt crashes wanneer
geen database beschikbaar is.
"""

from typing import Any

from services.interfaces import Definition, DefinitionRepositoryInterface


class NullDefinitionRepository(DefinitionRepositoryInterface):
    """
    Null Object pattern implementatie van DefinitionRepository.

    Doet niets, retourneert lege resultaten, maar crashed niet!
    Perfect voor development zonder database.
    """

    def __init__(self):
        """No database needed!"""
        self._stats = {
            "total_saves": 0,
            "total_searches": 0,
            "total_updates": 0,
            "total_deletes": 0,
        }

    def save(self, definition: Definition) -> int:
        """Pretend to save, return fake ID."""
        self._stats["total_saves"] += 1
        return 999  # Fake ID

    def get(self, definition_id: int) -> Definition | None:
        """Always return None - nothing stored."""
        return None

    def search(self, query: str, limit: int = 10) -> list[Definition]:
        """Always return empty list."""
        self._stats["total_searches"] += 1
        return []

    def update(self, definition_id: int, definition: Definition) -> bool:
        """Pretend to update successfully."""
        self._stats["total_updates"] += 1
        return True

    def delete(self, definition_id: int) -> bool:
        """Pretend to delete successfully."""
        self._stats["total_deletes"] += 1
        return True

    def find_by_begrip(self, begrip: str) -> Definition | None:
        """Always return None."""
        return None

    def find_duplicates(self, definition: Definition) -> list[Definition]:
        """No duplicates in null repository."""
        return []

    def get_by_status(self, status: str, limit: int = 50) -> list[Definition]:
        """Always return empty list."""
        return []

    def get_stats(self) -> dict[str, Any]:
        """Return fake stats."""
        return {
            **self._stats,
            "total_definitions": 0,
            "by_status": {},
        }

    def reset_stats(self) -> None:
        """Reset fake stats."""
        self._stats = {
            "total_saves": 0,
            "total_searches": 0,
            "total_updates": 0,
            "total_deletes": 0,
        }
