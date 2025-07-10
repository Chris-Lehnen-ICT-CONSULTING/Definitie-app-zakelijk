"""
Structure validation rules (STR-01 to STR-09).
These rules validate the structural aspects of definitions.
"""

import re
from .base_validator import BaseValidator, ValidationContext, ValidationOutput, ValidationResult


class StructureValidatorBase(BaseValidator):
    """Base class for structure validators with common functionality."""
    
    def _check_patterns_and_examples(self, context: ValidationContext) -> tuple:
        """Common pattern and example checking logic."""
        definitie = context.definitie
        regel = context.regel or {}
        
        goede_voorbeelden = regel.get("goede_voorbeelden", [])
        foute_voorbeelden = regel.get("foute_voorbeelden", [])
        
        goed = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
        fout = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)
        
        return goed, fout


class STR01Validator(StructureValidatorBase):
    """STR-01: Start with noun, not verb."""
    
    def __init__(self):
        super().__init__(
            rule_id="STR-01",
            name="Start met zelfstandig naamwoord, niet met werkwoord",
            description="De definitie moet beginnen met een zelfstandig naamwoord, niet met een werkwoord."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate that definition starts with noun, not verb."""
        regel = context.regel or {}
        beginwoorden = regel.get("herkenbaar_patronen", [])
        
        fout_begin = []
        for w in beginwoorden:
            try:
                if re.match(w, context.definitie):
                    fout_begin.append(w)
            except re.error:
                continue
        
        goed, fout = self._check_patterns_and_examples(context)
        
        if fout_begin:
            if fout:
                return self._create_result(
                    ValidationResult.FAIL,
                    f"definitie begint met werkwoord ({', '.join(fout_begin)}), en lijkt op fout voorbeeld"
                )
            return self._create_result(
                ValidationResult.FAIL,
                f"definitie begint met werkwoord ({', '.join(fout_begin)})"
            )
        
        if goed:
            return self._create_result(
                ValidationResult.PASS,
                "definitie start correct met zelfstandig naamwoord en komt overeen met goed voorbeeld"
            )
        
        return self._create_result(
            ValidationResult.PASS,
            "geen werkwoordelijke start herkend – mogelijk goed geformuleerd"
        )


class STR02Validator(StructureValidatorBase):
    """STR-02: Kick-off term should not be the term itself."""
    
    def __init__(self):
        super().__init__(
            rule_id="STR-02",
            name="Kick-off ≠ de term",
            description="De definitie mag niet beginnen met het te definiëren begrip zelf."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate that definition doesn't start with the term itself."""
        regel = context.regel or {}
        patronen = regel.get("herkenbaar_patronen", [])
        
        herhalingen = set()
        for patroon in patronen:
            try:
                herhalingen.update(re.findall(patroon, context.definitie, re.IGNORECASE))
            except re.error:
                continue
        
        goed, fout = self._check_patterns_and_examples(context)
        
        if herhalingen:
            if fout:
                return self._create_result(
                    ValidationResult.FAIL,
                    f"kick-off term is herhaling van begrip ({', '.join(herhalingen)}), en lijkt op fout voorbeeld"
                )
            return self._create_result(
                ValidationResult.FAIL,
                f"kick-off term is herhaling van begrip ({', '.join(herhalingen)})"
            )
        
        if goed:
            return self._create_result(
                ValidationResult.PASS,
                "definitie start met breder begrip en komt overeen met goed voorbeeld"
            )
        
        return self._create_result(
            ValidationResult.PASS,
            "geen herhaling van term herkend – mogelijk correct geformuleerd"
        )


class STR03Validator(StructureValidatorBase):
    """STR-03: Definition should not be a synonym."""
    
    def __init__(self):
        super().__init__(
            rule_id="STR-03",
            name="Definitie ≠ synoniem",
            description="De definitie mag niet alleen een synoniem zijn, maar moet een echte uitleg geven."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate that definition is not just a synonym."""
        regel = context.regel or {}
        patronen = regel.get("herkenbaar_patronen", [])
        
        synoniemen_gevonden = set()
        for patroon in patronen:
            try:
                synoniemen_gevonden.update(re.findall(patroon, context.definitie, re.IGNORECASE))
            except re.error:
                continue
        
        goed, fout = self._check_patterns_and_examples(context)
        
        if not synoniemen_gevonden:
            if goed:
                return self._create_result(
                    ValidationResult.PASS,
                    "geen synonieme formulering, komt overeen met goed voorbeeld"
                )
            return self._create_result(
                ValidationResult.PASS,
                "geen synonieme formulering gevonden"
            )
        
        if fout:
            return self._create_result(
                ValidationResult.FAIL,
                f"formulering lijkt synoniem ({', '.join(synoniemen_gevonden)}), komt overeen met fout voorbeeld"
            )
        
        return self._create_result(
            ValidationResult.FAIL,
            f"formulering lijkt synoniem ({', '.join(synoniemen_gevonden)}), zonder verdere uitleg"
        )


class STR04Validator(StructureValidatorBase):
    """STR-04: Follow kick-off with specification."""
    
    def __init__(self):
        super().__init__(
            rule_id="STR-04",
            name="Kick-off vervolgen met toespitsing",
            description="Na het algemene begrip moet een verdere toespitsing volgen."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate kick-off followed by specification."""
        regel = context.regel or {}
        patronen = regel.get("herkenbaar_patronen", [])
        
        match = False
        for patroon in patronen:
            try:
                if re.search(patroon, context.definitie, re.IGNORECASE):
                    match = True
                    break
            except re.error:
                continue
        
        goed, fout = self._check_patterns_and_examples(context)
        
        if match:
            if goed:
                return self._create_result(
                    ValidationResult.PASS,
                    "kick-off gevolgd door correcte toespitsing"
                )
            if fout:
                return self._create_result(
                    ValidationResult.FAIL,
                    "kick-off zonder toespitsing, komt overeen met fout voorbeeld"
                )
            return self._create_result(
                ValidationResult.PASS,
                "kick-off patroon herkend"
            )
        
        return self._create_result(
            ValidationResult.PASS,
            "geen specifiek kick-off patroon herkend"
        )


class STR05Validator(StructureValidatorBase):
    """STR-05: Avoid subordinate clauses."""
    
    def __init__(self):
        super().__init__(
            rule_id="STR-05",
            name="Vermijd bijzinnen",
            description="Vermijd bijzinnen met woorden als 'die', 'welke', 'waarin'."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate avoidance of subordinate clauses."""
        regel = context.regel or {}
        patronen = regel.get("herkenbaar_patronen", [])
        
        bijzinnen_gevonden = set()
        for patroon in patronen:
            try:
                matches = re.findall(patroon, context.definitie, re.IGNORECASE)
                bijzinnen_gevonden.update(matches)
            except re.error:
                continue
        
        goed, fout = self._check_patterns_and_examples(context)
        
        if bijzinnen_gevonden:
            if fout:
                return self._create_result(
                    ValidationResult.FAIL,
                    f"bijzinnen gevonden ({', '.join(bijzinnen_gevonden)}), komt overeen met fout voorbeeld"
                )
            return self._create_result(
                ValidationResult.WARNING,
                f"bijzinnen gevonden ({', '.join(bijzinnen_gevonden)}), overweeg herformulering"
            )
        
        if goed:
            return self._create_result(
                ValidationResult.PASS,
                "geen bijzinnen gevonden, komt overeen met goed voorbeeld"
            )
        
        return self._create_result(
            ValidationResult.PASS,
            "geen bijzinnen gevonden"
        )


class STR06Validator(StructureValidatorBase):
    """STR-06: Use singular form."""
    
    def __init__(self):
        super().__init__(
            rule_id="STR-06",
            name="Gebruik enkelvoud",
            description="Gebruik enkelvoud in plaats van meervoud in definities."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate use of singular form."""
        regel = context.regel or {}
        patronen = regel.get("herkenbaar_patronen", [])
        
        meervoud_gevonden = set()
        for patroon in patronen:
            try:
                matches = re.findall(patroon, context.definitie, re.IGNORECASE)
                meervoud_gevonden.update(matches)
            except re.error:
                continue
        
        goed, fout = self._check_patterns_and_examples(context)
        
        if meervoud_gevonden:
            if fout:
                return self._create_result(
                    ValidationResult.FAIL,
                    f"meervoud gevonden ({', '.join(meervoud_gevonden)}), komt overeen met fout voorbeeld"
                )
            return self._create_result(
                ValidationResult.WARNING,
                f"meervoud gevonden ({', '.join(meervoud_gevonden)}), gebruik enkelvoud"
            )
        
        if goed:
            return self._create_result(
                ValidationResult.PASS,
                "enkelvoud gebruikt, komt overeen met goed voorbeeld"
            )
        
        return self._create_result(
            ValidationResult.PASS,
            "geen meervoud aangetroffen"
        )


class STR07Validator(StructureValidatorBase):
    """STR-07: Avoid enumerations."""
    
    def __init__(self):
        super().__init__(
            rule_id="STR-07",
            name="Vermijd opsommingen",
            description="Vermijd opsommingen in definities, gebruik in plaats daarvan algemene karakterisering."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate avoidance of enumerations."""
        regel = context.regel or {}
        patronen = regel.get("herkenbaar_patronen", [])
        
        opsommingen_gevonden = set()
        for patroon in patronen:
            try:
                matches = re.findall(patroon, context.definitie, re.IGNORECASE)
                opsommingen_gevonden.update(matches)
            except re.error:
                continue
        
        goed, fout = self._check_patterns_and_examples(context)
        
        if opsommingen_gevonden:
            if fout:
                return self._create_result(
                    ValidationResult.FAIL,
                    f"opsomming gevonden ({', '.join(opsommingen_gevonden)}), komt overeen met fout voorbeeld"
                )
            return self._create_result(
                ValidationResult.WARNING,
                f"opsomming gevonden ({', '.join(opsommingen_gevonden)}), overweeg algemene karakterisering"
            )
        
        if goed:
            return self._create_result(
                ValidationResult.PASS,
                "geen opsomming gevonden, komt overeen met goed voorbeeld"
            )
        
        return self._create_result(
            ValidationResult.PASS,
            "geen opsomming aangetroffen"
        )


class STR08Validator(StructureValidatorBase):
    """STR-08: Avoid negative definitions."""
    
    def __init__(self):
        super().__init__(
            rule_id="STR-08",
            name="Vermijd negatieve definities",
            description="Definieer wat iets WEL is, niet wat het NIET is."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate avoidance of negative definitions."""
        regel = context.regel or {}
        patronen = regel.get("herkenbaar_patronen", [])
        
        negatieven_gevonden = set()
        for patroon in patronen:
            try:
                matches = re.findall(patroon, context.definitie, re.IGNORECASE)
                negatieven_gevonden.update(matches)
            except re.error:
                continue
        
        goed, fout = self._check_patterns_and_examples(context)
        
        if negatieven_gevonden:
            if fout:
                return self._create_result(
                    ValidationResult.FAIL,
                    f"negatieve formulering gevonden ({', '.join(negatieven_gevonden)}), komt overeen met fout voorbeeld"
                )
            return self._create_result(
                ValidationResult.WARNING,
                f"negatieve formulering gevonden ({', '.join(negatieven_gevonden)}), formuleer positief"
            )
        
        if goed:
            return self._create_result(
                ValidationResult.PASS,
                "positieve formulering, komt overeen met goed voorbeeld"
            )
        
        return self._create_result(
            ValidationResult.PASS,
            "geen negatieve formulering aangetroffen"
        )


class STR09Validator(StructureValidatorBase):
    """STR-09: Avoid circular definitions."""
    
    def __init__(self):
        super().__init__(
            rule_id="STR-09",
            name="Vermijd cirkelredeneringen",
            description="De definitie mag niet circulair zijn door het begrip in de definitie te herhalen."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate avoidance of circular definitions."""
        regel = context.regel or {}
        patronen = regel.get("herkenbaar_patronen", [])
        
        cirkels_gevonden = set()
        for patroon in patronen:
            try:
                matches = re.findall(patroon, context.definitie, re.IGNORECASE)
                cirkels_gevonden.update(matches)
            except re.error:
                continue
        
        goed, fout = self._check_patterns_and_examples(context)
        
        if cirkels_gevonden:
            if fout:
                return self._create_result(
                    ValidationResult.FAIL,
                    f"circulaire formulering gevonden ({', '.join(cirkels_gevonden)}), komt overeen met fout voorbeeld"
                )
            return self._create_result(
                ValidationResult.FAIL,
                f"circulaire formulering gevonden ({', '.join(cirkels_gevonden)})"
            )
        
        if goed:
            return self._create_result(
                ValidationResult.PASS,
                "geen circulaire formulering, komt overeen met goed voorbeeld"
            )
        
        return self._create_result(
            ValidationResult.PASS,
            "geen circulaire formulering aangetroffen"
        )