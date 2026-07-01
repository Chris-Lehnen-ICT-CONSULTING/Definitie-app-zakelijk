import logging

import pytest

from utils.logging_filters import PIIRedactingFilter, install_pii_redaction_filter

pytestmark = [pytest.mark.integration]


def _capture_logs(logger: logging.Logger, level=logging.INFO):
    stream = []

    class ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            stream.append(self.format(record))

    handler = ListHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return stream, handler


def test_logging_filter_redacts_openai_key():
    logger = logging.getLogger("test.redact.openai")
    logger.setLevel(logging.INFO)
    filt = PIIRedactingFilter()
    logger.addFilter(filt)
    stream, handler = _capture_logs(logger)
    try:
        logger.info("Using OPENAI_API_KEY=sk-ABCDEFGHIJKLmnopQRSTuvwx1234567890")
        assert stream, "No log captured"
        msg = stream[-1]
        # _mask_token levert "sk***7890": prefix + laatste 4, koppelteken verdwijnt.
        assert "sk***" in msg
        assert "[REDACTED]" in msg or "***" in msg
        assert "sk-ABCDEFGHIJKL" not in msg  # middelste deel gemaskeerd
    finally:
        logger.removeFilter(filt)
        logger.removeHandler(handler)


def test_logging_filter_redacts_email_and_bsn():
    logger = logging.getLogger("test.redact.pii")
    logger.setLevel(logging.INFO)
    filt = PIIRedactingFilter()
    logger.addFilter(filt)
    stream, handler = _capture_logs(logger)
    try:
        logger.info("contact=user@example.com; bsn=123456789")
        assert stream, "No log captured"
        msg = stream[-1]
        assert "user@example.com" not in msg
        assert "[REDACTED]" in msg
        assert "bsn=[REDACTED]" in msg
    finally:
        logger.removeFilter(filt)
        logger.removeHandler(handler)


def test_ancestor_logger_filter_does_NOT_reach_child_records():
    """Documenteert de bug (DEF-486): een filter op een *ancestor-logger* wordt
    NIET toegepast op records die van child-loggers propageren.

    Dit is precies de kapotte wiring in main.py: het filter zat op de
    root-logger, terwijl elke module via getLogger(__name__) een child-logger
    gebruikt. Deze test bewijst dat die opzet lekt.
    """
    parent = logging.getLogger("test.def486.broken")
    parent.setLevel(logging.INFO)
    parent.addFilter(
        PIIRedactingFilter()
    )  # filter op de LOGGER (fout, zoals oud main.py)
    stream, handler = _capture_logs(parent)
    child = logging.getLogger("test.def486.broken.child")
    child.setLevel(logging.INFO)
    try:
        child.info("token=sk-ABCDEFGHIJKLmnopQRSTuvwx1234567890")
        assert stream, "No log captured"
        # Bug: het token lekt ONGEMASKEERD omdat het ancestor-filter wordt overgeslagen.
        assert "sk-ABCDEFGHIJKLmnop" in stream[-1]
    finally:
        for f in list(parent.filters):
            parent.removeFilter(f)
        parent.removeHandler(handler)


def test_install_pii_redaction_filter_redacts_child_logger_records():
    """Regressietest voor DEF-486: na install op de HANDLERS worden records van
    child-loggers wél geredigeerd — de situatie die main.py in productie nodig heeft.
    """
    parent = logging.getLogger("test.def486.fixed")
    parent.setLevel(logging.INFO)
    stream, handler = _capture_logs(
        parent
    )  # handler bestaat vóór install (zoals basicConfig)
    install_pii_redaction_filter(parent)  # de fix: filter op de handlers
    child = logging.getLogger("test.def486.fixed.child")
    child.setLevel(logging.INFO)
    try:
        child.info("token=sk-ABCDEFGHIJKLmnopQRSTuvwx1234567890")
        assert stream, "No log captured"
        msg = stream[-1]
        assert "sk-ABCDEFGHIJKLmnop" not in msg, f"token lekte: {msg}"
        assert "***" in msg or "[REDACTED]" in msg
    finally:
        for f in list(handler.filters):
            handler.removeFilter(f)
        parent.removeHandler(handler)


def test_install_pii_redaction_filter_is_idempotent():
    """Twee keer installeren mag niet dubbel filteren of stapelen."""
    parent = logging.getLogger("test.def486.idempotent")
    parent.setLevel(logging.INFO)
    stream, handler = _capture_logs(parent)
    install_pii_redaction_filter(parent)
    install_pii_redaction_filter(parent)
    try:
        pii_filters = [f for f in handler.filters if isinstance(f, PIIRedactingFilter)]
        assert len(pii_filters) == 1, "filter mag maar één keer op de handler staan"
    finally:
        for f in list(handler.filters):
            handler.removeFilter(f)
        parent.removeHandler(handler)
