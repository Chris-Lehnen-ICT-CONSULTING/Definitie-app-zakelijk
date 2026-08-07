"""Tests for defensive paths in ModernWebLookupService."""

import asyncio

import pytest

from services.interfaces import LookupRequest, LookupResult, WebSource
from services.modern_web_lookup_service import ModernWebLookupService, SourceConfig

pytestmark = [pytest.mark.unit]


class _BadMeta(dict):
    """Metadata dict that raises for specific keys to trigger logging."""

    def get(self, key, default=None):  # - keep dict signature
        if key in {"article_number", "law_code", "law_clause", "dc_identifier"}:
            msg = "boom"
            raise ValueError(msg)
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
        msg = "cannot fetch attempts"
        raise RuntimeError(msg)


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


@pytest.mark.asyncio
async def test_lookup_filtert_baseexception_uit_gather(monkeypatch, caplog):
    """Een geannuleerde source-lookup mag niet als resultaat doorstromen.

    Regressie (DEF-609): de filtering gebruikte `isinstance(result, Exception)`,
    maar `asyncio.gather(return_exceptions=True)` levert ook BaseException-
    subklassen op en `asyncio.CancelledError` erft sinds Python 3.8 van
    BaseException. Het exception-object belandde daardoor in `valid_results` en
    werd doorgegeven aan de juridische ranking.

    Deze test faalt als de check terugvalt naar `Exception`.
    """
    goed = LookupResult(
        term="foo",
        source=WebSource(name="Wikipedia", url="", confidence=1.0),
        definition="Een geldige definitie.",
        success=True,
    )

    async def _ok(*_args, **_kwargs):
        return goed

    async def _cancelled(*_args, **_kwargs):
        raise asyncio.CancelledError

    def _setup(self):
        self.sources = {
            "wikipedia": SourceConfig(name="Wikipedia", base_url="", api_type="rest"),
            "kapot": SourceConfig(name="Kapot", base_url="", api_type="rest"),
        }

    monkeypatch.setattr(ModernWebLookupService, "_setup_sources", _setup)
    svc = ModernWebLookupService()
    svc._debug_attempts = []  # type: ignore[attr-defined]
    svc._classify_context_tokens = lambda _ctx: ([], [], [])  # type: ignore[attr-defined]
    # Beperk tot de twee gemockte bronnen; de echte lijst bevat namen die deze
    # fixture niet definieert.
    svc._determine_sources = lambda _req: ["wikipedia", "kapot"]  # type: ignore[method-assign]

    async def _dispatch(term, source_name, request):
        return await (_cancelled() if source_name == "kapot" else _ok())

    monkeypatch.setattr(svc, "_lookup_source", _dispatch)

    caplog.set_level("WARNING")
    resultaten = await svc.lookup(LookupRequest(term="foo", timeout=5))

    assert all(
        isinstance(r, LookupResult) for r in resultaten
    ), "een BaseException lekte door de filtering heen"
    assert not any(isinstance(r, BaseException) for r in resultaten)
    assert "Source lookup failed" in caplog.text
