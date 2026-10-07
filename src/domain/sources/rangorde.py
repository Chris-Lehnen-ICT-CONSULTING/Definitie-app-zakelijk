"""Rangorde van aangeleverde bronnen (DEF-844).

Web-, RAG- en documentbronnen dragen elk een score op een eigen schaal: een
webbron een (geboosted, op 1.0 afgekapte) providerconfidence, een RAG-fragment
een cosine-score (in de praktijk ~0.3–0.6), een document een termtreffer.
Die scores zijn onderling niet vergelijkbaar. De volgorde volgt daarom eerst
het **brontype** en pas daarbinnen de eigen score:

1. Wettelijke bronnen: RAG-fragmenten met ``bron_type == "wetgeving"`` en
   webbronnen van een officieel wetgevingsdomein (zie ``WETGEVING_HOSTS``) of
   uit het eigen wetgevingskanaal (``WETGEVING_PROVIDERS``; een BWB-treffer
   heeft niet altijd een URL).
2. Eigen bronnen: geüploade documenten, daarna overige RAG-fragmenten (de
   volgorde van vóór DEF-844 tussen die twee blijft zo behouden).
3. Overige webbronnen (encyclopedisch/algemeen: Wikipedia, Wiktionary,
   zoekmachines, maar ook jurisprudentie — geen wetgeving).

Binnen een groep: per kanaal (document → rag → web) en binnen een kanaal op
score aflopend. Documenten behouden hun aangeleverde volgorde (hun score is
alleen een termtreffer). De sortering is stabiel; er valt geen bron weg en er
verandert geen veld — de relevantiepoort (DEF-620) blijft volledig
stroomopwaarts.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any, TypeVar
from urllib.parse import urlsplit

# Officiële publicatieplaatsen van wet- en regelgeving. Bewust smal: alleen
# hosts waar geconsolideerde of bekendgemaakte regelgeving staat; algemene
# overheidsdomeinen (repository.overheid.nl, rijksoverheid.nl) en
# rechtspraak.nl zijn geen wetgeving.
WETGEVING_HOSTS: tuple[str, ...] = (
    "wetten.overheid.nl",
    "lokaleregelgeving.overheid.nl",
    "zoek.officielebekendmakingen.nl",
    "officielebekendmakingen.nl",
    "eur-lex.europa.eu",
)
# Webprovider (`source.name`, kleine letters) van het SRU-kanaal op het
# Basiswettenbestand (sru_service: "Wetgeving.nl", x-connection=BWB).
WETGEVING_PROVIDERS: tuple[str, ...] = ("wetgeving.nl",)

RANG_WETTELIJK = 0
RANG_EIGEN = 1
RANG_OVERIG_WEB = 2

_KANAALVOLGORDE = {"documents": 0, "rag": 1}
_KANAAL_WEB = 2

B = TypeVar("B")


def _host(url: Any) -> str:
    if not isinstance(url, str) or not url.strip():
        return ""
    try:
        return (urlsplit(url.strip()).hostname or "").casefold()
    except ValueError:
        return ""


def is_wetgevingsdomein(url: Any) -> bool:
    """True als de URL op een officieel wetgevingsdomein (of subdomein) staat."""
    host = _host(url)
    return any(host == h or host.endswith("." + h) for h in WETGEVING_HOSTS)


def bronrang(bron: Mapping[str, Any]) -> int:
    """Brontype-prioriteit: 0 wettelijk, 1 eigen bron, 2 overige webbron."""
    provider = str(bron.get("provider") or "").casefold()
    if provider == "rag":
        bron_type = str(bron.get("bron_type") or "").casefold()
        return RANG_WETTELIJK if bron_type == "wetgeving" else RANG_EIGEN
    if provider == "documents":
        return RANG_EIGEN
    if provider in WETGEVING_PROVIDERS:
        return RANG_WETTELIJK
    url = bron.get("url") or bron.get("link")
    return RANG_WETTELIJK if is_wetgevingsdomein(url) else RANG_OVERIG_WEB


def _score(bron: Mapping[str, Any]) -> float:
    try:
        score = float(bron.get("score") or 0.0)
    except (TypeError, ValueError):
        return 0.0
    # NaN maakt een sortering onvoorspelbaar; telt als geen score.
    return 0.0 if math.isnan(score) else score


def _sorteersleutel(bron: Any) -> tuple[int, int, float]:
    if not isinstance(bron, Mapping):
        # Onleesbaar element: achteraan, in aangeleverde volgorde.
        return (RANG_OVERIG_WEB + 1, _KANAAL_WEB + 1, 0.0)
    provider = str(bron.get("provider") or "").casefold()
    kanaal = _KANAALVOLGORDE.get(provider, _KANAAL_WEB)
    # Documentscore is een termtreffer, geen relevantie: aangeleverde volgorde.
    score = 0.0 if provider == "documents" else _score(bron)
    return (bronrang(bron), kanaal, -score)


def rangschik_bronnen(bronnen: Iterable[B]) -> list[B]:
    """Nieuwe lijst in DEF-844-rangorde; dezelfde objecten, niets gemuteerd."""
    return sorted(bronnen, key=_sorteersleutel)
