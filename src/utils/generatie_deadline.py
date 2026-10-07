"""DEF-842: de deadline van de lopende generatie, voor stappen binnen de keten.

De UI begrenst de hele generatie op één tijdsbudget (DEF-840:
``definition_generation`` in ``config/rate_limit_config.py``). Een stap diep
in de keten — zoals de CON-02-bronbeoordeling met haar herhaling — moet
binnen het resterende deel van dat budget blijven; anders annuleert de
UI-grens de hele generatie in plaats van alleen die stap te laten mislukken.

De deadline reist als ``ContextVar`` mee: geen procesglobale toestand,
geïsoleerd per asyncio-taak, en taken die binnen de generatie starten erven
haar. Buiten een generatie (bijv. hervalidatie vanuit de bewerktab) is er
geen deadline en gelden alleen de eigen grenzen van een stap.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

__all__ = ["generatie_deadline", "huidige_generatie_deadline"]

#: Absolute deadline als ``time.monotonic()``-tijdstip, of None.
_DEADLINE: ContextVar[float | None] = ContextVar("generatie_deadline", default=None)


@contextmanager
def generatie_deadline(seconden: float) -> Iterator[float]:
    """Zet de generatiedeadline op nu + ``seconden`` voor de duur van het blok.

    Een al lopende, strengere deadline blijft gelden (geneste generaties
    krijgen nooit meer tijd dan de buitenste). Levert de geldende deadline.
    """
    deadline = time.monotonic() + seconden
    lopend = _DEADLINE.get()
    if lopend is not None:
        deadline = min(deadline, lopend)
    token = _DEADLINE.set(deadline)
    try:
        yield deadline
    finally:
        _DEADLINE.reset(token)


def huidige_generatie_deadline() -> float | None:
    """De geldende generatiedeadline (``time.monotonic()``-tijdstip), of None."""
    return _DEADLINE.get()
