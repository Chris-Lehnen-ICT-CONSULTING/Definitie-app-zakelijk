"""Centrale mapping van aanvullende (legacy) regexpatronen per toetsregel.

Voorkomt duplicatie tussen de legacy validator en de V2‑validator.
Gebruik `get_additional_patterns(code)` om patronen voor een regelcode op te halen.
"""

from __future__ import annotations

from typing import List

_ADDITIONAL_PATTERNS: dict[str, list[str]] = {
    "CON-01": [
        r"\b(in de context van|binnen de context|juridische context)\b",
        r"\b(DJI|OM|KMAR|Openbaar Ministerie)\b",
        r"\bvolgens het Wetboek van\b",
    ],
    "ESS-01": [
        r"\b(om te|met als doel|bedoeld om|teneinde|zodat)\b",
        r"\b(gericht op|ten behoeve van)\b",
    ],
    "INT-01": [
        r"\.\s+[A-Z]",  # Meerdere zinnen
        r";\s*[a-z]",    # Semicolon gevolgd door kleine letter (mogelijk nieuwe zin)
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
}


def get_additional_patterns(code: str) -> List[str]:
    """Geef aanvullende patronen voor een toetsregelcode.

    Args:
        code: Regelcode, case-insensitive (bijv. "CON-01").

    Returns:
        Lijst van regex strings (kan leeg zijn).
    """
    return list(_ADDITIONAL_PATTERNS.get(str(code).upper(), []))

