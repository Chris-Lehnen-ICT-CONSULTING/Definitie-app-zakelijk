"""Tests for defensive paths in ModernWebLookupService."""

import pytest

from services.interfaces import LookupRequest, LookupResult, WebSource
from services.modern_web_lookup_service import (
    ModernWebLookupService,
    SourceConfig,
)


class _BadMeta(dict):
    """Metadata dict that raises for specific keys to trigger logging."""

    def get(self, key, default=None):  # noqa: D401 - keep dict signature
        if key in {"article_number", "law_code", "law_clause", "dc_identifier"}:
            raise ValueError("boom")
        return super().get(key, default)


class _DummySRUService:
    """Minimal async context manager that raises on get_attempts."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def search(self, term: str, endpoint: str, max_records: int):
        return []

    def get_attempts(self):
        raise RuntimeError("cannot fetch attempts")


@pytest.fixture
def service(monkeypatch):
    """Provide a ModernWebLookupService with minimal setup."""

    monkeypatch.setattr(
        ModernWebLookupService,
        "_setup_sources",
        lambda self: setattr(self, "sources", {}),
    )
    svc = ModernWebLookupService()
    svc._debug_attempts = []  # type: ignore[attr-defined]
    svc._classify_context_tokens = lambda _ctx: ([], [], [])  # type: ignore[attr-defined]
    return svc


@pytest.mark.asyncio
async def test_lookup_sru_logs_attempt_failures(service, monkeypatch, caplog):
    """SRU attempt logging failures should be surfaced as debug logs."""

    monkeypatch.setattr(
        "services.web_lookup.sru_service.SRUService",
        _DummySRUService,
    )

    request = LookupRequest(term="foo", timeout=1)
    source = SourceConfig(name="Rechtspraak.nl", base_url="", api_type="sru")

    caplog.set_level("DEBUG")
    result = await service._lookup_sru("foo", source, request)

    assert result is None
    assert "SRU attempt logging failed" in caplog.text


def test_to_contract_dict_logs_metadata_errors(service, caplog):
    """Metadata parsing failures are logged without breaking output."""

    bad_meta = _BadMeta(
        {
            "article_number": "10",
            "law_code": "BW",
            "law_clause": "1",
            "dc_identifier": "ECLI:123",
            "title": "Titel",
            "retrieved_at": "2024-01-01T00:00:00Z",
        }
    )

    result = LookupResult(
        term="foo",
        source=WebSource(name="Rechtspraak", url="", confidence=0.5, is_juridical=True),
        definition="Definitie",
        metadata=bad_meta,
    )

    caplog.set_level("DEBUG")
    contract = service._to_contract_dict(result)

    assert contract["snippet"].startswith("Definitie")
    assert "Kon juridische metadata niet verrijken" in caplog.text
    assert "Kon ECLI-boost niet toepassen" in caplog.text
