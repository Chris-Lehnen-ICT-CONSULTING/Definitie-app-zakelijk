"""
ASTRA Compliance Validator with Warning-Based Approach.

This validator checks context against ASTRA standards but never fails hard.
It provides helpful warnings and suggestions to improve compliance.
"""

import logging
import re
from dataclasses import dataclass, field
from difflib import get_close_matches
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of ASTRA validation with warnings and suggestions."""

    is_valid: bool = True  # Always True - we never block
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    compliance_score: float = 1.0
    details: dict[str, Any] = field(default_factory=dict)

    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)
        # Reduce compliance score for each warning
        self.compliance_score = max(0.0, self.compliance_score - 0.1)

    def add_suggestion(self, suggestion: str):
        """Add a suggestion for improvement."""
        self.suggestions.append(suggestion)

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def has_suggestions(self) -> bool:
        """Check if there are any suggestions."""
        return len(self.suggestions) > 0

    def get_summary(self) -> str:
        """Get a summary of the validation result."""
        if not self.has_warnings():
            return "Volledig ASTRA-compliant"

        warning_count = len(self.warnings)
        suggestion_count = len(self.suggestions)

        parts = []
        if warning_count > 0:
            parts.append(f"{warning_count} waarschuwing(en)")
        if suggestion_count > 0:
            parts.append(f"{suggestion_count} suggestie(s)")

        return f"Validatie compleet met {', '.join(parts)}"


class ASTRAValidator:
    """
    ASTRA compliance validator with warning-based approach.

    This validator:
    - Never fails hard or blocks operations
    - Provides helpful warnings for non-compliant entries
    - Suggests corrections using fuzzy matching
    - Generates compliance reports for audit
    """

    # Official ASTRA organization codes and names
    ASTRA_REGISTRY = {
        "OM": "Openbaar Ministerie",
        "ZM": "Zittende Magistratuur",
        "RECHTSPRAAK": "Rechtspraak",
        "3RO": "3RO - Reclassering",
        "RECLASSERING": "Reclassering Nederland",
        "DJI": "Dienst Justitiële Inrichtingen",
        "POLITIE": "Nationale Politie",
        "NP": "Nationale Politie",
        "IND": "Immigratie- en Naturalisatiedienst",
        "CJIB": "Centraal Justitieel Incassobureau",
        "JUSTID": "Dienst Justitiële Informatievoorziening",
        "NFI": "Nederlands Forensisch Instituut",
        "RVR": "Raad voor Rechtsbijstand",
        "RVDK": "Raad voor de Kinderbescherming",
        "FIOD": "Fiscale Inlichtingen- en Opsporingsdienst",
        "KMAR": "Koninklijke Marechaussee",
    }

    # Common legal reference patterns
    LEGAL_PATTERNS = [
        r"^Artikel\s+\d+[a-z]?\s+\w+",  # Artikel 3 Awb
        r"^Art\.\s+\d+[a-z]?\s+\w+",  # Art. 3 Awb
        r"^\d+[a-z]?\s+\w+",  # 3 Awb (short form)
        r"^[A-Z][a-z]+\s+\d+",  # Hoofdstuk 3, Afdeling 2
    ]

    # Known legal domains
    LEGAL_DOMAINS = [
        "Strafrecht",
        "Bestuursrecht",
        "Civiel recht",
        "Jeugdrecht",
        "Vreemdelingenrecht",
        "Sanctierecht",
        "Penitentiair recht",
        "Familierecht",
        "Arbeidsrecht",
    ]

    def __init__(self):
        """Initialize the validator."""
        self.validation_cache = {}
        logger.info("ASTRA Validator initialized with warning-based approach")

    def validate_with_warnings(self, context: dict[str, list[str]]) -> ValidationResult:
        """
        Validate context against ASTRA standards.

        Returns warnings and suggestions, never hard errors.

        Args:
            context: Dictionary with context fields

        Returns:
            ValidationResult with warnings and suggestions
        """
        result = ValidationResult()

        # Validate organizational context
        if "organisatorisch" in context:
            self._validate_organizations(context["organisatorisch"], result)

        # Validate legal references
        if "wettelijk" in context:
            self._validate_legal_references(context["wettelijk"], result)

        # Validate legal domains
        if "juridisch" in context:
            self._validate_legal_domains(context["juridisch"], result)

        # Add general suggestions if no context provided
        if not any(context.values()):
            result.add_suggestion(
                "Overweeg context toe te voegen voor meer specifieke definities"
            )

        # Calculate final compliance score
        result.details["total_items"] = sum(len(v) for v in context.values())
        result.details["warnings_ratio"] = len(result.warnings) / max(
            result.details["total_items"], 1
        )

        logger.info(
            f"ASTRA validation complete: {result.get_summary()}, "
            f"compliance score: {result.compliance_score:.2f}"
        )

        return result

    def _validate_organizations(
        self, organizations: list[str], result: ValidationResult
    ):
        """Validate organizational context entries."""
        for org in organizations:
            if not self._is_valid_astra_org(org):
                # Find suggestions
                suggestions = self._suggest_similar_org(org)

                if suggestions:
                    result.add_warning(
                        f"'{org}' is niet herkend als ASTRA-organisatie. "
                        f"Bedoelde u: {', '.join(suggestions[:3])}?"
                    )
                else:
                    result.add_warning(
                        f"'{org}' is niet herkend als ASTRA-organisatie. "
                        f"Controleer de spelling of gebruik een standaard organisatienaam."
                    )

    def _validate_legal_references(
        self, references: list[str], result: ValidationResult
    ):
        """Validate legal reference format."""
        for ref in references:
            if not self._is_valid_legal_format(ref):
                result.add_warning(
                    f"'{ref}' volgt niet het standaard juridische formaat. "
                    f"Gebruik bijvoorbeeld: 'Artikel 3:4 Awb' of 'Art. 141 Sr'"
                )

                # Suggest correction if possible
                corrected = self._suggest_legal_format(ref)
                if corrected and corrected != ref:
                    result.add_suggestion(
                        f"Overweeg: '{corrected}' in plaats van '{ref}'"
                    )

    def _validate_legal_domains(self, domains: list[str], result: ValidationResult):
        """Validate legal domain entries."""
        for domain in domains:
            if not self._is_known_legal_domain(domain):
                suggestions = get_close_matches(
                    domain, self.LEGAL_DOMAINS, n=2, cutoff=0.6
                )

                if suggestions:
                    result.add_suggestion(
                        f"'{domain}' is onbekend. Bedoelde u: {suggestions[0]}?"
                    )

    def _is_valid_astra_org(self, org: str) -> bool:
        """Check if organization is in ASTRA registry."""
        org_upper = org.upper()
        org_normalized = org.lower().strip()

        # Check exact matches
        if org_upper in self.ASTRA_REGISTRY:
            return True

        # Check against values
        for value in self.ASTRA_REGISTRY.values():
            if value.lower() == org_normalized:
                return True

        return False

    def _suggest_similar_org(self, org: str) -> list[str]:
        """Suggest similar ASTRA organizations."""
        all_orgs = list(self.ASTRA_REGISTRY.values())

        # Try fuzzy matching
        suggestions = get_close_matches(org, all_orgs, n=3, cutoff=0.6)

        return suggestions

    def _is_valid_legal_format(self, ref: str) -> bool:
        """Check if legal reference follows standard format."""
        for pattern in self.LEGAL_PATTERNS:
            if re.match(pattern, ref, re.IGNORECASE):
                return True
        return False

    def _suggest_legal_format(self, ref: str) -> str:
        """Try to correct legal reference format."""
        # Simple corrections
        ref = ref.strip()

        # If it starts with a number, assume it's an article
        if ref[0].isdigit():
            # Try to identify the law
            parts = ref.split()
            if len(parts) >= 2:
                return f"Artikel {parts[0]} {' '.join(parts[1:])}"

        # If it contains "artikel" but wrong case
        if "artikel" in ref.lower():
            ref = re.sub(r"\bartikel\b", "Artikel", ref, flags=re.IGNORECASE)

        # If it contains "art" abbreviation
        if "art" in ref.lower():
            ref = re.sub(r"\bart\.?\b", "Art.", ref, flags=re.IGNORECASE)

        return ref

    def _is_known_legal_domain(self, domain: str) -> bool:
        """Check if legal domain is recognized."""
        domain_normalized = domain.lower().strip()

        for known_domain in self.LEGAL_DOMAINS:
            if known_domain.lower() == domain_normalized:
                return True

        return False

    def generate_compliance_report(
        self, validation_result: ValidationResult
    ) -> dict[str, Any]:
        """
        Generate detailed compliance report for audit.

        Args:
            validation_result: Result from validation

        Returns:
            Dictionary with compliance metrics
        """
        report = {
            "timestamp": None,  # Would add datetime.now()
            "compliance_score": validation_result.compliance_score,
            "total_warnings": len(validation_result.warnings),
            "total_suggestions": len(validation_result.suggestions),
            "details": validation_result.details,
            "warnings": validation_result.warnings,
            "suggestions": validation_result.suggestions,
            "summary": validation_result.get_summary(),
        }

        # Calculate compliance percentage
        if validation_result.details.get("total_items", 0) > 0:
            report["compliance_percentage"] = (
                1 - validation_result.details["warnings_ratio"]
            ) * 100
        else:
            report["compliance_percentage"] = 100.0

        return report
