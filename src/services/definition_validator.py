"""
DefinitionValidator service implementatie.

Deze service is verantwoordelijk voor het valideren van definities
volgens de Nederlandse overheid kwaliteitscriteria.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

# Legacy imports voor backward compatibility
from ai_toetser.core import toets_definitie
from config.config_loader import laad_toetsregels
from services.interfaces import (
    Definition,
    DefinitionValidatorInterface,
    ValidationResult,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidatorConfig:
    """Configuratie voor de DefinitionValidator."""

    enable_all_rules: bool = True
    enabled_rule_categories: Set[str] = field(
        default_factory=lambda: {"CON", "ESS", "INT", "SAM", "STR", "VER", "ARAI"}
    )
    min_score_threshold: float = 0.6  # Minimale score voor acceptatie
    enable_suggestions: bool = True
    enable_detailed_scoring: bool = True
    custom_rules_path: Optional[str] = None


class DefinitionValidator(DefinitionValidatorInterface):
    """
    Service voor het valideren van definities.

    Deze implementatie gebruikt de bestaande toetsregels uit de ai_toetser
    module en maakt het herbruikbaar als een focused service.
    """

    def __init__(self, config: Optional[ValidatorConfig] = None):
        """
        Initialiseer de DefinitionValidator.

        Args:
            config: Optionele configuratie, gebruikt defaults indien niet opgegeven
        """
        self.config = config or ValidatorConfig()
        self._load_rules()
        self._stats = {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "average_score": 0.0,
        }
        logger.info("DefinitionValidator geïnitialiseerd")

    def validate(self, definition: Definition) -> ValidationResult:
        """
        Valideer een definitie volgens de geldende regels.

        Args:
            definition: Te valideren definitie

        Returns:
            ValidationResult met status en eventuele fouten/waarschuwingen
        """
        if not definition.definitie:
            return self._create_empty_result("Definitie is leeg")

        self._stats["total_validations"] += 1

        # Bereid context voor legacy toetser
        contexten = self._build_context_dict(definition)

        # Voer toetsing uit via legacy module
        toets_resultaten = toets_definitie(
            definitie=definition.definitie,
            regels=self.rules,
            begrip=definition.begrip,
            contexten=contexten,
            bronnen_gebruikt=definition.bron,
            voorkeursterm=(
                definition.metadata.get("voorkeursterm")
                if definition.metadata
                else None
            ),
            gebruik_logging=False,
        )

        # Analyseer resultaten
        violations = []
        passed_rules = []
        detailed_scores = {}

        for i, (regel_id, regel_data) in enumerate(self.rules.items()):
            if i >= len(toets_resultaten):
                continue

            resultaat = toets_resultaten[i]

            # Parse resultaat
            if resultaat.startswith("✔️"):
                passed_rules.append(regel_id)
                detailed_scores[regel_id] = 1.0
            elif resultaat.startswith("❌"):
                violation = self._create_violation(regel_id, regel_data, resultaat)
                violations.append(violation)
                detailed_scores[regel_id] = 0.0
            elif resultaat.startswith("🟡"):
                # Waarschuwing - telt als halve score
                violation = self._create_violation(
                    regel_id, regel_data, resultaat, is_warning=True
                )
                violations.append(violation)
                detailed_scores[regel_id] = 0.5

        # Bereken totaalscore
        if detailed_scores:
            overall_score = sum(detailed_scores.values()) / len(detailed_scores)
        else:
            overall_score = 0.0

        # Bepaal of definitie acceptabel is
        is_acceptable = overall_score >= self.config.min_score_threshold and not any(
            v for v in violations if v.startswith("❌ ESS-")
        )  # Essentiële regels zijn verplicht

        # Genereer suggesties
        suggestions = []
        if self.config.enable_suggestions:
            suggestions = self._generate_suggestions(violations, definition)

        # Update statistieken
        if is_acceptable:
            self._stats["passed_validations"] += 1
        else:
            self._stats["failed_validations"] += 1

        # Update gemiddelde score
        total = self._stats["total_validations"]
        current_avg = self._stats["average_score"]
        self._stats["average_score"] = (
            (current_avg * (total - 1)) + overall_score
        ) / total

        # Maak resultaat
        errors = [v for v in violations if v.startswith("❌")]
        warnings = [v for v in violations if v.startswith("🟡")]

        result = ValidationResult(
            is_valid=is_acceptable,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            score=overall_score,
        )

        return result

    def validate_field(self, field_name: str, value: Any) -> ValidationResult:
        """
        Valideer een specifiek veld van een definitie.

        Args:
            field_name: Naam van het veld
            value: Waarde om te valideren

        Returns:
            ValidationResult voor het specifieke veld
        """
        # Map velden naar relevante validatie regels
        field_rules = {
            "definitie": ["ESS-01", "ESS-02", "INT-01", "STR-01"],
            "begrip": ["SAM-05", "STR-03"],
            "toelichting": ["INT-06"],
            "synoniemen": ["SAM-06", "SAM-08"],
            "voorbeelden": ["INT-04"],
            "categorie": ["ARAI01"],
        }

        if field_name not in field_rules:
            return ValidationResult(
                is_valid=True, errors=[], warnings=[], suggestions=[], score=1.0
            )

        # Maak tijdelijke definitie voor veld validatie
        temp_def = Definition()
        setattr(temp_def, field_name, value)

        # Filter relevante regels
        relevant_rules = {
            rule_id: self.rules[rule_id]
            for rule_id in field_rules[field_name]
            if rule_id in self.rules
        }

        # Voer beperkte validatie uit
        if not relevant_rules:
            return ValidationResult(is_valid=True, score=1.0)

        # Gebruik subset van regels voor validatie
        original_rules = self.rules
        self.rules = relevant_rules

        try:
            result = self.validate(temp_def)
            # Pas score aan voor veld-specifieke validatie
            result.score = result.score if result.errors else 1.0
            return result
        finally:
            self.rules = original_rules

    # Private helper methods

    def _load_rules(self):
        """Laad toetsregels uit configuratie."""
        if self.config.custom_rules_path:
            self.rules = laad_toetsregels(self.config.custom_rules_path)
        else:
            self.rules = laad_toetsregels()

        # Filter regels op basis van configuratie
        if not self.config.enable_all_rules:
            filtered_rules = {}
            for regel_id, regel_data in self.rules.items():
                category = regel_id.split("-")[0]
                if category in self.config.enabled_rule_categories:
                    filtered_rules[regel_id] = regel_data
            self.rules = filtered_rules

        logger.info(f"Geladen: {len(self.rules)} validatie regels")

    def _build_context_dict(self, definition: Definition) -> Dict[str, List[str]]:
        """Bouw context dictionary voor legacy toetser."""
        contexten = {"organisatorisch": [], "juridisch": [], "domein": []}

        if definition.context:
            contexten["organisatorisch"].append(definition.context)

        if definition.metadata:
            if "organisatie" in definition.metadata:
                contexten["organisatorisch"].append(definition.metadata["organisatie"])
            if "domein" in definition.metadata:
                contexten["domein"].append(definition.metadata["domein"])

        return contexten

    def _create_violation(
        self, regel_id: str, regel_data: Dict, resultaat: str, is_warning: bool = False
    ) -> str:
        """Creëer een violation string uit toets resultaat."""
        # Voor nu return gewoon het resultaat
        # In toekomst kunnen we dit uitbreiden naar RuleViolation objects
        return resultaat

    def _create_empty_result(self, reason: str) -> ValidationResult:
        """Creëer een leeg ValidationResult voor edge cases."""
        return ValidationResult(
            is_valid=False,
            errors=[f"❌ Validatie mislukt: {reason}"],
            warnings=[],
            suggestions=["Zorg dat de definitie niet leeg is"],
            score=0.0,
        )

    def _generate_suggestions(
        self, violations: List[str], definition: Definition
    ) -> List[str]:
        """Genereer verbeter suggesties op basis van violations."""
        suggestions = []

        # Analyseer violations voor patronen
        for violation in violations:
            if "werkwoord" in violation.lower():
                suggestions.append("Begin de definitie met een zelfstandig naamwoord")

            elif "context" in violation.lower() and "letterlijk" in violation.lower():
                suggestions.append(
                    "Vermijd het letterlijk noemen van de context in de definitie"
                )

            elif "afkorting" in violation.lower():
                suggestions.append("Voorzie afkortingen van uitleg tussen haakjes")

            elif "circulair" in violation.lower():
                suggestions.append(
                    "Vermijd het gebruik van het te definiëren begrip in de definitie zelf"
                )

            elif "voorbeelden" in violation.lower():
                suggestions.append("Verplaats voorbeelden naar een apart veld")

            elif "meervoud" in violation.lower():
                suggestions.append(
                    "Gebruik enkelvoud voor het begrip, tenzij het een plurale tantum betreft"
                )

        # Voeg algemene suggesties toe bij lage score
        if definition.definitie and len(definition.definitie.split()) < 10:
            suggestions.append("Overweeg de definitie uit te breiden met meer details")

        # Verwijder duplicaten en return
        return list(dict.fromkeys(suggestions))

    # Statistieken methods

    def get_stats(self) -> Dict[str, Any]:
        """Haal validator statistieken op."""
        return self._stats.copy()

    def reset_stats(self) -> None:
        """Reset de statistieken."""
        self._stats = {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "average_score": 0.0,
        }

    def get_rule_info(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Haal informatie op over een specifieke regel.

        Args:
            rule_id: ID van de regel (bijv. "ESS-01")

        Returns:
            Dictionary met regel informatie of None
        """
        if rule_id not in self.rules:
            return None

        regel = self.rules[rule_id]
        return {
            "id": rule_id,
            "naam": regel.get("naam", "Onbekend"),
            "uitleg": regel.get("uitleg", "Geen uitleg beschikbaar"),
            "categorie": rule_id.split("-")[0],
            "prioriteit": regel.get("prioriteit", "normaal"),
            "verplicht": regel.get("verplicht", False),
        }
