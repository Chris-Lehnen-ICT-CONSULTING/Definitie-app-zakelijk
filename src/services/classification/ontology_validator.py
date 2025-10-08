"""
Rules-based validator voor ontologische classificaties.

Voert sanity checks uit op LLM classificaties om implausibele resultaten te detecteren.
"""

import logging
import re

logger = logging.getLogger(__name__)


class OntologyValidator:
    """
    Validator voor ontologische classificaties.

    Gebruikt linguïstische patronen en heuristics om classificaties te valideren.
    """

    # Linguïstische patronen per categorie
    PATTERNS = {
        "TYPE": {
            "strong_indicators": [
                r"\b(soort|type|categorie|klasse)\b",
                r"\b(een|de)\s+\w+\s+(is|betreft)\s+(een|de)\b",
                r"\b(alle|elk|elke|iedere)\b",
            ],
            "weak_indicators": [
                r"\b(algemeen|generiek|algemene)\b",
            ],
            "anti_indicators": [
                r"\b(deze|dit|dat|die)\b",  # Specifieke verwijzingen
                r"\b(handeling|proces|activiteit)\b",
            ],
        },
        "EXEMPLAAR": {
            "strong_indicators": [
                r"\b(deze|dit|dat|specifieke|bepaalde)\b",
                r"\b(individuele|concrete|specifieke)\b",
                r"\b(het\s+\w+|de\s+\w+)\s+(genaamd|genoemd)\b",
            ],
            "weak_indicators": [
                r"\b(voorbeeld|instantie)\b",
            ],
            "anti_indicators": [
                r"\b(soort|type|alle|algemeen)\b",
            ],
        },
        "PROCES": {
            "strong_indicators": [
                r"\b(het|de)\s+\w+(en|ing)\b",  # werkwoord -> zelfstandig naamwoord
                r"\b(handeling|proces|activiteit|actie)\b",
                r"\b(uitvoeren|verrichten|doen)\b",
            ],
            "weak_indicators": [
                r"\b(doorlopen|verloop)\b",
            ],
            "anti_indicators": [
                r"\b(resultaat|uitkomst|product)\b",
            ],
        },
        "RESULTAAT": {
            "strong_indicators": [
                r"\b(resultaat|uitkomst|gevolg|product)\b",
                r"\b(verkregen|ontstaan|geproduceerd)\b",
                r"\b(na\s+\w+(en|ing))\b",  # "na het plukken"
            ],
            "weak_indicators": [
                r"\b(eindproduct|output)\b",
            ],
            "anti_indicators": [
                r"\b(handeling|proces|activiteit)\b",
            ],
        },
    }

    # Domein-specifieke sanity checks
    DOMAIN_RULES = {
        # Biologische termen zijn meestal TYPEs
        "biology": {
            "keywords": ["soort", "species", "genus", "familie", "orde"],
            "expected_level": "TYPE",
            "confidence_boost": 0.1,
        },
        # Juridische procedures zijn meestal PROCESSen
        "legal_procedure": {
            "keywords": ["procedure", "beroep", "bezwaar", "aanvraag"],
            "expected_level": "PROCES",
            "confidence_boost": 0.1,
        },
    }

    def validate(self, level: str, begrip: str, definitie: str) -> list[str]:
        """
        Valideer classificatie en return lijst van warnings.

        Args:
            level: Geclassificeerde ontologische level
            begrip: Begrip dat geclassificeerd is
            definitie: Definitie van het begrip

        Returns:
            List van warning strings (lege list = geen warnings)
        """
        warnings = []

        # Skip validatie voor ONBESLIST
        if level == "ONBESLIST":
            return warnings

        # Check 1: Linguïstische patronen
        pattern_warnings = self._check_patterns(level, definitie)
        warnings.extend(pattern_warnings)

        # Check 2: Domein heuristics
        domain_warnings = self._check_domain_rules(level, begrip, definitie)
        warnings.extend(domain_warnings)

        # Check 3: Basis sanity checks
        sanity_warnings = self._sanity_checks(level, begrip)
        warnings.extend(sanity_warnings)

        return warnings

    def _check_patterns(self, level: str, definitie: str) -> list[str]:
        """Check linguïstische patronen."""
        warnings = []
        patterns = self.PATTERNS.get(level, {})

        definitie_lower = definitie.lower()

        # Check anti-indicators (sterke contradicties)
        anti_patterns = patterns.get("anti_indicators", [])
        for pattern in anti_patterns:
            if re.search(pattern, definitie_lower):
                match = re.search(pattern, definitie_lower).group()
                warnings.append(
                    f"Anti-indicator gevonden voor {level}: '{match}' in definitie"
                )

        # Check missing strong indicators (zwakke waarschuwing)
        strong_patterns = patterns.get("strong_indicators", [])
        has_strong = any(re.search(p, definitie_lower) for p in strong_patterns)
        if not has_strong and strong_patterns:
            warnings.append(
                f"Geen sterke linguïstische indicatoren voor {level} gevonden"
            )

        return warnings

    def _check_domain_rules(self, level: str, begrip: str, definitie: str) -> list[str]:
        """Check domein-specifieke regels."""
        warnings = []
        text = f"{begrip} {definitie}".lower()

        for domain_name, rule in self.DOMAIN_RULES.items():
            # Check of keywords aanwezig zijn
            keywords_found = [kw for kw in rule["keywords"] if kw.lower() in text]

            if keywords_found and level != rule["expected_level"]:
                warnings.append(
                    f"Domein '{domain_name}' keywords gevonden ({keywords_found}), "
                    f"verwachte level is {rule['expected_level']}, niet {level}"
                )

        return warnings

    def _sanity_checks(self, level: str, begrip: str) -> list[str]:
        """Basis sanity checks."""
        warnings = []

        # Check: EXEMPLAAR moet niet te generiek klinken
        if level == "EXEMPLAAR":
            generic_words = ["algemeen", "elke", "alle", "soort", "type"]
            if any(word in begrip.lower() for word in generic_words):
                warnings.append(
                    f"EXEMPLAAR classificatie lijkt generiek voor begrip: {begrip}"
                )

        # Check: PROCES moet geen statisch object zijn
        if level == "PROCES":
            static_words = ["document", "formulier", "bewijs", "certificaat"]
            if any(word in begrip.lower() for word in static_words):
                warnings.append(
                    f"PROCES classificatie onwaarschijnlijk voor statisch object: {begrip}"
                )

        return warnings

    def get_pattern_matches(self, level: str, text: str) -> dict[str, list[str]]:
        """
        Return alle pattern matches voor debugging.

        Args:
            level: Ontologische level om te checken
            text: Tekst om te analyseren

        Returns:
            Dict met 'strong', 'weak', 'anti' keys en lists van matches
        """
        patterns = self.PATTERNS.get(level, {})
        text_lower = text.lower()

        result = {"strong_indicators": [], "weak_indicators": [], "anti_indicators": []}

        for category in result:
            for pattern in patterns.get(category, []):
                matches = re.findall(pattern, text_lower)
                if matches:
                    result[category].extend(matches)

        return result
