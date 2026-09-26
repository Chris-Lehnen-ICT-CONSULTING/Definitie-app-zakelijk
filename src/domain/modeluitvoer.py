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

__all__ = ["MAX_JSON_DIEPTE", "parse_modeluitvoer"]

#: Eén volledig markdown-codeblok om het antwoord; alleen dán wordt het uitgepakt.
_CODEBLOK = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.IGNORECASE | re.DOTALL)

#: Maximale nesting van objecten en lijsten (het buitenste object telt als 1).
#: Ruim boven elk afgesproken antwoordschema (answer/2 met vier claimniveaus
#: komt niet boven de 15), maar laag genoeg dat recursieve verwerking verderop
#: (deepcopy, json.dumps) nooit de recursiegrens raakt (DEF-768, A2-01).
MAX_JSON_DIEPTE = 64


def _te_diep(data: Any) -> bool:
    """Iteratief (zonder recursie): nest `data` dieper dan MAX_JSON_DIEPTE?"""
    stapel: list[tuple[Any, int]] = [(data, 1)]
    while stapel:
        waarde, diepte = stapel.pop()
        if isinstance(waarde, dict):
            kinderen = list(waarde.values())
        elif isinstance(waarde, list):
            kinderen = waarde
        else:
            continue
        if diepte > MAX_JSON_DIEPTE:
            return True
        stapel.extend((kind, diepte + 1) for kind in kinderen)
    return False


def parse_modeluitvoer(text: Any) -> dict[str, Any] | None:
    """Het JSON-object dat het héle modelantwoord vormt, of None.

    Gesloten (DEF-766, correctieronde 1, R2): het antwoord is één JSON-object,
    eventueel in één markdown-codeblok, en niets anders. Omliggende tekst,
    meerdere objecten, een lijst of afgekapte JSON worden niet 'gerepareerd'
    door een deelstring te kiezen — dat is een technische fout.

    Te diep geneste JSON is evenmin een JSON-object: zowel wat `json.loads`
    zelf niet kan lezen (RecursionError) als wat dieper nest dan
    MAX_JSON_DIEPTE (DEF-768, A2-01).
    """
    if not isinstance(text, str) or not text.strip():
        return None
    schoon = text.strip()
    omhuld = _CODEBLOK.fullmatch(schoon)
    if omhuld is not None:
        schoon = omhuld.group(1).strip()
    try:
        data = json.loads(schoon)
    except (json.JSONDecodeError, RecursionError):
        return None
    if not isinstance(data, dict) or _te_diep(data):
        return None
    return data
