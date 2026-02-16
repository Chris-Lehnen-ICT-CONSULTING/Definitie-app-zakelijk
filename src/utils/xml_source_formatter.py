"""Shared XML source formatter voor alle brontypen in de prompt pipeline.

Standaardiseert RAG, web lookup en document bronnen naar uniform
XML-tags format: <bronnen><bron type="..." ...>tekst</bron></bronnen>.

DEF-315: Eén format voor alle brontypen.
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
        chunk_text: De brontekst (wordt XML-escaped).
        score: Optionele relevantiescore (0.0-1.0).
        confidence: Optionele betrouwbaarheidsscore (0.0-1.0).
        level: Optioneel level ("high"/"medium"/"low").
            Wordt automatisch berekend uit confidence als niet meegegeven.
        **attrs: Type-specifieke attributen, bijv.:
            RAG: rechtsgebied, regeling, artikel
            Web: provider, url, ecli, wet, artikel, citatie
            Document: titel, citatie

    Returns:
        XML string: <bron nr="1" type="rag" ...>tekst</bron>
    """
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
    escaped_text = escape(str(chunk_text))
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
