"""Gesloten lezing van een ruw modelantwoord als één JSON-object (pure logica).

Verplaatst uit `services.validation.ai_beoordeling_transport` (DEF-768,
R8-offsetherstel) zodat ook de domeinreplay een opgeslagen ruwe respons op
exact dezelfde manier kan lezen; de transportmodule exporteert deze functie
ongewijzigd door.
"""

from __future__ import annotations

import json
import re
from typing import Any

__all__ = ["parse_modeluitvoer"]

#: Eén volledig markdown-codeblok om het antwoord; alleen dán wordt het uitgepakt.
_CODEBLOK = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.IGNORECASE | re.DOTALL)


def parse_modeluitvoer(text: Any) -> dict[str, Any] | None:
    """Het JSON-object dat het héle modelantwoord vormt, of None.

    Gesloten (DEF-766, correctieronde 1, R2): het antwoord is één JSON-object,
    eventueel in één markdown-codeblok, en niets anders. Omliggende tekst,
    meerdere objecten, een lijst of afgekapte JSON worden niet 'gerepareerd'
    door een deelstring te kiezen — dat is een technische fout.
    """
    if not isinstance(text, str) or not text.strip():
        return None
    schoon = text.strip()
    omhuld = _CODEBLOK.fullmatch(schoon)
    if omhuld is not None:
        schoon = omhuld.group(1).strip()
    try:
        data = json.loads(schoon)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
