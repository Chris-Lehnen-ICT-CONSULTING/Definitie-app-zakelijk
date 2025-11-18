"""
Logging filters voor redactie/masking van gevoelige gegevens in logregels.

Implementeert een `PIIRedactingFilter` die o.a. API-sleutels, tokens en
basis-PII patronen (e-mail, BSN-tags) maskeert. Ontworpen om lichtgewicht te
zijn en geen externe afhankelijkheden te introduceren.
"""

from __future__ import annotations

import logging
import re
from typing import Any

REDACTED = "[REDACTED]"


def _mask_token(value: str) -> str:
    """Redact gevoelige token-achtige waarden, behoudt desgewenst de laatste 4 chars."""
    if not value:
        return value
    if len(value) <= 8:
        return REDACTED
    return f"{value[:2]}***{value[-4:]}"


def _redact_text(text: str) -> str:
    """Pas maskering toe op bekende patronen in de gegeven tekst."""
    if not text or not isinstance(text, str):
        return text

    s = text

    # 1) OpenAI sleutelpatroon (sk-<alnum>..)
    s = re.sub(r"sk-[A-Za-z0-9]{16,}", lambda m: _mask_token(m.group(0)), s)

    # 2) Lange hex tokens (32-64 tekens)
    s = re.sub(r"\b[0-9a-fA-F]{32,64}\b", REDACTED, s)

    # 3) Base64-achtige tokens (minimaal 32 tekens)
    s = re.sub(r"\b[A-Za-z0-9+/]{32,}={0,2}\b", REDACTED, s)

    # 4) API key velden in key=value of JSON-achtig formaat
    s = re.sub(
        r"(?i)(api[_-]?key|openai_api_key|token|bearer)[\s:=]+([\w+/=\-.]{8,})",
        lambda m: f"{m.group(1)}={REDACTED}",
        s,
    )

    # 5) E-mail adressen
    s = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", REDACTED, s)

    # 6) BSN-tags (voorkom over-masking; alleen wanneer expliciet gelabeld)
    return re.sub(r"(?i)\bbsn\s*[:=]?\s*\d{8,9}\b", "bsn=" + REDACTED, s)


class PIIRedactingFilter(logging.Filter):
    """Logging filter die gevoelige gegevens maskeert in logrecords."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            # Redact hoofdbericht
            if isinstance(record.msg, str):
                record.msg = _redact_text(record.msg)

            # Redact args (dict, tuple of enkelvoudig)
            if record.args:
                record.args = self._redact_args(record.args)

            # Redact extra bekende attributen indien aanwezig
            for key in ("error", "message"):
                if hasattr(record, key):
                    val = getattr(record, key)
                    if isinstance(val, str):
                        setattr(record, key, _redact_text(val))
        except Exception:
            # Fail-safe: nooit logging breken
            return True
        return True

    def _redact_args(self, args: Any) -> Any:
        if isinstance(args, dict):
            return {
                k: (_redact_text(v) if isinstance(v, str) else v)
                for k, v in args.items()
            }
        if isinstance(args, list | tuple):
            red = [(_redact_text(v) if isinstance(v, str) else v) for v in args]
            return type(args)(red)
        if isinstance(args, str):
            return _redact_text(args)
        return args


__all__ = ["PIIRedactingFilter"]
