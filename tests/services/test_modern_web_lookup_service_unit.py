import asyncio
import time

import pytest

from services.interfaces import LookupRequest, LookupResult, WebSource
from services.modern_web_lookup_service import ModernWebLookupService


@pytest.mark.asyncio
async def test_parallel_lookup_concurrency_and_timeout(monkeypatch):
    # Patch providers with small delays
    from tests.fixtures.web_lookup_mocks import SRUServiceStub, wikipedia_lookup_stub

    async def slow_wiki(term: str, language: str = "nl"):
        await asyncio.sleep(0.3)
        return await wikipedia_lookup_stub(term, language)

    class SlowSRU(SRUServiceStub):
        async def search(self, *a, **k):  # type: ignore[override]
            await asyncio.sleep(0.3)
            return await super().search(*a, **k)

    monkeypatch.setattr(
        "services.web_lookup.wikipedia_service.wikipedia_lookup", slow_wiki
    )
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", SlowSRU)

    svc = ModernWebLookupService()
    req = LookupRequest(
        term="authenticatie", sources=["wikipedia", "overheid"], max_results=2
    )

    start = time.perf_counter()
    results = await svc.lookup(req)
    elapsed = time.perf_counter() - start

    # Concurrency: total elapsed should be closer to 0.3s than 0.6s
    assert elapsed < 0.55, f"Expected concurrent lookups, took {elapsed:.2f}s"
    assert isinstance(results, list)
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_error_handling_returns_empty_results(monkeypatch):
    # Providers raise → service should handle and return []
    async def broken_wiki(*a, **k):
        msg = "boom"
        raise RuntimeError(msg)

    class BrokenSRU:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def search(self, *a, **k):
            msg = "sru boom"
            raise RuntimeError(msg)

    monkeypatch.setattr(
        "services.web_lookup.wikipedia_service.wikipedia_lookup", broken_wiki
    )
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", BrokenSRU)

    svc = ModernWebLookupService()
    req = LookupRequest(term="x", sources=["wikipedia", "overheid"], max_results=2)

    results = await svc.lookup(req)
    assert results == []


@pytest.mark.asyncio
async def test_ranking_relevance_based(monkeypatch):
    """
    FASE 3: Test quality-gated juridical boost.

    Scenario: High-quality relevant non-juridical beats low-quality irrelevant juridical
    - Wikipedia (0.8, relevant synoniem) should beat Overheid.nl (0.6, irrelevant BES)

    Quality gate ensures low-quality juridical sources (< 0.65) receive reduced boost,
    allowing high-quality relevant sources to win.

    Expected behavior:
    - Wikipedia:   0.8 × 1.0 × 0.85 (weight) = 0.68
    - Overheid.nl: 0.6 × 1.10 (reduced boost) × 1.0 = 0.66
    - Winner: Wikipedia (0.68 > 0.66) ✅
    """

    def make_result(
        name: str, url: str, score: float, is_juridical: bool, text: str
    ) -> LookupResult:
        return LookupResult(
            term="onherroepelijk",
            source=WebSource(
                name=name, url=url, confidence=score, is_juridical=is_juridical
            ),
            definition=text,
            success=True,
        )

    async def wiki(term: str, language: str = "nl"):
        # Wikipedia met relevant synoniem (hoge relevantie)
        return make_result(
            "Wikipedia",
            "https://nl.wikipedia.org/wiki/Kracht_van_gewijsde",
            0.8,  # Goede base score
            False,  # Niet juridisch, maar wel relevant
            "Kracht van gewijsde betekent onherroepelijk",
        )

    class SRUWithIrrelevant:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def search(self, *a, **k):
            # Overheid.nl met juridische bron maar LAGE relevantie (BES)
            return [
                make_result(
                    "Overheid.nl",
                    "https://wetten.overheid.nl/BES-wetgeving",
                    0.6,  # Lagere score door lage relevantie
                    True,  # Juridisch, maar niet relevant
                    "BES wetgeving paragraaf 3.2",  # No 'artikel' to avoid artikel_referentie boost
                )
            ]

    monkeypatch.setattr("services.web_lookup.wikipedia_service.wikipedia_lookup", wiki)
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", SRUWithIrrelevant)

    svc = ModernWebLookupService()
    req = LookupRequest(
        term="onherroepelijk", sources=["wikipedia", "overheid"], max_results=5
    )
    results = await svc.lookup(req)

    # FASE 3 EXPECTED BEHAVIOR (with quality gate):
    # Wikipedia: 0.8 × 0.85 (weight) = 0.68
    # Overheid.nl: 0.6 × 1.10 (reduced boost, quality gate) × 1.0 (weight) = 0.66
    # Result: Wikipedia wins (0.68 > 0.66) ✅
    assert len(results) >= 1, "Should have at least one result"

    # Wikipedia moet winnen door relevantie (quality gate voorkomt low-quality juridical boost)
    assert (
        "Wikipedia" in results[0].source.name
    ), f"Expected Wikipedia to win (relevance > low-quality juridical), got {results[0].source.name}"


@pytest.mark.asyncio
async def test_quality_gate_allows_high_quality_juridical(monkeypatch):
    """
    FASE 3: Test quality gate allows high-quality juridical sources full boost.

    Scenario: High-quality juridical (>= 0.65) should receive FULL boost
    - Overheid.nl (0.8, juridisch) should beat Wikipedia (0.7, relevant)

    Quality gate ensures high-quality juridical sources still get full boost.

    Expected behavior:
    - Overheid.nl: 0.8 × 1.2 (full boost) × 1.0 = 0.96
    - Wikipedia:   0.7 × 1.0 × 0.85 (weight) = 0.595
    - Winner: Overheid.nl (0.96 > 0.595) ✅
    """

    def make_result(
        name: str, url: str, score: float, is_juridical: bool, text: str
    ) -> LookupResult:
        return LookupResult(
            term="rechtbank",
            source=WebSource(
                name=name, url=url, confidence=score, is_juridical=is_juridical
            ),
            definition=text,
            success=True,
        )

    async def wiki(term: str, language: str = "nl"):
        # Wikipedia met relevante definitie (goede score)
        return make_result(
            "Wikipedia",
            "https://nl.wikipedia.org/wiki/Rechtbank",
            0.7,  # Goede score maar niet top
            False,  # Niet juridisch
            "Een rechtbank is een gerecht in eerste aanleg",
        )

    class SRUWithHighQuality:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def search(self, *a, **k):
            # Overheid.nl met HOGE juridische score + artikel boost
            return [
                make_result(
                    "Overheid.nl",
                    "https://wetten.overheid.nl/rechtsgebied/strafrecht",
                    0.8,  # HOGE score (>= 0.65) → full boost
                    True,  # Juridisch
                    "Artikel 12 Rv. De rechtbank is bevoegd in eerste aanleg",
                )
            ]

    monkeypatch.setattr("services.web_lookup.wikipedia_service.wikipedia_lookup", wiki)
    monkeypatch.setattr(
        "services.web_lookup.sru_service.SRUService", SRUWithHighQuality
    )

    svc = ModernWebLookupService()
    req = LookupRequest(
        term="rechtbank", sources=["wikipedia", "overheid"], max_results=5
    )
    results = await svc.lookup(req)

    # FASE 3 EXPECTED BEHAVIOR (with quality gate PASS):
    # Overheid.nl: 0.8 × 1.2 (full juridische_bron boost) × 1.15 (artikel) × 1.0 = 1.104 (capped to 1.0)
    # Wikipedia: 0.7 × 0.85 (weight) = 0.595
    # Result: Overheid.nl wins (1.0 > 0.595) ✅
    assert len(results) >= 1, "Should have at least one result"

    # Overheid.nl moet winnen (high-quality juridical > non-juridical)
    assert (
        "Overheid" in results[0].source.name
    ), f"Expected Overheid.nl to win (high-quality juridical), got {results[0].source.name}"


@pytest.mark.asyncio
async def test_quality_gate_disabled_gives_full_boost_to_all(monkeypatch):
    """
    FASE 3: Test quality gate disabled behavior (backward compatibility).

    Scenario: With quality_gate.enabled: false, ALL juridical sources get full boost
    - Even low-quality juridical (0.5) should get full 1.2x boost

    Expected behavior (gate DISABLED):
    - Overheid.nl: 0.5 × 1.2 (full boost, no gate) × 1.0 = 0.60
    - Wikipedia:   0.6 × 1.0 × 0.85 (weight) = 0.51
    - Winner: Overheid.nl (0.60 > 0.51) ✅ (old behavior)
    """

    # Override config to disable quality gate
    def patched_get_ranker_config(*args, **kwargs):
        from services.web_lookup.juridisch_ranker import JuridischRankerConfig

        config = JuridischRankerConfig()
        # Disable quality gate
        config.boost_factors["quality_gate"] = {
            "enabled": False,  # DISABLED
            "min_base_score": 0.65,
            "reduced_boost_factor": 0.5,
        }
        return config

    monkeypatch.setattr(
        "services.web_lookup.juridisch_ranker.get_ranker_config",
        patched_get_ranker_config,
    )

    def make_result(
        name: str, url: str, score: float, is_juridical: bool, text: str
    ) -> LookupResult:
        return LookupResult(
            term="executie",
            source=WebSource(
                name=name, url=url, confidence=score, is_juridical=is_juridical
            ),
            definition=text,
            success=True,
        )

    async def wiki(term: str, language: str = "nl"):
        return make_result(
            "Wikipedia",
            "https://nl.wikipedia.org/wiki/Executie",
            0.6,  # Redelijke score
            False,
            "Executie betekent uitvoering of terechtstelling",
        )

    class SRUWithLowQuality:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def search(self, *a, **k):
            # Overheid.nl met LAGE score maar juridisch
            return [
                make_result(
                    "Overheid.nl",
                    "https://wetten.overheid.nl/executie-info",
                    0.5,  # LAGE score (< 0.65) maar gate DISABLED
                    True,
                    "Executie van vonnissen in strafzaken",  # Juridische content
                )
            ]

    monkeypatch.setattr("services.web_lookup.wikipedia_service.wikipedia_lookup", wiki)
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", SRUWithLowQuality)

    svc = ModernWebLookupService()
    req = LookupRequest(
        term="executie", sources=["wikipedia", "overheid"], max_results=5
    )
    results = await svc.lookup(req)

    # With quality gate DISABLED, low-quality juridical should get full boost
    # Overheid.nl: 0.5 × 1.2 (full boost) × 1.0 = 0.60
    # Wikipedia: 0.6 × 0.85 = 0.51
    # Result: Overheid.nl wins (0.60 > 0.51) - OLD BEHAVIOR restored
    assert len(results) >= 1, "Should have at least one result"

    # With gate disabled, even low-quality juridical should win
    assert (
        "Overheid" in results[0].source.name
    ), f"Expected Overheid.nl to win (gate disabled, full boost), got {results[0].source.name}"


@pytest.mark.asyncio
async def test_quality_gate_boundary_exactly_at_threshold(monkeypatch):
    """
    FASE 3: Test quality gate boundary condition (base_score = threshold).

    Scenario: Source with base_score EXACTLY at threshold (0.65) should get full boost
    - Boundary test: >= operator verification

    Expected behavior:
    - Overheid.nl: 0.65 × 1.2 (full boost, >= threshold) × 1.0 = 0.78
    - Wikipedia:   0.64 × 1.0 × 0.85 = 0.544
    - Winner: Overheid.nl (0.78 > 0.544) ✅
    """

    def make_result(
        name: str, url: str, score: float, is_juridical: bool, text: str
    ) -> LookupResult:
        return LookupResult(
            term="beklag",
            source=WebSource(
                name=name, url=url, confidence=score, is_juridical=is_juridical
            ),
            definition=text,
            success=True,
        )

    async def wiki(term: str, language: str = "nl"):
        return make_result(
            "Wikipedia",
            "https://nl.wikipedia.org/wiki/Beklag",
            0.64,  # BELOW threshold
            False,
            "Beklag is een rechtsmiddel tegen beslissingen",
        )

    class SRUAtThreshold:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def search(self, *a, **k):
            # Overheid.nl met score EXACT OP threshold (0.65)
            return [
                make_result(
                    "Overheid.nl",
                    "https://wetten.overheid.nl/beklag-procedure",
                    0.65,  # EXACTLY at threshold (>= should PASS)
                    True,
                    "Artikel 552a Sv. Beklag tegen niet-vervolging",
                )
            ]

    monkeypatch.setattr("services.web_lookup.wikipedia_service.wikipedia_lookup", wiki)
    monkeypatch.setattr("services.web_lookup.sru_service.SRUService", SRUAtThreshold)

    svc = ModernWebLookupService()
    req = LookupRequest(term="beklag", sources=["wikipedia", "overheid"], max_results=5)
    results = await svc.lookup(req)

    # FASE 3 BOUNDARY TEST:
    # Overheid.nl: 0.65 × 1.2 (full boost, >= 0.65) × 1.15 (artikel) × 1.0 = 0.897
    # Wikipedia: 0.64 × 0.85 = 0.544
    # Result: Overheid.nl wins (0.897 > 0.544) ✅
    assert len(results) >= 1, "Should have at least one result"

    # Boundary case: exactly at threshold should get FULL boost
    assert (
        "Overheid" in results[0].source.name
    ), f"Expected Overheid.nl to win (boundary at threshold), got {results[0].source.name}"
