import logging

import pytest

from utils.logging_filters import PIIRedactingFilter

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
        # DEF-583: de sleutel wordt nu VOLLEDIG geredigeerd. Voorheen leverde
        # `_mask_token` "sk***7890" — prefix plus de laatste vier tekens van het
        # secret. Die staart dient geen debug-doel dat de prefix niet al dekt, en
        # was inconsistent met de hex- en base64-regels die altijd al volledig
        # redigeerden.
        assert "[REDACTED]" in msg
        assert "sk-ABCDEFGHIJKL" not in msg
        assert "7890" not in msg, "staart van de sleutel lekt nog"
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
