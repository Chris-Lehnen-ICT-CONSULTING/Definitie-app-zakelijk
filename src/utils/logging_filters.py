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

    # 1) API-sleutels met `sk-`-prefix (OpenAI én Anthropic).
    # DEF-583: `-` en `_` horen in de charset. De oude regel eiste 16+ *alfanumerieke*
    # tekens direct ná `sk-`, waardoor de moderne formaten er ongeredigeerd door
    # glipten: `sk-proj-...` breekt af na 4 tekens, `sk-ant-api03-...` na 3.
    # Anthropic is de default provider, dus dat was de sleutel die in productie in
    # een traceback kon belanden. De `sk-`-prefix is specifiek genoeg om
    # over-redactie te voorkomen (anders dan de base64-regel, zie DEF-580).
    s = re.sub(r"sk-[A-Za-z0-9_-]{16,}", lambda m: _mask_token(m.group(0)), s)

    # 2) Lange hex tokens (32-64 tekens)
    s = re.sub(r"\b[0-9a-fA-F]{32,64}\b", REDACTED, s)

    # 3) Base64-achtige tokens (minimaal 32 tekens).
    # DEF-580: `/` staat bewust NIET in de charset. Met slash matchte elk
    # filesystem-pad van 32+ tekens als token, waardoor DB-paden, importpaden en
    # tracebacks onleesbaar werden. Base64 mét slashes wordt daardoor alleen nog
    # gevangen als een segment zelf 32+ tekens haalt; de sk-, hex- en
    # api_key=-regels hierboven/hieronder draaien onafhankelijk en dekken de
    # praktische secret-vormen.
    s = re.sub(r"\b[A-Za-z0-9+]{32,}={0,2}\b", REDACTED, s)

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

            self._redact_traceback(record)
        except Exception:
            # Fail-safe: nooit logging breken
            return True
        return True

    @staticmethod
    def _redact_traceback(record: logging.LogRecord) -> None:
        """Redigeer de traceback vóór de formatter hem rendert (DEF-575).

        `Formatter.format()` roept `formatException()` alleen aan als
        `exc_text` nog leeg is. Door hem hier gevuld én geredigeerd achter te
        laten, komt de onbewerkte traceback nooit in de output. `exc_info`
        blijft staan voor handlers die hem zelf lezen.
        """
        if not record.exc_info:
            return
        if not record.exc_text:
            record.exc_text = logging.Formatter().formatException(record.exc_info)
        record.exc_text = _redact_text(record.exc_text)

    def _redact_args(self, args: Any) -> Any:
        if isinstance(args, dict):
            return {k: self._redact_value(v) for k, v in args.items()}
        if isinstance(args, list | tuple):
            return type(args)(self._redact_value(v) for v in args)
        return self._redact_value(args)

    @staticmethod
    def _redact_value(value: Any) -> Any:
        """Redigeer strings en exceptions; laat de rest ongemoeid.

        Een `Exception` als ``%s``-argument (``logger.error("...: %s", exc)``)
        is een veelgebruikt patroon en droeg voorheen ongeredigeerde PII. Andere
        types blijven intact zodat ``%d``-formatting niet breekt.
        """
        if isinstance(value, str):
            return _redact_text(value)
        if isinstance(value, BaseException):
            return _redact_text(str(value))
        return value


def install_pii_redaction_filter(logger: logging.Logger | None = None) -> None:
    """Installeer de PII-redactie op de HANDLERS van ``logger`` (default: root).

    DEF-486: een filter dat via ``Logger.addFilter`` op een logger hangt, wordt
    door Python **alleen** toegepast op records die direct op díe logger worden
    gelogd — niet op records die vanuit child-loggers (``getLogger(__name__)``)
    propageren naar de handlers van een ancestor. Redactie moet daarom op de
    *handlers* zitten, want die verwerken álle propagerende records.

    Idempotent: voegt per handler hoogstens één ``PIIRedactingFilter`` toe.
    Roep dit aan *nadat* de handlers bestaan (bv. ná ``logging.basicConfig`` of
    ``dictConfig``).
    """
    target = logger if logger is not None else logging.getLogger()
    for handler in target.handlers:
        if not any(isinstance(f, PIIRedactingFilter) for f in handler.filters):
            handler.addFilter(PIIRedactingFilter())


__all__ = ["PIIRedactingFilter", "install_pii_redaction_filter"]
