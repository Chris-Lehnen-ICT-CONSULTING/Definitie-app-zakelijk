"""
Gedeelde utilities voor chunking strategieën.

Bevat zins-splitting, overlap-berekening en forceer-split logica
die door zowel juridische als generieke strategieën gebruikt worden.
"""

from __future__ import annotations

import logging
import re

from services.rag.token_counter import tel_tokens

logger = logging.getLogger(__name__)

# Defaults
MAX_TOKENS_PER_CHUNK = 1000
MIN_TOKENS_PER_CHUNK = 50
OVERLAP_RATIO_JURIDISCH = 0.12
OVERLAP_RATIO_GENERIEK = 0.10

# Abbreviation-safe sentence boundary: match . ! ? followed by whitespace,
# but NOT after common Dutch/legal abbreviations.
# Used with finditer (not split) to preserve punctuation in results.
_ZINSGRENS_RE = re.compile(
    r"(?<![Mm]r)(?<![Dd]r)(?<![Dd]rs)(?<![Ii]ng)(?<![Ii]r)"
    r"(?<![Aa]rt)(?<![Nn]r)(?<![Rr]esp)(?<![Bb]ijv)"
    r"(?<![Ee]vt)(?<![Zz]gn)"
    r"[.!?]\s+",
)


def split_zinnen(tekst: str) -> list[str]:
    """Split tekst op zinsgrenzen, veilig voor Nederlandse afkortingen.

    Behoudt leestekens: elke zin eindigt met zijn originele .!? teken.
    """
    tekst = tekst.strip()
    if not tekst:
        return []

    # Vind alle zinsgrenzen en snij op de positie NA het leesteken
    zinnen: list[str] = []
    vorige_eind = 0

    for m in _ZINSGRENS_RE.finditer(tekst):
        # De match bevat "[.!?]\s+" — snij NA het leesteken (voor de whitespace)
        # m.start() = positie van .!?, m.end() = na de whitespace
        grens = m.start() + 1  # positie direct na het leesteken
        zin = tekst[vorige_eind:grens].strip()
        if zin:
            zinnen.append(zin)
        vorige_eind = m.end()

    # Laatste deel na de laatste match
    rest = tekst[vorige_eind:].strip()
    if rest:
        zinnen.append(rest)

    return zinnen


def bereken_overlap(tekst: str, ratio: float) -> str:
    """
    Bereken overlap-tekst: neem ~ratio van de tekst, afgekapt op zinsgrens.

    Returns de laatste paar zinnen die samen ~ratio van de token count vormen.
    """
    if not tekst:
        return ""

    tokens_totaal = tel_tokens(tekst)
    doel_tokens = int(tokens_totaal * ratio)
    if doel_tokens < 5:
        return ""

    zinnen = split_zinnen(tekst)
    if not zinnen:
        return ""

    # Neem zinnen van achteren tot we doel bereiken
    overlap_zinnen: list[str] = []
    token_count = 0
    for zin in reversed(zinnen):
        zin_tokens = tel_tokens(zin)
        if token_count + zin_tokens > doel_tokens and overlap_zinnen:
            break
        overlap_zinnen.insert(0, zin)
        token_count += zin_tokens

    return " ".join(overlap_zinnen)


def _split_op_tokens(tekst: str, max_tokens: int) -> list[str]:
    """Fallback: split tekst op token-grenzen wanneer geen zinsgrenzen beschikbaar.

    Probeert op woordgrenzen te splitten voor leesbaarheid.
    """
    woorden = tekst.split()
    if not woorden:
        return [tekst] if tekst.strip() else []

    delen: list[str] = []
    huidige: list[str] = []
    huidige_tokens = 0

    for woord in woorden:
        woord_tokens = tel_tokens(woord)
        if huidige_tokens + woord_tokens > max_tokens and huidige:
            delen.append(" ".join(huidige))
            huidige = []
            huidige_tokens = 0
        huidige.append(woord)
        huidige_tokens += woord_tokens

    if huidige:
        delen.append(" ".join(huidige))

    return delen


def forceer_split_op_zinnen(tekst: str, max_tokens: int) -> list[str]:
    """Split tekst op zinsgrenzen tot elk deel <= max_tokens.

    Gedeelde utility voor zowel juridische als generieke chunking.
    Valt terug op woord-gebaseerde split als een zin > max_tokens.
    """
    zinnen = split_zinnen(tekst)
    if not zinnen:
        return [tekst] if tekst.strip() else []

    delen: list[str] = []
    huidige_delen: list[str] = []
    huidige_tokens = 0

    for zin in zinnen:
        zin_tokens = tel_tokens(zin)

        # Mega-zin: splits op woordgrenzen
        if zin_tokens > max_tokens:
            # Flush huidige buffer eerst
            if huidige_delen:
                delen.append(" ".join(huidige_delen))
                huidige_delen = []
                huidige_tokens = 0
            delen.extend(_split_op_tokens(zin, max_tokens))
            continue

        if huidige_tokens + zin_tokens > max_tokens and huidige_delen:
            delen.append(" ".join(huidige_delen))
            huidige_delen = []
            huidige_tokens = 0
        huidige_delen.append(zin)
        huidige_tokens += zin_tokens

    if huidige_delen:
        delen.append(" ".join(huidige_delen))

    return delen
