"""Rangorde van aangeleverde bronnen (DEF-844).

Web-, RAG- en documentbronnen dragen elk een score op een eigen schaal: een
webbron een (geboosted, op 1.0 afgekapte) providerconfidence, een RAG-fragment
een cosine-score (in de praktijk ~0.3–0.6), een document een termtreffer.
Die scores zijn onderling niet vergelijkbaar. De volgorde volgt daarom eerst
het **brontype** en pas daarbinnen de eigen score:

1. Wettelijke bronnen, alleen op aantoonbare herkomst:
   - RAG-fragmenten met ``bron_type == "wetgeving"`` uit de bronbibliotheek
     (een bekende collectie die niet de uploadcollectie is);
   - webbronnen uit het BWB-kanaal (``WETGEVING_PROVIDERS``; een BWB-treffer
     heeft niet altijd een URL) of van ``WETGEVING_HOSTS``;
   - webbronnen van een gemengd publicatiedomein (``GEMENGDE_HOSTS``) alleen
     als het meegeleverde documenttype (SRU ``dc_type``) wet- of regelgeving
     aanduidt — daar staan ook Kamerstukken, Kamervragen en arresten.
2. Eigen bronnen: geüploade documenten en alle overige RAG-fragmenten. Een
   upload telt nooit als wettelijk, ook niet met een ``wetgeving``-label (dat
   label zet de uploadroute op basis van een gekozen rechtsgebied).
3. Overige webbronnen (encyclopedisch/algemeen: Wikipedia, Wiktionary,
   zoekmachines, maar ook jurisprudentie en Kamerstukken — geen wetgeving).

Binnen een groep: per kanaal (document → rag → web) en binnen een kanaal op
score aflopend. Documenten behouden hun aangeleverde volgorde (hun score is
alleen een termtreffer). De rangorde bepaalt alleen de **volgorde** van wat
al geselecteerd is — nooit welke bronnen worden opgenomen; selectie,
budgetten en de relevantiepoort (DEF-620) blijven volledig stroomopwaarts.
Weergave (``rangschik_bronnen``) en prompt (``sorteersleutel``) gebruiken
dezelfde sleutel.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any, TypeVar
from urllib.parse import urlsplit

# Hosts waar uitsluitend geconsolideerde wet- en regelgeving staat.
WETGEVING_HOSTS: tuple[str, ...] = (
    "wetten.overheid.nl",
    "lokaleregelgeving.overheid.nl",
)
# Gemengde publicatieplaatsen: naast regelgeving ook Kamerstukken,
# Kamervragen, Handelingen en (EUR-Lex) arresten. Host alleen is geen bewijs.
GEMENGDE_HOSTS: tuple[str, ...] = (
    "officielebekendmakingen.nl",
    "eur-lex.europa.eu",
)
# Documenttypen (SRU ``dc_type``, kleine letters) die wet- of regelgeving
# aanduiden. Bewust smal: een onbekend of ontbrekend type telt als "overig".
WETGEVING_DOCUMENTTYPEN: frozenset[str] = frozenset(
    {
        "wet",
        "rijkswet",
        "amvb",
        "algemene maatregel van bestuur",
        "ministeriele-regeling",
        "ministeriele regeling",
        "ministeriële regeling",
        "verordening",
        "richtlijn",
        "regulation",
        "directive",
        "staatsblad",
    }
)
# Webprovider (`source.name`, kleine letters) van het SRU-kanaal op het
# Basiswettenbestand (sru_service: "Wetgeving.nl", x-connection=BWB).
WETGEVING_PROVIDERS: tuple[str, ...] = ("wetgeving.nl",)
# RAG-collectie van de uploadroute (document_upload_renderer en de
# standaardcollectie van de orchestrator).
UPLOAD_COLLECTIE = "user_documents"

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


def _op_host(url: Any, hosts: tuple[str, ...]) -> bool:
    host = _host(url)
    return any(host == h or host.endswith("." + h) for h in hosts)


def is_wetgevingsdomein(url: Any) -> bool:
    """True als de URL op een host met uitsluitend wetgeving (of subdomein) staat."""
    return _op_host(url, WETGEVING_HOSTS)


def is_wetgevingsdocumenttype(documenttype: Any) -> bool:
    """True als het aangeleverde documenttype wet- of regelgeving aanduidt."""
    if not isinstance(documenttype, str):
        return False
    return documenttype.strip().casefold() in WETGEVING_DOCUMENTTYPEN


def _rag_rang(bron: Mapping[str, Any]) -> int:
    bron_type = str(bron.get("bron_type") or "").casefold()
    collectie = str(bron.get("collection_name") or "").strip()
    # Herkomst verplicht: zonder bekende collectie (oudere records) of uit de
    # uploadcollectie is een wetgeving-label geen bewijs.
    if bron_type == "wetgeving" and collectie and collectie != UPLOAD_COLLECTIE:
        return RANG_WETTELIJK
    return RANG_EIGEN


def bronrang(bron: Mapping[str, Any]) -> int:
    """Brontype-prioriteit: 0 wettelijk, 1 eigen bron, 2 overige webbron."""
    provider = str(bron.get("provider") or "").casefold()
    if provider == "rag":
        return _rag_rang(bron)
    if provider == "documents":
        return RANG_EIGEN
    if provider in WETGEVING_PROVIDERS:
        return RANG_WETTELIJK
    url = bron.get("url") or bron.get("link")
    if is_wetgevingsdomein(url):
        return RANG_WETTELIJK
    if _op_host(url, GEMENGDE_HOSTS) and is_wetgevingsdocumenttype(
        bron.get("document_type")
    ):
        return RANG_WETTELIJK
    return RANG_OVERIG_WEB


def _score(bron: Mapping[str, Any]) -> float:
    try:
        score = float(bron.get("score") or 0.0)
    except (TypeError, ValueError):
        return 0.0
    # NaN maakt een sortering onvoorspelbaar; telt als geen score.
    return 0.0 if math.isnan(score) else score


def sorteersleutel(bron: Any) -> tuple[int, int, float]:
    """De gedeelde DEF-844-sleutel: (brontype, kanaal, -eigen score).

    Kanaal via ``provider``: ``"documents"``, ``"rag"`` of een webprovider.
    """
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
    return sorted(bronnen, key=sorteersleutel)
