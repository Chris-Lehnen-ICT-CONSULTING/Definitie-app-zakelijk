"""ViolationBuilder - Gecentraliseerde violation constructie voor validatie.

Extracted uit ModularValidationService (Story 2.3 / DEF-remaining).
Centraliseert de logica voor:
- Violation dictionary constructie
- Category mapping
- Severity/severity_level mapping
- Suggestion generation

Design: Builder pattern met immutable output (dicts worden als frozen-like behandeld
doordat ze via to_dict() worden geretourneerd).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# Categorie prefixes voor rule_id -> category mapping
_CATEGORY_PREFIXES: dict[str, str] = {
    "STR-": "structuur",
    "CON-": "samenhang",
    "ESS-": "juridisch",
    "VAL-": "juridisch",
    "SAM-": "samenhang",
    "ARAI": "taal",
    "ARAI-": "taal",
    "AR-": "taal",
    "AR": "taal",
    "INT-": "structuur",
    "VER-": "taal",
    "LANG-": "taal",
}

# Severity mapping voor aanbeveling/prioriteit combinaties
_SEVERITY_LEVEL_MAP: dict[tuple[str, str], str] = {
    ("verplicht", "hoog"): "critical",
    ("verplicht", "midden"): "high",
    ("verplicht", "laag"): "high",
    ("aanbevolen", "hoog"): "medium",
    ("aanbevolen", "midden"): "low",
    ("aanbevolen", "laag"): "low",
}


def category_for_rule(code: str) -> str:
    """Bepaal de category voor een gegeven rule code.

    Args:
        code: De rule identifier (bijv. "STR-01", "VAL-EMP-001")

    Returns:
        Category string: "structuur", "samenhang", "juridisch", "taal", of "system"
    """
    c = str(code)
    for prefix, category in _CATEGORY_PREFIXES.items():
        if c.startswith(prefix) or c.upper().startswith(prefix):
            return category
    return "system"


def severity_level_for_rule(
    aanbeveling: str | None = None,
    prioriteit: str | None = None,
    *,
    default: str = "medium",
) -> str:
    """Bepaal severity level op basis van aanbeveling en prioriteit.

    Args:
        aanbeveling: "verplicht" of "aanbevolen"
        prioriteit: "hoog", "midden", of "laag"
        default: Fallback waarde

    Returns:
        Severity level: "critical", "high", "medium", of "low"
    """
    aan = (aanbeveling or "").lower().strip()
    pri = (prioriteit or "").lower().strip()
    return _SEVERITY_LEVEL_MAP.get((aan, pri), default)


def severity_for_level(severity_level: str) -> str:
    """Map severity_level naar severity (error/warning).

    Args:
        severity_level: "critical", "high", "medium", of "low"

    Returns:
        "error" voor critical/high, "warning" voor medium/low
    """
    return "error" if severity_level in ("critical", "high") else "warning"


@dataclass
class ViolationBuilder:
    """Builder voor het construeren van violation dictionaries.

    Maakt gestructureerde violation objects met correcte categorieën,
    severities en suggesties. Immutable na constructie via to_dict().

    Usage:
        violation = (
            ViolationBuilder("VAL-EMP-001")
            .with_message("Definitietekst is leeg")
            .with_suggestion("Vul de definitietekst in")
            .build()
        )
    """

    code: str
    _message: str = ""
    _description: str | None = None
    _suggestion: str | None = None
    _severity: str | None = None
    _severity_level: str | None = None
    _category: str | None = None
    _metadata: dict[str, Any] = field(default_factory=dict)

    # Rule metadata voor severity berekening
    _aanbeveling: str | None = None
    _prioriteit: str | None = None

    def with_message(self, message: str) -> ViolationBuilder:
        """Set de message (en description als die niet gezet is)."""
        self._message = message
        if self._description is None:
            self._description = message
        return self

    def with_description(self, description: str) -> ViolationBuilder:
        """Set een aparte description (indien anders dan message)."""
        self._description = description
        return self

    def with_suggestion(self, suggestion: str | None) -> ViolationBuilder:
        """Set de suggestion voor deze violation."""
        self._suggestion = suggestion
        return self

    def with_severity(
        self, severity: str, severity_level: str | None = None
    ) -> ViolationBuilder:
        """Set severity en optioneel severity_level expliciet."""
        self._severity = severity
        if severity_level is not None:
            self._severity_level = severity_level
        return self

    def with_rule_metadata(
        self, aanbeveling: str | None = None, prioriteit: str | None = None
    ) -> ViolationBuilder:
        """Set rule metadata voor automatische severity berekening."""
        self._aanbeveling = aanbeveling
        self._prioriteit = prioriteit
        return self

    def with_category(self, category: str) -> ViolationBuilder:
        """Override de category (normaal afgeleid van code prefix)."""
        self._category = category
        return self

    def with_metadata(self, **kwargs: Any) -> ViolationBuilder:
        """Voeg metadata toe aan de violation."""
        self._metadata.update(kwargs)
        return self

    def build(self) -> dict[str, Any]:
        """Bouw de violation dictionary.

        Returns:
            Dict met alle violation velden, klaar voor JSON serialisatie.
        """
        # Bepaal category
        category = self._category or category_for_rule(self.code)

        # Bepaal severity_level (van rule metadata of default)
        if self._severity_level is not None:
            severity_level = self._severity_level
        elif self._aanbeveling or self._prioriteit:
            severity_level = severity_level_for_rule(
                self._aanbeveling, self._prioriteit
            )
        else:
            # Default op basis van code prefix
            severity_level = (
                "high" if self.code.startswith(("VAL-", "ESS-")) else "medium"
            )

        # Bepaal severity
        severity = self._severity or severity_for_level(severity_level)

        # Bouw de dict
        result: dict[str, Any] = {
            "code": self.code,
            "severity": severity,
            "severity_level": severity_level,
            "message": self._message,
            "description": self._description or self._message,
            "rule_id": self.code,
            "category": category,
            "suggestion": self._suggestion,
        }

        # Voeg metadata toe indien aanwezig
        if self._metadata:
            result["metadata"] = dict(self._metadata)

        return result


# ============================================================
# Convenience functions voor veelvoorkomende violations
# ============================================================


def empty_definition_violation() -> dict[str, Any]:
    """Violation voor lege definitietekst (VAL-EMP-001)."""
    return (
        ViolationBuilder("VAL-EMP-001")
        .with_message("Definitietekst is leeg")
        .with_suggestion("Vul de definitietekst in; tekst mag niet leeg zijn.")
        .with_severity("error", "high")
        .build()
    )


def too_short_violation(min_words: int = 5, min_chars: int = 15) -> dict[str, Any]:
    """Violation voor te korte definitie (VAL-LEN-001)."""
    return (
        ViolationBuilder("VAL-LEN-001")
        .with_message("Definitie is te kort")
        .with_suggestion(
            f"Breid uit tot ≥ {min_words} woorden en ≥ {min_chars} tekens met kerninformatie."
        )
        .with_severity("error", "high")
        .build()
    )


def too_long_violation(max_words: int = 80, max_chars: int = 600) -> dict[str, Any]:
    """Violation voor te lange definitie (VAL-LEN-002)."""
    return (
        ViolationBuilder("VAL-LEN-002")
        .with_message("Definitie is te lang/overdadig")
        .with_suggestion(
            f"Verkort tot ≤ {max_words} woorden en ≤ {max_chars} tekens; splits indien nodig."
        )
        .with_severity("error", "low")
        .build()
    )


def essential_content_violation() -> dict[str, Any]:
    """Violation voor ontbrekende essentiële inhoud (ESS-CONT-001)."""
    return (
        ViolationBuilder("ESS-CONT-001")
        .with_message("Essentiële inhoud ontbreekt of te summier")
        .with_suggestion("Voeg essentiële inhoud toe: beschrijf wat het begrip is.")
        .with_severity("error", "high")
        .build()
    )


def circular_definition_violation(begrip: str | None = None) -> dict[str, Any]:
    """Violation voor circulaire definitie (CON-CIRC-001)."""
    begrip_str = begrip or "het begrip"
    return (
        ViolationBuilder("CON-CIRC-001")
        .with_message("Definitie is circulair (begrip komt voor in tekst)")
        .with_suggestion(
            f"Vermijd {begrip_str} letterlijk; omschrijf zonder de term te herhalen."
        )
        .with_severity("error", "high")
        .build()
    )


def informal_language_violation() -> dict[str, Any]:
    """Violation voor informele taal (LANG-INF-001)."""
    return (
        ViolationBuilder("LANG-INF-001")
        .with_message("Informele taal gedetecteerd")
        .with_suggestion(
            "Gebruik formele, precieze taal in plaats van informele bewoordingen."
        )
        .with_severity("error", "high")
        .build()
    )


def mixed_language_violation() -> dict[str, Any]:
    """Violation voor gemengde taal (LANG-MIX-001)."""
    return (
        ViolationBuilder("LANG-MIX-001")
        .with_message("Gemengde taal (NL/EN) gedetecteerd")
        .with_suggestion(
            "Kies één taal (NL) en vermijd Engelse termen in dezelfde zin."
        )
        .with_severity("error", "high")
        .build()
    )


def structure_violation() -> dict[str, Any]:
    """Violation voor ontoereikende structuur (STR-FORM-001)."""
    return (
        ViolationBuilder("STR-FORM-001")
        .with_message("Structuur ontoereikend (te summier)")
        .with_suggestion(
            "Breid de definitie uit met kernstructuur (wat het is, onderscheidend kenmerk)."
        )
        .with_severity("error", "high")
        .build()
    )


def terminology_violation(phrase: str = "HTTP protocol") -> dict[str, Any]:
    """Violation voor incorrecte terminologie (STR-TERM-001)."""
    return (
        ViolationBuilder("STR-TERM-001")
        .with_message(f"Terminologie/structuur: gebruik '{phrase.replace(' ', '-')}'")
        .with_suggestion("Gebruik correcte terminologie (bijv. 'HTTP-protocol').")
        .with_severity("warning", "low")
        .build()
    )


def organization_violation() -> dict[str, Any]:
    """Violation voor zwakke zinsstructuur (STR-ORG-001)."""
    return (
        ViolationBuilder("STR-ORG-001")
        .with_message("Zwakke zinsstructuur of redundantie gedetecteerd")
        .with_suggestion(
            "Vereenvoudig de zinsstructuur: minder komma's, kortere zinsdelen."
        )
        .with_severity("warning", "low")
        .build()
    )


# ============================================================
# JSON rule violation builder
# ============================================================


def json_rule_violation(
    code: str,
    message: str,
    rule: dict[str, Any],
    *,
    suggestion: str | None = None,
    detected_pattern: str | None = None,
    position: int | None = None,
) -> dict[str, Any]:
    """Bouw violation voor een JSON-gedefinieerde regel.

    Args:
        code: Rule identifier
        message: Violation message
        rule: JSON rule definitie (met aanbeveling/prioriteit)
        suggestion: Optionele suggestie
        detected_pattern: Optioneel gedetecteerd patroon
        position: Optionele positie van match

    Returns:
        Violation dictionary
    """
    builder = (
        ViolationBuilder(code)
        .with_message(message)
        .with_rule_metadata(
            aanbeveling=rule.get("aanbeveling"),
            prioriteit=rule.get("prioriteit"),
        )
    )

    if suggestion:
        builder.with_suggestion(suggestion)

    if detected_pattern is not None:
        builder.with_metadata(detected_pattern=detected_pattern)

    if position is not None:
        builder.with_metadata(position=position)

    return builder.build()
