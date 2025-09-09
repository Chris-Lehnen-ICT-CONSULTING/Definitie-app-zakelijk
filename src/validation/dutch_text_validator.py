"""
Dutch text validation system for DefinitieAgent.
Provides specialized validation for Dutch language content, government terminology, and legal definitions.
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime

UTC = UTC  # Python 3.10 compatibility
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DutchTextType(Enum):
    """Types of Dutch text content."""

    GENERAL = "general"
    LEGAL = "legal"
    GOVERNMENT = "government"
    DEFINITION = "definition"
    FORMAL = "formal"
    TECHNICAL = "technical"


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class DutchValidationRule:
    """Rule for Dutch text validation."""

    name: str
    pattern: str
    description: str
    severity: ValidationSeverity
    text_types: list[DutchTextType]
    suggestion: str | None = None
    replacement: str | None = None


@dataclass
class DutchValidationResult:
    """Result of Dutch text validation."""

    text: str
    text_type: DutchTextType
    passed: bool
    issues: list[dict[str, Any]]
    suggestions: list[str]
    corrected_text: str | None = None
    statistics: dict[str, Any] = None


class DutchTextValidator:
    """Main Dutch text validation system."""

    def __init__(self):
        self.validation_rules: dict[DutchTextType, list[DutchValidationRule]] = {}
        self.dutch_dictionary: set[str] = set()
        self.government_terms: set[str] = set()
        self.legal_terms: set[str] = set()
        self.validation_history: list[dict[str, Any]] = []

        self.load_validation_rules()
        self.load_dutch_dictionaries()

    def load_validation_rules(self):
        """Load Dutch text validation rules."""

        # General Dutch text rules
        general_rules = [
            DutchValidationRule(
                name="dutch_characters",
                pattern=r"[^a-zA-Z0-9\s\-\.,;:!?()\[\]{}\"\"''`~@#$%^&*+=|\\/<>àáâãäåæçèéêëìíîïñòóôõöøùúûüýÿ]",
                description="Contains non-Dutch characters",
                severity=ValidationSeverity.WARNING,
                text_types=[
                    DutchTextType.GENERAL,
                    DutchTextType.LEGAL,
                    DutchTextType.GOVERNMENT,
                ],
                suggestion="Use only Dutch characters and standard punctuation",
            ),
            DutchValidationRule(
                name="excessive_capitals",
                pattern=r"[A-Z]{4,}",
                description="Excessive use of capital letters",
                severity=ValidationSeverity.WARNING,
                text_types=[DutchTextType.GENERAL, DutchTextType.FORMAL],
                suggestion="Avoid excessive capitalization",
            ),
            DutchValidationRule(
                name="sentence_length",
                pattern=r"\b\w+(?:\s+\w+){49,}\b",
                description="Sentence is too long (50+ words)",
                severity=ValidationSeverity.WARNING,
                text_types=[DutchTextType.GENERAL, DutchTextType.FORMAL],
                suggestion="Consider breaking long sentences into shorter ones",
            ),
            DutchValidationRule(
                name="multiple_punctuation",
                pattern=r"[.!?]{2,}",
                description="Multiple punctuation marks",
                severity=ValidationSeverity.WARNING,
                text_types=[DutchTextType.GENERAL, DutchTextType.FORMAL],
                replacement=r".",
            ),
        ]

        # Legal text rules
        legal_rules = [
            DutchValidationRule(
                name="legal_article_format",
                pattern=r"\bartikel\s+(\d+)\b",
                description="Legal article reference format",
                severity=ValidationSeverity.INFO,
                text_types=[DutchTextType.LEGAL],
                suggestion="Use proper article formatting: 'artikel 12'",
            ),
            DutchValidationRule(
                name="legal_abbreviations",
                pattern=r"\b(art|lid|sub|jr|sr|wet|wvs|wvsr|bw|awb|gw)\b",
                description="Legal abbreviations found",
                severity=ValidationSeverity.INFO,
                text_types=[DutchTextType.LEGAL],
                suggestion="Consider spelling out abbreviations for clarity",
            ),
            DutchValidationRule(
                name="legal_conjunctions",
                pattern=r"\b(en/of|of/en|dan wel|althans|subsidiair)\b",
                description="Legal conjunctions used",
                severity=ValidationSeverity.INFO,
                text_types=[DutchTextType.LEGAL],
                suggestion="Legal conjunctions detected - ensure proper usage",
            ),
        ]

        # Government text rules
        government_rules = [
            DutchValidationRule(
                name="government_institutions",
                pattern=r"\b(ministerie|kabinet|parlement|tweede kamer|eerste kamer|raad van state|rekenkamer|nationale ombudsman)\b",
                description="Government institution mentioned",
                severity=ValidationSeverity.INFO,
                text_types=[DutchTextType.GOVERNMENT],
                suggestion="Ensure correct capitalization of government institutions",
            ),
            DutchValidationRule(
                name="formal_address",
                pattern=r"\b(u|uw|uzelf)\b",
                description="Formal address used",
                severity=ValidationSeverity.INFO,
                text_types=[DutchTextType.GOVERNMENT, DutchTextType.FORMAL],
                suggestion="Formal address detected - ensure consistency",
            ),
            DutchValidationRule(
                name="government_processes",
                pattern=r"\b(besluit|verordening|regeling|wet|beleidsregel|circulaire|aanwijzing)\b",
                description="Government process or document type",
                severity=ValidationSeverity.INFO,
                text_types=[DutchTextType.GOVERNMENT],
                suggestion="Government document type detected",
            ),
        ]

        # Definition-specific rules
        definition_rules = [
            DutchValidationRule(
                name="definition_structure",
                pattern=r"^(.+?)\s+(is|betekent|wordt verstaan|houdt in|omvat)",
                description="Definition structure detected",
                severity=ValidationSeverity.INFO,
                text_types=[DutchTextType.DEFINITION],
                suggestion="Definition follows proper structure",
            ),
            DutchValidationRule(
                name="circular_definition",
                pattern=r"\b(\w+)\b.*?\b\1\b",
                description="Potential circular definition",
                severity=ValidationSeverity.WARNING,
                text_types=[DutchTextType.DEFINITION],
                suggestion="Avoid using the term being defined in its own definition",
            ),
            DutchValidationRule(
                name="vague_terms",
                pattern=r"\b(ongeveer|min of meer|enigszins|tamelijk|redelijk|vrij|nogal|behoorlijk)\b",
                description="Vague terms in definition",
                severity=ValidationSeverity.WARNING,
                text_types=[DutchTextType.DEFINITION],
                suggestion="Use precise terms in definitions",
            ),
        ]

        # Technical text rules
        technical_rules = [
            DutchValidationRule(
                name="technical_abbreviations",
                pattern=r"\b[A-Z]{2,}\b",
                description="Technical abbreviations detected",
                severity=ValidationSeverity.INFO,
                text_types=[DutchTextType.TECHNICAL],
                suggestion="Define technical abbreviations on first use",
            ),
            DutchValidationRule(
                name="anglicisms",
                pattern=r"\b(performance|compliance|governance|framework|workflow|update|upgrade|download|upload|login|logout)\b",
                description="English terms (anglicisms) detected",
                severity=ValidationSeverity.WARNING,
                text_types=[DutchTextType.TECHNICAL, DutchTextType.GOVERNMENT],
                suggestion="Consider using Dutch equivalents for English terms",
            ),
        ]

        # Store rules by text type
        self.validation_rules[DutchTextType.GENERAL] = general_rules
        self.validation_rules[DutchTextType.LEGAL] = legal_rules + general_rules
        self.validation_rules[DutchTextType.GOVERNMENT] = (
            government_rules + general_rules
        )
        self.validation_rules[DutchTextType.DEFINITION] = (
            definition_rules + general_rules
        )
        self.validation_rules[DutchTextType.FORMAL] = government_rules + general_rules
        self.validation_rules[DutchTextType.TECHNICAL] = technical_rules + general_rules

    def load_dutch_dictionaries(self):
        """Load Dutch dictionaries and terminology."""

        # Basic Dutch words (sample)
        basic_words = {
            "identiteit",
            "authenticatie",
            "autorisatie",
            "verificatie",
            "validatie",
            "proces",
            "procedure",
            "behandeling",
            "verwerking",
            "controle",
            "veiligheid",
            "beveiliging",
            "bescherming",
            "toegang",
            "rechten",
            "gegevens",
            "informatie",
            "persoon",
            "burger",
            "gebruiker",
            "systeem",
            "applicatie",
            "platform",
            "service",
            "dienst",
            "overheid",
            "organisatie",
            "instantie",
            "autoriteit",
            "beheer",
            "wetgeving",
            "regeling",
            "voorschrift",
            "richtlijn",
            "norm",
        }
        self.dutch_dictionary.update(basic_words)

        # Government terminology
        government_terms = {
            "burgerservicenummer",
            "bsn",
            "identiteitsbewijs",
            "paspoort",
            "rijbewijs",
            "digid",
            "mijnoverheid",
            "basisregistratie",
            "brp",
            "gbav",
            "elektronische",
            "digitale",
            "handtekening",
            "certificaat",
            "pki",
            "eidas",
            "eulogin",
            "saml",
            "oauth",
            "openid",
            "gemeentelijke",
            "provinciale",
            "nationale",
            "europese",
            "internationale",
            "ministerie",
            "rijksoverheid",
            "gemeente",
            "provincie",
            "waterschap",
            "rechtspraak",
            "openbaar",
            "politie",
            "belastingdienst",
        }
        self.government_terms.update(government_terms)

        # Legal terminology
        legal_terms = {
            "wetboek",
            "strafrecht",
            "burgerlijk",
            "bestuursrecht",
            "grondwet",
            "wet",
            "algemene",
            "verordening",
            "regeling",
            "besluit",
            "jurisprudentie",
            "rechtspraak",
            "cassatie",
            "hoger",
            "beroep",
            "artikel",
            "lid",
            "onder",
            "aanhef",
            "slot",
            "rechtspersoon",
            "natuurlijk",
            "persoon",
            "rechtsbetrekking",
            "rechtsgevolg",
            "aansprakelijkheid",
            "verplichting",
            "bevoegdheid",
            "rechtsgrond",
            "rechtsmiddel",
        }
        self.legal_terms.update(legal_terms)

    def validate_text(
        self, text: str, text_type: DutchTextType = DutchTextType.GENERAL
    ) -> DutchValidationResult:
        """Validate Dutch text for language-specific issues."""

        issues = []
        suggestions = []
        corrected_text = text

        # Record validation attempt
        validation_record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "text_type": text_type.value,
            "text_length": len(text),
            "issues_found": 0,
        }

        try:
            # Apply validation rules for text type
            if text_type in self.validation_rules:
                for rule in self.validation_rules[text_type]:
                    matches = list(re.finditer(rule.pattern, text, re.IGNORECASE))

                    for match in matches:
                        issue = {
                            "rule_name": rule.name,
                            "description": rule.description,
                            "severity": rule.severity.value,
                            "position": match.span(),
                            "matched_text": match.group(),
                            "suggestion": rule.suggestion,
                        }
                        issues.append(issue)

                        if rule.suggestion:
                            suggestions.append(rule.suggestion)

                        # Apply automatic corrections if available
                        if rule.replacement:
                            corrected_text = re.sub(
                                rule.pattern,
                                rule.replacement,
                                corrected_text,
                                flags=re.IGNORECASE,
                            )

            # Check for spelling and terminology
            spelling_issues = self._check_spelling(text, text_type)
            issues.extend(spelling_issues)

            # Check text statistics
            statistics = self._calculate_statistics(text)

            # Overall validation result
            critical_issues = [
                issue for issue in issues if issue["severity"] == "critical"
            ]
            error_issues = [issue for issue in issues if issue["severity"] == "error"]

            passed = len(critical_issues) == 0 and len(error_issues) == 0

            validation_record["issues_found"] = len(issues)
            validation_record["passed"] = passed

            return DutchValidationResult(
                text=text,
                text_type=text_type,
                passed=passed,
                issues=issues,
                suggestions=list(set(suggestions)),  # Remove duplicates
                corrected_text=corrected_text if corrected_text != text else None,
                statistics=statistics,
            )

        except Exception as e:
            logger.error(f"Dutch text validation error: {e}")

            validation_record["error"] = str(e)
            validation_record["passed"] = False

            return DutchValidationResult(
                text=text,
                text_type=text_type,
                passed=False,
                issues=[
                    {
                        "rule_name": "validation_error",
                        "description": f"Validation error: {e!s}",
                        "severity": "critical",
                        "position": (0, 0),
                        "matched_text": "",
                        "suggestion": "Check text format and try again",
                    }
                ],
                suggestions=["Check text format and try again"],
                statistics={},
            )

        finally:
            # Store validation history
            self.validation_history.append(validation_record)
            if len(self.validation_history) > 1000:
                self.validation_history.pop(0)

    def _check_spelling(
        self, text: str, text_type: DutchTextType
    ) -> list[dict[str, Any]]:
        """Check spelling and terminology usage."""
        issues = []

        # Split text into words
        words = re.findall(r"\b\w+\b", text.lower())

        # Check against relevant dictionaries
        for word in words:
            if len(word) > 3:  # Skip short words
                # Check if word is in appropriate dictionary
                if text_type == DutchTextType.GOVERNMENT:
                    if (
                        word not in self.dutch_dictionary
                        and word not in self.government_terms
                    ):
                        issues.append(
                            {
                                "rule_name": "unknown_government_term",
                                "description": f"Unknown government term: {word}",
                                "severity": "info",
                                "position": (0, 0),
                                "matched_text": word,
                                "suggestion": "Verify government terminology usage",
                            }
                        )

                elif text_type == DutchTextType.LEGAL and (
                    word not in self.dutch_dictionary and word not in self.legal_terms
                ):
                    issues.append(
                        {
                            "rule_name": "unknown_legal_term",
                            "description": f"Unknown legal term: {word}",
                            "severity": "info",
                            "position": (0, 0),
                            "matched_text": word,
                            "suggestion": "Verify legal terminology usage",
                        }
                    )

        return issues

    def _calculate_statistics(self, text: str) -> dict[str, Any]:
        """Calculate text statistics."""
        sentences = re.split(r"[.!?]+", text)
        words = re.findall(r"\b\w+\b", text)

        return {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "avg_word_length": (
                sum(len(word) for word in words) / len(words) if words else 0
            ),
            "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
            "readability_score": self._calculate_readability(text),
        }

    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (simplified Dutch readability index)."""
        sentences = re.split(r"[.!?]+", text)
        words = re.findall(r"\b\w+\b", text)

        if not sentences or not words:
            return 0.0

        # Simplified readability calculation
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Dutch readability formula (simplified)
        readability = 100 - (0.7 * avg_sentence_length) - (0.5 * avg_word_length)

        return max(0, min(100, readability))

    def suggest_improvements(
        self, text: str, text_type: DutchTextType = DutchTextType.GENERAL
    ) -> list[str]:
        """Suggest improvements for Dutch text."""
        result = self.validate_text(text, text_type)

        improvements = []

        # Add specific suggestions based on text type
        if text_type == DutchTextType.DEFINITION:
            improvements.extend(
                [
                    "Ensure the definition is clear and unambiguous",
                    "Use present tense for definitions",
                    "Avoid circular definitions",
                    "Define terms in order of dependency",
                ]
            )

        elif text_type == DutchTextType.LEGAL:
            improvements.extend(
                [
                    "Use precise legal terminology",
                    "Reference relevant legal articles",
                    "Ensure consistency with existing legal framework",
                    "Consider legal implications of wording",
                ]
            )

        elif text_type == DutchTextType.GOVERNMENT:
            improvements.extend(
                [
                    "Use formal, professional language",
                    "Ensure accessibility for citizens",
                    "Follow government style guidelines",
                    "Use consistent terminology",
                ]
            )

        # Add suggestions from validation results
        improvements.extend(result.suggestions)

        return list(set(improvements))  # Remove duplicates

    def get_validation_statistics(self) -> dict[str, Any]:
        """Get validation statistics."""
        if not self.validation_history:
            return {"total_validations": 0}

        total_validations = len(self.validation_history)
        passed_validations = sum(
            1 for v in self.validation_history if v.get("passed", False)
        )

        # Text type usage
        text_type_usage = {}
        for validation in self.validation_history:
            text_type = validation.get("text_type", "unknown")
            text_type_usage[text_type] = text_type_usage.get(text_type, 0) + 1

        # Issue statistics
        total_issues = sum(v.get("issues_found", 0) for v in self.validation_history)
        avg_issues_per_validation = (
            total_issues / total_validations if total_validations > 0 else 0
        )

        return {
            "total_validations": total_validations,
            "passed_validations": passed_validations,
            "success_rate": (
                passed_validations / total_validations if total_validations > 0 else 0
            ),
            "total_issues": total_issues,
            "avg_issues_per_validation": avg_issues_per_validation,
            "text_type_usage": text_type_usage,
            "dictionary_size": len(self.dutch_dictionary),
            "government_terms_size": len(self.government_terms),
            "legal_terms_size": len(self.legal_terms),
        }

    def export_validation_report(self, filename: str | None = None) -> str:
        """Export validation report to file."""
        if filename is None:
            filename = f"dutch_validation_report_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"

        filepath = Path("reports") / filename
        filepath.parent.mkdir(exist_ok=True)

        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "statistics": self.get_validation_statistics(),
            "validation_rules": {
                text_type.value: len(rules)
                for text_type, rules in self.validation_rules.items()
            },
            "recent_validations": (
                self.validation_history[-100:]
                if len(self.validation_history) > 100
                else self.validation_history
            ),
        }

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return str(filepath)


# Global Dutch text validator instance
_dutch_validator: DutchTextValidator | None = None


def get_dutch_validator() -> DutchTextValidator:
    """Get or create global Dutch text validator instance."""
    global _dutch_validator
    if _dutch_validator is None:
        _dutch_validator = DutchTextValidator()
    return _dutch_validator


def validate_dutch_text(
    text: str, text_type: DutchTextType = DutchTextType.GENERAL
) -> DutchValidationResult:
    """Convenience function for Dutch text validation."""
    validator = get_dutch_validator()
    return validator.validate_text(text, text_type)


def suggest_dutch_improvements(
    text: str, text_type: DutchTextType = DutchTextType.GENERAL
) -> list[str]:
    """Convenience function for Dutch text improvement suggestions."""
    validator = get_dutch_validator()
    return validator.suggest_improvements(text, text_type)


def dutch_text_decorator(text_type: DutchTextType = DutchTextType.GENERAL):
    """Decorator to validate Dutch text in function arguments."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Validate text arguments
            for _i, arg in enumerate(args):
                if (
                    isinstance(arg, str) and len(arg) > 10
                ):  # Only validate substantial text
                    result = validate_dutch_text(arg, text_type)
                    if not result.passed:
                        error_messages = [
                            issue["description"]
                            for issue in result.issues
                            if issue["severity"] in ["error", "critical"]
                        ]
                        if error_messages:
                            msg = f"Dutch text validation failed: {'; '.join(error_messages)}"
                            raise ValueError(msg)

            return func(*args, **kwargs)

        return wrapper

    return decorator


async def test_dutch_validator():
    """Test the Dutch text validation system."""
    print("🇳🇱 Testing Dutch Text Validator")
    print("=" * 35)

    validator = get_dutch_validator()

    # Test general Dutch text
    dutch_text = (
        "Dit is een Nederlandse tekst voor identiteitsbehandeling binnen de overheid."
    )
    result = validator.validate_text(dutch_text, DutchTextType.GENERAL)
    print(f"✅ General Dutch text: {'PASSED' if result.passed else 'FAILED'}")
    print(f"   Issues found: {len(result.issues)}")

    # Test legal text
    legal_text = "Artikel 12 van de Wet op de identificatieplicht bepaalt dat elke burger een geldig identiteitsbewijs moet kunnen tonen."
    result = validator.validate_text(legal_text, DutchTextType.LEGAL)
    print(f"✅ Legal text: {'PASSED' if result.passed else 'FAILED'}")
    print(f"   Issues found: {len(result.issues)}")

    # Test government text
    government_text = "Het Ministerie van Binnenlandse Zaken en Koninkrijksrelaties is verantwoordelijk voor de uitgifte van Nederlandse identiteitsbewijzen."
    result = validator.validate_text(government_text, DutchTextType.GOVERNMENT)
    print(f"✅ Government text: {'PASSED' if result.passed else 'FAILED'}")
    print(f"   Issues found: {len(result.issues)}")

    # Test definition text
    definition_text = "Identiteitsbehandeling is het proces waarbij de identiteit van een persoon wordt vastgesteld, geverifieerd en gevalideerd."
    result = validator.validate_text(definition_text, DutchTextType.DEFINITION)
    print(f"✅ Definition text: {'PASSED' if result.passed else 'FAILED'}")
    print(f"   Issues found: {len(result.issues)}")

    # Test problematic text
    problematic_text = "Dit is een ZEER LANGE ZIN met veel hoofdletters die veel te lang is en eigenlijk opgedeeld zou moeten worden in kortere zinnen omdat het anders moeilijk te lezen is en niet voldoet aan de richtlijnen voor goed Nederlands!"
    result = validator.validate_text(problematic_text, DutchTextType.FORMAL)
    print(f"❌ Problematic text: {'PASSED' if result.passed else 'FAILED'}")
    print(f"   Issues found: {len(result.issues)}")

    # Show statistics
    stats = validator.get_validation_statistics()
    print("\n📊 Validation Statistics:")
    print(f"   Total validations: {stats['total_validations']}")
    print(f"   Success rate: {stats['success_rate']:.1%}")
    print(f"   Average issues per validation: {stats['avg_issues_per_validation']:.1f}")
    print(f"   Dictionary size: {stats['dictionary_size']} words")

    # Test suggestions
    suggestions = validator.suggest_improvements(
        definition_text, DutchTextType.DEFINITION
    )
    print(f"\n💡 Improvement suggestions ({len(suggestions)}):")
    for suggestion in suggestions[:3]:  # Show first 3
        print(f"   • {suggestion}")

    # Test readability
    complex_text = "De implementatie van een geïntegreerd identiteitsmanagementsysteem vereist een uitgebreide evaluatie van de bestaande infrastructuur en de ontwikkeling van nieuwe beveiligingsprotocollen."
    result = validator.validate_text(complex_text, DutchTextType.TECHNICAL)
    if result.statistics:
        print("\n📈 Text Statistics:")
        print(
            f"   Readability score: {result.statistics.get('readability_score', 0):.1f}/100"
        )
        print(
            f"   Average word length: {result.statistics.get('avg_word_length', 0):.1f}"
        )
        print(
            f"   Average sentence length: {result.statistics.get('avg_sentence_length', 0):.1f} words"
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_dutch_validator())
