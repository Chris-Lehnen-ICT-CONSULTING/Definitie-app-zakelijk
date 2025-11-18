"""Centrale mapping van aanvullende (legacy) regexpatronen per toetsregel.

Voorkomt duplicatie tussen de legacy validator en de V2-validator.
Gebruik `get_additional_patterns(code)` om patronen voor een regelcode op te halen.
"""

from __future__ import annotations

_ADDITIONAL_PATTERNS: dict[str, list[str]] = {
    # ARAI - taal/algemene formulering
    "ARAI-01": [
        r"\bbetekent\b",  # vaak gebruikte verbale kern in foutieve definities
    ],
    "ARAI-02": [
        # Aanvullende containerbegrippen (mild, om vals-positieven te beperken)
        r"\bcomponent\b(?!\s+dat|\s+van)",
        r"\bonderdeel\b(?!\s+dat|\s+van)",
    ],
    "ARAI-03": [
        # Enkele subjectieve bijvoeglijke naamwoorden aanvullend op JSON
        r"\bdoeltreffend\b",
        r"\bvoldoende\b",
    ],
    "CON-01": [
        r"\b(in de context van|binnen de context|juridische context)\b",
        r"\b(DJI|OM|KMAR|Openbaar Ministerie)\b",
        r"\bvolgens het Wetboek van\b",
        r"\bin het strafrecht\b",
        r"\bin de strafrechtelijke context\b",
    ],
    "ESS-01": [
        r"\b(om te|met als doel|bedoeld om|teneinde|zodat)\b",
        r"\b(gericht op|ten behoeve van)\b",
    ],
    "INT-01": [
        r"\.\s+[A-Z]",  # Meerdere zinnen
        r";\s*[a-z]",  # Semicolon gevolgd door kleine letter (mogelijk nieuwe zin)
    ],
    "INT-03": [
        r"\b(deze|dit|die|daarvan)\b(?!\s+(begrip|definitie|regel))",  # Onduidelijke verwijzingen
    ],
    "STR-01": [
        r"^(is|de|het|een|wordt|betreft)\b",  # Start niet met artikel/hulpwerkwoord
    ],
    "STR-02": [
        r"\b(proces|activiteit|handeling|zaak|ding)\b(?!\s+\w+)",  # Vage termen zonder specificatie
    ],
    # SAM - samenhang/kwalificaties
    "SAM-01": [
        r"\binstitutioneel\b",
        r"\bfunctioneel\b",
    ],
}


def get_additional_patterns(code: str) -> list[str]:
    """Geef aanvullende patronen voor een toetsregelcode.

    Args:
        code: Regelcode, case-insensitive (bijv. "CON-01").

    Returns:
        Lijst van regex strings (kan leeg zijn).
    """
    return list(_ADDITIONAL_PATTERNS.get(str(code).upper(), []))
