"""Gedeelde, idempotente logging-bootstrap voor alle entrypoints (DEF-571).

Streamlit draait `main.py` niet bij directe navigatie naar een subpagina
(`/synonym_admin`) — dezelfde root-cause als DEF-572. Elke pagina is dus een
eigen entrypoint en moet de logging-configuratie zelf garanderen.

Waarom niet enkel `install_pii_redaction_filter()` per pagina: dat hangt de
filter op de *bestaande* handlers en is een stille no-op zolang de root-logger
er geen heeft. Deze bootstrap garandeert eerst een handler, dan de filter.
"""

from __future__ import annotations

import logging
import os

from utils.logging_filters import install_pii_redaction_filter
from utils.structured_logging import setup_structured_logging

_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_JSON_LOG_FILE = "logs/app.json.log"


def ensure_logging_configured(
    level: int = logging.INFO, fmt: str = _LOG_FORMAT
) -> None:
    """Garandeer een geconfigureerde root-logger met actieve PII-redactie.

    Idempotent en veilig vanaf elk entrypoint. De volgorde is wezenlijk:
    structured logging voegt zijn JSON-handler toe, `basicConfig` doet daarna
    niets meer (er zijn dan handlers), en de redactie-filter komt op álle
    handlers — inclusief de JSON-handler. Omgekeerd zou de JSON-handler
    ongefilterd blijven.

    STRUCTURED_LOGGING hoort hier en niet in `main.py`: subpagina's draaien
    main.py niet en kregen anders nooit de JSON-handler.

    Args:
        level: Log-level voor de root-logger.
        fmt: Formatstring. CLI-tools gebruiken `"%(message)s"` voor schone
            console-output; `basicConfig` is een no-op zodra er handlers zijn,
            dus het format moet hier meekomen en niet later gezet worden.

    Faalt nooit: logging mag de applicatie niet breken. Slaagt de redactie
    niet, dan wordt dat als error gelogd (gevoelige data kan dan in de logs
    verschijnen).
    """
    try:
        if os.getenv("STRUCTURED_LOGGING", "false").lower() == "true":
            setup_structured_logging(enable_json=True, log_file=_JSON_LOG_FILE)
        logging.basicConfig(level=level, format=fmt)
        install_pii_redaction_filter()
    except Exception as exc:
        logging.getLogger(__name__).error(
            "PII redactie filter initialisatie gefaald - "
            "gevoelige data kan in logs verschijnen: %s",
            exc,
        )


__all__ = ["ensure_logging_configured"]
