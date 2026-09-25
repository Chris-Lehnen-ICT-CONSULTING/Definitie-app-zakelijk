"""Gedeelde transporthulp voor directe AI-beoordelingen (ESS-03, ESS-05).

Oorspronkelijk onderdeel van `ess03_assessment_service` (DEF-766); in DEF-768
ongewijzigd verplaatst zodat de ESS-05-dienst dezelfde fail-closed
transportregels gebruikt zonder kopie: gesloten JSON-parse, telling van
werkelijk waargenomen transportpogingen, foutsoortindeling, de door de
provider gemelde stopreden en de normhash.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from collections.abc import Mapping
from typing import Any

# Verplaatst naar het domein (R8-offsetherstel); hier ongewijzigd doorgegeven.
from domain.modeluitvoer import parse_modeluitvoer
from services.interfaces import AIRateLimitError, AIServiceError, AITimeoutError

__all__ = [
    "Pogingenteller",
    "foutsoort",
    "normhash",
    "parse_modeluitvoer",
    "stop_reason",
]

#: Loggers waarop de onderliggende lagen een herhaalde transportpoging melden
#: (Anthropic/OpenAI-SDK `_base_client`: "Retrying request"; AsyncGPTClient
#: `utils.async_api`: "retrying in"). Een logfilter werkt alleen op de logger
#: waarop het record ontstaat, daarom de exacte namen.
_RETRY_LOGGERS: tuple[str, ...] = (
    "anthropic._base_client",
    "openai._base_client",
    "utils.async_api",
)
_RETRY_MARKERS: tuple[str, ...] = ("Retrying request", "retrying in")


def normhash(norm: Mapping[str, str]) -> str:
    """sha256 over de normtekst die in de prompt staat (beoordelingsbinding)."""
    return hashlib.sha256(
        json.dumps(dict(norm), ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


class Pogingenteller(logging.Filter):
    """Telt werkelijk waargenomen herhaalde transportpogingen tijdens één aanroep.

    De onderliggende lagen (Anthropic/OpenAI-SDK, `AsyncGPTClient`) melden een
    herhaling in hun log. Deze filter hangt tijdens de aanroep aan die loggers
    en telt de meldingen; `attempts_observed` = 1 + waargenomen herhalingen.
    Dit is een meting via de logs van die lagen, geen hardgecodeerde 0.
    """

    def __init__(self) -> None:
        super().__init__()
        self.herhalingen = 0
        self._loggers = [logging.getLogger(naam) for naam in _RETRY_LOGGERS]
        self._oude_niveaus: dict[str, int] = {}

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            bericht = record.getMessage()
        except Exception:  # pragma: no cover - defensief
            return True
        if any(marker in bericht for marker in _RETRY_MARKERS):
            self.herhalingen += 1
        return True

    def __enter__(self) -> Pogingenteller:
        for log in self._loggers:
            # De herhalingsmeldingen zijn INFO/WARNING; staat de logger hoger,
            # dan ontstaat het record niet en valt er niets te tellen. Tijdelijk
            # (alleen tijdens deze aanroep) op INFO; daarna hersteld.
            self._oude_niveaus[log.name] = log.level
            if log.getEffectiveLevel() > logging.INFO:
                log.setLevel(logging.INFO)
            log.addFilter(self)
        return self

    def __exit__(self, *exc: object) -> None:
        for log in self._loggers:
            log.removeFilter(self)
            log.setLevel(self._oude_niveaus.get(log.name, logging.NOTSET))

    def attributie(self) -> dict[str, int]:
        return {
            "attempts_observed": 1 + self.herhalingen,
            "retries_observed": self.herhalingen,
        }


def foutsoort(exc: BaseException) -> str:
    if isinstance(exc, AITimeoutError | asyncio.TimeoutError | TimeoutError):
        return "timeout"
    if isinstance(exc, AIRateLimitError):
        return "rate_limit"
    if isinstance(exc, AIServiceError):
        return "connection"
    return "unknown"


def stop_reason(resultaat: Any) -> str | None:
    """De door de provider gemelde stopreden uit `AIGenerationResult.metadata`
    (DEF-766, correctieronde 3, F1); None wanneer de AI-laag er geen meldt."""
    metadata = getattr(resultaat, "metadata", None)
    if not isinstance(metadata, Mapping):
        return None
    waarde = metadata.get("stop_reason")
    return waarde if isinstance(waarde, str) and waarde else None
