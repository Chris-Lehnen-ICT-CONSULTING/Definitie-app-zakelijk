"""
Essential validation rules (ESS-01 to ESS-05).
These rules validate the essential characteristics of definitions.
"""

import re
from typing import Dict, List, Any, Optional
from .base_validator import BaseValidator, ValidationContext, ValidationOutput, ValidationResult


class ESS01Validator(BaseValidator):
    """
    ESS-01: Describe the essence, not the purpose.
    
    Validates that the definition describes what the concept IS rather than
    what it is used FOR or what its purpose is.
    """
    
    def __init__(self):
        super().__init__(
            rule_id="ESS-01",
            name="Beschrijf de essentie, niet het doel",
            description="De definitie moet beschrijven wat het begrip IS, niet waarvoor het wordt gebruikt."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate that definition describes essence, not purpose."""
        regel = context.regel or {}
        
        # Check for purpose-oriented patterns
        for patroon in regel.get("herkenbaar_patronen", []):
            try:
                match = re.search(patroon, context.definitie, re.IGNORECASE)
                if match:
                    return self._create_result(
                        ValidationResult.FAIL,
                        f"doelpatroon '{match.group(0)}' herkend in definitie (patroon: {patroon})"
                    )
            except re.error:
                # Skip invalid regex patterns
                continue
        
        # No purpose patterns found
        return self._create_result(
            ValidationResult.PASS,
            "geen doelgerichte formuleringen aangetroffen"
        )


class ESS02Validator(BaseValidator):
    """
    ESS-02: Ontological category clarification (type/instance/process/result).
    
    Validates that the definition clearly indicates which of the four ontological
    categories the concept belongs to: type, instance, process, or result.
    """
    
    def __init__(self):
        super().__init__(
            rule_id="ESS-02",
            name="Ontologische categorie expliciteren",
            description="De definitie moet duidelijk maken of het begrip een type, exemplaar, proces of resultaat is."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate ontological category clarity."""
        definitie = context.definitie
        regel = context.regel or {}
        marker = context.marker
        
        d = definitie.lower().strip()
        
        # 0️⃣ Metadata override if provided
        if marker:
            return self._validate_marker(marker)
        
        # 1️⃣ Check for explicit bad examples per category
        bad_result = self._check_bad_examples_per_category(d, regel)
        if bad_result:
            return bad_result
        
        # 2️⃣ Pattern detection per category
        hits = self._detect_patterns_per_category(d, regel)
        
        # 3️⃣ Single category → ✔️
        if len(hits) == 1:
            cat, pats = next(iter(hits.items()))
            unieke = ", ".join(sorted(set(pats)))
            return self._create_result(
                ValidationResult.PASS,
                f"eenduidig als {cat} gedefinieerd ({unieke})"
            )
        
        # 4️⃣ Multiple categories → ❌ ambiguity
        if len(hits) > 1:
            found = ", ".join(sorted(hits.keys()))
            return self._create_result(
                ValidationResult.FAIL,
                f"ambiguïteit – meerdere categories herkend ({found}); kies één betekenislaag"
            )
        
        # 5️⃣ No hits → check good examples per category
        good_result = self._check_good_examples_per_category(d, regel)
        if good_result:
            return good_result
        
        # 6️⃣ Fallback → no marker
        return self._create_result(
            ValidationResult.FAIL,
            "geen duidelijke ontologische marker (type, particulier, proces of resultaat) gevonden"
        )
    
    def _validate_marker(self, marker: str) -> ValidationOutput:
        """Validate provided metadata marker."""
        m = marker.lower()
        if m in {"soort", "type"}:
            return self._create_result(ValidationResult.PASS, "eenduidig als soort gedefinieerd (via metadata)")
        if m in {"exemplaar", "particulier"}:
            return self._create_result(ValidationResult.PASS, "eenduidig als exemplaar gedefinieerd (via metadata)")
        if m in {"proces", "activiteit"}:
            return self._create_result(ValidationResult.PASS, "eenduidig als proces gedefinieerd (via metadata)")
        if m in {"resultaat", "uitkomst"}:
            return self._create_result(ValidationResult.PASS, "eenduidig als resultaat gedefinieerd (via metadata)")
        
        return self._create_result(
            ValidationResult.FAIL,
            f"ongeldige marker '{marker}'; gebruik soort/exemplaar/proces/resultaat"
        )
    
    def _check_bad_examples_per_category(self, d: str, regel: Dict[str, Any]) -> Optional[ValidationOutput]:
        """Check for explicit bad examples per category."""
        categories = [
            ("type", "foute_voorbeelden_type"),
            ("particulier", "foute_voorbeelden_particulier"),
            ("proces", "foute_voorbeelden_proces"),
            ("resultaat", "foute_voorbeelden_resultaat"),
        ]
        
        for cat, key in categories:
            for voorbeeld in regel.get(key, []):
                if voorbeeld.lower() in d:
                    return self._create_result(
                        ValidationResult.FAIL,
                        f"expliciet fout voorbeeld voor {cat} gevonden – vermijd deze formulering"
                    )
        return None
    
    def _detect_patterns_per_category(self, d: str, regel: Dict[str, Any]) -> Dict[str, List[str]]:
        """Detect patterns per ontological category."""
        hits: Dict[str, List[str]] = {}
        pattern_keys = {
            "type": "herkenbaar_patronen_type",
            "particulier": "herkenbaar_patronen_particulier",
            "proces": "herkenbaar_patronen_proces",
            "resultaat": "herkenbaar_patronen_resultaat",
        }
        
        for cat, pat_key in pattern_keys.items():
            for pat in regel.get(pat_key, []):
                try:
                    if re.search(pat, d, flags=re.IGNORECASE):
                        hits.setdefault(cat, []).append(pat)
                except re.error:
                    # Skip invalid regex patterns
                    continue
        
        return hits
    
    def _check_good_examples_per_category(self, d: str, regel: Dict[str, Any]) -> Optional[ValidationOutput]:
        """Check for good examples per category."""
        good_keys = {
            "type": "goede_voorbeelden_type",
            "particulier": "goede_voorbeelden_particulier",
            "proces": "goede_voorbeelden_proces",
            "resultaat": "goede_voorbeelden_resultaat",
        }
        
        for cat, key in good_keys.items():
            for voorbeeld in regel.get(key, []):
                if voorbeeld.lower() in d:
                    return self._create_result(
                        ValidationResult.PASS,
                        f"eenduidig als {cat} gedefinieerd (voorbeeld match)"
                    )
        return None


class ESS03Validator(BaseValidator):
    """
    ESS-03: Instances uniquely distinguishable (countability).
    
    Validates that the definition provides criteria to uniquely identify
    and distinguish individual instances of the concept.
    """
    
    def __init__(self):
        super().__init__(
            rule_id="ESS-03",
            name="Instanties uniek onderscheidbaar (telbaarheid)",
            description="De definitie moet criteria bevatten om individuele instanties uniek te kunnen onderscheiden."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate unique identification criteria."""
        definitie = context.definitie
        regel = context.regel or {}
        d_lc = definitie.lower().strip()
        
        # 1️⃣ Check for explicit bad examples
        for fout in regel.get("foute_voorbeelden", []):
            if fout.lower() in d_lc:
                return self._create_result(
                    ValidationResult.FAIL,
                    "definitie mist unieke identificatiecriteria (fout voorbeeld aangetroffen)"
                )
        
        # 2️⃣ Check for explicit good examples
        for goed in regel.get("goede_voorbeelden", []):
            if goed.lower() in d_lc:
                return self._create_result(
                    ValidationResult.PASS,
                    "expliciete unieke identificatiecriteria gevonden (volgens goed voorbeeld)"
                )
        
        # 3️⃣ Pattern detection from JSON
        gevonden = set()
        for patroon in regel.get("herkenbaar_patronen", []):
            try:
                for m in re.finditer(patroon, definitie, flags=re.IGNORECASE):
                    gevonden.add(m.group(0).strip())
            except re.error:
                # Skip invalid regex patterns
                continue
        
        if gevonden:
            labels = ", ".join(sorted(gevonden))
            return self._create_result(
                ValidationResult.PASS,
                f"unieke identificatiecriteria herkend ({labels})"
            )
        
        # 4️⃣ Fallback: no criteria found
        return self._create_result(
            ValidationResult.FAIL,
            "geen unieke identificatiecriteria gevonden; definitie is niet telbaar onderscheidbaar"
        )


class ESS04Validator(BaseValidator):
    """
    ESS-04: Testability.
    
    Validates that the definition contains testable criteria so users can
    objectively determine whether something falls under the concept or not.
    """
    
    def __init__(self):
        super().__init__(
            rule_id="ESS-04",
            name="Toetsbaarheid",
            description="De definitie moet toetsbare criteria bevatten voor objectieve vaststelling."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate testability criteria."""
        definitie = context.definitie
        regel = context.regel or {}
        d = definitie.lower().strip()
        
        # 1️⃣ Check for explicit bad examples (vague formulations)
        for fout in regel.get("foute_voorbeelden", []):
            if fout.lower() in d:
                return self._create_result(
                    ValidationResult.FAIL,
                    "bevat vage bewoording (bijv. 'zo snel mogelijk') – definitie is niet toetsbaar"
                )
        
        # 2️⃣ Check for explicit good examples (concrete criteria)
        for goed in regel.get("goede_voorbeelden", []):
            if goed.lower() in d:
                return self._create_result(
                    ValidationResult.PASS,
                    "bevat toetsbare criteria (volgens goed voorbeeld uit config)"
                )
        
        # 3️⃣ Pattern detection from JSON
        gevonden = []
        for patroon in regel.get("herkenbaar_patronen", []):
            try:
                if re.search(patroon, definitie, flags=re.IGNORECASE):
                    gevonden.append(patroon)
            except re.error:
                # Skip invalid regex patterns
                continue
        
        # 3a️⃣ Additional automatic checks for numbers/time/percentages
        if re.search(r"\b\d+\s*(dagen|weken|uren|maanden)\b", d):
            gevonden.append("AUTO: numeriek tijdspatroon")
        if re.search(r"\b\d+\s*%\b", d):
            gevonden.append("AUTO: percentagepatroon")
        
        if gevonden:
            unieke = ", ".join(sorted(set(gevonden)))
            return self._create_result(
                ValidationResult.PASS,
                f"toetsbaar criterium herkend ({unieke})"
            )
        
        # 4️⃣ Fallback: nothing found → not testable
        return self._create_result(
            ValidationResult.FAIL,
            "geen toetsbare elementen gevonden; definitie bevat geen harde criteria voor objectieve toetsing"
        )


class ESS05Validator(BaseValidator):
    """
    ESS-05: Sufficiently distinguishing.
    
    Validates that the definition explicitly states how the concept differs
    from related concepts in the same domain.
    """
    
    def __init__(self):
        super().__init__(
            rule_id="ESS-05",
            name="Voldoende onderscheidend",
            description="De definitie moet duidelijk maken waarin het begrip zich onderscheidt van verwante begrippen."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate distinguishing characteristics."""
        definitie = context.definitie
        regel = context.regel or {}
        d = definitie.lower().strip()
        
        # 1️⃣ Check for explicit bad examples
        for fout in regel.get("foute_voorbeelden", []):
            if fout.lower() in d:
                return self._create_result(
                    ValidationResult.FAIL,
                    f"definitie bevat niet-onderscheidende formulering (fout voorbeeld: '{fout}')"
                )
        
        # 2️⃣ Check for explicit good examples
        for goed in regel.get("goede_voorbeelden", []):
            if goed.lower() in d:
                return self._create_result(
                    ValidationResult.PASS,
                    "onderscheidende formulering aangetroffen (volgens goed voorbeeld)"
                )
        
        # 3️⃣ Pattern detection from JSON
        gevonden = []
        for patroon in regel.get("herkenbaar_patronen", []):
            try:
                if re.search(patroon, definitie, flags=re.IGNORECASE):
                    gevonden.append(patroon)
            except re.error:
                # Skip invalid regex patterns
                continue
        
        if gevonden:
            labels = ", ".join(sorted(set(gevonden)))
            return self._create_result(
                ValidationResult.PASS,
                f"onderscheidende patroon(en) herkend ({labels})"
            )
        
        # 4️⃣ Fallback: nothing found → not sufficiently distinguishing
        return self._create_result(
            ValidationResult.FAIL,
            "geen onderscheidende elementen gevonden; definitie maakt niet duidelijk waarin het begrip zich onderscheidt"
        )