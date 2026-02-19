"""
Gedeelde utilities voor chunking strategieën.

Bevat zins-splitting, overlap-berekening en forceer-split logica
die door zowel juridische als generieke strategieën gebruikt worden.
"""

from __future__ import annotations

import re

from services.rag.token_counter import tel_tokens

# Defaults
MAX_TOKENS_PER_CHUNK = 1000
MIN_TOKENS_PER_CHUNK = 50
OVERLAP_RATIO_JURIDISCH = 0.12
OVERLAP_RATIO_GENERIEK = 0.10

# Abbreviation-safe sentence boundary: split on . ! ? followed by whitespace,
# but NOT after common Dutch/legal abbreviations.
_ZINSGRENS_RE = re.compile(
    r"(?<![Mm]r)(?<![Dd]r)(?<![Dd]rs)(?<![Ii]ng)(?<![Ii]r)"
    r"(?<![Aa]rt)(?<![Nn]r)(?<![Rr]esp)(?<![Bb]ijv)"
    r"(?<![Ee]vt)(?<![Zz]gn)"
    r"[.!?]\s+",
)


def split_zinnen(tekst: str) -> list[str]:
    """Split tekst op zinsgrenzen, veilig voor Nederlandse afkortingen."""
    delen = _ZINSGRENS_RE.split(tekst.strip())
    return [d for d in delen if d]


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


def forceer_split_op_zinnen(tekst: str, max_tokens: int) -> list[str]:
    """Split tekst op zinsgrenzen tot elk deel <= max_tokens.

    Gedeelde utility voor zowel juridische als generieke chunking.
    """
    zinnen = split_zinnen(tekst)
    if not zinnen:
        return [tekst] if tekst.strip() else []

    delen: list[str] = []
    huidige_delen: list[str] = []
    huidige_tokens = 0

    for zin in zinnen:
        zin_tokens = tel_tokens(zin)
        if huidige_tokens + zin_tokens > max_tokens and huidige_delen:
            delen.append(" ".join(huidige_delen))
            huidige_delen = []
            huidige_tokens = 0
        huidige_delen.append(zin)
        huidige_tokens += zin_tokens

    if huidige_delen:
        delen.append(" ".join(huidige_delen))

    return delen
