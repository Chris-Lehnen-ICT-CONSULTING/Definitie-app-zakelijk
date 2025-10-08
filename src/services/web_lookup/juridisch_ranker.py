"""
Context-aware ranking voor juridische begrippen.

Deze module boost resultaten die juridische keywords bevatten en
prioriteert juridische bronnen (rechtspraak.nl, wetgeving.nl) boven
algemene bronnen (Wikipedia).

Gebruik:
    from .juridisch_ranker import boost_juridische_resultaten

    results = await wikipedia_lookup("voorlopige hechtenis")
    boosted = boost_juridische_resultaten(results, context=["Sv", "strafrecht"])
"""

import logging
import re

logger = logging.getLogger(__name__)

# Juridische keywords voor content analysis
JURIDISCHE_KEYWORDS = {
    # Algemeen juridisch
    "wetboek",
    "artikel",
    "wet",
    "recht",
    "rechter",
    "vonnis",
    "uitspraak",
    "rechtspraak",  # Note: duplicate removed (was on line 36)
    "juridisch",
    "wettelijk",
    "strafbaar",
    "rechtbank",
    "gerechtshof",
    "hoge raad",
    # Strafrecht
    "strafrecht",
    "verdachte",
    "beklaagde",
    "dagvaarding",
    "veroordeling",
    "vrijspraak",
    "schuldig",
    "delict",
    "misdrijf",
    "overtreding",
    # Burgerlijk recht
    "burgerlijk",
    "civiel",
    "overeenkomst",
    "contract",
    "schadevergoeding",
    "aansprakelijkheid",
    # Bestuursrecht
    "bestuursrecht",
    "beschikking",
    "besluit",
    "bezwaar",
    "beroep",
    "awb",
    # Procesrecht
    "procedure",
    "proces",
    "hoger beroep",
    "cassatie",
    "appel",
    # Wetten (afkortingen)
    "sr",
    "sv",
    "rv",
    "bw",
}

# Juridische domeinen voor URL filtering
JURIDISCHE_DOMEINEN = {
    "rechtspraak.nl",
    "overheid.nl",
    "wetgeving.nl",
    "wetten.overheid.nl",
    "officielebekendmakingen.nl",
    "zoekservice.overheid.nl",
    "repository.overheid.nl",
    "data.rechtspraak.nl",
}

# Regex voor artikel-referenties (Art. 123, Artikel 12a)
ARTIKEL_PATTERN = re.compile(r"\b(?:artikel|art\.?)\s+(\d+[a-z]?)\b", re.IGNORECASE)

# Regex voor lid-referenties (lid 2, tweede lid)
LID_PATTERN = re.compile(
    r"\b(?:lid|eerste|tweede|derde|vierde|vijfde)\s+(?:lid\s+)?(\d+|eerste|tweede|derde|vierde|vijfde)\b",
    re.IGNORECASE,
)


def is_juridische_bron(url: str) -> bool:
    """
    Check of een URL van een juridische bron komt.

    Args:
        url: URL om te checken

    Returns:
        True als URL van juridische bron, anders False
    """
    if not url:
        return False

    url_lower = url.lower()

    for domein in JURIDISCHE_DOMEINEN:
        if domein in url_lower:
            return True

    return False


def count_juridische_keywords(text: str) -> int:
    """
    Tel aantal juridische keywords in tekst.

    Args:
        text: Tekst om te analyseren

    Returns:
        Aantal unieke juridische keywords gevonden
    """
    if not text:
        return 0

    text_lower = text.lower()
    count = 0

    for keyword in JURIDISCHE_KEYWORDS:
        # Word boundary matching om false positives te vermijden
        # "recht" moet match in "strafrecht" maar niet in "achtrecht"
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(pattern, text_lower):
            count += 1

    return count


def contains_artikel_referentie(text: str) -> bool:
    """
    Check of tekst artikel-referenties bevat (Art. X).

    Args:
        text: Tekst om te checken

    Returns:
        True als artikel-referentie gevonden
    """
    if not text:
        return False

    return ARTIKEL_PATTERN.search(text) is not None


def contains_lid_referentie(text: str) -> bool:
    """
    Check of tekst lid-referenties bevat.

    Args:
        text: Tekst om te checken

    Returns:
        True als lid-referentie gevonden
    """
    if not text:
        return False

    return LID_PATTERN.search(text) is not None


def calculate_juridische_boost(
    result: "LookupResult", context: list[str] | None = None
) -> float:
    """
    Bereken juridische boost factor voor een result.

    Boost factoren:
    - Juridische bron (rechtspraak.nl, overheid.nl): 1.2x
    - Juridische keywords in definitie: 1.1x per keyword (max 1.3x)
    - Artikel-referentie in definitie: 1.15x
    - Lid-referentie: 1.05x
    - Context match (optioneel): 1.1x

    Args:
        result: LookupResult om te boosten
        context: Optionele context tokens (bijv. ["Sv", "strafrecht"])

    Returns:
        Boost factor (> 1.0 voor juridische content, 1.0 voor neutrale content)
    """
    boost = 1.0

    # 1. Juridische bron boost
    if hasattr(result, "source") and hasattr(result.source, "url"):
        if is_juridische_bron(result.source.url):
            boost *= 1.2
            logger.debug(f"Juridische bron boost 1.2x: {result.source.url}")

    # Alternative: check source.is_juridical flag
    if hasattr(result, "source") and getattr(result.source, "is_juridical", False):
        if boost == 1.0:  # Alleen als niet al geboosted via URL
            boost *= 1.15
            logger.debug("Juridische bron flag boost 1.15x")

    # 2. Juridische keywords in definitie
    definitie = getattr(result, "definition", "") or ""
    keyword_count = count_juridische_keywords(definitie)

    if keyword_count > 0:
        # Cap bij 1.3x (max 3 keywords = 1.1^3 ≈ 1.33)
        keyword_boost = min(1.1**keyword_count, 1.3)
        boost *= keyword_boost
        logger.debug(f"Keyword boost {keyword_boost:.2f}x ({keyword_count} keywords)")

    # 3. Artikel-referentie boost
    if contains_artikel_referentie(definitie):
        boost *= 1.15
        logger.debug("Artikel-referentie boost 1.15x")

    # 4. Lid-referentie boost
    if contains_lid_referentie(definitie):
        boost *= 1.05
        logger.debug("Lid-referentie boost 1.05x")

    # 5. Context match boost (optioneel)
    if context:
        context_lower = [c.lower() for c in context]
        definitie_lower = definitie.lower()

        # Check of context tokens voorkomen in definitie
        matches = sum(1 for c in context_lower if c in definitie_lower)

        if matches > 0:
            # 1.1x per context match (max 1.3x voor 3+ matches)
            context_boost = min(1.1**matches, 1.3)
            boost *= context_boost
            logger.debug(
                f"Context match boost {context_boost:.2f}x ({matches} matches)"
            )

    return boost


def boost_juridische_resultaten(
    results: list["LookupResult"], context: list[str] | None = None
) -> list["LookupResult"]:
    """
    Boost confidence van juridische resultaten.

    Past calculate_juridische_boost() toe op elk result en update
    confidence score. Resultaten worden opnieuw gesorteerd op confidence.

    Args:
        results: Lijst van LookupResult objecten
        context: Optionele context tokens voor extra boosting

    Returns:
        Gesorteerde lijst van LookupResult (hoogste confidence eerst)

    Example:
        >>> results = await wikipedia_lookup("voorlopige hechtenis")
        >>> boosted = boost_juridische_resultaten(results, context=["Sv"])
        >>> # Juridische resultaten krijgen hogere confidence
    """
    if not results:
        return results

    logger.info(f"Boosting {len(results)} resultaten met juridische ranking")

    boosted_results = []

    for result in results:
        # Bereken boost factor
        boost_factor = calculate_juridische_boost(result, context)

        # Update confidence (met clipping naar [0.0, 1.0])
        original_confidence = getattr(result.source, "confidence", 0.5)
        new_confidence = min(original_confidence * boost_factor, 1.0)

        # Update result confidence
        if hasattr(result, "source"):
            result.source.confidence = new_confidence

            logger.debug(
                f"Boosted '{result.term}' from {original_confidence:.2f} to {new_confidence:.2f} "
                f"(boost: {boost_factor:.2f}x)"
            )

        boosted_results.append(result)

    # Sorteer op nieuwe confidence (hoogste eerst)
    # Null-safe: handle cases waar result.source None is
    boosted_results.sort(
        key=lambda r: getattr(r.source, "confidence", 0.0) if r.source else 0.0,
        reverse=True,
    )

    logger.info(
        f"Juridische ranking compleet: "
        f"top result confidence {boosted_results[0].source.confidence:.2f}"
    )

    return boosted_results


def get_juridische_score(result: "LookupResult") -> float:
    """
    Bereken hoe 'juridisch' een result is (0.0 - 1.0).

    Gebruikt dezelfde factoren als boost_juridische_resultaten maar
    returnt een absolute score i.p.v. een multiplier.

    Args:
        result: LookupResult om te scoren

    Returns:
        Score tussen 0.0 (niet juridisch) en 1.0 (zeer juridisch)
    """
    score = 0.0

    # Juridische bron: +0.4
    if hasattr(result, "source"):
        if hasattr(result.source, "url") and is_juridische_bron(result.source.url):
            score += 0.4
        elif getattr(result.source, "is_juridical", False):
            score += 0.3

    # Juridische keywords: +0.05 per keyword (max +0.3)
    definitie = getattr(result, "definition", "") or ""
    keyword_count = count_juridische_keywords(definitie)
    score += min(keyword_count * 0.05, 0.3)

    # Artikel-referentie: +0.2
    if contains_artikel_referentie(definitie):
        score += 0.2

    # Lid-referentie: +0.1
    if contains_lid_referentie(definitie):
        score += 0.1

    # Clamp naar [0.0, 1.0]
    return min(score, 1.0)
