"""
Unit tests for ModernWebLookupService with fully mocked providers.

No network calls are made; MediaWiki and SRU providers are patched to stubs.

DEF-519 — de drie node-intenties zijn behouden; alleen de fixtures zijn echt
gemaakt:

* de module-brede `pytest.mark.skip("Fixtures removed…")` klopte niet meer: de
  gedeelde stubs bestonden nog. Zonder skip waren alle drie de nodes groen,
  maar node 2 was vals groen: `lambda: SRUServiceStub(raise_on_search=True)`
  gooit een `TypeError` in de constructor, die het product zelf al opvangt. De
  SRU-provider werd dus nooit aangeroepen en het foutpad nooit doorlopen;
* de stubs staan nu lokaal, registreren hun exacte aanroepen en leveren echte
  `LookupResult`/`WebSource`-objecten. Geen mock van de lookupservice zelf en
  geen `raising=False` — de grenzen moeten bestaan;
* de parallelle uitvoering wordt bewezen met events (elke provider wacht op de
  ander), niet met een timingheuristiek. De productcode is niet aangepast.

Elke test bouwt een verse service en `monkeypatch` zet de grenzen daarna terug.
"""

from __future__ import annotations

import asyncio

import pytest

from services.interfaces import LookupRequest, LookupResult, WebSource
from services.modern_web_lookup_service import ModernWebLookupService

pytestmark = [pytest.mark.unit]

WIKIPEDIA_GRENS = "services.web_lookup.wikipedia_service.wikipedia_lookup"
SRU_GRENS = "services.web_lookup.sru_service.SRUService"

#: Harde bovengrens voor het wachten op de tegenpartij in de overlapproef.
#: Draaien de providers niet gelijktijdig, dan faalt de test hier begrensd in
#: plaats van te blijven hangen.
OVERLAP_TIMEOUT = 5.0


class WikipediaStub:
    """Providergrens voor Wikipedia: registreert aanroepen, levert een resultaat."""

    def __init__(self, *, tegenpartij: asyncio.Event | None = None) -> None:
        self.aanroepen: list[str] = []
        self.gereed = asyncio.Event()
        self.tegenpartij = tegenpartij

    async def __call__(self, term: str, language: str = "nl") -> LookupResult:
        self.aanroepen.append(term)
        self.gereed.set()
        if self.tegenpartij is not None:
            await asyncio.wait_for(self.tegenpartij.wait(), timeout=OVERLAP_TIMEOUT)
        return LookupResult(
            term=term,
            source=WebSource(
                name="Wikipedia",
                url=f"https://nl.wikipedia.org/wiki/{term}",
                confidence=0.8,
                is_juridical=False,
            ),
            definition=f"Stub Wikipedia definitie voor {term}",
            success=True,
        )


class SRUStub:
    """Providergrens voor SRU: registreert zoekopdrachten en levensduur."""

    def __init__(
        self, *, faalt: bool = False, tegenpartij: asyncio.Event | None = None
    ) -> None:
        self.zoekopdrachten: list[dict] = []
        self.geopend = 0
        self.gesloten = 0
        self.faalt = faalt
        self.gereed = asyncio.Event()
        self.tegenpartij = tegenpartij

    async def __aenter__(self) -> SRUStub:
        self.geopend += 1
        return self

    async def __aexit__(self, *args: object) -> bool:
        self.gesloten += 1
        return False

    async def search(
        self, term: str, endpoint: str = "overheid", max_records: int = 3
    ) -> list[LookupResult]:
        self.zoekopdrachten.append(
            {"term": term, "endpoint": endpoint, "max_records": max_records}
        )
        self.gereed.set()
        if self.tegenpartij is not None:
            await asyncio.wait_for(self.tegenpartij.wait(), timeout=OVERLAP_TIMEOUT)
        if self.faalt:
            raise RuntimeError("SRU-provider onbereikbaar (teststub)")
        return [
            LookupResult(
                term=term,
                source=WebSource(
                    name="Overheid.nl",
                    url=f"https://repository.overheid.nl/{term}",
                    confidence=0.7,
                    is_juridical=True,
                ),
                definition=f"Stub overheid definitie voor {term}",
                success=True,
            )
        ]

    def get_attempts(self) -> list[dict]:
        return []


def _verse_service() -> ModernWebLookupService:
    """Verse service per test; er is geen gedeelde resultaatcache in deze klasse."""
    service = ModernWebLookupService()
    assert service._debug_attempts == []
    return service


@pytest.mark.asyncio
async def test_parallel_lookup_mediawiki_and_sru(monkeypatch):
    """Lookup uses both MediaWiki and SRU providers concurrently and returns results."""
    wikipedia = WikipediaStub()
    sru = SRUStub()
    # Elke provider wacht op het startsein van de ander: dat kan alleen slagen
    # als beide werkelijk tegelijk lopen. Geen timingheuristiek.
    wikipedia.tegenpartij = sru.gereed
    sru.tegenpartij = wikipedia.gereed

    monkeypatch.setattr(WIKIPEDIA_GRENS, wikipedia)
    monkeypatch.setattr(SRU_GRENS, lambda: sru)

    svc = _verse_service()
    req = LookupRequest(
        term="authenticatie", sources=["wikipedia", "overheid"], max_results=2
    )
    try:
        results = await svc.lookup(req)
    finally:
        # Begrensde opruiming: wie nog wacht, wordt hoe dan ook vrijgegeven.
        wikipedia.gereed.set()
        sru.gereed.set()

    # Beide grenzen zijn werkelijk aangeroepen met de gevraagde term.
    assert wikipedia.aanroepen == ["authenticatie"]
    assert sru.zoekopdrachten == [
        {"term": "authenticatie", "endpoint": "overheid", "max_records": 3}
    ]
    assert sru.geopend == 1
    assert sru.gesloten == 1

    assert isinstance(results, list)
    assert len(results) == 2
    # Provider/source labels present and confidence applied
    names = {r.source.name for r in results}
    assert {"Wikipedia", "Overheid.nl"}.issubset(names)
    # Confidence weights are applied (>0)
    assert all((r.source.confidence or 0.0) > 0 for r in results)

    # Exacte inhoud per provider: verlies of verwisseling van definition/url
    # onderweg mag niet groen blijven.
    per_bron = {r.source.name: r for r in results}
    wiki_resultaat = per_bron["Wikipedia"]
    assert wiki_resultaat.term == "authenticatie"
    assert wiki_resultaat.definition == "Stub Wikipedia definitie voor authenticatie"
    assert wiki_resultaat.source.url == "https://nl.wikipedia.org/wiki/authenticatie"

    sru_resultaat = per_bron["Overheid.nl"]
    assert sru_resultaat.term == "authenticatie"
    assert sru_resultaat.definition == "Stub overheid definitie voor authenticatie"
    assert sru_resultaat.source.url == "https://repository.overheid.nl/authenticatie"


@pytest.mark.asyncio
async def test_error_in_sru_does_not_break_other_providers(monkeypatch):
    """SRU error is handled; MediaWiki result is still returned."""
    wikipedia = WikipediaStub()
    sru = SRUStub(faalt=True)

    monkeypatch.setattr(WIKIPEDIA_GRENS, wikipedia)
    monkeypatch.setattr(SRU_GRENS, lambda: sru)

    svc = _verse_service()
    req = LookupRequest(
        term="rechtspraak", sources=["wikipedia", "overheid"], max_results=2
    )
    results = await svc.lookup(req)

    # Het foutpad is werkelijk doorlopen: de SRU-provider is aangeroepen en
    # gooide tijdens `search`. Zonder deze assertie is de node vals groen zodra
    # de stub al bij constructie stukloopt.
    assert sru.zoekopdrachten == [
        {"term": "rechtspraak", "endpoint": "overheid", "max_records": 3}
    ]
    assert sru.geopend == 1
    # De contextmanager is ook ná de echte searchfout netjes afgesloten.
    assert sru.gesloten == 1
    assert wikipedia.aanroepen == ["rechtspraak"]

    # Only wikipedia survives — exact één resultaat, met de juiste inhoud.
    assert len(results) == 1
    resultaat = results[0]
    assert resultaat.source.name == "Wikipedia"
    assert resultaat.term == "rechtspraak"
    assert resultaat.definition == "Stub Wikipedia definitie voor rechtspraak"
    assert resultaat.source.url == "https://nl.wikipedia.org/wiki/rechtspraak"


@pytest.mark.asyncio
async def test_lookup_single_source(monkeypatch):
    """lookup_single_source returns a single LookupResult for the requested provider."""
    wikipedia = WikipediaStub()
    sru = SRUStub()

    monkeypatch.setattr(WIKIPEDIA_GRENS, wikipedia)
    monkeypatch.setattr(SRU_GRENS, lambda: sru)

    svc = _verse_service()
    result = await svc.lookup_single_source("authenticatie", "wikipedia")

    assert result is not None
    assert result.source.name == "Wikipedia"
    assert result.term == "authenticatie"
    assert result.definition == "Stub Wikipedia definitie voor authenticatie"
    assert result.source.url == "https://nl.wikipedia.org/wiki/authenticatie"
    # Alleen de gevraagde bron is bevraagd.
    assert wikipedia.aanroepen == ["authenticatie"]
    assert sru.zoekopdrachten == []
    assert sru.geopend == 0
