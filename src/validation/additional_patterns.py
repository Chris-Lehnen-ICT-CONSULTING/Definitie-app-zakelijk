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
    # CON-01 staat hier bewust niet meer (DEF-622, B-04): een vaste lijst
    # meta-frasen en organisatienamen is geen goedgekeurde afkeurgrond. De
    # regel leest de werkelijk geselecteerde contextwaarden via
    # `domain.context.contract`.
    "ESS-01": [
        r"\b(om te|met als doel|bedoeld om|teneinde|zodat)\b",
        r"\b(gericht op|ten behoeve van)\b",
    ],
    # INT-01 staat hier bewust niet meer (DEF-770): een punt plus hoofdletter
    # keurde 'dr. Smit' af en miste een vraagzin, en een puntkomma is geen
    # zelfstandige zinsgrens (K4). De regel stelt zinsgrenzen functioneel vast
    # in `services.validation.evaluators.sentence_boundary`.
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


def all_additional_patterns() -> dict[str, list[str]]:
    """Geef de volledige mapping, per regelcode.

    Deze patronen staan in Python en niet in de JSON-records, dus
    `build_rule_record` ziet ze nooit. Ze hebben daarom hun eigen
    compileerbaarheidsguard nodig (DEF-667); zonder een publieke leesweg zou
    die test op de private mapping moeten grijpen.
    """
    return {code: list(patronen) for code, patronen in _ADDITIONAL_PATTERNS.items()}


def get_additional_patterns(code: str) -> list[str]:
    """Geef aanvullende patronen voor een toetsregelcode.

    Args:
        code: Regelcode, case-insensitive (bijv. "CON-01").

    Returns:
        Lijst van regex strings (kan leeg zijn).
    """
    return list(_ADDITIONAL_PATTERNS.get(str(code).upper(), []))
