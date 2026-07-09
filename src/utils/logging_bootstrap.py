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

from utils.logging_filters import install_pii_redaction_filter

_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def ensure_logging_configured(level: int = logging.INFO) -> None:
    """Garandeer een geconfigureerde root-logger met actieve PII-redactie.

    Idempotent en veilig vanaf elk entrypoint. `basicConfig` doet niets als de
    root-logger al handlers heeft, dus een bestaande configuratie (structured
    logging, dictConfig, Streamlit) blijft intact; alleen de redactie-filter
    wordt er alsnog op gehangen.

    Faalt nooit: logging mag de applicatie niet breken. Slaagt de redactie
    niet, dan wordt dat als error gelogd (gevoelige data kan dan in de logs
    verschijnen).
    """
    try:
        logging.basicConfig(level=level, format=_LOG_FORMAT)
        install_pii_redaction_filter()
    except Exception as exc:
        logging.getLogger(__name__).error(
            "PII redactie filter initialisatie gefaald - "
            "gevoelige data kan in logs verschijnen: %s",
            exc,
        )


__all__ = ["ensure_logging_configured"]
