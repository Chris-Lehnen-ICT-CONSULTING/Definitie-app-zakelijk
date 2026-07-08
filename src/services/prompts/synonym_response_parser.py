"""Defensieve parser voor LLM-synoniem-output (DEF-459 / DEF-471-thema).

Verwacht JSON {"synoniemen": [{"synoniem","confidence","rationale"}, ...]},
maar is robuust tegen markdown-fences, extra tekst, ontbrekende keys,
confidence buiten [0,1] en volledig kapotte output. Faalt nooit hard:
onparseerbare of ongeldige items worden overgeslagen (gelogd), niet gethrowd.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from models.synonym_models import SynonymSuggestion

logger = logging.getLogger(__name__)

_DECODER = json.JSONDecoder()


def _extract_synonym_object(raw: str) -> dict[str, Any] | None:
    """Vind het JSON-object met key 'synoniemen' in vrije tekst.

    Scant vanaf elke '{' met raw_decode i.p.v. een greedy regex: dat verwerkt
    geneste accolades correct én negeert omringende prose/placeholders (bv.
    '{term}') en meerdere JSON-objecten zonder geldige data te verliezen.
    """
    idx = 0
    length = len(raw)
    while idx < length:
        brace = raw.find("{", idx)
        if brace == -1:
            break
        try:
            obj, end = _DECODER.raw_decode(raw, brace)
        except json.JSONDecodeError:
            idx = brace + 1
            continue
        if isinstance(obj, dict) and "synoniemen" in obj:
            return obj
        idx = max(end, brace + 1)
    return None


def parse_synonym_response(raw: str | None) -> list[SynonymSuggestion]:
    if not raw or not raw.strip():
        return []

    data = _extract_synonym_object(raw)
    if data is None:
        logger.warning("Synoniem-parser: geen JSON-object met 'synoniemen' gevonden")
        return []

    items = data.get("synoniemen")
    if not isinstance(items, list):
        logger.warning("Synoniem-parser: 'synoniemen' ontbreekt of is geen lijst")
        return []

    suggestions: list[SynonymSuggestion] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        term = item.get("synoniem")
        if not isinstance(term, str) or not term.strip():
            continue
        raw_conf = item.get("confidence", 0.5)
        try:
            confidence = float(raw_conf)
        except (TypeError, ValueError):
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))
        rationale = item.get("rationale")
        rationale = rationale if isinstance(rationale, str) else ""
        try:
            suggestions.append(
                SynonymSuggestion(
                    synoniem=term.strip(), confidence=confidence, rationale=rationale
                )
            )
        except ValueError as exc:
            logger.warning("Synoniem-parser: item overgeslagen (%s)", exc)
            continue

    return suggestions
