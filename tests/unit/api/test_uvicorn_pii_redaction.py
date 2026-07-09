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
    """Boots uvicorn's dictConfig na: eigen handler, geen propagatie.

    Dwingt de uitgangssituatie af in plaats van hem aan te nemen: een andere
    test in dezelfde sessie kan de filter al geïnstalleerd hebben, wat deze
    tests anders order-afhankelijk maakt (groen solo, rood in de volle suite).
    """
    from api.feature_status_api import _UVICORN_LOGGERS

    origineel: dict[str, tuple] = {}
    for naam in _UVICORN_LOGGERS:
        lg = logging.getLogger(naam)
        origineel[naam] = (list(lg.handlers), lg.propagate)
        verse_handler = logging.StreamHandler()
        for f in list(verse_handler.filters):
            verse_handler.removeFilter(f)
        lg.handlers = [verse_handler]
        lg.propagate = False
    try:
        yield _UVICORN_LOGGERS
    finally:
        for naam, (handlers, propagate) in origineel.items():
            lg = logging.getLogger(naam)
            lg.handlers = handlers
            lg.propagate = propagate


def _heeft_pii_filter(logger_naam: str) -> bool:
    handlers = logging.getLogger(logger_naam).handlers
    return bool(handlers) and all(
        any(isinstance(f, PIIRedactingFilter) for f in h.filters) for h in handlers
    )


def test_uvicorn_loggers_krijgen_pii_filter(uvicorn_loggers_met_handler):
    """De hook hangt de filter op elk van uvicorn's eigen loggers.

    Bewust géén "vóór de hook zijn er geen filters"-precondition: de fixture
    garandeert verse handlers, dus zo'n assertie toetst niets en kan alleen nog
    rood worden door interferentie van een andere test in dezelfde sessie.
    Faalt de hook, dan faalt de assertie hieronder.
    """
    from api.feature_status_api import install_uvicorn_pii_redaction

    install_uvicorn_pii_redaction()

    for naam in uvicorn_loggers_met_handler:
        assert _heeft_pii_filter(naam), f"{naam} mist de PII-redactie"


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
