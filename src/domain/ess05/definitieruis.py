"""ESS-05 — ruis uit een opgeslagen definitietekst neutraliseren (DEF-768, robuustheid P1).

Besluit Chris 29-09 (punt 2): vóór de ESS-05-beoordeling gaan een
categorie-voorregel aan het begin van de definitie en bronlabels "[Bron n]" uit
de tekst, consequent in wat het model als definitie krijgt en in de dekkings-
en citaatcontrole (`contract.beoordelingsmateriaal` is de enige plek). De
opgeslagen data blijft ongewijzigd; de vingerafdruk bindt de opgeslagen tekst.

Alleen vaste patronen, geïnventariseerd in de echte database (read-only,
29-09-2026, 183 records): `- Ontologische categorie: <cat>` (soort 19, proces
3, resultaat 1), `**Ontologische categorie: <cat>**` (1), `**<Cat>**` (1) en
een regel met alleen `<Cat>` (3), met <cat> een van soort, proces, resultaat of
exemplaar; `[Bron n]` in 2 records. Geen vrije heuristiek: een voorregel telt
alleen als eigen eerste regel, andere blokhaken en regels blijven staan.
"""

from __future__ import annotations

import re

__all__ = ["neutraliseer_definitieruis"]

_CATEGORIE = r"(?:soort|proces|resultaat|exemplaar)"
#: Eén categorie-voorregel als eerste regel, plus de witruimte tot de definitie.
_VOORREGEL = re.compile(
    r"\A(?:"
    rf"- Ontologische categorie: {_CATEGORIE}"
    rf"|\*\*Ontologische categorie: {_CATEGORIE}\*\*"
    rf"|\*\*{_CATEGORIE}\*\*"
    rf"|{_CATEGORIE}"
    r")[ \t]*\n\s*",
    re.IGNORECASE,
)
#: Een bronlabel met de spaties of tabs ervoor.
_BRONLABEL = re.compile(r"[ \t]*\[Bron \d+\]")


def neutraliseer_definitieruis(tekst: str) -> str:
    """De definitietekst zonder categorie-voorregel en zonder bronlabels."""
    return _BRONLABEL.sub("", _VOORREGEL.sub("", tekst, count=1))
