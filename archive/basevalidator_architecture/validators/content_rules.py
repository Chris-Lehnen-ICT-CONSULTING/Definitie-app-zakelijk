"""
Content validation rules (CON-01, CON-02).
These rules validate context-specific formulation and source authenticity.
"""

import re
from typing import Set
from .base_validator import BaseValidator, ValidationContext, ValidationOutput, ValidationResult


class CON01Validator(BaseValidator):
    """
    CON-01: Context-specific formulation without explicit naming.
    
    Validates that the definition is formulated to fit the given context(s)
    without explicitly mentioning the context itself in the definition.
    """
    
    def __init__(self):
        super().__init__(
            rule_id="CON-01",
            name="Eigen definitie voor elke context. Contextspecifieke formulering zonder expliciete benoeming",
            description="Formuleer de definitie zó dat deze past binnen de opgegeven context(en), zonder deze expliciet te benoemen in de definitie zelf."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate context-specific formulation."""
        definitie_lc = context.definitie.lower()
        contexten = context.contexten or {}
        regel = context.regel or {}
        
        # 1️⃣ Check for explicit user-provided contexts
        expliciete_hits = self._check_explicit_contexts(definitie_lc, contexten)
        if expliciete_hits:
            gevonden = ", ".join(sorted(set(expliciete_hits)))
            return self._create_result(
                ValidationResult.FAIL,
                f"opgegeven context letterlijk in definitie herkend ('{gevonden}')"
            )
        
        # 2️⃣ Check for broader context terms via regex patterns
        contextuele_term_hits = self._check_context_patterns(context.definitie, regel)
        
        # 3️⃣ Check against good/bad examples
        goede_match = self._check_good_examples(context.definitie, regel)
        foute_match = self._check_bad_examples(context.definitie, regel)
        
        # Determine result based on findings
        if contextuele_term_hits:
            if foute_match:
                return self._create_result(
                    ValidationResult.FAIL,
                    f"bredere contexttermen herkend ({', '.join(contextuele_term_hits)}), en lijkt op fout voorbeeld"
                )
            return self._create_result(
                ValidationResult.WARNING,
                f"bredere contexttaal herkend ({', '.join(contextuele_term_hits)}), formulering mogelijk vaag"
            )
        
        if foute_match:
            return self._create_result(
                ValidationResult.FAIL,
                "definitie bevat expliciet fout voorbeeld"
            )
        
        if goede_match:
            return self._create_result(
                ValidationResult.PASS,
                "definitie komt overeen met goed voorbeeld"
            )
        
        # Fallback - no explicit context reference found
        return self._create_result(
            ValidationResult.PASS,
            "geen expliciete contextverwijzing aangetroffen"
        )
    
    def _check_explicit_contexts(self, definitie_lc: str, contexten: dict) -> list:
        """Check for explicit user-provided contexts in definition."""
        expliciete_hits = []
        
        for label, waardelijst in contexten.items():
            if not waardelijst:
                continue
            
            for w in waardelijst:
                w = w.lower().strip()
                varianten = {
                    w,
                    w + "e",
                    w + "en",
                    w.rstrip("e")
                }
                
                for var in varianten:
                    if var and var in definitie_lc:
                        expliciete_hits.append(var)
        
        return expliciete_hits
    
    def _check_context_patterns(self, definitie: str, regel: dict) -> Set[str]:
        """Check for broader context terms via regex patterns."""
        patronen = regel.get("herkenbaar_patronen", [])
        contextuele_term_hits = set()
        
        for patroon in patronen:
            try:
                matches = re.findall(patroon, definitie, re.IGNORECASE)
                contextuele_term_hits.update(matches)
            except re.error:
                # Skip invalid regex patterns
                continue
        
        return contextuele_term_hits


class CON02Validator(BaseValidator):
    """
    CON-02: Base on authentic source.
    
    Validates that the definition is based on an authoritative source
    and includes explicit source references.
    """
    
    def __init__(self):
        super().__init__(
            rule_id="CON-02",
            name="Baseren op authentieke bron",
            description="De definitie moet gebaseerd zijn op een gezaghebbende bron en deze expliciet vermelden."
        )
    
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """Validate source authenticity."""
        bronnen_gebruikt = context.bronnen_gebruikt
        regel = context.regel or {}
        
        # 1️⃣ Check if sources are provided
        if not bronnen_gebruikt or not bronnen_gebruikt.strip():
            return self._create_result(
                ValidationResult.FAIL,
                "geen opgegeven bronnen gevonden (veld 'bronnen_gebruikt' is leeg of ontbreekt)"
            )
        
        bg = bronnen_gebruikt.strip()
        lc = bg.lower()
        
        # 2️⃣ Check for specific source patterns
        for pat in regel.get("bronpatronen_specifiek", []):
            try:
                if re.search(pat, lc):
                    return self._create_result(
                        ValidationResult.PASS,
                        f"bronvermelding voldoende specifiek → {bg}"
                    )
            except re.error:
                # Skip invalid regex patterns
                continue
        
        # 3️⃣ Check for general source patterns
        for pat in regel.get("bronpatronen_algemeen", []):
            try:
                if re.search(pat, lc):
                    return self._create_result(
                        ValidationResult.WARNING,
                        f"bronvermelding aanwezig ({bg}), maar mogelijk te algemeen"
                    )
            except re.error:
                # Skip invalid regex patterns
                continue
        
        # 4️⃣ Fallback - source found but not recognized as authentic
        return self._create_result(
            ValidationResult.FAIL,
            f"bronvermelding gevonden ({bg}), maar niet herkend als authentiek of specifiek"
        )