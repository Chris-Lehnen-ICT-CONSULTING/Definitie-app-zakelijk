"""
Test mocks for web lookup services.

Created for FASE 2 testing - provides stubs for Wikipedia and SRU services.
"""

from services.interfaces import LookupResult, WebSource


class SRUServiceStub:
    """Stub SRU service for testing."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        return False

    async def search(
        self, term: str, endpoint: str = "overheid", max_records: int = 3
    ) -> list[LookupResult]:
        """Return mock SRU result for testing."""
        return [
            LookupResult(
                term=term,
                source=WebSource(
                    name="Overheid.nl",
                    url=f"https://repository.overheid.nl/{term}",
                    confidence=0.7,
                    is_juridical=True,
                ),
                definition=f"Mock overheid definitie voor {term}",
                success=True,
            )
        ]

    def get_attempts(self) -> list[dict]:
        """Return empty attempts list."""
        return []


async def wikipedia_lookup_stub(term: str, language: str = "nl") -> LookupResult | None:
    """Stub Wikipedia lookup function."""
    return LookupResult(
        term=term,
        source=WebSource(
            name="Wikipedia",
            url=f"https://nl.wikipedia.org/wiki/{term}",
            confidence=0.8,
            is_juridical=False,
        ),
        definition=f"Mock Wikipedia definitie voor {term}",
        success=True,
    )
