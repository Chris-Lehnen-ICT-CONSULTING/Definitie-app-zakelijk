"""Shared XML source formatter voor alle brontypen in de prompt pipeline.

Standaardiseert RAG, web lookup en document bronnen naar uniform
XML-tags format: <bronnen><bron type="..." ...>tekst</bron></bronnen>.

DEF-315: Eén format voor alle brontypen.
DEF-743: Bronnen zijn DATA. Een `score` is uitsluitend een zoek-/selectiescore;
er wordt geen betrouwbaarheid, gezag of `level` uit afgeleid. `confidence` en
`level` blijven als kwargs bestaan voor bestaande aanroepers buiten de
generatieprompt (rag_service._format_context), maar de generatieprompt geeft
ze niet door. Een lege passage is geen bron.
"""

from __future__ import annotations

from xml.sax.saxutils import escape, quoteattr


def confidence_to_level(confidence: float) -> str:
    """Vertaal confidence score naar level label.

    Args:
        confidence: Score 0.0 - 1.0.

    Returns:
        "high" (>= 0.8), "medium" (0.5 - 0.8), of "low" (< 0.5).
    """
    if confidence >= 0.8:
        return "high"
    if confidence >= 0.5:
        return "medium"
    return "low"


def format_bron(
    nr: int,
    type: str,
    chunk_text: str,
    *,
    score: float | None = None,
    confidence: float | None = None,
    level: str | None = None,
    **attrs: str | float | int | None,
) -> str:
    """Format één <bron> tag met correcte XML escaping.

    Args:
        nr: Volgnummer (doorlopend over alle brontypen).
        type: Brontype — "rag", "web", of "document".
        chunk_text: De brontekst (wordt XML-escaped). Mag niet leeg zijn.
        score: Optionele zoek-/selectiescore (0.0-1.0) van de zoekfunctie.
            Zegt niets over gezag, toepasselijkheid of betrouwbaarheid.
        confidence: Alleen voor bestaande aanroepers buiten de generatieprompt;
            wordt uitsluitend gerenderd als hij expliciet is meegegeven.
        level: Idem; wordt uit `confidence` afgeleid als die is meegegeven.
        **attrs: Aangeleverde coördinaten (alleen als niet None/leeg), bijv.:
            RAG: rechtsgebied, regeling, artikel, lid, bronbestand, pagina, sectie
            Web: provider, url, titel, ecli, wet, artikel, citatie, opgehaald
            Document: titel, bestand, citatie, selectie
            Nooit verzonnen waarden meegeven: wat ontbreekt blijft weg.

    Returns:
        XML string: <bron nr="1" type="rag" ...>tekst</bron>

    Raises:
        ValueError: Bij een lege of alleen-witruimte passage — die is geen bron.
    """
    text = str(chunk_text)
    if not text.strip():
        msg = f"<bron nr={nr} type={type}> zonder inhoud: een lege passage is geen bron"
        raise ValueError(msg)

    parts = [f'nr="{nr}"', f'type="{type}"']

    if score is not None:
        parts.append(f'score="{score:.2f}"')

    if confidence is not None:
        parts.append(f'confidence="{confidence:.2f}"')
        if level is None:
            level = confidence_to_level(confidence)

    if level is not None:
        parts.append(f'level="{level}"')

    # Type-specifieke attributen (alleen als niet None/leeg)
    for key, value in attrs.items():
        if value is not None and value != "":
            parts.append(f"{key}={quoteattr(str(value))}")

    attr_str = " ".join(parts)
    escaped_text = escape(text)
    return f"  <bron {attr_str}>\n    {escaped_text}\n  </bron>"


def wrap_bronnen(bron_strings: list[str]) -> str:
    """Wrap lijst van <bron> strings in <bronnen> blok.

    Args:
        bron_strings: Lijst van strings geproduceerd door format_bron().

    Returns:
        Compleet <bronnen>...</bronnen> XML blok, of lege string als
        de lijst leeg is.
    """
    if not bron_strings:
        return ""

    inner = "\n".join(bron_strings)
    return f"<bronnen>\n{inner}\n</bronnen>"
