"""Uvicorn's eigen loggers moeten PII redigeren (DEF-571 / DEF-574).

`uvicorn`, `uvicorn.access` en `uvicorn.error` krijgen van uvicorn's dictConfig
`propagate = False` en eigen handlers. De filter op de root-handlers bereikt ze
dus nooit, terwijl `uvicorn.access` het volledige request-pad logt (inclusief
query-string). De lifespan-hook hangt de filter alsnog op die loggers.
"""

import logging

import pytest

pytestmark = pytest.mark.unit

from utils.logging_filters import PIIRedactingFilter


@pytest.fixture
def uvicorn_loggers_met_handler():
    """Boots uvicorn's dictConfig na: eigen handler, geen propagatie."""
    from api.feature_status_api import _UVICORN_LOGGERS

    origineel: dict[str, tuple] = {}
    for naam in _UVICORN_LOGGERS:
        lg = logging.getLogger(naam)
        origineel[naam] = (list(lg.handlers), lg.propagate)
        lg.handlers = [logging.StreamHandler()]
        lg.propagate = False
    try:
        yield _UVICORN_LOGGERS
    finally:
        for naam, (handlers, propagate) in origineel.items():
            lg = logging.getLogger(naam)
            lg.handlers = handlers
            lg.propagate = propagate


def test_uvicorn_loggers_krijgen_pii_filter(uvicorn_loggers_met_handler):
    from api.feature_status_api import install_uvicorn_pii_redaction

    # Vóór de hook: geen enkele filter.
    for naam in uvicorn_loggers_met_handler:
        for handler in logging.getLogger(naam).handlers:
            assert not any(isinstance(f, PIIRedactingFilter) for f in handler.filters)

    install_uvicorn_pii_redaction()

    for naam in uvicorn_loggers_met_handler:
        for handler in logging.getLogger(naam).handlers:
            assert any(
                isinstance(f, PIIRedactingFilter) for f in handler.filters
            ), f"{naam} mist de PII-redactie"


def test_access_log_met_pii_wordt_geredigeerd(uvicorn_loggers_met_handler):
    from api.feature_status_api import install_uvicorn_pii_redaction

    opgevangen: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            opgevangen.append(self.format(record))

    access = logging.getLogger("uvicorn.access")
    access.handlers = [_Capture()]
    access.setLevel(logging.INFO)
    install_uvicorn_pii_redaction()

    access.info('GET /zoek?email=%s HTTP/1.1" 200', "user@example.com")

    assert opgevangen, "er is niets gelogd"
    assert "user@example.com" not in opgevangen[-1]
    assert "[REDACTED]" in opgevangen[-1]


@pytest.mark.asyncio
async def test_lifespan_installeert_redactie(uvicorn_loggers_met_handler):
    """De hook moet daadwerkelijk aan de app hangen, niet alleen bestaan."""
    from api.feature_status_api import app, lifespan

    assert app.router.lifespan_context is not None
    async with lifespan(app):
        for naam in uvicorn_loggers_met_handler:
            for handler in logging.getLogger(naam).handlers:
                assert any(isinstance(f, PIIRedactingFilter) for f in handler.filters)
