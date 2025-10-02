from __future__ import annotations

import asyncio

from services.interfaces import LookupResult, WebSource


async def wikipedia_lookup_stub(term: str, language: str = "nl") -> LookupResult | None:
    await asyncio.sleep(0.05)
    return LookupResult(
        term=term,
        source=WebSource(
            name="Wikipedia",
            url=f"https://nl.wikipedia.org/wiki/{term}",
            confidence=0.7,
            api_type="mediawiki",
        ),
        definition=f"{term} is een encyclopedisch begrip",
        success=True,
        metadata={"title": term.title()},
    )


class SRUServiceStub:
    """Async context manager stub that mimics SRUService interface."""

    def __init__(
        self,
        results: list[LookupResult] | None = None,
        delay: float = 0.05,
        raise_on_search: bool = False,
    ):
        self._results = results or [
            LookupResult(
                term="authenticatie",
                source=WebSource(
                    name="Overheid.nl",
                    url="https://overheid.nl/doc/1",
                    confidence=1.0,
                    is_juridical=True,
                    api_type="sru",
                ),
                definition="Artikel 1 ...",
                success=True,
            )
        ]
        self._delay = delay
        self._raise_on_search = raise_on_search

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    async def search(
        self,
        term: str,
        endpoint: str = "overheid",
        max_records: int = 1,
        collection: str | None = None,
    ):
        await asyncio.sleep(self._delay)
        if self._raise_on_search:
            raise RuntimeError("SRU error")
        # Return at most max_records
        return self._results[:max_records]
